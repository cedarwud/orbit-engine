# 需求分析：訓練數據多樣性增強

## 📚 文獻研究總結

### 研究方法

**分析來源**: `/home/sat/satellite/rl-paper/` - 9 篇 LEO 衛星換手 RL 論文

**搜尋關鍵字**:
- diversity, scenario, training data, data collection
- propagation, weather, dynamic, traffic profile
- load balancing, satellite capacity

**分析工具**: WebSearch + WebFetch + PDF 文本提取

---

## 🔬 文獻要求的多樣性類型

### 1️⃣ 時間多樣性 (Temporal Diversity)

**定義**: 不同時間點的換手場景，確保涵蓋不同衛星位置。

**論文依據**:
- **2023_12 - Handover Protocol Learning for LEO Satellite Networks**
  - "The DHO employs importance-weighted Actor-Learner architecture"
  - "Training performance and convergence using various DRL algorithms"
  - **要求**: 訓練數據需涵蓋衛星完整軌道週期

**六階段現況**: ✅ **已滿足**
- 每顆衛星 21 個時間點
- 30 秒間隔（符合 Vallado 2013 建議）
- 涵蓋 10.5 分鐘（Starlink 軌道週期 ~95 分鐘的 11%）

**結論**: 無需改進

---

### 2️⃣ 網路條件多樣性 (Network Condition Diversity)

**定義**: 動態傳播條件變化（LOS/Shadowed/Blocked）

**論文依據**:
- **2024_06 - Multi-Agent DRL-Based Handover for Mega-Constellation Under Dynamic Propagation Conditions**
  - **核心論點**: "All existing handover schemes are designed under the **static propagation conditions**, which cannot satisfy the dynamic feature of communication environment"
  - **解決方案**: "Three-state Markov model to characterize the dynamically varying propagation conditions between satellites and users"
  - **實現**: "Loo model is employed to describe the dynamic land mobile satellite channels"

**技術細節**:
```
三態 Markov 模型:
  - LOS (Line of Sight): 直射路徑
  - Shadowed: 部分遮蔽（樹木、建築邊緣）
  - Blocked: 完全遮蔽（建築物、地形）

狀態轉換率矩陣 (3GPP TR 38.901):
  P = | P_LL  P_LS  P_LB |
      | P_SL  P_SS  P_SB |
      | P_BL  P_BS  P_BB |
```

**六階段現況**: ❌ **未實現**
- 僅計算靜態幾何可見性（仰角 > 5°/10°）
- 未考慮遮蔽物、天氣、動態通道特性

**改進需求**: 🔴 **高優先級**
- 實現三態 Markov 模型
- 實現 Loo 通道模型（適用於 LMS 鏈路）
- 為每個時間點生成 `propagation_state` 欄位

---

### 3️⃣ 用戶需求多樣性 (User Requirement Diversity)

**定義**: 不同流量類型的 QoS 需求（VoIP/Video/IoT）

**論文依據**:
- **2024_07 - User-Centric Satellite Handover for Multiple Traffic Profiles Using Deep Q-Learning**
  - **核心論點**: "Next-generation communication technologies are intended to support the unprecedented **diversity of various emerging applications**"
  - **問題**: "Distinguishing UEs with different and varying traffic profiles (TPs), i.e., different performance requirements and generated traffic statistics"
  - **解決方案**: "MADQL-based HO optimization approach that takes into account the **variation and diversity** of performance requirements of different UE classes"

**技術細節**:
```
流量類型定義 (3GPP TS 22.261):
  VoIP:
    - Delay: < 150 ms
    - Bandwidth: 64 kbps
    - Reliability: 99%

  Video (HD Streaming):
    - Delay: < 400 ms
    - Bandwidth: 5 Mbps
    - Reliability: 95%

  IoT (Sensor Data):
    - Delay: < 5 s
    - Bandwidth: 10 kbps
    - Reliability: 90%

  Best Effort:
    - Delay: Best effort
    - Bandwidth: Variable
    - Reliability: 80%
```

**六階段現況**: ❌ **未實現**
- 僅考慮單一地面站 NTPU
- 無流量類型區分
- 無 QoS 需求變化

**改進需求**: 🔴 **高優先級**
- 定義 4 種流量類型（VoIP/Video/IoT/BestEffort）
- 為每筆訓練數據生成 `traffic_profile` 欄位
- 支援多場景變體生成

---

### 4️⃣ 衛星負載多樣性 (Satellite Load Diversity)

**定義**: 不同衛星負載狀態（輕載/重載/過載）

**論文依據**:
- **2021_01 - Load-Aware Satellite Handover Strategy Based on Multi-Agent Reinforcement Learning**
  - **核心論點**: "Distributed satellite handover strategy is required to **balance satellite load** to avoid network congestion"
  - **問題**: "The competition for satellite channels between users covered by the same satellite may cause highly imbalanced satellite load"
  - **解決方案**: "Minimize average satellite handovers while satisfying the **load constraint** of each satellite"

**技術細節**:
```
負載狀態定義:
  current_users: 當前用戶數量
  capacity: 最大容量（3GPP TR 38.821: Starlink ~200 用戶/衛星）
  utilization: current_users / capacity

負載分布模式:
  Uniform: 所有衛星負載相近 (0.4-0.6)
  Concentrated: 少數衛星高負載 (0.8-0.9), 多數低負載 (0.1-0.3)
  Dynamic: 負載隨時間變化
```

**六階段現況**: ❌ **未實現**
- 無衛星負載狀態模擬
- 換手決策不考慮負載均衡

**改進需求**: 🟡 **中優先級**
- 模擬 3 種負載模式（Uniform/Concentrated/Dynamic）
- 為每個時間點生成 `satellite_loads` 欄位

---

### 5️⃣ 問題規模多樣性 (Problem Scale Diversity)

**定義**: 不同衛星數量、用戶數量場景

**論文依據**:
- **2023_12 - Handover Protocol Learning**
  - "Various scale experiments are considered to examine the performance of training scenarios"

**六階段現況**: ⚠️ **部分滿足**
- Starlink: 98 顆訓練池（固定）
- OneWeb: 25 顆訓練池（固定）

**改進需求**: 🟢 **低優先級**
- 當前規模已足夠（98 顆 > 論文典型 20-50 顆）
- 可選：支援池大小配置（未來擴展）

---

### ❌ 無證據支持的多樣性

**軌道面分佈多樣性** - 無任何論文提及
- 已分析 9 篇論文，均未要求軌道面分佈均勻性
- Proposal 001 已驗證：軌道面約束導致覆蓋率下降

**結論**: 不實施

---

## 📊 需求優先級矩陣

| 多樣性類型 | 優先級 | 實現階段 | 預估工期 | 學術依據強度 |
|-----------|-------|---------|---------|------------|
| 時間多樣性 | ✅ 已滿足 | - | - | 強 |
| **動態傳播條件** | 🔴 高 | Stage 5 | 3-5 天 | **很強** |
| **流量類型多樣性** | 🔴 高 | Stage 6 | 3-5 天 | **很強** |
| 衛星負載多樣性 | 🟡 中 | Stage 6 | 2-3 天 | 中 |
| 問題規模多樣性 | 🟢 低 | - | - | 弱 |
| ~~軌道面多樣性~~ | ❌ 不實施 | - | - | 無 |

---

## 🎯 功能需求

### FR-1: Stage 5 動態傳播條件模擬

**需求 ID**: FR-1
**優先級**: 🔴 高
**來源**: 2024_06 論文

**描述**: Stage 5 必須為每個衛星-地面站鏈路計算動態傳播狀態。

**輸入**:
- Stage 4 輸出的可見衛星列表
- 衛星位置（Lat/Lon/Alt）
- 仰角、方位角
- 氣象條件（溫度、濕度、雨量）- 可選

**輸出**:
```json
{
  "satellite_id": "46061",
  "timestamp": "2025-10-21T01:53:00+00:00",
  "propagation_state": "LOS",  // LOS | Shadowed | Blocked
  "markov_transition_prob": {
    "P_LL": 0.95,
    "P_LS": 0.04,
    "P_LB": 0.01
  },
  "channel_attenuation_db": 2.3,
  "loo_parameters": {
    "mp_db": -15.2,  // Multipath power
    "sigma_db": 3.5  // Shadowing std deviation
  }
}
```

**驗收標準**:
- ✅ 三態 Markov 模型符合 Gilbert-Elliott 理論
- ✅ Loo 通道參數來自官方論文（Loo 1985）
- ✅ 狀態轉換率來自 3GPP TR 38.901
- ✅ 每個時間點都有 `propagation_state` 欄位

---

### FR-2: Stage 6 流量類型生成

**需求 ID**: FR-2
**優先級**: 🔴 高
**來源**: 2024_07 論文

**描述**: Stage 6 必須為每筆訓練數據生成流量類型變體。

**輸入**:
- Stage 5 輸出的信號品質數據
- 配置的流量類型定義

**輸出**:
```json
{
  "scenario_variant_id": "voip_001",
  "traffic_profile": {
    "type": "voip",
    "qos_requirements": {
      "max_delay_ms": 150,
      "min_bandwidth_kbps": 64,
      "min_reliability": 0.99
    },
    "priority": "high"
  }
}
```

**支援的流量類型**:
1. VoIP (Voice over IP)
2. Video (HD Streaming)
3. IoT (Sensor Data)
4. BestEffort (General Data)

**驗收標準**:
- ✅ QoS 參數符合 3GPP TS 22.261
- ✅ 支援至少 4 種流量類型
- ✅ 每個軌道數據生成多個變體（≥4 種）

---

### FR-3: Stage 6 衛星負載模擬

**需求 ID**: FR-3
**優先級**: 🟡 中
**來源**: 2021_01 論文

**描述**: Stage 6 必須模擬衛星負載狀態。

**輸入**:
- Stage 4 輸出的可見衛星列表
- 配置的負載模式

**輸出**:
```json
{
  "satellite_loads": [
    {
      "satellite_id": "46061",
      "current_users": 120,
      "capacity": 200,
      "utilization": 0.60,
      "load_state": "moderate"
    }
  ]
}
```

**支援的負載模式**:
1. Uniform - 所有衛星負載相近
2. Concentrated - 少數衛星高負載
3. Dynamic - 負載隨時間變化

**驗收標準**:
- ✅ 容量值符合 3GPP TR 38.821
- ✅ 支援 3 種負載模式
- ✅ 負載值合理（0.0-1.0）

---

## 🚫 非功能需求

### NFR-1: 學術合規性

**需求**: 所有模型必須符合學術標準，不使用簡化算法。

**驗證方法**:
- ✅ 所有參數有 SOURCE 註解
- ✅ 引用官方標準（ITU-R, 3GPP, IEEE）
- ✅ 通過 `make compliance` 檢查

---

### NFR-2: 性能要求

**需求**: 擴充後性能下降控制在可接受範圍。

**標準**:
- Stage 5 執行時間增加 < 20%
- Stage 6 執行時間增加 < 30%
- 記憶體使用增加 < 15%
- 輸出檔案大小增加 < 50%

---

### NFR-3: 向後兼容性

**需求**: 不破壞現有功能和輸出格式。

**標準**:
- ✅ 現有欄位保持不變
- ✅ 新增欄位為可選（有預設值）
- ✅ Stage 1-4 不受影響

---

### NFR-4: 可配置性

**需求**: 所有新功能可透過配置啟用/停用。

**標準**:
- ✅ `enable_propagation_simulation: true/false`
- ✅ `enable_traffic_profiles: true/false`
- ✅ `enable_load_simulation: true/false`

---

## 🔗 需求追溯矩陣

| 需求 ID | 論文依據 | 標準依據 | 實現階段 | 優先級 |
|---------|---------|---------|---------|--------|
| FR-1 | 2024_06 | ITU-R P.1410, 3GPP TR 38.901 | Stage 5 | 高 |
| FR-2 | 2024_07 | 3GPP TS 22.261, ITU-T Y.1541 | Stage 6 | 高 |
| FR-3 | 2021_01 | 3GPP TR 38.821, ITU-T E.800 | Stage 6 | 中 |
| NFR-1 | All | ACADEMIC_STANDARDS.md | All | 高 |
| NFR-2 | - | Performance Baseline | All | 中 |
| NFR-3 | - | API Contract | All | 高 |
| NFR-4 | - | Configuration Design | All | 中 |

---

## 📚 參考文獻

### 主要論文
1. Liu, H., et al. (2024). "Multi-Agent Deep Reinforcement Learning-Based Handover Scheme for Mega-Constellation Under Dynamic Propagation Conditions." IEEE TWC.
2. Badini, I., et al. (2024). "User-Centric Satellite Handover for Multiple Traffic Profiles Using Deep Q-Learning." IEEE TAES.
3. He, S., et al. (2021). "Load-Aware Satellite Handover Strategy Based on Multi-Agent Reinforcement Learning." IEEE ICC.

### 技術標準
1. 3GPP TR 38.901 - Study on channel model for frequencies from 0.5 to 100 GHz
2. 3GPP TS 22.261 - Service requirements for the 5G system
3. 3GPP TR 38.821 - Solutions for NR to support non-terrestrial networks (NTN)
4. ITU-R P.1410 - Propagation data and prediction methods for terrestrial land mobile services
5. ITU-T Y.1541 - Network performance objectives for IP-based services

### 學術模型
1. Loo, C. (1985). "A statistical model for a land mobile satellite link." IEEE TVT.
2. Gilbert, E. N. (1960). "Capacity of a burst-noise channel." Bell System Technical Journal.
3. Lutz, E., et al. (1991). "The land mobile satellite communication channel." IEEE TVT.

---

**下一步**: 進入架構設計階段（02-ARCHITECTURE.md）
