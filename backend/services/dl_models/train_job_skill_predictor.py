"""
训练技能标签预测模型（TextCNN 多标签分类）
从 job_description 提取技能标签，训练多标签分类模型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc, precision_recall_curve
import matplotlib.pyplot as plt
from tqdm import tqdm

from db import get_db
from services.dl_models.skill_predictor_model import (SkillTextCNN, SkillTextProcessor,
                                                       SkillLabelExtractor)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class SkillDataset(Dataset):
    def __init__(self, texts, label_vecs, processor):
        self.texts = texts
        self.label_vecs = label_vecs
        self.processor = processor

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        seq = self.processor.text_to_sequence(self.texts[idx])
        return {
            'input': torch.tensor(seq, dtype=torch.long),
            'label': torch.tensor(self.label_vecs[idx], dtype=torch.float32)
        }


def load_data():
    """从数据库加载岗位描述数据"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT job_title AS job_name, job_description
        FROM jobs
        WHERE job_description IS NOT NULL AND job_description != ''
    """)
    rows = cur.fetchall()
    conn.close()

    texts = [f"{row['job_name']} {row['job_description']}" for row in rows]
    print(f"加载 {len(texts)} 条岗位数据")
    return texts


def compute_precision_recall_at_k(y_true, y_probs, ks=[1, 3, 5, 10]):
    """计算 Precision@K 和 Recall@K"""
    results = {}
    for k in ks:
        precisions, recalls = [], []
        for true_vec, prob_vec in zip(y_true, y_probs):
            top_k = prob_vec.argsort()[-k:][::-1]
            num_relevant = true_vec[top_k].sum()
            precisions.append(num_relevant / k)
            total_relevant = true_vec.sum()
            recalls.append(num_relevant / total_relevant if total_relevant > 0 else 0)
        results[f'P@{k}'] = np.mean(precisions)
        results[f'R@{k}'] = np.mean(recalls)
    return results


def plot_roc_curves(y_true, y_probs, label_names, save_dir, top_n=8):
    """绘制主要标签的 ROC 曲线"""
    # 选择样本数最多的标签
    label_counts = y_true.sum(axis=0)
    top_indices = label_counts.argsort()[-top_n:][::-1]

    plt.figure(figsize=(10, 8))
    for idx in top_indices:
        fpr, tpr, _ = roc_curve(y_true[:, idx], y_probs[:, idx])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f'{label_names[idx]} (AUC={roc_auc:.2f})', alpha=0.8)

    plt.plot([0, 1], [0, 1], 'k--', alpha=0.3)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves (Top Labels)')
    plt.legend(fontsize=8, loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'skill_roc_curves.png'), dpi=300)
    plt.close()
    print(f"ROC 曲线保存至 {save_dir}/skill_roc_curves.png")


def plot_history(history, save_dir):
    """绘制训练曲线"""
    epochs = range(1, len(history['train_loss']) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(epochs, history['train_loss'], label='Train Loss', linewidth=2)
    axes[0].plot(epochs, history['val_loss'], label='Val Loss', linewidth=2)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('BCE Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, history['train_f1'], label='Train F1 (Micro)', linewidth=2)
    axes[1].plot(epochs, history['val_f1'], label='Val F1 (Micro)', linewidth=2)
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('F1 Score')
    axes[1].set_title('Training and Validation F1 (Micro)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'skill_predictor_history.png'), dpi=300)
    plt.close()
    print(f"训练曲线保存至 {save_dir}/skill_predictor_history.png")


def train():
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/plots', exist_ok=True)

    # 1. 加载数据
    texts = load_data()

    # 2. 构建技能标签
    label_extractor = SkillLabelExtractor(max_labels=150)
    label_extractor.build_labels(texts)
    label_extractor.save('data/models/skill_label_extractor.pkl')

    # 3. 构建词表
    processor = SkillTextProcessor(vocab_size=10000, max_len=128)
    processor.build_vocab(texts)
    processor.save('data/models/skill_processor.pkl')

    # 4. 生成多标签向量
    label_vecs = np.array([label_extractor.encode_labels(t) for t in texts])
    positive_ratio = label_vecs.sum() / (label_vecs.shape[0] * label_vecs.shape[1])
    print(f"标签矩阵: {label_vecs.shape}, 正样本比例: {positive_ratio:.4f}")

    # 过滤没有任何标签的样本
    valid_mask = label_vecs.sum(axis=1) > 0
    texts = [t for t, m in zip(texts, valid_mask) if m]
    label_vecs = label_vecs[valid_mask]
    print(f"过滤后有效样本: {len(texts)}")

    # 5. 划分数据集
    X_train, X_val, y_train, y_val = train_test_split(
        texts, label_vecs, test_size=0.2, random_state=42
    )
    print(f"训练集: {len(X_train)}, 验证集: {len(X_val)}")

    train_ds = SkillDataset(X_train, y_train, processor)
    val_ds = SkillDataset(X_val, y_val, processor)
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    # 6. 模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    num_labels = len(label_extractor.labels)
    model = SkillTextCNN(vocab_size=len(processor.word2idx), num_labels=num_labels,
                         embed_dim=128, num_filters=100, dropout=0.4)
    model.to(device)

    # 处理标签不平衡：pos_weight
    pos_counts = y_train.sum(axis=0)
    neg_counts = len(y_train) - pos_counts
    pos_weight = torch.tensor(
        [(neg / max(pos, 1)) for pos, neg in zip(pos_counts, neg_counts)],
        dtype=torch.float32
    ).to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, 'min', patience=3, factor=0.5
    )

    # 7. 训练
    history = {'train_loss': [], 'val_loss': [], 'train_f1': [], 'val_f1': []}
    best_loss = float('inf')
    epochs = 25

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        all_train_probs, all_train_labels = [], []
        for batch in tqdm(train_loader, desc=f'Epoch {epoch+1}/{epochs}', leave=False):
            inputs = batch['input'].to(device)
            labels = batch['label'].to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            all_train_probs.append(torch.sigmoid(outputs).detach().cpu().numpy())
            all_train_labels.append(labels.cpu().numpy())

        model.eval()
        val_loss = 0
        all_val_probs, all_val_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                inputs = batch['input'].to(device)
                labels = batch['label'].to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                all_val_probs.append(torch.sigmoid(outputs).cpu().numpy())
                all_val_labels.append(labels.cpu().numpy())

        train_loss /= len(train_loader)
        val_loss /= len(val_loader)

        # 计算 Micro F1 (threshold=0.5)
        tp = np.vstack(all_train_probs)
        tl = np.vstack(all_train_labels)
        vp = np.vstack(all_val_probs)
        vl = np.vstack(all_val_labels)

        train_pred_bin = (tp >= 0.5).astype(int)
        val_pred_bin = (vp >= 0.5).astype(int)

        train_tp = (train_pred_bin & tl.astype(bool)).sum()
        train_fp = (train_pred_bin & ~tl.astype(bool)).sum()
        train_fn = (~train_pred_bin & tl.astype(bool)).sum()
        train_f1 = 2 * train_tp / (2 * train_tp + train_fp + train_fn + 1e-8)

        val_tp = (val_pred_bin & vl.astype(bool)).sum()
        val_fp = (val_pred_bin & ~vl.astype(bool)).sum()
        val_fn = (~val_pred_bin & vl.astype(bool)).sum()
        val_f1 = 2 * val_tp / (2 * val_tp + val_fp + val_fn + 1e-8)

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_f1'].append(train_f1)
        history['val_f1'].append(val_f1)

        # Precision@K / Recall@K
        pk = compute_precision_recall_at_k(vl, vp)
        print(f"Epoch {epoch+1:2d} | Train Loss {train_loss:.4f} F1 {train_f1:.3f} | "
              f"Val Loss {val_loss:.4f} F1 {val_f1:.3f} | "
              f"P@1={pk['P@1']:.3f} P@5={pk['P@5']:.3f} R@5={pk['R@5']:.3f}")

        scheduler.step(val_loss)
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), 'data/models/skill_predictor.pth')

    # 8. 最终评估
    print("\n=== 最终评估 ===")
    final_pk = compute_precision_recall_at_k(vl, vp, ks=[1, 3, 5, 10])
    for k, v in final_pk.items():
        print(f"  {k}: {v:.4f}")

    # 绘制 ROC 曲线
    plot_roc_curves(vl, vp, label_extractor.labels, 'data/plots')
    plot_history(history, 'data/plots')

    print("训练完成！")


if __name__ == '__main__':
    train()
