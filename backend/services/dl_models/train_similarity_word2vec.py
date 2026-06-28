"""
基于 Word2Vec 的岗位相似度模型（轻量、无需下载外部模型）
============================================================
原理：
  1. 将每个岗位名称视为一个"句子"，分词后训练 Word2Vec 得到每个词的向量
  2. 对每个岗位，将其包含的所有词的向量取平均，作为该岗位的向量表示
  3. 用余弦相似度计算岗位之间的相似度

优点：
  - 完全离线，无需下载任何预训练模型
  - 轻量快速，2 分钟内完成全流程
  - 效果优于 TF-IDF（能捕捉语义相似性）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np
import pickle
import random
import re
from collections import defaultdict

from db import get_db
from services.dl_models.text_utils import clean_text

# ============================================================================
# 依赖检查（友好提示）
# ============================================================================

_MISSING = []

try:
    import jieba
except ImportError:
    _MISSING.append("jieba")

try:
    from gensim.models import Word2Vec
except ImportError:
    _MISSING.append("gensim")

try:
    from sklearn.manifold import TSNE
except ImportError:
    _MISSING.append("scikit-learn")

try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端，无需 GUI
    import matplotlib.pyplot as plt
except ImportError:
    _MISSING.append("matplotlib")

# 中文字体设置（在导入 pyplot 之后）
if 'matplotlib' not in _MISSING:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei',
                                        'PingFang SC', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

if _MISSING:
    print(f"缺少依赖包: {', '.join(_MISSING)}")
    print(f"请运行: pip install {' '.join(_MISSING)}")
    sys.exit(1)


# ============================================================================
# 1. 数据加载与分词
# ============================================================================

def load_and_tokenize():
    """
    从数据库读取所有岗位名称，清洗后分词。
    保留所有记录（不去重），重复数据有助于 Word2Vec 训练。

    返回:
      job_ids:   list[int]   岗位 rowid 列表
      tokenized: list[list[str]]  每个岗位的分词列表
      raw_names: list[str]   清洗后的原始名称（用于显示）
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT rowid as id, job_name
        FROM job
        WHERE job_name IS NOT NULL AND job_name != ''
    """)
    rows = cur.fetchall()
    conn.close()

    job_ids = []
    tokenized = []
    raw_names = []

    for row in rows:
        # 文本清洗：去 HTML、特殊符号，保留中文/英文/数字
        name = clean_text(row['job_name'])
        if not name or len(name) < 2:
            continue

        # jieba 分词（精确模式）
        words = jieba.lcut(name)
        # 过滤空白词和单字符
        words = [w.strip() for w in words if w.strip() and len(w.strip()) >= 1]

        if words:  # 至少有一个有效词
            job_ids.append(row['id'])
            tokenized.append(words)
            raw_names.append(name)

    print(f"加载 {len(job_ids)} 条岗位数据，已清洗并分词")
    # 打印几条示例
    for i in range(min(5, len(tokenized))):
        print(f"  示例 {i+1}: {raw_names[i]} → {tokenized[i]}")
    return job_ids, tokenized, raw_names


# ============================================================================
# 2. 训练 Word2Vec
# ============================================================================

def train_word2vec(sentences, vector_size=100, window=5, min_count=2, workers=4, epochs=30):
    """
    训练 Word2Vec 模型（Skip-gram 算法）。

    参数:
      sentences:   分词后的句子列表
      vector_size: 词向量维度（默认 100）
      window:      上下文窗口大小
      min_count:   最低词频阈值，出现次数少于此值的词会被忽略
      workers:     并行训练的线程数
      epochs:      训练轮数

    返回:
      训练好的 Word2Vec 模型
    """
    print(f"\n开始训练 Word2Vec（vector_size={vector_size}, window={window}, "
          f"min_count={min_count}, epochs={epochs}）...")

    model = Word2Vec(
        sentences=sentences,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        workers=workers,
        sg=1,         # Skip-gram（对低频词效果更好）
        hs=0,         # 使用负采样而非层次 softmax
        negative=5,   # 负采样数量
        epochs=epochs,
        seed=42,
    )

    # 打印词表信息
    print(f"训练完成。词表大小: {len(model.wv)}, 向量维度: {model.wv.vector_size}")
    print(f"词表示例（前15个）: {list(model.wv.index_to_key[:15])}")

    # 快速测试：查找与某个词最相似的词
    if len(model.wv.index_to_key) > 0:
        test_word = model.wv.index_to_key[0]
        try:
            similar = model.wv.most_similar(test_word, topn=5)
            print(f"与 '{test_word}' 最相似的词: {similar}")
        except KeyError:
            pass

    return model


# ============================================================================
# 3. 计算岗位向量（词向量平均）
# ============================================================================

def compute_job_vectors(model, tokenized, job_ids):
    """
    对每个岗位，将其包含的所有词的 Word2Vec 向量取平均，
    得到该岗位的向量表示。如果某个岗位的所有词都不在词表中，则用零向量。

    返回:
      valid_ids:   list[int]  有效岗位的 id
      valid_vecs:  np.ndarray (n_valid, vector_size)
      valid_names: list[str]  有效岗位的岗位名称
    """
    vec_dim = model.wv.vector_size
    vectors = np.zeros((len(tokenized), vec_dim), dtype=np.float32)
    valid_mask = []

    for i, words in enumerate(tokenized):
        word_vecs = []
        for w in words:
            if w in model.wv:
                word_vecs.append(model.wv[w])
        if word_vecs:
            vectors[i] = np.mean(word_vecs, axis=0)
            valid_mask.append(True)
        else:
            valid_mask.append(False)

    n_valid = sum(valid_mask)
    print(f"\n计算岗位向量: {n_valid}/{len(tokenized)} 个岗位有有效向量")

    # 过滤掉无效的
    valid_ids = [jid for jid, ok in zip(job_ids, valid_mask) if ok]
    valid_vecs = vectors[valid_mask]

    # L2 归一化，便于后续用点积计算余弦相似度
    norms = np.linalg.norm(valid_vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-8, norms)
    valid_vecs = valid_vecs / norms

    return valid_ids, valid_vecs


# ============================================================================
# 4. 相似度检索
# ============================================================================

def cosine_similarity_search(query_idx, vectors, job_ids, raw_names, top_k=5):
    """
    计算 query 岗位与所有岗位的余弦相似度，返回 top_k 个最相似的
    **不同岗位名称**。

    参数:
      query_idx: 查询岗位在 vectors 数组中的索引
      vectors:   已归一化的岗位向量矩阵
      job_ids:   岗位 id 列表
      raw_names: 岗位原始名称列表（用于去重）
      top_k:     返回前 k 个不同的岗位名称

    返回:
      list[dict]: [{'job_id': int, 'similarity': float}, ...]
    """
    query_vec = vectors[query_idx]
    # 向量已 L2 归一化，点积即余弦相似度
    scores = np.dot(vectors, query_vec)

    # 按相似度降序排列
    top_indices = np.argsort(scores)[::-1]
    results = []
    seen_names = {raw_names[query_idx]}  # 排除自身（用名称匹配，而非索引）
    for idx in top_indices:
        name = raw_names[idx]
        if name in seen_names:
            continue
        seen_names.add(name)
        results.append({
            'job_id': int(job_ids[idx]),
            'similarity': round(float(scores[idx]), 4)
        })
        if len(results) >= top_k:
            break
    return results


# ============================================================================
# 5. t-SNE 可视化
# ============================================================================

def plot_tsne(vectors, raw_names, max_points=500, save_path=None):
    """
    用 t-SNE 将岗位向量降维到 2D，绘制散点图。
    按岗位名称去重后再绘图，避免同一个点重复出现。

    参数:
      vectors:    岗位向量矩阵（全量，含重复）
      raw_names:  岗位原始名称列表
      max_points: 最多显示的点数（避免过于拥挤）
      save_path:  图片保存路径
    """
    if save_path is None:
        save_path = 'data/plots/similarity_word2vec_tsne.png'

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 按岗位名称去重，每个岗位只保留第一个出现的向量
    seen = set()
    dedup_indices = []
    for i, name in enumerate(raw_names):
        if name not in seen:
            seen.add(name)
            dedup_indices.append(i)
    dedup_vecs = vectors[dedup_indices]
    dedup_names = [raw_names[i] for i in dedup_indices]
    print(f"t-SNE: 岗位名称去重后 {len(dedup_indices)} 个（原始 {len(raw_names)} 条）")

    # 限制点数
    n = min(len(dedup_vecs), max_points)
    if n < len(dedup_vecs):
        indices = np.random.choice(len(dedup_vecs), n, replace=False)
        sub_vecs = dedup_vecs[indices]
        sub_names = [dedup_names[i] for i in indices]
    else:
        sub_vecs = dedup_vecs
        sub_names = dedup_names

    print(f"正在进行 t-SNE 降维（{n} 个点）...")
    perplexity = min(30, n - 1) if n > 1 else 1
    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity,
                max_iter=1000, metric='cosine')
    reduced = tsne.fit_transform(sub_vecs)

    # 绘制
    fig, ax = plt.subplots(figsize=(16, 12))
    scatter = ax.scatter(reduced[:, 0], reduced[:, 1],
                         c=range(n), cmap='tab20', alpha=0.7, s=30)

    # 只标注部分点（避免文字重叠）
    label_step = max(1, n // 40)  # 大约标注 40 个点
    for i in range(0, n, label_step):
        ax.annotate(sub_names[i], (reduced[i, 0], reduced[i, 1]),
                    fontsize=6, alpha=0.8,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow',
                              alpha=0.3, edgecolor='none'))

    ax.set_title('Job2Vec t-SNE 岗位向量分布 (Word2Vec + 词向量平均)',
                 fontsize=14)
    ax.set_xlabel('Dimension 1')
    ax.set_ylabel('Dimension 2')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"t-SNE 图已保存至 {save_path}")


# ============================================================================
# 6. 相似度热力图（按岗位名称去重）
# ============================================================================

def plot_similarity_heatmap(vectors, raw_names, top_n=15,
                            save_path='data/plots/similarity_word2vec_heatmap.png'):
    """
    绘制部分岗位的相似度矩阵热力图。
    按岗位名称去重后取前 top_n 个不同岗位。

    参数:
      vectors:   岗位向量矩阵（全量，含重复）
      raw_names: 岗位原始名称
      top_n:     展示前 N 个不同岗位
      save_path: 保存路径
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 按岗位名称去重，每个岗位只保留第一个
    seen = set()
    dedup_indices = []
    for i, name in enumerate(raw_names):
        if name not in seen:
            seen.add(name)
            dedup_indices.append(i)

    n = min(len(dedup_indices), top_n)
    use_indices = dedup_indices[:n]
    sub_vecs = vectors[use_indices]
    sub_names = [raw_names[i] for i in use_indices]

    sim_matrix = np.dot(sub_vecs, sub_vecs.T)  # 余弦相似度矩阵

    fig, ax = plt.subplots(figsize=(12, 10))
    # 截断名称长度以便显示
    short_names = [name[:12] + '..' if len(name) > 12 else name
                   for name in sub_names]

    im = ax.imshow(sim_matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(short_names, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(short_names, fontsize=8)
    ax.set_title(f'Job Similarity Matrix (top {n} unique jobs)', fontsize=14)
    plt.colorbar(im, ax=ax, label='Cosine Similarity')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"相似度热力图已保存至 {save_path}")


# ============================================================================
# 7. 保存模型
# ============================================================================

def save_artifacts(model, job_ids, vectors, raw_names,
                   emb_dir='data/embeddings'):
    """
    持久化 Word2Vec 模型和岗位向量。

    保存内容：
      - data/embeddings/word2vec_model.pkl  (gensim Word2Vec 模型)
      - data/embeddings/job_vectors_word2vec.pkl  (job_id, vectors, raw_names)
    """
    os.makedirs(emb_dir, exist_ok=True)

    # 保存 gensim 模型
    model_path = os.path.join(emb_dir, 'word2vec_model.pkl')
    model.save(model_path)
    print(f"Word2Vec 模型保存至 {model_path}")

    # 保存岗位向量
    vec_path = os.path.join(emb_dir, 'job_vectors_word2vec.pkl')
    with open(vec_path, 'wb') as f:
        pickle.dump({
            'job_ids': job_ids,
            'vectors': vectors,
            'raw_names': raw_names,
        }, f)
    print(f"岗位向量保存至 {vec_path} (共 {len(job_ids)} 条)")


# ============================================================================
# 主流程
# ============================================================================

def main():
    os.makedirs('data/embeddings', exist_ok=True)
    os.makedirs('data/plots', exist_ok=True)

    # Step 1: 加载数据并分词（保留所有记录，不去重）
    print("=" * 60)
    print("Step 1: 加载岗位数据并分词")
    print("=" * 60)
    job_ids, tokenized, raw_names = load_and_tokenize()

    # Step 2: 训练 Word2Vec
    print("\n" + "=" * 60)
    print("Step 2: 训练 Word2Vec 模型")
    print("=" * 60)
    model = train_word2vec(tokenized)

    # Step 3: 计算岗位向量
    print("\n" + "=" * 60)
    print("Step 3: 计算岗位向量（词向量平均）")
    print("=" * 60)
    valid_ids, vectors = compute_job_vectors(model, tokenized, job_ids)
    # raw_names 与 vectors 一一对应（compute_job_vectors 不过滤名称）
    valid_names = raw_names

    # Step 4: 随机测试 3 个岗位的相似度检索（按名称去重后输出）
    print("\n" + "=" * 60)
    print("Step 4: 相似度检索测试（按岗位名称去重）")
    print("=" * 60)
    rng = random.Random(42)
    test_indices = rng.sample(range(len(valid_ids)), min(3, len(valid_ids)))
    for idx in test_indices:
        results = cosine_similarity_search(idx, vectors, valid_ids, valid_names, top_k=5)
        print(f"\n查询岗位: {valid_names[idx]} (id={valid_ids[idx]})")
        for r in results:
            # 找到结果对应的岗位名称
            result_name = valid_names[valid_ids.index(r['job_id'])]
            print(f"  → {result_name} "
                  f"(id={r['job_id']}, sim={r['similarity']:.4f})")

    # Step 5: t-SNE 可视化（按岗位名称去重后绘图）
    print("\n" + "=" * 60)
    print("Step 5: t-SNE 可视化")
    print("=" * 60)
    plot_tsne(vectors, valid_names)

    # Step 6: 相似度热力图（按岗位名称去重）
    print("\n" + "=" * 60)
    print("Step 6: 相似度热力图")
    print("=" * 60)
    plot_similarity_heatmap(vectors, valid_names)

    # Step 7: 保存模型
    print("\n" + "=" * 60)
    print("Step 7: 保存模型产物")
    print("=" * 60)
    save_artifacts(model, valid_ids, vectors, valid_names)

    print("\n" + "=" * 60)
    print("全部完成！")
    print(f"  - 岗位记录数: {len(valid_ids)}")
    print(f"  - 不重复岗位名称数: {len(set(valid_names))}")
    print(f"  - 向量维度: {model.wv.vector_size}")
    print(f"  - t-SNE 图: data/plots/similarity_word2vec_tsne.png")
    print(f"  - 热力图:   data/plots/similarity_word2vec_heatmap.png")
    print(f"  - 向量文件: data/embeddings/job_vectors_word2vec.pkl")
    print("=" * 60)


if __name__ == '__main__':
    main()
