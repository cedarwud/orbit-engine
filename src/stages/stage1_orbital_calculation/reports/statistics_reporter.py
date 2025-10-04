#!/usr/bin/env python3
"""統計報告器"""
import logging

logger = logging.getLogger(__name__)


class StatisticsReporter:
    """統計報告器"""

    def __init__(self, checksum_validator):
        """
        初始化統計報告器

        Args:
            checksum_validator: Checksum驗證器實例（用於獲取統計）
        """
        self.checksum_validator = checksum_validator
        self.logger = logging.getLogger(__name__)

    def report_checksum_statistics(self):
        """報告 checksum 驗證統計信息"""
        stats = self.checksum_validator.get_stats()
        total = sum(stats.values())

        if total > 0:
            official_pct = (stats['official_standard'] / total) * 100
            legacy_pct = (stats['legacy_non_standard'] / total) * 100
            invalid_pct = (stats['invalid'] / total) * 100

            self.logger.info(f"📊 TLE Checksum 統計報告:")
            self.logger.info(f"  ✅ 官方標準: {stats['official_standard']} ({official_pct:.1f}%)")

            if stats['legacy_non_standard'] > 0:
                self.logger.warning(
                    f"  ⚠️ 數據來源問題: {stats['legacy_non_standard']} ({legacy_pct:.1f}%) "
                    f"使用錯誤的checksum算法 (錯誤地將正號+算作1)"
                )

            if stats['invalid'] > 0:
                self.logger.error(f"  ❌ 校驗失敗: {stats['invalid']} ({invalid_pct:.1f}%)")
