# 六階段詳細實現

本文檔詳細說明每個階段的執行器、處理器、配置和依賴關係。

---

## Stage 1: TLE 數據載入層

### 核心文件

```
scripts/stage_executors/stage1_executor.py (74 行)
src/stages/stage1_orbital_calculation/stage1_main_processor.py
scripts/stage_validators/stage1_validator.py (190 行)
```

### 執行器實現

**文件**: `scripts/stage_executors/stage1_executor.py`

**關鍵函數**: `execute_stage1(previous_results=None)`

**執行流程**:

```python
def execute_stage1(previous_results=None):
    # 1. 清理舊輸出
    clean_stage_outputs(1)

    # 2. 檢查是否為取樣模式
    use_sampling = is_sampling_mode()  # 讀取 ORBIT_ENGINE_SAMPLING_MODE

    # 3. 配置 Stage 1
    config = {
        'sample_mode': use_sampling,
        'sample_size': 50,
        'epoch_analysis': {
            'enabled': True  # 啟用 epoch 動態分析
        },
        'epoch_filter': {
            'enabled': True,           # 啟用 epoch 篩選
            'mode': 'latest_date',     # 篩選模式：保留最新日期衛星
            'tolerance_hours': 24      # 容差範圍：± 24 小時
        }
    }

    # 4. 創建處理器
    from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor
    stage1_processor = create_stage1_processor(config)

    # 5. 執行處理
    stage1_result = stage1_processor.execute()

    # 6. 返回結果
    return True, stage1_result, stage1_processor
```

### 處理器實現

**文件**: `src/stages/stage1_orbital_calculation/stage1_main_processor.py`

**主要功能**:
- 讀取 TLE 文件 (`data/tle_data/*.tle`)
- 解析 Starlink 和 OneWeb 衛星數據
- Epoch 動態分析（找出最新日期，容差 ±24 小時）
- TLE 格式驗證（NORAD 標準 69 字符）
- 星座配置生成 (`constellation_configs`)

**關鍵方法**:
- `execute()`: 主執行流程
- `save_validation_snapshot()`: 保存驗證快照
- `run_validation_checks()`: 內建驗證

### 配置文件

**隱式配置** (寫在執行器內部):
- `sample_mode`: 取樣模式開關
- `epoch_filter.mode`: `'latest_date'` (保留最新日期衛星)
- `epoch_filter.tolerance_hours`: 24 小時

### 輸出文件

```
data/outputs/stage1/stage1_output_YYYYMMDD_HHMMSS.json
data/validation_snapshots/stage1_validation.json
```

### 輸出結構

```json
{
  "satellites": [
    {
      "name": "STARLINK-1007",
      "norad_id": 44713,
      "tle_line1": "1 44713U 19074A   ...",
      "tle_line2": "2 44713  53.0534 ...",
      "epoch_datetime": "2025-10-05T12:34:56.789012Z",
      "constellation": "starlink"
    }
  ],
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
}
```

### 驗證器實現

**文件**: `scripts/stage_validators/stage1_validator.py`

**檢查項目**:
1. 數據完整性 (衛星數量 ≥ 95% 期望值)
2. 時間基準合規性 (禁止統一時間基準字段)
3. 配置完整性 (`constellation_configs`, `research_configuration`)
4. TLE 格式品質 (抽樣檢查 20 顆衛星)
5. Epoch 多樣性 (至少 5 個不同 epoch)

**關鍵邏輯**:

```python
# 防禦性檢查 - 確保不存在統一時間基準字段
forbidden_time_fields = ['calculation_base_time', 'primary_epoch_time', 'unified_time_base']
for field in forbidden_time_fields:
    if field in metadata:
        return False, f"❌ 學術標準違規: 檢測到禁止字段 '{field}'"

# 檢查 TLE 格式
for sat in satellites_sample[:20]:
    tle_line1 = sat.get('tle_line1', '')
    if len(tle_line1) != 69:
        return False, f"❌ TLE 格式錯誤: Line1 長度 {len(tle_line1)} ≠ 69"

# 檢查 Epoch 多樣性
unique_epochs = len(set(epoch_times))
if unique_epochs < 5:
    return False, f"❌ Epoch 多樣性不足（{unique_epochs}/20，應≥5）"
```

### 依賴關係

- **輸入依賴**: TLE 文件 (`data/tle_data/*.tle`)
- **輸出依賴**: Stage 2 需要此階段的衛星數據和星座配置

---

## Stage 2: 軌道狀態傳播層

### 核心文件

```
scripts/stage_executors/stage2_executor.py (84 行)
src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py
config/stage2_orbital_computing.yaml
scripts/stage_validators/stage2_validator.py
```

### 執行器實現

**文件**: `scripts/stage_executors/stage2_executor.py`

**關鍵函數**: `execute_stage2(previous_results)`

**執行流程**:

```python
def execute_stage2(previous_results):
    # 1. 檢查前序階段
    if 'stage1' not in previous_results:
        return False, None, None

    # 2. 清理舊輸出
    clean_stage_outputs(2)

    # 3. 載入配置文件
    config_path = project_root / "config/stage2_orbital_computing.yaml"
    config_dict = load_stage2_config(str(config_path))

    # 4. 創建處理器
    from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
    stage2 = Stage2OrbitalPropagationProcessor(config=config_dict)

    # 5. 提取 Stage 1 數據
    stage1_data = extract_data_from_result(previous_results['stage1'])

    # 6. 執行處理
    stage2_result = stage2.execute(stage1_data)

    return True, stage2_result, stage2
```

### 處理器實現

**文件**: `src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py`

**主要功能**:
- SGP4 軌道傳播（使用 Skyfield 庫）
- 時間序列生成（1-2 個軌道週期）
- TEME 座標計算 (x, y, z, vx, vy, vz)
- 並行處理（30 個工作進程）
- HDF5 輸出（高效存儲 1.7M 數據點）

**關鍵方法**:
- `execute(stage1_data)`: 主執行流程
- `_propagate_satellite()`: 單顆衛星傳播
- `_calculate_orbital_period()`: 計算軌道週期

### 配置文件

**文件**: `config/stage2_orbital_computing.yaml`

```yaml
time_series_config:
  time_step_seconds: 60        # 時間步長 (1分鐘)
  coverage_orbital_periods: 2  # 覆蓋 2 個軌道週期

propagation_config:
  coordinate_system: TEME      # True Equator Mean Equinox
  sgp4_library: skyfield       # 使用 Skyfield 實現 SGP4
  ephemeris_file: de421.bsp    # NASA JPL DE421 星曆表

performance_config:
  max_workers: 30              # 並行工作進程數
  chunk_size: 100              # 批次大小
```

### 輸出文件

```
data/outputs/stage2/orbital_propagation_output_YYYYMMDD_HHMMSS.json (元數據)
data/outputs/stage2/orbital_propagation_output_YYYYMMDD_HHMMSS.h5 (TEME 座標數據)
data/validation_snapshots/stage2_validation.json
```

### 輸出結構

**JSON 文件** (元數據):

```json
{
  "metadata": {
    "total_satellites": 9015,
    "time_series_length": 190,
    "constellation_summary": {
      "starlink": {"count": 6654, "avg_period_min": 95.2},
      "oneweb": {"count": 2361, "avg_period_min": 112.5}
    }
  },
  "satellites": {
    "44713": {
      "name": "STARLINK-1007",
      "orbital_period_seconds": 5712.3,
      "h5_dataset_path": "/satellites/44713"
    }
  }
}
```

**HDF5 文件** (TEME 座標):

```
/satellites/44713/teme_positions    # shape: (190, 3) - [x, y, z] in km
/satellites/44713/teme_velocities   # shape: (190, 3) - [vx, vy, vz] in km/s
/satellites/44713/timestamps        # shape: (190,) - UTC timestamps
```

### 驗證器實現

**文件**: `scripts/stage_validators/stage2_validator.py`

**檢查項目**:
1. 衛星數量一致性 (與 Stage 1 匹配)
2. 時間序列長度合理性 (≥ 180 點)
3. 軌道週期正確性 (Starlink: 90-95 min, OneWeb: 109-115 min)
4. HDF5 文件存在性
5. TEME 座標範圍合理性 (距離 550-1200 km)

### 依賴關係

- **輸入依賴**: Stage 1 的衛星數據和 TLE
- **輸出依賴**: Stage 3 需要 TEME 座標數據

---

## Stage 3: 座標系統轉換層

### 核心文件

```
scripts/stage_executors/stage3_executor.py (83 行)
src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py
scripts/stage_validators/stage3_validator.py
```

### 執行器實現

**文件**: `scripts/stage_executors/stage3_executor.py`

**關鍵函數**: `execute_stage3(previous_results)`

**執行流程**:

```python
def execute_stage3(previous_results):
    # 1. 檢查前序階段
    if 'stage2' not in previous_results:
        return False, None, None

    # 2. 清理舊輸出
    clean_stage_outputs(3)

    # 3. 配置 Stage 3
    stage3_config = {
        'enable_geometric_prefilter': False,  # v3.1: 禁用預篩選
        'coordinate_config': {
            'source_frame': 'TEME',
            'target_frame': 'WGS84',
            'time_corrections': True,
            'polar_motion': True,
            'nutation_model': 'IAU2000A'
        },
        'precision_config': {
            'target_accuracy_m': 0.5  # 亞米級精度
        }
    }

    # 4. 創建處理器
    from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
    stage3 = Stage3CoordinateTransformProcessor(config=stage3_config)

    # 5. 提取 Stage 2 數據
    stage2_data = extract_data_from_result(previous_results['stage2'])

    # 6. 執行處理
    stage3_result = stage3.execute(stage2_data)

    return True, stage3_result, stage3
```

### 處理器實現

**文件**: `src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py`

**主要功能**:
- TEME → ECEF → Geodetic WGS84 座標轉換
- IAU 2000A 歲差章動模型
- IERS 地球定向參數修正
- 極移修正 (Polar Motion)
- 並行處理（30 個工作進程）
- HDF5 緩存機制（首次 ~25min，緩存後 ~2min）

**關鍵方法**:
- `execute(stage2_data)`: 主執行流程
- `_transform_coordinates()`: 座標轉換核心邏輯
- `_cache_to_hdf5()`: HDF5 緩存保存

### 配置文件

**隱式配置** (寫在執行器內部):
- `enable_geometric_prefilter`: `False` (v3.1 已禁用)
- `coordinate_config.nutation_model`: `'IAU2000A'` (國際天文聯合會標準)
- `precision_config.target_accuracy_m`: `0.5` (亞米級精度)

### 輸出文件

```
data/outputs/stage3/stage3_coordinate_transformation_real_YYYYMMDD_HHMMSS.json
data/validation_snapshots/stage3_validation.json
data/cache/stage3/*.h5 (緩存文件, ~154MB)
```

### 輸出結構

```json
{
  "metadata": {
    "total_satellites": 9015,
    "coordinate_system": "WGS84",
    "time_series_length": 190
  },
  "geographic_coordinates": {
    "44713": {
      "name": "STARLINK-1007",
      "time_series": [
        {
          "timestamp": "2025-10-05T12:34:56.789012Z",
          "latitude_deg": 24.5,
          "longitude_deg": 121.2,
          "altitude_m": 551234.5,
          "azimuth_deg": 145.3,
          "elevation_deg": 35.2,
          "slant_range_km": 1423.5
        }
      ]
    }
  }
}
```

### 驗證器實現

**文件**: `scripts/stage_validators/stage3_validator.py`

**檢查項目**:
1. 衛星數量一致性 (與 Stage 2 匹配)
2. 座標系統正確性 (WGS84)
3. 地理座標範圍合理性 (緯度 ±90°, 經度 ±180°)
4. 高度範圍合理性 (550-1200 km)
5. 時間序列完整性

### 依賴關係

- **輸入依賴**: Stage 2 的 TEME 座標數據
- **輸出依賴**: Stage 4 需要 WGS84 地理座標和仰角數據

---

## Stage 4: 鏈路可行性評估層

### 核心文件

```
scripts/stage_executors/stage4_executor.py (78 行)
src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py
config/stage4_link_feasibility_config.yaml
scripts/stage_validators/stage4_validator.py
```

### 執行器實現

**文件**: `scripts/stage_executors/stage4_executor.py`

**關鍵函數**: `execute_stage4(previous_results)`

**執行流程**:

```python
def execute_stage4(previous_results):
    # 1. 清理舊輸出
    clean_stage_outputs(4)

    # 2. 尋找 Stage 3 輸出 (支持單一階段執行)
    stage3_output = find_latest_stage_output(3)
    if not stage3_output:
        return False, None, None

    # 3. 載入 Stage 4 配置
    stage4_config_path = project_root / "config/stage4_link_feasibility_config.yaml"
    with open(stage4_config_path, 'r', encoding='utf-8') as f:
        stage4_config = yaml.safe_load(f)

    # 4. 創建處理器
    from stages.stage4_link_feasibility.stage4_link_feasibility_processor import Stage4LinkFeasibilityProcessor
    processor = Stage4LinkFeasibilityProcessor(stage4_config)

    # 5. 載入前階段數據
    with open(stage3_output, 'r') as f:
        stage3_data = json.load(f)

    # 6. 執行處理
    result = processor.process(stage3_data)

    return True, result, processor
```

### 處理器實現

**文件**: `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`

**主要功能**:
- 可見性判斷（仰角門檻篩選）
- 動態衛星池優化（Pool Optimization）
- 服務窗口分析（Service Windows）
- 3GPP NTN 換手準備（Handover Preparation）
- 配置合併（Stage 4 本地配置 + Stage 1 上游配置）

**關鍵方法**:
- `process(stage3_data)`: 主執行流程
- `_optimize_satellite_pools()`: 動態池優化
- `_calculate_service_windows()`: 服務窗口計算

### 配置文件

**文件**: `config/stage4_link_feasibility_config.yaml`

```yaml
use_iau_standards: true
validate_epochs: false  # Stage 1 已完成 epoch 驗證

pool_optimization_targets:
  starlink:
    target_coverage_rate: 0.95        # 目標覆蓋率 95%
    min_pool_size: 10                 # 最小池大小
    max_pool_size: 15                 # 最大池大小
    elevation_threshold_deg: 5.0      # 仰角門檻 5°
  oneweb:
    target_coverage_rate: 0.90
    min_pool_size: 3
    max_pool_size: 6
    elevation_threshold_deg: 10.0     # 仰角門檻 10°

handover_preparation:
  enabled: true
  hysteresis_margin_deg: 2.0          # 遲滯餘量 2°
  time_to_trigger_seconds: 5          # 觸發時間 5 秒
```

### 輸出文件

```
data/outputs/stage4/stage4_link_analysis_YYYYMMDD_HHMMSS.json
data/validation_snapshots/stage4_validation.json
```

### 輸出結構

```json
{
  "metadata": {
    "visible_satellites_count": 4523,
    "pool_optimization_results": {
      "starlink": {
        "average_pool_size": 12.3,
        "coverage_rate": 0.96
      },
      "oneweb": {
        "average_pool_size": 4.5,
        "coverage_rate": 0.91
      }
    }
  },
  "link_feasibility": {
    "44713": {
      "name": "STARLINK-1007",
      "service_windows": [
        {
          "start_time": "2025-10-05T12:34:56Z",
          "end_time": "2025-10-05T12:45:12Z",
          "duration_seconds": 616,
          "max_elevation_deg": 45.2,
          "in_optimized_pool": true
        }
      ]
    }
  }
}
```

### 驗證器實現

**文件**: `scripts/stage_validators/stage4_validator.py`

**檢查項目**:
1. 可見衛星數量合理性 (≥ 40% 總數)
2. 池優化結果正確性 (覆蓋率達標)
3. 服務窗口完整性
4. 星座特定配置正確性 (Starlink 5°, OneWeb 10°)

### 依賴關係

- **輸入依賴**: Stage 3 的 WGS84 座標和仰角數據
- **輸出依賴**: Stage 5 需要可見衛星和服務窗口數據

---

## Stage 5: 信號品質分析層

### 核心文件

```
scripts/stage_executors/stage5_executor.py (154 行)
src/stages/stage5_signal_analysis/stage5_signal_analysis_processor.py
src/stages/stage5_signal_analysis/gpp_ts38214_signal_calculator.py
src/stages/stage5_signal_analysis/itur_official_atmospheric_model.py
config/stage5_signal_analysis_config.yaml
scripts/stage_validators/stage5_validator.py
```

### 執行器實現

**文件**: `scripts/stage_executors/stage5_executor.py`

**關鍵函數**: `execute_stage5(previous_results)`

**執行流程**:

```python
def execute_stage5(previous_results):
    print('📊 階段五：信號品質分析層 (Grade A+ 模式)')

    # 1. 清理舊輸出
    clean_stage_outputs(5)

    # 2. 載入 Stage 5 配置文件
    config = load_stage5_config()  # 從 config/stage5_signal_analysis_config.yaml 載入

    # 3. 驗證配置完整性
    valid, message = validate_stage5_config(config)
    if not valid:
        return False, None, None

    # 4. 尋找 Stage 4 輸出
    stage4_output = find_latest_stage_output(4)

    # 5. 創建處理器
    from stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor
    processor = Stage5SignalAnalysisProcessor(config)

    # 6. 載入前階段數據
    with open(stage4_output, 'r') as f:
        stage4_data = json.load(f)

    # 7. 執行處理
    result = processor.execute(stage4_data)

    return True, result, processor
```

### 處理器實現

**文件**: `src/stages/stage5_signal_analysis/stage5_signal_analysis_processor.py`

**主要功能**:
- RSRP/RSRQ/SINR 計算（3GPP TS 38.214）
- ITU-R 大氣衰減模型（P.676-13 官方實現）
- A3 offset 計算（3GPP TS 38.331 Section 5.5.4.4）
- 時間序列信號品質分析
- 並行處理（30 個工作進程）

**關鍵方法**:
- `execute(stage4_data)`: 主執行流程
- `_calculate_signal_quality()`: 信號品質計算

**依賴算法模塊**:

1. **3GPP TS 38.214 信號計算器**
   - 文件: `src/stages/stage5_signal_analysis/gpp_ts38214_signal_calculator.py`
   - RSRP: 參考信號接收功率 (dBm)
   - RSRQ: 參考信號接收品質 (dB)
   - SINR: 信號與干擾加噪聲比 (dB)

2. **ITU-R 官方大氣模型**
   - 文件: `src/stages/stage5_signal_analysis/itur_official_atmospheric_model.py`
   - 使用 `itur` Python 官方包裝
   - P.676-13: 大氣氣體衰減
   - P.618-13: 降雨衰減（未來實現）

### 配置文件

**文件**: `config/stage5_signal_analysis_config.yaml`

```yaml
signal_calculator:
  bandwidth_mhz: 100                # 頻寬 100 MHz
  subcarrier_spacing_khz: 30        # 子載波間隔 30 kHz
  noise_figure_db: 5.0              # 噪聲指數 5 dB
  temperature_k: 290                # 系統溫度 290 K

atmospheric_model:
  temperature_k: 288.15             # 溫度 15°C
  pressure_hpa: 1013.25             # 標準大氣壓
  water_vapor_density_g_m3: 7.5    # 水汽密度 7.5 g/m³

a3_event_config:
  offset_db: 3.0                    # A3 offset 3 dB
  hysteresis_db: 2.0                # 遲滯 2 dB
  time_to_trigger_ms: 640           # 觸發時間 640 ms
```

### 輸出文件

```
data/outputs/stage5/stage5_signal_analysis_YYYYMMDD_HHMMSS.json
data/validation_snapshots/stage5_validation.json
```

### 輸出結構

```json
{
  "metadata": {
    "total_analyzed_satellites": 4523,
    "signal_model": "3GPP TS 38.214",
    "atmospheric_model": "ITU-R P.676-13"
  },
  "signal_analysis": {
    "44713": {
      "name": "STARLINK-1007",
      "time_series": [
        {
          "timestamp": "2025-10-05T12:34:56Z",
          "signal_quality": {
            "rsrp_dbm": -85.2,          # 參考信號接收功率
            "rsrq_db": -10.5,           # 參考信號接收品質
            "sinr_db": 12.3             # 信噪比
          },
          "atmospheric_effects": {
            "attenuation_db": 0.12      # 大氣衰減
          },
          "a3_offset": {
            "offset_mo_db": 5.6,        # 測量偏移
            "cell_offset_db": 0.0       # 小區偏移
          }
        }
      ]
    }
  }
}
```

### 驗證器實現

**文件**: `scripts/stage_validators/stage5_validator.py`

**檢查項目**:
1. 衛星數量一致性 (與 Stage 4 匹配)
2. 信號品質範圍合理性 (RSRP: -140 ~ -30 dBm)
3. 時間序列完整性
4. A3 offset 存在性
5. ITU-R 模型參數正確性

### 依賴關係

- **輸入依賴**: Stage 4 的可見衛星和服務窗口數據
- **輸出依賴**: Stage 6 需要信號品質和 A3 offset 數據

---

## Stage 6: 研究數據生成層

### 核心文件

```
scripts/stage_executors/stage6_executor.py (62 行)
src/stages/stage6_research_optimization/stage6_research_optimization_processor.py
src/stages/stage6_research_optimization/gpp_event_detector.py
src/stages/stage6_research_optimization/handover_decision_evaluator.py
config/stage6_research_optimization_config.yaml
scripts/stage_validators/stage6_validator.py
```

### 執行器實現

**文件**: `scripts/stage_executors/stage6_executor.py`

**關鍵函數**: `execute_stage6(previous_results)`

**執行流程**:

```python
def execute_stage6(previous_results):
    print('💾 階段六：研究數據生成層')

    # 1. 清理舊輸出
    clean_stage_outputs(6)

    # 2. 尋找 Stage 5 輸出
    stage5_output = find_latest_stage_output(5)
    if not stage5_output:
        return False, None, None

    # 3. 創建處理器
    from stages.stage6_research_optimization.stage6_research_optimization_processor import Stage6ResearchOptimizationProcessor
    processor = Stage6ResearchOptimizationProcessor()

    # 4. 載入前階段數據
    with open(stage5_output, 'r') as f:
        stage5_data = json.load(f)

    # 5. 執行處理
    result = processor.execute(stage5_data)

    # 6. 保存驗證快照
    if hasattr(processor, 'save_validation_snapshot'):
        processor.save_validation_snapshot(result)

    return True, result, processor
```

### 處理器實現

**文件**: `src/stages/stage6_research_optimization/stage6_research_optimization_processor.py`

**主要功能**:
- 3GPP 換手事件檢測 (A3/A4/A5/D2)
- 換手決策評估
- 強化學習訓練數據生成
- 歷史數據重現分析

**關鍵方法**:
- `execute(stage5_data)`: 主執行流程
- `_detect_handover_events()`: 換手事件檢測
- `_evaluate_handover_decisions()`: 換手決策評估

**依賴算法模塊**:

1. **3GPP 事件檢測器**
   - 文件: `src/stages/stage6_research_optimization/gpp_event_detector.py`
   - A3: 鄰居信號優於服務衛星（相對偏移）
   - A4: 鄰居信號超過絕對門檻
   - A5: 服務信號劣化且鄰居良好
   - D2: 地面基站切換事件（未來實現）

2. **換手決策評估器**
   - 文件: `src/stages/stage6_research_optimization/handover_decision_evaluator.py`
   - 評估換手候選衛星
   - 計算決策質量指標
   - 歷史數據重現分析（非實時系統）

### 配置文件

**文件**: `config/stage6_research_optimization_config.yaml`

```yaml
event_detection:
  a3_offset_db: 3.0                 # A3 偏移門檻
  a4_threshold_dbm: -110            # A4 絕對門檻
  a5_threshold1_dbm: -110           # A5 服務門檻
  a5_threshold2_dbm: -95            # A5 鄰居門檻
  hysteresis_db: 2.0                # 遲滯
  time_to_trigger_ms: 640           # 觸發時間

handover_decision:
  evaluation_mode: "batch"          # 批次評估模式（非實時）
  enable_performance_metrics: false # 禁用性能監控（學術研究用）
  enable_adaptive_thresholds: false # 禁用自適應門檻（使用 3GPP 標準值）
```

### 輸出文件

```
data/outputs/stage6/stage6_research_YYYYMMDD_HHMMSS.json
data/validation_snapshots/stage6_validation.json
```

### 輸出結構

```json
{
  "metadata": {
    "total_events": {
      "a3_events": 1234,
      "a4_events": 567,
      "a5_events": 89,
      "d2_events": 0
    },
    "handover_evaluation": {
      "total_evaluated": 1234,
      "successful_rate": 0.92
    }
  },
  "handover_events": {
    "timestamp_group_0": {
      "timestamp": "2025-10-05T12:34:56Z",
      "serving_satellite": "44713",
      "event_type": "A3",
      "neighbor_candidates": [
        {
          "satellite_id": "44714",
          "rsrp_dbm": -82.3,
          "offset_from_serving_db": 5.6,
          "decision": "handover_recommended"
        }
      ]
    }
  },
  "research_data": {
    "state_action_pairs": [
      {
        "state": {
          "serving_rsrp": -85.2,
          "neighbor_rsrp": -82.3,
          "elevation": 35.2
        },
        "action": "handover",
        "reward": 0.85
      }
    ]
  }
}
```

### 驗證器實現

**文件**: `scripts/stage_validators/stage6_validator.py`

**檢查項目**:
1. 事件數量合理性 (A3 events > 0)
2. 換手決策完整性
3. 研究數據結構正確性
4. 3GPP 標準合規性

### 依賴關係

- **輸入依賴**: Stage 5 的信號品質和 A3 offset 數據
- **輸出依賴**: 最終輸出，供研究分析使用

---

## 共用工具模塊

### executor_utils.py

**文件**: `scripts/stage_executors/executor_utils.py`

**提供函數**:

1. **`project_root`**: 項目根目錄路徑
   ```python
   project_root = Path(__file__).parent.parent.parent
   ```

2. **`extract_data_from_result(result)`**: 從 ProcessingResult 提取數據
   ```python
   if hasattr(result, "data"):
       return result.data
   else:
       return result
   ```

3. **`is_sampling_mode()`**: 檢測是否為取樣模式
   ```python
   use_sampling = os.getenv('ORBIT_ENGINE_SAMPLING_MODE', 'auto')
   if use_sampling == 'auto':
       return os.getenv('ORBIT_ENGINE_TEST_MODE') == '1'
   ```

4. **`clean_stage_outputs(stage_number)`**: 清理階段輸出
   ```python
   output_dir = Path(f'data/outputs/stage{stage_number}')
   # 刪除所有文件
   ```

5. **`find_latest_stage_output(stage_number)`**: 找到最新輸出文件
   ```python
   json_files = list(output_dir.glob('*.json'))
   return max(json_files, key=lambda p: p.stat().st_mtime)
   ```

---

## 階段依賴關係總結

```
TLE 文件 (data/tle_data/*.tle)
  ↓
Stage 1: 載入並解析 TLE
  ↓ (衛星數據 + 星座配置)
Stage 2: SGP4 軌道傳播
  ↓ (TEME 座標)
Stage 3: 座標系統轉換
  ↓ (WGS84 座標 + 仰角)
Stage 4: 鏈路可行性評估
  ↓ (可見衛星 + 服務窗口)
Stage 5: 信號品質分析
  ↓ (RSRP/RSRQ + A3 offset)
Stage 6: 研究數據生成
  ↓
換手事件 + RL 訓練數據
```

---

**文檔版本**: v1.0
**創建日期**: 2025-10-10
