# 時間特徵實施指南
## Implementation Guide for Temporal Features Integration

**狀態**: Phase 1-2 完成，Phase 3-4 待實施
**預計時間**: 30-60 分鐘

---

## ✅ 已完成工作 (Phase 1-2)

### 1. 數據結構更新 ✅
- `types.py::SatelliteState` 添加 4 個時間特徵
- 狀態維度：53 → 77 features
- `to_numpy()` 方法已更新

### 2. 時間特徵計算器 ✅
- `temporal_feature_calculator.py` 已創建
- 實現了 velocity 和 predicted RSRP 計算
- Factory function 可用：`create_temporal_feature_calculator()`

---

## 🚧 待完成工作 (Phase 3-4)

### Phase 3: 修改 state_extractor.py

#### 步驟 3.1: 添加計算器初始化

在 `state_extractor.py` 的 `__init__` 方法中：

```python
from .temporal_feature_calculator import create_temporal_feature_calculator

class StateExtractor:
    def __init__(self, max_candidates: int = 5):
        self.max_candidates = max_candidates
        # NEW: 初始化時間特徵計算器
        self.temporal_calculator = create_temporal_feature_calculator(time_interval_sec=30.0)
        logger.info(f"StateExtractor initialized with temporal features")
```

#### 步驟 3.2: 修改 _build_satellite_state 方法

在 `state_extractor.py` 找到 `_build_satellite_state` 方法（約 line 292），添加時間特徵計算：

```python
def _build_satellite_state(
    self,
    satellite_id: int,
    entry: Dict,
    stage6_output: Stage6Output,
    timestamp_idx: Optional[int] = None  # NEW: 添加時間索引參數
) -> Optional[SatelliteState]:
    """構建衛星狀態（包含時間特徵）"""

    # ... 現有代碼 (提取 signal_quality, visibility_metrics 等) ...

    # NEW: 計算時間特徵
    temporal_features = {
        'rsrp_velocity': 0.0,
        'distance_velocity': 0.0,
        'predicted_rsrp_30s': signal_quality.get('rsrp_dbm', 0.0),
        'predicted_rsrp_60s': signal_quality.get('rsrp_dbm', 0.0)
    }

    # 如果有時間索引和時間序列，計算實際值
    if timestamp_idx is not None and timestamp_idx >= 0:
        sat_id_str = str(satellite_id)
        if sat_id_str in stage6_output.signal_analysis:
            time_series = stage6_output.signal_analysis[sat_id_str].get('time_series', [])
            if 0 <= timestamp_idx < len(time_series):
                temporal_features = self.temporal_calculator.calculate_all_temporal_features(
                    time_series, timestamp_idx
                )

    # 構建 SatelliteState (添加時間特徵參數)
    return SatelliteState(
        satellite_id=satellite_id,
        rsrp_dbm=signal_quality.get('rsrp_dbm', 0.0),
        rsrq_db=signal_quality.get('rsrq_db', 0.0),
        snr_db=signal_quality.get('snr_db', 0.0),
        distance_km=visibility_metrics.get('distance_km', 0.0),
        elevation_deg=visibility_metrics.get('elevation_deg', 0.0),
        azimuth_deg=visibility_metrics.get('azimuth_deg', 0.0),
        load_percent=load_percent,
        # NEW: 時間特徵
        rsrp_velocity=temporal_features['rsrp_velocity'],
        distance_velocity=temporal_features['distance_velocity'],
        predicted_rsrp_30s=temporal_features['predicted_rsrp_30s'],
        predicted_rsrp_60s=temporal_features['predicted_rsrp_60s']
    )
```

#### 步驟 3.3: 更新所有 _build_satellite_state 調用

在 `state_extractor.py` 中搜索所有調用 `_build_satellite_state` 的地方，添加 `timestamp_idx` 參數：

```python
# 示例：在 extract_serving_satellite 中
serving_satellite = self._build_satellite_state(
    best_satellite_id,
    entry,
    stage6_output,
    timestamp_idx=timestamp_idx  # NEW
)

# 示例：在 extract_candidates 中
satellite_state = self._build_satellite_state(
    sat_id,
    entry,
    stage6_output,
    timestamp_idx=timestamp_idx  # NEW
)
```

### Phase 4: 驗證與測試

#### 步驟 4.1: 快速驗證

```bash
cd /home/sat/satellite/orbit-engine
PYTHONPATH=. python3 -c "
from tools.ml_training_data_generator.core.types import SatelliteState

# 測試新特徵
sat = SatelliteState(
    satellite_id=12345,
    rsrp_dbm=-35.0, rsrq_db=-10.0, snr_db=20.0,
    distance_km=1000.0, elevation_deg=45.0, azimuth_deg=180.0, load_percent=50.0,
    rsrp_velocity=-0.5, distance_velocity=2.0,
    predicted_rsrp_30s=-36.0, predicted_rsrp_60s=-37.0
)

state_vector = sat.to_numpy()
print(f'✅ State vector shape: {state_vector.shape}')
print(f'✅ Expected: (11,), Got: {state_vector.shape}')
assert state_vector.shape == (11,), f'Error: shape mismatch!'
print('✅ Validation passed!')
"
```

#### 步驟 4.2: 生成測試數據集

```bash
# 重新生成 HDF5 數據集
cd /home/sat/satellite/orbit-engine
PYTHONPATH=. venv/bin/python3 tools/ml_training_data_generator/dataset_builder.py \
    --stage6-file data/outputs/stage6/stage6_research_optimization_20251024_010110.json \
    --output data/ml_training/rl_training_dataset_temporal.h5

# 檢查數據集
PYTHONPATH=. venv/bin/python3 -c "
import h5py
import numpy as np

with h5py.File('data/ml_training/rl_training_dataset_temporal.h5', 'r') as f:
    states = f['train/states'][:]
    print(f'✅ Train states shape: {states.shape}')
    print(f'✅ Expected state_dim: 77, Got: {states.shape[1]}')

    # 檢查時間特徵範圍
    for i, feat_name in enumerate(['rsrp', 'rsrq', 'snr', 'distance', 'elevation', 'azimuth', 'load',
                                     'rsrp_velocity', 'distance_velocity', 'pred_rsrp_30s', 'pred_rsrp_60s']):
        feat_vals = states[:, i]
        print(f'   {feat_name}: min={feat_vals.min():.2f}, max={feat_vals.max():.2f}, mean={feat_vals.mean():.2f}')
"
```

---

## 📊 預期結果

### 數據集統計（預期）
```
State dimension: 77
- Serving satellite: 11 features
  - Instant (7): rsrp, rsrq, snr, distance, elevation, azimuth, load
  - Temporal (4): rsrp_velocity, distance_velocity, predicted_rsrp_30s, predicted_rsrp_60s
- Candidate satellites (5): 5 × 11 = 55 features
- QoS requirements: 4 features
- Network load: 3 features
- Time features: 4 features
```

### 時間特徵預期範圍
- `rsrp_velocity`: -5 ~ 5 dB/s (典型)
- `distance_velocity`: -8 ~ 8 km/s (LEO 相對速度)
- `predicted_rsrp_30s`: -140 ~ -20 dBm
- `predicted_rsrp_60s`: -140 ~ -20 dBm

---

## ⚠️ 常見問題

### Q1: 狀態維度不匹配錯誤
**Error**: `ValueError: State dimension mismatch: expected 53, got 77`

**解決**: 確保 handover-rl 的環境配置已更新：
```python
# 在 handover-rl/config/training_config.yaml
state_dim: 77  # 更新從 53 → 77
```

### Q2: 時間特徵全為 0
**原因**: `timestamp_idx` 未正確傳遞到 `_build_satellite_state`

**檢查**: 確保所有調用點都添加了 `timestamp_idx` 參數

### Q3: predicted_rsrp 超出合理範圍
**原因**: Distance velocity 異常大導致預測錯誤

**解決**: 已在 `temporal_feature_calculator.py` 中添加 clamp [-140, -20] dBm

---

## 🎯 完成檢查清單

- [x] `types.py::SatelliteState` 添加 4 個時間特徵
- [x] `types.py::RLState.to_numpy()` 更新狀態維度為 77
- [x] 創建 `temporal_feature_calculator.py`
- [ ] `state_extractor.py` 初始化 `TemporalFeatureCalculator`
- [ ] `state_extractor.py::_build_satellite_state` 添加時間特徵計算
- [ ] 更新所有 `_build_satellite_state` 調用點添加 `timestamp_idx`
- [ ] 運行驗證測試
- [ ] 重新生成 HDF5 訓練數據集
- [ ] 更新 handover-rl 配置（state_dim: 77）

---

## 📝 下一步

完成以上步驟後：
1. 驗證新數據集質量
2. 更新 handover-rl 的狀態維度配置
3. 開始 DQN 訓練，觀察時間特徵的學習效果
4. 分析特徵重要性（是否比 baseline 的 0.97x 更好）

**預期改進**: D2 特徵重要性從 0.97x 提升到 > 1.2x

---

**Status**: 實施指南完成
**Next Action**: 執行 Phase 3 (修改 state_extractor.py)
