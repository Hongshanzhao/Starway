"""
高级算法与大模型封装（以类形式实现，提供降级回退以保证可运行）
本文件夹下的代码皆为临时所用，现只做历史保留
包含：
- CareerRecommend: TF-IDF + 余弦相似度（技能/岗位匹配）+ 多目标加权（技能 0.7 / 城市 0.3）
- CareerPathPredict: 简单 HMM/马尔可夫链训练与预测（训练为统计频次）
- ResumeAnalysis: 基于 spaCy/正则的实体抽取与 Excel 简历解析
- TrendAnalysis: Prophet or 线性回归 + KMeans 职业聚类

实现原则：尝试导入可用的 ML 库（scikit-learn, pandas, spacy, prophet），若不存在则使用轻量回退实现。
"""
from typing import List, Dict, Any, Tuple, Optional
import math
import re
import statistics

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    from sklearn.linear_model import LinearRegression
except Exception:
    np = None
    TfidfVectorizer = None
    cosine_similarity = None
    KMeans = None
    LinearRegression = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import spacy
    _nlp = spacy.load('en_core_web_sm') if 'en_core_web_sm' in spacy.util.get_installed_models() else None
except Exception:
    spacy = None
    _nlp = None


class CareerRecommend:
    """职业推荐：TF-IDF + 余弦相似度，技能占比 0.7，城市/地点占比 0.3

    方法：get_match_list(user_features, job_list)
    user_features 示例：{'skills': ['python','sql'], 'interests':[], 'location':'北京'}
    job_list 示例：[{ 'job_name':..., 'skills': [...], 'job_description': ..., 'location': '北京' }, ...]
    """

    def __init__(self):
        self.vectorizer = None

    def _text_from_job(self, job: Dict[str, Any]) -> str:
        parts = []
        if job.get('job_name'):
            parts.append(str(job.get('job_name')))
        if job.get('job_description'):
            parts.append(str(job.get('job_description')))
        if job.get('skills'):
            parts.append(' '.join(job.get('skills') if isinstance(job.get('skills'), list) else [str(job.get('skills'))]))
        return ' '.join(parts)

    def get_match_list(self, user: Dict[str, Any], jobs: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        # 构造用户文本
        user_text = ' '.join((user.get('skills') or []) + (user.get('interests') or []))
        job_texts = [self._text_from_job(j) for j in jobs]

        # 若 sklearn 可用，使用 TF-IDF
        if TfidfVectorizer is not None and cosine_similarity is not None:
            corpus = [user_text] + job_texts
            try:
                vec = TfidfVectorizer(ngram_range=(1,2), max_features=2000)
                X = vec.fit_transform(corpus)
                user_vec = X[0]
                job_vecs = X[1:]
                sims = cosine_similarity(user_vec, job_vecs)[0]
            except Exception:
                sims = [0.0] * len(jobs)
        else:
            # 回退：基于技能重叠率
            user_skills = set([s.lower() for s in (user.get('skills') or [])])
            sims = []
            for j in jobs:
                js = set([s.lower() for s in (j.get('skills') or [])])
                if not js:
                    sims.append(0.0)
                    continue
                sims.append(len(user_skills & js) / max(1, len(js)))

        # 结合城市加权
        out = []
        for idx, j in enumerate(jobs):
            skill_score = float(sims[idx])
            city_score = 1.0 if (str(user.get('location') or '').strip() and str(user.get('location') or '').strip() == str(j.get('location') or '').strip()) else 0.0
            final = 0.7 * skill_score + 0.3 * city_score
            out.append({'job': j, 'score': round(float(final), 4), 'skill_score': round(float(skill_score),4), 'city_score': city_score})

        out.sort(key=lambda x: x['score'], reverse=True)
        return out[:top_k]


class CareerPathPredict:
    """职业路径预测：基于历史状态序列的马尔可夫链训练与预测（降级实现）

    用法：train_model(history_sequences)，predict_next_state(current_sequence)
    history_sequences 示例：[['实习','初级','中级'], ['实习','初级']]
    """

    def __init__(self):
        self.transitions = {}

    def train_model(self, sequences: List[List[str]]):
        for seq in sequences:
            for a, b in zip(seq, seq[1:]):
                self.transitions.setdefault(a, {})
                self.transitions[a][b] = self.transitions[a].get(b, 0) + 1
        # 转换为概率
        for a, nxt in self.transitions.items():
            total = sum(nxt.values())
            for b in nxt:
                nxt[b] = nxt[b] / total

    def predict_next_state(self, current_sequence: List[str], top_k: int = 3) -> List[Tuple[str, float]]:
        if not current_sequence:
            return []
        last = current_sequence[-1]
        nxt = self.transitions.get(last, {})
        if not nxt:
            return []
        arr = sorted(nxt.items(), key=lambda x: x[1], reverse=True)
        return arr[:top_k]


class ResumeAnalysis:
    """简历分析：尝试使用 spaCy/NLP 提取实体，否则使用正则与关键词表回退"""

    COMMON_SKILLS = ['python','java','sql','excel','tensorflow','pytorch','c++','linux']

    def __init__(self):
        self.nlp = _nlp

    def extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {'skills': [], 'positions': [], 'edu': []}
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_.lower() in ('skill', 'technology'):
                    entities['skills'].append(ent.text)
                if ent.label_.lower() in ('org', 'position', 'title'):
                    entities['positions'].append(ent.text)
        else:
            # 简单正则：匹配常见技能关键词
            txt = text.lower()
            for sk in self.COMMON_SKILLS:
                if sk in txt and sk not in entities['skills']:
                    entities['skills'].append(sk)
            # 职位抽取：查找 '担任|任职' 后的若干词
            m = re.findall(r'(?:担任|任职|职位：)\s*([\u4e00-\u9fff\w\- ]{2,30})', text)
            entities['positions'].extend(m)

        return entities

    def parse_excel_resume(self, path: str) -> Dict[str, Any]:
        if pd is None:
            return {'error': 'pandas not installed'}
        try:
            df = pd.read_excel(path)
            # 尝试找到技能列
            skills = []
            for col in df.columns:
                if 'skill' in col.lower() or '技能' in col:
                    vals = df[col].dropna().astype(str).tolist()
                    for v in vals:
                        skills.extend([s.strip() for s in v.split(',') if s.strip()])
            return {'skills': list(set(skills)), 'raw': df.to_dict(orient='records')}
        except Exception as e:
            return {'error': str(e)}


class TrendAnalysis:
    """趋势分析：薪资预测（Prophet/线性回归回退）与职业聚类（KMeans 回退）"""

    def predict_salary_trend(self, dates: List[str], values: List[float], periods: int = 12) -> Dict[str, Any]:
        # 降级：用线性回归预测未来均值
        if LinearRegression is not None and np is not None:
            try:
                X = np.arange(len(values)).reshape(-1,1)
                y = np.array(values)
                model = LinearRegression().fit(X, y)
                future_x = np.arange(len(values), len(values)+periods).reshape(-1,1)
                preds = model.predict(future_x).tolist()
                return {'predictions': preds}
            except Exception:
                pass
        # 简单回退：延用均值
        avg = statistics.mean(values) if values else 0
        return {'predictions': [avg for _ in range(periods)]}

    def cluster_career(self, jobs: List[Dict[str, Any]], k: int = 5) -> Dict[str, Any]:
        texts = [ (j.get('job_name') or '') + ' ' + (j.get('industry') or '') for j in jobs]
        if TfidfVectorizer is not None and KMeans is not None:
            try:
                vec = TfidfVectorizer(max_features=1000)
                X = vec.fit_transform(texts)
                km = KMeans(n_clusters=min(k, max(1, len(jobs))))
                labels = km.fit_predict(X)
                clusters = {}
                for i, lab in enumerate(labels):
                    clusters.setdefault(int(lab), []).append(jobs[i])
                return {'clusters': clusters}
            except Exception:
                pass
        # 回退：按 industry 分组
        clusters = {}
        for j in jobs:
            key = j.get('industry') or '其他'
            clusters.setdefault(key, []).append(j)
        return {'clusters': clusters}


__all__ = ['CareerRecommend', 'CareerPathPredict', 'ResumeAnalysis', 'TrendAnalysis']
