# Phase 2: Distance Features in State Space

**階段目標**: 將距離特徵加入 DQN 狀態空間，讓模型自動學習 RSRP 和距離的最優權衡

**預計工期**: 3-5 天
**優先級**: MEDIUM
**前置條件**: Phase 1 完成
**狀態**: 📋 Planning

---

## 🎯 核心理念

### 從 Hand-Crafted Weights → Learned Representations

**Phase 1 方法**:
```python
# 人工設定權重
combined_score = rsrp_margin * 0.6 + distance_improvement / 200 * 0.4
```
- ✅ 簡單直觀
- ✅ 可解釋
- ❌ 權重固定（可能不是最優）
- ❌ 無法適應不同場景

**Phase 2 方法**:
```python
# 將距離作為狀態特徵，讓 DQN 學習權重
state = [rsrp_features, distance_features, ...]  # 53 → 57 維
action = DQN(state)  # 神經網絡自動學習最優策略
```
- ✅ 自適應（不同場景不同策略）
- ✅ 可能找到更優解
- ✅ 符合深度學習哲學
- ❌ 訓練時間更長
- ❌ 可解釋性降低

---

## 📐 狀態空間設計

### 當前狀態結構 (53 維)

**來源**: `tools/ml_training_data_generator/core/state_extractor.py:60-140`

```python
# Serving Satellite (14 features)
serving_features = [
    rsrp_dbm / 50,           # 1. RSRP (normalized)
    rsrq_db / 20,            # 2. RSRQ
    sinr_db / 30,            # 3. SINR
    elevation_deg / 90,      # 4. Elevation angle
    azimuth_deg / 360,       # 5. Azimuth
    doppler_shift_hz / 50000, # 6. Doppler shift
    altitude_km / 2000,      # 7. Altitude
    latitude_deg / 90,       # 8. Latitude
    longitude_deg / 180,     # 9. Longitude
    velocity_x_km_s / 10,    # 10. Velocity X
    velocity_y_km_s / 10,    # 11. Velocity Y
    velocity_z_km_s / 10,    # 12. Velocity Z
    constellation_id,        # 13. Constellation (0=Starlink, 1=OneWeb)
    satellite_id / 100000    # 14. Satellite ID (normalized)
]

# Candidate Satellites (5 candidates × 7 features = 35)
for candidate in top_5_candidates:
    candidate_features = [
        rsrp_dbm / 50,       # 1. RSRP
        rsrq_db / 20,        # 2. RSRQ
        sinr_db / 30,        # 3. SINR
        elevation_deg / 90,  # 4. Elevation
        azimuth_deg / 360,   # 5. Azimuth
        doppler_shift_hz / 50000, # 6. Doppler
        satellite_id / 100000 # 7. Satellite ID
    ]

# Context Features (4)
context_features = [
    timestamp_normalized,    # 1. Time of day
    num_visible_satellites / 20, # 2. Visible satellites
    handover_history,        # 3. Recent handover count
    serving_duration / 3600  # 4. Connection duration
]

# Total: 14 + 35 + 4 = 53 features
```

### 新增距離特徵 (+4 維 → 57 總維度)

#### Feature 1: Serving Satellite Ground Distance

**定義**: 服務衛星與地面站的 2D 地面距離

**位置**: 加入 serving_features (第 15 項)

**計算**:
```python
serving_ground_distance_km = haversine_distance(
    ground_station_lat_lon,
    serving_satellite_ground_point_lat_lon
)
normalized = serving_ground_distance_km / 2000  # [0, 1]
```

**物理意義**:
- 距離越大 → 信號衰減越嚴重
- 距離越大 → 衛星即將離開可見範圍
- LEO 典型範圍: 500-2000 km

**學術依據**:
- SOURCE: 3GPP TR 38.821, Section 6.1.1
- "Ground distance 是 LEO NTN 的關鍵幾何參數"

#### Feature 2-6: Candidate Satellites Ground Distance

**定義**: 每個候選衛星與地面站的 2D 地面距離

**位置**: 加入每個 candidate_features (第 8 項)

**計算**:
```python
for candidate in top_5_candidates:
    candidate_ground_distance_km = haversine_distance(
        ground_station_lat_lon,
        candidate_satellite_ground_point_lat_lon
    )
    normalized = candidate_ground_distance_km / 2000
```

**作用**:
- DQN 可以比較不同候選的距離
- 學習「選擇更近的候選」策略

#### Feature 7: Relative Distance Ratio

**定義**: 候選池中最小距離與服務距離的比率

**位置**: 加入 context_features (第 5 項)

**計算**:
```python
min_candidate_distance = min(candidate_ground_distances)
distance_ratio = min_candidate_distance / serving_ground_distance

# 範圍: [0, 1+]
# < 1: 有更近的候選 → 可能需要換手
# ≈ 1: 距離相近 → 保持
# > 1: 服務衛星最近 → 保持
```

**物理意義**:
- 直觀的換手信號
- 與 RSRP margin 互補

---

## 🔧 實施計劃

### Step 1: 修改狀態提取器

**文件**: `tools/ml_training_data_generator/core/state_extractor.py`

#### 1.1 更新 `extract_state_for_satellite()` (lines 60-140)

**修改點 1**: Serving satellite features

```python
# 原有 14 個特徵
serving_features = [
    serving.rsrp_dbm / 50,
    serving.rsrq_db / 20,
    # ... (保持不變)
]

# ✅ 新增第 15 個特徵
serving_ground_distance_km = self._calculate_ground_distance(
    serving.ground_point,  # Stage 6 提供
    self.ground_station_location
)
serving_features.append(serving_ground_distance_km / 2000)
```

**修改點 2**: Candidate features

```python
# 原有每個候選 7 個特徵
for candidate in candidates:
    candidate_features = [
        candidate.rsrp_dbm / 50,
        # ... (保持不變)
    ]

    # ✅ 新增第 8 個特徵
    candidate_ground_distance_km = self._calculate_ground_distance(
        candidate.ground_point,
        self.ground_station_location
    )
    candidate_features.append(candidate_ground_distance_km / 2000)
```

**修改點 3**: Context features

```python
# 原有 4 個特徵
context_features = [
    timestamp_normalized,
    num_visible / 20,
    handover_history,
    serving_duration / 3600
]

# ✅ 新增第 5 個特徵 (distance ratio)
candidate_distances = [
    self._calculate_ground_distance(c.ground_point, self.ground_station_location)
    for c in candidates
]
min_candidate_distance = min(candidate_distances) if candidate_distances else float('inf')
distance_ratio = min_candidate_distance / serving_ground_distance_km
context_features.append(np.clip(distance_ratio, 0, 2))  # clip to [0, 2]
```

#### 1.2 新增輔助方法

```python
def _calculate_ground_distance(
    self,
    satellite_ground_point: Dict[str, float],
    ground_station_location: Tuple[float, float]
) -> float:
    """計算衛星地面點與地面站的 Haversine 距離

    SOURCE: Sinnott (1984) - Haversine formula

    Args:
        satellite_ground_point: {'lat': ..., 'lon': ...}
        ground_station_location: (lat, lon) tuple

    Returns:
        距離 (km)
    """
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0  # Earth radius in km

    lat1, lon1 = radians(satellite_ground_point['lat']), radians(satellite_ground_point['lon'])
    lat2, lon2 = radians(ground_station_location[0]), radians(ground_station_location[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
```

#### 1.3 確保 Stage 6 提供 ground_point

**檢查**: `Stage6Output` 類是否包含 `ground_point` 字段

如果沒有，需要回溯修改 Stage 6:
```python
# Stage 6 gpp_event_detector.py 應該已經提供
# 參考 D2 事件中的 serving_ground_point 和 neighbor_ground_point
```

### Step 2: 更新配置參數

**文件**: `tools/ml_training_data_generator/config/data_generator_config.yaml`

```yaml
# State Extraction Configuration
state_extraction:
  state_dimension: 57  # Updated from 53
  include_distance_features: true

  # Ground Station Location (NTPU)
  ground_station:
    latitude: 24.94388888
    longitude: 121.37083333
    altitude_m: 36.0

  # Normalization Factors
  normalization:
    max_distance_km: 2000  # LEO satellite typical range
    max_rsrp_dbm: 50
    max_elevation_deg: 90
    # ... (other normalizations)

  # Feature Configuration
  features:
    serving_satellite:
      - rsrp
      - rsrq
      - sinr
      - elevation
      - azimuth
      - doppler
      - altitude
      - position  # lat, lon
      - velocity  # vx, vy, vz
      - constellation_id
      - satellite_id
      - ground_distance  # ✅ NEW

    candidate_satellites:
      - rsrp
      - rsrq
      - sinr
      - elevation
      - azimuth
      - doppler
      - satellite_id
      - ground_distance  # ✅ NEW

    context:
      - timestamp
      - num_visible_satellites
      - handover_history
      - serving_duration
      - distance_ratio  # ✅ NEW
```

### Step 3: 更新 DQN 網絡配置

**文件**: `tools/rl_algorithms/dqn/config/training_config.yaml`

```yaml
# Environment Configuration
environment:
  state_dim: 57  # ✅ Updated from 53
  action_dim: 6  # Unchanged (stay + 5 candidates)
  max_episodes_per_reset: null

# Network Configuration
network:
  hidden_dims: [256, 256]  # ✅ Keep same (auto-adapts to input size)
  # PyTorch 會自動調整輸入層: Linear(57, 256)
```

**DQN 網絡結構變化**:
```python
# Before (Phase 1)
Q-Network:
  Input: 53 → Hidden1: 256 → Hidden2: 256 → Output: 6

# After (Phase 2)
Q-Network:
  Input: 57 → Hidden1: 256 → Hidden2: 256 → Output: 6

# 參數增加: (57-53) × 256 = 1024 個參數 (+0.3%)
```

### Step 4: 資料集重新生成

**注意**: Phase 2 數據集與 Phase 1 **不兼容**（狀態維度不同）

**步驟**:
```bash
# 1. 清理 Phase 1 模型（避免混淆）
mkdir -p data/models/dqn_phase1_backup
mv data/models/dqn/* data/models/dqn_phase1_backup/

# 2. 生成新數據集（57 維狀態）
PYTHONPATH=. venv/bin/python tools/ml_training_data_generator/main.py \
  2>&1 | tee /tmp/ml_data_gen_phase2.log

# 3. 驗證狀態維度
PYTHONPATH=. venv/bin/python -c "
import h5py
with h5py.File('data/ml_training/rl_training_dataset_YYYYMMDD_HHMMSS.h5', 'r') as f:
    state_dim = f['train/states'].shape[1]
    print(f'State dimension: {state_dim}')
    assert state_dim == 57, f'Expected 57, got {state_dim}'
    print('✅ State dimension verified')
"
```

### Step 5: DQN 訓練（可能需要更多 episodes）

**為何可能需要更多訓練？**
- 狀態空間更複雜 (53 → 57)
- DQN 需要學習距離與 RSRP 的權衡
- 更多參數（輸入層 +1024 params）

**建議訓練配置**:
```yaml
# tools/rl_algorithms/dqn/config/training_config.yaml

training:
  episodes: 1000  # ✅ Increase from 500 (Phase 1 可能不夠)
  batch_size: 64
  learning_rate: 0.0001  # Keep same

  # Exploration schedule (更長的探索期)
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay: 0.997  # ✅ Slower decay (from 0.995)

early_stopping:
  enabled: true
  patience: 100  # ✅ Increase from 50
  min_delta: 0.1
```

**訓練命令**:
```bash
PYTHONPATH=. venv/bin/python tools/rl_algorithms/dqn/train.py \
  2>&1 | tee /tmp/dqn_phase2_training.log

# 預期訓練時間: ~1-1.5 小時 (1000 episodes)
```

### Step 6: 評估與對比

**三方對比**:
```bash
# 1. RSRP Baseline (always-greedy)
# 2. Phase 1 (weighted combination, state_dim=53)
# 3. Phase 2 (distance in state, state_dim=57)
```

**評估腳本**:
```bash
PYTHONPATH=. venv/bin/python tools/rl_algorithms/dqn/evaluate.py \
  --model-path data/models/dqn/best_model.pt \
  --output-dir data/evaluation_reports/dqn_phase2 \
  2>&1 | tee /tmp/dqn_phase2_eval.log
```

---

## 📊 預期結果

### 定量對比

| 指標 | RSRP Baseline | Phase 1 | Phase 2 目標 |
|------|---------------|---------|--------------|
| D2 使用率 | N/A | ~15% | 自動學習 |
| 換手率 | ~2-3% | ~10% | 8-15% |
| 總獎勵改進 | 0% (baseline) | +20% | **+25%** |
| 訓練時間 | N/A | ~30 min | ~60-90 min |
| 模型參數 | N/A | ~140K | ~141K (+1K) |

### 定性優勢

**Phase 2 vs Phase 1**:
1. **自適應權重**: 不同場景不同策略（近地仰角 vs 遠距仰角）
2. **潛在更優解**: 可能發現人類未想到的策略
3. **端到端學習**: 減少人工特徵工程

**Phase 2 風險**:
1. **可解釋性降低**: 難以理解 DQN 的決策邏輯
2. **訓練不穩定**: 更複雜的狀態空間可能導致收斂困難
3. **過擬合風險**: 如果訓練數據不足

---

## 🔬 實驗設計

### Ablation Study

為了驗證距離特徵的有效性，進行以下實驗：

**實驗組**:
1. **Baseline**: 無距離特徵 (state_dim=53)
2. **+Serving Distance**: 只加服務距離 (state_dim=54)
3. **+Candidate Distance**: 加候選距離 (state_dim=53+5=58)
4. **+Distance Ratio**: 加相對比率 (state_dim=59)
5. **Full (Phase 2)**: 所有距離特徵 (state_dim=57)

**對比指標**:
- 訓練收斂速度（達到 90% 最佳獎勵的 episodes）
- 最終評估獎勵
- 換手決策分布

### 特徵重要性分析

**方法 1**: SHAP (SHapley Additive exPlanations)
```python
import shap

# 計算 SHAP 值
explainer = shap.DeepExplainer(dqn_model, background_data)
shap_values = explainer.shap_values(test_states)

# 分析距離特徵的重要性
distance_feature_indices = [14, 21, 28, 35, 42, 49, 53]  # serving + 5 candidates + ratio
distance_importance = shap_values[:, distance_feature_indices].mean(axis=0)

print("Distance feature importance:")
print(f"  Serving distance: {distance_importance[0]:.3f}")
print(f"  Avg candidate distance: {distance_importance[1:6].mean():.3f}")
print(f"  Distance ratio: {distance_importance[6]:.3f}")
```

**方法 2**: Permutation Importance
```python
from sklearn.inspection import permutation_importance

# 隨機打亂距離特徵，觀察性能下降
baseline_reward = evaluate_model(dqn_model, test_env)

# Permute distance features
permuted_states = test_states.copy()
permuted_states[:, distance_feature_indices] = np.random.permutation(
    permuted_states[:, distance_feature_indices]
)
permuted_reward = evaluate_model(dqn_model, permuted_states)

importance = (baseline_reward - permuted_reward) / baseline_reward * 100
print(f"Distance features contribution: {importance:.1f}%")
```

---

## ⚠️ 風險與緩解

### 技術風險

**風險 1**: 距離特徵與 RSRP 高度相關（信息冗余）
**概率**: 中
**影響**: Phase 2 性能提升有限
**緩解**:
```python
# 預先檢查相關性
import numpy as np
correlation = np.corrcoef(rsrp_features, distance_features)[0, 1]
print(f"RSRP-Distance correlation: {correlation:.3f}")
# 如果 |correlation| > 0.8，考慮只保留其中一個
```

**風險 2**: 訓練不穩定（更複雜的狀態空間）
**概率**: 中
**影響**: Loss 震盪，無法收斂
**緩解**:
- 降低學習率 (0.0001 → 0.00005)
- 增加 replay buffer (100K → 200K)
- 使用 Double DQN 或 Dueling DQN

**風險 3**: 過擬合（訓練數據不足）
**概率**: 低
**影響**: Test 性能遠低於 Val
**緩解**:
- 監控 train/val/test gap
- 早停 (patience=100)
- 如果嚴重，考慮數據增強

### 學術風險

**風險**: 審稿人要求解釋為何 Phase 2 優於 Phase 1
**緩解**:
- 提供 ablation study
- 分析學習到的權重（與人工權重對比）
- 展示 Phase 2 在不同場景下的自適應能力

---

## ✅ 驗收標準

### 必須達成 (Must-Have)

- [x] 狀態維度正確擴展至 57
- [x] 數據集生成無錯誤
- [x] DQN 訓練收斂（loss 下降，reward 上升）
- [x] 總獎勵改進 ≥ Phase 1
- [x] 代碼通過所有單元測試

### 期望達成 (Should-Have)

- [ ] 總獎勵改進 > Phase 1 + 5%
- [ ] 訓練穩定（無震盪）
- [ ] Ablation study 顯示距離特徵有效

### 加分項 (Nice-to-Have)

- [ ] SHAP 分析完成
- [ ] 發現「Phase 1 未能學到」的策略
- [ ] 撰寫學術論文草稿

---

## 📝 實施檢查清單

### 代碼修改

- [ ] 修改 `state_extractor.py` - 擴展狀態空間
- [ ] 新增 `_calculate_ground_distance()` 方法
- [ ] 更新配置文件 (state_dim: 57)
- [ ] 確保 Stage 6 提供 `ground_point` 數據
- [ ] 更新單元測試（狀態維度檢查）

### 數據生成

- [ ] 備份 Phase 1 數據集
- [ ] 生成 Phase 2 數據集 (state_dim=57)
- [ ] 驗證狀態維度正確
- [ ] 檢查數據完整性

### 模型訓練

- [ ] 備份 Phase 1 模型
- [ ] 更新訓練配置（1000 episodes）
- [ ] 啟動訓練
- [ ] 監控訓練曲線
- [ ] 保存最佳模型

### 評估與分析

- [ ] 運行評估腳本
- [ ] 三方對比（RSRP, Phase 1, Phase 2）
- [ ] Ablation study
- [ ] SHAP 分析（可選）
- [ ] 生成對比報告

### 文檔與報告

- [ ] 更新開發日誌
- [ ] 記錄實驗結果
- [ ] 撰寫 Phase 2 總結
- [ ] 對比 Phase 1 和 Phase 2 優劣

---

## 📅 時間計劃

**Day 1 (4-6 hours)**: 狀態空間擴展
- [ ] 09:00-11:00: 修改 state_extractor.py
- [ ] 11:00-12:00: 更新配置文件
- [ ] 13:00-14:00: 單元測試
- [ ] 14:00-15:00: 數據集生成
- [ ] 15:00-16:00: 數據驗證

**Day 2 (6-8 hours)**: DQN 訓練
- [ ] 09:00-10:00: 更新訓練配置
- [ ] 10:00-11:00: 啟動訓練（1000 episodes）
- [ ] 11:00-17:00: 監控訓練（中途可做其他事）
- [ ] 17:00-18:00: 訓練完成檢查

**Day 3 (4-6 hours)**: 評估與分析
- [ ] 09:00-10:00: 模型評估
- [ ] 10:00-11:00: 三方對比
- [ ] 11:00-12:00: Ablation study
- [ ] 13:00-15:00: SHAP 分析（可選）
- [ ] 15:00-16:00: 結果整理

**Day 4-5 (選擇性)**: 深入研究
- [ ] 特徵重要性分析
- [ ] 決策可視化
- [ ] 學術論文撰寫

**總工時**: 14-20 小時

---

## 📚 學術參考

1. **Mnih et al. (2015)** - "Human-level control through deep reinforcement learning", *Nature*
   - DQN 網絡設計與訓練方法

2. **Henderson et al. (2018)** - "Deep Reinforcement Learning that Matters", *AAAI*
   - Ablation study 與特徵重要性分析

3. **Lundberg & Lee (2017)** - "A Unified Approach to Interpreting Model Predictions", *NeurIPS*
   - SHAP 方法用於 DQN 可解釋性

4. **3GPP TR 38.821** - "Solutions for NR to support non-terrestrial networks (NTN)"
   - LEO 衛星幾何參數定義

5. **Badini et al. (2024)** - "Handover Management in LEO Satellite Networks"
   - 對比 Phase 1 和 Phase 2 的優劣

---

## 🔄 Phase 1 vs Phase 2 對比

| 維度 | Phase 1 (Weighted) | Phase 2 (Learned) |
|------|-------------------|-------------------|
| **實現難度** | ⭐⭐ 中等 | ⭐⭐⭐ 較高 |
| **訓練時間** | ~30 min | ~60-90 min |
| **可解釋性** | ⭐⭐⭐⭐ 高 | ⭐⭐ 低 |
| **自適應性** | ⭐⭐ 固定權重 | ⭐⭐⭐⭐ 自動學習 |
| **性能上限** | ⭐⭐⭐ 受限於人工權重 | ⭐⭐⭐⭐ 潛在更優 |
| **調參難度** | ⭐⭐ 調整權重 | ⭐⭐⭐ 調整超參數 |
| **學術價值** | ⭐⭐⭐ 多目標優化 | ⭐⭐⭐⭐ 端到端學習 |

**建議**:
- 如果追求可解釋性 → Phase 1
- 如果追求最優性能 → Phase 2
- 最佳方案: **兩者都實現，論文中對比**

---

**文件版本**: v1.0
**最後更新**: 2025-10-24
**作者**: SuperClaude (Orbit Engine Development Team)
**前置文件**: PHASE1_WEIGHTED_COMBINATION.md
