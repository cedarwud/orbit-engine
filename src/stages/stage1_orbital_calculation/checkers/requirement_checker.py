#!/usr/bin/env python3
"""學術需求檢查器"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RequirementChecker:
    """學術需求檢查器"""

    def __init__(self, format_validator):
        """
        初始化需求檢查器

        Args:
            format_validator: 格式驗證器實例
        """
        self.format_validator = format_validator
        self.logger = logging.getLogger(__name__)

    def check(self, tle_data_list: List[Dict[str, Any]], requirement: str) -> bool:
        """檢查指定需求"""

        if requirement == 'format_compliance':
            return self._check_format_compliance(tle_data_list)

        elif requirement == 'time_reference_standard':
            return self._check_time_reference(tle_data_list)

        elif requirement == 'unique_satellite_ids':
            return self._check_unique_ids(tle_data_list)

        elif requirement == 'complete_orbital_parameters':
            return self._check_orbital_parameters(tle_data_list)

        elif requirement == 'metadata_completeness':
            return self._check_metadata(tle_data_list)

        else:
            self.logger.warning(f"Unknown requirement: {requirement}")
            return False

    def _check_format_compliance(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查格式合規性"""
        for tle_data in tle_data_list:
            line1 = tle_data.get('line1', '')
            line2 = tle_data.get('line2', '')

            if not self.format_validator.validate_tle_line(line1, 1):
                return False
            if not self.format_validator.validate_tle_line(line2, 2):
                return False

        return True

    def _check_time_reference(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查時間基準標準"""
        for tle_data in tle_data_list:
            if 'epoch_datetime' not in tle_data:
                return False

            try:
                epoch_str = tle_data['epoch_datetime']
                epoch_dt = datetime.fromisoformat(epoch_str.replace('Z', '+00:00'))

                if epoch_dt.tzinfo != timezone.utc:
                    return False

            except (ValueError, AttributeError):
                return False

        return True

    def _check_unique_ids(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查衛星ID唯一性"""
        satellite_ids = [tle.get('satellite_id', '') for tle in tle_data_list]
        return len(satellite_ids) == len(set(satellite_ids)) and all(sid for sid in satellite_ids)

    def _check_orbital_parameters(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查軌道參數完整性"""
        required_params = ['line1', 'line2', 'satellite_id', 'name']

        for tle_data in tle_data_list:
            # 檢查必要參數
            for param in required_params:
                if param not in tle_data or not tle_data[param]:
                    return False

            # 檢查軌道參數合理性
            line2 = tle_data['line2']
            try:
                mean_motion = float(line2[52:63])
                if mean_motion <= 0:
                    return False
            except (ValueError, IndexError):
                return False

        return True

    def _check_metadata(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查元數據完整性"""
        for tle_data in tle_data_list:
            if not all(key in tle_data for key in ['name', 'satellite_id', 'constellation']):
                return False

        return True
