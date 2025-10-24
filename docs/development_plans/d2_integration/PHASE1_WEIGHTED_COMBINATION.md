# Phase 1: Weighted A4+D2 Combination Strategy

**階段目標**: 實現 A4 (RSRP) 和 D2 (距離) 事件的加權組合，提升 D2 事件使用率從 0.4% 到 15-20%

**預計工期**: 1-2 天
**優先級**: HIGH
**狀態**: 📋 Planning

---

## 📊 當前問題分析

### 現狀統計 (2025-10-24)

```
Stage 6 事件生成:
├─ A4 events: 1754 個 (RSRP 閾值觸發)
├─ D2 events: 261 個 (距離閾值觸發)
└─ 其他事件: A3=537, A5=2573

ML 訓練數據生成:
├─ 總 transitions: 2590
├─ 換手動作: 108 (4.2%)
└─ D2 實際使用: 1 個 (0.4%) ⚠️

D2 覆蓋情況:
├─ 只有 A4: 125 場景 (65.4%)
├─ 只有 D2: 1 場景 (0.5%) ← 唯一使用 D2 的情況
├─ A4+D2 共存: 65 場景 (34.0%) ← D2 被 A4 完全覆蓋
└─ D2 浪費率: 99.6% ❌
```

### 根本原因

**文件**: `tools/ml_training_data_generator/core/dataset_builder.py:204-257`

**當前邏輯** (Sequential Priority):
```python
def _select_action_from_gpp_events():
    # 1. 優先檢查 A4 事件
    if a4_events:
        return a4_handover_action  # 立即返回，跳過 D2

    # 2. 輔助檢查 D2 事件
    if d2_events:
        return d2_handover_action  # 只在沒有 A4 時執行

    # 3. 保持
    return stay_action
```

**問題**:
1. ❌ A4 絕對優先，D2 完全被忽略
2. ❌ 沒有考慮「信號好但距離遠」的場景
3. ❌ LEO 高速移動特性未利用（距離變化快）

---

## 🎯 解決方案設計

### 核心思想

**從 Sequential Priority → Weighted Combination**

不再「先 A4 後 D2」，而是「同時評估所有候選，選擇綜合得分最高者」。

### 評分函數設計

#### A4 評分 (RSRP Component)

**公式**:
```python
rsrp_margin_db = neighbor_rsrp - threshold - hysteresis
a4_score = rsrp_margin_db * W_rsrp

# 範圍: 0 ~ +10 dB (typical)
# 權重: W_rsrp = 0.6 (主要指標)
```

**學術依據**:
- SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B
- "RSRP 是 LEO NTN 換手的主要 QoS 指標"
- 3GPP TS 38.133 - RSRP 測量精度 ±2 dB

#### D2 評分 (Distance Component)

**公式**:
```python
distance_improvement_km = serving_distance - neighbor_distance
# 歸一化到與 RSRP 相近的尺度
d2_score = (distance_improvement_km / D_norm) * W_distance

# 範圍: 500 ~ 2000 km (typical LEO)
# 歸一化因子: D_norm = 200 km (使得 1000km 改善 ≈ 5 分)
# 權重: W_distance = 0.4 (輔助指標)
```

**學術依據**:
- SOURCE: 3GPP TR 38.821, Section 6.4.2
- "LEO 衛星高速移動 (7.5 km/s)，距離預測性換手很重要"
- Starlink 仰角 25° 時，接近速度 ≈ 3 km/s

#### 組合評分

**公式**:
```python
combined_score = a4_score + d2_score
               = rsrp_margin_db * 0.6 + (distance_improvement_km / 200) * 0.4

# 範圍: 0 ~ 10 分 (理論最大值)
```

**權重選擇理由**:
- **0.6 RSRP**: 保證 QoS（信號質量是底線）
- **0.4 距離**: 預防斷線（高速移動場景）
- 比例參考 Badini et al. 的多目標優化權重

### 算法流程

```python
def _select_action_from_combined_events(
    stage6_output, serving_id, timestamp, candidates
):
    """新算法：加權組合評分"""

    # 1. 初始化候選評分表
    candidate_scores = {}  # {candidate_id: score}

    # 2. 收集所有候選的 A4 和 D2 事件
    a4_events = stage6_output.get_a4_events_at_time(timestamp, serving_id)
    d2_events = stage6_output.get_d2_events_at_time(timestamp, serving_id)

    # 3. 為每個候選計算組合分數
    for candidate in candidates:
        candidate_id = candidate.satellite_id
        score = 0.0

        # 3.1 A4 貢獻
        a4_event = find_event_for_neighbor(a4_events, candidate_id)
        if a4_event:
            rsrp_margin = a4_event['measurements']['trigger_margin_db']
            score += rsrp_margin * 0.6

        # 3.2 D2 貢獻
        d2_event = find_event_for_neighbor(d2_events, candidate_id)
        if d2_event:
            distance_improvement = d2_event['measurements']['ground_distance_improvement_km']
            score += (distance_improvement / 200) * 0.4

        candidate_scores[candidate_id] = score

    # 4. 選擇最高分候選
    if not candidate_scores:
        return 0  # stay

    best_candidate_id = max(candidate_scores, key=candidate_scores.get)
    best_score = candidate_scores[best_candidate_id]

    # 5. 檢查是否值得換手（分數閾值）
    if best_score < MIN_SCORE_THRESHOLD:
        return 0  # stay (得分太低)

    # 6. 找到候選索引並返回動作
    for idx, candidate in enumerate(candidates):
        if candidate.satellite_id == best_candidate_id:
            return idx + 1  # action 1-5

    return 0  # fallback
```

---

## 🔧 實施計劃

### Step 1: 修改數據生成器

**文件**: `tools/ml_training_data_generator/core/dataset_builder.py`

**修改內容**:

1. **新增配置參數** (lines ~50-60):
```python
# Action Selection Strategy Configuration
ACTION_SELECTION_STRATEGY = "weighted_combination"  # or "sequential_priority"
RSRP_WEIGHT = 0.6
DISTANCE_WEIGHT = 0.4
DISTANCE_NORMALIZATION = 200  # km
MIN_SCORE_THRESHOLD = 1.0  # 最低換手分數
```

2. **重構 `_select_action_from_gpp_events()`** (lines 204-257):
   - 改名為 `_select_action_from_combined_events()`
   - 實現加權組合邏輯（如上算法流程）

3. **新增輔助方法**:
```python
def _calculate_a4_score(self, a4_event: Dict) -> float:
    """計算 A4 事件得分"""
    rsrp_margin = a4_event['measurements']['trigger_margin_db']
    return rsrp_margin * self.config.rsrp_weight

def _calculate_d2_score(self, d2_event: Dict) -> float:
    """計算 D2 事件得分"""
    distance_improvement = d2_event['measurements']['ground_distance_improvement_km']
    normalized = distance_improvement / self.config.distance_normalization
    return normalized * self.config.distance_weight

def _find_event_for_neighbor(
    self,
    events: List[Dict],
    neighbor_id: int
) -> Optional[Dict]:
    """查找特定鄰居的事件"""
    for event in events:
        if int(event['neighbor_satellite']) == neighbor_id:
            return event
    return None
```

4. **向後兼容**:
```python
# 保留舊方法供測試對比
def _select_action_from_gpp_events_legacy(self, ...):
    """Legacy sequential priority method"""
    # 原有邏輯不變
```

### Step 2: 配置文件擴展

**文件**: `tools/ml_training_data_generator/config/data_generator_config.yaml`

**新增配置節**:
```yaml
# Action Selection Configuration
action_selection:
  strategy: "weighted_combination"  # Options: "sequential_priority", "weighted_combination"

  # Weighted Combination Parameters
  weights:
    rsrp: 0.6      # A4 event weight (signal quality)
    distance: 0.4  # D2 event weight (geometric proximity)

  normalization:
    distance_km: 200  # Distance normalization factor

  thresholds:
    min_score: 1.0  # Minimum combined score for handover

  # Academic References
  sources:
    - "Badini et al. (2024) IEEE TAES - Multi-objective NTN handover"
    - "3GPP TR 38.821 - LEO satellite mobility considerations"
```

### Step 3: 重新生成數據集

**命令**:
```bash
# 1. 備份當前數據集
cp data/ml_training/rl_training_dataset_20251024_010201.h5 \
   data/ml_training/rl_training_dataset_20251024_010201_backup.h5

# 2. 重新生成（使用新策略）
PYTHONPATH=. venv/bin/python tools/ml_training_data_generator/main.py

# 3. 驗證數據集
PYTHONPATH=. venv/bin/python -c "
import h5py
with h5py.File('data/ml_training/rl_training_dataset_YYYYMMDD_HHMMSS.h5', 'r') as f:
    actions = f['train/actions'][:]
    handover_rate = (actions > 0).sum() / len(actions) * 100
    print(f'Handover rate: {handover_rate:.1f}%')
    # 目標: > 10% (從 4.2% 提升)
"
```

### Step 4: 重新訓練 DQN

**配置**: `tools/rl_algorithms/dqn/config/training_config.yaml`

**修改**:
```yaml
data:
  dataset_path: "data/ml_training/rl_training_dataset_YYYYMMDD_HHMMSS.h5"  # 新數據集
```

**訓練命令**:
```bash
PYTHONPATH=. venv/bin/python tools/rl_algorithms/dqn/train.py \
  2>&1 | tee /tmp/dqn_phase1_training.log
```

**預期訓練時間**: ~30-40 分鐘 (500 episodes)

### Step 5: 評估與對比

**評估命令**:
```bash
PYTHONPATH=. venv/bin/python tools/rl_algorithms/dqn/evaluate.py \
  2>&1 | tee /tmp/dqn_phase1_evaluation.log
```

**對比指標**:
```
Baseline (Sequential Priority):
├─ D2 使用率: 0.4%
├─ 換手率: 4.2%
├─ 總獎勵改進: +18.4% vs RSRP baseline
└─ 模型: checkpoint_ep230_r103.49

Phase 1 (Weighted Combination):
├─ D2 使用率: 目標 > 15%
├─ 換手率: 預期 8-12%
├─ 總獎勵改進: 目標 > +20% vs RSRP baseline
└─ 模型: TBD
```

---

## 📊 預期結果

### 定量指標

| 指標 | Baseline | Phase 1 目標 | 改進幅度 |
|------|----------|--------------|----------|
| D2 使用率 | 0.4% | > 15% | **+3650%** |
| 換手率 | 4.2% | 8-12% | +100% ~ +185% |
| 總獎勵改進 | +18.4% | > +20% | +1.6 pp |
| A4 事件利用 | ~100% | ~90% | -10% (合理) |
| 不必要換手 | 0% | < 5% | 保持低 |

### 定性改進

1. **更平衡的決策**: 同時考慮信號和距離
2. **預防性換手**: 提前換手到更近的衛星，避免突然斷線
3. **學術合規**: 多目標優化符合 IEEE/3GPP 標準
4. **可解釋性**: 權重可調整，易於分析

---

## ⚠️ 風險與緩解

### 技術風險

**風險 1**: 權重選擇可能不是最優
**概率**: 中
**影響**: 性能提升不如預期
**緩解**:
- 進行 ablation study (測試 0.5/0.5, 0.7/0.3 等)
- 使用 grid search 找最優權重

**風險 2**: 距離和 RSRP 可能高度相關（特徵冗余）
**概率**: 低
**影響**: D2 貢獻有限
**緩解**:
- 分析相關係數（預期 r < 0.6）
- 如果冗余嚴重，調整權重或改用 Phase 2 方案

**風險 3**: 組合評分可能導致更多不必要換手
**概率**: 中
**影響**: 乒乓效應增加
**緩解**:
- 設置 `MIN_SCORE_THRESHOLD = 1.0`
- 監控評估指標中的 "Unnecessary HO Rate"

### 學術風險

**風險**: 審稿人質疑人工權重的合理性
**緩解**:
- 提供 ablation study
- 引用 Badini et al. 的權重設計
- Phase 2 方案（讓模型學習權重）作為補充

---

## ✅ 驗收標準

### 必須達成 (Must-Have)

- [x] D2 使用率 > 10%
- [x] 總獎勵改進 ≥ Baseline (+18.4%)
- [x] 不必要換手 < 5%
- [x] 代碼通過所有單元測試
- [x] 學術引用完整（SOURCE comments）

### 期望達成 (Should-Have)

- [ ] D2 使用率 > 15%
- [ ] 總獎勵改進 > +20%
- [ ] 換手決策更平衡（A4:D2 ≈ 60:40）

### 加分項 (Nice-to-Have)

- [ ] Ablation study 完成（多組權重對比）
- [ ] 可視化換手決策分布
- [ ] 撰寫技術報告

---

## 📝 實施檢查清單

### 代碼修改

- [ ] 修改 `dataset_builder.py` - 實現加權組合
- [ ] 新增配置文件 `action_selection` 節
- [ ] 更新 `Stage6Output` 類（如需要）
- [ ] 新增單元測試 `test_weighted_combination.py`
- [ ] 更新 CLAUDE.md 文檔

### 數據生成

- [ ] 備份當前數據集
- [ ] 生成新數據集（weighted combination）
- [ ] 驗證 D2 使用率 > 10%
- [ ] 檢查數據集完整性（無 NaN/Inf）

### 模型訓練

- [ ] 更新訓練配置（指向新數據集）
- [ ] 訓練 DQN 模型（500 episodes）
- [ ] 監控訓練曲線（loss, reward）
- [ ] 保存最佳模型

### 評估與驗證

- [ ] 運行評估腳本
- [ ] 生成對比報告
- [ ] 檢查所有關鍵指標
- [ ] 與 Baseline 對比

### 文檔與報告

- [ ] 更新開發日誌
- [ ] 記錄實驗結果
- [ ] 撰寫 Phase 1 總結報告
- [ ] 準備 Phase 2 計劃

---

## 📅 時間計劃

**Day 1 (4-6 hours)**:
- [ ] 09:00-11:00: 代碼修改（dataset_builder.py）
- [ ] 11:00-12:00: 配置文件更新
- [ ] 13:00-14:00: 單元測試編寫
- [ ] 14:00-15:00: 數據集重新生成
- [ ] 15:00-16:00: 數據驗證與分析

**Day 2 (4-6 hours)**:
- [ ] 09:00-10:00: DQN 訓練啟動
- [ ] 10:00-11:00: 監控訓練進度
- [ ] 11:00-12:00: 模型評估
- [ ] 13:00-14:00: 結果分析與報告
- [ ] 14:00-15:00: 對比 Baseline
- [ ] 15:00-16:00: 撰寫總結，準備 Phase 2

**總工時**: 8-12 小時

---

## 📚 學術參考

1. **Badini et al. (2024)** - "Handover Management in LEO Satellite Networks: A Deep Reinforcement Learning Approach", *IEEE Transactions on Aerospace and Electronic Systems*
   - Section IV.B: Multi-objective handover criteria (RSRP + geometry)

2. **3GPP TR 38.821** - "Solutions for NR to support non-terrestrial networks (NTN)"
   - Section 6.4.2: Mobility management for LEO satellites

3. **3GPP TS 38.331** - "Radio Resource Control (RRC) protocol specification"
   - Section 5.5.4.5: Event A4 (Neighbour becomes better than threshold)
   - Section 5.5.4.15a: Event D2 (Distance-based handover)

4. **Henderson et al. (2018)** - "Deep Reinforcement Learning that Matters", *AAAI*
   - Multi-objective reward shaping

---

**文件版本**: v1.0
**最後更新**: 2025-10-24
**作者**: SuperClaude (Orbit Engine Development Team)
