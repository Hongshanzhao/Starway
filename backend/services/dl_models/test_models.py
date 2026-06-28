"""
测试脚本：验证岗位相似度检索和技能标签预测两个模型
运行方式: python -m services.dl_models.test_models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_similarity():
    """测试岗位相似度检索（基于 Word2Vec）"""
    print("=" * 60)
    print("测试: 岗位相似度检索 (Word2Vec)")
    print("=" * 60)

    emb_path = 'data/embeddings/job_vectors_word2vec.pkl'
    if not os.path.exists(emb_path):
        print(f"向量文件不存在: {emb_path}")
        print("请先运行: python -m services.dl_models.train_similarity_word2vec")
        return False

    import pickle
    import numpy as np
    with open(emb_path, 'rb') as f:
        data = pickle.load(f)
    job_ids = data['job_ids']
    vectors = data['vectors']
    id_to_idx = {jid: i for i, jid in enumerate(job_ids)}
    print(f"已加载 {len(job_ids)} 条岗位向量")

    # 测试前3个岗位的相似检索
    for job_id in job_ids[:3]:
        idx = id_to_idx[job_id]
        scores = np.dot(vectors, vectors[idx])
        top_indices = np.argsort(scores)[::-1]
        results = []
        for i in top_indices:
            if i == idx:
                continue
            results.append({
                'job_id': int(job_ids[i]),
                'similarity': round(float(scores[i]), 4)
            })
            if len(results) >= 5:
                break
        print(f"\n与 job_id={job_id} 最相似的岗位:")
        for r in results:
            print(f"  job_id={r['job_id']}, similarity={r['similarity']:.4f}")
        assert len(results) > 0, f"未找到与 {job_id} 相似的岗位"
        assert all('job_id' in r and 'similarity' in r for r in results)

    print("\n岗位相似度检索测试通过!")
    return True


def test_skill_predictor():
    """测试技能标签预测"""
    print("\n" + "=" * 60)
    print("测试: 技能标签预测 (SkillPredictor)")
    print("=" * 60)

    paths = [
        'data/models/skill_predictor.pth',
        'data/models/skill_text_processor.pkl',
        'data/models/skill_label_extractor.pkl',
    ]
    if not all(os.path.exists(p) for p in paths):
        missing = [p for p in paths if not os.path.exists(p)]
        print(f"模型文件缺失: {missing}")
        print("请先运行: python -m services.dl_models.train_skill_predictor")
        return False

    from services.dl_models.skill_predictor_model import SkillPredictor
    predictor = SkillPredictor(*paths)
    print(f"模型已加载，共 {len(predictor.label_extractor.labels)} 个技能标签")

    tests = [
        "负责后端API开发，使用Python Django框架，熟悉MySQL和Redis缓存，有Docker容器化经验",
        "参与产品需求分析和原型设计，协调研发与设计团队，撰写PRD文档",
        "使用React和TypeScript进行前端开发，熟悉Webpack和Node.js，有CI/CD经验",
    ]
    for desc in tests:
        results = predictor.predict(desc, top_k=5)
        print(f"\n描述: {desc[:60]}...")
        for r in results:
            print(f"  {r['skill']}: {r['probability']:.2%}")
        assert len(results) > 0, "预测结果为空"
        assert all('skill' in r and 'probability' in r for r in results)

    print("\n技能标签预测测试通过!")
    return True


def test_api_simulation():
    """模拟 API 调用"""
    print("\n" + "=" * 60)
    print("模拟 API 接口测试")
    print("=" * 60)

    # GET /api/jobs/<job_id>/similar
    print("\n[GET /api/jobs/<job_id>/similar]")
    emb_path = 'data/embeddings/job_vectors_word2vec.pkl'
    if os.path.exists(emb_path):
        import pickle
        import numpy as np
        with open(emb_path, 'rb') as f:
            data = pickle.load(f)
        job_ids = data['job_ids']
        vectors = data['vectors']
        id_to_idx = {jid: i for i, jid in enumerate(job_ids)}
        job_id = job_ids[0]
        idx = id_to_idx[job_id]
        scores = np.dot(vectors, vectors[idx])
        top_indices = np.argsort(scores)[::-1][1:4]
        results = [{'job_id': int(job_ids[i]), 'similarity': round(float(scores[i]), 4)} for i in top_indices]
        resp = {'success': True, 'data': results}
        print(f"  响应: success={resp['success']}, 返回{len(resp['data'])}条")
    else:
        resp = {'success': True, 'data': [], 'message': '模型未生成'}
        print(f"  降级响应: {resp}")

    # POST /api/jobs/skills
    print("\n[POST /api/jobs/skills]")
    model_path = 'data/models/skill_predictor.pth'
    if os.path.exists(model_path):
        from services.dl_models.skill_predictor_model import SkillPredictor
        predictor = SkillPredictor(
            'data/models/skill_predictor.pth',
            'data/models/skill_text_processor.pkl',
            'data/models/skill_label_extractor.pkl',
        )
        results = predictor.predict("Python后端开发，Django框架，MySQL数据库", top_k=5)
        resp = {'success': True, 'data': results}
        print(f"  响应: success={resp['success']}, 返回{len(resp['data'])}条技能")
    else:
        resp = {'success': True, 'data': [], 'message': '模型未训练'}
        print(f"  降级响应: {resp}")

    print("\nAPI 模拟测试通过!")


if __name__ == '__main__':
    print("=" * 60)
    print("  深度学习模型测试")
    print("=" * 60)

    sim_ok = test_similarity()
    skill_ok = test_skill_predictor()

    if sim_ok and skill_ok:
        test_api_simulation()

    print("\n" + "=" * 60)
    if sim_ok and skill_ok:
        print("全部测试通过!")
    else:
        print("部分模型未就绪，请先运行训练脚本:")
        if not sim_ok:
            print("  python -m services.dl_models.train_similarity_word2vec")
        if not skill_ok:
            print("  python -m services.dl_models.train_skill_predictor")
    print("=" * 60)
