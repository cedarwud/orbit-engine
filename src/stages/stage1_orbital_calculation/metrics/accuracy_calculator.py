#!/usr/bin/env python3
"""準確性計算器"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AccuracyCalculator:
    """準確性評分計算器"""

    def __init__(self, format_validator, checksum_validator):
        """
        初始化準確性計算器

        Args:
            format_validator: 格式驗證器實例
            checksum_validator: Checksum驗證器實例
        """
        self.format_validator = format_validator
        self.checksum_validator = checksum_validator
        self.logger = logging.getLogger(__name__)

    def calculate(self, tle_data_list: List[Dict[str, Any]]) -> float:
        """計算準確性評分"""
        if not tle_data_list:
            return 0.0

        accuracy_checks = {
            'format_accuracy': 0,
            'checksum_accuracy': 0,
            'physical_parameter_accuracy': 0,
            'epoch_accuracy': 0
        }

        total_records = len(tle_data_list)

        for tle_data in tle_data_list:
            line1 = tle_data.get('line1', '')
            line2 = tle_data.get('line2', '')

            # 1. 格式準確性
            if (self.format_validator.validate_tle_line(line1, 1) and
                self.format_validator.validate_tle_line(line2, 2)):
                accuracy_checks['format_accuracy'] += 1

            # 2. 校驗和準確性
            if (self.checksum_validator.verify_tle_checksum(line1) and
                self.checksum_validator.verify_tle_checksum(line2)):
                accuracy_checks['checksum_accuracy'] += 1

            # 3. 物理參數準確性
            if self._validate_physical_parameters(line2):
                accuracy_checks['physical_parameter_accuracy'] += 1

            # 4. Epoch時間準確性
            if self._validate_epoch_time(line1):
                accuracy_checks['epoch_accuracy'] += 1

        # 計算綜合評分
        format_score = accuracy_checks['format_accuracy'] / total_records
        checksum_score = accuracy_checks['checksum_accuracy'] / total_records
        physical_score = accuracy_checks['physical_parameter_accuracy'] / total_records
        epoch_score = accuracy_checks['epoch_accuracy'] / total_records

        # 加權平均
        overall_score = (
            format_score * 0.3 +
            checksum_score * 0.2 +
            physical_score * 0.3 +
            epoch_score * 0.2
        )

        return overall_score

    def _validate_physical_parameters(self, line2: str) -> bool:
        """驗證物理參數"""
        try:
            inclination = float(line2[8:16])
            eccentricity = float(line2[26:33]) * 1e-7
            mean_motion = float(line2[52:63])

            # 檢查物理約束
            if not (0 <= inclination <= 180):
                return False
            if not (0 <= eccentricity < 1):
                return False
            if not (0.5 <= mean_motion <= 20.0):
                return False

            return True

        except (ValueError, IndexError):
            return False

    def _validate_epoch_time(self, line1: str) -> bool:
        """驗證 Epoch 時間"""
        try:
            epoch_year = int(line1[18:20])
            epoch_day = float(line1[20:32])

            SATELLITE_ERA_START = 1957
            REASONABLE_FUTURE_LIMIT = 2035

            full_year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year

            if SATELLITE_ERA_START <= full_year <= REASONABLE_FUTURE_LIMIT:
                if 1.0 <= epoch_day <= 366.999999:
                    return True

            return False

        except (ValueError, IndexError):
            return False
