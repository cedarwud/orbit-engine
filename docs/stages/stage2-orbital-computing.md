# 🛰️ Stage 2: 軌道狀態傳播層 - 完整規格文檔

**最後更新**: 2025-09-28
**概念修正**: ❌ 可見性篩選 → ✅ 軌道狀態傳播
**學術合規**: Grade A 標準，使用 Stage 1 獨立時間基準
**接口標準**: 100% BaseStageProcessor 合規

## 📖 概述與目標

**核心職責**: SGP4/SDP4 軌道傳播，時間序列軌道狀態計算
**輸入**: Stage 1 的 ProcessingResult (包含每顆衛星的 epoch_datetime)
**輸出**: TEME 座標系統中的位置/速度時間序列
**處理時間**: ~239秒 (9,041顆衛星的時間序列)
**學術標準**: 使用專業 SGP4 庫，零 TLE 重新解析

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

### ✅ **修正後的正確概念**
```
Stage 2: 軌道狀態傳播
- 使用 Stage 1 的 epoch_datetime (零重新解析)
- SGP4/SDP4 時間序列計算
- TEME 座標系統輸出
- 提供原始軌道狀態給後續階段
```

**學術依據**:
> *"Orbital propagation should be separated from visibility analysis. SGP4/SDP4 algorithms generate orbital states in TEME coordinates, while visibility requires coordinate transformation and geometric calculations."*
> — Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications

## 🏗️ 架構設計

### 重構後組件架構
```
┌─────────────────────────────────────────────────────────┐
│           Stage 2: 軌道狀態傳播層 (重構版)               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Time Series  │  │SGP4/SDP4    │  │TEME         │    │
│  │Generator    │  │Propagator   │  │Coordinator  │    │
│  │             │  │             │  │             │    │
│  │• 時間窗口    │  │• 軌道計算    │  │• 座標系統    │    │
│  │• 步長設定    │  │• 位置速度    │  │• 數據格式    │    │
│  │• NTPU時區    │  │• 專業庫     │  │• 標準化     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│           │              │              │             │
│           └──────────────┼──────────────┘             │
│                          ▼                            │
│  ┌──────────────────────────────────────────────┐    │
│  │        Stage2OrbitalPropagationProcessor     │    │
│  │        (BaseStageProcessor 合規)             │    │
│  │                                              │    │
│  │ • 使用 Stage 1 epoch_datetime               │    │
│  │ • SGP4 時間序列生成                          │    │
│  │ • TEME 座標輸出                             │    │
│  │ • ProcessingResult 標準輸出                  │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

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

## ⚡ 性能指標

### 實際性能指標
- **處理時間**: ~239秒 (9,041顆衛星，2小時時間序列)
- **時間步長**: 30秒間隔
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