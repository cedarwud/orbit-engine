# 📡 Stage 4: 鏈路可行性評估層 - 完整規格文檔

**最後更新**: 2025-09-28
**核心職責**: 星座感知的可連線性評估與地理可見性分析
**學術合規**: Grade A 標準，星座特定服務門檻
**接口標準**: 100% BaseStageProcessor 合規

## 📖 概述與目標

**核心職責**: 基於 WGS84 座標的星座感知鏈路可行性評估
**輸入**: Stage 3 的 WGS84 地理座標時間序列
**輸出**: 可連線衛星池（包含完整時間序列，~95-220 時間點/衛星）
**處理時間**: ~0.5-1秒 (8,995顆衛星可見性篩選)
**學術標準**: 星座感知設計，符合實際系統需求

⚠️ **關鍵數據結構說明**: Stage 4 輸出包含**完整時間序列數據**，而非單一時間點快照
```python
{
    'starlink': [
        {
            'satellite_id': 'STARLINK-1234',
            'time_series': [  # ← 完整時間序列 (~191 時間點)
                {
                    'timestamp': '2025-09-27T08:00:00Z',
                    'is_connectable': True,   # ← 此時刻可見
                    'elevation': 15.2,
                    ...
                },
                # ... 繼續 190+ 時間點
            ]
        },
        # ... 繼續 ~2000 顆候選衛星
    ]
}
```

### 🎯 Stage 4 核心價值
- **星座感知評估**: Starlink (5°) vs OneWeb (10°) 特定門檻
- **鏈路預算約束**: 200-2000km 距離範圍，確保通訊品質
- **地理可見性**: NTPU 位置的精確仰角、方位角計算
- **服務窗口**: 可連線時間段計算和優化

### 🚨 **關鍵概念：「可連線衛星池」的正確理解**

**Stage 4 輸出的「可連線衛星池」是什麼？**

```
✅ 正確理解：
可連線衛星池 = 整個軌道週期內「曾經滿足可連線條件」的候選衛星集合

範例：
- Starlink 可連線衛星池: 1845 顆候選衛星
  → 這是整個 90-95 分鐘軌道週期內，曾經經過 NTPU 上空的衛星總數
  → 包含每顆衛星的完整時間序列 time_series[]
  → 每個時間點都有 is_connectable 狀態標記

- 任意時刻可見數: 10-15 顆
  → 這是在某個特定時間點 t，is_connectable=True 的衛星數量
  → 由 Stage 6 遍歷時間序列進行驗證

❌ 錯誤理解：
"1845 顆候選衛星" ≠ "任意時刻有 1845 顆可見"
"1845 顆候選衛星" ≠ "已達成 10-15 顆可見目標"
```

**數據結構說明**:
```python
connectable_satellites = {
    'starlink': [
        {
            'satellite_id': 'STARLINK-1234',
            'time_series': [  # ← 完整時間序列
                {
                    'timestamp': '2025-09-27T08:00:00Z',
                    'is_connectable': True,   # ← 該時刻可連線
                    'elevation_deg': 15.5
                },
                {
                    'timestamp': '2025-09-27T08:00:30Z',
                    'is_connectable': True,   # ← 該時刻可連線
                    'elevation_deg': 16.2
                },
                {
                    'timestamp': '2025-09-27T08:01:00Z',
                    'is_connectable': False,  # ← 該時刻不可連線
                    'elevation_deg': 4.8      # ← 低於 5° 門檻
                }
            ]
        },
        # ... 更多候選衛星
    ]
}

# ✅ Stage 4 的職責：
# 產生候選衛星池，包含每顆衛星的完整時間序列可見性數據

# ✅ Stage 6 的職責：
# 遍歷時間序列，驗證「任意時刻維持 10-15 顆可見」的目標
```

## 🚨 重要概念修正

### ❌ **修正前的錯誤概念**
```
Stage 4: 優化處理
- 統一 10° 仰角門檻
- 通用衛星處理
- 簡單距離篩選
- 忽略星座差異
```

### ✅ **修正後的正確概念**
```
Stage 4: 鏈路可行性評估與池規劃層 (兩階段處理)

階段 4.1: 可見性篩選
- 星座特定門檻 (Starlink: 5°, OneWeb: 10°)
- 鏈路預算約束 (200-2000km)
- 地理邊界驗證
- 服務窗口計算
- 輸出: ~2000 顆候選衛星（整個軌道週期內曾經可見）

階段 4.2: 時空錯置池規劃 🔴 **CRITICAL - 必要功能**
- 從 ~2000 顆候選中優化選擇 ~500 顆
- 目標: 確保任意時刻維持 10-15 顆 Starlink 可見
- 優化算法: 時空分布優化、覆蓋連續性優化
- 輸出: ~500 顆 Starlink + ~100 顆 OneWeb 最優池

🔴 **CRITICAL**: 階段 4.2 為**必要功能**，當前為文檔規劃階段，實際代碼尚未實現
這是「動態衛星池」概念的核心算法步驟，缺少此步驟將無法保證「任意時刻維持目標數量可見」
待實際執行測試後，將根據真實數據調整數字和策略
```

**學術依據**:
> *"Satellite link feasibility assessment requires constellation-specific elevation thresholds that reflect the operational characteristics of different satellite systems. LEO constellations like Starlink can operate at lower elevation angles compared to MEO systems."*
> — Kodheli, O., et al. (2021). Satellite communications in the new space era

## 🏗️ 架構設計

### 兩階段處理架構
```
┌─────────────────────────────────────────────────────────────────────┐
│         Stage 4: 鏈路可行性評估與池規劃層 (兩階段架構)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📍 階段 4.1: 可見性篩選 (當前已實現)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │Visibility   │  │Constellation│  │Link Budget  │                │
│  │Calculator   │  │Filter       │  │Analyzer     │                │
│  │             │  │             │  │             │                │
│  │• 仰角計算    │  │• 星座識別    │  │• 距離範圍    │                │
│  │• 方位角     │  │• 特定門檻    │  │• 功率預算    │                │
│  │• 地平座標    │  │• 服務標準    │  │• 都卜勒    │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│           │              │              │                         │
│           └──────────────┼──────────────┘                         │
│                          ▼                                        │
│            輸出: ~2000 顆候選衛星（含時間序列）                     │
│                          │                                        │
│  ════════════════════════▼════════════════════════                │
│                                                                   │
│  📍 階段 4.2: 時空錯置池規劃 ⚠️ (規劃中，待實現)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │Pool         │  │Coverage     │  │Optimization │              │
│  │Selector     │  │Optimizer    │  │Validator    │              │
│  │             │  │             │  │             │              │
│  │• 時空分布    │  │• 連續性分析  │  │• 覆蓋率驗證  │              │
│  │• 候選評分    │  │• 空窗檢測    │  │• 目標達成    │              │
│  │• 優選策略    │  │• 輪替優化    │  │• 品質保證    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│           │              │              │                       │
│           └──────────────┼──────────────┘                       │
│                          ▼                                      │
│            輸出: ~500 顆 Starlink + ~100 顆 OneWeb 最優池        │
│                                                                 │
│  ┌──────────────────────────────────────────────┐              │
│  │        Stage4LinkFeasibilityProcessor        │              │
│  │        (BaseStageProcessor 合規)             │              │
│  │                                              │              │
│  │ ✅ 已實現: 階段 4.1 可見性篩選                │              │
│  │ ⚠️ 待實現: 階段 4.2 池規劃優化                │              │
│  │ • ProcessingResult 標準輸出                  │              │
│  └──────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘

⚠️ **實現狀態說明**:
- 階段 4.1 (可見性篩選): ✅ 已完整實現
- 階段 4.2 (池規劃優化): ⚠️ 規劃階段，代碼待開發
- 估算數字: 基於 final.md 需求的理論估算，待實測驗證
```

## 🎯 核心功能與職責

### ✅ **階段 4.1: 可見性篩選 (已實現)**

#### 1. **地理可見性計算**
- **NTPU 地面站**: 24°56'39"N, 121°22'17"E, 35m 海拔
- **仰角計算**: 基於 WGS84 座標的精確仰角計算
- **方位角計算**: 地平座標系統方位角
- **距離計算**: 地心距離和斜距計算

#### 2. **星座感知篩選**
- **Starlink 門檻**: 5° 最小仰角 (LEO 特性)
- **OneWeb 門檻**: 10° 最小仰角 (MEO 特性)
- **其他星座**: 10° 預設門檻
- **星座識別**: 基於 TLE 名稱和 NORAD ID 自動識別

#### 3. **鏈路預算約束**
- **最小距離**: 200km (避免多普勒過大和調度複雜性)
- **最大距離**: 2000km (確保信號強度充足)
- **地理邊界**: NTPU 服務覆蓋區域驗證
- **服務品質**: 基本通訊鏈路可行性評估

#### 4. **服務窗口計算**
- **可見時間段**: 連續可見性時間窗口
- **過境預測**: 衛星過境時間和持續時間
- **最佳觀測**: 高仰角時段識別

**階段 4.1 輸出**:
- ✅ ~2000 顆候選衛星（估算值，待實測）
- ✅ 完整時間序列數據（每顆衛星 ~95-220 時間點）
- ✅ 每個時間點的 `is_connectable` 狀態標記

### ⚠️ **階段 4.2: 時空錯置池規劃 (規劃中，待實現)**

#### 5. **時空分布優化**
- **候選池輸入**: ~2000 顆 (來自階段 4.1)
- **優化目標**: 確保任意時刻維持 10-15 顆 Starlink 可見
- **空間分布**: 選擇不同軌道面的衛星，確保全方向覆蓋
- **時間交錯**: 選擇過境時間互補的衛星，確保連續覆蓋

#### 6. **覆蓋連續性優化**
- **時間窗分析**: 遍歷整個軌道週期的每個時間點
- **可見數量驗證**: 每個時刻計算 `count(is_connectable=True)`
- **空窗檢測**: 識別覆蓋率低於目標的時間段
- **補充策略**: 增加額外衛星填補覆蓋空窗

#### 7. **優化算法** (待設計)
- **方法選項 A**: 貪心算法（快速，次優解）
- **方法選項 B**: 遺傳算法（較慢，較優解）
- **方法選項 C**: 整數規劃（精確，計算密集）
- **評估標準**: 覆蓋率 ≥95%, 任意時刻可見數在目標範圍

**階段 4.2 輸出** (估算):
- ⚠️ ~500 顆 Starlink 最優候選（待實測調整）
- ⚠️ ~100 顆 OneWeb 最優候選（待實測調整）
- ⚠️ 覆蓋率報告: 每個時間點的可見衛星數統計

### ❌ **明確排除職責** (移至後續階段)
- ❌ **信號品質**: RSRP/RSRQ/SINR 計算 (移至 Stage 5)
- ❌ **3GPP 事件**: A4/A5/D2 事件檢測 (移至 Stage 6)
- ❌ **ML 訓練**: 強化學習數據生成 (移至 Stage 6)
- ❌ **換手決策**: 智能換手算法 (移至後續階段)

## 🔍 星座感知實現

### 🚨 **CRITICAL: 星座特定門檻**

**✅ 正確的星座感知實現**:
```python
def apply_constellation_threshold(self, satellite_data, wgs84_coordinates):
    """星座感知的仰角門檻篩選"""

    constellation_thresholds = {
        'starlink': 5.0,    # LEO 低軌，可用較低仰角
        'oneweb': 10.0,     # MEO 中軌，需要較高仰角
        'default': 10.0     # 其他星座預設
    }

    feasible_satellites = []

    for satellite in satellite_data:
        # 識別星座
        constellation = self._identify_constellation(satellite['name'])
        threshold = constellation_thresholds.get(constellation, 10.0)

        # 計算仰角
        elevation = self._calculate_elevation(
            satellite_coords=wgs84_coordinates[satellite['id']],
            observer_location=self.ntpu_location
        )

        # 應用星座特定門檻
        if elevation >= threshold:
            satellite['elevation_deg'] = elevation
            satellite['constellation'] = constellation
            satellite['threshold_applied'] = threshold
            feasible_satellites.append(satellite)

    return feasible_satellites

def _identify_constellation(self, satellite_name):
    """基於衛星名稱識別星座"""
    name_lower = satellite_name.lower()

    if 'starlink' in name_lower:
        return 'starlink'
    elif 'oneweb' in name_lower:
        return 'oneweb'
    elif 'kuiper' in name_lower:
        return 'kuiper'
    else:
        return 'other'
```

**❌ 絕對禁止的統一門檻**:
```python
# 禁止！不得使用統一仰角門檻
def uniform_elevation_filter(satellites):
    threshold = 10.0  # 忽略星座差異
    return [sat for sat in satellites if sat['elevation'] >= threshold]
```

### 星座特定門檻設計依據

| 星座 | 門檻 | 軌道高度 | 設計依據 |
|------|------|----------|----------|
| **Starlink** | 5° | ~550km LEO | 低軌快速移動，短時可見，需降低門檻增加覆蓋 |
| **OneWeb** | 10° | ~1200km MEO | 中軌較穩定，較長可見，可用較高門檻確保品質 |
| **其他** | 10° | 變動 | 保守策略，確保通訊品質 |

## 🔄 數據流：上游依賴與下游使用

### 📥 上游依賴 (Stage 3 → Stage 4)

#### 從 Stage 3 接收的數據
**必要輸入數據**:
- ✅ `geographic_coordinates[satellite_id]` - 每顆衛星的 WGS84 地理座標
  - `time_series[]` - WGS84 座標時間序列
    - `timestamp` - UTC 時間戳記
    - `latitude_deg` - WGS84 緯度 (-90 to 90度)
    - `longitude_deg` - WGS84 經度 (-180 to 180度)
    - `altitude_m` - WGS84 橢球高度 (米)
    - `altitude_km` - 高度 (公里)
  - `transformation_metadata` - 座標轉換元數據
    - `coordinate_system: 'WGS84'` - 座標系統確認
    - `precision_m` - 轉換精度 (米)

**從 Stage 1 接收的配置** (透過前階段傳遞):
- ✅ `research_configuration.observation_location` - NTPU 地面站
  - `latitude_deg: 24.9442` - NTPU 緯度
  - `longitude_deg: 121.3714` - NTPU 經度
  - `altitude_m: 0` - NTPU 海拔
  - `name: 'NTPU'` - 地面站名稱

- ✅ `constellation_configs` - 星座配置
  - `starlink.service_elevation_threshold_deg: 5.0` - Starlink 門檻
  - `oneweb.service_elevation_threshold_deg: 10.0` - OneWeb 門檻
  - `starlink.expected_visible_satellites: [10, 15]` - 目標範圍
  - `oneweb.expected_visible_satellites: [3, 6]` - 目標範圍

**數據訪問範例**:
```python
from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
from stages.stage4_link_feasibility.stage4_link_feasibility_processor import Stage4LinkFeasibilityProcessor

# 執行 Stage 3
stage3_processor = Stage3CoordinateTransformProcessor(config)
stage3_result = stage3_processor.execute(stage2_result.data)

# Stage 4 訪問 Stage 3 WGS84 座標
ntpu_lat = stage1_result.data['metadata']['research_configuration']['observation_location']['latitude_deg']
ntpu_lon = stage1_result.data['metadata']['research_configuration']['observation_location']['longitude_deg']

constellation_configs = stage1_result.data['metadata']['constellation_configs']

for satellite_id, geo_data in stage3_result.data['geographic_coordinates'].items():
    # 獲取星座類型
    constellation = geo_data.get('constellation', 'other')
    elevation_threshold = constellation_configs[constellation]['service_elevation_threshold_deg']

    for time_point in geo_data['time_series']:
        # WGS84 座標 (Stage 3 輸出)
        sat_lat = time_point['latitude_deg']
        sat_lon = time_point['longitude_deg']
        sat_alt_km = time_point['altitude_km']

        # 計算可見性指標
        elevation = calculate_elevation_angle(ntpu_lat, ntpu_lon, sat_lat, sat_lon, sat_alt_km)
        azimuth = calculate_azimuth_angle(ntpu_lat, ntpu_lon, sat_lat, sat_lon)
        distance_km = calculate_slant_range(ntpu_lat, ntpu_lon, 0, sat_lat, sat_lon, sat_alt_km)

        # 星座感知的可連線性判斷
        is_connectable = (
            elevation >= elevation_threshold and
            200 <= distance_km <= 2000
        )
```

#### Stage 3 數據依賴關係
- **座標系統**: 必須是 WGS84 地理座標
  - Stage 4 的可見性計算基於 WGS84 橢球
  - 禁止使用其他座標系統 (TEME, GCRS, ECEF)
- **精度要求**: 亞米級座標精度
  - 影響仰角計算準確性 (精度要求 ±0.1°)
  - 影響距離計算準確性 (精度要求 ±100m)
- **時間同步**: UTC 時間戳記保持連續
  - 用於服務窗口計算
  - 確保時間交錯覆蓋分析準確性

### 📤 下游使用 (Stage 4 → Stage 5/6)

#### Stage 5: 信號品質分析層使用的數據
**使用的輸出**:
- ✅ `connectable_satellites` - 可連線衛星池 (按星座分類)
  - **⚠️ 重要**: 包含**完整時間序列數據**，非單一時間點快照
  - `starlink[]` - Starlink 可連線衛星列表 (完整時間序列)
  - `oneweb[]` - OneWeb 可連線衛星列表 (完整時間序列)
  - 每顆衛星包含:
    - `satellite_id` - 衛星唯一標識
    - `constellation` - 星座類型
    - **`time_series[]`** - 完整可見性時間序列 ⚠️ **關鍵數據結構**
      - `timestamp` - UTC 時間戳記 (ISO 8601格式)
      - `visibility_metrics` - 可見性指標 (每個時間點)
        - `elevation_deg` - 仰角 (度)
        - `azimuth_deg` - 方位角 (度)
        - `distance_km` - 斜距 (公里)
        - `threshold_applied` - 應用的仰角門檻
        - `is_connectable` - 當前時間點可連線狀態
      - `position` - WGS84 位置 (每個時間點)
        - `latitude_deg` - 緯度
        - `longitude_deg` - 經度
        - `altitude_km` - 高度
    - `service_window` - 整體服務窗口摘要
      - `start_time` - 窗口開始時間
      - `end_time` - 窗口結束時間
      - `duration_minutes` - 持續時間
      - `time_points_count` - 時間序列點數

- ✅ `feasibility_summary` - 可行性摘要
  - `total_connectable` - 可連線衛星總數
  - `by_constellation` - 按星座統計
    - `starlink: 1845` - Starlink 可連線數
    - `oneweb: 278` - OneWeb 可連線數

**Stage 5 數據流範例**:
```python
# Stage 5 處理器接收 Stage 4 輸出
stage5_processor = Stage5SignalAnalysisProcessor(config)
stage5_result = stage5_processor.execute(stage4_result.data)

# Stage 5 僅對可連線衛星進行信號分析
connectable_satellites = stage4_result.data['connectable_satellites']

for constellation, satellites in connectable_satellites.items():
    for satellite in satellites:
        # ⚠️ 重要: Stage 4 輸出包含完整時間序列，非單一時間點
        time_series = satellite['time_series']  # 完整時間序列數據

        # 對每個時間點進行信號品質計算
        for time_point in time_series:
            timestamp = time_point['timestamp']

            # 獲取該時間點的可見性指標 (Stage 4 輸出)
            elevation_deg = time_point['visibility_metrics']['elevation_deg']
            distance_km = time_point['visibility_metrics']['distance_km']
            is_connectable = time_point['visibility_metrics']['is_connectable']

            # 僅對可連線時間點計算信號品質
            if is_connectable:
                # 計算信號品質 (3GPP 標準)
                rsrp_dbm = calculate_rsrp_3gpp(
                    tx_power_dbw=40.0,
                    tx_gain_db=35.0,
                    rx_gain_db=calculate_rx_gain(elevation_deg),
                    distance_km=distance_km,
                    elevation_deg=elevation_deg,
                    frequency_ghz=12.5
                )

                rsrq_db = calculate_rsrq_3gpp(rsrp_dbm, interference_db, noise_db)
                sinr_db = calculate_sinr_3gpp(rsrp_dbm, interference_db, noise_db)

                # 構建時間序列信號品質數據
                signal_quality_time_series.append({
                    'timestamp': timestamp,
                    'rsrp_dbm': rsrp_dbm,
                    'rsrq_db': rsrq_db,
                    'sinr_db': sinr_db,
                    'elevation_deg': elevation_deg,
                    'distance_km': distance_km
                })
```

#### Stage 6: 研究優化層使用的數據
**使用的輸出**:
- ✅ `connectable_satellites` - 可連線衛星池 (用於動態池規劃)
  - 星座特定數量驗證: Starlink 10-15顆, OneWeb 3-6顆
  - 時空錯置分析: 基於 service_window 時間交錯
  - 覆蓋連續性: 基於 duration_minutes 確保無空窗

- ✅ `feasibility_summary.ntpu_coverage` - NTPU 覆蓋分析
  - `continuous_coverage_hours` - 連續覆蓋時數
  - `coverage_gaps_minutes` - 覆蓋空隙
  - `average_satellites_visible` - 平均可見衛星數

**Stage 6 數據流範例**:
```python
# Stage 6 處理器接收 Stage 4 輸出 (透過 Stage 5)
stage6_processor = Stage6ResearchOptimizationProcessor(config)
stage6_result = stage6_processor.execute(stage5_result.data)

# Stage 6 使用可連線衛星池進行研究數據生成
connectable_satellites = stage4_result.data['connectable_satellites']

# 動態衛星池規劃驗證
starlink_count = len(connectable_satellites['starlink'])
oneweb_count = len(connectable_satellites['oneweb'])

# 檢查是否滿足研究目標
starlink_target_met = 10 <= starlink_count <= 15
oneweb_target_met = 3 <= oneweb_count <= 6

# 3GPP NTN 事件檢測 (基於可連線衛星)
for serving_satellite in connectable_satellites['starlink'][:1]:  # 當前服務衛星
    for neighbor in connectable_satellites['starlink'][1:]:  # 鄰近候選
        # A4 事件: 鄰近衛星變得優於門檻
        if neighbor['signal_quality']['rsrp_dbm'] > -100.0:
            generate_a4_event(serving_satellite, neighbor)
```

#### Stage 5/6 間接依賴關係
**關鍵傳遞鏈**:
```
Stage 3 WGS84 座標
  → Stage 4 星座感知可見性篩選 (仰角/距離門檻)
    → Stage 5 3GPP 信號品質計算 (僅可連線衛星)
      → Stage 6 研究數據生成 (3GPP 事件 + ML 訓練)
```

**數據流效率優化**:
- Stage 4 篩選: 9040 → 2000顆衛星 (78%減少)
- Stage 5 信號計算: 僅對2000顆可連線衛星進行精確計算
- Stage 6 事件檢測: 基於篩選後的高品質候選池

### 🔄 數據完整性保證

✅ **星座感知篩選**: 基於 Stage 1 配置的差異化門檻應用
✅ **NTPU 特定分析**: 基於精確地面站座標的可見性計算
✅ **鏈路預算約束**: 200-2000km 距離範圍確保通訊可行性
✅ **服務窗口計算**: 完整的時間窗口和覆蓋連續性分析
✅ **資源集中**: 為後續階段提供高品質可連線衛星候選池

## 📊 標準化輸出格式

### ProcessingResult 結構
```python
ProcessingResult(
    status=ProcessingStatus.SUCCESS,
    data={
        'stage': 4,
        'stage_name': 'link_feasibility_assessment',
        'connectable_satellites': {
            'starlink': [
                {
                    'satellite_id': 'STARLINK-1234',
                    'name': 'STARLINK-1234',
                    'constellation': 'starlink',
                    'current_position': {
                        'latitude_deg': 25.1234,
                        'longitude_deg': 121.5678,
                        'altitude_km': 550.123
                    },
                    'visibility_metrics': {
                        'elevation_deg': 15.5,
                        'azimuth_deg': 245.7,
                        'distance_km': 750.2,
                        'threshold_applied': 5.0,
                        'is_connectable': True
                    },
                    'service_window': {
                        'start_time': '2025-09-27T08:15:00+00:00',
                        'end_time': '2025-09-27T08:23:00+00:00',
                        'duration_minutes': 8.0,
                        'max_elevation_deg': 18.2
                    }
                }
                # ... 更多 Starlink 衛星
            ],
            'oneweb': [
                # OneWeb 衛星列表，格式相同
            ],
            'other': [
                # 其他星座衛星列表
            ]
        },
        'feasibility_summary': {
            'total_connectable': 2156,
            'by_constellation': {
                'starlink': 1845,    # 10-15顆目標範圍
                'oneweb': 278,       # 3-6顆目標範圍
                'other': 33
            },
            'ntpu_coverage': {
                'continuous_coverage_hours': 23.8,
                'coverage_gaps_minutes': [2.5, 8.1],
                'average_satellites_visible': 12.3
            }
        },
        'metadata': {
            # 地面站配置
            'observer_location': {
                'latitude_deg': 24.9441,    # NTPU 精確座標
                'longitude_deg': 121.3714,
                'altitude_m': 35,
                'location_name': 'NTPU'
            },

            # 星座配置
            'constellation_config': {
                'starlink_threshold_deg': 5.0,
                'oneweb_threshold_deg': 10.0,
                'default_threshold_deg': 10.0,
                'distance_constraints': {
                    'min_distance_km': 200,
                    'max_distance_km': 2000
                }
            },

            # 處理統計
            'total_satellites_analyzed': 8995,
            'processing_duration_seconds': 0.756,
            'feasibility_analysis_complete': True,

            # 合規標記
            'constellation_aware': True,
            'ntpu_specific': True,
            'academic_standard': 'Grade_A'
        }
    },
    metadata={...},
    errors=[],
    warnings=[],
    metrics=ProcessingMetrics(...)
)
```

### 可連線衛星數據格式
```python
connectable_satellite = {
    'satellite_id': 'STARLINK-1234',
    'name': 'STARLINK-1234',
    'constellation': 'starlink',
    'norad_id': '12345',
    'visibility_metrics': {
        'elevation_deg': 15.5,      # 當前仰角
        'azimuth_deg': 245.7,       # 當前方位角
        'distance_km': 750.2,       # 斜距
        'threshold_applied': 5.0,   # 應用的門檻
        'is_connectable': True      # 可連線標記
    },
    'link_budget': {
        'within_distance_range': True,
        'min_distance_ok': True,    # > 200km
        'max_distance_ok': True,    # < 2000km
        'link_quality_estimate': 'good'
    },
    'service_window': {
        'start_time': '2025-09-27T08:15:00+00:00',
        'end_time': '2025-09-27T08:23:00+00:00',
        'duration_minutes': 8.0,
        'max_elevation_deg': 18.2,
        'window_quality': 'excellent'
    }
}
```

## ⚡ 性能指標

### 階段 4.1 性能指標 (已實現)
- **輸入**: 8,995 顆衛星（來自 Stage 3）
- **處理時間**: < 1秒（可見性計算）
- **輸出**: ~2000 顆候選衛星（估算值，待實測）
  - Starlink: ~1800 顆候選
  - OneWeb: ~200 顆候選
- **數據量**: 每顆衛星 ~95-220 時間點

### 階段 4.2 性能指標 (規劃中)
- **輸入**: ~2000 顆候選（來自階段 4.1）
- **處理時間**: 估算 2-5秒（優化算法）
- **輸出**: ~500 顆 Starlink + ~100 顆 OneWeb（估算值）
- **驗證目標**:
  - Starlink: 任意時刻 10-15 顆可見
  - OneWeb: 任意時刻 3-6 顆可見
  - 覆蓋率: ≥ 95% 時間點達標

⚠️ **估算說明**:
- 候選數量 (~2000, ~500) 基於 final.md 需求的理論估算
- 實際數字需要運行 Stage 1-4 後實測確認
- 優化算法性能取決於具體實現方法

### 與 Stage 5 集成
- **數據格式**: 最優衛星池（階段 4.2 輸出）
- **星座標記**: 完整星座識別和分類
- **傳遞方式**: ProcessingResult.data 結構
- **數據規模**: ~600 顆（相比 2000 顆減少 70%）
- **兼容性**: 為 Stage 5 信號分析準備

## 🔬 驗證框架

### 5項專用驗證檢查
1. **constellation_threshold_validation** - 星座門檻驗證
   - Starlink 5° 門檻正確應用
   - OneWeb 10° 門檻正確應用
   - 星座識別準確性檢查

2. **visibility_calculation_accuracy** - 可見性計算精度
   - 仰角計算合理性 (0°-90°)
   - 方位角計算準確性 (0°-360°)
   - 距離計算物理合理性

3. **link_budget_constraints** - 鏈路預算約束
   - 200km 最小距離檢查
   - 2000km 最大距離檢查
   - 地理邊界驗證

4. **ntpu_coverage_analysis** - NTPU 覆蓋分析
   - 連續覆蓋時間驗證
   - 衛星數量目標達成檢查
   - 覆蓋空隙時間分析

5. **service_window_optimization** - 服務窗口優化
   - 時間窗口連續性檢查
   - 最佳觀測時段識別
   - 交錯覆蓋驗證

## 🚀 使用方式與配置

### 標準調用方式
```python
from stages.stage4_link_feasibility.stage4_link_feasibility_processor import Stage4LinkFeasibilityProcessor

# 接收 Stage 3 結果
stage3_result = stage3_processor.execute()

# 創建 Stage 4 處理器
processor = Stage4LinkFeasibilityProcessor(config)

# 執行鏈路可行性評估
result = processor.execute(stage3_result.data)  # 使用 Stage 3 WGS84 數據

# 驗證檢查
validation = processor.run_validation_checks(result.data)

# Stage 5 數據準備
stage5_input = result.data  # 可連線衛星池
```

### 配置選項
```python
config = {
    'observer_config': {
        'latitude_deg': 24.9441,    # NTPU 緯度
        'longitude_deg': 121.3714,  # NTPU 經度
        'altitude_m': 35,           # NTPU 海拔
        'location_name': 'NTPU'
    },
    'constellation_config': {
        'starlink_threshold_deg': 5.0,
        'oneweb_threshold_deg': 10.0,
        'kuiper_threshold_deg': 8.0,
        'default_threshold_deg': 10.0
    },
    'link_budget_config': {
        'min_distance_km': 200,
        'max_distance_km': 2000,
        'elevation_mask_deg': 0,    # 地平線遮擋
        'atmospheric_refraction': True
    },
    'target_coverage': {
        'starlink_satellites': {'min': 10, 'max': 15},
        'oneweb_satellites': {'min': 3, 'max': 6},
        'continuous_coverage_hours': 23.5
    }
}
```

## 📋 部署與驗證

### 部署檢驗標準
**成功指標**:
- [ ] 星座特定門檻正確應用
- [ ] NTPU 地面站座標精確設定
- [ ] 2000+顆可連線衛星識別
- [ ] Starlink: 10-15顆可見範圍
- [ ] OneWeb: 3-6顆可見範圍
- [ ] > 95% NTPU 覆蓋率

### 測試命令
```bash
# 完整 Stage 4 測試
python scripts/run_six_stages_with_validation.py --stage 4

# 檢查可連線衛星數量
cat data/validation_snapshots/stage4_validation.json | jq '.feasibility_summary.total_connectable'

# 驗證星座分布
cat data/validation_snapshots/stage4_validation.json | jq '.feasibility_summary.by_constellation'
```

## 🎯 學術標準合規

### Grade A 強制要求
- **✅ 星座感知**: 基於實際系統特性的差異化門檻設計
- **✅ NTPU 特定**: 精確地面站座標和地理特性
- **✅ 鏈路預算**: 基於通訊工程原理的距離約束
- **✅ 服務標準**: 符合實際衛星通訊系統需求
- **✅ 覆蓋優化**: 連續覆蓋和時間交錯設計

### 零容忍項目
- **❌ 統一門檻**: 禁止對所有星座使用相同仰角門檻
- **❌ 忽略地理**: 禁止使用通用地面站假設
- **❌ 簡化約束**: 禁止忽略鏈路預算距離限制
- **❌ 靜態分析**: 禁止忽略服務窗口時間動態性
- **❌ 非學術假設**: 禁止使用不符合實際的系統參數

---

**文檔版本**: v4.0 (重構版)
**概念狀態**: ✅ 鏈路可行性評估 (已修正)
**學術合規**: ✅ Grade A 標準
**維護負責**: Orbit Engine Team