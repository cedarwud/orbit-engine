# 📋 Stage 4 重構計劃 C: 動態池規劃實現

**計劃代號**: STAGE4-REFACTOR-C
**優先級**: P2 - 增強 (Enhancement)
**預估工時**: 6-8 小時
**依賴**: 計劃 A + 計劃 B 完成
**狀態**: 📝 規劃中

---

## 🎯 重構目標

實現 **階段 4.2: 時空錯置池規劃**，這是 Stage 4 的核心功能增強，確保**任意時刻維持目標數量的可見衛星**。

### 核心目標
1. ✅ 從 ~2000 顆候選衛星優化選擇 ~500 顆最優衛星
2. ✅ 確保任意時刻維持 10-15 顆 Starlink 可見
3. ✅ 確保任意時刻維持 3-6 顆 OneWeb 可見
4. ✅ 覆蓋率 ≥ 95% (時間點達標率)

---

## 📊 問題分析

### 問題背景: 「可見衛星池」的正確理解

**文檔說明** (`stage4-link-feasibility.md:43-64`):
```
可連線衛星池 = 整個軌道週期內「曾經滿足可連線條件」的候選衛星集合

範例:
- Starlink 可連線衛星池: 1845 顆候選衛星
  → 這是整個 90-95 分鐘軌道週期內，曾經經過 NTPU 上空的衛星總數
  → 包含每顆衛星的完整時間序列 time_series[]
  → 每個時間點都有 is_connectable 狀態標記

- 任意時刻可見數: 10-15 顆
  → 這是在某個特定時間點 t，is_connectable=True 的衛星數量
  → 由 Stage 6 遍歷時間序列進行驗證

❌ 錯誤理解:
"1845 顆候選衛星" ≠ "任意時刻有 1845 顆可見"
"1845 顆候選衛星" ≠ "已達成 10-15 顆可見目標"
```

**核心問題**:
- 階段 4.1 輸出 ~2000 顆候選，但**不保證任意時刻的可見數量**
- 需要**時空錯置池規劃**算法來優化選擇
- 目標是從 2000 顆中選擇 ~500 顆，使得任意時刻都有足夠可見數

---

### 時空錯置原理

**時空錯置** (Temporal-Spatial Staggering):
```
原理: 選擇不同軌道面、不同過境時間的衛星組合，
     使得當某些衛星下山時，其他衛星正在上升，
     從而確保連續覆蓋。

範例:
時間軸: |-------|-------|-------|-------|-------|
       t0      t1      t2      t3      t4      t5

衛星A: [可見---------]
衛星B:         [可見---------]
衛星C:                 [可見---------]
衛星D:                         [可見---------]

結果: t0-t5 任意時刻至少有 2-3 顆衛星可見
```

**學術依據**:
> *"LEO constellation coverage requires careful satellite pool selection to ensure continuous service availability through temporal staggering of satellite passes."*
> — Kodheli, O., et al. (2021). Satellite communications in the new space era

---

## 🛠️ 重構方案

### 任務 C.1: 時空分布分析器

#### 目標檔案
- `src/stages/stage4_link_feasibility/temporal_spatial_analyzer.py` (新建)

#### 實現步驟

**步驟 1.1: 創建 TemporalSpatialAnalyzer 類**

```python
#!/usr/bin/env python3
"""
時空分布分析器 - Stage 4.2 核心模組

分析候選衛星池的時空分布特性，為優化算法提供基礎數據
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class TemporalSpatialAnalyzer:
    """時空分布分析器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logger

        # 時間窗口配置 (默認 2 小時，30 秒間隔)
        self.time_window_hours = self.config.get('time_window_hours', 2.0)
        self.time_step_seconds = self.config.get('time_step_seconds', 30)

        self.logger.info("🕐 時空分布分析器初始化")
        self.logger.info(f"   時間窗口: {self.time_window_hours} 小時")
        self.logger.info(f"   時間步長: {self.time_step_seconds} 秒")

    def analyze_temporal_coverage(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析時間覆蓋分布

        為每個時間點統計可見衛星數量，識別覆蓋空窗

        Returns:
            {
                'time_points': [timestamp1, timestamp2, ...],
                'visible_counts': [count1, count2, ...],
                'coverage_gaps': [gap1, gap2, ...],
                'statistics': {...}
            }
        """
        self.logger.info(f"🔍 開始分析 {len(satellites)} 顆衛星的時間覆蓋...")

        # 收集所有時間點
        all_time_points = set()
        satellite_visibility_map = {}  # {sat_id: {timestamp: is_connectable}}

        for satellite in satellites:
            sat_id = satellite['satellite_id']
            time_series = satellite.get('time_series', [])

            visibility_map = {}
            for point in time_series:
                timestamp = point['timestamp']
                is_connectable = point.get('is_connectable', False)

                all_time_points.add(timestamp)
                visibility_map[timestamp] = is_connectable

            satellite_visibility_map[sat_id] = visibility_map

        # 排序時間點
        sorted_time_points = sorted(list(all_time_points))

        # 統計每個時間點的可見衛星數
        visible_counts = []
        for timestamp in sorted_time_points:
            count = sum(
                1 for sat_id, vis_map in satellite_visibility_map.items()
                if vis_map.get(timestamp, False)
            )
            visible_counts.append(count)

        # 識別覆蓋空窗 (可見數 < 目標最小值)
        coverage_gaps = self._identify_coverage_gaps(
            sorted_time_points, visible_counts, min_target=10
        )

        # 統計數據
        statistics = {
            'total_time_points': len(sorted_time_points),
            'min_visible_count': min(visible_counts) if visible_counts else 0,
            'max_visible_count': max(visible_counts) if visible_counts else 0,
            'avg_visible_count': sum(visible_counts) / len(visible_counts) if visible_counts else 0,
            'coverage_gaps_count': len(coverage_gaps),
            'coverage_ratio': sum(1 for c in visible_counts if c >= 10) / len(visible_counts) if visible_counts else 0
        }

        self.logger.info(f"📊 時間覆蓋分析完成:")
        self.logger.info(f"   時間點數: {statistics['total_time_points']}")
        self.logger.info(f"   平均可見: {statistics['avg_visible_count']:.1f} 顆")
        self.logger.info(f"   覆蓋率: {statistics['coverage_ratio']:.1%}")
        self.logger.info(f"   空窗數: {statistics['coverage_gaps_count']}")

        return {
            'time_points': sorted_time_points,
            'visible_counts': visible_counts,
            'coverage_gaps': coverage_gaps,
            'statistics': statistics,
            'satellite_visibility_map': satellite_visibility_map
        }

    def _identify_coverage_gaps(self, time_points: List[str], visible_counts: List[int],
                               min_target: int = 10) -> List[Dict[str, Any]]:
        """識別覆蓋空窗"""
        gaps = []
        in_gap = False
        gap_start_idx = 0

        for i, count in enumerate(visible_counts):
            if count < min_target:
                if not in_gap:
                    # 開始新的空窗
                    in_gap = True
                    gap_start_idx = i
            else:
                if in_gap:
                    # 結束當前空窗
                    gaps.append({
                        'start_time': time_points[gap_start_idx],
                        'end_time': time_points[i - 1],
                        'duration_points': i - gap_start_idx,
                        'min_visible': min(visible_counts[gap_start_idx:i])
                    })
                    in_gap = False

        # 處理最後一個空窗
        if in_gap:
            gaps.append({
                'start_time': time_points[gap_start_idx],
                'end_time': time_points[-1],
                'duration_points': len(time_points) - gap_start_idx,
                'min_visible': min(visible_counts[gap_start_idx:])
            })

        return gaps

    def analyze_spatial_distribution(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析空間分布

        分析衛星在軌道面的分佈，識別軌道多樣性

        Returns:
            {
                'orbital_diversity': float,  # 軌道多樣性指標
                'azimuth_distribution': {...},
                'elevation_distribution': {...}
            }
        """
        self.logger.info("🌍 開始分析空間分布...")

        # 收集方位角和仰角數據
        azimuth_samples = []
        elevation_samples = []

        for satellite in satellites:
            time_series = satellite.get('time_series', [])
            for point in time_series:
                if point.get('is_connectable', False):
                    azimuth_samples.append(point.get('azimuth_deg', 0))
                    elevation_samples.append(point.get('elevation_deg', 0))

        # 方位角分布 (8 個方向)
        azimuth_bins = self._bin_azimuth(azimuth_samples, num_bins=8)

        # 仰角分布 (3 個範圍: 低、中、高)
        elevation_bins = self._bin_elevation(elevation_samples)

        # 計算軌道多樣性 (方位角分布的均勻性)
        orbital_diversity = self._calculate_distribution_uniformity(azimuth_bins)

        self.logger.info(f"📊 空間分布分析完成:")
        self.logger.info(f"   軌道多樣性: {orbital_diversity:.2f}")

        return {
            'orbital_diversity': orbital_diversity,
            'azimuth_distribution': azimuth_bins,
            'elevation_distribution': elevation_bins
        }

    def _bin_azimuth(self, azimuth_samples: List[float], num_bins: int = 8) -> Dict[str, int]:
        """將方位角分組 (北、東北、東、東南...）"""
        bin_size = 360.0 / num_bins
        bins = {f"bin_{i}": 0 for i in range(num_bins)}

        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

        for azimuth in azimuth_samples:
            bin_idx = int(azimuth / bin_size) % num_bins
            bins[f"bin_{bin_idx}"] += 1

        # 添加方向標籤
        labeled_bins = {directions[i]: bins[f"bin_{i}"] for i in range(num_bins)}

        return labeled_bins

    def _bin_elevation(self, elevation_samples: List[float]) -> Dict[str, int]:
        """將仰角分組 (低、中、高)"""
        bins = {'low': 0, 'medium': 0, 'high': 0}

        for elevation in elevation_samples:
            if elevation < 30:
                bins['low'] += 1
            elif elevation < 60:
                bins['medium'] += 1
            else:
                bins['high'] += 1

        return bins

    def _calculate_distribution_uniformity(self, distribution: Dict[str, int]) -> float:
        """
        計算分布均勻性 (0-1, 1=完全均勻)

        使用香農熵 (Shannon Entropy) 歸一化
        """
        values = list(distribution.values())
        total = sum(values)

        if total == 0:
            return 0.0

        # 計算概率分布
        probabilities = [v / total for v in values]

        # 計算熵
        import math
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

        # 歸一化 (最大熵 = log2(num_bins))
        max_entropy = math.log2(len(distribution))
        uniformity = entropy / max_entropy if max_entropy > 0 else 0

        return uniformity


def create_temporal_spatial_analyzer(config: Dict[str, Any] = None) -> TemporalSpatialAnalyzer:
    """創建時空分布分析器實例"""
    return TemporalSpatialAnalyzer(config)
```

---

### 任務 C.2: 動態池優化算法

#### 目標檔案
- `src/stages/stage4_link_feasibility/pool_optimizer.py` (新建)

#### 實現步驟

**步驟 2.1: 創建 PoolOptimizer 類 (貪心算法版本)**

```python
#!/usr/bin/env python3
"""
動態池優化器 - Stage 4.2 核心算法

從候選衛星池中選擇最優子集，確保任意時刻維持目標可見數量
"""

import logging
from typing import Dict, Any, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class PoolOptimizer:
    """
    動態池優化器 (貪心算法版本)

    算法策略:
    1. 優先選擇覆蓋空窗的衛星
    2. 優先選擇可見時間長的衛星
    3. 優先選擇軌道多樣性好的衛星
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logger

        # 優化目標配置
        self.target_pool_size = {
            'starlink': self.config.get('starlink_pool_size', 500),
            'oneweb': self.config.get('oneweb_pool_size', 100)
        }

        self.target_visible_range = {
            'starlink': (10, 15),
            'oneweb': (3, 6)
        }

        self.logger.info("🎯 動態池優化器初始化")
        self.logger.info(f"   Starlink 目標池: {self.target_pool_size['starlink']} 顆")
        self.logger.info(f"   OneWeb 目標池: {self.target_pool_size['oneweb']} 顆")

    def optimize_satellite_pool(self, candidate_satellites: List[Dict[str, Any]],
                               constellation: str,
                               temporal_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        優化衛星池選擇

        Args:
            candidate_satellites: 候選衛星列表 (來自階段 4.1)
            constellation: 星座類型
            temporal_analysis: 時間覆蓋分析結果

        Returns:
            優化後的衛星池
        """
        self.logger.info(f"🔧 開始優化 {constellation} 衛星池...")
        self.logger.info(f"   候選數量: {len(candidate_satellites)} 顆")

        target_size = self.target_pool_size.get(constellation, 500)
        min_visible, max_visible = self.target_visible_range.get(constellation, (10, 15))

        # 步驟 1: 為每顆衛星計算評分
        satellite_scores = self._calculate_satellite_scores(
            candidate_satellites, temporal_analysis
        )

        # 步驟 2: 貪心選擇 - 迭代添加衛星直到滿足目標
        selected_satellites = []
        remaining_candidates = candidate_satellites.copy()

        while len(selected_satellites) < target_size and remaining_candidates:
            # 選擇當前得分最高的衛星
            best_satellite = max(
                remaining_candidates,
                key=lambda sat: satellite_scores[sat['satellite_id']]
            )

            selected_satellites.append(best_satellite)
            remaining_candidates.remove(best_satellite)

            # 每選擇 50 顆衛星，重新評估覆蓋情況
            if len(selected_satellites) % 50 == 0:
                coverage_check = self._evaluate_pool_coverage(
                    selected_satellites, temporal_analysis
                )

                self.logger.info(f"   進度: {len(selected_satellites)}/{target_size} 顆")
                self.logger.info(f"   當前覆蓋率: {coverage_check['coverage_ratio']:.1%}")
                self.logger.info(f"   平均可見: {coverage_check['avg_visible_count']:.1f} 顆")

                # 如果已經達標，可以提前結束
                if (coverage_check['coverage_ratio'] >= 0.95 and
                    min_visible <= coverage_check['avg_visible_count'] <= max_visible):
                    self.logger.info(f"✅ 提前達標，停止優化")
                    break

        # 最終評估
        final_coverage = self._evaluate_pool_coverage(selected_satellites, temporal_analysis)

        self.logger.info(f"✅ {constellation} 衛星池優化完成:")
        self.logger.info(f"   最終數量: {len(selected_satellites)} 顆")
        self.logger.info(f"   覆蓋率: {final_coverage['coverage_ratio']:.1%}")
        self.logger.info(f"   平均可見: {final_coverage['avg_visible_count']:.1f} 顆")

        return selected_satellites

    def _calculate_satellite_scores(self, satellites: List[Dict[str, Any]],
                                   temporal_analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        計算每顆衛星的評分

        評分因子:
        1. 可見時間長度 (40%)
        2. 覆蓋空窗貢獻 (40%)
        3. 軌道多樣性 (20%)
        """
        scores = {}
        coverage_gaps = temporal_analysis.get('coverage_gaps', [])

        for satellite in satellites:
            sat_id = satellite['satellite_id']
            time_series = satellite.get('time_series', [])

            # 因子 1: 可見時間長度
            connectable_points = sum(1 for p in time_series if p.get('is_connectable', False))
            visibility_score = connectable_points / len(time_series) if time_series else 0

            # 因子 2: 覆蓋空窗貢獻
            gap_coverage_score = self._calculate_gap_coverage_score(
                satellite, coverage_gaps
            )

            # 因子 3: 軌道多樣性 (基於方位角變化)
            diversity_score = self._calculate_diversity_score(satellite)

            # 綜合評分 (加權平均)
            total_score = (
                0.40 * visibility_score +
                0.40 * gap_coverage_score +
                0.20 * diversity_score
            )

            scores[sat_id] = total_score

        return scores

    def _calculate_gap_coverage_score(self, satellite: Dict[str, Any],
                                     coverage_gaps: List[Dict[str, Any]]) -> float:
        """計算衛星對覆蓋空窗的貢獻"""
        if not coverage_gaps:
            return 0.5  # 無空窗，返回中等評分

        time_series = satellite.get('time_series', [])
        gap_contribution = 0

        for gap in coverage_gaps:
            # 檢查衛星是否在空窗期間可見
            gap_start = gap['start_time']
            gap_end = gap['end_time']

            for point in time_series:
                if (gap_start <= point['timestamp'] <= gap_end and
                    point.get('is_connectable', False)):
                    gap_contribution += 1

        # 歸一化
        max_possible_contribution = len(coverage_gaps) * 10  # 假設每個空窗最多貢獻 10 點
        score = min(gap_contribution / max_possible_contribution, 1.0) if max_possible_contribution > 0 else 0

        return score

    def _calculate_diversity_score(self, satellite: Dict[str, Any]) -> float:
        """計算軌道多樣性評分 (基於方位角變化)"""
        time_series = satellite.get('time_series', [])

        if not time_series:
            return 0.0

        # 提取方位角
        azimuths = [p.get('azimuth_deg', 0) for p in time_series if p.get('is_connectable', False)]

        if len(azimuths) < 2:
            return 0.0

        # 計算方位角標準差 (高標準差 = 高多樣性)
        import statistics
        azimuth_std = statistics.stdev(azimuths) if len(azimuths) > 1 else 0

        # 歸一化 (最大標準差約為 180°)
        diversity_score = min(azimuth_std / 180.0, 1.0)

        return diversity_score

    def _evaluate_pool_coverage(self, selected_satellites: List[Dict[str, Any]],
                               temporal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """評估當前衛星池的覆蓋情況"""
        if not selected_satellites:
            return {
                'coverage_ratio': 0.0,
                'avg_visible_count': 0.0,
                'min_visible_count': 0,
                'max_visible_count': 0
            }

        # 重新計算時間覆蓋
        time_points = temporal_analysis['time_points']
        satellite_visibility_map = temporal_analysis['satellite_visibility_map']

        # 只考慮已選擇的衛星
        selected_ids = {sat['satellite_id'] for sat in selected_satellites}

        visible_counts = []
        for timestamp in time_points:
            count = sum(
                1 for sat_id in selected_ids
                if satellite_visibility_map.get(sat_id, {}).get(timestamp, False)
            )
            visible_counts.append(count)

        # 計算統計
        coverage_ratio = sum(1 for c in visible_counts if c >= 10) / len(visible_counts) if visible_counts else 0
        avg_visible = sum(visible_counts) / len(visible_counts) if visible_counts else 0

        return {
            'coverage_ratio': coverage_ratio,
            'avg_visible_count': avg_visible,
            'min_visible_count': min(visible_counts) if visible_counts else 0,
            'max_visible_count': max(visible_counts) if visible_counts else 0
        }


def create_pool_optimizer(config: Dict[str, Any] = None) -> PoolOptimizer:
    """創建池優化器實例"""
    return PoolOptimizer(config)
```

---

### 任務 C.3: 整合到主處理器

#### 實現步驟

**步驟 3.1: 修改 Stage4LinkFeasibilityProcessor**

```python
# stage4_link_feasibility_processor.py
from .temporal_spatial_analyzer import TemporalSpatialAnalyzer
from .pool_optimizer import PoolOptimizer

class Stage4LinkFeasibilityProcessor(BaseStageProcessor):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(stage_number=4, stage_name="link_feasibility", config=config)

        # 階段 4.1 組件
        self.constellation_filter = ConstellationFilter(config)
        self.visibility_calculator = SkyfieldVisibilityCalculator(config)

        # 階段 4.2 組件 (新增)
        self.temporal_analyzer = TemporalSpatialAnalyzer(config)
        self.pool_optimizer = PoolOptimizer(config)

        self.enable_pool_optimization = config.get('enable_pool_optimization', True)

        self.logger.info("🛰️ Stage 4 鏈路可行性評估處理器初始化完成")
        self.logger.info(f"   階段 4.2 動態池規劃: {'✅ 啟用' if self.enable_pool_optimization else '❌ 停用'}")

    def _process_link_feasibility(self, wgs84_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行主要的鏈路可行性評估流程"""

        # 階段 4.1: 可見性篩選 (計劃 A 實現)
        time_series_metrics = self._calculate_time_series_metrics(wgs84_data)
        constellation_result = self.constellation_filter.apply_constellation_filtering(...)

        # 階段 4.2: 動態池規劃 (計劃 C 實現)
        if self.enable_pool_optimization:
            optimized_pool = self._apply_pool_optimization(
                constellation_result['filtered_satellites']
            )
        else:
            optimized_pool = constellation_result['filtered_satellites']

        # 構建輸出
        return self._build_stage4_output(
            wgs84_data,
            optimized_pool,
            constellation_result
        )

    def _apply_pool_optimization(self, candidate_satellites: Dict[str, Any]) -> Dict[str, Any]:
        """應用階段 4.2 動態池規劃"""
        self.logger.info("🎯 開始階段 4.2: 動態池規劃...")

        optimized_pool = {}

        # 按星座分別優化
        for constellation in ['starlink', 'oneweb']:
            # 提取該星座的候選衛星
            constellation_candidates = [
                sat for sat_id, sat in candidate_satellites.items()
                if sat.get('constellation', '').lower() == constellation
            ]

            if not constellation_candidates:
                continue

            # 時空分布分析
            temporal_analysis = self.temporal_analyzer.analyze_temporal_coverage(
                constellation_candidates
            )

            spatial_analysis = self.temporal_analyzer.analyze_spatial_distribution(
                constellation_candidates
            )

            # 池優化
            optimized_satellites = self.pool_optimizer.optimize_satellite_pool(
                constellation_candidates,
                constellation,
                temporal_analysis
            )

            optimized_pool[constellation] = {
                'satellites': optimized_satellites,
                'temporal_analysis': temporal_analysis,
                'spatial_analysis': spatial_analysis
            }

        self.logger.info("✅ 階段 4.2 動態池規劃完成")

        return optimized_pool
```

---

## 🧪 測試計劃

### 測試 C.1: 時空覆蓋分析驗證

```python
def test_temporal_coverage_analysis():
    """測試時間覆蓋分析"""

    analyzer = TemporalSpatialAnalyzer()

    # 模擬衛星時間序列
    test_satellites = [
        {
            'satellite_id': 'SAT-A',
            'time_series': [
                {'timestamp': '2025-09-30T10:00:00Z', 'is_connectable': True},
                {'timestamp': '2025-09-30T10:01:00Z', 'is_connectable': True},
                {'timestamp': '2025-09-30T10:02:00Z', 'is_connectable': False}
            ]
        },
        {
            'satellite_id': 'SAT-B',
            'time_series': [
                {'timestamp': '2025-09-30T10:00:00Z', 'is_connectable': False},
                {'timestamp': '2025-09-30T10:01:00Z', 'is_connectable': True},
                {'timestamp': '2025-09-30T10:02:00Z', 'is_connectable': True}
            ]
        }
    ]

    result = analyzer.analyze_temporal_coverage(test_satellites)

    # 驗證覆蓋連續性
    assert result['statistics']['min_visible_count'] >= 1
    assert result['statistics']['total_time_points'] == 3
```

### 測試 C.2: 池優化算法驗證

```python
def test_pool_optimization():
    """測試池優化算法"""

    optimizer = PoolOptimizer()

    # 模擬 2000 顆候選衛星
    candidate_satellites = generate_mock_candidates(2000)

    # 執行優化
    optimized_pool = optimizer.optimize_satellite_pool(
        candidate_satellites,
        'starlink',
        temporal_analysis={}
    )

    # 驗證結果
    assert len(optimized_pool) <= 500  # 不超過目標池大小
    assert len(optimized_pool) > 0     # 至少選擇了一些衛星
```

---

## 📋 驗收標準

### 功能驗收
- [ ] 時空分布分析器正常運行
- [ ] 池優化算法成功選擇衛星子集
- [ ] 覆蓋率達到 ≥ 95%
- [ ] 任意時刻可見數量在目標範圍內

### 性能驗收
- [ ] 優化算法處理 2000 顆候選 < 10 秒
- [ ] 記憶體使用合理 (< 1GB)

### 數據驗收
- [ ] Starlink 最優池: ~500 顆 (±100)
- [ ] OneWeb 最優池: ~100 顆 (±20)
- [ ] 空窗數量顯著減少

---

## 📦 交付物

1. **新增檔案**
   - `src/stages/stage4_link_feasibility/temporal_spatial_analyzer.py`
   - `src/stages/stage4_link_feasibility/pool_optimizer.py`

2. **修改檔案**
   - `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`

3. **測試檔案**
   - `tests/stages/stage4/test_temporal_analysis.py` (新建)
   - `tests/stages/stage4/test_pool_optimization.py` (新建)

4. **文檔更新**
   - 更新 `docs/stages/stage4-link-feasibility.md` 階段 4.2 實現狀態

---

## 🚀 執行順序

1. **任務 C.1** (2-3小時): 時空分布分析器
2. **任務 C.2** (3-4小時): 池優化算法
3. **任務 C.3** (1小時): 主處理器整合
4. **測試驗證** (1小時): 完整測試和驗收

**總計**: 6-8 小時

---

## ⚠️ 風險與依賴

### 依賴
- ✅ **前置**: 計劃 A (時間序列數據) 和計劃 B (精確可見性) 必須完成
- 📊 **數據**: 需要真實的 Stage 1-3 數據進行測試

### 風險
- 優化算法可能需要多次迭代調整參數
- 實際衛星分布可能與估算不同，需要靈活調整目標池大小
- 貪心算法可能不是最優解，未來可考慮更複雜算法

### 未來增強
- 遺傳算法版本 (更優解，但計算時間較長)
- 整數規劃版本 (最優解，計算密集)
- 機器學習預測最優組合

---

**文檔版本**: v1.0
**創建日期**: 2025-09-30
**負責人**: Orbit Engine Team
**審核狀態**: 待審核