"""
Satellite Handover Gymnasium Environment

從 HDF5 數據集加載衛星切換場景，提供標準 Gymnasium 接口用於 RL 訓練。

SOURCE: Proposal 003, Phase 2 - DQN Baseline Implementation
"""

import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import numpy as np
import h5py
import gymnasium as gym
from gymnasium import spaces

logger = logging.getLogger(__name__)


class SatelliteHandoverEnv(gym.Env):
    """
    衛星切換 Gymnasium 環境

    Observation Space:
        Box(low=-inf, high=inf, shape=(state_dim,), dtype=float32)
        - State dimension: 53
        - Contains: serving satellite, candidates, QoS, load, time features

    Action Space:
        Discrete(N+1) where N is max_satellites (default 5)
        - 0: Stay with serving satellite
        - 1~N: Handover to candidate i

    Reward:
        Based on QoS satisfaction, signal quality, and handover cost
        SOURCE: Badini et al. (2024) IEEE TAES, Equation (5)

    SOURCE: Brockman et al. (2016) "OpenAI Gym", arXiv:1606.01540
            Towers et al. (2023) "Gymnasium: A Standard Interface for RL"
    """

    metadata = {'render_modes': ['human']}

    def __init__(
        self,
        dataset_path: str,
        split: str = 'train',
        max_episodes: Optional[int] = None
    ):
        """初始化環境

        Args:
            dataset_path: HDF5 數據集路徑
            split: 數據集分割（'train', 'val', 'test'）
            max_episodes: 最大 episode 數量（None = 無限）
        """
        super().__init__()

        self.dataset_path = Path(dataset_path)
        self.split = split
        self.max_episodes = max_episodes

        # 定義空間維度（在加載數據集之前）
        # SOURCE: Proposal 003 - State space dimension is 53
        self.state_dim = 53

        # 加載數據集
        self._load_dataset()
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.state_dim,),
            dtype=np.float32
        )

        # 動作空間：0=保持，1-5=切換到候選
        # SOURCE: Proposal 003 - Action space is Discrete(6)
        self.max_satellites = 5
        self.action_space = spaces.Discrete(self.max_satellites + 1)

        # Episode 管理
        self.current_episode_idx = 0
        self.current_step_idx = 0
        self.episode_count = 0

        logger.info(f"SatelliteHandoverEnv initialized: split={split}, "
                   f"episodes={len(self.episodes)}, "
                   f"total_transitions={self.total_transitions}")

    def _load_dataset(self):
        """加載 HDF5 數據集

        Raises:
            FileNotFoundError: 數據集文件不存在
            KeyError: 數據集分割不存在
        """
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        logger.info(f"Loading dataset from {self.dataset_path} (split={self.split})")

        with h5py.File(self.dataset_path, 'r') as f:
            if self.split not in f:
                raise KeyError(f"Split '{self.split}' not found in dataset")

            group = f[self.split]

            # 加載所有數據到內存（數據集通常不大）
            self.states = group['states'][:]
            self.actions = group['actions'][:]
            self.rewards = group['rewards'][:]
            self.next_states = group['next_states'][:]
            self.dones = group['dones'][:]

            # 讀取 metadata
            self.num_samples = group.attrs['num_samples']
            self.state_dim_actual = group.attrs['state_dim']
            self.action_dim = group.attrs['action_dim']

            logger.info(f"✅ Loaded {self.num_samples} transitions "
                       f"(state_dim={self.state_dim_actual}, "
                       f"action_dim={self.action_dim})")

        # 驗證狀態維度
        if self.state_dim_actual != self.state_dim:
            logger.warning(f"State dimension mismatch: "
                          f"expected {self.state_dim}, got {self.state_dim_actual}")

        # 分割 episodes（基於 done 標記）
        self._split_episodes()

        self.total_transitions = len(self.states)

    def _split_episodes(self):
        """將數據分割為 episodes

        每個 episode 是一個連續的 transition 序列，直到 done=True
        """
        self.episodes = []
        episode_start = 0

        for i in range(len(self.dones)):
            if self.dones[i] or i == len(self.dones) - 1:
                # Episode 結束
                episode_end = i + 1
                episode = {
                    'states': self.states[episode_start:episode_end],
                    'actions': self.actions[episode_start:episode_end],
                    'rewards': self.rewards[episode_start:episode_end],
                    'next_states': self.next_states[episode_start:episode_end],
                    'dones': self.dones[episode_start:episode_end],
                    'length': episode_end - episode_start
                }
                self.episodes.append(episode)
                episode_start = episode_end

        if not self.episodes:
            # 如果沒有 done=True，整個數據集作為一個 episode
            self.episodes.append({
                'states': self.states,
                'actions': self.actions,
                'rewards': self.rewards,
                'next_states': self.next_states,
                'dones': self.dones,
                'length': len(self.states)
            })

        logger.info(f"Split into {len(self.episodes)} episodes "
                   f"(avg length: {np.mean([ep['length'] for ep in self.episodes]):.1f})")

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """重置環境（Gymnasium API）

        Args:
            seed: 隨機種子
            options: 額外選項

        Returns:
            observation (np.ndarray): 初始狀態 (state_dim,)
            info (dict): 額外信息
                - episode_id: Episode ID
                - episode_length: Episode 長度
        """
        super().reset(seed=seed)

        # 檢查是否達到最大 episode 數量
        if self.max_episodes and self.episode_count >= self.max_episodes:
            logger.info(f"Reached max episodes ({self.max_episodes}), resetting to 0")
            self.episode_count = 0

        # 隨機選擇一個 episode（如果有多個）
        if seed is not None:
            np.random.seed(seed)

        self.current_episode_idx = np.random.randint(0, len(self.episodes))
        self.current_episode = self.episodes[self.current_episode_idx]
        self.current_step_idx = 0
        self.episode_count += 1

        # 獲取初始狀態
        obs = self.current_episode['states'][0].copy()

        info = {
            'episode_id': self.current_episode_idx,
            'episode_length': self.current_episode['length']
        }

        return obs, info

    def step(
        self,
        action: int
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """執行動作（Gymnasium API）

        Args:
            action: 動作（0=保持，1-5=切換到候選）

        Returns:
            observation (np.ndarray): 新狀態
            reward (float): 獎勵
            terminated (bool): Episode 是否自然結束
            truncated (bool): Episode 是否被截斷
            info (dict): 額外信息
                - actual_action: 數據集中的實際動作
                - action_match: 是否與實際動作匹配
        """
        # 檢查動作有效性
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action: {action}")

        # 獲取當前 transition
        actual_action = self.current_episode['actions'][self.current_step_idx]
        reward = self.current_episode['rewards'][self.current_step_idx]
        next_state = self.current_episode['next_states'][self.current_step_idx].copy()
        done = self.current_episode['dones'][self.current_step_idx]

        self.current_step_idx += 1

        # 檢查是否超過 episode 長度
        terminated = done or (self.current_step_idx >= self.current_episode['length'])
        truncated = False  # 我們的數據集沒有 truncation

        info = {
            'actual_action': int(actual_action),
            'action_match': (action == actual_action)
        }

        return next_state, float(reward), terminated, truncated, info

    def render(self, mode: str = 'human'):
        """渲染環境（可選實現）

        Args:
            mode: 渲染模式
        """
        if mode == 'human':
            print(f"Episode {self.current_episode_idx}, "
                  f"Step {self.current_step_idx}/{self.current_episode['length']}")

    def close(self):
        """關閉環境"""
        pass

    def get_episode_stats(self) -> Dict[str, Any]:
        """獲取 episode 統計信息

        Returns:
            統計信息字典
        """
        episode_lengths = [ep['length'] for ep in self.episodes]
        episode_rewards = [np.sum(ep['rewards']) for ep in self.episodes]

        return {
            'num_episodes': len(self.episodes),
            'avg_episode_length': np.mean(episode_lengths),
            'std_episode_length': np.std(episode_lengths),
            'avg_episode_reward': np.mean(episode_rewards),
            'std_episode_reward': np.std(episode_rewards),
            'total_transitions': self.total_transitions
        }


def test_environment():
    """測試環境"""
    import logging
    logging.basicConfig(level=logging.INFO)

    # 測試加載環境
    dataset_path = "data/ml_training/rl_training_dataset_20251023_120619.h5"
    if not Path(dataset_path).exists():
        print(f"❌ Dataset not found: {dataset_path}")
        return

    # 測試 train split
    env = SatelliteHandoverEnv(dataset_path, split='train')

    print(f"\n✅ Environment created:")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")

    # 測試 reset
    obs, info = env.reset(seed=42)
    print(f"\n✅ Reset successful:")
    print(f"   Observation shape: {obs.shape}")
    print(f"   Info: {info}")

    # 測試幾個 steps
    print(f"\n✅ Running 5 steps:")
    for i in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"   Step {i+1}: action={action}, reward={reward:.3f}, "
              f"terminated={terminated}, info={info}")

        if terminated or truncated:
            print(f"   Episode ended, resetting...")
            obs, info = env.reset()
            break

    # 獲取統計信息
    stats = env.get_episode_stats()
    print(f"\n📊 Episode Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")

    env.close()


if __name__ == "__main__":
    test_environment()
