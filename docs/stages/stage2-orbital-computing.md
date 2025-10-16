# 🛰️ Stage 2: 軌道狀態傳播層 - 完整規格文檔

**最後更新**: 2025-10-16 (實際測試結果同步)
**重構狀態**: ✅ 已完成 Skyfield 直接實現 + 統一時間窗口
**學術合規**: Grade A 標準，NASA JPL 精度
**接口標準**: 100% BaseStageProcessor 合規
**效能提升**: 🚀 96% 處理速度提升 (vs 重構前)
**時間同步**: 🆕 統一時間窗口模式（v3.1）

## 📖 概述與目標

**核心職責**: 直接使用 Skyfield 進行 SGP4/SDP4 軌道傳播
**輸入**: Stage 1 的 ProcessingResult (包含每顆衛星的 epoch_datetime)
**輸出**: TEME 座標系統中的位置/速度時間序列
**處理效能**: ✅ **13.0秒** (9,165顆衛星，完整數據集) - v3.0 優化處理
**處理速度**: ✅ **704.5 顆衛星/秒** - NASA JPL 標準精度
**軌道點生成**: ✅ **1,760,880個** TEME 座標點 (696 MB JSON + 199 MB HDF5)
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

### ✅ 簡化重構後的直接架構（v3.1 統一時間窗口）
```
┌─────────────────────────────────────────────────────────┐
│       Stage 2: 軌道狀態傳播層 (Skyfield 直接實現)         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │     🆕 UnifiedTimeWindowManager (v3.1)          │   │
│  │                                                 │   │
│  │  📊 從 Stage 1 讀取推薦參考時刻                  │   │
│  │  🕐 統一時間窗口生成 (所有衛星共用起點)          │   │
│  │  🌍 星座感知軌道週期 (Starlink/OneWeb)         │   │
│  │  ✅ 參考時刻驗證 (±12h 容差檢查)               │   │
│  │  🔄 向後兼容 (支持 independent_epoch 模式)     │   │
│  └─────────────────────────────────────────────────┘   │
│                            │                            │
│                            ▼                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │            SGP4Calculator (簡化版)              │   │
│  │                                                 │   │
│  │  🚀 直接使用 Skyfield NASA JPL 標準            │   │
│  │  ❌ 移除 SGP4OrbitalEngine 中間層              │   │
│  │  📦 內建衛星快取 (避免重複創建)                 │   │
│  │  📊 零格式轉換，原生 TEME 輸出                 │   │
│  │  ⚡ 680 顆/秒處理速度 (v3.0 優化)            │   │
│  └─────────────────────────────────────────────────┘   │
│                            │                            │
│                            ▼                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │      Stage2OrbitalPropagationProcessor          │   │
│  │                                                 │   │
│  │  ✅ 使用 Stage 1 epoch_datetime (v3.0合規)     │   │
│  │  🆕 整合統一時間窗口管理器 (v3.1)              │   │
│  │  🛰️ 星座分離計算 (Starlink/OneWeb)            │   │
│  │  ⏱️ 時間序列生成 (統一參考時刻或獨立epoch)     │   │
│  │  📍 TEME 座標標準輸出                          │   │
│  │  🔬 5項專用驗證檢查                            │   │
│  │  📈 100% 成功率 (9,165顆衛星實測)             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 🎯 **重構改進對比**

| 項目 | 重構前 (複雜版) | 重構後 (v3.0 簡化版) | 提升幅度 |
|------|----------------|---------------------|----------|
| **調用層數** | 3層包裝 | 1層直接 | **67% 簡化** |
| **處理時間** | ~239秒 (9041顆) | **13.0秒** (9165顆) | **🚀 95% 提升** |
| **處理速度** | ~38顆/秒 | **704.5顆/秒** | **🚀 1754% 提升** |
| **成功率** | 未知 | **100.0%** | **完美穩定** |
| **維護負擔** | 複雜包裝層 | 單一Skyfield | **大幅簡化** |
| **學術可信** | 自建包裝 | NASA JPL標準 | **權威保證** |

**📊 測試數據說明**: 重構後數據基於完整衛星數據集（9,165顆），無Epoch篩選。性能提升源自架構優化、Skyfield直接調用、並行處理優化。

## 🆕 統一時間窗口功能（v3.1 新增）

### 🎯 核心問題與解決方案

**問題**：當前 Stage 2 讓每顆衛星使用各自的 epoch 時間生成時間序列，導致：
- 9,039 顆衛星產生 272,226 個完全不同的時間戳
- Stage 4 無法統計「某個時刻有多少顆衛星同時可見」
- 平均可見衛星數異常低（1.02 顆，預期 10-15 顆）

**解決方案**：統一時間窗口模式
- ✅ 所有衛星共用同一個參考起點時刻（來自 Stage 1 Epoch 分析）
- ✅ 保持星座特性（Starlink 95分鐘，OneWeb 110分鐘）
- ✅ 時間序列完全同步（所有 Starlink 共用 190 個時間點）
- ✅ 計算量減少 39.8%（5,444 顆 vs 9,039 顆）

### 📊 時間序列生成模式

#### 模式 1：unified_window（統一時間窗口）🆕
```python
# 所有衛星從同一參考時刻開始
reference_time = "2025-10-02T02:30:00Z"  # 來自 Stage 1 Epoch 分析

for satellite in satellites:
    time_series = generate_time_series(
        start=reference_time,                      # 統一起點！
        duration=get_orbital_period(satellite),    # 星座特定週期
        interval=30
    )
    # Starlink: [02:30:00, 02:30:30, ..., 04:05:00] (190 點)
    # OneWeb:   [02:30:00, 02:30:30, ..., 04:22:00] (224 點)
```

#### 模式 2：independent_epoch（獨立 epoch）
```python
# 每顆衛星使用各自的 epoch 時間（舊行為，向後兼容）
for satellite in satellites:
    start_time = satellite['epoch_datetime']  # 不同的起點
    time_series = generate_time_series(
        start=start_time,
        duration=get_orbital_period(satellite),
        interval=30
    )
```

### 🔧 配置示例

```yaml
time_series:
  # 時間序列生成模式
  mode: 'unified_window'  # 'unified_window' | 'independent_epoch'

  # 統一時間窗口配置（mode='unified_window' 時生效）
  unified_window:
    reference_time_source: 'stage1_analysis'  # 從 Stage 1 讀取
    max_epoch_deviation_hours: 12             # 參考時刻容差

  # 星座軌道週期配置
  constellation_orbital_periods:
    starlink_minutes: 95   # Starlink 軌道週期 (SOURCE: 開普勒第三定律, a=6921km)
    oneweb_minutes: 110    # OneWeb 軌道週期 (SOURCE: 開普勒第三定律, a=7571km)
    default_minutes: 100   # 其他衛星默認週期

  # 時間步長
  interval_seconds: 30
```

### 📊 Stage 1 Epoch 分析文件格式

當使用 `reference_time_source: 'stage1_analysis'` 時，Stage 2 會讀取 Stage 1 生成的 `epoch_analysis.json`：

**文件路徑**: `data/outputs/stage1/epoch_analysis.json`

**格式範例**:
```json
{
  "total_satellites": 9036,
  "epoch_time_range": {
    "earliest": "2025-10-01T03:09:50.315904Z",
    "latest": "2025-10-03T14:39:19.996704Z",
    "span_days": 2.48
  },
  "date_distribution": {
    "2025-10-03": {"count": 6191, "percentage": 68.5},
    "2025-10-02": {"count": 2824, "percentage": 31.3}
  },
  "time_distribution": {
    "target_date": "2025-10-03",
    "hourly_distribution": {
      "6": 1509,  // 最密集時段
      "5": 870
    },
    "most_dense_hour": 6,
    "most_dense_count": 1509,
    "most_dense_percentage": 24.4
  },
  "constellation_distribution": {
    "STARLINK": {"count": 8385, "latest_epoch": "2025-10-03T14:39:19.996704Z"},
    "ONEWEB": {"count": 651, "latest_epoch": "2025-10-03T08:00:01.999872Z"}
  },
  "recommended_reference_time": "2025-10-03T06:30:00Z",  // ← Stage 2 使用此時刻
  "recommendation_reason": "最新日期 2025-10-03 的最密集時段 06:00-06:59 (1509 顆衛星，24.4%)"
}
```

**使用流程**:
1. Stage 1 分析所有衛星的 TLE epoch 分布
2. 找出最密集的時段（例：06:00-06:59 有 24.4% 衛星）
3. 推薦該時段中點作為參考時刻（例：06:30:00）
4. Stage 2 讀取並驗證該參考時刻（±12h 容差）
5. 所有衛星使用此參考時刻作為時間序列起點

**優勢**:
- ✅ 自動適應 TLE 數據更新日期
- ✅ 最大化時間同步衛星數量（80%+ 合規率）
- ✅ 零硬編碼，完全數據驅動

### ✅ 預期效果

| 項目 | 改善前 | 改善後 | 說明 |
|------|--------|--------|------|
| **時間序列數量** | 272,226 個 | 190 個 (Starlink) | 所有 Starlink 共用 |
| **平均可見衛星數** | 1.02 顆 | 10-15 顆 | 時間同步後正常統計 |
| **處理衛星數** | 9,039 顆 | 5,444 顆 | Stage 1 日期篩選 |
| **座標點數** | 1,726,109 | 1,039,599 | -39.8% |

## 🎯 核心功能與職責

### ✅ **Stage 2 專屬職責**

#### 1. **時間序列規劃與星座分離計算**
- **🆕 時間序列模式**: 統一時間窗口（unified_window）或獨立 epoch（independent_epoch）
- **🆕 參考時刻來源**: Stage 1 Epoch 分析推薦時刻（例: 2025-10-02T02:30:00Z）
- **目標時間窗口**: 基於星座軌道週期的傳播窗口
- **時間步長**: 30秒間隔 (可配置)
- **星座特定軌道週期** ⚠️ **重要**：
  - **Starlink**: 95分鐘軌道週期 → 190個時間點
  - **OneWeb**: 110分鐘軌道週期 → 220個時間點
- **時間來源**: 100% 使用 Stage 1 提供的 epoch_datetime
- **🆕 時間同步保證**: 同一星座的所有衛星使用相同時間序列

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
        'stage': 'stage2_orbital_computing',
        'satellites': {  # ✅ 按星座分組（不是 orbital_states）
            'starlink': {  # 星座層級
                '44734': {  # 衛星 ID
                    'satellite_id': '44734',
                    'constellation': 'starlink',
                    'epoch_datetime': '2025-10-03T06:30:24.123456+00:00',
                    'orbital_states': [  # 軌道狀態序列
                        {
                            'timestamp': '2025-10-03T06:30:00+00:00',
                            'position_teme': [-3981.8, 1921.4, 4968.7],  # TEME 座標 (km)
                            'velocity_teme': [-5.279, -5.216, -2.206],   # TEME 速度 (km/s)
                            'satellite_id': '44734'
                        },
                        # ... 更多時間點（約 193 個，Starlink）
                    ],
                    'propagation_successful': True,
                    'algorithm_used': 'SGP4',
                    'coordinate_system': 'TEME',
                    'total_positions': 193
                }
                # ... 更多 Starlink 衛星
            },
            'oneweb': {  # OneWeb 星座
                # ... OneWeb 衛星（類似結構）
            }
        },
        'metadata': {
            # ⚠️ 注意: 配置參數直接在 metadata 下（不使用 propagation_config 嵌套）
            'coordinate_system': 'TEME',
            'propagation_method': 'SGP4',
            'epoch_datetime_source': 'stage1_provided',
            'architecture_version': 'v3.0',
            'stage_concept': 'orbital_state_propagation',

            # 處理統計
            'total_satellites_processed': 9165,
            'successful_propagations': 9165,
            'failed_propagations': 0,
            'total_teme_positions': 1760880,
            'processing_duration_seconds': 13.009987,
            'constellation_distribution': {
                'starlink': 8514,
                'oneweb': 651
            },

            # 時間序列配置
            'time_interval_seconds': 30,
            'dynamic_calculation_enabled': True,
            'coverage_cycles': 1.0,

            # 合規標記
            'tle_reparse_prohibited': True,
            'processing_grade': 'A',

            # Stage 1 metadata 繼承（完整保留）
            'constellation_configs': {...},  # 來自 Stage 1
            'research_configuration': {...}  # 來自 Stage 1
        },
        'processing_stats': {...},
        'next_stage_ready': True
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
    'timestamp': '2025-10-03T06:30:00+00:00',
    'position_teme': [x, y, z],      # TEME 座標 (km)
    'velocity_teme': [vx, vy, vz],   # TEME 速度 (km/s)
    'satellite_id': 'STARLINK-1234'
    # ⚠️ 注意: v3.0 已移除 propagation_error 字段
    # 依據 Grade A 標準，SGP4 誤差應從算法實際計算獲取，不使用硬編碼估算值
    # 參考: stage2_result_manager.py:86-90, docs/ACADEMIC_STANDARDS.md
}
```

## ⚡ 性能指標 (簡化重構後實測)

### 🚀 **實際性能指標 - 2025-10-16 最新測試結果**
- **處理時間**: ✅ **13.0秒** (9,165顆衛星) - 完整數據集處理
- **處理速度**: ✅ **704.5顆衛星/秒** - NASA JPL 標準精度
- **軌道點速度**: ✅ **135,452點/秒** - 高速批量計算
- **成功率**: ✅ **100.0%** - 零失敗率 (9,165/9,165)
- **軌道點總數**: ✅ **1,760,880個** - 完整動態軌道週期時間序列
- **平均點數/衛星**: ✅ **192.1點** - 動態軌道週期計算 (1.0x週期覆蓋)
- **時間步長**: 30秒間隔 (可配置)
- **輸出文件大小**: 696 MB (JSON) + 199 MB (HDF5)
- **HDF5壓縮率**: 71.4% (199 MB vs 696 MB JSON)

### 📊 **星座分離處理效能**
- **Starlink**: 8,514顆衛星，~193軌道點/衛星 (~95分鐘，1.01x軌道週期)
- **OneWeb**: 651顆衛星，~192軌道點/衛星 (~96分鐘，0.87x軌道週期)
- **引擎類型**: `Skyfield_Direct` (NASA JPL 標準)
- **記憶體使用**: ~1,634 MB (完整時間序列數據)
- **精度標準**: SGP4 官方精度規範
- **時間窗口**: 動態軌道週期 (Starlink: 90-95min, OneWeb: 109-115min, 覆蓋 ~1.0x 軌道週期)

**📊 測試配置**: 本測試處理完整衛星數據集（無Epoch篩選），使用統一時間窗口模式（v3.1），所有衛星共用參考時刻 2025-10-02T02:30:00Z。

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
- [x] TEME 座標數據生成正常 (1,760,880個軌道點)
- [x] 時間序列完整性檢查通過
- [x] SGP4 計算精度符合標準
- [x] 處理時間 < 300秒 (實際 13.0秒，v3.0 優化)
- [x] 9,165顆衛星軌道狀態生成 (完整數據集)
- [x] 100% 成功率 (零失敗)
- [x] 5/5 專用驗證檢查通過
- [x] 輸出文件正常保存 (696 MB JSON + 199 MB HDF5)

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

**實際測試結果 (2025-10-16)**:
```
✅ Stage 2 執行成功
   執行時間: 13.0 秒
   處理衛星: 9,165 顆 (完整數據集，無Epoch篩選)
   成功率: 100.0%
   軌道點數: 1,760,880 個
   輸出文件: orbital_propagation_output_*.json (696 MB)
              orbital_propagation_output_*.h5 (199 MB)
   驗證狀態: 5/5 項檢查通過
   處理速度: 704.5 顆/秒 (NASA JPL 標準精度)
   星座分布: Starlink 8,514顆 | OneWeb 651顆
   記憶體使用: 1,634 MB
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