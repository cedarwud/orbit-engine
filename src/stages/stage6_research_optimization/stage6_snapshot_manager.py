#!/usr/bin/env python3
"""
Stage 6: 驗證快照管理器

核心職責:
1. 保存驗證快照到 data/validation_snapshots/
2. 加載歷史驗證快照
3. 提取核心指標摘要

Author: ORBIT Engine Team
Created: 2025-10-02 (重構自 stage6_research_optimization_processor.py)
"""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


class Stage6SnapshotManager:
    """Stage 6 驗證快照管理器

    負責:
    - 保存驗證快照到標準路徑
    - 加載歷史快照進行比對
    - 提取核心指標摘要
    """

    def __init__(self, logger: logging.Logger = None, snapshot_dir: Optional[Path] = None):
        """初始化快照管理器

        Args:
            logger: 日誌記錄器，如未提供則創建新的
            snapshot_dir: 快照目錄，默認為 data/validation_snapshots
        """
        self.logger = logger or logging.getLogger(__name__)
        self.snapshot_dir = snapshot_dir or Path('data/validation_snapshots')

    def save_validation_snapshot(self, processing_results: Dict[str, Any],
                                validation_results: Optional[Dict[str, Any]] = None) -> bool:
        """保存驗證快照到 data/validation_snapshots/stage6_validation.json

        Args:
            processing_results: Stage 6 處理結果
            validation_results: 驗證結果 (可選，如未提供則從 processing_results 中提取)

        Returns:
            bool: 保存是否成功
        """
        try:
            # 確保目錄存在
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)

            # 提取或使用提供的驗證結果
            if validation_results is None:
                validation_results = processing_results.get('validation_results', {})

            # 提取核心指標
            metadata = processing_results.get('metadata', {})
            gpp_events = processing_results.get('gpp_events', {})
            pool_verification = processing_results.get('pool_verification', {})
            ml_training_data = processing_results.get('ml_training_data', {})
            decision_support = processing_results.get('decision_support', {})

            # 構建快照數據
            snapshot_data = {
                'stage': processing_results.get('stage', 'stage6_research_optimization'),
                'stage_name': 'research_optimization',
                'status': 'success' if validation_results.get('overall_status') == 'PASS' else 'failed',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'validation_results': validation_results,
                'metadata': metadata,
                'gpp_events': gpp_events,
                'pool_verification': pool_verification,
                'ml_training_data': ml_training_data,
                'decision_support': decision_support,
                'data_summary': {
                    'total_events_detected': metadata.get('total_events_detected', 0),
                    'ml_training_samples': metadata.get('ml_training_samples', 0),
                    'pool_verification_passed': metadata.get('pool_verification_passed', False),
                    'handover_decisions': metadata.get('handover_decisions', 0),
                    'decision_support_calls': metadata.get('decision_support_calls', 0)
                },
                'validation_passed': validation_results.get('overall_status') == 'PASS',
                'next_stage_ready': validation_results.get('overall_status') == 'PASS'
            }

            # 保存快照
            snapshot_path = self.snapshot_dir / 'stage6_validation.json'
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ Stage 6 驗證快照已保存: {snapshot_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存驗證快照失敗: {e}", exc_info=True)
            return False

    def load_validation_snapshot(self, snapshot_name: str = 'stage6_validation.json') -> Optional[Dict[str, Any]]:
        """加載驗證快照

        Args:
            snapshot_name: 快照檔案名稱，默認為 stage6_validation.json

        Returns:
            Optional[Dict]: 快照數據，如果加載失敗則返回 None
        """
        try:
            snapshot_path = self.snapshot_dir / snapshot_name

            if not snapshot_path.exists():
                self.logger.warning(f"快照檔案不存在: {snapshot_path}")
                return None

            with open(snapshot_path, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)

            self.logger.info(f"✅ 加載驗證快照: {snapshot_path}")
            return snapshot_data

        except Exception as e:
            self.logger.error(f"加載驗證快照失敗: {e}", exc_info=True)
            return None

    def extract_summary(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取核心指標摘要

        Args:
            processing_results: Stage 6 處理結果

        Returns:
            Dict: 核心指標摘要
        """
        metadata = processing_results.get('metadata', {})

        return {
            'total_events_detected': metadata.get('total_events_detected', 0),
            'ml_training_samples': metadata.get('ml_training_samples', 0),
            'pool_verification_passed': metadata.get('pool_verification_passed', False),
            'handover_decisions': metadata.get('handover_decisions', 0),
            'decision_support_calls': metadata.get('decision_support_calls', 0),
            'gpp_standard_compliance': metadata.get('gpp_standard_compliance', False),
            'ml_research_readiness': metadata.get('ml_research_readiness', False),
            'real_time_capability': metadata.get('real_time_capability', False),
            'academic_standard': metadata.get('academic_standard', 'Unknown')
        }
