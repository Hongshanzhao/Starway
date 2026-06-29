"""
深度学习模型二：岗位向量化（Word2Vec）
基于职位序列训练，用于推荐晋升/转型路径
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import defaultdict, Counter
import json
import pickle
import os
from typing import List, Tuple, Dict
import random

from db import get_db

class Job2Vec:
    """基于职位序列训练Word2Vec模型"""
    
    def __init__(self, embedding_dim=128, window_size=5, learning_rate=0.01):
        self.embedding_dim = embedding_dim
        self.window_size = window_size
        self.lr = learning_rate
        self.job2id = {}
        self.id2job = {}
        self.embeddings = None
        
    def build_vocab(self, sequences: List[List[str]], min_count=2):
        """从职位序列构建词表"""
        counter = Counter()
        for seq in sequences:
            for job in seq:
                counter[job] += 1
        
        # 过滤低频职位
        self.job2id = {'<PAD>': 0, '<UNK>': 1}
        for job, count in counter.items():
            if count >= min_count:
                self.job2id[job] = len(self.job2id)
        self.id2job = {v: k for k, v in self.job2id.items()}
        self.vocab_size = len(self.job2id)
        print(f"✅ 词表构建完成，共 {self.vocab_size} 个岗位")
    
    def generate_training_pairs(self, sequences: List[List[str]]):
        """生成 (中心词，上下文词) 训练对"""
        pairs = []
        for seq in sequences:
            for i, center in enumerate(seq):
                if center not in self.job2id:
                    continue
                center_id = self.job2id[center]
                start = max(0, i - self.window_size)
                end = min(len(seq), i + self.window_size + 1)
                for j in range(start, end):
                    if j == i:
                        continue
                    context = seq[j]
                    if context in self.job2id:
                        context_id = self.job2id[context]
                        pairs.append((center_id, context_id))
        return pairs
    
    def train(self, sequences: List[List[str]], epochs=50, batch_size=64):
        """训练Word2Vec (Skip-gram with negative sampling)"""
        self.build_vocab(sequences)
        pairs = self.generate_training_pairs(sequences)
        print(f"✅ 生成 {len(pairs)} 个训练对")
        
        # 初始化参数
        self.embeddings = np.random.randn(self.vocab_size, self.embedding_dim) / self.embedding_dim
        self.context_embeddings = np.random.randn(self.vocab_size, self.embedding_dim) / self.embedding_dim
        
        # 负采样分布
        word_counts = np.array([1] * self.vocab_size)  # 简化，实际可用频率
        neg_sample_probs = word_counts / word_counts.sum()
        
        for epoch in range(epochs):
            np.random.shuffle(pairs)
            total_loss = 0
            for i in range(0, len(pairs), batch_size):
                batch = pairs[i:i+batch_size]
                loss = self._train_batch(batch, neg_sample_probs)
                total_loss += loss
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(pairs):.4f}")
    
    def _train_batch(self, batch, neg_sample_probs, num_neg=5):
        loss = 0
        for center, context in batch:
            # 正样本梯度
            center_vec = self.embeddings[center]
            context_vec = self.context_embeddings[context]
            score = np.dot(center_vec, context_vec)
            sig = 1 / (1 + np.exp(-score))
            grad = (sig - 1) * context_vec
            self.embeddings[center] -= self.lr * grad
            self.context_embeddings[context] -= self.lr * (sig - 1) * center_vec
            loss += -np.log(sig)
            
            # 负样本
            for _ in range(num_neg):
                neg = np.random.choice(self.vocab_size, p=neg_sample_probs)
                if neg == context:
                    continue
                neg_vec = self.context_embeddings[neg]
                score_neg = np.dot(center_vec, neg_vec)
                sig_neg = 1 / (1 + np.exp(-score_neg))
                grad_neg = sig_neg * neg_vec
                self.embeddings[center] -= self.lr * grad_neg
                self.context_embeddings[neg] -= self.lr * sig_neg * center_vec
                loss += -np.log(1 - sig_neg)
        return loss
    
    def most_similar(self, job_name: str, top_n=10) -> List[Tuple[str, float]]:
        """找出最相似的岗位"""
        if job_name not in self.job2id:
            return []
        job_id = self.job2id[job_name]
        job_vec = self.embeddings[job_id]
        similarities = []
        for other_id, other_vec in enumerate(self.embeddings):
            if other_id == job_id:
                continue
            sim = np.dot(job_vec, other_vec) / (np.linalg.norm(job_vec) * np.linalg.norm(other_vec) + 1e-8)
            similarities.append((self.id2job[other_id], sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    def analogy(self, a: str, b: str, c: str, top_n=5) -> List[str]:
        """向量类比: a 相对于 b 类似于 c 相对于 ?"""
        if a not in self.job2id or b not in self.job2id or c not in self.job2id:
            return []
        vec_a = self.embeddings[self.job2id[a]]
        vec_b = self.embeddings[self.job2id[b]]
        vec_c = self.embeddings[self.job2id[c]]
        target_vec = vec_c + (vec_b - vec_a)
        similarities = []
        for job_id, job_vec in enumerate(self.embeddings):
            sim = np.dot(target_vec, job_vec) / (np.linalg.norm(target_vec) * np.linalg.norm(job_vec) + 1e-8)
            similarities.append((self.id2job[job_id], sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [job for job, _ in similarities[:top_n] if job not in [a, b, c]]
    
    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({
                'job2id': self.job2id,
                'id2job': self.id2job,
                'embeddings': self.embeddings,
                'embedding_dim': self.embedding_dim
            }, f)
    
    @classmethod
    def load(cls, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        model = cls(embedding_dim=data['embedding_dim'])
        model.job2id = data['job2id']
        model.id2job = data['id2job']
        model.embeddings = data['embeddings']
        model.vocab_size = len(model.job2id)
        return model


class JobPathRecommender:
    """基于Job2Vec的职业路径推荐器"""
    
    def __init__(self, model_path: str):
        self.model = Job2Vec.load(model_path)
    
    def get_promotion_path(self, current_job: str, max_steps=3) -> List[str]:
        """基于向量相似度推荐同赛道相邻发展路径。"""
        if current_job not in self.model.job2id:
            return []

        path = [current_job]
        current_vec = self.model.embeddings[self.model.job2id[current_job]]
        for _ in range(max_steps):
            best_job = None
            best_sim = -1
            for job_id, job_vec in enumerate(self.model.embeddings):
                if self.model.id2job[job_id] in path:
                    continue
                sim = np.dot(current_vec, job_vec) / (np.linalg.norm(current_vec) * np.linalg.norm(job_vec) + 1e-8)
                if sim > best_sim:
                    best_sim = sim
                    best_job = self.model.id2job[job_id]
            if best_job:
                path.append(best_job)
                current_vec = self.model.embeddings[self.model.job2id[best_job]]
            else:
                break
        return path
    
    def get_transition_paths(self, current_job: str, top_n=5) -> List[Tuple[str, float]]:
        """推荐横向转型岗位（直接最相似）"""
        return self.model.most_similar(current_job, top_n)
