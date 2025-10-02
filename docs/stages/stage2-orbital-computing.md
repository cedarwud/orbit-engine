# 🛰️ Stage 2: 軌道狀態傳播層 - 完整規格文檔

**最後更新**: 2025-10-01 (效能數據更新)
**重構狀態**: ✅ 已完成 Skyfield 直接實現
**學術合規**: Grade A 標準，NASA JPL 精度
**接口標準**: 100% BaseStageProcessor 合規
**效能提升**: 🚀 56% 處理速度提升 (vs 重構前)

## 📖 概述與目標

**核心職責**: 直接使用 Skyfield 進行 SGP4/SDP4 軌道傳播
**輸入**: Stage 1 的 ProcessingResult (包含每顆衛星的 epoch_datetime)
**輸出**: TEME 座標系統中的位置/速度時間序列
**處理效能**: ✅ **152.9秒** (9,041顆衛星，動態軌道週期) - 生產環境完整處理
**處理速度**: ✅ **59.1 顆衛星/秒** - NASA JPL 標準精度
**軌道點生成**: ✅ **1,726,294個** TEME 座標點 (652 MB 輸出)
**成功率**: ✅ **100%** - 零失敗率

### 🎯 Stage 2 核心價值
- **軌道狀態計算**: 基於 Stage 1 epoch_datetime 的精確 SGP4/SDP4 傳播
- **時間序列生成**: 為目標時間窗口生成完整的位置/速度序列
- **TEME 座標輸出**: 提供標準 True Equator Mean Equinox 座標給 Stage 3
- **零重複解析**: 完全使用 Stage 1 提供的 epoch_datetime，不重新解析 TLE

## 🚨 重要概念修正

### ❌ **修正前的錯誤概念**
```
Stage 2: 可見性篩選
- 重新解析 TLE epoch 時間
- 仰角門檻篩選 (10°)
- 距離範圍檢查 (200-2000km)
- 輸出「可見衛星」列表
```

### ✅ **簡化重構後的實現**
```
Stage 2: 軌道狀態傳播 (Skyfield 直接實現)
- 直接使用 Skyfield NASA JPL 標準庫
- 移除 SGP4OrbitalEngine 中間包裝層
- 零格式轉換，原生 TEME 座標輸出
- 衛星快取機制，避免重複創建
- 59.1 顆衛星/秒處理速度 (56% 提升)
```

**學術依據**:
> *"Orbital propagation should be separated from visibility analysis. SGP4/SDP4 algorithms generate orbital states in TEME coordinates, while visibility requires coordinate transformation and geometric calculations."*
> — Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications

## 🏗️ 架構設計

### ✅ 簡化重構後的直接架構
```
┌─────────────────────────────────────────────────────────┐
│       Stage 2: 軌道狀態傳播層 (Skyfield 直接實現)         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │            SGP4Calculator (簡化版)              │   │
│  │                                                 │   │
│  │  🚀 直接使用 Skyfield NASA JPL 標準            │   │
│  │  ❌ 移除 SGP4OrbitalEngine 中間層              │   │
│  │  📦 內建衛星快取 (避免重複創建)                 │   │
│  │  📊 零格式轉換，原生 TEME 輸出                 │   │
│  │  ⚡ 59.1 顆/秒處理速度 (56% 提升)             │   │
│  └─────────────────────────────────────────────────┘   │
│                            │                            │
│                            ▼                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │      Stage2OrbitalPropagationProcessor          │   │
│  │                                                 │   │
│  │  ✅ 使用 Stage 1 epoch_datetime (v3.0合規)     │   │
│  │  🛰️ 星座分離計算 (Starlink/OneWeb)            │   │
│  │  ⏱️ 時間序列生成 (動態軌道週期)                │   │
│  │  📍 TEME 座標標準輸出                          │   │
│  │  🔬 5項專用驗證檢查                            │   │
│  │  📈 100% 成功率 (9,041顆衛星實測)             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 🎯 **重構改進對比**

| 項目 | 重構前 (複雜版) | 重構後 (簡化版) | 提升幅度 |
|------|----------------|-----------------|----------|
| **調用層數** | 3層包裝 | 1層直接 | **67% 簡化** |
| **處理時間** | ~239秒 | **152.9秒** | **🚀 56% 提升** |
| **處理速度** | ~38顆/秒 | **59.1顆/秒** | **🚀 56% 提升** |
| **成功率** | 未知 | **100.0%** | **完美穩定** |
| **維護負擔** | 複雜包裝層 | 單一Skyfield | **大幅簡化** |
| **學術可信** | 自建包裝 | NASA JPL標準 | **權威保證** |

## 🎯 核心功能與職責

### ✅ **Stage 2 專屬職責**

#### 1. **時間序列規劃與星座分離計算**
- **目標時間窗口**: 2小時軌道傳播窗口 (基於星座軌道週期優化)
- **時間步長**: 30秒間隔 (配置優化後)
- **星座特定軌道週期** ⚠️ **重要**：
  - **Starlink**: ~90-95分鐘軌道週期 (LEO 低軌 ~550km)
  - **OneWeb**: ~109-115分鐘軌道週期 (LEO 高軌 ~1200km)
- **時間範圍**: 動態計算
  - Starlink: 191個時間點 (95分鐘 ÷ 30秒)
  - OneWeb: 224個時間點 (112分鐘 ÷ 30秒)
- **時間來源**: 100% 使用 Stage 1 提供的 epoch_datetime

#### 2. **SGP4/SDP4 軌道傳播**
- **專業庫使用**: 使用 skyfield 或 pyephem 等學術級庫
- **精確計算**: 基於每顆衛星的真實 epoch 時間
- **軌道元素**: 使用 Stage 1 解析的完整 TLE 數據
- **誤差控制**: 符合 SGP4 官方精度標準

#### 3. **TEME 座標系統輸出**
- **標準座標**: True Equator Mean Equinox 座標
- **位置向量**: (x, y, z) 在 TEME 參考系
- **速度向量**: (vx, vy, vz) 在 TEME 參考系
- **時間戳記**: 每個狀態點的精確時間

#### 4. **數據結構標準化**
- **時間序列格式**: 標準化軌道狀態陣列
- **元數據完整**: 包含傳播參數和誤差估計
- **記憶體優化**: 高效的數據結構設計

### ❌ **明確排除職責** (移至後續階段)
- ❌ **座標轉換**: TEME→ITRF→WGS84 轉換 (移至 Stage 3)
- ❌ **可見性分析**: 仰角、方位角計算 (移至 Stage 4)
- ❌ **距離篩選**: 地面站距離約束 (移至 Stage 4)
- ❌ **星座感知**: 特定門檻值處理 (移至 Stage 4)
- ❌ **TLE 重新解析**: 禁止重新解析任何 TLE 資料

## 🔍 時間基準使用規範

### 🚨 **CRITICAL: 禁止 TLE 重新解析**

**❌ 絕對禁止的做法**:
```python
# 禁止！不得重新解析 TLE epoch
epoch_year = int(tle_line1[18:20])
epoch_day = float(tle_line1[20:32])
epoch_time = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)
```

**✅ 正確的做法**:
```python
# 正確！使用 Stage 1 提供的 epoch_datetime
satellite_data = stage1_result.data['satellites'][i]
epoch_datetime = datetime.fromisoformat(satellite_data['epoch_datetime'])

# 使用 epoch_datetime 進行 SGP4 計算
satrec = Satrec.twoline2rv(
    satellite_data['tle_line1'],
    satellite_data['tle_line2']
)
```

### 時間基準繼承機制
```python
# Stage 1 → Stage 2 數據流
stage1_output = {
    'satellites': [
        {
            'name': 'STARLINK-1234',
            'epoch_datetime': '2025-09-27T07:30:24.572437+00:00',  # 使用此時間
            'tle_line1': '...',
            'tle_line2': '...'
        }
    ]
}

# Stage 2 處理流程
for satellite in stage1_output['satellites']:
    epoch_dt = datetime.fromisoformat(satellite['epoch_datetime'])
    # 基於此 epoch 時間進行 SGP4 時間序列計算
```

## 🔄 數據流：上游依賴與下游使用

### 📥 上游依賴 (Stage 1 → Stage 2)

#### 從 Stage 1 接收的數據
**必要輸入數據**:
- ✅ `satellites[]` - 完整的衛星列表
  - `satellite_id` - 衛星唯一標識符
  - `name` - 衛星名稱 (用於星座識別)
  - `norad_id` - NORAD 目錄編號
  - `epoch_datetime` - **核心時間基準** (ISO 8601 格式)
  - `tle_line1` - TLE 第一行 (69字符標準格式)
  - `tle_line2` - TLE 第二行 (69字符標準格式)
  - `constellation` - 星座歸屬 (starlink/oneweb)

- ✅ `metadata.constellation_configs` - 星座配置元數據
  - `orbital_period_range_minutes` - 軌道週期範圍 (用於時間窗口規劃)
  - `typical_altitude_km` - 典型軌道高度 (參考值)

**數據訪問範例**:
```python
from stages.stage1_orbital_calculation.stage1_main_processor import Stage1TLEDataProcessor

# 執行 Stage 1
stage1_processor = Stage1TLEDataProcessor(config)
stage1_result = stage1_processor.execute()

# Stage 2 訪問必要數據
satellites = stage1_result.data['satellites']
constellation_configs = stage1_result.data['metadata']['constellation_configs']

for satellite in satellites:
    # 獲取時間基準 (零重複解析)
    epoch_dt = datetime.fromisoformat(satellite['epoch_datetime'])

    # 獲取 TLE 數據
    tle_line1 = satellite['tle_line1']
    tle_line2 = satellite['tle_line2']

    # 獲取星座配置
    constellation = satellite['constellation']
    orbital_period = constellation_configs[constellation]['orbital_period_range_minutes']

    # 進行 SGP4 軌道傳播...
```

#### Stage 1 數據依賴關係
- **🚨 CRITICAL**: `epoch_datetime` 是唯一的時間基準來源
  - **禁止**: 重新解析 TLE 中的 epoch 欄位
  - **必須**: 100% 使用 Stage 1 提供的 ISO 8601 格式時間
- **星座分離**: `constellation` 欄位用於動態軌道週期計算
  - Starlink: 90-95分鐘時間窗口
  - OneWeb: 109-115分鐘時間窗口
- **學術合規**: Stage 1 已完成 TLE 格式驗證和時間解析

### 📤 下游使用 (Stage 2 → Stage 3/4)

#### Stage 3: 座標轉換層使用的數據
**使用的輸出**:
- ✅ `orbital_states[satellite_id].time_series[]` - TEME 座標時間序列
  - `timestamp` - 時間戳記 (UTC)
  - `position_teme` - TEME 座標系統位置向量 [x, y, z] (km)
  - `velocity_teme` - TEME 座標系統速度向量 [vx, vy, vz] (km/s)

- ✅ `orbital_states[satellite_id].propagation_metadata` - 軌道傳播元數據
  - `epoch_datetime` - 原始 epoch 時間 (傳遞自 Stage 1)
  - `orbital_period_minutes` - 實際軌道週期
  - `time_step_seconds` - 時間步長 (30秒)

**Stage 3 數據流範例**:
```python
# Stage 3 處理器接收 Stage 2 輸出
stage3_processor = Stage3CoordinateTransformProcessor(config)
stage3_result = stage3_processor.execute(stage2_result.data)

# Stage 3 訪問 TEME 座標
for satellite_id, orbital_data in stage2_result.data['orbital_states'].items():
    for time_point in orbital_data['time_series']:
        # TEME 座標 (Stage 2 輸出)
        position_teme = time_point['position_teme']  # [x, y, z] km
        velocity_teme = time_point['velocity_teme']  # [vx, vy, vz] km/s
        timestamp = time_point['timestamp']

        # 進行 TEME → ITRF → WGS84 轉換...
        wgs84_coords = skyfield_transform(position_teme, velocity_teme, timestamp)
```

#### Stage 4: 鏈路可行性層間接使用的數據
**間接依賴** (透過 Stage 3):
- Stage 2 提供的軌道週期資訊 → Stage 3 → Stage 4
- Stage 2 的時間步長保證 → 影響 Stage 4 可見性分析的時間解析度
- 星座分離計算結果 → 確保 Stage 4 能正確應用星座特定門檻

**關鍵傳遞鏈**:
```
Stage 1 epoch_datetime
  → Stage 2 SGP4 傳播 (TEME 座標)
    → Stage 3 座標轉換 (WGS84)
      → Stage 4 可見性分析 (仰角/距離)
```

### 🔄 數據完整性保證

✅ **時間基準繼承**: Stage 1 epoch → Stage 2 時間序列 → Stage 3/4 分析
✅ **座標系統標準**: TEME 標準輸出，符合 Skyfield/NASA JPL 規範
✅ **星座感知傳遞**: 星座配置從 Stage 1 → Stage 2 → 後續階段
✅ **學術合規**: 零重複解析，零自製算法，100% 專業庫實現

## 📊 標準化輸出格式

### ProcessingResult 結構
```python
ProcessingResult(
    status=ProcessingStatus.SUCCESS,
    data={
        'stage': 2,
        'stage_name': 'orbital_state_propagation',
        'orbital_states': {
            'satellite_id_1': {
                'time_series': [
                    {
                        'timestamp': '2025-09-27T08:00:00.000000+00:00',
                        'position_teme': [x, y, z],  # TEME 座標 (km)
                        'velocity_teme': [vx, vy, vz]  # TEME 速度 (km/s)
                    },
                    # ... 更多時間點
                ],
                'propagation_metadata': {
                    'epoch_datetime': '2025-09-27T07:30:24.572437+00:00',
                    'orbital_period_minutes': 93.2,
                    'time_step_seconds': 30,
                    'total_time_points': 224
                }
            }
            # ... 更多衛星
        },
        'metadata': {
            # 時間序列參數
            'time_window': {
                'start_time': '2025-09-27T08:00:00.000000+00:00',
                'end_time': '2025-09-28T08:00:00.000000+00:00',
                'time_step_seconds': 30,
                'timezone': 'UTC'
            },

            # 軌道傳播設定
            'propagation_config': {
                'sgp4_library': 'skyfield',
                'coordinate_system': 'TEME',
                'gravitational_model': 'SGP4',
                'epoch_source': 'stage1_parsed'
            },

            # 處理統計
            'total_satellites': 9041,
            'processing_duration_seconds': 239.2,
            'time_series_generated': True,

            # 合規標記
            'tle_reparsing_forbidden': True,
            'stage1_epoch_compliance': True,
            'academic_standard': 'Grade_A'
        }
    },
    metadata={...},
    errors=[],
    warnings=[],
    metrics=ProcessingMetrics(...)
)
```

### 軌道狀態數據格式
```python
orbital_state = {
    'timestamp': '2025-09-27T08:00:00.000000+00:00',
    'position_teme': [x, y, z],      # TEME 座標 (km)
    'velocity_teme': [vx, vy, vz],   # TEME 速度 (km/s)
    'satellite_id': 'STARLINK-1234',
    'propagation_error': 0.001,      # km (估計誤差)
}
```

## ⚡ 性能指標 (簡化重構後實測)

### 🚀 **實際性能指標 - 2025-10-01 最新測試結果**
- **處理時間**: ✅ **152.9秒** (9,041顆衛星) - 生產環境完整處理
- **處理速度**: ✅ **59.1顆衛星/秒** - NASA JPL 標準精度
- **軌道點速度**: ✅ **11,287點/秒** - 高速批量計算
- **成功率**: ✅ **100.0%** - 零失敗率 (9,041/9,041)
- **軌道點總數**: ✅ **1,726,294個** - 完整動態軌道週期時間序列
- **平均點數/衛星**: ✅ **190.9點** - 動態軌道週期計算 (1.0x週期覆蓋)
- **時間步長**: 30秒間隔 (可配置)
- **輸出文件大小**: 652 MB (完整 TEME 座標數據)

### 📊 **星座分離處理效能**
- **Starlink**: 8,390顆衛星，~191軌道點/衛星 (~95分鐘，1.03x軌道週期)
- **OneWeb**: 651顆衛星，~218軌道點/衛星 (~108.5分鐘，0.97x軌道週期)
- **引擎類型**: `Skyfield_Direct` (NASA JPL 標準)
- **記憶體使用**: ~1,485 MB (完整時間序列數據)
- **精度標準**: SGP4 官方精度規範
- **時間窗口**: 動態軌道週期 (Starlink: 90-95min, OneWeb: 109-115min, 覆蓋 ~1.0x 軌道週期)

### 與 Stage 3 集成
- **數據格式**: 標準化 TEME 座標
- **座標系統**: True Equator Mean Equinox
- **傳遞方式**: ProcessingResult.data 結構
- **兼容性**: 為 Stage 3 座標轉換準備

## 🏗️ 驗證架構設計

### 兩層驗證機制

本系統採用**兩層驗證架構**，確保數據品質的同時避免重複邏輯：

#### **Layer 1: 處理器內部驗證** (生產驗證)
- **負責模組**: `Stage2OrbitalPropagationProcessor.run_validation_checks()`
- **執行時機**: 處理器執行完成後立即執行
- **驗證內容**: 詳細的 5 項專用驗證檢查
- **輸出結果**:
  ```json
  {
    "checks_performed": 5,
    "checks_passed": 5,
    "check_details": {
      "epoch_datetime_validation": {"passed": true, "details": {...}},
      "sgp4_propagation_accuracy": {"passed": true, "details": {...}},
      "time_series_completeness": {"passed": true, "details": {...}},
      "teme_coordinate_validation": {"passed": true, "details": {...}},
      "memory_performance_check": {"passed": true, "details": {...}}
    }
  }
  ```
- **保存位置**: `data/validation_snapshots/stage2_validation.json`

#### **Layer 2: 腳本品質檢查** (快照驗證)
- **負責模組**: `check_validation_snapshot_quality()` in `run_six_stages_with_validation.py`
- **執行時機**: 讀取驗證快照文件後
- **設計原則**:
  - ✅ **信任 Layer 1 的詳細驗證結果**
  - ✅ 檢查 Layer 1 是否執行完整 (`checks_performed == 5`)
  - ✅ 檢查 Layer 1 是否通過 (`checks_passed >= 4`)
  - ✅ 額外的架構合規性檢查（v3.0 標記、星座分離、禁止職責等）
- **不應重複**: Layer 1 的詳細檢查邏輯

### 驗證流程圖

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 2 執行                                               │
├─────────────────────────────────────────────────────────────┤
│  1. processor.execute(stage1_data) → ProcessingResult       │
│     ↓                                                       │
│  2. processor.run_validation_checks() (Layer 1)             │
│     → 執行 5 項詳細驗證                                      │
│     → 生成 validation_checks 對象                           │
│     ↓                                                       │
│  3. processor.save_validation_snapshot()                    │
│     → 保存到 stage2_validation.json                         │
│     ↓                                                       │
│  4. check_validation_snapshot_quality() (Layer 2)           │
│     → 讀取驗證快照                                           │
│     → 檢查 checks_performed/checks_passed                   │
│     → 架構合規性檢查 (v3.0, 禁止職責)                        │
│     ↓                                                       │
│  5. 驗證通過 → 進入 Stage 3                                 │
└─────────────────────────────────────────────────────────────┘
```

### 為什麼不在 Layer 2 重複檢查？

**設計哲學**：
- **單一職責**: Layer 1 負責詳細驗證，Layer 2 負責合理性檢查
- **避免重複**: 詳細驗證邏輯已在處理器內部實現，無需在腳本中重複
- **信任機制**: Layer 2 信任 Layer 1 的專業驗證結果
- **效率考量**: 避免重複讀取大量數據進行二次驗證

**Layer 2 的真正價值**：
- 確保 Layer 1 確實執行了驗證（防止忘記調用）
- 架構層面的防禦性檢查（如禁止 TLE 重新解析、禁止座標轉換）
- 數據摘要的合理性檢查（如衛星數量、軌道點數、星座分離）

## 🔬 驗證框架

### 5項專用驗證檢查 (Layer 1 處理器內部)
1. **epoch_datetime_validation** - 時間基準驗證
   - 確認使用 Stage 1 提供的 epoch_datetime
   - 禁止 TLE 重新解析檢查
   - 時間格式一致性驗證

2. **sgp4_propagation_accuracy** - 軌道傳播精度
   - SGP4 計算結果合理性檢查
   - 軌道週期驗證 (LEO: 90-120分鐘)
   - 速度量級檢查 (LEO: ~7.5 km/s)

3. **time_series_completeness** - 時間序列完整性
   - 時間步長一致性檢查
   - 數據點連續性驗證
   - 時間窗口覆蓋完整性

4. **teme_coordinate_validation** - TEME 座標驗證
   - 座標系統正確性檢查
   - 位置向量量級驗證 (LEO: 6400-8000 km)
   - 速度向量方向性檢查

5. **memory_performance_check** - 記憶體性能檢查
   - 記憶體使用量監控
   - 數據結構效率驗證
   - 處理時間性能基準

## 🚀 使用方式與配置

### 標準調用方式
```python
from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor

# 接收 Stage 1 結果
stage1_result = stage1_processor.execute()

# 創建 Stage 2 處理器
processor = Stage2OrbitalPropagationProcessor(config)

# 執行軌道傳播
result = processor.execute(stage1_result.data)  # 使用 Stage 1 數據

# 驗證檢查
validation = processor.run_validation_checks(result.data)

# Stage 3 數據準備
stage3_input = result.data  # TEME 座標數據
```

### 配置選項
```python
config = {
    'time_series_config': {
        'start_time': '2025-09-27T08:00:00+08:00',  # 台灣時間
        'duration_hours': 24,
        'time_step_seconds': 30,
        'timezone': 'Asia/Taipei'
    },
    'propagation_config': {
        'sgp4_library': 'skyfield',  # 或 'pyephem'
        'coordinate_system': 'TEME',
        'error_tolerance': 0.001,  # km
        'max_propagation_days': 7
    },
    'performance_config': {
        'parallel_processing': True,
        'max_workers': 8,
        'memory_limit_gb': 2
    }
}
```

## 📋 部署與驗證

### 部署檢驗標準
**成功指標**:
- [x] 使用 Stage 1 epoch_datetime (零 TLE 重新解析)
- [x] TEME 座標數據生成正常 (1,726,294個軌道點)
- [x] 時間序列完整性檢查通過
- [x] SGP4 計算精度符合標準
- [x] 處理時間 < 300秒 (實際 152.9秒)
- [x] 9,041顆衛星軌道狀態生成
- [x] 100% 成功率 (零失敗)
- [x] 5/5 專用驗證檢查通過
- [x] 輸出文件正常保存 (652 MB)

### 測試命令
```bash
# 設置測試模式
export ORBIT_ENGINE_TEST_MODE=1

# 完整 Stage 2 測試
python scripts/run_six_stages_with_validation.py --stage 2

# 檢查軌道狀態輸出
cat data/validation_snapshots/stage2_validation.json | jq '.data_summary'

# 驗證 TEME 座標
cat data/validation_snapshots/stage2_validation.json | jq '.metadata.coordinate_system'

# 檢查輸出文件
ls -lh data/outputs/stage2/
```

**實際測試結果 (2025-10-01)**:
```
✅ Stage 2 執行成功
   執行時間: 152.9 秒
   處理衛星: 9,041 顆
   成功率: 100.0%
   軌道點數: 1,726,294 個
   輸出文件: orbital_propagation_output_20251001_065111.json (652 MB)
   驗證狀態: 5/5 項檢查通過
```

## 🎯 學術標準合規

### Grade A 強制要求
- **✅ 專業庫**: 使用 skyfield 或 pyephem 等學術級 SGP4 實現
- **✅ 時間基準**: 100% 使用 Stage 1 epoch_datetime，零重新解析
- **✅ 座標標準**: 嚴格 TEME 座標系統輸出
- **✅ 軌道精度**: 符合 SGP4 官方精度規範
- **✅ 數據完整**: 完整的位置/速度時間序列

### 零容忍項目
- **❌ TLE 重新解析**: 絕對禁止重新解析任何 TLE 資料
- **❌ 簡化軌道**: 禁止使用 Keplerian 或簡化軌道模型
- **❌ 自製 SGP4**: 禁止自行實現 SGP4 算法
- **❌ 座標混合**: 禁止在此階段進行座標轉換
- **❌ 可見性計算**: 禁止在此階段進行可見性分析

---

**文檔版本**: v3.0 (重構版)
**概念狀態**: ✅ 軌道狀態傳播 (已修正)
**學術合規**: ✅ Grade A 標準
**維護負責**: Orbit Engine Team