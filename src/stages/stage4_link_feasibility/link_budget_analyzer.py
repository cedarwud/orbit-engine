#!/usr/bin/env python3
"""
鏈路預算分析器 - Stage 4 核心模組

職責範圍:
- 幾何可見性約束（仰角門檻）
- 真實信號品質由 Stage 5 使用 3GPP TS 38.214 計算

學術依據:
> "Link feasibility for LEO satellite communications requires consideration of
> elevation-dependent path loss, Doppler effects, and constellation-specific
> service requirements."
> — Kodheli, O., et al. (2021). Satellite communications in the new space era:
>    A survey and future challenges. IEEE Communications Surveys & Tutorials, 23(1), 70-109.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LinkBudgetAnalyzer:
    """
    鏈路預算分析器

    Stage 4 職責：
    - 幾何可見性判斷（基於仰角門檻）
    - 不進行信號品質估算（由 Stage 5 使用 3GPP TS 38.214 標準計算）
    """

    # 鏈路預算約束參數
    LINK_BUDGET_CONSTRAINTS = {
        # 最小距離約束已移除（設為 0 = 無約束）
        #
        # 移除理由：
        # 1. Stage 4 職責為幾何可見性，不應引入未經驗證的距離約束
        # 2. 真實的都卜勒效應由 Stage 5 基於精確軌道速度計算
        # 3. 3GPP NR NTN 標準（TS 38.821）已支援極低仰角連線
        # 4. 星座特定仰角門檻（Starlink 5°, OneWeb 10°）已提供足夠篩選
        #
        # 學術依據：
        #   - 3GPP TR 38.821 (2021). "Solutions for NR to support non-terrestrial networks (NTN)"
        #     Section 6.1: NTN 支援仰角低至 10° 的連線場景
        #   - Stage 5 使用完整 3GPP TS 38.214 鏈路預算計算（包含都卜勒補償）
        #   - 過早引入距離約束可能排除有效的低仰角連線機會
        #
        # 原有 200km 約束問題：
        #   - 缺乏具體學術依據（Kodheli 2021 為一般性引用）
        #   - "避免多普勒過大" 未量化（多大算過大？）
        #   - "調度複雜性" 非 Stage 4 考量範圍
        'min_distance_km': 0,  # 無距離約束（幾何可見性由仰角門檻控制）

        # 注: 已移除 max_distance_km 約束
        # 理由: 2000km 約束與星座仰角門檻數學上不兼容
        #   - Starlink (550km, 5°) 斜距 = 2205km > 2000km
        #   - OneWeb (1200km, 10°) 斜距 = 3131km > 2000km
        # 真實信號強度由 Stage 5 使用 3GPP TS 38.214 鏈路預算計算
        'min_elevation_deg': 0,   # 地平線遮擋 (基本可見性，實際門檻由星座配置控制)
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化鏈路預算分析器

        Args:
            config: 配置字典 (可選)
        """
        self.config = config or {}
        self.logger = logger

        # 允許通過配置覆蓋預設值
        self.min_distance_km = self.config.get(
            'min_distance_km',
            self.LINK_BUDGET_CONSTRAINTS['min_distance_km']
        )
        # 最大距離約束已移除（與星座仰角門檻數學上不兼容）
        self.max_distance_km = None

        self.logger.info("🔗 鏈路預算分析器初始化")
        if self.min_distance_km > 0:
            self.logger.info(f"   最小距離: {self.min_distance_km} km")
        else:
            self.logger.info(f"   距離約束: 無（幾何可見性由仰角門檻控制）")
        self.logger.info(f"   職責範圍: 幾何可見性判斷（信號品質由 Stage 5 計算）")

    def check_distance_constraint(self, distance_km: float) -> bool:
        """
        檢查距離是否滿足最小距離約束

        注: 已移除最大距離約束（與星座仰角門檻數學上不兼容）
        真實信號強度由 Stage 5 使用 3GPP TS 38.214 鏈路預算計算

        Args:
            distance_km: 衛星與地面站的距離 (公里)

        Returns:
            True 如果距離 >= 最小距離，否則 False
        """
        return distance_km >= self.min_distance_km

    def analyze_link_feasibility(self, elevation_deg: float,
                                 distance_km: float,
                                 constellation: str,
                                 elevation_threshold: float) -> Dict[str, Any]:
        """
        綜合分析鏈路可行性

        檢查項目:
        1. 仰角是否達到星座特定門檻
        2. 距離是否滿足最小距離要求 (>= 200km)

        Args:
            elevation_deg: 衛星仰角 (度)
            distance_km: 衛星距離 (公里)
            constellation: 星座類型
            elevation_threshold: 星座特定仰角門檻

        Returns:
            {
                'is_connectable': bool,           # 綜合判斷: 是否可連線
                'elevation_ok': bool,             # 仰角是否達標
                'distance_ok': bool,              # 距離是否在範圍內
                'elevation_deg': float,           # 仰角值
                'distance_km': float,             # 距離值
                'elevation_threshold': float,     # 應用的門檻
                'distance_range': (float, float), # 距離範圍
                'failure_reasons': List[str]      # 失敗原因列表
            }
        """
        # 檢查仰角
        elevation_ok = elevation_deg >= elevation_threshold

        # 檢查距離
        distance_ok = self.check_distance_constraint(distance_km)

        # 綜合判斷可連線性
        is_connectable = elevation_ok and distance_ok

        # 收集失敗原因
        failure_reasons = []
        if not elevation_ok:
            failure_reasons.append(
                f"仰角不足: {elevation_deg:.2f}° < {elevation_threshold:.2f}°"
            )
        if not distance_ok:
            # 注: 已移除最大距離約束（與星座仰角門檻數學上不兼容）
            failure_reasons.append(
                f"距離過近: {distance_km:.1f}km < {self.min_distance_km}km (多普勒效應過大)"
            )

        return {
            'is_connectable': is_connectable,
            'elevation_ok': elevation_ok,
            'distance_ok': distance_ok,
            'elevation_deg': elevation_deg,
            'distance_km': distance_km,
            'elevation_threshold': elevation_threshold,
            'distance_range': {'min_km': self.min_distance_km, 'max_km': None},  # 無最大距離限制
            'failure_reasons': failure_reasons
            # 注: Stage 4 不再提供簡化的品質估計
            # 真實的信號品質 (RSRP/RSRQ/SINR) 由 Stage 5 使用 3GPP TS 38.214 標準計算
        }


    def batch_analyze(self, time_series: list, constellation: str,
                     elevation_threshold: float) -> Dict[str, Any]:
        """
        批次分析時間序列的鏈路可行性

        Args:
            time_series: 時間序列數據列表
            constellation: 星座類型
            elevation_threshold: 仰角門檻

        Returns:
            {
                'connectable_points': int,        # 可連線時間點數
                'total_points': int,              # 總時間點數
                'connectivity_ratio': float,      # 可連線比例
                'avg_elevation': float,           # 平均仰角
                'avg_distance': float,            # 平均距離
                'max_elevation': float,           # 最大仰角
                'min_distance': float             # 最小距離
            }
        """
        if not time_series:
            return {
                'connectable_points': 0,
                'total_points': 0,
                'connectivity_ratio': 0.0,
                'avg_elevation': 0.0,
                'avg_distance': 0.0,
                'max_elevation': 0.0,
                'min_distance': float('inf')
            }

        connectable_count = 0
        elevations = []
        distances = []

        for point in time_series:
            elevation = point.get('elevation_deg', -90.0)
            distance = point.get('distance_km', float('inf'))

            elevations.append(elevation)
            distances.append(distance)

            # 分析該點的可行性
            analysis = self.analyze_link_feasibility(
                elevation, distance, constellation, elevation_threshold
            )

            if analysis['is_connectable']:
                connectable_count += 1

        total_points = len(time_series)

        return {
            'connectable_points': connectable_count,
            'total_points': total_points,
            'connectivity_ratio': connectable_count / total_points if total_points > 0 else 0.0,
            'avg_elevation': sum(elevations) / len(elevations) if elevations else 0.0,
            'avg_distance': sum(distances) / len(distances) if distances else 0.0,
            'max_elevation': max(elevations) if elevations else 0.0,
            'min_distance': min(distances) if distances else float('inf')
        }

    def get_constraint_info(self) -> Dict[str, Any]:
        """
        獲取當前約束配置信息

        Returns:
            約束配置字典
        """
        return {
            'min_distance_km': self.min_distance_km,
            'max_distance_km': None,  # 已移除最大距離約束
            'distance_range_km': {'min_km': self.min_distance_km, 'max_km': 'unlimited'},
            'constraint_rationale': {
                'min_distance_removed': 'Stage 4 專注幾何可見性，距離約束已移除（設為 0）。都卜勒效應由 Stage 5 基於精確軌道速度計算。',
                'max_distance_removed': '2000km 約束與星座仰角門檻數學上不兼容（Starlink 5°→2205km, OneWeb 10°→3131km），真實信號強度由 Stage 5 使用 3GPP TS 38.214 標準計算'
            },
            'academic_reference': {
                'general': 'Kodheli, O., et al. (2021). Satellite communications in the new space era: A survey and future challenges. IEEE Communications Surveys & Tutorials, 23(1), 70-109.',
                'ntn_standard': '3GPP TR 38.821 (2021). Solutions for NR to support non-terrestrial networks (NTN), Section 6.1',
                'stage_division': 'Stage 4: 幾何可見性 | Stage 5: 3GPP TS 38.214 信號品質計算'
            }
        }


def create_link_budget_analyzer(config: Optional[Dict[str, Any]] = None) -> LinkBudgetAnalyzer:
    """
    創建鏈路預算分析器實例

    Args:
        config: 配置字典 (可選)

    Returns:
        LinkBudgetAnalyzer 實例
    """
    return LinkBudgetAnalyzer(config)


if __name__ == "__main__":
    # 測試鏈路預算分析器
    print("🧪 測試鏈路預算分析器")
    print("=" * 60)

    analyzer = create_link_budget_analyzer()

    # 測試案例 1: 距離過近
    print("\n測試 1: 距離過近 (150km)")
    result = analyzer.analyze_link_feasibility(
        elevation_deg=10.0,
        distance_km=150.0,
        constellation='starlink',
        elevation_threshold=5.0
    )
    print(f"  可連線: {result['is_connectable']}")
    print(f"  失敗原因: {result['failure_reasons']}")

    # 測試案例 2: 正常範圍
    print("\n測試 2: 正常範圍 (500km, 10°)")
    result = analyzer.analyze_link_feasibility(
        elevation_deg=10.0,
        distance_km=500.0,
        constellation='starlink',
        elevation_threshold=5.0
    )
    print(f"  可連線: {result['is_connectable']}")
    print(f"  仰角達標: {result['elevation_ok']}")
    print(f"  距離達標: {result['distance_ok']}")

    # 測試案例 3: 大距離但仰角達標 (測試移除最大距離限制後的行為)
    print("\n測試 3: 大距離但仰角達標 (3000km, OneWeb 10°)")
    result = analyzer.analyze_link_feasibility(
        elevation_deg=12.0,
        distance_km=3000.0,
        constellation='oneweb',
        elevation_threshold=10.0
    )
    print(f"  可連線: {result['is_connectable']}")
    print(f"  仰角達標: {result['elevation_ok']}")
    print(f"  距離達標: {result['distance_ok']}")

    # 測試案例 4: 仰角不足
    print("\n測試 4: 仰角不足 (3°, OneWeb)")
    result = analyzer.analyze_link_feasibility(
        elevation_deg=3.0,
        distance_km=800.0,
        constellation='oneweb',
        elevation_threshold=10.0
    )
    print(f"  可連線: {result['is_connectable']}")
    print(f"  失敗原因: {result['failure_reasons']}")

    # 顯示約束信息
    print("\n約束配置信息:")
    info = analyzer.get_constraint_info()
    print(f"  距離範圍: {info['distance_range_km']}")
    print(f"  最小距離依據: {info['constraint_rationale']['min_distance']}")
    print(f"  最大距離移除原因: {info['constraint_rationale']['max_distance_removed']}")

    print("\n✅ 測試完成")