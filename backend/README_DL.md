# 深度学习模型说明

## 依赖安装

```bash
pip install sentence-transformers torch jieba scikit-learn matplotlib seaborn tqdm
```

## 模型概览

| 模型 | 类型 | 架构 | 输入 | 输出 |
|------|------|------|------|------|
| 模型一：岗位相似度 | 无监督 | MiniLM-L12-v2 | job_name + job_description | 384维向量 + top-K 相似岗位 |
| 模型二：技能标签预测 | 多标签分类 | TextCNN | job_description | top-5 技能标签 |

---

## 模型一：岗位相似度检索

### 运行训练

```bash
cd backend
python -m services.dl_models.train_similarity
```

### 输出文件

- `data/embeddings/job_embeddings.pkl` — 所有岗位的 384 维向量

### API

```
GET /api/jobs/<job_id>/similar?top_k=10
```

返回示例：
```json
{
  "success": true,
  "data": [
    {"job_id": 123, "similarity": 0.9876},
    {"job_id": 456, "similarity": 0.9543}
  ]
}
```

### 降级处理

模型文件不存在时返回空列表，不会报错。

---

## 模型二：技能标签预测

### 运行训练

```bash
cd backend
python -m services.dl_models.train_skill_predictor
```

### 自动构造标签

训练脚本会自动：
1. 用 jieba 对所有 job_description 分词
2. 过滤非技能停用词
3. 取词频 top-150 作为技能词表

### 输出文件

- `data/models/skill_predictor.pth` — 模型权重
- `data/models/skill_text_processor.pkl` — 分词词表
- `data/models/skill_label_extractor.pkl` — 技能标签词表
- `data/plots/skill_predictor/training_history.png` — Loss/F1 曲线
- `data/plots/skill_predictor/roc_pr_curves.png` — ROC/PR 曲线

### API

```
POST /api/jobs/skills
Content-Type: application/json

{"job_description": "负责后端开发，使用Python和Django框架", "top_k": 5}
```

返回示例：
```json
{
  "success": true,
  "data": [
    {"skill": "python", "probability": 0.9234},
    {"skill": "django", "probability": 0.8765},
    {"skill": "mysql", "probability": 0.8123}
  ]
}
```

### 降级处理

模型文件不存在时返回空列表，不会报错。

---

## 运行测试

```bash
cd backend
python -m services.dl_models.test_models
```

## 文件清单

| 文件 | 说明 |
|------|------|
| `services/dl_models/text_utils.py` | 文本清洗工具 |
| `services/dl_models/job_similarity_model.py` | 相似度模型定义 |
| `services/dl_models/train_similarity.py` | 相似度训练/向量生成 |
| `services/dl_models/skill_predictor_model.py` | 技能预测模型定义 |
| `services/dl_models/train_skill_predictor.py` | 技能预测训练 |
| `services/dl_models/test_models.py` | 测试脚本 |
| `routes/job.py` (末尾追加) | API 端点 |

## 注意事项

- 文本清洗仅在内存中进行，不修改数据库
- 编码器在 CPU 上也可运行（略慢）
- 所有新增文件不覆盖已有文件
- 依赖 `db.get_db()` 连接数据库
