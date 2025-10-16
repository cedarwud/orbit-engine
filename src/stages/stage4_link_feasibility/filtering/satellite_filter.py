#!/usr/bin/env python3
"""衛星篩選器 - Stage 4"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SatelliteFilter:
    """可連線衛星篩選器"""

    def __init__(self, service_window_calculator):
        """
        初始化篩選器

        Args:
            service_window_calculator: 服務窗口計算器實例
        """
        self.service_window_calculator = service_window_calculator
        self.logger = logging.getLogger(__name__)

    def filter_by_constellation(self, time_series_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按星座分類並篩選可連線衛星

        只保留至少有一個時間點 is_connectable=True 的衛星

        Returns:
            {
                'starlink': [...],
                'oneweb': [...],
                'other': [...]
            }
        """
        connectable_by_constellation = {
            'starlink': [],
            'oneweb': [],
            'other': []
        }

        for sat_id, sat_metrics in time_series_metrics.items():
            time_series = sat_metrics['time_series']
            constellation = sat_metrics['constellation']

            # 檢查是否至少有一個時間點可連線
            has_connectable_time = any(
                point['visibility_metrics']['is_connectable']
                for point in time_series
            )

            if has_connectable_time:
                # 確定星座分類
                if 'starlink' in constellation:
                    constellation_key = 'starlink'
                elif 'oneweb' in constellation:
                    constellation_key = 'oneweb'
                else:
                    constellation_key = 'other'

                # ✅ 修復: 只保留可連線的時間點 (仰角 > 門檻值)
                # 原因: 下游驗證器和 Stage 5/6 不需要負仰角的數據點
                connectable_time_series = [
                    point for point in time_series
                    if point['visibility_metrics']['is_connectable']
                ]

                # 計算服務窗口 (基於已過濾的時間序列)
                service_window = self.service_window_calculator.calculate(connectable_time_series)

                satellite_entry = {
                    'satellite_id': sat_id,
                    'name': sat_metrics['name'],
                    'constellation': constellation_key,
                    'time_series': connectable_time_series,  # ✅ 只保留可連線點
                    'service_window': service_window
                }

                connectable_by_constellation[constellation_key].append(satellite_entry)

        # 記錄統計
        for constellation, sats in connectable_by_constellation.items():
            if sats:
                self.logger.info(f"📊 {constellation}: {len(sats)} 顆可連線衛星")

        return connectable_by_constellation
