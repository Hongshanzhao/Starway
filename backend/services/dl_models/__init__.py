"""
深度学习模型模块
包含岗位匹配度预测、岗位向量化、岗位相似度检索、技能标签预测模型
"""

from .matching_model import SiameseMatchingNet, TextProcessor, MatchingPredictor
from .job2vec_model import Job2Vec, JobPathRecommender
from .job_similarity_model import JobSimilarityModel
from .skill_predictor_model import SkillTextCNN, SkillPredictor

__all__ = [
    'SiameseMatchingNet',
    'TextProcessor',
    'MatchingPredictor',
    'Job2Vec',
    'JobPathRecommender',
    'JobSimilarityModel',
    'SkillTextCNN',
    'SkillPredictor',
]