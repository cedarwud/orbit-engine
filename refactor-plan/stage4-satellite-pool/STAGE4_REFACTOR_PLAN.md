# 🛰️ Stage 4: 衛星池分析優化計劃

## 📋 階段概覽

**目標**：澄清動態衛星池概念，實現時空錯置原理，優化衛星池分析邏輯

**時程**：第3週後半 (3個工作日)

**優先級**：⚠️ 中等風險 - 概念澄清

**現狀問題**：自建衛星池分析概念需澄清，缺乏明確的動態池規劃理論

## 🎯 重構目標

### 核心目標
- ✅ **概念澄清**: 明確定義動態衛星池vs靜態篩選的區別
- ✅ **時空錯置實現**: 實現空間多軌道面+時間差的覆蓋策略
- ✅ **星座感知**: 分別處理Starlink/OneWeb的不同池狀態要求
- ✅ **連續覆蓋驗證**: 確保95%+時間無服務中斷空窗

### 學術創新要求 (基於 docs/final.md)
- **動態衛星池**: 數百顆衛星協同輪替，維持指定數量可見
- **Starlink池狀態**: 任意時刻保持10-15顆衛星可見 (5°仰角門檻)
- **OneWeb池狀態**: 任意時刻保持3-6顆衛星可見 (10°仰角門檻)
- **覆蓋要求**: 各自軌道週期內95%+時間滿足池狀態

## 🔧 技術實現

### 動態池核心概念

#### 動態池 vs 靜態篩選
```python
# ❌ 錯誤概念：靜態篩選
def static_satellite_selection():
    """從星座中選出固定的少數衛星 - 錯誤做法"""
    selected_satellites = constellation[:15]  # 靜態選擇
    return selected_satellites

# ✅ 正確概念：動態衛星池
def dynamic_satellite_pool():
    """數百顆候選衛星協同輪替，維持穩定池狀態"""
    pool_state = maintain_satellite_count_over_time()
    return pool_state
```

#### 時空錯置原理
```python
# 空間錯置：多軌道面覆蓋
orbital_planes = {
    'plane_A': {'direction': 'west_to_east', 'satellites': [...], 'phase': 0},
    'plane_B': {'direction': 'north_to_south', 'satellites': [...], 'phase': 120},
    'plane_C': {'direction': 'northeast_to_southwest', 'satellites': [...], 'phase': 240}
}

# 時間錯置：同軌道面內衛星群時間差
time_offsets = {
    'starlink_plane_1': [0, 15, 30, 45],  # 分鐘
    'oneweb_plane_1': [0, 18, 36, 54]    # 週期較長，間隔更大
}
```

### 新架構設計

```python
# 衛星池分析架構
satellite_pool/
├── pool_manager.py             # 動態池狀態管理
├── spacetime_coordinator.py    # 時空錯置協調器
├── coverage_analyzer.py        # 覆蓋連續性分析
└── pool_validator.py           # 池狀態驗證器
```

## 📅 實施計劃 (3天)

### Day 1: 動態池管理核心
```python
# pool_manager.py 動態池核心
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class ConstellationType(Enum):
    STARLINK = "starlink"
    ONEWEB = "oneweb"

@dataclass
class PoolRequirement:
    """池狀態需求定義 - 基於研究目標"""
    constellation: ConstellationType
    min_satellites: int
    max_satellites: int
    elevation_threshold: float
    orbital_period_minutes: int
    coverage_requirement: float  # 95%+

class DynamicPoolManager:
    """動態衛星池管理器"""

    def __init__(self, ntpu_coordinates: Coordinates):
        self.ntpu_coords = ntpu_coordinates
        self.pool_requirements = self._init_pool_requirements()

    def _init_pool_requirements(self) -> Dict[ConstellationType, PoolRequirement]:
        """初始化池需求 - 基於docs/final.md"""
        return {
            ConstellationType.STARLINK: PoolRequirement(
                constellation=ConstellationType.STARLINK,
                min_satellites=10,
                max_satellites=15,
                elevation_threshold=5.0,   # 5°仰角門檻 (LEO特性)
                orbital_period_minutes=95,  # 90-95分鐘週期
                coverage_requirement=0.95   # 95%覆蓋率
            ),
            ConstellationType.ONEWEB: PoolRequirement(
                constellation=ConstellationType.ONEWEB,
                min_satellites=3,
                max_satellites=6,
                elevation_threshold=10.0,  # 10°仰角門檻 (MEO特性)
                orbital_period_minutes=115, # 109-115分鐘週期
                coverage_requirement=0.95   # 95%覆蓋率
            )
        }

    def analyze_dynamic_pool_state(self, constellation: ConstellationType,
                                 candidate_satellites: List[SatelliteCoordinates],
                                 time_window_minutes: int) -> PoolAnalysisResult:
        """分析動態衛星池狀態 - 完整軌道週期"""

        requirement = self.pool_requirements[constellation]
        pool_timeline = []

        # 完整軌道週期分析
        for minute in range(time_window_minutes):
            current_time_satellites = [
                sat for sat in candidate_satellites
                if sat.time.minute == minute  # 簡化的時間匹配
            ]

            # 計算當前時刻可見衛星
            visible_satellites = self._filter_visible_satellites(
                current_time_satellites,
                requirement.elevation_threshold
            )

            # 檢查池狀態是否滿足需求
            visible_count = len(visible_satellites)
            pool_satisfied = (
                requirement.min_satellites <= visible_count <= requirement.max_satellites
            )

            pool_timeline.append(PoolTimePoint(
                time_minute=minute,
                visible_satellites=visible_satellites,
                visible_count=visible_count,
                requirement_satisfied=pool_satisfied,
                constellation=constellation
            ))

        return PoolAnalysisResult(
            constellation=constellation,
            timeline=pool_timeline,
            coverage_ratio=self._calculate_coverage_ratio(pool_timeline),
            requirement_met=self._validate_coverage_requirement(pool_timeline, requirement)
        )

    def _filter_visible_satellites(self, satellites: List[SatelliteCoordinates],
                                 elevation_threshold: float) -> List[SatelliteCoordinates]:
        """篩選可見衛星 - 基於仰角門檻"""

        visible = []
        for satellite in satellites:
            # 基礎可見性檢查 (仰角 > 0°)
            if satellite.elevation > 0:
                # 星座特定服務門檻檢查
                if satellite.elevation >= elevation_threshold:
                    # 鏈路預算約束檢查 (200-2000km)
                    if 200 <= satellite.distance_km <= 2000:
                        visible.append(satellite)

        return visible
```

### Day 2: 時空錯置協調器
```python
# spacetime_coordinator.py 時空錯置實現
class SpacetimeCoordinator:
    """時空錯置協調器 - 實現連續覆蓋策略"""

    def __init__(self):
        self.orbital_planes = {}
        self.time_offset_strategies = {}

    def analyze_spatial_displacement(self, satellites: List[SatelliteCoordinates]) -> SpatialAnalysis:
        """分析空間錯置 - 多軌道面覆蓋"""

        # 按軌道面分組衛星 (簡化實現：按方位角分組)
        orbital_planes = self._group_by_orbital_direction(satellites)

        coverage_analysis = {}
        for direction, sats in orbital_planes.items():
            coverage_analysis[direction] = {
                'satellite_count': len(sats),
                'average_elevation': np.mean([s.elevation for s in sats]),
                'coverage_direction': direction,
                'pass_frequency': self._estimate_pass_frequency(sats)
            }

        return SpatialAnalysis(
            orbital_planes=coverage_analysis,
            spatial_diversity_score=len(orbital_planes),
            coverage_completeness=self._assess_coverage_completeness(coverage_analysis)
        )

    def _group_by_orbital_direction(self, satellites: List[SatelliteCoordinates]) -> Dict:
        """按軌道方向分組衛星"""

        direction_groups = {
            'north_south': [],
            'west_east': [],
            'northeast_southwest': [],
            'northwest_southeast': []
        }

        for satellite in satellites:
            # 根據方位角判斷軌道方向 (簡化邏輯)
            azimuth = satellite.azimuth
            if 315 <= azimuth or azimuth < 45:
                direction_groups['north_south'].append(satellite)
            elif 45 <= azimuth < 135:
                direction_groups['west_east'].append(satellite)
            elif 135 <= azimuth < 225:
                direction_groups['northeast_southwest'].append(satellite)
            else:
                direction_groups['northwest_southeast'].append(satellite)

        return {k: v for k, v in direction_groups.items() if v}  # 移除空組

    def plan_temporal_displacement(self, constellation: ConstellationType,
                                 orbital_period_minutes: int) -> TemporalPlan:
        """規劃時間錯置 - 同軌道面內時間差安排"""

        if constellation == ConstellationType.STARLINK:
            # Starlink: 短週期，密集時間安排
            time_intervals = [0, 15, 30, 45, 60, 75, 90]  # 每15分鐘一批
        else:  # OneWeb
            # OneWeb: 長週期，較大時間間隔
            time_intervals = [0, 18, 36, 54, 72, 90, 108]  # 每18分鐘一批

        return TemporalPlan(
            constellation=constellation,
            time_intervals=time_intervals,
            total_groups=len(time_intervals),
            coverage_strategy="時間錯置輪替"
        )

    def validate_continuous_coverage(self, pool_timeline: List[PoolTimePoint]) -> CoverageValidation:
        """驗證時空錯置是否確保連續覆蓋"""

        coverage_gaps = []
        total_time_points = len(pool_timeline)
        satisfied_count = 0

        for i, time_point in enumerate(pool_timeline):
            if time_point.requirement_satisfied:
                satisfied_count += 1
            else:
                # 發現覆蓋空窗
                gap_start = i
                gap_duration = 1

                # 計算空窗持續時間
                while (i + gap_duration < total_time_points and
                       not pool_timeline[i + gap_duration].requirement_satisfied):
                    gap_duration += 1

                coverage_gaps.append(CoverageGap(
                    start_minute=gap_start,
                    duration_minutes=gap_duration,
                    severity="high" if gap_duration > 2 else "low"
                ))

        coverage_ratio = satisfied_count / total_time_points

        return CoverageValidation(
            coverage_ratio=coverage_ratio,
            requirement_met=coverage_ratio >= 0.95,  # 95%要求
            coverage_gaps=coverage_gaps,
            max_gap_duration=max([gap.duration_minutes for gap in coverage_gaps]) if coverage_gaps else 0,
            continuous_coverage_achieved=len(coverage_gaps) == 0
        )
```

### Day 3: 覆蓋分析與驗證
```python
# coverage_analyzer.py 覆蓋分析
class CoverageAnalyzer:
    """覆蓋連續性分析器"""

    def __init__(self):
        self.pool_manager = DynamicPoolManager()
        self.spacetime_coordinator = SpacetimeCoordinator()

    def analyze_constellation_coverage(self, constellation: ConstellationType,
                                     satellite_coordinates: List[SatelliteCoordinates]) -> ConstellationCoverage:
        """分析星座覆蓋能力"""

        requirement = self.pool_manager.pool_requirements[constellation]

        # 動態池分析
        pool_analysis = self.pool_manager.analyze_dynamic_pool_state(
            constellation,
            satellite_coordinates,
            requirement.orbital_period_minutes
        )

        # 空間錯置分析
        spatial_analysis = self.spacetime_coordinator.analyze_spatial_displacement(
            satellite_coordinates
        )

        # 時間錯置規劃
        temporal_plan = self.spacetime_coordinator.plan_temporal_displacement(
            constellation,
            requirement.orbital_period_minutes
        )

        # 連續覆蓋驗證
        coverage_validation = self.spacetime_coordinator.validate_continuous_coverage(
            pool_analysis.timeline
        )

        return ConstellationCoverage(
            constellation=constellation,
            pool_analysis=pool_analysis,
            spatial_analysis=spatial_analysis,
            temporal_plan=temporal_plan,
            coverage_validation=coverage_validation,
            meets_research_requirements=self._assess_research_compliance(
                pool_analysis, coverage_validation
            )
        )

    def _assess_research_compliance(self, pool_analysis: PoolAnalysisResult,
                                  coverage_validation: CoverageValidation) -> bool:
        """評估是否符合研究需求"""

        return (
            pool_analysis.requirement_met and
            coverage_validation.requirement_met and
            coverage_validation.coverage_ratio >= 0.95
        )

# pool_validator.py 池狀態驗證
class PoolValidator:
    """池狀態驗證器 - 學術標準檢查"""

    def validate_dynamic_pool_concept(self, constellation_coverage: ConstellationCoverage) -> ValidationReport:
        """驗證動態池概念實現"""

        validation_checks = {
            'pool_state_maintained': self._check_pool_state_maintained(constellation_coverage),
            'coverage_continuity': self._check_coverage_continuity(constellation_coverage),
            'spatial_diversity': self._check_spatial_diversity(constellation_coverage),
            'temporal_coordination': self._check_temporal_coordination(constellation_coverage),
            'research_requirements': constellation_coverage.meets_research_requirements
        }

        return ValidationReport(
            constellation=constellation_coverage.constellation,
            validation_checks=validation_checks,
            overall_compliance=all(validation_checks.values()),
            recommendations=self._generate_recommendations(validation_checks)
        )

    def _check_pool_state_maintained(self, coverage: ConstellationCoverage) -> bool:
        """檢查池狀態是否穩定維持"""

        satisfied_ratio = coverage.pool_analysis.coverage_ratio
        return satisfied_ratio >= 0.95

    def _check_coverage_continuity(self, coverage: ConstellationCoverage) -> bool:
        """檢查覆蓋連續性"""

        max_gap = coverage.coverage_validation.max_gap_duration
        return max_gap <= 2  # 最大空窗不超過2分鐘
```

## 🧪 驗證測試

### 動態池概念驗證
```python
def test_dynamic_pool_vs_static_selection():
    """測試動態池vs靜態選擇的區別"""

    # 模擬500顆Starlink候選衛星
    starlink_candidates = generate_test_starlink_satellites(500)

    analyzer = CoverageAnalyzer()
    coverage_result = analyzer.analyze_constellation_coverage(
        ConstellationType.STARLINK,
        starlink_candidates
    )

    # 驗證是動態輪替而非靜態選擇
    unique_satellites = set()
    for time_point in coverage_result.pool_analysis.timeline:
        for sat in time_point.visible_satellites:
            unique_satellites.add(sat.satellite_name)

    # 應該有遠超過15顆衛星參與輪替 (證明是動態池)
    assert len(unique_satellites) > 50, "可能是靜態選擇而非動態池"

def test_coverage_requirements():
    """測試覆蓋需求達成"""

    for constellation in [ConstellationType.STARLINK, ConstellationType.ONEWEB]:
        test_data = generate_test_constellation_data(constellation)

        analyzer = CoverageAnalyzer()
        coverage = analyzer.analyze_constellation_coverage(constellation, test_data)

        # 驗證95%覆蓋要求
        assert coverage.coverage_validation.coverage_ratio >= 0.95, \
            f"{constellation}未達95%覆蓋要求"

        # 驗證池狀態要求
        if constellation == ConstellationType.STARLINK:
            # 檢查10-15顆衛星池狀態
            pass
        else:  # OneWeb
            # 檢查3-6顆衛星池狀態
            pass
```

## 📊 成功指標

### 量化指標
- **Starlink池狀態**: 95%+時間維持10-15顆可見衛星
- **OneWeb池狀態**: 95%+時間維持3-6顆可見衛星
- **覆蓋連續性**: 最大服務空窗 < 2分鐘
- **衛星輪替**: 50+顆衛星參與動態輪替 (證明非靜態選擇)

### 質化指標
- **概念清晰**: 明確區分動態池vs靜態篩選
- **理論創新**: 時空錯置原理的具體實現
- **學術價值**: 符合research goal的池規劃理論
- **可視化準備**: 為前端展示提供清晰的池狀態數據

## ⚠️ 風險控制

### 概念風險
| 風險 | 影響 | 應對策略 |
|------|------|----------|
| 動態池概念理解偏差 | 高 | 嚴格按照docs/final.md實現 |
| 時空錯置效果不明顯 | 中等 | 充分的對比測試驗證 |
| 95%覆蓋要求難達成 | 高 | 調整候選衛星數量和篩選策略 |

### 實現風險
- **算法複雜度**: 保持算法簡潔明確
- **數據依賴**: 依賴Stage 1-3提供的高質量數據
- **驗證困難**: 需要充分的測試案例驗證

---

**文檔版本**: v1.0 (修正版)
**建立日期**: 2024-01-15
**前置條件**: Stage 1-3完成 (TLE/軌道/座標數據可用)
**重點**: 動態池概念澄清，為前端視覺化準備
**下一階段**: Stage 5 - 3GPP事件檢測優化