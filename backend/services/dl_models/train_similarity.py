"""
训练脚本：为所有岗位生成 sentence-transformers 向量并保存
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_db
from services.dl_models.text_utils import clean_text, is_valid_text
from services.dl_models.job_similarity_model import JobSimilarityModel


def load_jobs_from_db():
    """从数据库加载岗位数据（仅内存清洗，不写回）"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT rowid AS id, job_title AS job_name, job_description
        FROM jobs
        WHERE job_title IS NOT NULL AND job_title != ''
    """)
    rows = cur.fetchall()
    conn.close()

    job_ids = []
    job_texts = []
    skipped = 0
    for row in rows:
        desc = row['job_description'] or ''
        # 拼接岗位名称 + 清洗后描述前200字
        desc_clean = clean_text(desc)
        combined = f"{row['job_name']} {desc_clean[:200]}".strip()
        if len(combined) < 5:
            skipped += 1
            continue
        job_ids.append(row['id'])
        job_texts.append(combined)

    if skipped:
        print(f"跳过了 {skipped} 条文本过短的岗位")
    print(f"加载 {len(job_ids)} 条有效岗位数据")
    return job_ids, job_texts


def main():
    os.makedirs('data/embeddings', exist_ok=True)

    job_ids, job_texts = load_jobs_from_db()

    model = JobSimilarityModel()
    model.encode_jobs(job_texts, job_ids)
    model.save('data/embeddings/job_embeddings.pkl')

    # 快速测试
    if job_ids:
        sample_id = job_ids[0]
        results = model.search_similar(sample_id, top_k=5)
        print(f"\n测试：与岗位 {sample_id} 最相似的5个岗位:")
        for r in results:
            print(f"  job_id={r['job_id']}, similarity={r['similarity']:.4f}")

    print("训练完成！")


if __name__ == '__main__':
    main()
