#!/usr/bin/env python3
"""
快照管理器 - Stage 5

✅ Grade A+ 標準: 100% Fail-Fast
依據: docs/ACADEMIC_STANDARDS.md Line 265-274

Updated: 2025-10-04 - Fail-Fast 重構
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    驗證快照管理器

    ✅ Grade A+ 標準: Fail-Fast 數據驗證
    - 禁止使用 `.get()` 預設值回退
    - 數據缺失時拋出異常而非靜默返回 False
    """

    def __init__(self, validator):
        self.validator = validator

    def save(self, processing_results: Dict[str, Any]) -> bool:
        """
        保存驗證快照

        ✅ Grade A+ 標準: Fail-Fast 保存驗證

        Args:
            processing_results: Stage 5 處理結果

        Returns:
            bool: 保存成功返回 True

        Raises:
            ValueError: 數據結構不完整
            Exception: 保存過程中的其他錯誤
        """
        try:
            # ============================================================================
            # 第 1 層: 結構驗證 - 檢查頂層必要字段
            # ============================================================================

            required_top_level = ['analysis_summary', 'metadata']
            missing = [f for f in required_top_level if f not in processing_results]
            if missing:
                raise ValueError(
                    f"processing_results 缺少必要字段: {missing}\n"
                    f"快照保存失敗：數據結構不完整"
                )

            analysis_summary = processing_results['analysis_summary']
            metadata = processing_results['metadata']

            # 驗證類型
            if not isinstance(analysis_summary, dict):
                raise ValueError(
                    f"analysis_summary 類型錯誤: {type(analysis_summary).__name__} (期望: dict)"
                )

            if not isinstance(metadata, dict):
                raise ValueError(
                    f"metadata 類型錯誤: {type(metadata).__name__} (期望: dict)"
                )

            # ============================================================================
            # 第 2 層: analysis_summary 字段驗證
            # ============================================================================

            required_summary = [
                'total_satellites_analyzed',
                'usable_satellites',
                'signal_quality_distribution',
                'average_rsrp_dbm',
                'average_sinr_db',
                'total_time_points_processed'
            ]

            missing_summary = [f for f in required_summary if f not in analysis_summary]
            if missing_summary:
                raise ValueError(
                    f"analysis_summary 缺少必要字段: {missing_summary}\n"
                    f"快照保存失敗：分析摘要不完整\n"
                    f"所有必要字段: {required_summary}"
                )

            # ============================================================================
            # 第 3 層: 執行驗證檢查
            # ============================================================================

            validation_results = self.validator.run_validation_checks(processing_results)

            # ============================================================================
            # 第 4 層: 構建快照數據（無需 .get()）
            # ============================================================================

            snapshot_data = {
                'stage': 'stage5_signal_analysis',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data_summary': {
                    'total_satellites_analyzed': analysis_summary['total_satellites_analyzed'],
                    'usable_satellites': analysis_summary['usable_satellites'],
                    'signal_quality_distribution': analysis_summary['signal_quality_distribution'],
                    'average_rsrp_dbm': analysis_summary['average_rsrp_dbm'],
                    'average_sinr_db': analysis_summary['average_sinr_db'],
                    'total_time_points_processed': analysis_summary['total_time_points_processed']
                },
                'metadata': metadata,
                'validation_results': validation_results
            }

            # ============================================================================
            # 第 5 層: 保存快照文件
            # ============================================================================

            validation_dir = Path("data/validation_snapshots")
            validation_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path = validation_dir / "stage5_validation.json"

            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📋 Stage 5驗證快照已保存: {snapshot_path}")
            return True

        except ValueError as e:
            # 數據驗證錯誤 - 拋出異常而非靜默失敗
            logger.error(f"❌ 快照數據驗證失敗: {e}")
            raise

        except Exception as e:
            # 其他錯誤 - 同樣拋出異常
            logger.error(f"❌ 快照保存失敗: {e}")
            raise
