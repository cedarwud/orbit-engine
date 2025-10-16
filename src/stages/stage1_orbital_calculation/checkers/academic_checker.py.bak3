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
        """
        檢查 Epoch 新鮮度（完整驗證）

        要求:
        1. epoch_datetime 字段存在
        2. 可解析為有效日期時間
        3. 時間範圍合理（非未來日期，未過於陳舊）

        SOURCE: Vallado (2013) - TLE數據有效性標準
        """
        from datetime import datetime, timezone, timedelta
        from shared.constants.tle_constants import TLEConstants

        now = datetime.now(timezone.utc)
        max_age = timedelta(days=TLEConstants.TLE_FRESHNESS_ACCEPTABLE_DAYS)

        for tle_data in tle_data_list:
            if 'epoch_datetime' not in tle_data:
                return False

            try:
                # 解析epoch時間
                epoch_str = tle_data['epoch_datetime']
                if isinstance(epoch_str, datetime):
                    epoch_dt = epoch_str
                else:
                    epoch_dt = datetime.fromisoformat(
                        epoch_str.replace('Z', '+00:00')
                    )

                # 檢查時間範圍
                if epoch_dt > now:  # 未來日期不合理
                    return False
                if (now - epoch_dt) > max_age:  # 過於陳舊
                    return False

            except (ValueError, AttributeError, TypeError) as e:
                raise ValueError(
                    f"❌ Epoch 新鮮度檢查失敗\n"
                    f"衛星ID: {tle_data.get('satellite_id', 'unknown')}\n"
                    f"錯誤: {e}\n"
                    f"Fail-Fast 原則: 數據格式錯誤應立即失敗"
                ) from e

        return True

    def _check_constellation_coverage(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """檢查星座覆蓋"""
        constellations = set(tle.get('constellation', 'unknown') for tle in tle_data_list)
        return 'unknown' not in constellations and len(constellations) > 0

    def _check_data_source(self, tle_data_list: List[Dict[str, Any]]) -> bool:
        """
        檢查數據來源

        ✅ Fail-Fast: 所有數據必須有明確來源
        """
        for tle_data in tle_data_list:
            if 'data_source' not in tle_data and 'source_file' not in tle_data:
                raise ValueError(
                    f"❌ TLE 數據缺少 data_source/source_file 字段\n"
                    f"衛星ID: {tle_data.get('satellite_id', 'unknown')}\n"
                    f"Fail-Fast 原則: 所有數據必須有明確來源"
                )
        return True
