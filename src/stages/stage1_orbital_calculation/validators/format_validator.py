#!/usr/bin/env python3
"""TLE 格式驗證器"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class FormatValidator:
    """TLE 格式驗證器"""

    def __init__(self, validation_rules: Dict[str, Any]):
        """
        初始化格式驗證器

        Args:
            validation_rules: 驗證規則配置
        """
        self.validation_rules = validation_rules
        self.logger = logging.getLogger(__name__)

    def validate_tle_line(self, tle_line: str, line_number: int) -> bool:
        """驗證單行 TLE 格式"""
        if not tle_line:
            return False

        # 檢查長度
        expected_length = self.validation_rules.get('tle_line_length', 69)
        if len(tle_line) != expected_length:
            return False

        # 驗證行號標識
        if tle_line[0] != str(line_number):
            return False

        # 基本格式檢查通過
        return True

    def validate_format_compliance(self, tle_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證 TLE 格式合規性"""
        total_records = len(tle_data_list)
        valid_records = 0
        invalid_records = []

        for idx, tle_data in enumerate(tle_data_list):
            line1 = tle_data.get('line1', '')
            line2 = tle_data.get('line2', '')

            # 驗證兩行格式
            if self.validate_tle_line(line1, 1) and self.validate_tle_line(line2, 2):
                valid_records += 1
            else:
                invalid_records.append({
                    'index': idx,
                    'satellite_id': tle_data.get('satellite_id', 'unknown'),
                    'reason': 'Invalid TLE format'
                })

        compliance_rate = valid_records / total_records if total_records > 0 else 0.0

        return {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': invalid_records,
            'compliance_rate': compliance_rate,
            'passed': compliance_rate >= 0.95
        }
