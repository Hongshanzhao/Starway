"""
训练脚本：岗位技能标签预测模型（TextCNN 多标签分类）
自动构造标签、训练、生成评估曲线
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import matplotlib.pyplot as plt
from tqdm import tqdm

from db import get_db
from services.dl_models.text_utils import clean_text
from services.dl_models.skill_predictor_model import (
    SkillLabelExtractor, SkillTextProcessor, SkillTextCNN
)

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
        return (
            torch.tensor(seq, dtype=torch.long),
            torch.tensor(self.label_vecs[idx], dtype=torch.float32)
        )


def load_data():
    """从数据库加载并清洗岗位数据"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT job_name, job_description
        FROM job
        WHERE job_description IS NOT NULL AND job_description != ''
    """)
    rows = cur.fetchall()
    conn.close()

    texts = []
    for row in rows:
        desc = clean_text(row['job_description'] or '')
        combined = f"{row['job_name']} {desc[:200]}".strip()
        if len(combined) >= 5:
            texts.append(combined)

    print(f"加载 {len(texts)} 条有效岗位数据")
    return texts


def plot_training_curves(history, save_dir):
    epochs = range(1, len(history['train_loss']) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(epochs, history['train_loss'], 'b-', label='Train Loss', linewidth=2)
    axes[0].plot(epochs, history['val_loss'], 'r-', label='Val Loss', linewidth=2)
    axes[0].set_xlabel('Epoch'); axes[0].set_ylabel('BCE Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, history['train_f1'], 'b-', label='Train F1', linewidth=2)
    axes[1].plot(epochs, history['val_f1'], 'r-', label='Val F1', linewidth=2)
    axes[1].set_xlabel('Epoch'); axes[1].set_ylabel('Micro F1')
    axes[1].set_title('Training and Validation F1')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'training_history.png'), dpi=300)
    plt.close()


def plot_roc_and_pr(val_labels, val_probs, label_names, save_dir):
    """绘制微平均 ROC 和 PR 曲线，以及 top-8 标签的独立曲线"""
    n_labels = val_labels.shape[1]

    # Micro-average ROC
    fpr_micro, tpr_micro, _ = roc_curve(val_labels.ravel(), val_probs.ravel())
    auc_micro = auc(fpr_micro, tpr_micro)

    # Top labels by sample count
    label_counts = val_labels.sum(axis=0)
    top_indices = label_counts.argsort()[-8:][::-1]

    # ROC
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    axes[0].plot(fpr_micro, tpr_micro, 'k-', lw=2,
                 label=f'Micro-average (AUC={auc_micro:.3f})')
    for idx in top_indices:
        fpr, tpr, _ = roc_curve(val_labels[:, idx], val_probs[:, idx])
        axes[0].plot(fpr, tpr, alpha=0.6, label=f'{label_names[idx]}')
    axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.3)
    axes[0].set_xlabel('FPR'); axes[0].set_ylabel('TPR')
    axes[0].set_title('ROC Curves'); axes[0].legend(fontsize=7)

    # Precision-Recall
    ap_micro = average_precision_score(val_labels, val_probs, average='micro')
    precision, recall, _ = precision_recall_curve(val_labels.ravel(), val_probs.ravel())
    axes[1].plot(recall, precision, 'k-', lw=2,
                 label=f'Micro-average (AP={ap_micro:.3f})')
    for idx in top_indices:
        p, r, _ = precision_recall_curve(val_labels[:, idx], val_probs[:, idx])
        axes[1].plot(r, p, alpha=0.6, label=f'{label_names[idx]}')
    axes[1].set_xlabel('Recall'); axes[1].set_ylabel('Precision')
    axes[1].set_title('Precision-Recall Curves'); axes[1].legend(fontsize=7)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'roc_pr_curves.png'), dpi=300)
    plt.close()
    print(f"ROC/PR 曲线保存至 {save_dir}/roc_pr_curves.png")


def compute_micro_f1(labels, probs, threshold=0.5):
    preds = (probs >= threshold).astype(int)
    tp = (preds & labels.astype(bool)).sum()
    fp = (preds & ~labels.astype(bool)).sum()
    fn = (~preds & labels.astype(bool)).sum()
    return 2 * tp / (2 * tp + fp + fn + 1e-8)


def train():
    save_dir = 'data/plots/skill_predictor'
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs('data/models', exist_ok=True)

    # 1. 加载数据
    texts = load_data()

    # 2. 构建技能标签词表
    label_extractor = SkillLabelExtractor(max_labels=150)
    label_extractor.build_from_texts(texts)
    label_extractor.save('data/models/skill_label_extractor.pkl')

    # 3. 构建词表
    processor = SkillTextProcessor(vocab_size=10000, max_len=128)
    processor.build_vocab(texts)
    processor.save('data/models/skill_text_processor.pkl')

    # 4. 生成多标签向量
    label_vecs = np.array([label_extractor.encode(t) for t in texts])
    valid = label_vecs.sum(axis=1) > 0
    texts = [t for t, v in zip(texts, valid) if v]
    label_vecs = label_vecs[valid]
    print(f"过滤后有效样本: {len(texts)}, 标签矩阵: {label_vecs.shape}")

    # 5. 划分数据集
    X_tr, X_val, y_tr, y_val = train_test_split(
        texts, label_vecs, test_size=0.2, random_state=42)
    print(f"训练集: {len(X_tr)}, 验证集: {len(X_val)}")

    tr_ds = SkillDataset(X_tr, y_tr, processor)
    val_ds = SkillDataset(X_val, y_val, processor)
    tr_loader = DataLoader(tr_ds, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64)

    # 6. 模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")
    num_labels = len(label_extractor.labels)
    model = SkillTextCNN(len(processor.word2idx), num_labels, 128).to(device)

    # pos_weight for imbalance
    pos_counts = y_tr.sum(axis=0)
    neg_counts = len(y_tr) - pos_counts
    pos_weight = torch.tensor(
        [n / max(p, 1) for p, n in zip(pos_counts, neg_counts)],
        dtype=torch.float32
    ).to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, 'min', patience=3, factor=0.5)

    # 7. 训练
    history = {'train_loss': [], 'val_loss': [], 'train_f1': [], 'val_f1': []}
    best_loss = float('inf')
    epochs = 25

    for epoch in range(epochs):
        model.train()
        tr_loss = 0
        tr_probs, tr_lbls = [], []
        for x, y in tqdm(tr_loader, desc=f'Epoch {epoch+1}/{epochs}', leave=False):
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            tr_loss += loss.item()
            tr_probs.append(torch.sigmoid(out).detach().cpu().numpy())
            tr_lbls.append(y.cpu().numpy())

        model.eval()
        val_loss = 0
        val_probs, val_lbls = [], []
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                out = model(x)
                val_loss += criterion(out, y).item()
                val_probs.append(torch.sigmoid(out).cpu().numpy())
                val_lbls.append(y.cpu().numpy())

        tr_loss /= len(tr_loader); val_loss /= len(val_loader)
        tp = np.vstack(tr_probs); tl = np.vstack(tr_lbls)
        vp = np.vstack(val_probs); vl = np.vstack(val_lbls)
        tr_f1 = compute_micro_f1(tl, tp)
        val_f1 = compute_micro_f1(vl, vp)

        history['train_loss'].append(tr_loss)
        history['val_loss'].append(val_loss)
        history['train_f1'].append(tr_f1)
        history['val_f1'].append(val_f1)

        print(f"Epoch {epoch+1:2d} | TrL {tr_loss:.4f} F1 {tr_f1:.3f} | "
              f"VaL {val_loss:.4f} F1 {val_f1:.3f}")

        scheduler.step(val_loss)
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), 'data/models/skill_predictor.pth')

    # 8. 最终评估图表
    plot_training_curves(history, save_dir)
    plot_roc_and_pr(vl, vp, label_extractor.labels, save_dir)

    # 9. 测试预测
    print("\n=== 测试预测 ===")
    predictor = None  # 由 SkillPredictor 在 API 侧加载
    model.eval()
    for i in range(min(3, len(X_val))):
        seq = processor.text_to_sequence(X_val[i])
        t = torch.tensor([seq], dtype=torch.long).to(device)
        with torch.no_grad():
            probs = torch.sigmoid(model(t)).cpu().numpy()[0]
        top = label_extractor.decode(probs, top_k=5)
        print(f"\n岗位: {X_val[i][:60]}...")
        skills_str = ', '.join(f"{s['skill']}({s['probability']:.2%})" for s in top)
        print(f"预测技能: {skills_str}")

    print(f"\n训练完成！模型保存至 data/models/skill_predictor.pth")


if __name__ == '__main__':
    train()
