# 📡 Stage 4: 鏈路可行性評估層 - 完整規格文檔

**最後更新**: 2025-09-28
**核心職責**: 星座感知的可連線性評估與地理可見性分析
**學術合規**: Grade A 標準，星座特定服務門檻
**接口標準**: 100% BaseStageProcessor 合規

## 📖 概述與目標

**核心職責**: 基於 WGS84 座標的星座感知鏈路可行性評估
**輸入**: Stage 3 的 WGS84 地理座標時間序列
**輸出**: 可連線衛星池，包含星座特定門檻評估
**處理時間**: ~0.5-1秒 (8,995顆衛星可見性篩選)
**學術標準**: 星座感知設計，符合實際系統需求

### 🎯 Stage 4 核心價值
- **星座感知評估**: Starlink (5°) vs OneWeb (10°) 特定門檻
- **鏈路預算約束**: 200-2000km 距離範圍，確保通訊品質
- **地理可見性**: NTPU 位置的精確仰角、方位角計算
- **服務窗口**: 可連線時間段計算和優化

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
Stage 4: 鏈路可行性評估
- 星座特定門檻 (Starlink: 5°, OneWeb: 10°)
- 鏈路預算約束 (200-2000km)
- 地理邊界驗證
- 服務窗口計算
```

**學術依據**:
> *"Satellite link feasibility assessment requires constellation-specific elevation thresholds that reflect the operational characteristics of different satellite systems. LEO constellations like Starlink can operate at lower elevation angles compared to MEO systems."*
> — Kodheli, O., et al. (2021). Satellite communications in the new space era

## 🏗️ 架構設計

### 重構後組件架構
```
┌─────────────────────────────────────────────────────────┐
│         Stage 4: 鏈路可行性評估層 (重構版)               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Visibility   │  │Constellation│  │Link Budget  │    │
│  │Calculator   │  │Filter       │  │Analyzer     │    │
│  │             │  │             │  │             │    │
│  │• 仰角計算    │  │• 星座識別    │  │• 距離範圍    │    │
│  │• 方位角     │  │• 特定門檻    │  │• 功率預算    │    │
│  │• 地平座標    │  │• 服務標準    │  │• 都卜勒    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│           │              │              │             │
│           └──────────────┼──────────────┘             │
│                          ▼                            │
│  ┌──────────────────────────────────────────────┐    │
│  │        Stage4LinkFeasibilityProcessor        │    │
│  │        (BaseStageProcessor 合規)             │    │
│  │                                              │    │
│  │ • NTPU 地面站座標 (24.9441°N, 121.3714°E)   │    │
│  │ • 星座感知篩選邏輯                           │    │
│  │ • 服務窗口優化                               │    │
│  │ • ProcessingResult 標準輸出                  │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 🎯 核心功能與職責

### ✅ **Stage 4 專屬職責**

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
- **覆蓋優化**: 時間交錯的衛星池規劃

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

### 目標性能指標
- **處理時間**: < 1秒 (8,995顆衛星可見性分析)
- **篩選結果**: ~2000顆可連線衛星
- **Starlink 可見**: 10-15顆 (目標範圍)
- **OneWeb 可見**: 3-6顆 (目標範圍)
- **覆蓋率**: > 95% NTPU 連續覆蓋

### 與 Stage 5 集成
- **數據格式**: 可連線衛星池
- **星座標記**: 完整星座識別和分類
- **傳遞方式**: ProcessingResult.data 結構
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