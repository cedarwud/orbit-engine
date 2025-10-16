#!/usr/bin/env python3
"""服務窗口計算器 - Stage 4"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ServiceWindowCalculator:
    """服務窗口計算器"""

    @staticmethod
    def calculate(time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算服務窗口"""
        if not time_series:
            return {
                'total_window_minutes': 0,
                'window_start': None,
                'window_end': None,
                'continuity_score': 0.0
            }

        connectable_points = [p for p in time_series if p.get('is_connectable', False)]

        if not connectable_points:
            return {
                'total_window_minutes': 0,
                'window_start': None,
                'window_end': None,
                'continuity_score': 0.0
            }

        # 計算總窗口時間
        total_window_minutes = len(connectable_points)

        # 取第一個和最後一個可連線點
        window_start = connectable_points[0].get('timestamp')
        window_end = connectable_points[-1].get('timestamp')

        # 計算連續性分數
        continuity_score = len(connectable_points) / len(time_series) if time_series else 0.0

        return {
            'total_window_minutes': total_window_minutes,
            'window_start': window_start,
            'window_end': window_end,
            'continuity_score': round(continuity_score, 3)
        }
