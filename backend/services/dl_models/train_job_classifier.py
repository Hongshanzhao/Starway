"""
训练岗位自动分类模型（TextCNN 多分类）
从 job 表加载数据，处理类别不平衡，生成分类报告和混淆矩阵
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import numpy as np
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import random

from db import get_db
from services.dl_models.job_classifier_model import TextCNN, JobTextProcessor

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class JobDataset(Dataset):
    def __init__(self, texts, labels, processor):
        self.texts = texts
        self.labels = labels
        self.processor = processor

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        seq = self.processor.text_to_sequence(self.texts[idx])
        return {
            'input': torch.tensor(seq, dtype=torch.long),
            'label': torch.tensor(self.labels[idx], dtype=torch.long)
        }


def load_data():
    """从数据库加载岗位数据"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT job_name, job_description, industry
        FROM job
        WHERE job_description IS NOT NULL AND job_description != ''
          AND industry IS NOT NULL AND industry != ''
    """)
    rows = cur.fetchall()
    conn.close()

    texts = []
    labels = []
    for row in rows:
        texts.append(f"{row['job_name']} {row['job_description']}")
        labels.append(row['industry'])

    # 将 category_id 映射为 0..N-1
    unique_cats = sorted(set(labels))
    cat2id = {cat: i for i, cat in enumerate(unique_cats)}
    id2cat = {i: cat for cat, i in cat2id.items()}
    labels = [cat2id[l] for l in labels]

    print(f"加载数据：{len(texts)} 条有效样本，{len(unique_cats)} 个类别")
    for cat_id, idx in sorted(id2cat.items(), key=lambda x: x[1]):
        count = sum(1 for l in labels if l == idx)
        print(f"  类别 {cat_id}: {count} 条")
    return texts, labels, cat2id, id2cat


def compute_class_weights(labels, num_classes):
    """计算类别权重处理不平衡"""
    counts = Counter(labels)
    total = len(labels)
    weights = []
    for c in range(num_classes):
        count = counts.get(c, 1)
        weights.append(total / (num_classes * count))
    print(f"类别权重: {[f'{w:.2f}' for w in weights]}")
    return torch.tensor(weights, dtype=torch.float32)


def plot_confusion(cm, class_names, save_path):
    """绘制混淆矩阵"""
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names,
                annot_kws={'size': 8})
    plt.xlabel('Predicted', fontsize=12)
    plt.ylabel('Actual', fontsize=12)
    plt.title('Confusion Matrix (岗位分类)', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"混淆矩阵保存至 {save_path}")


def plot_history(history, save_dir):
    """绘制 Loss 和 Accuracy 曲线"""
    epochs = range(1, len(history['train_loss']) + 1)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(epochs, history['train_loss'], label='Train Loss', linewidth=2)
    axes[0].plot(epochs, history['val_loss'], label='Val Loss', linewidth=2)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, history['train_acc'], label='Train Acc', linewidth=2)
    axes[1].plot(epochs, history['val_acc'], label='Val Acc', linewidth=2)
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy (%)')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'job_classifier_history.png'), dpi=300)
    plt.close()
    print(f"训练曲线保存至 {save_dir}/job_classifier_history.png")


def train():
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/plots', exist_ok=True)

    # 1. 加载数据
    texts, labels, cat2id, id2cat = load_data()
    num_classes = len(id2cat)

    # 2. 构建词表
    processor = JobTextProcessor(vocab_size=8000, max_len=128)
    processor.build_vocab(texts)
    processor.save('data/models/job_classifier_processor.pkl')

    # 3. 划分数据集
    X_train, X_val, y_train, y_val = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"训练集: {len(X_train)}, 验证集: {len(X_val)}")

    # 4. 类别权重 + WeightedRandomSampler
    class_weights = compute_class_weights(y_train, num_classes)
    sample_weights = [class_weights[l].item() for l in y_train]
    sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)

    train_ds = JobDataset(X_train, y_train, processor)
    val_ds = JobDataset(X_val, y_val, processor)
    train_loader = DataLoader(train_ds, batch_size=64, sampler=sampler)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    # 5. 模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    model = TextCNN(vocab_size=len(processor.word2idx), embed_dim=128,
                    num_classes=num_classes, num_filters=100, dropout=0.4)
    model.to(device)

    class_weights = class_weights.to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, 'min', patience=3, factor=0.5
    )

    # 6. 训练
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    best_loss = float('inf')
    epochs = 30

    for epoch in range(epochs):
        model.train()
        train_loss, train_correct, train_total = 0, 0, 0
        for batch in tqdm(train_loader, desc=f'Epoch {epoch+1}/{epochs}', leave=False):
            inputs = batch['input'].to(device)
            labels = batch['label'].to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            train_correct += (outputs.argmax(1) == labels).sum().item()
            train_total += labels.size(0)

        model.eval()
        val_loss, val_correct, val_total = 0, 0, 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                inputs = batch['input'].to(device)
                labels = batch['label'].to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                val_correct += (outputs.argmax(1) == labels).sum().item()
                val_total += labels.size(0)
                all_preds.extend(outputs.argmax(1).cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        train_acc = train_correct / train_total * 100
        val_acc = val_correct / val_total * 100

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)

        print(f"Epoch {epoch+1:2d} | Train Loss {train_loss:.4f} Acc {train_acc:.1f}% | "
              f"Val Loss {val_loss:.4f} Acc {val_acc:.1f}%")

        scheduler.step(val_loss)
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), 'data/models/job_classifier.pth')

    # 7. 评估
    print("\n=== 分类报告 ===")
    try:
        cat_names = [f"cat{id2cat[i]}" for i in range(num_classes)]
    except Exception:
        cat_names = [str(id2cat.get(i, i)) for i in range(num_classes)]
    print(classification_report(all_labels, all_preds, target_names=cat_names, zero_division=0))

    # 混淆矩阵
    cm = confusion_matrix(all_labels, all_preds)
    plot_confusion(cm, cat_names, 'data/plots/job_classifier_cm.png')
    plot_history(history, 'data/plots')

    # 8. 保存分类映射
    import pickle
    with open('data/models/job_classifier_cat_map.pkl', 'wb') as f:
        pickle.dump({'cat2id': cat2id, 'id2category': id2cat}, f)

    print("训练完成！")


if __name__ == '__main__':
    train()
