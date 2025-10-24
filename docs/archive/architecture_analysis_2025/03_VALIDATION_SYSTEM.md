# 雙層驗證系統架構

本文檔詳細說明 Orbit Engine 的雙層驗證系統設計和實現。

## 驗證系統總覽

### 設計理念

```
每個階段執行後 → 立即驗證 (Fail-Fast)
  ↓
Layer 1: 內建驗證 (Processor 內部)
  - 算法正確性驗證
  - 數據完整性檢查
  - 學術標準合規性
  ↓ (通過後)
Layer 2: 快照品質檢查 (Validator 外部)
  - 數據結構合理性
  - 架構合規性檢查
  - 統計特性驗證
  ↓ (通過後)
執行下一階段
```

### Fail-Fast 策略

```python
# 在 run_all_stages_sequential() 中
for stage_num in range(1, 7):
    # 執行階段
    success, result, processor = executor(stage_results)

    # 立即驗證
    validation_success, validation_msg = validate_stage_immediately(...)

    # 驗證失敗則停止
    if not validation_success:
        print(f'❌ 階段{stage_num}驗證失敗: {validation_msg}')
        return False, stage_num, validation_msg  # 立即返回
```

**優勢**:
- 節省計算資源 (不執行後續無意義階段)
- 快速定位問題 (問題發生時立即停止)
- 保持數據一致性 (避免錯誤數據流向下游)

---

## Layer 1: 內建驗證 (Processor 內部)

### 實現位置

每個階段的處理器類內部實現：

```
src/stages/stage1_orbital_calculation/stage1_main_processor.py
  - run_validation_checks(data)
  - save_validation_snapshot(data)

src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py
  - run_validation_checks(data)
  - save_validation_snapshot(data)

... (以此類推)
```

### 驗證流程

```python
def validate_stage_immediately(stage_processor, processing_results, stage_num, stage_name):
    # 1. 檢查 ProcessingResult 狀態
    if hasattr(processing_results, "status"):
        if processing_results.status.value != 'success':
            return False, f"階段{stage_num}執行失敗"

    # 2. 保存驗證快照
    if hasattr(stage_processor, 'save_validation_snapshot'):
        snapshot_success = stage_processor.save_validation_snapshot(data)
        if not snapshot_success:
            return False, f"階段{stage_num}驗證快照生成失敗"

    # 3. 執行內建驗證
    if hasattr(stage_processor, 'run_validation_checks'):
        validation_result = stage_processor.run_validation_checks(data)
        validation_status = validation_result.get('validation_status')

        if validation_status != 'passed':
            return False, f"階段{stage_num}驗證失敗"

    # 4. 通過 Layer 1，進入 Layer 2
    return check_validation_snapshot_quality(stage_num)
```

### 驗證內容

Layer 1 驗證由各階段處理器自行實現，通常包括：

- **算法正確性**: 計算結果符合公式和標準
- **數據完整性**: 所有必要字段存在且有效
- **範圍合理性**: 數值在合理範圍內
- **學術標準合規性**: 符合 ITU-R, 3GPP, NASA JPL 標準

### 驗證快照

每個階段保存驗證快照到 `data/validation_snapshots/`:

```
data/validation_snapshots/
├── stage1_validation.json
├── stage2_validation.json
├── stage3_validation.json
├── stage4_validation.json
├── stage5_validation.json
└── stage6_validation.json
```

**快照結構** (通用格式):

```json
{
  "status": "success",
  "validation_passed": true,
  "timestamp": "2025-10-10T12:34:56.789012Z",
  "metadata": {
    "stage": 1,
    "stage_name": "數據載入層"
  },
  "data_summary": {
    "satellite_count": 9015,
    "constellation_statistics": {
      "starlink": {"count": 6654},
      "oneweb": {"count": 2361}
    }
  },
  "validation_details": {
    "success_rate": 1.0,
    "checks_performed": 15,
    "checks_passed": 15
  },
  "satellites_sample": [
    // 前 20 顆衛星樣本
  ]
}
```

---

## Layer 2: 快照品質檢查 (Validator 外部)

### 實現位置

獨立的驗證器模塊：

```
scripts/stage_validators/
├── stage1_validator.py - check_stage1_validation(snapshot_data)
├── stage2_validator.py - check_stage2_validation(snapshot_data)
├── stage3_validator.py - check_stage3_validation(snapshot_data)
├── stage4_validator.py - check_stage4_validation(snapshot_data)
├── stage5_validator.py - check_stage5_validation(snapshot_data)
└── stage6_validator.py - check_stage6_validation(snapshot_data)
```

### 驗證流程

```python
def check_validation_snapshot_quality(stage_num):
    """Layer 2 驗證: 使用重構後的模塊化驗證器"""

    # 1. 讀取驗證快照
    snapshot_path = f"data/validation_snapshots/stage{stage_num}_validation.json"
    with open(snapshot_path, 'r', encoding='utf-8') as f:
        snapshot_data = json.load(f)

    # 2. 調用對應的驗證器
    validator = STAGE_VALIDATORS.get(stage_num)
    if not validator:
        return False, f"❌ Stage {stage_num} 驗證器不存在"

    # 3. 執行驗證
    return validator(snapshot_data)
```

### 驗證內容

Layer 2 驗證**信任** Layer 1 結果，不重複詳細驗證，主要檢查：

- **數據結構**: 快照格式正確
- **合理性檢查**: 統計數據合理
- **架構合規性**: 符合系統設計規範
- **抽樣檢查**: 隨機抽樣驗證數據品質

---

## 各階段驗證詳細說明

### Stage 1 驗證器

**文件**: `scripts/stage_validators/stage1_validator.py` (190 行)

**檢查項目**:

1. **數據完整性** (P1)
   ```python
   # 動態計算期望總數
   expected_total = starlink_count + oneweb_count
   min_acceptable = int(expected_total * 0.95)  # 95% 完整度標準

   if satellite_count < min_acceptable:
       return False, f"❌ 數據不完整: {satellite_count}/{expected_total}"
   ```

2. **時間基準合規性** (P0 - CRITICAL)
   ```python
   # 防禦性檢查 - 確保不存在統一時間基準字段
   forbidden_time_fields = ['calculation_base_time', 'primary_epoch_time', 'unified_time_base']
   for field in forbidden_time_fields:
       if field in metadata:
           return False, f"❌ 學術標準違規: 檢測到禁止字段 '{field}'"
   ```
   **依據**: 學術標準要求每顆衛星保留其原始 TLE epoch，禁止統一時間基準。

3. **配置完整性** (P1)
   ```python
   # 檢查 constellation_configs 存在性
   if 'starlink' not in constellation_configs:
       return False, "❌ constellation_configs 缺失 starlink"
   if 'oneweb' not in constellation_configs:
       return False, "❌ constellation_configs 缺失 oneweb"

   # 檢查 research_configuration 完整性
   required_fields = ['name', 'latitude_deg', 'longitude_deg', 'altitude_m']
   for field in required_fields:
       if field not in observation_location:
           return False, f"❌ observation_location 缺失 {field}"
   ```

4. **TLE 格式品質** (P0-2)
   ```python
   # 抽樣檢查 20 顆衛星 (系統性錯誤檢測)
   for i, sat in enumerate(satellites_sample[:20], start=1):
       # 檢查必要字段
       required_fields = ['name', 'tle_line1', 'tle_line2', 'epoch_datetime', 'constellation']
       for field in required_fields:
           if not sat.get(field):
               return False, f"❌ 第{i}顆衛星缺少 {field}"

       # 檢查 TLE 格式 (NORAD 標準 69 字符)
       if len(sat['tle_line1']) != 69:
           return False, f"❌ TLE Line1 長度 {len(tle_line1)} ≠ 69"
       if len(sat['tle_line2']) != 69:
           return False, f"❌ TLE Line2 長度 {len(tle_line2)} ≠ 69"

       # 檢查 TLE 行號
       if not tle_line1.startswith('1 '):
           return False, f"❌ TLE Line1 未以 '1 ' 開頭"
       if not tle_line2.startswith('2 '):
           return False, f"❌ TLE Line2 未以 '2 ' 開頭"
   ```

   **抽樣量說明**:
   - 樣本量: 20 顆
   - 目的: 系統性錯誤檢測 (非統計推論)
   - 範例: 檢測所有 TLE 是否都是空字串 (程式 bug)
   - 機率分析: 假設總體有 50% 系統性錯誤，隨機 20 顆都正常的機率 < 0.0001%

5. **Epoch 多樣性** (P1-2)
   ```python
   # 檢查 Epoch 多樣性（至少 5 個不同 epoch）
   unique_epochs = len(set(epoch_times))
   min_unique_epochs = 5

   if unique_epochs < min_unique_epochs:
       return False, f"❌ Epoch 多樣性不足（{unique_epochs}/20，應≥{min_unique_epochs}）"
   ```

   **閾值依據**:
   - 目的: 檢測是否所有 TLE 來自同一時間點（系統性時間基準錯誤）
   - 真實數據特性: 20 顆樣本中有 17 個 unique epochs (85% 多樣性)
   - 閾值: 5 個 (25% 多樣性) - 對應統計學 P10 分位數

**返回值**:

```python
return True, "Stage 1 數據完整性檢查通過: 載入9015顆衛星 (完整度:100.0%, Starlink:6654, OneWeb:2361) | 品質檢查: 20顆樣本✓, TLE格式✓, Epoch多樣性 17/20✓ | [constellation_configs✓, research_config✓]"
```

---

### Stage 2 驗證器

**文件**: `scripts/stage_validators/stage2_validator.py`

**檢查項目**:

1. **衛星數量一致性**
   ```python
   stage1_count = expected_satellite_count  # 從 metadata 獲取
   stage2_count = snapshot_data.get('data_summary', {}).get('satellite_count', 0)

   if abs(stage2_count - stage1_count) > 5:
       return False, f"❌ 衛星數量不一致: Stage 1 {stage1_count}, Stage 2 {stage2_count}"
   ```

2. **時間序列長度合理性**
   ```python
   avg_time_series_length = snapshot_data.get('data_summary', {}).get('avg_time_series_length', 0)

   if avg_time_series_length < 180:
       return False, f"❌ 時間序列過短: {avg_time_series_length} < 180"
   ```

3. **軌道週期正確性**
   ```python
   constellation_summary = snapshot_data.get('metadata', {}).get('constellation_summary', {})

   # Starlink: 90-95 分鐘
   starlink_period = constellation_summary.get('starlink', {}).get('avg_period_min', 0)
   if not (90 <= starlink_period <= 95):
       return False, f"❌ Starlink 軌道週期異常: {starlink_period} min (應為 90-95 min)"

   # OneWeb: 109-115 分鐘
   oneweb_period = constellation_summary.get('oneweb', {}).get('avg_period_min', 0)
   if not (109 <= oneweb_period <= 115):
       return False, f"❌ OneWeb 軌道週期異常: {oneweb_period} min (應為 109-115 min)"
   ```

4. **HDF5 文件存在性**
   ```python
   h5_file_path = snapshot_data.get('metadata', {}).get('h5_file_path')
   if not os.path.exists(h5_file_path):
       return False, f"❌ HDF5 文件不存在: {h5_file_path}"
   ```

5. **TEME 座標範圍合理性** (抽樣檢查)
   ```python
   satellites_sample = snapshot_data.get('satellites_sample', [])
   for sat in satellites_sample[:10]:
       position_km = sat.get('sample_teme_position', {})
       distance = (position_km['x']**2 + position_km['y']**2 + position_km['z']**2)**0.5

       if not (550 <= distance <= 1200):
           return False, f"❌ TEME 座標距離異常: {distance:.1f} km (應為 550-1200 km)"
   ```

---

### Stage 3 驗證器

**文件**: `scripts/stage_validators/stage3_validator.py`

**檢查項目**:

1. **衛星數量一致性**
2. **座標系統正確性**
   ```python
   coordinate_system = snapshot_data.get('metadata', {}).get('coordinate_system')
   if coordinate_system != 'WGS84':
       return False, f"❌ 座標系統錯誤: {coordinate_system} (應為 WGS84)"
   ```

3. **地理座標範圍合理性**
   ```python
   for sat in satellites_sample[:10]:
       lat = sat.get('sample_geo_position', {}).get('latitude_deg')
       lon = sat.get('sample_geo_position', {}).get('longitude_deg')
       alt = sat.get('sample_geo_position', {}).get('altitude_m')

       if not (-90 <= lat <= 90):
           return False, f"❌ 緯度範圍錯誤: {lat}° (應為 ±90°)"
       if not (-180 <= lon <= 180):
           return False, f"❌ 經度範圍錯誤: {lon}° (應為 ±180°)"
       if not (550000 <= alt <= 1200000):
           return False, f"❌ 高度範圍錯誤: {alt} m (應為 550-1200 km)"
   ```

4. **時間序列完整性**
5. **仰角和方位角合理性**
   ```python
   elevation = sat.get('sample_geo_position', {}).get('elevation_deg')
   azimuth = sat.get('sample_geo_position', {}).get('azimuth_deg')

   if not (-90 <= elevation <= 90):
       return False, f"❌ 仰角範圍錯誤: {elevation}°"
   if not (0 <= azimuth <= 360):
       return False, f"❌ 方位角範圍錯誤: {azimuth}°"
   ```

---

### Stage 4 驗證器

**文件**: `scripts/stage_validators/stage4_validator.py`

**檢查項目**:

1. **可見衛星數量合理性**
   ```python
   visible_count = snapshot_data.get('data_summary', {}).get('visible_satellites_count', 0)
   total_satellites = snapshot_data.get('metadata', {}).get('total_satellites', 9015)

   min_visible = int(total_satellites * 0.4)  # 至少 40% 可見

   if visible_count < min_visible:
       return False, f"❌ 可見衛星過少: {visible_count}/{total_satellites}"
   ```

2. **池優化結果正確性**
   ```python
   pool_results = snapshot_data.get('metadata', {}).get('pool_optimization_results', {})

   # Starlink 覆蓋率應 ≥ 95%
   starlink_coverage = pool_results.get('starlink', {}).get('coverage_rate', 0)
   if starlink_coverage < 0.95:
       return False, f"❌ Starlink 覆蓋率不足: {starlink_coverage:.1%} < 95%"

   # OneWeb 覆蓋率應 ≥ 90%
   oneweb_coverage = pool_results.get('oneweb', {}).get('coverage_rate', 0)
   if oneweb_coverage < 0.90:
       return False, f"❌ OneWeb 覆蓋率不足: {oneweb_coverage:.1%} < 90%"
   ```

3. **服務窗口完整性**
4. **星座特定配置正確性**
   ```python
   # Starlink 仰角門檻應為 5°
   # OneWeb 仰角門檻應為 10°
   ```

---

### Stage 5 驗證器

**文件**: `scripts/stage_validators/stage5_validator.py`

**檢查項目**:

1. **衛星數量一致性**
2. **信號品質範圍合理性**
   ```python
   for sat in satellites_sample[:10]:
       signal_quality = sat.get('sample_signal_quality', {})
       rsrp = signal_quality.get('rsrp_dbm')
       rsrq = signal_quality.get('rsrq_db')
       sinr = signal_quality.get('sinr_db')

       # RSRP: -140 ~ -30 dBm (修復後，無截斷)
       if not (-140 <= rsrp <= -30):
           return False, f"❌ RSRP 範圍異常: {rsrp} dBm"

       # RSRQ: -20 ~ -3 dB
       if not (-20 <= rsrq <= -3):
           return False, f"❌ RSRQ 範圍異常: {rsrq} dB"

       # SINR: -10 ~ 30 dB
       if not (-10 <= sinr <= 30):
           return False, f"❌ SINR 範圍異常: {sinr} dB"
   ```

3. **時間序列完整性**
4. **A3 offset 存在性**
   ```python
   a3_offset = sat.get('sample_signal_quality', {}).get('a3_offset', {})
   if 'offset_mo_db' not in a3_offset or 'cell_offset_db' not in a3_offset:
       return False, "❌ A3 offset 數據缺失"
   ```

5. **ITU-R 模型參數正確性**
   ```python
   atmospheric_model = snapshot_data.get('metadata', {}).get('atmospheric_model')
   if 'ITU-R P.676' not in atmospheric_model:
       return False, f"❌ 大氣模型錯誤: {atmospheric_model}"
   ```

---

### Stage 6 驗證器

**文件**: `scripts/stage_validators/stage6_validator.py`

**檢查項目**:

1. **事件數量合理性**
   ```python
   total_events = snapshot_data.get('metadata', {}).get('total_events', {})
   a3_events = total_events.get('a3_events', 0)

   # A3 事件應該 > 0（修復 RSRP 截斷和服務衛星選擇後）
   if a3_events == 0:
       return False, "❌ A3 事件為 0（可能存在 RSRP 計算或服務衛星選擇錯誤）"
   ```

2. **換手決策完整性**
   ```python
   handover_evaluation = snapshot_data.get('metadata', {}).get('handover_evaluation', {})
   successful_rate = handover_evaluation.get('successful_rate', 0)

   if successful_rate < 0.5:
       return False, f"❌ 換手決策成功率過低: {successful_rate:.1%}"
   ```

3. **研究數據結構正確性**
   ```python
   # 檢查 state_action_pairs 存在性
   research_data = snapshot_data.get('research_data', {})
   if 'state_action_pairs' not in research_data:
       return False, "❌ 研究數據缺失 state_action_pairs"
   ```

4. **3GPP 標準合規性**
   ```python
   # 檢查事件定義符合 3GPP TS 38.331
   # A3: Neighbour becomes offset better than serving
   # A4: Neighbour becomes better than threshold
   # A5: Serving becomes worse than threshold1 and neighbour better than threshold2
   ```

---

## 驗證失敗處理

### 失敗返回格式

所有驗證器返回統一格式：

```python
(validation_passed: bool, message: str)
```

**範例**:

```python
# 成功
return True, "Stage 1 數據完整性檢查通過: ..."

# 失敗
return False, "❌ Stage 1 TLE 格式錯誤: Line1 長度 65 ≠ 69"
```

### 失敗後的行為

```python
if not validation_success:
    print(f'❌ 階段{stage_num}驗證失敗: {validation_msg}')
    return False, stage_num, validation_msg  # 立即停止管道
```

### 典型失敗場景

1. **數據完整性問題**
   ```
   ❌ Stage 1 數據不完整: 僅載入8500顆衛星 (完整度:94.3%，需要≥8564顆)
   ```

2. **學術標準違規**
   ```
   ❌ Stage 1 學術標準違規: 檢測到禁止字段 'calculation_base_time'
   ```

3. **算法結果異常**
   ```
   ❌ Stage 2 軌道週期異常: Starlink 112.5 min (應為 90-95 min)
   ```

4. **配置錯誤**
   ```
   ❌ Stage 4 覆蓋率不足: Starlink 88% < 95%
   ```

---

## 驗證快照範例

### Stage 1 驗證快照

```json
{
  "status": "success",
  "validation_passed": true,
  "timestamp": "2025-10-10T12:34:56.789012Z",
  "refactored_version": true,
  "interface_compliance": true,
  "metadata": {
    "stage": 1,
    "stage_name": "數據載入層",
    "constellation_statistics": {
      "starlink": {"count": 6654, "percentage": 73.8},
      "oneweb": {"count": 2361, "percentage": 26.2}
    },
    "constellation_configs": {
      "starlink": {
        "elevation_threshold": 5.0,
        "frequency_ghz": 12.5
      },
      "oneweb": {
        "elevation_threshold": 10.0,
        "frequency_ghz": 12.75
      }
    },
    "research_configuration": {
      "observation_location": {
        "name": "NTPU",
        "latitude_deg": 24.94388888,
        "longitude_deg": 121.37083333,
        "altitude_m": 36
      }
    }
  },
  "data_summary": {
    "satellite_count": 9015,
    "epoch_analysis": {
      "latest_date": "2025-10-05",
      "tolerance_hours": 24,
      "satellites_within_tolerance": 9015
    }
  },
  "validation_details": {
    "success_rate": 1.0,
    "checks_performed": 15,
    "checks_passed": 15
  },
  "satellites_sample": [
    {
      "name": "STARLINK-1007",
      "norad_id": 44713,
      "tle_line1": "1 44713U 19074A   25278.52404514  .00001234  00000-0  12345-4 0  9999",
      "tle_line2": "2 44713  53.0534 123.4567 0001234  45.6789 314.5678 15.12345678123456",
      "epoch_datetime": "2025-10-05T12:34:56.789012Z",
      "constellation": "starlink"
    }
    // ... 更多樣本
  ],
  "next_stage_ready": true
}
```

### Stage 5 驗證快照

```json
{
  "status": "success",
  "validation_passed": true,
  "timestamp": "2025-10-10T13:45:23.123456Z",
  "metadata": {
    "stage": 5,
    "stage_name": "信號品質分析層",
    "total_analyzed_satellites": 4523,
    "signal_model": "3GPP TS 38.214",
    "atmospheric_model": "ITU-R P.676-13 (official itur package v0.4.0)"
  },
  "data_summary": {
    "satellite_count": 4523,
    "avg_time_series_length": 185,
    "signal_quality_statistics": {
      "rsrp_range_dbm": [-38.2, -31.1],
      "rsrq_range_db": [-12.5, -8.2],
      "sinr_range_db": [8.3, 18.7]
    }
  },
  "validation_details": {
    "success_rate": 1.0,
    "checks_performed": 12,
    "checks_passed": 12
  },
  "satellites_sample": [
    {
      "satellite_id": "44713",
      "name": "STARLINK-1007",
      "sample_signal_quality": {
        "rsrp_dbm": -35.2,
        "rsrq_db": -10.5,
        "sinr_db": 12.3,
        "a3_offset": {
          "offset_mo_db": 5.6,
          "cell_offset_db": 0.0
        }
      }
    }
    // ... 更多樣本
  ],
  "next_stage_ready": true
}
```

---

## 驗證統計與監控

### 執行統計輸出

```
📊 執行統計:
   執行時間: 2314.52 秒
   完成階段: 6/6
   最終狀態: ✅ 成功
   訊息: 所有階段成功完成
```

### 驗證成功輸出

```
🔍 階段1立即驗證檢查...
----------------------------------------
✅ 驗證快照已保存
✅ 階段1完成並驗證通過: Stage 1 數據完整性檢查通過
```

### 驗證失敗輸出

```
🔍 階段5立即驗證檢查...
----------------------------------------
❌ 階段5驗證失敗: ❌ RSRP 範圍異常: -44.0 dBm (所有衛星相同值)
❌ 階段5驗證失敗: ❌ RSRP 範圍異常: -44.0 dBm (所有衛星相同值)

📊 執行統計:
   執行時間: 1234.56 秒
   完成階段: 5/6
   最終狀態: ❌ 失敗
   訊息: 階段5驗證失敗: ❌ RSRP 範圍異常: -44.0 dBm (所有衛星相同值)
```

---

## 最佳實踐

### 1. 信任 Layer 1 結果

Layer 2 驗證器**不應該**重複 Layer 1 的詳細驗證邏輯，應該信任處理器的內建驗證結果。

**錯誤示範** ❌:
```python
# 在 Layer 2 重複驗證軌道週期計算
for sat in satellites_sample:
    period = calculate_orbital_period(sat)  # 重複計算
    if not (90 <= period <= 95):
        return False, "軌道週期錯誤"
```

**正確示範** ✅:
```python
# Layer 2 只檢查統計特性
avg_period = snapshot_data['constellation_summary']['starlink']['avg_period_min']
if not (90 <= avg_period <= 95):
    return False, f"❌ Starlink 平均軌道週期異常: {avg_period} min"
```

### 2. 使用抽樣檢查

對於大量數據，使用抽樣檢查代替全量驗證。

```python
# 檢查前 20 顆衛星（系統性錯誤檢測）
satellites_sample = snapshot_data.get('satellites_sample', [])
for i, sat in enumerate(satellites_sample[:20], start=1):
    # 驗證邏輯
```

### 3. 明確錯誤信息

驗證失敗時，提供清晰、可操作的錯誤信息。

```python
# ❌ 不明確
return False, "數據錯誤"

# ✅ 明確
return False, f"❌ Stage 1 TLE 格式錯誤: 第{i}顆衛星 Line1 長度 {len(tle_line1)} ≠ 69"
```

### 4. 文檔化閾值依據

所有閾值應該有明確的學術或工程依據。

```python
# 檢查 Epoch 多樣性（至少 5 個不同的 epoch）
#
# 閾值依據（基於真實數據分析）：
# 目的：檢測是否所有TLE來自同一時間點（系統性時間基準錯誤）
# 真實數據特性（2025-09-30實測）：
#   - 20顆樣本中有 17 個 unique epochs（85% 多樣性）
#   - Space-Track.org 每日更新，不同衛星有不同epoch是正常的
# 閾值選擇：5 個（25% 多樣性）
#   - 對應統計學 P10 分位數（保守估計）
unique_epochs = len(set(epoch_times))
min_unique_epochs = 5

if unique_epochs < min_unique_epochs:
    return False, f"❌ Epoch 多樣性不足（{unique_epochs}/20，應≥{min_unique_epochs}）"
```

---

## 總結

### 驗證系統優勢

1. **Fail-Fast**: 問題發生時立即停止，節省計算資源
2. **模塊化**: 6 個獨立驗證器，易於維護和擴展
3. **雙層驗證**: Layer 1 詳細驗證 + Layer 2 快照檢查，確保數據品質
4. **學術合規性**: 所有驗證基於 ITU-R, 3GPP, NASA JPL 標準
5. **可追溯性**: 驗證快照保存完整數據，便於問題追蹤

### 驗證覆蓋率

- **Stage 1**: 15 項檢查（數據完整性、時間基準、TLE 格式、Epoch 多樣性）
- **Stage 2**: 12 項檢查（衛星數量、時間序列、軌道週期、TEME 座標）
- **Stage 3**: 10 項檢查（座標系統、地理座標範圍、仰角方位角）
- **Stage 4**: 8 項檢查（可見衛星、池優化、服務窗口、星座配置）
- **Stage 5**: 12 項檢查（信號品質範圍、A3 offset、ITU-R 模型）
- **Stage 6**: 6 項檢查（事件數量、換手決策、研究數據結構）

**總計**: 63 項驗證檢查，確保系統從數據載入到研究數據生成的全流程品質。

---

**文檔版本**: v1.0
**創建日期**: 2025-10-10
