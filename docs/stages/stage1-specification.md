# 📥 Stage 1: TLE 數據載入層 - 完整規格文檔

**最後更新**: 2025-09-30 (新增 constellation_configs、research_configuration、下游階段使用說明)
**程式狀態**: ✅ 重構完成，Grade A 合規，所有 P0/P1 問題已修復
**接口標準**: 100% BaseStageProcessor 合規
**TLE 格式**: ✅ 嚴格 69 字符 NORAD 標準，Checksum 已修復

## 📖 概述與目標

**核心職責**: TLE 數據載入、驗證、時間基準建立
**輸入**: TLE 檔案（約 2.2MB）
**輸出**: 標準化 ProcessingResult → 記憶體傳遞至 Stage 2
**處理時間**: ~0.56秒 (9,040顆衛星)
**當前狀態**: ✅ 重構完成，Grade A 學術合規

### 🎯 Stage 1 核心價值
- **數據品質保證**: 嚴格的 TLE 格式驗證與 Checksum 檢查
- **時間基準標準化**: 為後續階段提供統一的計算基準時間
- **接口標準化**: 100% 符合 BaseStageProcessor 接口規範
- **學術級合規**: 符合 Grade A 學術標準，零容忍簡化算法

## 🏗️ 架構設計

### 模組化組件架構
```
┌─────────────────────────────────────────────────────────┐
│               Stage 1: 數據載入層 (重構版)                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │TLE Data     │  │Data         │  │Time Reference│    │
│  │Loader       │  │Validator    │  │Manager      │    │
│  │             │  │             │  │             │    │
│  │• 檔案讀取    │  │• 格式驗證    │  │• Epoch提取   │    │
│  │• 解析TLE    │  │• Checksum   │  │• 基準時間    │    │
│  │• 批次處理    │  │• 完整性檢查  │  │• 標準化     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│           │              │              │             │
│           └──────────────┼──────────────┘             │
│                          ▼                            │
│  ┌──────────────────────────────────────────────┐    │
│  │        Stage1MainProcessor                   │    │
│  │        (BaseStageProcessor 合規)             │    │
│  │                                              │    │
│  │ • 協調三個組件                                │    │
│  │ • ProcessingResult 標準輸出                  │    │
│  │ • run_validation_checks() 實現               │    │
│  │ • save_validation_snapshot() 實現            │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 核心處理器實現

**唯一處理器**: `Stage1MainProcessor`（簡化版，單一職責）

```python
class Stage1MainProcessor(BaseStageProcessor):
    """Stage 1 主處理器 - 唯一處理器（簡化重構版）

    100% 接口合規，直接返回 ProcessingResult
    """

    def process(self, input_data) -> ProcessingResult:
        """直接返回標準化 ProcessingResult"""

    def run_validation_checks(self, results) -> Dict:
        """5項 Stage 1 專用驗證檢查"""

    def save_validation_snapshot(self, results) -> bool:
        """標準化快照保存"""

    def _integrate_results(self, ...) -> Dict:
        """內部方法：整合處理結果"""
```

**工廠函數**:
```python
# 推薦方式（最簡潔）
processor = create_stage1_processor(config)

# 向後兼容別名
processor = create_stage1_main_processor(config)
processor = create_stage1_refactored_processor(config)  # 舊名稱
```

**重構說明**: 原雙層架構（Stage1RefactoredProcessor包裝Stage1MainProcessor）已簡化為單一處理器，減少43%冗餘代碼。

## 🎯 核心功能與職責

### ✅ **Stage 1 專屬職責**

#### 1. **TLE 數據載入**
- **TLE 檔案讀取**: 支援標準 NORAD TLE 格式
- **批次處理**: 高效處理 9,040 顆衛星
- **錯誤處理**: 完整的異常和恢復機制
- **來源追蹤**: 完整的數據血統記錄

#### 2. **數據格式驗證**
- **格式嚴格檢查**: 69字符行長度、行號驗證
- **Checksum 驗證**: 完整的 Modulo 10 算法實現
- **NORAD ID 一致性**: 兩行數據一致性檢查
- **必要字段檢查**: 確保所有關鍵字段存在

#### 3. **時間基準建立** 🚨
- **TLE Epoch 提取**: 高精度時間解析，保存每顆衛星的獨立 epoch_datetime
- **時間標準化**: ISO 8601 格式輸出
- **🔴 CRITICAL: 獨立時間基準**: 每筆 TLE 記錄使用自身的 epoch 時間
- **🚫 禁止統一時間**: 不得創建全域統一的 calculation_base_time
- **微秒精度**: 科學級時間精度保證
- **數據傳遞**: 為 Stage 2 提供每顆衛星的 epoch_datetime 字段

**⚠️ 時間基準關鍵原則**:
- 每個 TLE 文件包含多天數據，每筆記錄的 epoch 時間不同
- 必須保持每筆記錄的獨立 epoch_datetime，Stage 2 直接使用此時間
- Stage 2 **禁止重新解析 TLE**，必須使用 Stage 1 提供的 epoch_datetime

#### 4. **數據標準化**
- **衛星數據結構**: 標準化衛星記錄格式
- **元數據組織**: 完整的處理元數據
- **品質標記**: A/B/C/F 數據品質評級

### ❌ **明確排除職責** (移至 Stage 2)
- SGP4/SDP4 軌道計算
- 座標系統轉換 (TEME→ITRF→WGS84)
- 可見性分析和篩選
- 仰角、方位角、距離計算

## 🔍 驗證框架

### 5項專用驗證檢查
1. **tle_format_validation** - TLE 格式嚴格驗證
   - 69字符長度檢查
   - 行號正確性 ('1', '2')
   - NORAD ID 一致性

2. **tle_checksum_verification** - Checksum 完整驗證
   - Modulo 10 官方算法完整實作
   - 所有行的校驗和檢查 (Line 1 & Line 2)
   - 要求: 95% 以上通過率
   - 當前實測: 100% 通過率

3. **data_completeness_check** - 數據完整性檢查
   - 必要字段存在性驗證
   - 衛星數據結構完整性
   - 元數據完整性評估

4. **time_base_establishment** - 時間基準建立驗證
   - 驗證不存在統一時間基準字段（符合獨立時間原則）
   - 驗證每顆衛星都有獨立的 epoch_datetime
   - 時間格式標準化檢查（ISO 8601, UTC, 微秒精度）

5. **satellite_data_structure** - 衛星數據結構驗證
   - 關鍵字段完整性檢查
   - 數據類型正確性驗證
   - 結構一致性檢查

### 驗證等級標準
- **A+ 級**: 100% 檢查通過，完美數據品質
- **A 級**: 95%+ 檢查通過，優秀數據品質
- **B 級**: 80%+ 檢查通過，良好數據品質
- **C 級**: 70%+ 檢查通過，可用數據品質
- **F 級**: <70% 檢查通過，不可用數據

## 📊 標準化輸出格式

### ProcessingResult 結構
```python
ProcessingResult(
    status=ProcessingStatus.SUCCESS,
    data={
        'stage': 1,
        'stage_name': 'refactored_tle_data_loading',
        'satellites': [...],  # 9,040 顆衛星數據列表
        'metadata': {
            # ✅ 時間基準政策 (每顆衛星獨立時間)
            'individual_epoch_processing': True,
            'time_base_source': 'individual_tle_epochs',
            'epoch_time_range': {
                'earliest': '2025-09-25T00:23:51.721440+00:00',
                'latest': '2025-09-29T08:00:01.999872+00:00',
                'span_days': 4,
                'total_individual_epochs': 9040
            },

            # 時間品質度量
            'time_quality_metrics': {
                'epoch_precision_microseconds': True,
                'utc_timezone_compliance': True,
                'iso8601_format': True
            },

            # 處理統計
            'total_satellites': 9040,
            'processing_duration_seconds': 0.560174,
            'time_reference_established': True,

            # 學術標準合規
            'academic_compliance': {
                'real_tle_data': True,
                'official_source': 'Space-Track.org',
                'no_simplified_algorithms': True,
                'no_estimated_values': True
            },

            # ✅ 星座配置 (Stage 2/4 需求) - 2025-09-30 新增
            'constellation_configs': {
                'starlink': {
                    'orbital_period_range_minutes': [90, 95],
                    'typical_altitude_km': 550,
                    'service_elevation_threshold_deg': 5.0,
                    'expected_visible_satellites': [10, 15],
                    'candidate_pool_size': [200, 500],
                    'orbital_characteristics': 'LEO_low'
                },
                'oneweb': {
                    'orbital_period_range_minutes': [109, 115],
                    'typical_altitude_km': 1200,
                    'service_elevation_threshold_deg': 10.0,
                    'expected_visible_satellites': [3, 6],
                    'candidate_pool_size': [50, 100],
                    'orbital_characteristics': 'LEO_high'
                }
            },

            # ✅ 研究配置 (Stage 3/4 需求) - 2025-09-30 新增
            'research_configuration': {
                'observation_location': {
                    'name': 'NTPU',
                    'latitude_deg': 24.9442,
                    'longitude_deg': 121.3714,
                    'altitude_m': 0,
                    'coordinates': "24°56'39\"N 121°22'17\"E"
                },
                'analysis_method': 'offline_historical_tle',
                'computation_type': 'full_orbital_period_analysis',
                'research_goals': [
                    'dynamic_satellite_pool_planning',
                    'time_space_staggered_coverage',
                    '3gpp_ntn_handover_events',
                    'reinforcement_learning_training'
                ]
            },

            # ✅ 星座統計 - 2025-09-30 新增
            'constellation_statistics': {
                'starlink': {'count': 8389},
                'oneweb': {'count': 651}
            },

            # 重構標記
            'refactored_version': True,
            'interface_compliance': True
        },
        'processing_stats': {...}
    },
    metadata={...},
    errors=[],
    warnings=[],
    metrics=ProcessingMetrics(...)
)
```

### 衛星數據格式
```python
satellite = {
    # 基本信息
    'name': 'STARLINK-1008',
    'constellation': 'starlink',
    'satellite_id': '44714',
    'norad_id': '44714',

    # TLE 數據 (69 字符官方標準，已修復 checksum)
    'tle_line1': '1 44714U 19074B   25272.21657815  .00017278  00000+0  11769-2 0  9995',
    'tle_line2': '2 44714  53.0521 191.5010 0001330  86.2947 273.8195 15.06371849324411',
    'line1': '1 44714U 19074B   25272.21657815...',  # 別名，與 tle_line1 相同
    'line2': '2 44714  53.0521 191.5010...',        # 別名，與 tle_line2 相同

    # 🚨 CRITICAL: 獨立時間基準 (Stage 2 必須使用)
    'epoch_datetime': '2025-09-29T05:11:52.352160+00:00',  # ISO 8601 格式，微秒精度

    # 來源信息
    'source_file': 'data/tle_data/starlink/tle/starlink_20250929.tle'
}
```

### 📤 下游階段數據使用說明

#### Stage 2: 軌道狀態傳播層
**使用的數據**:
- ✅ `satellites[].epoch_datetime` - **零重複解析 TLE**，直接使用 Stage 1 提供的時間基準
- ✅ `satellites[].tle_line1/tle_line2` - 69 字符標準 TLE，用於 Skyfield SGP4 傳播
- ✅ `satellites[].constellation` - 星座歸屬，用於分離計算
- ✅ `metadata.constellation_configs[].orbital_period_range_minutes` - 動態時間窗口規劃

**數據流範例**:
```python
for satellite in stage1_result.data['satellites']:
    epoch_dt = datetime.fromisoformat(satellite['epoch_datetime'])
    # 基於此 epoch 進行 SGP4 時間序列計算
    orbital_states = sgp4_propagate(
        tle_line1=satellite['tle_line1'],
        tle_line2=satellite['tle_line2'],
        epoch_time=epoch_dt,
        time_window_minutes=112  # 從 constellation_configs 獲取
    )
```

#### Stage 3: 座標轉換層
**使用的數據**:
- ✅ `metadata.research_configuration.observation_location` - NTPU 觀測點座標
  - `latitude_deg: 24.9442°N`
  - `longitude_deg: 121.3714°E`
  - `altitude_m: 0`
- 用於 TEME → WGS84 → 地平座標系統轉換

**數據流範例**:
```python
observer_location = stage1_result.metadata['research_configuration']['observation_location']
observer = wgs84.latlon(
    observer_location['latitude_deg'],
    observer_location['longitude_deg'],
    observer_location['altitude_m']
)
# 進行座標轉換...
```

#### Stage 4: 鏈路可行性分析層
**使用的數據**:
- ✅ `metadata.constellation_configs[].service_elevation_threshold_deg` - 星座特定仰角門檻
  - Starlink: 5.0° (LEO_low 特性)
  - OneWeb: 10.0° (LEO_high 特性)
- ✅ `metadata.constellation_configs[].typical_altitude_km` - 鏈路預算計算
- ✅ `metadata.constellation_configs[].expected_visible_satellites` - 候選池規劃

**數據流範例**:
```python
constellation_config = stage1_result.metadata['constellation_configs']['starlink']
elevation_threshold = constellation_config['service_elevation_threshold_deg']  # 5.0°

# 星座感知的可見性篩選
if satellite['constellation'] == 'starlink':
    visible = elevation_deg >= 5.0 and 200 <= distance_km <= 2000
elif satellite['constellation'] == 'oneweb':
    visible = elevation_deg >= 10.0 and 200 <= distance_km <= 2000
```

#### Stage 5: 信號品質分析層
**使用的數據**:
- ✅ 間接使用 `metadata.constellation_configs` - 星座特定配置影響信號模型
  - `typical_altitude_km` - 用於路徑損耗計算基準
  - `service_elevation_threshold_deg` - 影響大氣衰減模型選擇
- Stage 5 主要依賴 Stage 4 的可連線衛星池，Stage 1 配置透過前階段傳遞

**數據流範例**:
```python
# Stage 5 透過 Stage 4 間接使用 Stage 1 配置
constellation_configs = stage1_result.metadata['constellation_configs']

for satellite in connectable_satellites:
    constellation = satellite['constellation']
    typical_altitude = constellation_configs[constellation]['typical_altitude_km']

    # 基於星座特定高度優化信號計算
    if typical_altitude < 600:  # Starlink LEO_low
        atmospheric_model = 'low_orbit_optimized'
    elif typical_altitude > 1000:  # OneWeb LEO_high
        atmospheric_model = 'mid_orbit_standard'
```

#### Stage 6: 研究數據生成與優化層
**使用的數據**:
- ✅ `metadata.constellation_configs[].expected_visible_satellites` - **動態衛星池規劃驗證核心**
  - Starlink: `[10, 15]` - 驗證時空錯置池是否維持目標範圍
  - OneWeb: `[3, 6]` - 驗證極軌道覆蓋是否滿足需求
- ✅ `metadata.constellation_configs[].candidate_pool_size` - 候選池規模驗證
  - Starlink: `[200, 500]` 顆候選 - 確保足夠的輪替衛星
  - OneWeb: `[50, 100]` 顆候選 - 極軌道覆蓋特性驗證
- ✅ `metadata.constellation_configs[].orbital_characteristics` - 研究場景分類
  - `LEO_low` (Starlink) - 高速移動、短時可見、頻繁換手場景
  - `LEO_high` (OneWeb) - 中速移動、較長可見、穩定覆蓋場景
- ✅ `metadata.research_configuration.research_goals` - 研究目標對齊驗證

**數據流範例**:
```python
# Stage 6 動態衛星池規劃驗證
constellation_configs = stage1_result.metadata['constellation_configs']
research_goals = stage1_result.metadata['research_configuration']['research_goals']

# 1. 驗證 Starlink 池維持目標
starlink_config = constellation_configs['starlink']
starlink_target_min = starlink_config['expected_visible_satellites'][0]  # 10
starlink_target_max = starlink_config['expected_visible_satellites'][1]  # 15

connectable_starlink_count = len(connectable_satellites['starlink'])
starlink_pool_met = starlink_target_min <= connectable_starlink_count <= starlink_target_max

# 2. 驗證 OneWeb 池維持目標
oneweb_config = constellation_configs['oneweb']
oneweb_target_min = oneweb_config['expected_visible_satellites'][0]  # 3
oneweb_target_max = oneweb_config['expected_visible_satellites'][1]  # 6

connectable_oneweb_count = len(connectable_satellites['oneweb'])
oneweb_pool_met = oneweb_target_min <= connectable_oneweb_count <= oneweb_target_max

# 3. 動態衛星池規劃報告
pool_planning_report = {
    'starlink_pool': {
        'target_range': {'min': starlink_target_min, 'max': starlink_target_max},
        'current_count': connectable_starlink_count,
        'target_met': starlink_pool_met,
        'candidate_pool_size': starlink_config['candidate_pool_size'],
        'orbital_characteristics': starlink_config['orbital_characteristics']
    },
    'oneweb_pool': {
        'target_range': {'min': oneweb_target_min, 'max': oneweb_target_max},
        'current_count': connectable_oneweb_count,
        'target_met': oneweb_pool_met,
        'candidate_pool_size': oneweb_config['candidate_pool_size'],
        'orbital_characteristics': oneweb_config['orbital_characteristics']
    },
    'research_goals_alignment': {
        'dynamic_satellite_pool_planning': starlink_pool_met and oneweb_pool_met,
        'time_space_staggered_coverage': True,  # 基於時空錯置原理
        '3gpp_ntn_handover_events': True,  # A4/A5/D2 事件生成
        'reinforcement_learning_training': True  # ML 訓練數據生成
    }
}

# 4. 驗證研究目標達成
if 'dynamic_satellite_pool_planning' in research_goals:
    assert pool_planning_report['research_goals_alignment']['dynamic_satellite_pool_planning'], \
        f"動態衛星池規劃未達標: Starlink {connectable_starlink_count}顆 (目標 {starlink_target_min}-{starlink_target_max}), " \
        f"OneWeb {connectable_oneweb_count}顆 (目標 {oneweb_target_min}-{oneweb_target_max})"

# 5. 時空錯置效果分析
if starlink_pool_met:
    # 基於 orbital_characteristics 分析
    if starlink_config['orbital_characteristics'] == 'LEO_low':
        # 高速移動場景：預期頻繁換手，短時服務窗口
        expected_handover_frequency = 'high'  # 每小時 8-12 次
        expected_service_duration = 'short'   # 3-8 分鐘
```

### 🔄 數據完整性保證

✅ **所有必要欄位已提供**: Stage 2/3/4/5/6 所需的所有數據都包含在 Stage 1 輸出中
✅ **TLE 格式標準**: 嚴格 69 字符 NORAD 標準，Checksum 已修復為官方 Modulo 10 算法
✅ **時間基準明確**: 每顆衛星獨立 epoch_datetime，ISO 8601 格式，微秒精度
✅ **配置驅動設計**: constellation_configs 支援動態星座擴展，覆蓋所有下游階段需求
✅ **研究目標對齊**: research_configuration 完整對應 final.md 核心研究需求
✅ **學術合規**: 無模擬數據、無簡化算法、無估計值

### 📊 **下游階段配置依賴總覽**

| 配置項目 | Stage 2 | Stage 3 | Stage 4 | Stage 5 | Stage 6 |
|---------|---------|---------|---------|---------|---------|
| **epoch_datetime** | ✅ 核心 | 傳遞 | 傳遞 | 傳遞 | 傳遞 |
| **constellation** | ✅ 分離 | 傳遞 | ✅ 篩選 | ✅ 模型 | ✅ 驗證 |
| **orbital_period_range** | ✅ 時間窗口 | - | - | - | 傳遞 |
| **service_elevation_threshold** | - | - | ✅ 門檻 | ✅ 模型 | 傳遞 |
| **expected_visible_satellites** | - | - | ✅ 規劃 | - | ✅ 驗證 |
| **candidate_pool_size** | - | - | - | - | ✅ 驗證 |
| **observation_location** | - | ✅ 轉換 | ✅ 計算 | - | 傳遞 |
| **research_goals** | - | - | - | - | ✅ 對齊 |

**說明**:
- ✅ **核心**: 該階段的主要使用
- ✅ **分離/篩選/驗證**: 該階段的關鍵功能
- **傳遞**: 透過前階段傳遞給後續階段

## ⚡ 性能指標

### 實測性能 (當前狀態)
- **處理時間**: ~0.56秒 (9,040顆衛星)
- **處理速度**: ~16,143顆/秒
- **記憶體使用**: < 200MB
- **驗證成功率**: 100% (A+級品質)
- **快照生成**: < 0.01秒

### 與 Stage 2 集成
- **數據訪問**: `stage1_result.data`
- **兼容性**: 100% 向後兼容
- **傳遞格式**: 標準字典結構
- **時間基準**: 完整繼承機制

## 🚀 使用方式與配置

### 標準調用方式
```python
from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor

# 創建處理器（推薦使用工廠函數）
processor = create_stage1_processor(config)

# 執行處理
result = processor.execute()  # 返回 ProcessingResult

# 驗證檢查
validation = processor.run_validation_checks(result.data)

# 保存快照
snapshot_saved = processor.save_validation_snapshot(result.data)

# Stage 2 數據訪問
stage2_input = result.data  # 提取數據部分
```

### 配置選項

**最小配置**（腳本實際使用）:
```python
config = {
    'sample_mode': False,  # 生產模式：載入全部 9,040 顆衛星
    'sample_size': 500     # 僅在 sample_mode=True 時有效
}
```

**完整配置**（可選，處理器有智能默認值）:
```python
config = {
    # 基本配置
    'sample_mode': False,  # False=生產模式, True=測試模式
    'sample_size': 500,    # 測試模式時的衛星數量

    # 以下為可選配置，處理器會使用內建默認值
    'tle_validation_config': {
        'strict_format_check': True,
        'checksum_verification': True,
        'line_length_check': True,
        'required_fields_check': True
    },
    'time_config': {
        'precision_seconds': 1e-6,  # 微秒精度
        'output_format': 'iso_8601',
        'timezone': 'UTC'
    }
}
```

## 📋 部署與驗證

### 部署檢驗標準
**成功指標**:
- [ ] ProcessingResult 正確返回
- [ ] 5項驗證檢查全部通過 (100% success_rate)
- [ ] 快照文件正常生成 (`validation_passed: true`)
- [ ] Stage 2 數據接收正常
- [ ] 處理時間 < 1秒
- [ ] 衛星數據數量: 9,040顆

### 測試命令
```bash
# 完整系統測試
python scripts/run_six_stages_with_validation.py --stage 1

# 檢查快照文件
cat data/validation_snapshots/stage1_validation.json | jq '.validation_passed'

# 驗證數據數量
cat data/validation_snapshots/stage1_validation.json | jq '.data_summary.satellite_count'
```

## 🚨 故障排除

### 常見問題
1. **TLE數據過期**
   - 檢查: TLE檔案最後修改時間
   - 解決: 執行增量更新腳本

2. **格式驗證失敗**
   - 檢查: TLE格式完整性
   - 解決: 重新下載TLE數據

3. **時間基準問題**
   - 檢查: metadata中時間基準字段
   - 解決: 確認TLE epoch時間解析正確

### 診斷指令
```bash
# 檢查TLE數據狀態
find data/tle_data -name '*.tle' -exec ls -la {} \;

# 驗證處理器狀態
python -c "
from stages.stage1_orbital_calculation.stage1_main_processor import Stage1MainProcessor
print('✅ Stage 1 處理器載入正常')
"

# 檢查驗證快照
python -c "
import json
with open('data/validation_snapshots/stage1_validation.json', 'r') as f:
    data = json.load(f)
    print(f'驗證狀態: {data.get(\"validation_passed\", False)}')
    print(f'衛星數量: {data.get(\"data_summary\", {}).get(\"satellite_count\", 0)}')
    print(f'重構版本: {data.get(\"refactored_version\", False)}')
"
```

## 🎯 學術標準合規

### Grade A 強制要求
- **✅ 真實數據**: Space-Track.org 官方 TLE 數據
- **✅ 完整驗證**: 5項專用驗證檢查
- **✅ 時間基準**: 100% 使用 TLE epoch 時間
- **✅ 格式標準**: 嚴格遵循 NORAD TLE 格式
- **✅ 精度保證**: 微秒級時間精度
- **✅ 獨立時間**: 每筆記錄保持獨立的 epoch_datetime

### 零容忍項目
- **❌ 簡化算法**: 絕不允許回退到簡化實現
- **❌ 估算值**: 禁止使用任何估算或假設值
- **❌ 模擬數據**: 必須使用真實 TLE 數據
- **❌ 當前時間**: 禁止使用系統當前時間作為計算基準
- **❌ 統一時間基準**: 禁止為不同 epoch 的 TLE 創建統一時間基準
- **❌ 文件時間**: 禁止使用文件日期替代記錄內部 epoch 時間

---

**文檔版本**: v1.0 (統一版)
**程式版本**: Stage1MainProcessor (重構完成版)
**合規狀態**: ✅ Grade A 學術標準
**維護負責**: Orbit Engine Team