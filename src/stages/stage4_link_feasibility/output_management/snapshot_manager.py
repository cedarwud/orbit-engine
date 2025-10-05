#!/usr/bin/env python3
"""快照管理器 - Stage 4 (Fail-Fast 版本)"""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Stage 4 驗證快照管理器 - 使用 Fail-Fast 原則"""

    @staticmethod
    def save(processing_results: Dict[str, Any]) -> bool:
        """保存 Stage 4 驗證快照 - Fail-Fast 模式"""
        try:
            validation_dir = Path("data/validation_snapshots")
            validation_dir.mkdir(parents=True, exist_ok=True)

            # ✅ Fail-Fast: 檢查必需頂層字段
            if 'metadata' not in processing_results:
                logger.error("❌ processing_results 缺少必需字段 'metadata'")
                return False

            if 'feasibility_summary' not in processing_results:
                logger.error("❌ processing_results 缺少必需字段 'feasibility_summary'")
                return False

            if 'pool_optimization' not in processing_results:
                logger.error("❌ processing_results 缺少必需字段 'pool_optimization'")
                return False

            metadata = processing_results['metadata']
            feasibility_summary = processing_results['feasibility_summary']
            pool_optimization = processing_results['pool_optimization']

            # ✅ Fail-Fast: 檢查階段完成狀態字段
            if 'stage_4_1_completed' not in metadata:
                logger.error("❌ metadata 缺少必需字段 'stage_4_1_completed'")
                return False

            if 'stage_4_2_completed' not in metadata:
                logger.error("❌ metadata 缺少必需字段 'stage_4_2_completed'")
                return False

            stage_4_1_completed = metadata['stage_4_1_completed']
            stage_4_2_completed = metadata['stage_4_2_completed']

            # ✅ Fail-Fast: 檢查驗證結果結構
            if 'validation_results' not in pool_optimization:
                logger.error("❌ pool_optimization 缺少必需字段 'validation_results'")
                return False

            validation_results = pool_optimization['validation_results']

            if 'starlink' not in validation_results:
                logger.error("❌ validation_results 缺少必需字段 'starlink'")
                return False

            starlink_validation = validation_results['starlink']

            if 'validation_passed' not in starlink_validation:
                logger.error("❌ starlink_validation 缺少必需字段 'validation_passed'")
                return False

            starlink_passed = starlink_validation['validation_passed']

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
