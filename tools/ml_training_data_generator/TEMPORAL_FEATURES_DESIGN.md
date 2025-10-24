# 時間特徵設計文檔
## Temporal Features Design for D2 Predictive Handover

**日期**: 2025-10-24
**目的**: 添加時間特徵以增強 DQN 對 D2 預測性換手的學習能力

---

## 1. 當前狀態特徵 (Baseline)

### SatelliteState (7 features per satellite)
```python
@dataclass
class SatelliteState:
    rsrp_dbm: float          # Instant RSRP
    rsrq_db: float           # Instant RSRQ
    snr_db: float            # Instant SNR
    distance_km: float       # Instant distance
    elevation_deg: float     # Instant elevation
    azimuth_deg: float       # Instant azimuth
    load_percent: float      # Satellite load
```

### 總狀態維度
- Serving satellite: 7 features
- Candidate satellites (5): 5 × 7 = 35 features
- QoS requirements: 4 features
- Network load: 3 features
- Time features: 4 features
- **Total**: 53 features

---

## 2. 新增時間特徵設計

### 2.1 Velocity Features (動態特徵)

#### RSRP Velocity (dRSRP/dt)
```python
rsrp_velocity: float  # dB/s

# Calculation method
rsrp_velocity = (rsrp_t - rsrp_t-1) / delta_t
```

**學術依據**:
- SOURCE: Badini et al. (2024) IEEE TAES, Section III.B
- RSRP velocity 指示信號質量的變化趨勢
- 正值 → 信號改善 (衛星接近)
- 負值 → 信號劣化 (衛星遠離)

**使用場景**:
- D2 策略應優先選擇 RSRP velocity > 0 的衛星
- 即使當前 RSRP 較低，但 velocity 正向表示未來會改善

#### Distance Velocity (dDistance/dt)
```python
distance_velocity: float  # km/s

# Calculation method
distance_velocity = (distance_t - distance_t-1) / delta_t
```

**學術依據**:
- SOURCE: 3GPP TR 38.821 Section 6.4.2 (LEO mobility)
- LEO 衛星相對速度可達 7.5 km/s
- Distance velocity 直接反映衛星軌道幾何

**使用場景**:
- 負值 → 衛星接近 (優選)
- 正值 → 衛星遠離 (應避免換手)

### 2.2 Predicted Features (預測特徵)

#### Predicted RSRP (t+30s, t+60s)
```python
predicted_rsrp_30s: float  # dBm (30 seconds later)
predicted_rsrp_60s: float  # dBm (60 seconds later)

# Calculation method
1. Use SGP4 to predict satellite position at t+30s, t+60s
2. Calculate predicted distance using ground station position
3. Estimate RSRP using Free Space Path Loss (FSPL):
   FSPL(dB) = 20*log10(d_km) + 20*log10(f_MHz) + 32.44
   predicted_rsrp = tx_power - fspl - atmospheric_loss
```

**學術依據**:
- SOURCE: ITU-R P.525-4 (Free Space Path Loss)
- SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a (D2 predictive intent)

**簡化策略** (避免重複完整信號計算):
- 使用 FSPL 線性近似：
  ```python
  # 基於當前 RSRP 和 distance velocity 估算
  delta_distance = distance_velocity * delta_t
  delta_rsrp_db = -20 * log10((distance + delta_distance) / distance)
  predicted_rsrp = current_rsrp + delta_rsrp_db
  ```

**使用場景**:
- D2 策略應選擇 predicted_rsrp_60s > threshold 的衛星
- 即使當前 RSRP 較好，但預測會低於門檻應避免

---

## 3. 更新後的狀態結構

### SatelliteState (11 features per satellite)
```python
@dataclass
class SatelliteState:
    # Instant features (7)
    rsrp_dbm: float
    rsrq_db: float
    snr_db: float
    distance_km: float
    elevation_deg: float
    azimuth_deg: float
    load_percent: float

    # Temporal features (4) ← NEW
    rsrp_velocity: float         # dB/s
    distance_velocity: float     # km/s
    predicted_rsrp_30s: float    # dBm
    predicted_rsrp_60s: float    # dBm
```

### 總狀態維度 (更新)
- Serving satellite: **11** features (+4)
- Candidate satellites (5): 5 × 11 = **55** features (+20)
- QoS requirements: 4 features
- Network load: 3 features
- Time features: 4 features
- **Total**: **77** features (+24)

---

## 4. 實施計劃

### Phase 1: 修改數據結構 ✅
- [x] 更新 `types.py::SatelliteState` 添加 4 個新特徵
- [x] 更新 `to_numpy()` 方法輸出 11 維向量
- [x] 更新 `RLState.to_numpy()` 狀態維度為 77

### Phase 2: 實現特徵計算
- [ ] 在 `state_extractor.py` 添加 `_calculate_rsrp_velocity()`
- [ ] 在 `state_extractor.py` 添加 `_calculate_distance_velocity()`
- [ ] 在 `state_extractor.py` 添加 `_predict_rsrp_future()`
- [ ] 處理邊界情況（t=0 時無歷史數據 → velocity=0）

### Phase 3: 驗證與測試
- [ ] 單元測試: velocity 計算正確性
- [ ] 單元測試: predicted RSRP 合理性檢查
- [ ] 生成測試數據集，檢查特徵分布
- [ ] 驗證狀態維度 = 77

### Phase 4: 重新生成訓練數據
- [ ] 運行 `dataset_builder.py` 生成新 HDF5
- [ ] 檢查數據集統計信息
- [ ] 更新 handover-rl 的數據加載器（如需要）

---

## 5. 預期影響

### 對 DQN 學習的幫助
1. **Velocity features**: 讓 DQN 理解信號/距離的變化趨勢
2. **Predicted RSRP**: 直接提供未來信號質量預測，減少學習難度
3. **D2 優勢凸顯**: D2 選擇的衛星應該在這些時間特徵上表現更好

### 學術貢獻
- 明確量化 D2 的預測性價值
- 驗證時間特徵對 LEO 換手決策的重要性
- 提供可復現的特徵工程方法

---

## 6. References

- Badini et al. (2024). "Reinforcement Learning for LEO Satellite Handover Optimization". IEEE Transactions on Aerospace and Electronic Systems.
- 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a: Event D2 (Distance-based handover)
- 3GPP TR 38.821 Section 6.4.2: NTN high-speed mobility requirements
- ITU-R P.525-4: Free Space Path Loss calculation
- Temporal D2 Analysis: `docs/D2_TEMPORAL_ANALYSIS_FINDINGS.md`

---

**Status**: Design Complete ✅
**Next**: Implementation (Phase 2)
**ETA**: ~2 hours for full implementation + testing
