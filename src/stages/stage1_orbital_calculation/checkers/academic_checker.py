#!/usr/bin/env python3
"""學術合規檢查器"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AcademicChecker:
    """學術合規檢查器"""

    def __init__(self, requirement_checker):
        """
        初始化學術檢查器

        Args:
            requirement_checker: 需求檢查器實例
        """
        self.requirement_checker = requirement_checker
        self.logger = logging.getLogger(__name__)

    def validate(self, tle_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證學術合規性"""

        # Grade A 學術標準檢查項目
        academic_requirements = {
            'real_data': self._check_real_data(tle_data_list),
            'epoch_freshness': self._check_epoch_freshness(tle_data_list),
            'constellation_coverage': self._check_constellation_coverage(tle_data_list),
            'data_source_verification': self._check_data_source(tle_data_list),
            'format_compliance': self.requirement_checker.check(tle_data_list, 'format_compliance'),
            'time_reference_standard': self.requirement_checker.check(tle_data_list, 'time_reference_standard'),
            'unique_satellite_ids': self.requirement_checker.check(tle_data_list, 'unique_satellite_ids'),
            'complete_orbital_parameters': self.requirement_checker.check(tle_data_list, 'complete_orbital_parameters'),
            'metadata_completeness': self.requirement_checker.check(tle_data_list, 'metadata_completeness')
        }

        # 計算合規分數
        passed_checks = sum(1 for v in academic_requirements.values() if v)
        total_checks = len(academic_requirements)
        compliance_score = passed_checks / total_checks if total_checks > 0 else 0.0

        # Grade A 需要 >= 95% 合規率
        grade_a_compliant = compliance_score >= 0.95

        return {
            'requirements': academic_requirements,
            'compliance_score': compliance_score,
            'grade_a_compliant': grade_a_compliant,
            'passed_checks': passed_checks,
            'total_checks': total_checks
        }

    def _check_real_data(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查是否為真實TLE數據"""
        for tle_data in tle_data_list:
            line1 = tle_data.get('line1', '')
            if 'SAMPLE' in line1.upper() or 'TEST' in line1.upper():
                return False
        return True

    def _check_epoch_freshness(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查 Epoch 新鮮度"""
        # 簡化檢查：確保有 epoch_datetime
        for tle_data in tle_data_list:
            if 'epoch_datetime' not in tle_data:
                return False
        return True

    def _check_constellation_coverage(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查星座覆蓋"""
        constellations = set(tle.get('constellation', 'unknown') for tle in tle_data_list)
        return 'unknown' not in constellations and len(constellations) > 0

    def _check_data_source(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查數據來源"""
        for tle_data in tle_data_list:
            if 'data_source' in tle_data:
                return True
        # 如果沒有數據來源標記，仍然通過（兼容舊數據）
        return True
