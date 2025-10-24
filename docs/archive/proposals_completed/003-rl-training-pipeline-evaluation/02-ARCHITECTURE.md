# Proposal 003: 系統架構 (Architecture)

**文檔版本**: v2.0
**最後更新**: 2025-10-23

---

## 🏗️ 總體架構

### 系統概覽

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Proposal 003 System Architecture                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   Stage 6 Outputs    │
│   (JSON Files)       │
│                      │
│ • signal_analysis    │
│ • scenario_variants  │ ← Proposal 002
│ • gpp_events         │
│ • pool_verification  │
└──────────┬───────────┘
           │
           │ 讀取 (不修改!)
           │
           ▼
┌─────────────────────────────────────┐
│   ML Training Data Generator        │  ← Phase 1
│   (獨立工具)                         │
│                                      │
│ ├─ JSON Parser                      │
│ ├─ State Extractor                  │
│ ├─ Reward Calculator                │
│ └─ HDF5 Writer                      │
└──────────┬──────────────────────────┘
           │
           │ 生成
           ▼
┌─────────────────────────┐
│   RL Training Dataset   │
│   (HDF5 Format)         │
│                         │
│ ├─ train/ (70%)         │
│ ├─ val/ (15%)           │
│ └─ test/ (15%)          │
└──────────┬──────────────┘
           │
           │ 載入
           ▼
┌─────────────────────────────────────────┐
│   DQN Training System                    │  ← Phase 2 + 3
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Gymnasium Environment              │  │
│ │ (SatelliteHandoverEnv)             │  │
│ │                                    │  │
│ │ • observation_space                │  │
│ │ • action_space                     │  │
│ │ • reset() / step()                 │  │
│ └────────────┬───────────────────────┘  │
│              │                           │
│              ▼                           │
│ ┌────────────────────────────────────┐  │
│ │ DQN Agent                          │  │
│ │                                    │  │
│ │ ├─ Q-Network (PyTorch)             │  │
│ │ ├─ Target Network                  │  │
│ │ ├─ Experience Replay Buffer        │  │
│ │ └─ ε-greedy Policy                 │  │
│ └────────────┬───────────────────────┘  │
│              │                           │
│              ▼                           │
│ ┌────────────────────────────────────┐  │
│ │ Training Pipeline                  │  │
│ │                                    │  │
│ │ ├─ Training Loop                   │  │
│ │ ├─ Checkpoint Manager              │  │
│ │ ├─ TensorBoard Logger              │  │
│ │ └─ Config Manager                  │  │
│ └────────────┬───────────────────────┘  │
└──────────────┼──────────────────────────┘
               │
               │ 輸出
               ▼
┌────────────────────────┐
│   Trained DQN Model    │
│   (*.pt checkpoints)   │
└────────────┬───────────┘
             │
             │ 評估
             ▼
┌──────────────────────────────────────┐
│   Evaluation Framework               │  ← Phase 4
│                                      │
│ ├─ Metrics Calculator                │
│ ├─ Baseline Comparator (RSRP-based) │
│ ├─ Scenario Analyzer (12 variants)  │
│ └─ Report Generator                  │
└──────────┬───────────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Evaluation Report  │
│  (Markdown + Plots) │
└─────────────────────┘
```

---

## 📦 模組設計

### Module 1: ML Training Data Generator

**路徑**: `tools/ml_training_data_generator/`

#### 1.1 JSON Parser

```python
# json_parser.py
class Stage6OutputParser:
    """解析 Stage 6 JSON 輸出"""

    def parse_file(self, json_path: str) -> Stage6Output:
        """解析單個 JSON 文件"""

    def parse_batch(self, json_dir: str) -> List[Stage6Output]:
        """批量解析目錄中的 JSON 文件"""

    def validate_schema(self, data: dict) -> bool:
        """驗證 JSON schema 完整性"""
```

**關鍵功能**:
- 解析 Stage 6 標準輸出格式
- 提取 signal_analysis, scenario_variants, gpp_events 等字段
- Schema 驗證（確保必要字段存在）

#### 1.2 State Extractor

```python
# state_extractor.py
class StateExtractor:
    """從 Stage 6 輸出提取 RL 狀態"""

    def extract_state(self, stage6_output: Stage6Output,
                     timestamp_idx: int) -> RLState:
        """提取指定時間點的狀態"""

    def extract_serving_satellite(self, signal_analysis: dict) -> SatelliteState:
        """提取服務衛星狀態（信號最強）"""

    def extract_candidates(self, signal_analysis: dict,
                          max_candidates: int = 5) -> List[SatelliteState]:
        """提取候選衛星（信號次強的 K 個）"""

    def extract_qos_requirements(self, scenario_variant: dict) -> QoSRequirements:
        """從場景變體提取 QoS 需求"""

    def extract_network_load(self, scenario_variant: dict) -> NetworkLoadState:
        """從場景變體提取網絡負載"""
```

**狀態表示**:
```python
@dataclass
class RLState:
    serving_satellite: SatelliteState
    candidate_satellites: List[SatelliteState]  # 最多 5 個
    qos_requirements: QoSRequirements
    network_load: NetworkLoadState
    time_features: TimeFeatures  # hour, day_of_week 等

    def to_numpy(self) -> np.ndarray:
        """轉換為 numpy array（用於神經網絡輸入）"""
```

#### 1.3 Reward Calculator

```python
# reward_calculator.py
class RewardCalculator:
    """計算獎勵函數"""

    def compute_reward(self,
                      state: RLState,
                      action: int,
                      next_state: RLState) -> float:
        """
        計算 (state, action, next_state) 的獎勵

        SOURCE: Badini et al. (2024) IEEE TAES, Equation (5)
        """

    def compute_qos_satisfaction(self,
                                state: RLState,
                                qos_req: QoSRequirements) -> float:
        """計算 QoS 滿足度（1.0 或 -1.0）"""

    def compute_signal_quality_score(self, sat_state: SatelliteState) -> float:
        """計算信號品質分數（0.0 ~ 1.0）"""

    def compute_handover_cost(self, action: int) -> float:
        """計算換手成本（action 0: 無成本，其他: 有成本）"""
```

**獎勵函數實現**:
```python
reward = (
    0.5 * qos_satisfaction +      # QoS 滿足獎勵
    0.3 * signal_quality_score -  # 信號品質獎勵
    0.2 * handover_cost           # 換手成本懲罰
)

# QoS 滿足度
qos_satisfaction = 1.0 if meets_all_qos() else -1.0

# 信號品質分數（歸一化到 0-1）
signal_quality = (rsrp + 140) / 60  # 假設 RSRP 範圍 -140 ~ -80 dBm

# 換手成本
handover_cost = 0.0 if action == 0 else 0.2
if is_unnecessary_handover():
    handover_cost += 0.3  # 額外懲罰
```

#### 1.4 Dataset Builder

```python
# dataset_builder.py
class RLDatasetBuilder:
    """構建 RL 訓練數據集"""

    def build_dataset(self,
                     stage6_outputs: List[Stage6Output],
                     output_path: str):
        """構建完整數據集並保存為 HDF5"""

    def generate_transitions(self, stage6_output: Stage6Output) -> List[Transition]:
        """從單個 Stage 6 輸出生成 transitions"""

    def split_dataset(self, transitions: List[Transition],
                     train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """分割數據集"""

    def save_to_hdf5(self, dataset: dict, output_path: str):
        """保存為 HDF5 格式"""

    def validate_dataset(self, dataset_path: str) -> ValidationReport:
        """驗證數據集完整性和質量"""
```

**HDF5 數據結構**:
```python
with h5py.File('dataset.h5', 'w') as f:
    # Train split
    train_group = f.create_group('train')
    train_group.create_dataset('states', data=train_states, compression='gzip')
    train_group.create_dataset('actions', data=train_actions)
    train_group.create_dataset('rewards', data=train_rewards)
    train_group.create_dataset('next_states', data=train_next_states, compression='gzip')
    train_group.create_dataset('dones', data=train_dones)

    # Metadata
    train_group.attrs['num_samples'] = len(train_states)
    train_group.attrs['state_dim'] = state_dim
    train_group.attrs['action_dim'] = action_dim

    # Val and test splits (same structure)
    val_group = f.create_group('val')
    test_group = f.create_group('test')
```

---

### Module 2: DQN Implementation

**路徑**: `tools/rl_algorithms/dqn/`

#### 2.1 Gymnasium Environment

```python
# envs/satellite_handover_env.py
import gymnasium as gym
from gymnasium import spaces

class SatelliteHandoverEnv(gym.Env):
    """
    衛星換手 Gymnasium 環境

    Observation Space:
        Box(low=-inf, high=inf, shape=(state_dim,))

    Action Space:
        Discrete(N+1) where N is max_satellites
        - 0: Stay with serving satellite
        - 1~N: Handover to candidate i

    Reward:
        Based on QoS satisfaction, signal quality, handover cost
    """

    metadata = {'render_modes': ['human']}

    def __init__(self, dataset_path: str, split: str = 'train'):
        super().__init__()

        # 載入數據集
        self.dataset = self._load_dataset(dataset_path, split)

        # 定義空間
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(self.state_dim,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(self.max_satellites + 1)

    def reset(self, seed=None, options=None):
        """重置環境（Gymnasium API）"""
        super().reset(seed=seed)

        # 隨機選擇一個 episode
        self.current_episode = self._sample_episode()
        self.step_idx = 0

        obs = self.current_episode['states'][0]
        info = {'episode_id': self.current_episode['id']}

        return obs, info

    def step(self, action):
        """執行動作（Gymnasium API）"""
        # 獲取當前 transition
        state = self.current_episode['states'][self.step_idx]
        reward = self.current_episode['rewards'][self.step_idx]
        next_state = self.current_episode['next_states'][self.step_idx]
        done = self.current_episode['dones'][self.step_idx]

        self.step_idx += 1

        # 檢查是否超過 episode 長度
        terminated = done or (self.step_idx >= len(self.current_episode['states']))
        truncated = False  # 我們的數據集沒有 truncation

        info = {}

        return next_state, reward, terminated, truncated, info
```

#### 2.2 Q-Network

```python
# networks/q_network.py
import torch
import torch.nn as nn

class QNetwork(nn.Module):
    """
    Q-Network 架構

    SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B
    Architecture: Input → FC(256) → ReLU → FC(256) → ReLU → Output
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dims=[256, 256]):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[1], action_dim)
        )

    def forward(self, state):
        """
        Forward pass

        Args:
            state: (batch_size, state_dim)

        Returns:
            q_values: (batch_size, action_dim)
        """
        return self.network(state)
```

#### 2.3 DQN Agent

```python
# dqn_agent.py
class DQNAgent:
    """
    DQN Agent 實現

    SOURCE: Mnih et al. (2015) "Human-level control through deep RL"
    """

    def __init__(self, config: dict):
        self.state_dim = config['state_dim']
        self.action_dim = config['action_dim']

        # Q-network and target network
        self.q_network = QNetwork(self.state_dim, self.action_dim).to(device)
        self.target_network = QNetwork(self.state_dim, self.action_dim).to(device)
        self.target_network.load_state_dict(self.q_network.state_dict())

        # Optimizer
        self.optimizer = torch.optim.Adam(
            self.q_network.parameters(),
            lr=config['learning_rate']
        )

        # Experience replay
        self.replay_buffer = ReplayBuffer(config['buffer_size'])

        # Hyperparameters (SOURCE: Badini et al. 2024, Table II)
        self.gamma = config['gamma']  # 0.99
        self.epsilon = config['epsilon_start']  # 1.0
        self.epsilon_end = config['epsilon_end']  # 0.01
        self.epsilon_decay = config['epsilon_decay']  # 0.995
        self.batch_size = config['batch_size']  # 64
        self.target_update_freq = config['target_update_freq']  # 1000

        self.steps = 0

    def select_action(self, state, training=True):
        """ε-greedy 動作選擇"""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
                q_values = self.q_network(state_tensor)
                return q_values.argmax(1).item()

    def store_experience(self, state, action, reward, next_state, done):
        """存儲經驗到 replay buffer"""
        self.replay_buffer.push(state, action, reward, next_state, done)

    def train_step(self):
        """訓練一步"""
        if len(self.replay_buffer) < self.batch_size:
            return None

        # Sample batch
        batch = self.replay_buffer.sample(self.batch_size)
        states, actions, rewards, next_states, dones = batch

        # Convert to tensors
        states = torch.FloatTensor(states).to(device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(device)
        next_states = torch.FloatTensor(next_states).to(device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(device)

        # Compute current Q values
        current_q_values = self.q_network(states).gather(1, actions)

        # Compute target Q values
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0].unsqueeze(1)
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values

        # Compute loss
        loss = nn.MSELoss()(current_q_values, target_q_values)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update target network
        self.steps += 1
        if self.steps % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return loss.item()
```

---

### Module 3: Training Pipeline

**路徑**: `tools/rl_training/`

```python
# training_pipeline.py
class TrainingPipeline:
    """DQN 訓練管道"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)

        # Initialize environment
        self.env = SatelliteHandoverEnv(
            dataset_path=self.config['dataset']['path'],
            split='train'
        )
        self.val_env = SatelliteHandoverEnv(
            dataset_path=self.config['dataset']['path'],
            split='val'
        )

        # Initialize agent
        self.agent = DQNAgent(self.config['algorithm'])

        # Initialize logger
        self.logger = TensorBoardLogger(self.config['logging']['log_dir'])

        # Initialize checkpoint manager
        self.checkpoint_manager = CheckpointManager(
            save_dir=self.config['logging']['log_dir'] + '/checkpoints'
        )

    def train(self, num_episodes: int):
        """主訓練循環"""
        for episode in range(num_episodes):
            # Train one episode
            episode_metrics = self._train_episode()

            # Log metrics
            self.logger.log_scalar('train/episode_reward', episode_metrics['reward'], episode)
            self.logger.log_scalar('train/loss', episode_metrics['loss'], episode)
            self.logger.log_scalar('train/epsilon', self.agent.epsilon, episode)

            # Evaluate
            if episode % self.config['training']['eval_frequency'] == 0:
                eval_metrics = self._evaluate()
                self.logger.log_dict('eval', eval_metrics, episode)

            # Save checkpoint
            if episode % self.config['training']['checkpoint_frequency'] == 0:
                self.checkpoint_manager.save(self.agent, episode)

    def _train_episode(self):
        """訓練一個 episode"""
        state, _ = self.env.reset()
        episode_reward = 0
        episode_loss = []

        done = False
        while not done:
            # Select action
            action = self.agent.select_action(state, training=True)

            # Step environment
            next_state, reward, terminated, truncated, _ = self.env.step(action)
            done = terminated or truncated

            # Store experience
            self.agent.store_experience(state, action, reward, next_state, done)

            # Train
            loss = self.agent.train_step()
            if loss is not None:
                episode_loss.append(loss)

            state = next_state
            episode_reward += reward

        return {
            'reward': episode_reward,
            'loss': np.mean(episode_loss) if episode_loss else 0.0
        }
```

---

### Module 4: Evaluation Framework

**路徑**: `tools/rl_evaluation/`

```python
# evaluator.py
class RLEvaluator:
    """RL Agent 評估器"""

    def evaluate(self, agent, env, num_episodes=100):
        """評估 agent 性能"""
        metrics = {
            'episode_rewards': [],
            'handover_counts': [],
            'qos_satisfactions': [],
            # ... 其他指標
        }

        for _ in range(num_episodes):
            episode_metrics = self._evaluate_episode(agent, env)
            for key in metrics:
                metrics[key].append(episode_metrics[key])

        # 聚合指標
        aggregated_metrics = {
            'avg_reward': np.mean(metrics['episode_rewards']),
            'handover_success_rate': self._compute_success_rate(metrics),
            'qos_satisfaction_rate': np.mean(metrics['qos_satisfactions']),
            # ...
        }

        return aggregated_metrics

    def compare_with_baseline(self, dqn_metrics, baseline_metrics):
        """與基線對比"""
        comparison = {}
        for metric_name in dqn_metrics:
            dqn_value = dqn_metrics[metric_name]
            baseline_value = baseline_metrics[metric_name]
            improvement = ((dqn_value - baseline_value) / baseline_value) * 100

            comparison[metric_name] = {
                'dqn': dqn_value,
                'baseline': baseline_value,
                'improvement_pct': improvement
            }

        # 統計顯著性檢驗
        p_value = self._significance_test(dqn_metrics, baseline_metrics)
        comparison['statistical_significance'] = p_value < 0.05

        return comparison
```

---

## 🔗 模組間接口

### 接口 1: Stage 6 → ML Data Generator

**輸入**: Stage 6 JSON 文件
**輸出**: HDF5 訓練數據

```python
# 使用方式
from ml_training_data_generator import RLDatasetBuilder

builder = RLDatasetBuilder()
builder.build_dataset(
    input_dir='data/outputs/stage6/',
    output_path='data/rl_training/dataset_v1.h5',
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15
)
```

### 接口 2: Dataset → Training Pipeline

**輸入**: HDF5 數據集
**輸出**: 訓練好的模型

```python
# 使用方式
from rl_training import TrainingPipeline

pipeline = TrainingPipeline(config_path='config/rl_training/dqn_config.yaml')
pipeline.train(num_episodes=500)
```

### 接口 3: Trained Model → Evaluation

**輸入**: 模型檢查點
**輸出**: 評估報告

```python
# 使用方式
from rl_evaluation import RLEvaluator, ReportGenerator

evaluator = RLEvaluator()
dqn_metrics = evaluator.evaluate(agent, test_env, num_episodes=100)
baseline_metrics = evaluator.evaluate_baseline(test_env, method='rsrp')

report_gen = ReportGenerator()
report_gen.generate_report(
    dqn_metrics=dqn_metrics,
    baseline_metrics=baseline_metrics,
    output_path='reports/evaluation_report.md'
)
```

---

## 📂 目錄結構

```
orbit-engine/
├── tools/
│   ├── ml_training_data_generator/
│   │   ├── __init__.py
│   │   ├── json_parser.py
│   │   ├── state_extractor.py
│   │   ├── reward_calculator.py
│   │   ├── dataset_builder.py
│   │   └── data_formats.py
│   │
│   ├── rl_algorithms/
│   │   ├── __init__.py
│   │   ├── envs/
│   │   │   ├── __init__.py
│   │   │   └── satellite_handover_env.py
│   │   ├── dqn/
│   │   │   ├── __init__.py
│   │   │   ├── dqn_agent.py
│   │   │   └── networks/
│   │   │       ├── __init__.py
│   │   │       └── q_network.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── replay_buffer.py
│   │
│   ├── rl_training/
│   │   ├── __init__.py
│   │   ├── training_pipeline.py
│   │   ├── config_manager.py
│   │   ├── checkpoint_manager.py
│   │   └── logger.py
│   │
│   └── rl_evaluation/
│       ├── __init__.py
│       ├── evaluator.py
│       ├── metrics.py
│       ├── baselines/
│       │   ├── __init__.py
│       │   ├── rsrp_based.py
│       │   └── distance_based.py
│       └── report_generator.py
│
├── config/
│   └── rl_training/
│       └── dqn_config.yaml
│
├── scripts/
│   ├── generate_rl_dataset.py
│   ├── train_dqn.py
│   └── evaluate_dqn.py
│
└── data/
    └── rl_training/
        └── dataset_v1.h5
```

---

**文檔狀態**: ✅ 完成
**下一篇**: [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) - 實施計畫
