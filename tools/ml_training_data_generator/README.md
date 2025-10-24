# ML Training Data Generator

將 Stage 6 JSON 輸出轉換為 RL 訓練數據集（HDF5 格式）

**SOURCE**: Proposal 003, Phase 1 - ML Data Generator

---

## 📋 概述

ML Training Data Generator 是一個**獨立工具**，從 Orbit Engine Stage 6 輸出中提取 RL 訓練數據。

### 關鍵設計

✅ **獨立工具** - 不修改 Stage 6 輸出，Stage 6 JSON 仍用於前端渲染
✅ **讀取 JSON** - 解析 Stage 6 標準格式
✅ **生成 HDF5** - 輸出 (state, action, reward, next_state, done) 訓練數據集
✅ **場景多樣性** - 支持 12 種場景變體（Proposal 002）

---

## 🚀 快速開始

### 基本用法

```bash
# 使用默認配置
python tools/ml_training_data_generator/generate_dataset.py

# 使用自定義配置
python tools/ml_training_data_generator/generate_dataset.py --config my_config.yaml

# 指定輸入/輸出路徑
python tools/ml_training_data_generator/generate_dataset.py \
    --input-dir data/outputs/stage6 \
    --output-path data/ml_training/my_dataset.h5
```

### 輸入要求

- **Stage 6 JSON 文件**: `data/outputs/stage6/stage6_research*.json`
- **必需字段**: `signal_analysis`, `constellation`, `analysis_start_time`
- **可選字段**: `scenario_variants`, `gpp_events`（來自 Proposal 002）

### 輸出格式

HDF5 文件結構:
```
rl_training_dataset.h5
├─ train/
│  ├─ states (N, 53)         # RL 狀態
│  ├─ actions (N,)           # 動作 (0=stay, 1-5=handover)
│  ├─ rewards (N,)           # 獎勵值
│  ├─ next_states (N, 53)    # 下一狀態
│  └─ dones (N,)             # Episode 結束標記
├─ val/ (same structure)
└─ test/ (same structure)
```

---

## 📦 模組設計

### 核心組件

#### 1. JSON Parser (`core/json_parser.py`)
- 解析 Stage 6 JSON 輸出
- Schema 驗證
- 批量處理

#### 2. State Extractor (`core/state_extractor.py`)
- 提取服務衛星（RSRP 最強）
- 提取候選衛星（RSRP 次強的 K 個）
- 提取 QoS 需求和網絡負載（從 scenario_variants）
- 提取時間特徵

#### 3. Reward Calculator (`core/reward_calculator.py`)
- 計算獎勵函數：
  ```
  reward = 0.5 * qos_satisfaction +
           0.3 * signal_quality -
           0.2 * handover_cost
  ```
- **SOURCE**: Badini et al. (2024) IEEE TAES, Equation (5)

#### 4. Dataset Builder (`core/dataset_builder.py`)
- 生成 transitions: (s, a, r, s', done)
- 數據集分割: train (70%) / val (15%) / test (15%)
- HDF5 保存（gzip 壓縮）
- 數據集驗證

---

## ⚙️ 配置說明

配置文件: `config/data_generator_config.yaml`

### 路徑配置

```yaml
paths:
  stage6_input_dir: "data/outputs/stage6"
  stage6_pattern: "stage6_research*.json"
  output_dir: "data/ml_training"
  output_filename: "rl_training_dataset.h5"
```

### 狀態提取配置

```yaml
state_extraction:
  max_candidates: 5  # 最大候選衛星數量
```

### 獎勵函數配置

```yaml
reward_function:
  # 權重（總和必須為 1.0）
  weight_qos: 0.5           # QoS 滿足度權重
  weight_signal: 0.3        # 信號品質權重
  weight_handover: 0.2      # 換手成本權重

  # QoS RSRP 門檻 (dBm)
  qos_rsrp_thresholds:
    voip: -95.0         # VoIP 需要高信號品質
    video: -100.0       # Video 需要中等信號品質
    iot: -110.0         # IoT 可以容忍低信號品質
    best_effort: -105.0 # Best effort 中等門檻

  # 換手參數
  handover_base_cost: 0.2       # 基礎換手成本
  unnecessary_penalty: 0.3      # 不必要換手額外懲罰
  hysteresis_db: 3.0            # 遲滯門檻（防止乒乓）
```

### 數據集分割配置

```yaml
dataset_split:
  train_ratio: 0.7      # 70% 訓練集
  val_ratio: 0.15       # 15% 驗證集
  test_ratio: 0.15      # 15% 測試集
  random_seed: 42       # 可重現性
```

---

## 📊 狀態空間定義

RL 狀態向量（53 維）:

| 組件 | 維度 | 說明 |
|------|------|------|
| Serving Satellite | 7 | RSRP, RSRQ, SNR, 距離, 仰角, 方位角, 負載 |
| Candidate Satellites | 35 | 5 個候選 × 7 特徵（不足則 padding） |
| QoS Requirements | 4 | Traffic type, 吞吐量, 延遲, 丟包率 |
| Network Load | 3 | Load pattern, 平均負載, 最大負載 |
| Time Features | 4 | Hour (sin/cos), Day of week (sin/cos) |
| **總計** | **53** | |

**SOURCE**: Badini et al. (2024) IEEE TAES, Section III.B

---

## 🎯 動作空間定義

動作空間: Discrete(6)

| 動作 | 說明 |
|------|------|
| 0 | 保持當前服務衛星 |
| 1 | 切換到候選衛星 1 |
| 2 | 切換到候選衛星 2 |
| 3 | 切換到候選衛星 3 |
| 4 | 切換到候選衛星 4 |
| 5 | 切換到候選衛星 5 |

---

## 🧪 測試

### 單元測試

```bash
# 運行所有測試
pytest tools/ml_training_data_generator/tests/

# 運行特定測試
pytest tools/ml_training_data_generator/tests/test_json_parser.py
pytest tools/ml_training_data_generator/tests/test_state_extractor.py
pytest tools/ml_training_data_generator/tests/test_reward_calculator.py
pytest tools/ml_training_data_generator/tests/test_dataset_builder.py
```

### 組件單獨測試

```bash
# 測試 JSON Parser
python -m tools.ml_training_data_generator.core.json_parser

# 測試 State Extractor
python -m tools.ml_training_data_generator.core.state_extractor

# 測試 Reward Calculator
python -m tools.ml_training_data_generator.core.reward_calculator

# 測試 Dataset Builder
python -m tools.ml_training_data_generator.core.dataset_builder
```

---

## 📚 學術引用

所有實現都基於學術文獻，並在代碼中標註 SOURCE:

### 核心文獻

1. **Badini et al. (2024)** - "Reinforcement Learning-based Handover for LEO Satellite Networks", IEEE TAES
   - 獎勵函數設計
   - 狀態空間定義
   - 候選衛星選擇

2. **3GPP TS 38.331 v18.5.1** - RRC Protocol
   - A3 事件定義
   - 遲滯機制
   - 換手決策

3. **3GPP TS 38.215 v18.1.0** - Physical Layer Measurements
   - RSRP/RSRQ/SNR 定義
   - 測量範圍

4. **3GPP TS 22.261 v19.5.0** - Service Requirements
   - QoS 參數定義
   - Traffic type 分類

5. **Sutton & Barto (2018)** - "Reinforcement Learning: An Introduction"
   - Transition 定義
   - MDP 框架

---

## 🔍 資料驗證

工具會自動執行以下驗證:

### JSON Schema 驗證
- ✅ 必需字段存在 (`signal_analysis`, `constellation`, etc.)
- ✅ 時間序列結構正確
- ✅ 信號品質字段完整 (`rsrp_dbm`, `rsrq_db`, `snr_db`)

### 數據集品質驗證
- ✅ 所有 splits (train/val/test) 存在
- ✅ Dataset shapes 一致
- ✅ 狀態維度正確（53 維）
- ✅ 動作範圍合法（0-5）
- ✅ 場景變體均衡分佈

---

## ❓ FAQ

### Q1: 這個工具會修改 Stage 6 輸出嗎？

**A**: 不會。ML Data Generator 是**獨立工具**，只讀取 Stage 6 JSON 文件，不修改原始輸出。Stage 6 輸出仍然用於前端渲染。

### Q2: 為什麼需要場景多樣性？

**A**: 來自 Proposal 002 的 12 種場景變體（4 traffic types × 3 load patterns）確保訓練數據涵蓋不同的網絡條件，提高 RL 算法的泛化能力。

### Q3: 如何選擇服務衛星和候選衛星？

**A**:
- **服務衛星**: 選擇當前時間點 RSRP 最強的衛星
- **候選衛星**: 選擇 RSRP 次強的 K 個衛星（默認 K=5）
- **SOURCE**: 3GPP TS 38.331 - 基於 RSRP 的 cell selection

### Q4: 獎勵函數是如何設計的？

**A**: 獎勵函數組合三個因素:
- **QoS 滿足度** (50%): 是否滿足 traffic type 的 QoS 要求
- **信號品質** (30%): RSRP 和 SNR 的歸一化分數
- **換手成本** (20%): 避免頻繁和不必要的換手

**SOURCE**: Badini et al. (2024) IEEE TAES, Equation (5)

### Q5: 數據集分割策略？

**A**:
- Train: 70%, Val: 15%, Test: 15%
- 按場景變體分層分割，確保每種場景在各個集合中均衡分佈
- 使用固定 random seed (42) 保證可重現性

### Q6: HDF5 文件太大怎麼辦？

**A**:
- 工具使用 gzip 壓縮（compression level 4）
- 典型壓縮率：原始大小的 20-30%
- 可在配置中調整 `compression_opts` (1-9)

---

## 📞 聯繫與支持

- **項目**: Orbit Engine
- **Proposal**: 003 - RL Training Pipeline & Evaluation Framework
- **Phase**: 1 - ML Data Generator
- **文檔**: `docs/development/proposals/003-rl-training-pipeline-evaluation/`

---

**版本**: 1.0.0
**最後更新**: 2025-10-23
**狀態**: ✅ Phase 1 實現完成
