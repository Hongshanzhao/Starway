"""
利用 job 表和分类信息训练 Word2Vec（去重 + 中文显示修复）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_db
from services.dl_models.job2vec_model import Job2Vec
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import numpy as np
import random

# ========== 修复 matplotlib 中文显示 ==========
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Arial Unicode MS']  # 支持中文
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def build_sequences():
    """
    构造训练序列（自动去重）
    1. 每个岗位大类下的所有岗位名称构成一个序列（去重）
    2. 从 job_relations 表中提取已有的晋升/转型路径作为序列
    """
    conn = get_db()
    cur = conn.cursor()
    sequences = []

    # 方法1：同一大类下的岗位名列表（去重）
    cur.execute("SELECT id, name FROM job_categories")
    categories = cur.fetchall()
    for cat in categories:
        cur.execute("SELECT job_name FROM job WHERE category_id=? AND job_name IS NOT NULL", (cat['id'],))
        jobs = [row['job_name'] for row in cur.fetchall()]
        if len(jobs) >= 2:
            # 去重（保持原有顺序）
            unique_jobs = list(dict.fromkeys(jobs))
            # 可选：随机打乱顺序增加多样性
            random.shuffle(unique_jobs)
            sequences.append(unique_jobs)

    # 方法2：已有的 job_relations 中的路径（promotion 或 transition）
    cur.execute("SELECT from_job, to_job FROM job_relations WHERE relation_type IN ('promotion', 'transition')")
    for row in cur.fetchall():
        sequences.append([row['from_job'], row['to_job']])

    conn.close()

    # 保底序列（仅当上面构造的序列不足 10 条时使用）
    if len(sequences) < 10:
        print("⚠️ 从数据库构造的序列不足10条，使用通用保底序列（仅供演示）")
        fallback = [
            ['工程师', '高级工程师', '技术专家'],
            ['产品专员', '产品经理', '产品总监'],
            ['设计师', 'UI设计师', '设计主管'],
            ['测试工程师', '测试经理'],
            ['运维工程师', '运维经理'],
        ]
        sequences.extend(fallback)

    print(f"✅ 构造了 {len(sequences)} 条职位序列")
    # 打印前3条示例（只显示前5个元素）
    for i, seq in enumerate(sequences[:3]):
        sample = seq[:5] + (['...'] if len(seq) > 5 else [])
        print(f"   示例{i+1}: {sample}")
    return sequences

def train():
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/plots', exist_ok=True)

    sequences = build_sequences()
    if not sequences:
        print("❌ 没有构造出任何序列，无法训练")
        return

    model = Job2Vec(embedding_dim=64, window_size=2, learning_rate=0.01)
    model.train(sequences, epochs=30, batch_size=8)
    model.save('data/models/job2vec_model.pkl')

    # t-SNE 可视化（只显示前50个岗位）
    job_names = list(model.job2id.keys())[:50]
    if len(job_names) < 2:
        print("⚠️ 词表中的岗位不足2个，无法进行 t-SNE 可视化")
        return

    vecs = np.array([model.embeddings[model.job2id[j]] for j in job_names])
    perplexity = min(30, len(job_names) - 1)
    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
    reduced = tsne.fit_transform(vecs)

    plt.figure(figsize=(14, 10))
    # 用颜色映射区分不同点（可选）
    plt.scatter(reduced[:, 0], reduced[:, 1], c=range(len(job_names)), cmap='tab20', alpha=0.7)
    for i, name in enumerate(job_names):
        plt.annotate(name, (reduced[i, 0], reduced[i, 1]), fontsize=8, alpha=0.8)
    plt.title('Job2Vec t-SNE Visualization (岗位向量分布)', fontsize=14)
    plt.xlabel('Dimension 1')
    plt.ylabel('Dimension 2')
    plt.tight_layout()
    plt.savefig('data/plots/job2vec_tsne.png', dpi=300)
    plt.close()
    print("✅ Job2Vec 训练完成，模型和 t-SNE 图已保存至 data/plots/job2vec_tsne.png")

if __name__ == '__main__':
    train()