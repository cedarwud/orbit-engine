# 🌍 Stage 3: 座標系統轉換層 - 完整規格文檔

**最後更新**: 2025-09-28
**核心職責**: TEME→ITRF→WGS84 專業級座標轉換
**學術合規**: Grade A 標準，使用 Skyfield 專業庫
**接口標準**: 100% BaseStageProcessor 合規

## 📖 概述與目標

**核心職責**: 專業級座標系統轉換，TEME→ITRF→WGS84
**輸入**: Stage 2 的 TEME 座標時間序列
**輸出**: WGS84 地理座標 (經度/緯度/高度)
**處理時間**: ~1-2秒 (8,995顆衛星座標轉換)
**學術標準**: 使用 Skyfield IAU 標準實現

### 🎯 Stage 3 核心價值
- **專業座標轉換**: 使用 Skyfield 確保 IAU 標準合規
- **精確時間處理**: 考慮極移、章動、時間修正
- **地理座標輸出**: 提供標準 WGS84 經緯度給 Stage 4
- **高精度保證**: 亞米級座標轉換精度

## 🚨 重要概念修正

### ❌ **修正前的錯誤概念**
```
Stage 3: 信號品質分析
- RSRP/RSRQ/SINR 計算
- 3GPP NTN 事件檢測
- 物理層參數計算
- 信號品質評估和分類
```

### ✅ **修正後的正確概念**
```
Stage 3: 座標系統轉換
- TEME→ITRF 座標轉換
- ITRF→WGS84 地理座標轉換
- 精確時間基準處理
- IAU 標準極移修正
```

**學術依據**:
> *"Accurate coordinate transformation is essential for satellite visibility analysis. The TEME to ITRF transformation requires precise time corrections and polar motion parameters as specified by IAU standards."*
> — Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications

## 🏗️ 架構設計

### 重構後組件架構
```
┌─────────────────────────────────────────────────────────┐
│           Stage 3: 座標系統轉換層 (重構版)               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │TEME→ITRF    │  │ITRF→WGS84   │  │Time         │    │
│  │Converter    │  │Converter    │  │Corrector    │    │
│  │             │  │             │  │             │    │
│  │• IAU 標準    │  │• 地理座標    │  │• 極移修正    │    │
│  │• 極移參數    │  │• 經緯度     │  │• 章動修正    │    │
│  │• 旋轉矩陣    │  │• 橢球座標    │  │• UTC/TT轉換  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│           │              │              │             │
│           └──────────────┼──────────────┘             │
│                          ▼                            │
│  ┌──────────────────────────────────────────────┐    │
│  │        Stage3CoordinateTransformProcessor    │    │
│  │        (BaseStageProcessor 合規)             │    │
│  │                                              │    │
│  │ • Skyfield 專業庫使用                        │    │
│  │ • 批次座標轉換                               │    │
│  │ • 精度驗證                                   │    │
│  │ • ProcessingResult 標準輸出                  │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 🎯 核心功能與職責

### ✅ **Stage 3 專屬職責**

#### 1. **分層處理架構** (新增優化)
- **第一層**: 快速可見性篩選 (9041→2000顆)
  - 使用簡化TEME→WGS84轉換 (公里級精度)
  - NTPU座標可見性判斷 (仰角>0°)
  - 快速排除永不可見衛星
  - 兩星座統一篩選標準
- **第二層**: 精密座標轉換 (2000顆候選，各自軌道週期)
  - **Starlink處理**: ~1600顆 × 191時間點 (95分鐘週期)
  - **OneWeb處理**: ~400顆 × 218時間點 (108.5分鐘週期)
  - 使用Skyfield專業級轉換 (亞米級精度)
  - 完整IAU標準算法鏈
  - 為動態池規劃提供高精度基礎

#### 2. **TEME→ITRF 轉換** (精密層)
- **旋轉矩陣計算**: 使用 Skyfield 計算精確旋轉矩陣
- **極移修正**: IERS 極移參數自動獲取和應用
- **章動修正**: IAU 2000A 章動模型
- **時間修正**: UTC↔TT↔UT1 精確轉換

#### 3. **ITRF→WGS84 轉換** (精密層)
- **橢球座標**: 精確 Cartesian→Geodetic 轉換
- **WGS84 標準**: 使用 WGS84 橢球參數
- **高度計算**: 橢球高度與正交高度
- **精度保證**: 亞米級轉換精度

#### 4. **效率優化處理**
- **資源集中**: 精密計算只用於可見候選衛星
- **記憶體管理**: 分批處理降低記憶體壓力
- **並行處理**: 多核心座標轉換加速
- **精度監控**: 轉換精度實時監控

### ❌ **明確排除職責** (移至後續階段)
- ❌ **可見性分析**: 仰角、方位角計算 (移至 Stage 4)
- ❌ **信號計算**: RSRP/RSRQ/SINR 分析 (移至 Stage 5)
- ❌ **事件檢測**: 3GPP NTN 事件處理 (移至 Stage 6)
- ❌ **優化決策**: 衛星選擇和排序 (移至後續階段)

## 🔬 Skyfield 專業實現

### 🚨 **CRITICAL: 使用 Skyfield 專業庫**

**✅ 正確的專業實現**:
```python
from skyfield.api import load, wgs84
from skyfield.framelib import itrs
from skyfield.timelib import Time

# 正確！使用 Skyfield 專業座標轉換
def convert_teme_to_wgs84(position_teme_km, velocity_teme_km_s, time_ut1):
    """使用 Skyfield 進行 TEME→WGS84 轉換"""

    # 創建 Skyfield 時間對象
    ts = load.timescale()
    t = ts.from_datetime(time_ut1)

    # 創建 GCRS (近似 TEME) 位置
    position_au = position_teme_km / 149597870.7  # km to AU
    velocity_au_day = velocity_teme_km_s * 86400 / 149597870.7  # km/s to AU/day

    # 創建位置對象
    gcrs_position = build_position_velocity(position_au, velocity_au_day, t)

    # 轉換到 ITRS (地球固定座標)
    itrs_position = gcrs_position.frame_xyz(itrs)

    # 轉換到 WGS84 地理座標
    geographic = wgs84.geographic_position_of(itrs_position)

    return {
        'latitude_deg': geographic.latitude.degrees,
        'longitude_deg': geographic.longitude.degrees,
        'altitude_m': geographic.elevation.m
    }
```

**❌ 絕對禁止的自製算法**:
```python
# 禁止！不得使用自製座標轉換
def manual_teme_to_wgs84(position, time):
    # 自製旋轉矩陣計算 - 精度不足
    # 忽略極移、章動 - 不符合學術標準
    # 簡化橢球轉換 - 誤差過大
```

### Skyfield 實現優勢
- **IAU 標準**: 完全符合國際天文聯合會標準
- **IERS 數據**: 自動獲取地球旋轉參數
- **高精度**: 亞米級座標轉換精度
- **維護良好**: 天文學界標準庫，持續更新

## 📊 標準化輸出格式

### ProcessingResult 結構
```python
ProcessingResult(
    status=ProcessingStatus.SUCCESS,
    data={
        'stage': 3,
        'stage_name': 'coordinate_system_transformation',
        'geographic_coordinates': {
            'satellite_id_1': {
                'time_series': [
                    {
                        'timestamp': '2025-09-27T08:00:00.000000+00:00',
                        'latitude_deg': 25.1234,     # WGS84 緯度
                        'longitude_deg': 121.5678,   # WGS84 經度
                        'altitude_m': 550123.45,     # WGS84 橢球高度
                        'altitude_km': 550.12345     # 高度公里 (便於使用)
                    },
                    # ... 更多時間點
                ],
                'transformation_metadata': {
                    'coordinate_system': 'WGS84',
                    'reference_frame': 'ITRS',
                    'time_standard': 'UTC',
                    'precision_m': 0.15  # 估計精度
                }
            }
            # ... 更多衛星
        },
        'metadata': {
            # 座標轉換參數
            'transformation_config': {
                'source_frame': 'TEME',
                'target_frame': 'WGS84',
                'time_corrections': True,
                'polar_motion': True,
                'nutation_model': 'IAU2000A'
            },

            # Skyfield 配置
            'skyfield_config': {
                'library_version': '1.46',
                'ephemeris': 'de421.bsp',
                'iers_data': 'finals2000A.all',
                'leap_seconds': 'Leap_Second.dat'
            },

            # 處理統計
            'total_satellites': 8995,
            'total_coordinate_points': 12952800,  # 8995 × 1440
            'processing_duration_seconds': 1.856,
            'coordinates_generated': True,

            # 精度標記
            'transformation_accuracy_m': 0.15,
            'iau_standard_compliance': True,
            'academic_standard': 'Grade_A'
        }
    },
    metadata={...},
    errors=[],
    warnings=[],
    metrics=ProcessingMetrics(...)
)
```

### 地理座標數據格式
```python
geographic_point = {
    'timestamp': '2025-09-27T08:00:00.000000+00:00',
    'latitude_deg': 25.1234,      # WGS84 緯度 (度)
    'longitude_deg': 121.5678,    # WGS84 經度 (度)
    'altitude_m': 550123.45,      # WGS84 橢球高度 (米)
    'altitude_km': 550.12345,     # 高度 (公里)
    'satellite_id': 'STARLINK-1234',
    'transformation_error_m': 0.12  # 估計誤差 (米)
}
```

## ⚡ 性能指標

### 🎯 CPU基準測試結果 (2025-09-29)

**📊 實際測試數據 (CPU基準)**:
- **總執行時間**: 802.65 秒 (**13.4 分鐘**)
- **輸入衛星數**: 9,040 顆
- **第一層篩選結果**: 2,059/9,040 顆衛星通過 (**22.8% 通過率**)
- **第二層轉換點數**: 195,849 個座標點
- **轉換成功率**: **100%** (195,849/195,849)
- **轉換速度**: **518 點/秒**
- **輸出文件大小**: 189MB (JSON格式)

**階段時間分析**:
- **第一層篩選**: ~2分鐘 (快速可見性篩選)
- **第二層轉換**: ~11分鐘 (精密座標轉換)
- **其他處理**: ~0.4分鐘 (初始化、驗證、輸出)

**質量指標**:
- ✅ **IERS數據使用**: 正常，無緩存警告
- ✅ **座標轉換**: 100%成功，無錯誤
- ✅ **驗證結果**: 完全通過
- ✅ **數據完整性**: 全部座標點成功生成

### 目標性能指標 (優化後分層處理)
- **處理時間**: < 20分鐘 (分層處理：快速篩選 + 精密轉換)
- **座標點數**: 1,744,408 點 (兩星座各自軌道週期)
  - **Starlink**: 8,390顆 × 191點 (95分鐘軌道週期) = 1,602,490點
  - **OneWeb**: 651顆 × 218點 (108.5分鐘軌道週期) = 141,918點
- **分層策略**:
  - 第一層：9041→2000顆快速可見性篩選 (3分鐘)
  - 第二層：2000顆候選精密Skyfield轉換 (15分鐘)
    - Starlink候選: ~1600顆 × 191點
    - OneWeb候選: ~400顆 × 218點
- **轉換精度**: < 0.5米 (95% 信賴區間，IAU標準)
- **記憶體使用**: < 1GB (優化後批次處理)
- **效率提升**: 67%時間節省 (60分鐘→20分鐘)

### 🚀 GPU優化目標 (基於CPU基準)

**瓶頸分析**:
- **主要瓶頸**: 第二層精密座標轉換 (11分鐘，518點/秒)
- **優化策略**: 僅對第二層實施GPU加速
- **保持原樣**: 第一層篩選邏輯保持CPU實現

**GPU優化目標**:
- **目標速度**: 5,000-10,000 點/秒 (**10-20倍提升**)
- **預期時間**: 第二層從11分鐘縮短到 **1-2分鐘**
- **總執行時間**: 從13.4分鐘縮短到 **3-4分鐘**
- **性能提升**: **70-75%** 時間節省

**實現方案**:
```python
# 第一層：保持CPU實現（已經很高效）
visible_satellites = self._apply_real_visibility_filter(teme_data)

# 第二層：改用GPU批量轉換
if GPU_AVAILABLE:
    batch_results = self.coordinate_engine.batch_convert_teme_to_wgs84_gpu(batch_data)
else:
    batch_results = self.coordinate_engine.batch_convert_teme_to_wgs84(batch_data)  # CPU回退
```

### 性能說明
**分層處理策略的合理性**：
- **第一層篩選**: 使用簡化算法快速排除不可見衛星
- **第二層精算**: 對候選衛星使用Skyfield專業級轉換
- **資源集中**: 精密計算只用於真正需要的2000顆衛星
- **效率平衡**: 在保持最終精度的同時大幅提升處理效率

### 與 Stage 4 集成
- **數據格式**: 標準化 WGS84 地理座標
- **座標系統**: WGS84 橢球座標
- **傳遞方式**: ProcessingResult.data 結構
- **兼容性**: 為 Stage 4 可見性分析準備

## 🔬 驗證框架

### 5項專用驗證檢查
1. **coordinate_transformation_accuracy** - 座標轉換精度
   - Skyfield 轉換結果合理性檢查
   - 位置座標範圍驗證 (緯度: -90°~90°)
   - 高度範圍檢查 (LEO: 200-2000km)

2. **time_system_validation** - 時間系統驗證
   - UTC/TT/UT1 時間轉換檢查
   - 閏秒處理正確性驗證
   - IERS 數據有效性檢查

3. **iau_standard_compliance** - IAU 標準合規
   - 極移參數應用檢查
   - 章動模型驗證 (IAU2000A)
   - 旋轉矩陣正交性檢查

4. **skyfield_library_validation** - Skyfield 庫驗證
   - 庫版本兼容性檢查
   - 星歷數據完整性驗證
   - 計算結果一致性檢查

5. **batch_processing_performance** - 批次處理性能
   - 記憶體使用量監控
   - 處理速度基準檢查
   - 並行效率驗證

## 🚀 使用方式與配置

### 標準調用方式
```python
from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor

# 接收 Stage 2 結果
stage2_result = stage2_processor.execute()

# 創建 Stage 3 處理器
processor = Stage3CoordinateTransformProcessor(config)

# 執行座標轉換
result = processor.execute(stage2_result.data)  # 使用 Stage 2 TEME 數據

# 驗證檢查
validation = processor.run_validation_checks(result.data)

# Stage 4 數據準備
stage4_input = result.data  # WGS84 座標數據
```

### 配置選項
```python
config = {
    'coordinate_config': {
        'source_frame': 'TEME',
        'target_frame': 'WGS84',
        'time_corrections': True,
        'polar_motion': True,
        'nutation_model': 'IAU2000A'
    },
    'skyfield_config': {
        'ephemeris_file': 'de421.bsp',
        'iers_data_file': 'finals2000A.all',
        'leap_second_file': 'Leap_Second.dat',
        'auto_download': True
    },
    'performance_config': {
        'batch_size': 1000,
        'parallel_processing': True,
        'max_workers': 8,
        'memory_limit_gb': 1
    },
    'precision_config': {
        'target_accuracy_m': 0.5,
        'convergence_tolerance': 1e-12,
        'max_iterations': 50
    }
}
```

## 📋 部署與驗證

### 部署檢驗標準
**成功指標**:
- [ ] Skyfield 庫正確安裝和配置
- [ ] IERS 數據自動下載和更新
- [ ] WGS84 座標數據生成正常
- [ ] 座標轉換精度 < 0.5米
- [ ] 處理時間 < 2秒
- [ ] 12,952,800 座標點生成

### 測試命令
```bash
# 完整 Stage 3 測試
python scripts/run_six_stages_with_validation.py --stage 3

# 檢查座標轉換輸出
cat data/validation_snapshots/stage3_validation.json | jq '.data_summary.coordinate_points_count'

# 驗證 WGS84 座標
cat data/validation_snapshots/stage3_validation.json | jq '.metadata.target_frame'
```

### Skyfield 環境檢查
```bash
# 檢查 Skyfield 安裝
python -c "import skyfield; print(f'Skyfield version: {skyfield.__version__}')"

# 檢查星歷數據
python -c "
from skyfield.api import load
ts = load.timescale()
print('Skyfield 環境正常')
"
```

## 🎯 學術標準合規

### Grade A 強制要求
- **✅ Skyfield 專業庫**: 使用天文學界標準座標轉換庫
- **✅ IAU 標準**: 完全符合國際天文聯合會座標系統標準
- **✅ IERS 數據**: 自動獲取和使用地球旋轉參數
- **✅ 時間精度**: 精確 UTC/TT/UT1 時間系統轉換
- **✅ 轉換精度**: 亞米級座標轉換精度保證

### 零容忍項目
- **❌ 自製轉換**: 絕對禁止自行實現座標轉換算法
- **❌ 簡化公式**: 禁止使用簡化的旋轉矩陣或橢球轉換
- **❌ 忽略修正**: 禁止忽略極移、章動、時間修正
- **❌ 精度妥協**: 禁止為性能犧牲座標轉換精度
- **❌ 非標準系統**: 禁止使用非 WGS84 地理座標系統

## 📈 基準測試記錄

### CPU基準測試 - 2025-09-29

**測試環境**:
- **測試時間**: 2025-09-29 00:37-00:51 UTC
- **測試命令**: `ORBIT_ENGINE_TEST_MODE=1 python scripts/run_six_stages_with_validation.py --stage 3`
- **日誌文件**: `/tmp/stage3_cpu_baseline_final_clean.log`

**測試數據**:
```
輸入衛星: 9,040 顆
第一層篩選: 2,059 顆通過 (22.8%)
第二層轉換: 195,849 座標點
轉換速度: 518 點/秒
總執行時間: 802.65 秒 (13.4 分鐘)
成功率: 100%
```

**關鍵日誌摘要**:
```log
INFO:stage3_coordinate_system_transformation:✅ 第一層篩選完成: 2059/9040 顆衛星可見
INFO:stage3_coordinate_system_transformation:📊 篩選結果: 9040 → 2059 顆衛星 (22.8% 通過)
INFO:stage3_coordinate_system_transformation:📊 準備完成: 195,849 個座標點，9040 顆衛星
INFO:shared.coordinate_systems.skyfield_coordinate_engine:✅ 批次轉換完成: 195849/195849 成功 (100.0%), 平均 518 點/秒
INFO:stage3_coordinate_system_transformation:✅ 批量轉換完成: 195,849/195,849 成功 (100.0%), 518 點/秒
```

**輸出文件**:
- **結果文件**: `data/outputs/stage3/stage3_coordinate_transformation_real_20250929_005119.json`
- **文件大小**: 189MB
- **驗證快照**: `data/validation_snapshots/stage3_validation.json`

**修正問題**:
- ✅ 修正IERS數據緩存邏輯，消除"緩存為空"警告
- ✅ 移除失效的Bulletin A URL，消除404錯誤
- ✅ 實現智能緩存載入，避免不必要的數據下載
- ✅ 優化IERS數據管理器初始化邏輯

**下一步**:
- [ ] 實現GPU版本的第二層座標轉換
- [ ] 性能比較測試 (CPU vs GPU)
- [ ] 驗證GPU結果與CPU基準的一致性

---

**文檔版本**: v3.1 (包含CPU基準測試結果)
**概念狀態**: ✅ 座標系統轉換 (已修正)
**學術合規**: ✅ Grade A 標準
**維護負責**: Orbit Engine Team