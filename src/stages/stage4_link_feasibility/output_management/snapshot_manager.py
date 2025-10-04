#!/usr/bin/env python3
"""快照管理器 - Stage 4"""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Stage 4 驗證快照管理器"""

    @staticmethod
    def save(processing_results: Dict[str, Any]) -> bool:
        """保存 Stage 4 驗證快照"""
        try:
            validation_dir = Path("data/validation_snapshots")
            validation_dir.mkdir(parents=True, exist_ok=True)

            # 提取必要數據
            metadata = processing_results.get('metadata', {})
            feasibility_summary = processing_results.get('feasibility_summary', {})
            pool_optimization = processing_results.get('pool_optimization', {})

            # 檢查階段完成狀態
            stage_4_1_completed = metadata.get('stage_4_1_completed', False)
            stage_4_2_completed = metadata.get('stage_4_2_completed', False)

            # 判斷驗證狀態
            validation_results = pool_optimization.get('validation_results', {})
            starlink_validation = validation_results.get('starlink', {})
            starlink_passed = starlink_validation.get('validation_passed', False)

            overall_validation_passed = (
                stage_4_1_completed and
                stage_4_2_completed and
                starlink_passed
            )

            # 構建驗證快照數據
            snapshot_data = {
                'stage': 'stage4_link_feasibility',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'success' if overall_validation_passed else 'warning',
                'metadata': metadata,
                'feasibility_summary': feasibility_summary,
                'pool_optimization': pool_optimization,
                'validation_status': 'passed' if overall_validation_passed else 'warning',
                'validation_passed': overall_validation_passed,
                'data_summary': {
                    'total_connectable_satellites': feasibility_summary.get('total_connectable_satellites', 0),
                    'starlink_optimized_pool_size': pool_optimization.get('starlink', {}).get('optimized_pool_size', 0),
                    'oneweb_optimized_pool_size': pool_optimization.get('oneweb', {}).get('optimized_pool_size', 0)
                }
            }

            # 保存快照
            snapshot_path = validation_dir / "stage4_validation.json"
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📋 Stage 4 驗證快照已保存: {snapshot_path}")
            logger.info(f"   驗證狀態: {'通過' if overall_validation_passed else '警告'}")
            logger.info(f"   階段 4.1: {'✅' if stage_4_1_completed else '❌'}")
            logger.info(f"   階段 4.2: {'✅' if stage_4_2_completed else '❌'}")

            return True

        except Exception as e:
            logger.error(f"❌ Stage 4 驗證快照保存失敗: {e}")
            return False
