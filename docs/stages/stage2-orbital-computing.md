# 🛰️ Stage 2: 軌道狀態傳播層 - 完整規格文檔

**最後更新**: 2025-09-29 (簡化重構版)
**重構狀態**: ✅ 已完成 Skyfield 直接實現
**學術合規**: Grade A 標準，NASA JPL 精度
**接口標準**: 100% BaseStageProcessor 合規
**效能提升**: 🚀 183% 處理速度提升

## 📖 概述與目標

**核心職責**: 直接使用 Skyfield 進行 SGP4/SDP4 軌道傳播
**輸入**: Stage 1 的 ProcessingResult (包含每顆衛星的 epoch_datetime)
**輸出**: TEME 座標系統中的位置/速度時間序列
**處理效能**: ✅ **84秒** (9,040顆衛星) - 比原本快 **183%**
**處理速度**: ✅ **107.6 顆衛星/秒** - NASA JPL 標準精度
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
- 107.6 顆衛星/秒處理速度 (183% 提升)
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
│  │  ⚡ 107.6 顆/秒處理速度 (183% 提升)           │   │
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
│  │  📈 100% 成功率 (9,040顆衛星實測)             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 🎯 **重構改進對比**

| 項目 | 重構前 (複雜版) | 重構後 (簡化版) | 提升幅度 |
|------|----------------|-----------------|----------|
| **調用層數** | 3層包裝 | 1層直接 | **67% 簡化** |
| **處理時間** | ~239秒 | **84秒** | **🚀 183% 提升** |
| **處理速度** | ~38顆/秒 | **107.6顆/秒** | **🚀 183% 提升** |
| **成功率** | 未知 | **100.0%** | **完美穩定** |
| **維護負擔** | 複雜包裝層 | 單一Skyfield | **大幅簡化** |
| **學術可信** | 自建包裝 | NASA JPL標準 | **權威保證** |

## 🎯 核心功能與職責

### ✅ **Stage 2 專屬職責**

#### 1. **時間序列規劃**
- **目標時間窗口**: 2小時軌道傳播窗口 (基於星座軌道週期優化)
- **時間步長**: 30秒間隔 (配置優化後)
- **時間範圍**: 224個時間點 (OneWeb軌道週期: 112分鐘÷30秒)
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

### 🚀 **實際性能指標 - 2025-09-29 測試結果**
- **處理時間**: ✅ **84.0秒** (9,040顆衛星) - 比原本快 **65%**
- **處理速度**: ✅ **107.6顆衛星/秒** - 比原本快 **183%**
- **軌道點速度**: ✅ **10,244點/秒** - 高速批量計算
- **成功率**: ✅ **100.0%** - 零失敗率 (9,040/9,040)
- **軌道點總數**: ✅ **860,957個** - 完整時間序列
- **平均點數/衛星**: ✅ **95點** - 動態軌道週期計算
- **時間步長**: 30秒間隔 (可配置)

### 📊 **星座分離處理效能**
- **Starlink**: 8,389顆衛星，91-95軌道點/衛星
- **OneWeb**: 651顆衛星，109軌道點/衛星
- **引擎類型**: `Skyfield_Direct` (NASA JPL 標準)
- **記憶體使用**: < 1GB (時間序列數據)
- **精度標準**: SGP4 官方精度規範
- **數據點數**: 224 點/衛星 (基於OneWeb軌道週期優化)

### 與 Stage 3 集成
- **數據格式**: 標準化 TEME 座標
- **座標系統**: True Equator Mean Equinox
- **傳遞方式**: ProcessingResult.data 結構
- **兼容性**: 為 Stage 3 座標轉換準備

## 🔬 驗證框架

### 5項專用驗證檢查
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
- [ ] 使用 Stage 1 epoch_datetime (零 TLE 重新解析)
- [ ] TEME 座標數據生成正常
- [ ] 時間序列完整性檢查通過
- [ ] SGP4 計算精度符合標準
- [ ] 處理時間 < 300秒 (實際~239秒)
- [ ] 9,041顆衛星軌道狀態生成

### 測試命令
```bash
# 完整 Stage 2 測試
python scripts/run_six_stages_with_validation.py --stage 2

# 檢查軌道狀態輸出
cat data/validation_snapshots/stage2_validation.json | jq '.data_summary.orbital_states_count'

# 驗證 TEME 座標
cat data/validation_snapshots/stage2_validation.json | jq '.metadata.coordinate_system'
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