# Proposal 003: 總覽 (Overview)

**文檔版本**: v2.0
**最後更新**: 2025-10-23

---

## 📋 執行摘要

在 Proposal 002 成功實現訓練數據多樣性增強後，Proposal 003 將建立 **DQN baseline 訓練和評估體系**，為未來的算法開發提供標準化的對比基準。

### 核心目標

**建立可運行的 RL 訓練管道**，包括：
1. **數據轉換** - 將 Stage 6 JSON 轉為 RL 訓練格式
2. **DQN 實現** - 完整的 DQN baseline 算法
3. **訓練流程** - 端到端的訓練工作流
4. **評估框架** - 標準化的性能評估

---

## 🎯 問題陳述

### 當前狀態

**已完成** (Proposal 001-002):
- ✅ Stage 1-4: 軌道傳播和候選衛星選擇
- ✅ Stage 5: 動態傳播條件的信號分析
- ✅ Stage 6: 場景多樣性生成（12 種場景變體）
- ✅ 豐富的訓練數據（12x 場景擴增）

**缺失環節**:
- ❌ 沒有將 JSON 數據轉換為 RL 訓練格式的工具
- ❌ 沒有任何 RL 算法實現
- ❌ 沒有訓練管道
- ❌ 沒有標準化評估框架

### 核心問題

1. **數據格式不兼容**
   - Stage 6 輸出: JSON 格式（信號品質、物理參數、場景變體）
   - RL 需要: (state, action, reward, next_state) 元組

2. **無法訓練 RL 模型**
   - 沒有 baseline 算法實現
   - 無法驗證訓練數據的有效性

3. **無法評估性能**
   - 沒有標準化指標
   - 無法與傳統方法對比

---

## 💡 解決方案

### 總體策略

**分階段建立 DQN baseline 體系**:

```
Stage 6 JSON 輸出
      ↓
ML Data Generator (獨立工具)
      ↓
HDF5 訓練數據
      ↓
DQN Training Pipeline
      ↓
Trained Model
      ↓
Evaluation Framework
      ↓
Performance Report
```

### 關鍵設計決策

#### 決策 1: 只實現 DQN

**原因**:
- ✅ DQN 作為 baseline 已足夠（Badini et al. 2024 使用 DQN）
- ✅ 先驗證整個流程可行
- ✅ 為未來的算法對比建立基準
- ✅ 避免過度設計

**未來擴展**:
- ⏸️ 您的算法開發完成後再整合
- ⏸️ 需要時再添加其他 baseline（PPO, SAC 等）

#### 決策 2: 獨立工具設計

**ML Data Generator 是獨立後處理工具**:

```
✅ 正確設計:
Stage 6 → JSON 輸出 → 前端渲染 (不變)
             ↓
        ML Data Generator (獨立讀取)
             ↓
        RL 訓練數據
```

**原因**:
- ✅ 不修改 Stage 6 輸出
- ✅ 前端渲染不受影響
- ✅ 解耦設計，易於維護

#### 決策 3: 使用 Gymnasium

**使用 Gymnasium (不是舊的 OpenAI Gym)**:

| 框架 | 狀態 | 選擇 |
|------|------|------|
| OpenAI Gym | ❌ 停止維護 (2022) | 不使用 |
| Gymnasium | ✅ 活躍維護 | **使用** |

**原因**:
- ✅ 持續更新和維護
- ✅ 更好的 API 設計
- ✅ 社區生態活躍
- ✅ 與 Stable-Baselines3 兼容

---

## 🏗️ 四階段實施計畫

### Phase 1: ML Data Generator (2 天)

**目標**: 獨立工具，將 Stage 6 JSON 轉為 RL 訓練數據

**核心功能**:
- 讀取 Stage 6 JSON 輸出
- 提取 (state, action, reward, next_state) 元組
- 生成 HDF5 訓練數據
- 數據集分割（train/val/test）

**學術依據**:
- Badini et al. (2024) - State space 定義
- Sutton & Barto (2018) - RL 數據格式

---

### Phase 2: DQN Baseline (3-4 天)

**目標**: 完整的 DQN 算法實現

**核心組件**:
1. **Gymnasium Environment** - `SatelliteHandoverEnv`
2. **DQN Agent** - Q-network + target network + experience replay
3. **Neural Networks** - Q-network 架構
4. **Utils** - Replay buffer, epsilon-greedy 等

**學術依據**:
- Mnih et al. (2015) - DQN 原始論文
- Badini et al. (2024) - 衛星換手應用

---

### Phase 3: Training Pipeline (2 天)

**目標**: 端到端訓練工作流

**核心功能**:
- 配置管理（YAML）
- 訓練循環
- 檢查點保存/恢復
- TensorBoard 日誌
- 早停機制

---

### Phase 4: Evaluation Framework (2 天)

**目標**: 標準化性能評估

**核心指標**:
- 換手性能（成功率、延遲、不必要換手率）
- QoS 指標（滿足率、吞吐量）
- 場景多樣性分析（12 種場景變體）

**對比基線**:
- RSRP-based handover（傳統方法）
- Distance-based handover

---

## 📊 預期成果

### 代碼交付物

| 模組 | 文件數 | 代碼行數 | 測試 |
|------|-------|---------|------|
| ML Data Generator | 3 | ~1,000 | 20+ |
| DQN Implementation | 6 | ~2,000 | 25+ |
| Training Pipeline | 4 | ~1,200 | 15+ |
| Evaluation Framework | 5 | ~1,500 | 20+ |
| **總計** | **18** | **~5,700** | **80+** |

### 實驗結果

**預期性能**:

| Metric | DQN Baseline | RSRP-Baseline | 期望 |
|--------|--------------|---------------|------|
| Handover Success Rate | ~92% | ~87% | DQN > RSRP |
| QoS Satisfaction | ~94% | ~89% | DQN > RSRP |
| Avg Reward | ~8.4 | ~7.5 | DQN > RSRP |

**場景分析** (基於 Proposal 002):
- VoIP, Video, IoT, Best Effort 各場景性能
- Uniform, Concentrated, Dynamic 各負載模式性能
- 統計顯著性檢驗

---

## ⏱️ 時間線

```
Week 1 (Day 1-5):
├─ Day 1-2: Phase 1 - ML Data Generator
└─ Day 3-5: Phase 2 開始 - Environment + DQN

Week 2 (Day 6-10):
├─ Day 6-7: Phase 2 完成 - DQN 訓練測試
├─ Day 8-9: Phase 3 - Training Pipeline
└─ Day 10: Phase 4 - Evaluation Framework

總工期: 7-10 天
```

---

## 🎓 學術標準

### SOURCE 標註要求

所有實現必須標註學術來源：

```python
def compute_reward(...):
    """
    SOURCE: Badini et al. (2024) IEEE TAES, Equation (5)
    """
    ...
```

### 參考文獻

#### 核心論文

1. **Mnih, V., et al.** (2015). "Human-level control through deep reinforcement learning." *Nature*, 518(7540), 529-533.
   - DQN 原始論文

2. **Badini, I., et al.** (2024). "User-Centric Satellite Handover for Multiple Traffic Profiles Using Deep Q-Learning." *IEEE TAES*, 60(4), 4352-4367.
   - 衛星換手 DQN 應用

3. **Sutton, R. S., & Barto, A. G.** (2018). *Reinforcement learning: An introduction* (2nd ed.). MIT press.
   - RL 基礎理論

#### 標準文檔

4. **3GPP TS 38.331** v18.5.1 - RRC Protocol specification
   - 換手程序標準

5. **3GPP TS 22.261** v18.2.0 - 5G service requirements
   - QoS 要求

---

## 🔗 與其他 Proposal 的關聯

### 依賴 Proposal 002

```
Proposal 002 (已完成)
    ↓
  Stage 6 輸出
    ├─ 12 種場景變體
    ├─ 動態傳播條件
    └─ 豐富的信號數據
    ↓
Proposal 003 (本提案)
    ├─ 讀取 Stage 6 JSON
    ├─ 轉換為 RL 數據
    ├─ 訓練 DQN baseline
    └─ 評估性能
```

### 為未來鋪路

**Proposal 003 完成後可以**:
- ✅ 您的算法直接對比 DQN baseline
- ✅ 使用標準化評估框架
- ✅ 快速驗證新算法效果

---

## 🎯 成功標準

### 必須達成 (Must Have)

- ✅ ML Data Generator 正確轉換 Stage 6 JSON
- ✅ DQN 能成功訓練並收斂
- ✅ 訓練管道完整運行（數據→訓練→評估）
- ✅ DQN 性能優於 RSRP baseline
- ✅ 100% SOURCE 標註覆蓋

### 應該達成 (Should Have)

- ✅ 12 種場景變體的性能分析
- ✅ TensorBoard 可視化
- ✅ 自動化評估報告生成
- ✅ 完整的測試覆蓋（>80%）

### 希望達成 (Nice to Have)

- ⏸️ 超參數調優工具
- ⏸️ W&B 整合
- ⏸️ 模型壓縮和優化

---

## ⚠️ 風險與緩解

### 技術風險

| 風險 | 影響 | 概率 | 緩解措施 |
|------|------|------|---------|
| DQN 訓練不穩定 | 高 | 中 | 參考 Badini et al. 超參數 |
| 數據格式轉換錯誤 | 中 | 低 | 詳細單元測試 |
| 評估指標不準確 | 中 | 低 | 基於 3GPP 標準定義 |

### 資源風險

| 風險 | 影響 | 概率 | 緩解措施 |
|------|------|------|---------|
| GPU 資源不足 | 中 | 低 | 使用小規模數據驗證 |
| 開發時間不足 | 中 | 中 | 優先實現核心功能 |

---

## 📞 後續步驟

### 立即行動

1. **審批本提案** - 確認技術方案和時間線
2. **資源分配** - GPU、開發人員
3. **環境準備** - Gymnasium, PyTorch 等依賴安裝

### 開始實施

**Day 1**: 開始 Phase 1 - ML Data Generator 設計

---

**文檔狀態**: ✅ 完成
**下一篇**: [01-REQUIREMENTS.md](01-REQUIREMENTS.md) - 詳細需求分析
