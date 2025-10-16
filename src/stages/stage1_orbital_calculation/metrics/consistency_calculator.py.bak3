#!/usr/bin/env python3
"""一致性計算器"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ConsistencyCalculator:
    """一致性評分計算器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate(self, tle_data_list: List[Dict[str, Any]]) -> float:
        """計算一致性評分"""
        if not tle_data_list:
            return 0.0

        consistency_checks = {
            'satellite_id_consistency': 0,
            'constellation_consistency': 0,
            'epoch_consistency': 0,
            'orbital_regime_consistency': 0
        }

        total_records = len(tle_data_list)

        # 檢查衛星ID一致性
        satellite_ids = [tle.get('satellite_id') for tle in tle_data_list]
        if len(satellite_ids) == len(set(satellite_ids)):
            consistency_checks['satellite_id_consistency'] = total_records

        # 檢查星座一致性
        for tle_data in tle_data_list:
            if tle_data.get('constellation'):
                consistency_checks['constellation_consistency'] += 1

        # 檢查 epoch 一致性
        for tle_data in tle_data_list:
            if 'epoch_datetime' in tle_data:
                consistency_checks['epoch_consistency'] += 1

        # 檢查軌道參數一致性
        for tle_data in tle_data_list:
            line2 = tle_data.get('line2', '')
            if len(line2) >= 63:
                try:
                    mean_motion = float(line2[52:63])
                    if mean_motion > 0:
                        consistency_checks['orbital_regime_consistency'] += 1
                except (ValueError, IndexError):
                    pass

        # 計算綜合評分
        id_score = consistency_checks['satellite_id_consistency'] / total_records
        const_score = consistency_checks['constellation_consistency'] / total_records
        epoch_score = consistency_checks['epoch_consistency'] / total_records
        orbital_score = consistency_checks['orbital_regime_consistency'] / total_records

        overall_score = (id_score + const_score + epoch_score + orbital_score) / 4

        return overall_score
