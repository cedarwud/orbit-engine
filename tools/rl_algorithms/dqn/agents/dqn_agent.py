"""
DQN Agent Implementation

完整的 DQN Agent，整合 Q-Network, Target Network, 和 Experience Replay。

SOURCE: Mnih et al. (2015) "Human-level control through deep reinforcement learning"
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Optional
import copy

from ..networks.q_network import QNetwork
from ..utils.replay_buffer import ReplayBuffer


class DQNAgent:
    """
    DQN Agent 實現

    組件:
    - Q-Network: 估計 Q 值
    - Target Network: 穩定訓練目標
    - Experience Replay: 打破樣本相關性
    - Epsilon-greedy: 平衡探索與利用

    SOURCE: Mnih et al. (2015) Nature, Algorithm 1
    """

    def __init__(
        self,
        state_dim: int = 53,
        action_dim: int = 6,
        hidden_dims: list = None,
        learning_rate: float = 0.0001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_capacity: int = 100000,
        batch_size: int = 64,
        target_update_freq: int = 10,
        device: str = 'cpu'
    ):
        """初始化 DQN Agent"""
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.update_counter = 0

        self.device = torch.device(device)

        # Q-Network 和 Target Network
        if hidden_dims is None:
            hidden_dims = [256, 256]

        self.q_network = QNetwork(state_dim, action_dim, hidden_dims).to(self.device)
        self.target_network = QNetwork(state_dim, action_dim, hidden_dims).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()

        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)

        # Experience Replay
        self.memory = ReplayBuffer(capacity=buffer_capacity)

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """選擇動作（epsilon-greedy）"""
        state_tensor = torch.FloatTensor(state).to(self.device)

        if training and np.random.rand() < self.epsilon:
            return np.random.randint(0, self.action_dim)
        else:
            return self.q_network.get_action(state_tensor, epsilon=0.0)

    def train_step(self) -> Optional[float]:
        """訓練一步"""
        if not self.memory.is_ready(self.batch_size):
            return None

        # 從 buffer 採樣
        states, actions, rewards, next_states, dones = self.memory.sample(
            self.batch_size, self.device
        )

        # 計算當前 Q 值
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # 計算目標 Q 值（使用 Target Network）
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values

        # 計算 loss
        loss = nn.MSELoss()(current_q_values, target_q_values)

        # 優化
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 更新 Target Network
        self.update_counter += 1
        if self.update_counter % self.target_update_freq == 0:
            self.update_target_network()

        return loss.item()

    def update_target_network(self):
        """更新 Target Network"""
        self.target_network.load_state_dict(self.q_network.state_dict())

    def decay_epsilon(self):
        """衰減 epsilon"""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def save(self, path: str):
        """儲存模型"""
        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)

    def load(self, path: str):
        """加載模型"""
        checkpoint = torch.load(path)
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
