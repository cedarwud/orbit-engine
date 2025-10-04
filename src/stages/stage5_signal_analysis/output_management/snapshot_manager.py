#!/usr/bin/env python3
"""快照管理器 - Stage 5"""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SnapshotManager:
    """驗證快照管理器"""

    def __init__(self, validator):
        self.validator = validator

    def save(self, processing_results: Dict[str, Any]) -> bool:
        """保存驗證快照"""
        try:
            validation_dir = Path("data/validation_snapshots")
            validation_dir.mkdir(parents=True, exist_ok=True)

            validation_results = self.validator.run_validation_checks(processing_results)
            analysis_summary = processing_results.get('analysis_summary', {})
            metadata = processing_results.get('metadata', {})

            snapshot_data = {
                'stage': 'stage5_signal_analysis',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data_summary': {
                    'total_satellites_analyzed': analysis_summary.get('total_satellites_analyzed', 0),
                    'usable_satellites': analysis_summary.get('usable_satellites', 0),
                    'signal_quality_distribution': analysis_summary.get('signal_quality_distribution', {})
                },
                'metadata': metadata,
                'validation_results': validation_results
            }

            snapshot_path = validation_dir / "stage5_validation.json"
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📋 Stage 5驗證快照已保存: {snapshot_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 快照保存失敗: {e}")
            return False
