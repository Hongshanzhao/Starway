"""
模型二：岗位技能标签预测（TextCNN 多标签分类）
自动从 job_description 提取技能词表，训练多标签预测模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Tuple, Optional
from collections import Counter
import jieba
import pickle
import os
import re

from services.dl_models.text_utils import clean_text


# 非技能停用词（将被自动过滤）
NON_SKILL_PATTERNS = re.compile(
    r'^(负责|工作|进行|岗位|职责|任职|要求|公司|团队|业务|项目|技术|开发|设计|管理|分析|'
    r'完成|参与|提供|支持|协助|推进|提升|推动|建立|制定|执行|维护|优化|实现|解决|处理|'
    r'协调|沟通|组织|安排|相关|以上|以下|优先|经验|能力|具有|具备|拥有|掌握|熟悉|了解|'
    r'可以|能够|需要|已经|还有|并将|把被|让对|从以|之与|及或|等其|中进|行通|过往|'
    r'根据|按照|关于|以及|并而|而且|但仅|只更|最非|常十|分比|较特|别主|要包|括例|'
    r'如比|的了一|是我不|有和就|人都一|个上也|很到说|要去你|会着没有|看好自己|'
    r'他她它|们那些|所为|所以|因为|但是|然而|虽然|如果)$'
)


def is_skill_word(word: str) -> bool:
    """判断是否为有效技能词"""
    if len(word) < 2:
        return False
    if word.isdigit():
        return False
    if NON_SKILL_PATTERNS.match(word):
        return False
    return True


class SkillLabelExtractor:
    """从岗位描述中自动提取技能标签词表"""

    def __init__(self, max_labels: int = 150):
        self.max_labels = max_labels
        self.labels: List[str] = []
        self.label2id: dict = {}
        self.id2label: dict = {}

    def build_from_texts(self, texts: List[str]):
        """统计词频，选 top-N 个高频词作为技能标签"""
        cleaned = [clean_text(t) for t in texts]
        counter = Counter()
        for text in cleaned:
            words = jieba.lcut(text)
            for w in words:
                w = w.strip().lower()
                if is_skill_word(w):
                    counter[w] += 1

        # 取 top max_labels
        self.labels = [w for w, _ in counter.most_common(self.max_labels)]
        self.label2id = {lbl: i for i, lbl in enumerate(self.labels)}
        self.id2label = {i: lbl for lbl, i in self.label2id.items()}
        print(f"技能词表构建完成，共 {len(self.labels)} 个标签")
        print(f"  示例: {self.labels[:15]}")

    def encode(self, text: str) -> np.ndarray:
        """将文本转为多标签向量 (0/1)"""
        words = set(jieba.lcut(clean_text(text)))
        vec = np.zeros(len(self.labels), dtype=np.float32)
        for i, label in enumerate(self.labels):
            if label.lower() in words:
                vec[i] = 1.0
        return vec

    def decode(self, probs: np.ndarray, top_k: int = 5) -> List[dict]:
        """将概率向量解码为 top-k 标签列表"""
        indices = np.argsort(probs)[::-1][:top_k]
        return [
            {'skill': self.labels[i], 'probability': round(float(probs[i]), 4)}
            for i in indices
        ]

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'labels': self.labels,
                'label2id': self.label2id,
                'id2label': self.id2label,
                'max_labels': self.max_labels,
            }, f)

    @classmethod
    def load(cls, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        instance = cls(max_labels=data['max_labels'])
        instance.labels = data['labels']
        instance.label2id = data['label2id']
        instance.id2label = data['id2label']
        return instance


class SkillTextProcessor:
    """技能标签文本处理器（分词 + 序列化）"""

    def __init__(self, vocab_size: int = 10000, max_len: int = 128):
        self.vocab_size = vocab_size
        self.max_len = max_len
        self.word2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2word = {0: '<PAD>', 1: '<UNK>'}

    def build_vocab(self, texts: List[str]):
        word_freq = {}
        for text in texts:
            for w in jieba.lcut(text):
                word_freq[w] = word_freq.get(w, 0) + 1
        for w, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:self.vocab_size - 2]:
            idx = len(self.word2idx)
            self.word2idx[w] = idx
            self.idx2word[idx] = w
        print(f"词表构建完成，共 {len(self.word2idx)} 个词")

    def text_to_sequence(self, text: str) -> np.ndarray:
        words = jieba.lcut(text)
        seq = [self.word2idx.get(w, 1) for w in words]
        if len(seq) > self.max_len:
            seq = seq[:self.max_len]
        else:
            seq += [0] * (self.max_len - len(seq))
        return np.array(seq, dtype=np.int64)

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({
                'word2idx': self.word2idx, 'idx2word': self.idx2word,
                'vocab_size': self.vocab_size, 'max_len': self.max_len,
            }, f)

    @classmethod
    def load(cls, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        instance = cls(data['vocab_size'], data['max_len'])
        instance.word2idx = data['word2idx']
        instance.idx2word = data['idx2word']
        return instance


class SkillTextCNN(nn.Module):
    """TextCNN 多标签分类"""

    def __init__(self, vocab_size: int, num_labels: int, embed_dim: int = 128,
                 kernel_sizes: List[int] = None, num_filters: int = 100,
                 dropout: float = 0.4):
        super().__init__()
        if kernel_sizes is None:
            kernel_sizes = [2, 3, 4]
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, num_filters, k, padding='same') for k in kernel_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(num_filters * len(kernel_sizes), num_labels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.embedding(x).permute(0, 2, 1)  # (B, E, L)
        pooled = []
        for conv in self.convs:
            c = F.relu(conv(x))
            c = F.max_pool1d(c, c.size(2)).squeeze(2)
            pooled.append(c)
        x = torch.cat(pooled, dim=1)
        x = self.dropout(x)
        return self.fc(x)  # raw logits


class SkillPredictor:
    """技能标签预测器"""

    def __init__(self, model_path: str, processor_path: str,
                 label_path: str, device: str = 'cpu'):
        self.device = torch.device(device)
        self.processor = SkillTextProcessor.load(processor_path)
        self.label_extractor = SkillLabelExtractor.load(label_path)
        self.model = SkillTextCNN(
            len(self.processor.word2idx), len(self.label_extractor.labels), 128
        ).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def predict(self, job_description: str, top_k: int = 5) -> List[dict]:
        text = clean_text(job_description)
        seq = self.processor.text_to_sequence(text)
        t = torch.from_numpy(np.asarray([seq], dtype=np.int64)).to(self.device)
        with torch.no_grad():
            probs = torch.sigmoid(self.model(t)).cpu().numpy()[0]
        return self.label_extractor.decode(probs, top_k=top_k)
