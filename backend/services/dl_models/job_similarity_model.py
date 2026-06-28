"""
模型一：岗位相似度检索（无监督，sentence-transformers）
使用预训练模型生成384维向量，余弦相似度检索
"""

import numpy as np
import pickle
import os
from typing import List, Tuple, Optional


class JobSimilarityModel:
    """岗位相似度检索模型"""

    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.model_name = model_name
        self.model = None
        self.job_ids: List[int] = []
        self.embeddings: Optional[np.ndarray] = None
        self._norms: Optional[np.ndarray] = None

    def _lazy_load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    def encode_jobs(self, job_texts: List[str], job_ids: List[int],
                    batch_size: int = 64, show_progress: bool = True) -> np.ndarray:
        """将岗位文本编码为向量"""
        self._lazy_load_model()
        self.job_ids = list(job_ids)
        self.embeddings = self.model.encode(
            job_texts, batch_size=batch_size,
            show_progress_bar=show_progress, normalize_embeddings=True
        )
        self._norms = None  # already normalized
        return self.embeddings

    def search_similar(self, job_id: int, top_k: int = 10) -> List[dict]:
        """根据 job_id 查找最相似的岗位"""
        if self.embeddings is None:
            raise ValueError("请先调用 encode_jobs() 或 load() 加载向量")

        try:
            idx = self.job_ids.index(job_id)
        except ValueError:
            return []

        query_vec = self.embeddings[idx]
        # 余弦相似度（向量已归一化，直接点积）
        scores = np.dot(self.embeddings, query_vec)

        # 排除自身，取 top_k
        top_indices = np.argsort(scores)[::-1]
        results = []
        for i in top_indices:
            if i == idx:
                continue
            results.append({
                'job_id': int(self.job_ids[i]),
                'similarity': round(float(scores[i]), 4)
            })
            if len(results) >= top_k:
                break
        return results

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model_name': self.model_name,
                'job_ids': self.job_ids,
                'embeddings': self.embeddings,
            }, f)
        print(f"向量保存至 {path} (共 {len(self.job_ids)} 条)")

    @classmethod
    def load(cls, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        instance = cls(model_name=data['model_name'])
        instance.job_ids = data['job_ids']
        instance.embeddings = data['embeddings']
        return instance
