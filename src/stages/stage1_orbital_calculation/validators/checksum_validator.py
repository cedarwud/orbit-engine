#!/usr/bin/env python3
"""
TLE Checksum 驗證器

⚠️ CRITICAL - Grade A 學術標準強制聲明 ⚠️

本模組遵循嚴格的學術合規性標準:
- ✅ 使用完整的 NORAD TLE Checksum 官方標準
- ✅ 支持官方標準和舊版相容性檢查
- ❌ 禁止使用簡化算法或估算值

參考文檔: docs/ACADEMIC_STANDARDS.md
"""
import logging

logger = logging.getLogger(__name__)


class ChecksumValidator:
    """TLE Checksum 驗證器（NORAD 官方標準）"""

    def __init__(self):
        self.checksum_stats = {
            'official_standard': 0,
            'legacy_non_standard': 0,
            'invalid': 0
        }
        self.logger = logging.getLogger(__name__)

    def verify_tle_checksum(self, tle_line: str) -> bool:
        """
        驗證 TLE checksum (NORAD 官方標準)

        算法依據:
        - SOURCE: NORAD TLE Format Specification
        - Reference: Kelso, T.S. (2007) "Validation of SGP4 and IS-GPS-200D"
        - CelesTrak: https://celestrak.org/columns/v04n03/

        Checksum 計算規則（官方標準）:
        1. 對前68個字符進行掃描
        2. 數字字符 (0-9): 加上數字本身的值
        3. 減號 (-): 加1
        4. 加號 (+): 加0（不計算）
        5. 其他字符（字母、空格、小數點）: 忽略
        6. 結果對10取模，得到0-9的單一數字

        相容性處理:
        - 官方標準: 加號(+)不計算（加0）
        - 舊版標準: 錯誤地將加號計為1（向後兼容檢查）

        Args:
            tle_line: TLE行字符串（69字符）

        Returns:
            bool: checksum驗證是否通過
        """
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

    def calculate_checksum(self, tle_line: str) -> int:
        """
        計算 TLE 行的 checksum（NORAD 官方標準）

        算法依據：
        - SOURCE: NORAD TLE Format Specification
        - CelesTrak: https://celestrak.org/NORAD/documentation/tle-fmt.php

        Checksum 計算規則：
        1. 掃描前68個字符
        2. 數字 (0-9): 加上數字值
        3. 減號 (-): 加1
        4. 其他字符：忽略
        5. 結果 % 10

        Args:
            tle_line: TLE行字符串（至少68字符）

        Returns:
            int: 計算得出的 checksum (0-9)

        Raises:
            ValueError: 當 TLE 行長度不足時
        """
        if not tle_line or len(tle_line) < 68:
            raise ValueError(
                f"❌ TLE 行長度不足 (需要 >= 68 字符)\n"
                f"實際長度: {len(tle_line) if tle_line else 0}"
            )

        checksum = 0
        for char in tle_line[:68]:
            if char.isdigit():
                checksum += int(char)
            elif char == '-':
                checksum += 1
            # 其他字符（字母、空格、句點、正號+）被忽略

        return checksum % 10

    def fix_checksum(self, tle_line: str) -> str:
        """
        修復 TLE 行的 checksum（使用官方標準重新計算）

        Args:
            tle_line: TLE行字符串（69字符）

        Returns:
            str: 修復後的 TLE 行（69字符）

        Raises:
            ValueError: 當 TLE 行長度不為69時
        """
        if not tle_line or len(tle_line) != 69:
            raise ValueError(
                f"❌ TLE 行長度必須為 69 字符\n"
                f"實際長度: {len(tle_line) if tle_line else 0}"
            )

        # 使用官方算法計算正確的 checksum
        correct_checksum = self.calculate_checksum(tle_line)

        # 構建修復後的 TLE 行
        fixed_line = tle_line[:68] + str(correct_checksum)

        return fixed_line

    def get_stats(self) -> dict:
        """獲取統計數據"""
        return self.checksum_stats.copy()
