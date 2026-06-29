"""Train the matching model from the Tianchi jobs table."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
import random
from tqdm import tqdm
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

from db import get_db
from services.dl_models.matching_model import SiameseMatchingNet, TextProcessor

class SyntheticDataset(Dataset):
    def __init__(self, pairs, labels, processor):
        self.pairs = pairs
        self.labels = labels
        self.processor = processor
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, idx):
        resume_text, job_text = self.pairs[idx]
        return {
            'resume': torch.tensor(self.processor.text_to_sequence(resume_text), dtype=torch.long),
            'job': torch.tensor(self.processor.text_to_sequence(job_text), dtype=torch.long),
            'label': torch.tensor(self.labels[idx], dtype=torch.float32)
        }

def generate_data():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT job_title AS job_name, job_description FROM jobs WHERE job_description IS NOT NULL AND job_description != ''")
    jobs = cur.fetchall()
    conn.close()
    if len(jobs) < 10:
        # 保底模拟
        jobs = [("Python开发", "后端开发"), ("Java开发", "系统架构")] * 200
    pos, neg = [], []
    # 正样本：相同岗位
    for j in jobs[:1500]:
        text = f"{j['job_name']} {j['job_description']}"
        pos.append((text, text))
    # 负样本：随机不同岗位
    for _ in range(1500):
        j1, j2 = random.sample(jobs, 2)
        t1 = f"{j1['job_name']} {j1['job_description']}"
        t2 = f"{j2['job_name']} {j2['job_description']}"
        neg.append((t1, t2))
    pairs = pos + neg
    labels = [1.0]*len(pos) + [0.0]*len(neg)
    combined = list(zip(pairs, labels))
    random.shuffle(combined)
    pairs, labels = zip(*combined)
    print(f"生成数据：正样本{len(pos)}，负样本{len(neg)}")
    return list(pairs), list(labels)

def train():
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/plots', exist_ok=True)
    pairs, labels = generate_data()
    all_texts = [p[0]+" "+p[1] for p in pairs]
    processor = TextProcessor(vocab_size=8000, max_len=256)
    processor.build_vocab(all_texts)
    processor.save('data/models/text_processor.pkl')
    
    X_train, X_val, y_train, y_val = train_test_split(pairs, labels, test_size=0.2, random_state=42)
    train_ds = SyntheticDataset(X_train, y_train, processor)
    val_ds = SyntheticDataset(X_val, y_val, processor)
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = SiameseMatchingNet(vocab_size=len(processor.word2idx), embed_dim=128, hidden_dim=256)
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3)
    criterion = nn.MSELoss()
    
    history = {'train_loss':[], 'val_loss':[], 'train_acc':[], 'val_acc':[]}
    best_loss = float('inf')
    for epoch in range(25):
        model.train()
        train_loss, train_preds, train_trues = 0, [], []
        for batch in tqdm(train_loader, desc=f'Epoch {epoch+1}'):
            resume = batch['resume'].to(device)
            job = batch['job'].to(device)
            label = batch['label'].to(device).view(-1,1)
            optimizer.zero_grad()
            pred = model(resume, job)/100.0
            loss = criterion(pred, label)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            train_preds.extend((pred*100).cpu().detach().numpy().flatten())
            train_trues.extend((label*100).cpu().numpy().flatten())
        
        model.eval()
        val_loss, val_preds, val_trues = 0, [], []
        with torch.no_grad():
            for batch in val_loader:
                resume = batch['resume'].to(device)
                job = batch['job'].to(device)
                label = batch['label'].to(device).view(-1,1)
                pred = model(resume, job)/100.0
                loss = criterion(pred, label)
                val_loss += loss.item()
                val_preds.extend((pred*100).cpu().numpy().flatten())
                val_trues.extend((label*100).cpu().numpy().flatten())
        
        train_acc = np.mean([abs(p-t)<15 for p,t in zip(train_preds, train_trues)])*100
        val_acc = np.mean([abs(p-t)<15 for p,t in zip(val_preds, val_trues)])*100
        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)
        print(f"Epoch {epoch+1:2d} | Train Loss {train_loss:.4f} | Val Loss {val_loss:.4f} | Acc {train_acc:.1f}/{val_acc:.1f}")
        
        scheduler.step(val_loss)
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), 'data/models/matching_model_best.pth')
    
    # 画图
    plt.figure()
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.legend()
    plt.title('Loss Curves')
    plt.savefig('data/plots/matching_loss.png')
    plt.figure()
    plt.plot(history['train_acc'], label='Train Acc')
    plt.plot(history['val_acc'], label='Val Acc')
    plt.legend()
    plt.title('Accuracy Curves')
    plt.savefig('data/plots/matching_acc.png')
    print("训练完成，模型和图表已保存")

if __name__ == '__main__':
    train()
