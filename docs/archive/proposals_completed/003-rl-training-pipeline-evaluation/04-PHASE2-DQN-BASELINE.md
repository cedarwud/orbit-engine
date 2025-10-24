# Proposal 003: Phase 2 - DQN Baseline Implementation

**文檔版本**: v2.0
**最後更新**: 2025-10-23
**預計時間**: 3-4 天

---

## 📋 概述

Phase 2 實現 DQN (Deep Q-Network) baseline 強化學習算法，作為未來算法比較的基準。

**關鍵設計**:
- ✅ **僅 DQN** - 不實現 A3C/PPO/SAC
- ✅ **Gymnasium API** - 使用現代框架
- ✅ **模組化設計** - 便於未來擴展

---

## 🎯 目標

1. 實現 DQN 核心算法（Experience Replay + Target Network）
2. 建立 Gymnasium 環境（SatelliteHandoverEnv）
3. 整合 ML Data Generator 輸出
4. 實現基本訓練循環

---

## 📦 模組設計

詳見 [02-ARCHITECTURE.md](02-ARCHITECTURE.md) Module 2

### 核心組件

1. **DQN Agent** - Q-Network + Target Network
2. **Experience Replay** - 記憶體緩衝區
3. **Gymnasium Environment** - 衛星切換環境
4. **Training Loop** - 訓練主循環

---

## 🏗️ DQN 架構

### Q-Network 設計

```python
class QNetwork(nn.Module):
    """DQN Q-Network

    SOURCE: Mnih et al. (2015) Nature, "Human-level control through
            deep reinforcement learning", Section: Methods
    """

    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, 256)
        self.fc2 = nn.Linear(256, 256)
        self.fc3 = nn.Linear(256, action_dim)

    def forward(self, state):
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
```

### Experience Replay

```python
class ReplayBuffer:
    """Experience Replay Buffer

    SOURCE: Mnih et al. (2015) Nature, Algorithm 1: Deep Q-learning
            with experience replay
    """

    def __init__(self, capacity: int = 100000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        return random.sample(self.buffer, batch_size)
```

---

## 🌍 Gymnasium Environment

### 環境定義

```python
import gymnasium as gym
from gymnasium import spaces

class SatelliteHandoverEnv(gym.Env):
    """衛星切換 Gymnasium 環境

    SOURCE: Brockman et al. (2016) "OpenAI Gym", arXiv:1606.01540
            (Gymnasium API: Towers et al. 2023)
    """

    metadata = {'render_modes': ['human', 'rgb_array']}

    def __init__(self, data_path: str):
        super().__init__()

        # 狀態空間: [RSRP, SNR, 距離, 仰角, 負載, 業務類型]
        self.observation_space = spaces.Box(
            low=np.array([-140, -20, 0, 0, 0, 0]),
            high=np.array([-50, 30, 10000, 90, 100, 3]),
            dtype=np.float32
        )

        # 動作空間: 3 個候選衛星 + 保持當前
        self.action_space = spaces.Discrete(4)

        # 加載訓練數據
        self.data = self._load_data(data_path)

    def reset(self, seed=None, options=None):
        """重置環境（Gymnasium API）

        Returns:
            observation (np.ndarray): 初始狀態
            info (dict): 額外信息
        """
        super().reset(seed=seed)
        self.current_step = 0
        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def step(self, action):
        """執行動作（Gymnasium API）

        Returns:
            observation (np.ndarray): 新狀態
            reward (float): 獎勵
            terminated (bool): 回合是否自然結束
            truncated (bool): 回合是否被截斷
            info (dict): 額外信息
        """
        # 執行切換決策
        reward = self._calculate_reward(action)
        self.current_step += 1

        terminated = self._is_episode_done()
        truncated = self.current_step >= self.max_steps

        obs = self._get_observation()
        info = self._get_info()

        return obs, reward, terminated, truncated, info
```

---

## 🔄 訓練循環

### DQN 訓練流程

```python
def train_dqn(env, agent, episodes=500):
    """DQN 訓練主循環

    SOURCE: Mnih et al. (2015) Nature, Algorithm 1
    """

    for episode in range(episodes):
        # Gymnasium API: reset() 返回 (obs, info)
        state, info = env.reset()
        episode_reward = 0

        while True:
            # 選擇動作（ε-greedy）
            action = agent.select_action(state)

            # Gymnasium API: step() 返回 5-tuple
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            # 存入 Replay Buffer
            agent.memory.push(state, action, reward, next_state, done)

            # 訓練 Q-Network
            if len(agent.memory) > agent.batch_size:
                agent.train_step()

            state = next_state
            episode_reward += reward

            if done:
                break

        # 更新 Target Network
        if episode % agent.target_update_freq == 0:
            agent.update_target_network()

        # 記錄訓練進度
        logger.log_episode(episode, episode_reward)
```

---

## ⏱️ 實施計畫

詳見 [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) Phase 2

### Day 3: DQN 核心實現
- Q-Network 實現
- Experience Replay 實現
- Target Network 更新機制

### Day 4: Gymnasium 環境
- SatelliteHandoverEnv 實現
- 狀態/動作空間定義
- 獎勵函數整合

### Day 5: 訓練循環整合
- 訓練主循環
- ε-greedy 探索策略
- TensorBoard 日誌記錄
- 單元測試

---

## ✅ 驗收標準

- [ ] DQN Agent 正確實現（Q-Network + Target Network）
- [ ] Experience Replay 正常運作
- [ ] Gymnasium 環境符合 API 規範
- [ ] 訓練循環可以完整執行
- [ ] ε-greedy 探索策略正確實現
- [ ] Target Network 定期更新
- [ ] TensorBoard 正確記錄訓練指標
- [ ] 單元測試覆蓋率 > 80%
- [ ] 所有函數有 SOURCE 標註

---

## 🔬 測試策略

### 單元測試
```python
def test_q_network_forward():
    """測試 Q-Network 前向傳播"""
    net = QNetwork(state_dim=6, action_dim=4)
    state = torch.randn(32, 6)
    q_values = net(state)
    assert q_values.shape == (32, 4)

def test_replay_buffer():
    """測試 Experience Replay"""
    buffer = ReplayBuffer(capacity=1000)
    buffer.push(state, action, reward, next_state, done)
    batch = buffer.sample(32)
    assert len(batch) == 32

def test_gymnasium_environment():
    """測試 Gymnasium 環境 API"""
    env = SatelliteHandoverEnv(data_path="test_data.h5")

    # 測試 reset() 返回 (obs, info)
    obs, info = env.reset()
    assert obs.shape == (6,)
    assert isinstance(info, dict)

    # 測試 step() 返回 5-tuple
    obs, reward, terminated, truncated, info = env.step(0)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
```

---

## 📚 參考文獻

1. **Mnih et al. (2015)** - "Human-level control through deep reinforcement learning", Nature 518(7540):529-533
   - DQN 核心算法
   - Experience Replay
   - Target Network

2. **Brockman et al. (2016)** - "OpenAI Gym", arXiv:1606.01540
   - Gym 環境設計原則

3. **Towers et al. (2023)** - "Gymnasium: A Standard Interface for Reinforcement Learning Environments"
   - Gymnasium API 規範
   - 與 OpenAI Gym 的差異

---

**文檔狀態**: ✅ 完成
**下一階段**: [05-PHASE3-TRAINING.md](05-PHASE3-TRAINING.md)
