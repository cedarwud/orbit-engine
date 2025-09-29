# 🛰️ Stage 4 新實現計畫 - 鏈路可行性評估層

**目標**: 按照 v3.0 架構和 final.md 需求，全新實現正確的 Stage 4 功能

## 🎯 實現目標

### 核心職責 (符合 final.md 需求)
1. **星座感知篩選**: Starlink 5° vs OneWeb 10° 差異化門檻
2. **地理可見性計算**: NTPU 地面站 (24°56'39"N, 121°22'17"E) 精確計算
3. **軌道週期感知**: Starlink 90-95分鐘 vs OneWeb 109-115分鐘 分別處理
4. **服務窗口計算**: 連續可見時間窗口分析
5. **動態衛星池基礎**: 為 Stage 6 提供可連線衛星池

## 🏗️ 新架構設計

### 模組化組件
```
src/stages/stage4_link_feasibility/
├── stage4_link_feasibility_processor.py     # 主處理器
├── constellation_filter.py                   # 星座感知篩選
├── ntpu_visibility_calculator.py            # NTPU 地面站可見性
├── orbital_period_analyzer.py               # 軌道週期分析
├── service_window_calculator.py             # 服務窗口計算
├── link_budget_analyzer.py                  # 鏈路預算分析
├── config_manager.py                        # 配置管理
└── __init__.py                              # 模組初始化
```

### 輔助模組
```
src/stages/stage4_link_feasibility/utils/
├── coordinate_calculator.py                 # 座標計算工具
├── time_window_utils.py                     # 時間窗口工具
├── distance_calculator.py                   # 距離計算工具
└── constants.py                             # 常數定義
```

## 📊 核心功能實現

### 1. 星座感知篩選 (constellation_filter.py)
```python
class ConstellationFilter:
    """星座感知篩選器 - 符合 final.md 需求"""

    CONSTELLATION_THRESHOLDS = {
        'starlink': {
            'min_elevation_deg': 5.0,      # final.md 第38行
            'target_satellites': (10, 15),  # final.md 第27行
            'orbital_period_min': (90, 95)  # final.md 第27行
        },
        'oneweb': {
            'min_elevation_deg': 10.0,     # final.md 第39行
            'target_satellites': (3, 6),    # final.md 第32行
            'orbital_period_min': (109, 115) # final.md 第32行
        },
        'default': {
            'min_elevation_deg': 10.0
        }
    }

    def apply_constellation_threshold(self, wgs84_data, ntpu_coordinates):
        """應用星座感知門檻篩選"""

    def classify_by_constellation(self, satellites):
        """按星座分類衛星"""

    def filter_by_elevation_threshold(self, satellites, constellation):
        """按仰角門檻篩選"""
```

### 2. NTPU 可見性計算 (ntpu_visibility_calculator.py)
```python
class NTPUVisibilityCalculator:
    """NTPU 地面站可見性計算器"""

    # 精確 NTPU 座標 (final.md 第8行)
    NTPU_COORDINATES = {
        'latitude_deg': 24.9441,    # 24°56'39"N
        'longitude_deg': 121.3714,  # 121°22'17"E
        'altitude_m': 200.0         # 估計海拔
    }

    def calculate_satellite_elevation(self, sat_wgs84, timestamp):
        """計算衛星相對於 NTPU 的仰角"""

    def is_satellite_visible(self, sat_wgs84, constellation, timestamp):
        """判斷衛星是否可見"""

    def get_visibility_windows(self, satellite_trajectory, time_range):
        """獲取可見性時間窗口"""
```

### 3. 軌道週期分析 (orbital_period_analyzer.py)
```python
class OrbitalPeriodAnalyzer:
    """軌道週期感知分析器"""

    def analyze_orbital_characteristics(self, satellite_data):
        """分析軌道特徵 - 區分不同星座的軌道週期"""

    def predict_coverage_cycles(self, satellites, time_window_hours=24):
        """預測覆蓋週期 - 符合 final.md 連續覆蓋需求"""

    def optimize_time_windows(self, constellation_type, satellites):
        """優化時間窗口 - 根據軌道週期特性"""
```

### 4. 服務窗口計算 (service_window_calculator.py)
```python
class ServiceWindowCalculator:
    """服務窗口計算器"""

    def calculate_service_windows(self, visible_satellites):
        """計算服務窗口"""

    def find_continuous_coverage(self, satellites, min_duration_minutes=30):
        """查找連續覆蓋窗口"""

    def analyze_coverage_gaps(self, service_windows):
        """分析覆蓋空隙"""
```

### 5. 主處理器 (stage4_link_feasibility_processor.py)
```python
class Stage4LinkFeasibilityProcessor(BaseStageProcessor):
    """Stage 4 鏈路可行性評估處理器"""

    def __init__(self, config=None):
        super().__init__(stage_number=4, stage_name="link_feasibility", config=config)

        # 初始化組件
        self.constellation_filter = ConstellationFilter()
        self.visibility_calculator = NTPUVisibilityCalculator()
        self.period_analyzer = OrbitalPeriodAnalyzer()
        self.window_calculator = ServiceWindowCalculator()

    def process(self, wgs84_input):
        """主處理流程"""
        # 1. 星座感知篩選
        filtered_satellites = self.constellation_filter.apply_constellation_threshold(
            wgs84_input, self.visibility_calculator.NTPU_COORDINATES
        )

        # 2. 可見性計算
        visible_satellites = self.visibility_calculator.calculate_visibility_for_all(
            filtered_satellites
        )

        # 3. 軌道週期分析
        period_analysis = self.period_analyzer.analyze_orbital_characteristics(
            visible_satellites
        )

        # 4. 服務窗口計算
        service_windows = self.window_calculator.calculate_service_windows(
            visible_satellites
        )

        # 5. 構建標準化輸出
        return self._build_output(visible_satellites, period_analysis, service_windows)
```

## 📋 標準化輸出格式

```python
stage4_output = {
    'stage': 'stage4_link_feasibility',
    'feasible_satellites': {
        'starlink': {
            'satellites': [...],          # 5°門檻通過的衛星
            'target_count': (10, 15),     # final.md 目標數量
            'current_count': int,
            'coverage_analysis': {...}
        },
        'oneweb': {
            'satellites': [...],          # 10°門檻通過的衛星
            'target_count': (3, 6),       # final.md 目標數量
            'current_count': int,
            'coverage_analysis': {...}
        }
    },
    'ntpu_analysis': {
        'ground_station': {
            'latitude_deg': 24.9441,
            'longitude_deg': 121.3714,
            'altitude_m': 200.0
        },
        'visibility_summary': {...},
        'service_windows': [...],
        'coverage_gaps': [...]
    },
    'orbital_period_analysis': {
        'starlink_periods': {...},       # 90-95分鐘週期分析
        'oneweb_periods': {...},         # 109-115分鐘週期分析
        'coverage_prediction': {...}
    },
    'metadata': {
        'processing_timestamp': str,
        'total_input_satellites': int,
        'feasible_satellites_count': int,
        'constellation_distribution': {...},
        'link_feasibility_criteria': {...}
    }
}
```

## 🔧 實現步驟

### Phase 1: 基礎架構建立
1. 建立目錄結構和基礎檔案
2. 實現配置管理和常數定義
3. 建立基礎測試框架

### Phase 2: 核心算法實現
1. 實現星座感知篩選邏輯
2. 實現 NTPU 可見性計算
3. 實現軌道週期分析

### Phase 3: 整合和優化
1. 整合所有組件到主處理器
2. 實現標準化輸出格式
3. 性能優化和測試

### Phase 4: 驗證和文檔
1. 全面測試和驗證
2. 更新相關文檔
3. 準備與其他階段的整合

## ✅ 驗證標準

### 功能驗證
- [ ] 星座感知篩選符合 final.md 門檻要求
- [ ] NTPU 地面站可見性計算準確
- [ ] 軌道週期分析區分不同星座
- [ ] 服務窗口計算合理

### 數據驗證
- [ ] Starlink 目標 10-15顆可達成
- [ ] OneWeb 目標 3-6顆可達成
- [ ] 連續覆蓋時間符合需求
- [ ] 為 Stage 5 提供正確輸入

### 性能驗證
- [ ] 處理時間 < 1秒
- [ ] 記憶體使用合理
- [ ] 算法效率符合要求

## 📂 從 Stage 3 遷移的功能

### 需要整合的現有代碼
```
# 從 stage3_coordinate_transformation 遷移:
- _geometric_elevation_calculation()      → coordinate_calculator.py
- _real_elevation_calculation()           → ntpu_visibility_calculator.py
- 星座感知門檻邏輯                         → constellation_filter.py
- 可見性篩選邏輯                          → visibility_calculator.py
```

## 🎯 與 final.md 需求的對應

| final.md 需求 | Stage 4 實現 |
|---------------|-------------|
| "Starlink 5°仰角門檻" | `ConstellationFilter.starlink.min_elevation_deg = 5.0` |
| "OneWeb 10°仰角門檻" | `ConstellationFilter.oneweb.min_elevation_deg = 10.0` |
| "10-15顆 Starlink 持續可見" | 星座感知篩選 + 服務窗口計算 |
| "3-6顆 OneWeb 持續可見" | 星座感知篩選 + 服務窗口計算 |
| "24°56'39"N, 121°22'17"E" | `NTPU_COORDINATES` 精確定義 |
| "90-95分鐘 vs 109-115分鐘" | `OrbitalPeriodAnalyzer` 週期感知 |

完成後的 Stage 4 將成為整個研究架構的關鍵基礎，為後續的信號分析和 3GPP 事件檢測提供準確的可連線衛星池。