#!/usr/bin/env python3
"""TLE Checksum 驗證器"""
import logging

logger = logging.getLogger(__name__)


class ChecksumValidator:
    """TLE Checksum 驗證器"""

    def __init__(self):
        self.checksum_stats = {
            'official_standard': 0,
            'legacy_non_standard': 0,
            'invalid': 0
        }
        self.logger = logging.getLogger(__name__)

    def verify_tle_checksum(self, tle_line: str) -> bool:
        """驗證 TLE checksum"""
        if not tle_line or len(tle_line) < 69:
            return False

        try:
            # 提取 checksum
            expected_checksum = int(tle_line[68])

            # 計算 checksum (官方標準)
            checksum = 0
            for char in tle_line[:68]:
                if char.isdigit():
                    checksum += int(char)
                elif char == '-':
                    checksum += 1

            calculated_checksum = checksum % 10

            # 驗證
            if calculated_checksum == expected_checksum:
                self.checksum_stats['official_standard'] += 1
                return True
            else:
                # 嘗試舊標準 (錯誤地將 + 算作 1)
                legacy_checksum = checksum
                for char in tle_line[:68]:
                    if char == '+':
                        legacy_checksum += 1
                legacy_checksum = legacy_checksum % 10

                if legacy_checksum == expected_checksum:
                    self.checksum_stats['legacy_non_standard'] += 1
                    return True
                else:
                    self.checksum_stats['invalid'] += 1
                    return False

        except (ValueError, IndexError):
            self.checksum_stats['invalid'] += 1
            return False

    def get_stats(self) -> dict:
        """獲取統計數據"""
        return self.checksum_stats.copy()
