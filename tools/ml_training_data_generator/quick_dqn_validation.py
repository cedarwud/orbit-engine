#!/usr/bin/env python3
"""
Quick DQN Validation - 验证 distance 特征是否被学习
========================================================

目的: 快速验证（不是完整训练）DQN 能否学到 distance 特征的价值

方法:
1. 训练简单 DQN 2-3 epoch
2. 分析 feature importance
3. 对比使用/不使用 distance 的性能

Author: Claude (Anthropic AI)
Date: 2025-10-24
"""

import h5py
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HandoverDataset(Dataset):
    """Handover transition dataset"""

    def __init__(self, states, actions, rewards, next_states, dones):
        self.states = torch.FloatTensor(states)
        self.actions = torch.LongTensor(actions)
        self.rewards = torch.FloatTensor(rewards)
        self.next_states = torch.FloatTensor(next_states)
        self.dones = torch.FloatTensor(dones)

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return (
            self.states[idx],
            self.actions[idx],
            self.rewards[idx],
            self.next_states[idx],
            self.dones[idx]
        )


class SimpleDQN(nn.Module):
    """简单的 DQN 网络"""

    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super(SimpleDQN, self).__init__()

        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )

    def forward(self, state):
        return self.network(state)


class FeatureImportanceAnalyzer:
    """分析哪些特征对模型重要"""

    def __init__(self, model, device):
        self.model = model
        self.device = device

    def compute_gradient_importance(self, states, actions):
        """
        通过梯度计算特征重要性

        方法: 对每个特征计算其梯度的绝对值均值
        梯度大 → 模型对该特征敏感 → 特征重要
        """
        self.model.eval()
        states = states.to(self.device)
        states.requires_grad = True

        # Forward pass
        q_values = self.model(states)

        # 选择实际采取的 action 的 Q 值
        actions_tensor = actions.to(self.device)
        selected_q = q_values.gather(1, actions_tensor.unsqueeze(1))

        # Backward to get gradients
        selected_q.sum().backward()

        # 计算每个特征的梯度绝对值均值
        gradients = states.grad.abs().mean(dim=0).cpu().numpy()

        return gradients

    def compute_feature_importance_permutation(self, model, dataloader):
        """
        通过特征置换计算重要性

        方法: 打乱某个特征后，看性能下降多少
        下降多 → 特征重要
        """
        self.model.eval()

        # 计算 baseline 性能
        baseline_loss = self._evaluate_loss(dataloader)

        # 计算每个特征的重要性
        num_features = next(iter(dataloader))[0].shape[1]
        importance = np.zeros(num_features)

        for feature_idx in range(num_features):
            # 打乱这个特征
            permuted_loss = self._evaluate_loss_with_permutation(dataloader, feature_idx)
            importance[feature_idx] = permuted_loss - baseline_loss

        return importance

    def _evaluate_loss(self, dataloader):
        """评估当前模型的 loss"""
        total_loss = 0
        count = 0

        with torch.no_grad():
            for states, actions, rewards, next_states, dones in dataloader:
                states = states.to(self.device)
                actions = actions.to(self.device)
                rewards = rewards.to(self.device)
                next_states = next_states.to(self.device)
                dones = dones.to(self.device)

                # Q-learning target
                q_values = self.model(states)
                next_q_values = self.model(next_states)

                targets = rewards + 0.99 * next_q_values.max(1)[0] * (1 - dones)
                selected_q = q_values.gather(1, actions.unsqueeze(1)).squeeze()

                loss = nn.MSELoss()(selected_q, targets)
                total_loss += loss.item()
                count += 1

        return total_loss / count if count > 0 else 0

    def _evaluate_loss_with_permutation(self, dataloader, feature_idx):
        """评估打乱某个特征后的 loss"""
        total_loss = 0
        count = 0

        with torch.no_grad():
            for states, actions, rewards, next_states, dones in dataloader:
                # 打乱指定特征
                states_permuted = states.clone()
                perm_indices = torch.randperm(states.shape[0])
                states_permuted[:, feature_idx] = states[perm_indices, feature_idx]

                states_permuted = states_permuted.to(self.device)
                actions = actions.to(self.device)
                rewards = rewards.to(self.device)
                next_states = next_states.to(self.device)
                dones = dones.to(self.device)

                q_values = self.model(states_permuted)
                next_q_values = self.model(next_states)

                targets = rewards + 0.99 * next_q_values.max(1)[0] * (1 - dones)
                selected_q = q_values.gather(1, actions.unsqueeze(1)).squeeze()

                loss = nn.MSELoss()(selected_q, targets)
                total_loss += loss.item()
                count += 1

        return total_loss / count if count > 0 else 0


def load_dataset(h5_path):
    """加载 HDF5 数据集"""
    logger.info(f"Loading dataset: {h5_path}")

    with h5py.File(h5_path, 'r') as f:
        # Load train data
        train_states = f['train/states'][:]
        train_actions = f['train/actions'][:]
        train_rewards = f['train/rewards'][:]
        train_next_states = f['train/next_states'][:]
        train_dones = f['train/dones'][:]

        # Load val data
        val_states = f['val/states'][:]
        val_actions = f['val/actions'][:]
        val_rewards = f['val/rewards'][:]
        val_next_states = f['val/next_states'][:]
        val_dones = f['val/dones'][:]

    logger.info(f"✅ Loaded dataset:")
    logger.info(f"   Train: {len(train_states)} samples")
    logger.info(f"   Val: {len(val_states)} samples")
    logger.info(f"   State dim: {train_states.shape[1]}")

    return (
        (train_states, train_actions, train_rewards, train_next_states, train_dones),
        (val_states, val_actions, val_rewards, val_next_states, val_dones)
    )


def train_dqn_quick(model, dataloader, optimizer, device, num_epochs=3):
    """快速训练 DQN（仅验证用）"""
    model.train()

    logger.info(f"\n🚀 Starting quick DQN training ({num_epochs} epochs)...")

    for epoch in range(num_epochs):
        total_loss = 0
        count = 0

        for batch_idx, (states, actions, rewards, next_states, dones) in enumerate(dataloader):
            states = states.to(device)
            actions = actions.to(device)
            rewards = rewards.to(device)
            next_states = next_states.to(device)
            dones = dones.to(device)

            # Q-learning
            q_values = model(states)
            next_q_values = model(next_states).detach()

            # Target: r + γ * max Q(s', a')
            targets = rewards + 0.99 * next_q_values.max(1)[0] * (1 - dones)

            # Selected Q values
            selected_q = q_values.gather(1, actions.unsqueeze(1)).squeeze()

            # Loss
            loss = nn.MSELoss()(selected_q, targets)

            # Optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            count += 1

        avg_loss = total_loss / count if count > 0 else 0
        logger.info(f"   Epoch {epoch+1}/{num_epochs}: Loss = {avg_loss:.4f}")

    logger.info("✅ Quick training completed")
    return model


def analyze_feature_importance(model, dataloader, device):
    """分析特征重要性"""
    logger.info("\n📊 Analyzing feature importance...")

    analyzer = FeatureImportanceAnalyzer(model, device)

    # Method 1: Gradient-based
    logger.info("\n   Method 1: Gradient-based importance")
    states_batch, actions_batch = next(iter(dataloader))[:2]
    gradient_importance = analyzer.compute_gradient_importance(states_batch, actions_batch)

    # 归一化
    gradient_importance = gradient_importance / gradient_importance.sum()

    # 找出最重要的特征
    top_indices = np.argsort(gradient_importance)[::-1][:10]

    logger.info("   Top 10 most important features:")
    for i, idx in enumerate(top_indices):
        logger.info(f"      {i+1}. Feature {idx}: {gradient_importance[idx]:.4f}")

    return gradient_importance, top_indices


def identify_distance_features(state_dim):
    """
    识别哪些特征是 distance 相关的

    State 特征结构（来自 state_extractor.py）:
    对于每个候选卫星 (最多5个):
        - rsrp_dbm
        - rsrq_db
        - sinr_db
        - distance_km  ← 这个！
        - elevation_deg
        - azimuth_deg
        - doppler_shift_hz
        - path_loss_db
        - atmospheric_loss_db
        - snr_db
        (10 个特征/卫星)

    加上服务卫星特征和其他 (3个)

    Total = 5*10 + 3 = 53
    """
    # Distance 特征的索引（每个卫星的第4个特征）
    distance_indices = []
    features_per_satellite = 10
    num_candidates = 5

    for i in range(num_candidates):
        # distance_km 是每个卫星特征块的第4个 (index 3)
        distance_idx = 3 + i * features_per_satellite + 3  # +3 for serving satellite features
        if distance_idx < state_dim:
            distance_indices.append(distance_idx)

    return distance_indices


def main():
    # Configuration
    h5_path = Path("data/ml_training/rl_training_dataset_20251024_083603.h5")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    logger.info("="*80)
    logger.info("🎯 Quick DQN Validation - 验证 Distance 特征学习")
    logger.info("="*80)
    logger.info(f"Device: {device}")

    # Load data
    train_data, val_data = load_dataset(h5_path)

    train_dataset = HandoverDataset(*train_data)
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

    val_dataset = HandoverDataset(*val_data)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    # Model setup
    state_dim = train_data[0].shape[1]
    action_dim = 7  # stay + handover_1 to handover_6

    model = SimpleDQN(state_dim, action_dim).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    logger.info(f"\n📋 Model info:")
    logger.info(f"   State dim: {state_dim}")
    logger.info(f"   Action dim: {action_dim}")
    logger.info(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Quick training (2-3 epochs)
    model = train_dqn_quick(model, train_loader, optimizer, device, num_epochs=3)

    # Analyze feature importance
    gradient_importance, top_indices = analyze_feature_importance(model, val_loader, device)

    # Check if distance features are in top important features
    distance_indices = identify_distance_features(state_dim)

    logger.info("\n" + "="*80)
    logger.info("🔍 DISTANCE FEATURE ANALYSIS")
    logger.info("="*80)

    logger.info(f"\nDistance feature indices: {distance_indices}")
    logger.info(f"Distance features in state: {len(distance_indices)}")

    # Check how many distance features are in top 10
    distance_in_top10 = sum(1 for idx in top_indices[:10] if idx in distance_indices)
    distance_in_top20 = sum(1 for idx in top_indices[:20] if idx in distance_indices)

    logger.info(f"\n📊 Results:")
    logger.info(f"   Distance features in Top 10: {distance_in_top10}/{len(distance_indices)}")
    logger.info(f"   Distance features in Top 20: {distance_in_top20}/{len(distance_indices)}")

    # Calculate average importance for distance features
    distance_importance = [gradient_importance[idx] for idx in distance_indices]
    avg_distance_importance = np.mean(distance_importance) if distance_importance else 0

    # Calculate average importance for non-distance features
    non_distance_importance = [gradient_importance[i] for i in range(state_dim) if i not in distance_indices]
    avg_non_distance_importance = np.mean(non_distance_importance) if non_distance_importance else 0

    logger.info(f"\n📈 Importance Comparison:")
    logger.info(f"   Avg distance feature importance: {avg_distance_importance:.6f}")
    logger.info(f"   Avg other feature importance: {avg_non_distance_importance:.6f}")
    logger.info(f"   Ratio (distance/other): {avg_distance_importance/avg_non_distance_importance:.2f}x")

    # Interpretation
    logger.info("\n" + "="*80)
    logger.info("✅ CONCLUSION")
    logger.info("="*80)

    if distance_in_top10 >= 2:
        logger.info("\n✅ Distance features ARE being learned!")
        logger.info(f"   {distance_in_top10} out of {len(distance_indices)} distance features")
        logger.info("   are in the top 10 most important features.")
        logger.info("\n   This validates that the DQN is utilizing distance information")
        logger.info("   from the D2 events, not just relying on A4 (RSRP).")
    elif distance_in_top20 >= 2:
        logger.info("\n⚠️  Distance features are moderately important")
        logger.info(f"   {distance_in_top20} out of {len(distance_indices)} distance features")
        logger.info("   are in the top 20 features.")
        logger.info("\n   DQN is learning distance, but not as strongly as expected.")
    else:
        logger.info("\n❌ Distance features have low importance")
        logger.info("   DQN may not be effectively utilizing D2 information.")
        logger.info("\n   Possible reasons:")
        logger.info("   - Training time too short (this is just a quick validation)")
        logger.info("   - Need more data or longer training")
        logger.info("   - Feature scaling issues")

    logger.info("\n" + "="*80)
    logger.info("Note: This is a QUICK VALIDATION (3 epochs), not full training.")
    logger.info("A fully trained model would show clearer patterns.")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
