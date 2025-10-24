"""
Experience Replay Buffer

Stores and samples transitions for DQN training.

SOURCE: Mnih et al. (2015) "Human-level control through deep reinforcement learning"
        Nature 518(7540):529-533, Algorithm 1
"""

import random
from collections import deque
from typing import List, Tuple, Optional
import numpy as np
import torch


class ReplayBuffer:
    """
    Experience Replay Buffer for DQN

    Stores transitions (s, a, r, s', done) and provides random sampling
    for breaking correlation in training data.

    SOURCE: Mnih et al. (2015) Nature, Algorithm 1: Deep Q-learning with
            experience replay

    Args:
        capacity: Maximum buffer size
        seed: Random seed for reproducibility
    """

    def __init__(self, capacity: int = 100000, seed: Optional[int] = None):
        """初始化 Replay Buffer

        Args:
            capacity: 最大容量（當達到上限時，舊的 transitions 會被覆蓋）
                SOURCE: Mnih et al. (2015) - 典型值為 100K ~ 1M
            seed: 隨機種子
        """
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """添加 transition 到 buffer

        Args:
            state: 當前狀態
            action: 執行的動作
            reward: 獲得的獎勵
            next_state: 下一狀態
            done: Episode 是否結束
        """
        self.buffer.append((state, action, reward, next_state, done))

    def sample(
        self,
        batch_size: int,
        device: torch.device = torch.device('cpu')
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """從 buffer 隨機採樣一個 batch

        Args:
            batch_size: Batch 大小
            device: PyTorch device (cpu or cuda)

        Returns:
            states: 狀態 tensor, shape (batch_size, state_dim)
            actions: 動作 tensor, shape (batch_size,)
            rewards: 獎勵 tensor, shape (batch_size,)
            next_states: 下一狀態 tensor, shape (batch_size, state_dim)
            dones: Done 標記 tensor, shape (batch_size,)

        Raises:
            ValueError: Buffer 中樣本不足 batch_size
        """
        if len(self.buffer) < batch_size:
            raise ValueError(f"Not enough samples in buffer: "
                           f"{len(self.buffer)} < {batch_size}")

        # 隨機採樣
        transitions = random.sample(self.buffer, batch_size)

        # 分離各個組件
        states, actions, rewards, next_states, dones = zip(*transitions)

        # 轉換為 PyTorch tensors
        states = torch.FloatTensor(np.array(states)).to(device)
        actions = torch.LongTensor(actions).to(device)
        rewards = torch.FloatTensor(rewards).to(device)
        next_states = torch.FloatTensor(np.array(next_states)).to(device)
        dones = torch.FloatTensor(dones).to(device)

        return states, actions, rewards, next_states, dones

    def __len__(self) -> int:
        """返回 buffer 中的樣本數量"""
        return len(self.buffer)

    def is_ready(self, batch_size: int) -> bool:
        """檢查 buffer 是否準備好採樣

        Args:
            batch_size: Batch 大小

        Returns:
            True if buffer has enough samples
        """
        return len(self.buffer) >= batch_size

    def clear(self):
        """清空 buffer"""
        self.buffer.clear()

    def get_statistics(self) -> dict:
        """獲取 buffer 統計信息

        Returns:
            統計信息字典
        """
        if len(self.buffer) == 0:
            return {
                'size': 0,
                'capacity': self.capacity,
                'utilization': 0.0
            }

        # 提取 rewards
        rewards = [transition[2] for transition in self.buffer]

        return {
            'size': len(self.buffer),
            'capacity': self.capacity,
            'utilization': len(self.buffer) / self.capacity,
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'min_reward': np.min(rewards),
            'max_reward': np.max(rewards)
        }


def test_replay_buffer():
    """測試 Replay Buffer"""
    print("Testing Replay Buffer...")

    # 創建 Replay Buffer
    buffer = ReplayBuffer(capacity=1000, seed=42)

    print(f"\n✅ Replay Buffer created:")
    print(f"   Capacity: {buffer.capacity}")
    print(f"   Size: {len(buffer)}")

    # 添加一些 transitions
    state_dim = 53
    print(f"\n✅ Adding transitions...")
    for i in range(100):
        state = np.random.randn(state_dim)
        action = np.random.randint(0, 6)
        reward = np.random.randn()
        next_state = np.random.randn(state_dim)
        done = (i % 20 == 19)  # 每 20 步結束一個 episode

        buffer.push(state, action, reward, next_state, done)

    print(f"   Buffer size: {len(buffer)}")

    # 檢查是否準備好採樣
    batch_size = 32
    print(f"\n✅ Checking if ready for sampling (batch_size={batch_size}):")
    print(f"   Ready: {buffer.is_ready(batch_size)}")

    # 採樣一個 batch
    print(f"\n✅ Sampling a batch:")
    states, actions, rewards, next_states, dones = buffer.sample(batch_size)

    print(f"   States shape: {states.shape}")
    print(f"   Actions shape: {actions.shape}")
    print(f"   Rewards shape: {rewards.shape}")
    print(f"   Next states shape: {next_states.shape}")
    print(f"   Dones shape: {dones.shape}")

    # 測試多次採樣（應該得到不同的 batches）
    print(f"\n✅ Sampling multiple batches:")
    batches = []
    for i in range(3):
        _, actions, _, _, _ = buffer.sample(batch_size)
        batches.append(actions.tolist())
        print(f"   Batch {i+1} first 5 actions: {actions[:5].tolist()}")

    # 驗證不同批次不同
    all_same = all(batches[0] == batch for batch in batches[1:])
    print(f"   All batches same? {all_same} (should be False)")

    # 獲取統計信息
    stats = buffer.get_statistics()
    print(f"\n📊 Buffer Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.4f}")
        else:
            print(f"   {key}: {value}")

    # 測試 buffer 容量上限
    print(f"\n✅ Testing capacity limit:")
    original_size = len(buffer)
    for i in range(1000):
        buffer.push(
            np.random.randn(state_dim),
            np.random.randint(0, 6),
            np.random.randn(),
            np.random.randn(state_dim),
            False
        )

    print(f"   Original size: {original_size}")
    print(f"   After adding 1000: {len(buffer)}")
    print(f"   Capacity: {buffer.capacity}")
    print(f"   Buffer capped at capacity: {len(buffer) == buffer.capacity}")


if __name__ == "__main__":
    test_replay_buffer()
