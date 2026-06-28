"""
深度学习模型一：岗位-简历匹配度预测（Siamese Network）
用于人岗智能匹配，输出0-100的匹配分数
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, List, Optional
import jieba
import pickle
import os
import json
import re
from pathlib import Path

class SiameseMatchingNet(nn.Module):
    """孪生网络：计算简历和岗位要求的匹配度"""
    
    def __init__(self, vocab_size: int = 10000, embed_dim: int = 128, 
                 hidden_dim: int = 256, num_layers: int = 2, dropout: float = 0.3):
        super().__init__()
        
        # 嵌入层
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        
        # BiLSTM 编码器（共享权重）
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim // 2,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # 编码后的向量维度 = hidden_dim * 3（因为拼接了 last_hidden, pooled_max, pooled_mean）
        encoding_dim = hidden_dim * 3   # 当 hidden_dim=256 时，encoding_dim=768
        
        # 融合层的输入维度 = concat(2个编码) + diff + product = 2*encoding_dim + encoding_dim + encoding_dim = 4*encoding_dim
        fusion_input_dim = 4 * encoding_dim   # 4*768=3072
        
        # 特征融合层
        self.fusion = nn.Sequential(
            nn.Linear(fusion_input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """编码单侧文本为特征向量"""
        embedded = self.embedding(x)
        outputs, (hidden, _) = self.encoder(embedded)
        # 取最后一层的双向隐藏状态
        last_hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)
        # Max pooling 和 Mean pooling
        pooled_max = torch.max(outputs, dim=1)[0]
        pooled_mean = torch.mean(outputs, dim=1)
        # 拼接三种特征
        return torch.cat([last_hidden, pooled_max, pooled_mean], dim=1)
    
    def forward(self, resume_text: torch.Tensor, job_text: torch.Tensor) -> torch.Tensor:
        resume_vec = self.encode(resume_text)
        job_vec = self.encode(job_text)
        
        # 多种交互特征
        concat = torch.cat([resume_vec, job_vec], dim=1)
        diff = torch.abs(resume_vec - job_vec)
        product = resume_vec * job_vec
        combined = torch.cat([concat, diff, product], dim=1)
        
        return self.fusion(combined) * 100  # 输出0-100分


class TextProcessor:
    """文本预处理：分词、构建词表、序列化"""
    
    def __init__(self, vocab_size: int = 10000, max_len: int = 256):
        self.vocab_size = vocab_size
        self.max_len = max_len
        self.word2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2word = {0: '<PAD>', 1: '<UNK>'}
        self.vocab_built = False
        
    def build_vocab(self, texts: List[str]):
        """从文本列表构建词表"""
        word_freq = {}
        for text in texts:
            words = jieba.lcut(text)
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        for word, _ in sorted_words[:self.vocab_size - 2]:
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word
        
        self.vocab_built = True
        print(f"✅ 词表构建完成，共 {len(self.word2idx)} 个词")
    
    def text_to_sequence(self, text: str) -> np.ndarray:
        if not self.vocab_built:
            raise ValueError("请先调用 build_vocab()")
        words = jieba.lcut(text)
        seq = [self.word2idx.get(word, 1) for word in words]
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


class MatchingPredictor:
    """匹配预测器：封装模型加载和预测逻辑"""
    
    def __init__(self, model_path: str, processor_path: str, device: str = 'cpu'):
        self.device = torch.device(device)
        self.processor = TextProcessor.load(processor_path)
        self.model = SiameseMatchingNet(
            vocab_size=len(self.processor.word2idx),
            embed_dim=128,
            hidden_dim=256
        ).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
    
    def predict(self, resume_text: str, job_text: str) -> float:
        """返回匹配分数 0-100"""
        resume_seq = self.processor.text_to_sequence(resume_text)
        job_seq = self.processor.text_to_sequence(job_text)
        
        resume_tensor = torch.tensor([resume_seq], dtype=torch.long).to(self.device)
        job_tensor = torch.tensor([job_seq], dtype=torch.long).to(self.device)
        
        with torch.no_grad():
            score = self.model(resume_tensor, job_tensor).item()
        return round(score, 2)