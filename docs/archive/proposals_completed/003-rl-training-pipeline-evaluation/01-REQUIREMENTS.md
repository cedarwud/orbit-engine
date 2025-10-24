# Proposal 003: 需求分析 (Requirements)

**文檔版本**: v2.0
**最後更新**: 2025-10-23

---

## 📋 需求總覽

本文檔明確定義 Proposal 003 的功能需求、非功能需求、約束條件和範圍邊界。

---

## 🎯 功能需求

### FR1: ML Training Data Generator

**需求描述**: 獨立工具，將 Stage 6 JSON 輸出轉換為 RL 訓練數據格式

#### FR1.1: 數據讀取

**需求**:
- 讀取 Stage 6 JSON 輸出文件
- 支持單文件和批量處理
- 解析場景變體數據（Proposal 002 生成的 12 種變體）

**輸入**:
```bash
data/outputs/stage6/stage6_research_optimization_20251023_*.json
```

**驗收標準**:
- ✅ 能正確解析 Stage 6 JSON 結構
- ✅ 能提取所有場景變體
- ✅ 錯誤處理：JSON 格式錯誤時給出明確錯誤信息

#### FR1.2: 狀態空間提取

**需求**: 從 Stage 6 輸出提取 RL 狀態表示

**狀態組成**:
```python
State = {
    # 服務衛星
    'serving_satellite': {
        'rsrp_dbm': float,      # 來自 Stage 5
        'rsrq_db': float,
        'sinr_db': float,
        'propagation_state': str,  # Proposal 002
        'distance_km': float,
        'elevation_deg': float,
        'velocity_m_s': float
    },

    # 候選衛星（最多 K 個）
    'candidate_satellites': List[SatelliteState],

    # QoS 需求（來自場景變體）
    'qos_requirements': {
        'max_delay_ms': float,
        'min_bandwidth_kbps': float,
        'min_reliability': float,
        'traffic_type': str  # voip/video/iot/best_effort
    },

    # 網絡負載（來自場景變體）
    'network_load': {
        'serving_utilization': float,
        'load_pattern': str  # uniform/concentrated/dynamic
    }
}
```

**驗收標準**:
- ✅ 所有字段從 Stage 6 JSON 正確提取
- ✅ 數據類型正確
- ✅ 缺失值處理：必要字段缺失時報錯

#### FR1.3: 動作空間定義

**需求**: 定義離散動作空間

**動作定義**:
```python
Action = int  # 0 ~ N

# 0: Stay with current serving satellite
# 1~N: Handover to candidate satellite i
```

**驗收標準**:
- ✅ 動作範圍明確定義
- ✅ 候選衛星數量動態適應

#### FR1.4: 獎勵函數計算

**需求**: 計算每個 (state, action) 的獎勵值

**獎勵函數**（基於 Badini et al. 2024）:
```python
reward = w_qos * qos_satisfaction +
         w_signal * signal_quality +
         w_handover * handover_cost

where:
  w_qos = 0.5
  w_signal = 0.3
  w_handover = -0.2
```

**QoS 滿足度計算**:
```python
qos_satisfaction = {
    1.0 if meets_all_qos_requirements(),
    -1.0 otherwise
}

where:
  meets_qos: delay < max_delay AND
             bandwidth >= min_bandwidth AND
             reliability >= min_reliability
```

**學術依據**:
- SOURCE: Badini et al. (2024) IEEE TAES, Section III.C, Equation (5)

**驗收標準**:
- ✅ 獎勵值在合理範圍內（-2.0 ~ 2.0）
- ✅ QoS 違反時獎勵為負
- ✅ 不必要換手時有懲罰

#### FR1.5: 數據集生成

**需求**: 生成 HDF5 格式的訓練數據

**輸出格式**:
```
dataset.h5
├── train/
│   ├── states          # (N, state_dim)
│   ├── actions         # (N,)
│   ├── rewards         # (N,)
│   ├── next_states     # (N, state_dim)
│   ├── dones           # (N,)
│   └── metadata        # episode_id, scenario_variant_id, etc.
├── val/
│   └── ... (same structure)
└── test/
    └── ... (same structure)
```

**數據集分割**:
- Train: 70%
- Val: 15%
- Test: 15%

**驗收標準**:
- ✅ HDF5 文件格式正確
- ✅ 數據集分割比例正確
- ✅ 12 種場景變體均衡分佈

---

### FR2: DQN Baseline Implementation

**需求描述**: 實現完整的 DQN 算法

#### FR2.1: Gymnasium Environment

**需求**: 實現 `SatelliteHandoverEnv` 兼容 Gymnasium API

**必須實現的方法**:
```python
class SatelliteHandoverEnv(gym.Env):
    def reset(self, seed=None, options=None) -> Tuple[obs, info]:
        """重置環境，返回初始狀態"""

    def step(self, action) -> Tuple[obs, reward, terminated, truncated, info]:
        """執行動作，返回下一個狀態"""

    def render(self, mode='human'):
        """可視化（可選）"""
```

**驗收標準**:
- ✅ 符合 Gymnasium v0.29+ API
- ✅ `reset()` 返回 (obs, info) tuple
- ✅ `step()` 返回 5-tuple (obs, reward, terminated, truncated, info)
- ✅ 通過 Gymnasium API 檢查

#### FR2.2: Q-Network 架構

**需求**: 實現 Q-network 神經網絡

**網絡結構**（基於 Badini et al. 2024）:
```
Input Layer (state_dim)
    ↓
Dense(256) + ReLU
    ↓
Dense(256) + ReLU
    ↓
Output Layer (action_dim)
```

**學術依據**:
- SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B

**驗收標準**:
- ✅ 網絡結構與論文一致
- ✅ 支持 GPU 加速
- ✅ 可配置的隱藏層大小

#### FR2.3: DQN Agent

**需求**: 實現 DQN 核心算法

**核心組件**:
1. **Q-network** - 估計 Q 值
2. **Target network** - 穩定訓練目標
3. **Experience replay buffer** - 存儲經驗
4. **ε-greedy exploration** - 探索策略

**超參數**（基於 Badini et al. 2024）:
```python
HYPERPARAMETERS = {
    'learning_rate': 1e-4,
    'gamma': 0.99,
    'epsilon_start': 1.0,
    'epsilon_end': 0.01,
    'epsilon_decay': 0.995,
    'buffer_size': 100_000,
    'batch_size': 64,
    'target_update_freq': 1000
}
```

**學術依據**:
- SOURCE: Badini et al. (2024) IEEE TAES, Table II

**驗收標準**:
- ✅ DQN 算法正確實現
- ✅ Target network 定期更新
- ✅ Experience replay 正常運作
- ✅ ε-greedy 探索策略正確

#### FR2.4: Replay Buffer

**需求**: 實現經驗回放緩衝區

**功能**:
```python
class ReplayBuffer:
    def push(state, action, reward, next_state, done):
        """存儲經驗"""

    def sample(batch_size) -> List[Transition]:
        """隨機採樣 batch"""

    def __len__() -> int:
        """返回緩衝區大小"""
```

**驗收標準**:
- ✅ 固定大小緩衝區（FIFO）
- ✅ 均勻隨機採樣
- ✅ 記憶體效率

---

### FR3: Training Pipeline

**需求描述**: 端到端訓練工作流

#### FR3.1: 配置管理

**需求**: 使用 YAML 配置文件管理超參數

**配置文件結構**:
```yaml
experiment:
  name: "dqn_satellite_handover_v1"
  seed: 42
  device: "cuda"

dataset:
  path: "data/rl_training/dataset_v1.h5"
  train_split: 0.7
  val_split: 0.15
  test_split: 0.15

algorithm:
  type: "dqn"
  hyperparameters:
    learning_rate: 0.0001
    gamma: 0.99
    # ... 其他超參數

training:
  num_episodes: 500
  checkpoint_frequency: 50
  eval_frequency: 10
  early_stopping_patience: 50
```

**驗收標準**:
- ✅ 支持 YAML 配置載入
- ✅ 參數驗證（類型、範圍檢查）
- ✅ 配置版本控制

#### FR3.2: 訓練循環

**需求**: 實現主訓練循環

**功能**:
```python
for episode in range(num_episodes):
    state = env.reset()
    episode_reward = 0

    while not done:
        action = agent.select_action(state, epsilon)
        next_state, reward, done = env.step(action)
        agent.store_experience(...)

        if agent.ready_to_train():
            loss = agent.train_step()

        state = next_state
        episode_reward += reward

    # 定期評估
    if episode % eval_freq == 0:
        eval_metrics = evaluate(agent, val_env)

    # 保存檢查點
    if episode % checkpoint_freq == 0:
        save_checkpoint(agent, episode)
```

**驗收標準**:
- ✅ 訓練循環正常運行
- ✅ ε 衰減正確實施
- ✅ 定期評估和保存

#### FR3.3: 檢查點保存

**需求**: 保存和恢復訓練狀態

**保存內容**:
```python
checkpoint = {
    'episode': episode,
    'q_network_state_dict': agent.q_network.state_dict(),
    'target_network_state_dict': agent.target_network.state_dict(),
    'optimizer_state_dict': agent.optimizer.state_dict(),
    'epsilon': agent.epsilon,
    'replay_buffer': agent.replay_buffer,
    'config': config
}
```

**驗收標準**:
- ✅ 能完整恢復訓練狀態
- ✅ 檢查點文件命名清晰
- ✅ 自動清理舊檢查點（保留最近 5 個）

#### FR3.4: 日誌記錄

**需求**: 使用 TensorBoard 記錄訓練指標

**記錄指標**:
- Training loss
- Episode reward
- Epsilon value
- Q-value estimates
- Evaluation metrics (定期)

**驗收標準**:
- ✅ TensorBoard 可視化正常
- ✅ 所有關鍵指標已記錄
- ✅ 日誌文件結構清晰

---

### FR4: Evaluation Framework

**需求描述**: 標準化性能評估

#### FR4.1: 核心指標

**需求**: 計算標準化評估指標

**換手性能指標**:
```python
metrics = {
    'handover_success_rate': float,      # 換手成功率
    'unnecessary_handover_rate': float,  # 不必要換手率
    'avg_handover_latency_ms': float,    # 平均換手延遲
}
```

**QoS 指標**:
```python
qos_metrics = {
    'qos_satisfaction_rate': float,  # QoS 滿足率
    'avg_throughput_mbps': float,    # 平均吞吐量
    'avg_latency_ms': float,         # 平均延遲
}
```

**學術依據**:
- SOURCE: 3GPP TS 38.331 - Handover performance metrics
- SOURCE: 3GPP TS 22.261 - QoS requirements

**驗收標準**:
- ✅ 所有指標計算正確
- ✅ 與論文指標定義一致

#### FR4.2: 場景多樣性分析

**需求**: 分析各場景下的性能（基於 Proposal 002）

**分析維度**:
1. **各流量類型性能**:
   - VoIP
   - Video
   - IoT
   - Best Effort

2. **各負載模式性能**:
   - Uniform
   - Concentrated
   - Dynamic

**驗收標準**:
- ✅ 12 種場景變體全部分析
- ✅ 性能差異顯著性檢驗
- ✅ 可視化圖表生成

#### FR4.3: 基線對比

**需求**: 與傳統方法對比

**基線算法**:
1. **RSRP-based handover**:
   - 當候選衛星 RSRP > 服務衛星 + 3dB 時換手
   - SOURCE: 3GPP TS 38.331 A3 event

2. **Distance-based handover**:
   - 選擇距離最近的衛星

**驗收標準**:
- ✅ 基線算法正確實現
- ✅ DQN 性能優於基線
- ✅ 統計顯著性檢驗 (p < 0.05)

#### FR4.4: 報告生成

**需求**: 自動生成 Markdown 評估報告

**報告結構**:
```markdown
# Evaluation Report

## 整體性能

| Metric | DQN | RSRP-Base | Improvement |
|--------|-----|-----------|-------------|
| Success Rate | 92% | 87% | +5% |
| ...

## 場景分析

### 各流量類型
...

### 各負載模式
...

## 統計檢驗
...
```

**驗收標準**:
- ✅ 報告自動生成
- ✅ 包含所有關鍵指標
- ✅ 圖表嵌入報告

---

## 🚫 非功能需求

### NFR1: 性能

| 指標 | 要求 | 驗收 |
|------|------|------|
| 數據轉換速度 | > 1000 samples/s | 性能測試 |
| 訓練速度 | < 12 小時 (500 episodes) | 實際訓練 |
| 內存使用 | < 16 GB RAM | 監控工具 |
| GPU 利用率 | > 70% | nvidia-smi |

### NFR2: 可靠性

| 指標 | 要求 | 驗收 |
|------|------|------|
| 訓練中斷恢復 | 支持從檢查點恢復 | 測試 |
| 錯誤處理 | 所有異常有清晰錯誤信息 | 代碼審查 |
| 數據驗證 | 輸入數據完整性檢查 | 單元測試 |

### NFR3: 可維護性

| 指標 | 要求 | 驗收 |
|------|------|------|
| 代碼風格 | 遵循 PEP 8 | linter |
| 文檔覆蓋 | 所有公共 API 有 docstring | 代碼審查 |
| 測試覆蓋 | > 80% | pytest-cov |
| 學術標註 | 100% SOURCE 覆蓋 | 代碼審查 |

### NFR4: 可擴展性

| 指標 | 要求 | 驗收 |
|------|------|------|
| 新算法整合 | 清晰的 Agent 接口 | 設計審查 |
| 新指標添加 | 模塊化評估框架 | 設計審查 |
| 配置靈活性 | YAML 驅動配置 | 功能測試 |

---

## 🔒 約束條件

### C1: 技術約束

- **必須使用 Gymnasium** (不是 OpenAI Gym)
- **必須使用 PyTorch** (不是 TensorFlow)
- **Python 版本**: 3.8+
- **GPU**: NVIDIA with CUDA support

### C2: 學術約束

- **所有參數必須有 SOURCE 標註**
- **算法實現必須與論文一致**
- **不允許簡化或估計**
- **結果必須可重現（固定 seed）**

### C3: 兼容性約束

- **不修改 Stage 6 輸出格式**
- **前端渲染不受影響**
- **ML Data Generator 是獨立工具**

---

## 📏 範圍邊界

### ✅ 在範圍內 (In Scope)

- DQN baseline 實現
- ML Data Generator（獨立工具）
- Training Pipeline（基本版）
- Evaluation Framework（基本版）
- 與 RSRP baseline 對比
- 12 種場景變體分析

### ❌ 不在範圍內 (Out of Scope)

- ❌ 其他 RL 算法（A3C, PPO, SAC）- 未來工作
- ❌ 超參數自動調優 - 未來工作
- ❌ 分佈式訓練 - 未來工作
- ❌ 模型壓縮和部署 - 未來工作
- ❌ 在線學習 - 未來工作
- ❌ 多智能體 RL - 未來工作

### ⏸️ 未來可能擴展 (Future Considerations)

- 您的算法整合（等開發完成）
- 更多 baseline 算法（按需添加）
- Weights & Biases 整合
- 超參數搜索工具
- A/B testing framework

---

## ✅ 驗收標準總結

### 核心驗收標準

| 編號 | 標準 | 驗收方法 |
|------|------|---------|
| AC1 | ML Data Generator 正確轉換 Stage 6 JSON | 單元測試 + 手動驗證 |
| AC2 | DQN 能成功訓練並收斂 | 訓練曲線 + loss 下降 |
| AC3 | DQN 性能優於 RSRP baseline | 評估報告 + 統計檢驗 |
| AC4 | 12 種場景全部覆蓋 | 數據集統計 |
| AC5 | 100% SOURCE 標註 | 代碼審查 |
| AC6 | 測試覆蓋率 > 80% | pytest-cov report |

---

**文檔狀態**: ✅ 完成
**下一篇**: [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - 系統架構設計
