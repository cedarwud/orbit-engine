# Proposal 003: 實施計畫 (Implementation Plan)

**文檔版本**: v2.0
**最後更新**: 2025-10-23

---

## ⏱️ 總體時間線

```
┌───────────────────────────────────────────────────────────────┐
│           Proposal 003 Implementation Timeline                 │
│                   Total: 7-10 Days                             │
└───────────────────────────────────────────────────────────────┘

Week 1: Days 1-5
├─ Day 1-2: Phase 1 - ML Data Generator
│  ├─ Day 1: 數據格式設計 + JSON Parser
│  └─ Day 2: State Extractor + Reward Calculator + Dataset Builder
│
└─ Day 3-5: Phase 2 - DQN Implementation
   ├─ Day 3: Gymnasium Environment + Q-Network
   ├─ Day 4: DQN Agent + Replay Buffer
   └─ Day 5: 訓練測試與調試

Week 2: Days 6-10
├─ Day 6-7: Phase 3 - Training Pipeline
│  ├─ Day 6: Training Loop + Config Manager
│  └─ Day 7: Checkpoint Manager + TensorBoard Logger
│
├─ Day 8-9: Phase 4 - Evaluation Framework
│  ├─ Day 8: Metrics + Baselines
│  └─ Day 9: Report Generator + Visualization
│
└─ Day 10: Integration Testing & Documentation
   ├─ End-to-end testing
   ├─ Documentation updates
   └─ Final report
```

---

## 📋 Phase 1: ML Data Generator (Day 1-2)

### Day 1: 數據格式設計 + JSON Parser

**時間**: 1 天

#### 任務 1.1: 數據格式定義 (2 小時)

**目標**: 定義 RL 訓練數據的標準格式

**交付物**:
```python
# tools/ml_training_data_generator/data_formats.py

@dataclass
class RLState:
    """RL 狀態表示"""
    serving_satellite: SatelliteState
    candidate_satellites: List[SatelliteState]
    qos_requirements: QoSRequirements
    network_load: NetworkLoadState
    time_features: TimeFeatures

@dataclass
class Transition:
    """RL transition 元組"""
    state: RLState
    action: int
    reward: float
    next_state: RLState
    done: bool
    metadata: dict
```

**驗收標準**:
- ✅ 所有數據類定義完整
- ✅ 包含 docstring 和 SOURCE 標註
- ✅ Type hints 完整

#### 任務 1.2: JSON Parser 實現 (3 小時)

**目標**: 解析 Stage 6 JSON 輸出

**交付物**:
```python
# tools/ml_training_data_generator/json_parser.py

class Stage6OutputParser:
    def parse_file(self, json_path: str) -> Stage6Output
    def parse_batch(self, json_dir: str) -> List[Stage6Output]
    def validate_schema(self, data: dict) -> bool
```

**測試**:
- 單個文件解析測試
- 批量文件解析測試
- Schema 驗證測試
- 錯誤處理測試

**驗收標準**:
- ✅ 正確解析 Stage 6 JSON
- ✅ 場景變體正確提取（12 種）
- ✅ 單元測試覆蓋率 > 80%

#### 任務 1.3: 測試與驗證 (3 小時)

**測試數據準備**:
```bash
# 使用實際的 Stage 6 輸出進行測試
cp data/outputs/stage6/stage6_research_optimization_*.json tests/fixtures/
```

**測試腳本**:
```python
# tests/test_json_parser.py

def test_parse_single_file():
    parser = Stage6OutputParser()
    output = parser.parse_file('tests/fixtures/stage6_output.json')
    assert output is not None
    assert len(output.scenario_variants) == 12

def test_validate_schema():
    parser = Stage6OutputParser()
    valid_data = {...}
    assert parser.validate_schema(valid_data) == True
```

---

### Day 2: State Extractor + Reward Calculator + Dataset Builder

**時間**: 1 天

#### 任務 2.1: State Extractor 實現 (3 小時)

**目標**: 從 Stage 6 輸出提取 RL 狀態

**交付物**:
```python
# tools/ml_training_data_generator/state_extractor.py

class StateExtractor:
    def extract_state(self, stage6_output, timestamp_idx) -> RLState
    def extract_serving_satellite(self, signal_analysis) -> SatelliteState
    def extract_candidates(self, signal_analysis, max_k=5) -> List[SatelliteState]
    def extract_qos_requirements(self, scenario_variant) -> QoSRequirements
    def extract_network_load(self, scenario_variant) -> NetworkLoadState
```

**驗收標準**:
- ✅ 服務衛星選擇邏輯正確（信號最強）
- ✅ 候選衛星數量正確（最多 5 個）
- ✅ QoS 需求正確提取（基於流量類型）
- ✅ 網絡負載正確提取（基於負載模式）

#### 任務 2.2: Reward Calculator 實現 (2 小時)

**目標**: 實現獎勵函數

**交付物**:
```python
# tools/ml_training_data_generator/reward_calculator.py

class RewardCalculator:
    def compute_reward(self, state, action, next_state) -> float:
        """
        SOURCE: Badini et al. (2024) IEEE TAES, Equation (5)
        """

    def compute_qos_satisfaction(self, state, qos_req) -> float
    def compute_signal_quality_score(self, sat_state) -> float
    def compute_handover_cost(self, action) -> float
```

**驗收標準**:
- ✅ 獎勵計算與論文一致
- ✅ QoS 滿足邏輯正確
- ✅ 單元測試覆蓋各種情況

#### 任務 2.3: Dataset Builder 實現 (3 小時)

**目標**: 構建完整的訓練數據集

**交付物**:
```python
# tools/ml_training_data_generator/dataset_builder.py

class RLDatasetBuilder:
    def build_dataset(self, stage6_outputs, output_path)
    def generate_transitions(self, stage6_output) -> List[Transition]
    def split_dataset(self, transitions, train=0.7, val=0.15, test=0.15)
    def save_to_hdf5(self, dataset, output_path)
    def validate_dataset(self, dataset_path) -> ValidationReport
```

**驗收標準**:
- ✅ HDF5 文件格式正確
- ✅ 數據集分割比例正確
- ✅ 12 種場景變體均衡分佈

---

## 📋 Phase 2: DQN Implementation (Day 3-5)

### Day 3: Gymnasium Environment + Q-Network

**時間**: 1 天

#### 任務 3.1: Gymnasium Environment (4 小時)

**目標**: 實現 `SatelliteHandoverEnv`

**交付物**:
```python
# tools/rl_algorithms/envs/satellite_handover_env.py

class SatelliteHandoverEnv(gym.Env):
    def __init__(self, dataset_path, split='train')
    def reset(self, seed=None, options=None) -> Tuple[obs, info]
    def step(self, action) -> Tuple[obs, reward, terminated, truncated, info]
    def _load_dataset(self, path, split)
    def _sample_episode(self)
```

**測試**:
```python
# tests/test_satellite_handover_env.py

def test_environment_creation():
    env = SatelliteHandoverEnv('data/rl_training/dataset_v1.h5', split='train')
    assert env.observation_space.shape[0] > 0
    assert env.action_space.n > 0

def test_reset():
    env = SatelliteHandoverEnv('data/rl_training/dataset_v1.h5')
    obs, info = env.reset(seed=42)
    assert obs.shape == env.observation_space.shape

def test_step():
    env = SatelliteHandoverEnv('data/rl_training/dataset_v1.h5')
    obs, _ = env.reset()
    next_obs, reward, terminated, truncated, info = env.step(0)
    assert next_obs.shape == obs.shape
```

**驗收標準**:
- ✅ 符合 Gymnasium v0.29+ API
- ✅ 通過 Gymnasium API check
- ✅ 單元測試通過

#### 任務 3.2: Q-Network 實現 (2 小時)

**目標**: 實現 Q-network 架構

**交付物**:
```python
# tools/rl_algorithms/dqn/networks/q_network.py

class QNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
        """
        SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B
        """

    def forward(self, state) -> torch.Tensor
```

**測試**:
```python
def test_q_network_forward():
    net = QNetwork(state_dim=50, action_dim=6)
    state = torch.randn(32, 50)
    q_values = net(state)
    assert q_values.shape == (32, 6)
```

**驗收標準**:
- ✅ 網絡結構與論文一致
- ✅ 支持 GPU
- ✅ Forward pass 測試通過

#### 任務 3.3: Replay Buffer 實現 (2 小時)

**目標**: 實現經驗回放緩衝區

**交付物**:
```python
# tools/rl_algorithms/utils/replay_buffer.py

class ReplayBuffer:
    def __init__(self, capacity):
    def push(self, state, action, reward, next_state, done):
    def sample(self, batch_size) -> List[Transition]:
    def __len__(self) -> int
```

**驗收標準**:
- ✅ FIFO 行為正確
- ✅ 隨機採樣正確
- ✅ 記憶體效率測試通過

---

### Day 4: DQN Agent 實現

**時間**: 1 天

#### 任務 4.1: DQN Agent 核心邏輯 (5 小時)

**目標**: 實現 DQN 核心算法

**交付物**:
```python
# tools/rl_algorithms/dqn/dqn_agent.py

class DQNAgent:
    def __init__(self, config):
    def select_action(self, state, training=True) -> int
    def store_experience(self, state, action, reward, next_state, done):
    def train_step(self) -> float
    def update_target_network(self):
```

**關鍵邏輯**:
- ε-greedy exploration
- Q-learning update rule
- Target network 更新
- ε 衰減

**驗收標準**:
- ✅ DQN 算法正確實現
- ✅ Loss 計算正確
- ✅ Target network 更新邏輯正確

#### 任務 4.2: 單元測試 (3 小時)

**測試**:
```python
def test_epsilon_greedy():
    agent = DQNAgent(config)
    # Test exploration
    agent.epsilon = 1.0
    actions = [agent.select_action(state) for _ in range(100)]
    assert len(set(actions)) > 1  # Should be random

    # Test exploitation
    agent.epsilon = 0.0
    actions = [agent.select_action(state) for _ in range(100)]
    assert len(set(actions)) == 1  # Should be deterministic

def test_train_step():
    agent = DQNAgent(config)
    # Fill replay buffer
    for _ in range(1000):
        agent.store_experience(...)

    loss = agent.train_step()
    assert loss is not None
    assert loss > 0
```

**驗收標準**:
- ✅ 所有核心功能有單元測試
- ✅ 測試覆蓋率 > 80%

---

### Day 5: 訓練測試與調試

**時間**: 1 天

#### 任務 5.1: 小規模訓練測試 (3 小時)

**目標**: 驗證訓練流程可運行

**測試腳本**:
```python
# scripts/test_train_dqn.py

# 使用小規模數據集測試
config = {
    'dataset': {'path': 'data/rl_training/dataset_v1.h5'},
    'training': {'num_episodes': 10},  # 只訓練 10 個 episode
    ...
}

pipeline = TrainingPipeline(config)
pipeline.train(num_episodes=10)
```

**驗證點**:
- ✅ 訓練循環正常運行
- ✅ Loss 有下降趨勢
- ✅ Epsilon 正常衰減
- ✅ TensorBoard 可視化正常

#### 任務 5.2: 調試與優化 (3 小時)

**調試項目**:
- GPU 利用率優化
- 內存使用監控
- 訓練速度優化
- 錯誤處理改進

#### 任務 5.3: 文檔更新 (2 小時)

**更新文檔**:
- README with usage examples
- API documentation
- Troubleshooting guide

---

## 📋 Phase 3: Training Pipeline (Day 6-7)

### Day 6: Training Loop + Config Manager

**時間**: 1 天

#### 任務 6.1: Config Manager (2 小時)

**交付物**:
```python
# tools/rl_training/config_manager.py

class ConfigManager:
    def load_config(self, path: str) -> dict
    def validate_config(self, config: dict) -> bool
    def merge_configs(self, base, override) -> dict
```

**配置文件模板**:
```yaml
# config/rl_training/dqn_config.yaml
experiment:
  name: "dqn_satellite_handover_v1"
  seed: 42
  device: "cuda"

dataset:
  path: "data/rl_training/dataset_v1.h5"
  # ...

algorithm:
  type: "dqn"
  hyperparameters:
    learning_rate: 0.0001
    gamma: 0.99
    # ...

training:
  num_episodes: 500
  checkpoint_frequency: 50
  eval_frequency: 10
```

#### 任務 6.2: Training Pipeline 實現 (4 小時)

**交付物**:
```python
# tools/rl_training/training_pipeline.py

class TrainingPipeline:
    def __init__(self, config_path: str)
    def train(self, num_episodes: int)
    def _train_episode(self) -> dict
    def _evaluate(self) -> dict
```

#### 任務 6.3: 測試 (2 小時)

**驗收標準**:
- ✅ 完整訓練流程可運行
- ✅ 配置文件正確解析
- ✅ 評估正常執行

---

### Day 7: Checkpoint Manager + TensorBoard Logger

**時間**: 1 天

#### 任務 7.1: Checkpoint Manager (3 小時)

**交付物**:
```python
# tools/rl_training/checkpoint_manager.py

class CheckpointManager:
    def save(self, agent, episode, metrics)
    def load(self, checkpoint_path) -> agent
    def list_checkpoints(self) -> List[str]
    def cleanup_old_checkpoints(self, keep_last=5)
```

#### 任務 7.2: TensorBoard Logger (3 小時)

**交付物**:
```python
# tools/rl_training/logger.py

class TensorBoardLogger:
    def log_scalar(self, tag, value, step)
    def log_dict(self, prefix, metrics_dict, step)
    def log_histogram(self, tag, values, step)
```

#### 任務 7.3: 整合測試 (2 小時)

**驗收標準**:
- ✅ 檢查點保存/恢復正常
- ✅ TensorBoard 可視化正常
- ✅ 日誌記錄完整

---

## 📋 Phase 4: Evaluation Framework (Day 8-9)

### Day 8: Metrics + Baselines

**時間**: 1 天

#### 任務 8.1: Metrics 實現 (3 小時)

**交付物**:
```python
# tools/rl_evaluation/metrics.py

class MetricsCalculator:
    def compute_handover_success_rate(self, episodes) -> float
    def compute_qos_satisfaction_rate(self, episodes) -> float
    def compute_avg_reward(self, episodes) -> float
    # ... 其他指標
```

#### 任務 8.2: Baseline 算法 (3 小時)

**交付物**:
```python
# tools/rl_evaluation/baselines/rsrp_based.py

class RSRPBasedHandover:
    def decide_handover(self, state) -> int:
        """
        SOURCE: 3GPP TS 38.331 A3 event
        """
```

#### 任務 8.3: 評估器實現 (2 小時)

**交付物**:
```python
# tools/rl_evaluation/evaluator.py

class RLEvaluator:
    def evaluate(self, agent, env, num_episodes=100) -> dict
    def evaluate_baseline(self, env, method='rsrp') -> dict
    def compare_with_baseline(self, dqn_metrics, baseline_metrics) -> dict
```

---

### Day 9: Report Generator + Visualization

**時間**: 1 天

#### 任務 9.1: Report Generator (4 小時)

**交付物**:
```python
# tools/rl_evaluation/report_generator.py

class ReportGenerator:
    def generate_report(self, dqn_metrics, baseline_metrics, output_path)
    def _generate_summary_table(self, metrics) -> str
    def _generate_scenario_analysis(self, metrics) -> str
    def _generate_plots(self, metrics) -> List[str]
```

**報告結構**:
```markdown
# Evaluation Report

## 整體性能
| Metric | DQN | RSRP-Baseline | Improvement |
|--------|-----|---------------|-------------|
| ...

## 場景分析
### 各流量類型
### 各負載模式

## 統計檢驗
```

#### 任務 9.2: Visualization (3 小時)

**圖表**:
- Learning curves
- Performance comparison bar charts
- Scenario analysis heatmaps

#### 任務 9.3: 測試 (1 小時)

**驗收標準**:
- ✅ 報告自動生成
- ✅ 圖表正確嵌入
- ✅ 統計檢驗正確

---

## 📋 Day 10: Integration Testing & Documentation

**時間**: 1 天

### 任務 10.1: 端到端測試 (3 小時)

**測試流程**:
```bash
# 1. 生成 RL 數據集
python scripts/generate_rl_dataset.py \
  --input data/outputs/stage6/ \
  --output data/rl_training/dataset_v1.h5

# 2. 訓練 DQN
python scripts/train_dqn.py \
  --config config/rl_training/dqn_config.yaml \
  --num-episodes 500

# 3. 評估
python scripts/evaluate_dqn.py \
  --checkpoint logs/dqn_v1/checkpoints/episode_500.pt \
  --output reports/evaluation_report.md
```

**驗收標準**:
- ✅ 完整流程無錯誤運行
- ✅ DQN 性能優於 baseline
- ✅ 報告生成正常

### 任務 10.2: 文檔完善 (3 小時)

**更新文檔**:
- User guide
- API documentation
- Troubleshooting guide
- Performance benchmarks

### 任務 10.3: 最終報告 (2 小時)

**創建文檔**:
- FINAL_COMPLETION_REPORT.md
- 總結所有成果
- 記錄遇到的問題和解決方案

---

## 📊 里程碑檢查點

| 里程碑 | 日期 | 驗收標準 |
|--------|------|---------|
| M1: Phase 1 完成 | Day 2 | ML Data Generator 可用，數據集生成成功 |
| M2: Phase 2 完成 | Day 5 | DQN 實現完成，小規模訓練成功 |
| M3: Phase 3 完成 | Day 7 | Training Pipeline 完整運行 |
| M4: Phase 4 完成 | Day 9 | 評估報告自動生成 |
| M5: 項目完成 | Day 10 | 端到端測試通過，文檔完整 |

---

## 🎯 成功標準檢查

### 必須達成

- [ ] ML Data Generator 正確轉換 Stage 6 JSON
- [ ] DQN 能成功訓練並收斂
- [ ] DQN 性能優於 RSRP baseline
- [ ] 12 種場景變體全部分析
- [ ] 100% SOURCE 標註覆蓋
- [ ] 測試覆蓋率 > 80%

### 應該達成

- [ ] TensorBoard 可視化完整
- [ ] 自動化評估報告生成
- [ ] 完整的使用文檔
- [ ] 性能基準測試

---

## 🚨 風險與應對

| 風險 | 應對措施 |
|------|---------|
| DQN 訓練不穩定 | 參考 Badini et al. 超參數，小步調試 |
| 數據格式問題 | 詳細的 schema 驗證和錯誤處理 |
| GPU 資源不足 | 優先使用小規模數據集驗證 |
| 時間不足 | 優先核心功能，Nice-to-have 功能延後 |

---

**文檔狀態**: ✅ 完成
**預計開始**: 待批准
**預計完成**: 開始後 7-10 天
