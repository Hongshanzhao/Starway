"""
深度学习模型三：岗位自动分类（TextCNN 多分类）
输入 job_name + job_description，预测 category_id
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Tuple, Optional
import jieba
import pickle
import os


class TextCNN(nn.Module):
    """TextCNN：多核一维卷积 + 最大池化 + 全连接分类"""

    def __init__(self, vocab_size: int, embed_dim: int = 128,
                 num_classes: int = 13, kernel_sizes: List[int] = None,
                 num_filters: int = 100, dropout: float = 0.4):
        super().__init__()
        if kernel_sizes is None:
            kernel_sizes = [2, 3, 4]

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embed_dim, out_channels=num_filters,
                      kernel_size=k, padding='same')
            for k in kernel_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(num_filters * len(kernel_sizes), num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len)
        embedded = self.embedding(x)          # (batch, seq_len, embed_dim)
        embedded = embedded.permute(0, 2, 1)  # (batch, embed_dim, seq_len)
        conv_outputs = []
        for conv in self.convs:
            c = F.relu(conv(embedded))        # (batch, num_filters, seq_len)
            c = F.max_pool1d(c, c.size(2))    # (batch, num_filters, 1)
            conv_outputs.append(c.squeeze(2)) # (batch, num_filters)
        combined = torch.cat(conv_outputs, dim=1)  # (batch, num_filters * len(kernels))
        combined = self.dropout(combined)
        return self.fc(combined)  # raw logits


class JobTextProcessor:
    """岗位文本预处理：分词、词表、序列化"""

    def __init__(self, vocab_size: int = 10000, max_len: int = 128):
        self.vocab_size = vocab_size
        self.max_len = max_len
        self.word2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2word = {0: '<PAD>', 1: '<UNK>'}
        self.vocab_built = False

    def build_vocab(self, texts: List[str]):
        word_freq = {}
        for text in texts:
            for word in jieba.lcut(text):
                word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        for word, _ in sorted_words[:self.vocab_size - 2]:
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word
        self.vocab_built = True
        print(f"词表构建完成，共 {len(self.word2idx)} 个词")

    def text_to_sequence(self, text: str) -> np.ndarray:
        if not self.vocab_built:
            raise ValueError("请先调用 build_vocab()")
        words = jieba.lcut(text)
        seq = [self.word2idx.get(w, 1) for w in words]
        if len(seq) > self.max_len:
            seq = seq[:self.max_len]
        else:
            seq = seq + [0] * (self.max_len - len(seq))
        return np.array(seq, dtype=np.int64)

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({
                'word2idx': self.word2idx,
                'idx2word': self.idx2word,
                'vocab_size': self.vocab_size,
                'max_len': self.max_len
            }, f)

    @classmethod
    def load(cls, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        processor = cls(vocab_size=data['vocab_size'], max_len=data['max_len'])
        processor.word2idx = data['word2idx']
        processor.idx2word = data['idx2word']
        processor.vocab_built = True
        return processor


class JobClassifier:
    """岗位分类预测器"""

    def __init__(self, model_path: str, processor_path: str,
                 category_map_path: str, device: str = 'cpu'):
        self.device = torch.device(device)
        self.processor = JobTextProcessor.load(processor_path)

        with open(category_map_path, 'rb') as f:
            data = pickle.load(f)
        self.id2category = data['id2category']
        self.category2id = data['category2id']
        num_classes = len(self.id2category)

        self.model = TextCNN(
            vocab_size=len(self.processor.word2idx),
            embed_dim=128,
            num_classes=num_classes
        ).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def predict(self, job_name: str, job_description: str = '',
                top_k: int = 3) -> List[dict]:
        """返回 top_k 个分类及概率"""
        text = f"{job_name} {job_description}"
        seq = self.processor.text_to_sequence(text)
        tensor = torch.tensor([seq], dtype=torch.long).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
        top_indices = probs.argsort()[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append({
                'category_id': int(idx),
                'category_name': self.id2category.get(int(idx), f'未知({idx})'),
                'probability': round(float(probs[idx]), 4)
            })
        return results
