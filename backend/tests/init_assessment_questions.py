#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化霍兰德职业兴趣测评题目
使用方法：python init_assessment_questions.py
"""

from db import get_db

def init_questions():
    """初始化 30 道测评题目（每个维度 5 题）"""
    
    questions = [
        # R - 实际型
        ('我喜欢动手操作机械或工具', 'R', 1),
        ('我擅长修理电器或机械设备', 'R', 2),
        ('我喜欢户外活动和体力劳动', 'R', 3),
        ('我愿意学习使用各种仪器设备', 'R', 4),
        ('我喜欢制作手工艺品或模型', 'R', 5),
        
        # I - 研究型
        ('我喜欢思考和分析问题', 'I', 6),
        ('我对科学实验感兴趣', 'I', 7),
        ('我喜欢阅读科技类书籍', 'I', 8),
        ('我愿意深入研究复杂的问题', 'I', 9),
        ('我喜欢独立思考和探索', 'I', 10),
        
        # A - 艺术型
        ('我喜欢绘画、音乐或写作', 'A', 11),
        ('我有较强的创造力和想象力', 'A', 12),
        ('我喜欢欣赏艺术作品', 'A', 13),
        ('我愿意尝试新的创意表达', 'A', 14),
        ('我注重事物的美感和设计', 'A', 15),
        
        # S - 社会型
        ('我喜欢帮助他人解决问题', 'S', 16),
        ('我善于与人沟通和合作', 'S', 17),
        ('我愿意参与志愿服务', 'S', 18),
        ('我喜欢团队工作和社交活动', 'S', 19),
        ('我关心他人的感受和需求', 'S', 20),
        
        # E - 企业型
        ('我喜欢领导和组织活动', 'E', 21),
        ('我善于说服和影响他人', 'E', 22),
        ('我对商业和管理感兴趣', 'E', 23),
        ('我愿意承担风险和挑战', 'E', 24),
        ('我追求成就和地位', 'E', 25),
        
        # C - 常规型
        ('我喜欢按规则和流程做事', 'C', 26),
        ('我注重细节和准确性', 'C', 27),
        ('我擅长整理和归类信息', 'C', 28),
        ('我喜欢稳定的工作环境', 'C', 29),
        ('我善于处理数据和文档', 'C', 30),
    ]
    
    conn = get_db()
    cur = conn.cursor()
    
    # ==============================================
    # 👇 这里是我帮你修改的核心：先清空所有旧题目
    # ==============================================
    cur.execute("DELETE FROM assessment_questions")
    
    # 插入 30 道全新题目
    for question, dimension, sort_order in questions:
        cur.execute('''
            INSERT INTO assessment_questions (question, dimension, sort_order)
            VALUES (?, ?, ?)
        ''', (question, dimension, sort_order))
    
    conn.commit()

    # 验证是否真的插入了30题（可选，很稳）
    cur.execute("SELECT COUNT(*) FROM assessment_questions")
    total = cur.fetchone()[0]
    
    conn.close()
    print(f"✅ 测评题目初始化完成！数据库中总题数：{total}")


if __name__ == '__main__':
    init_questions()