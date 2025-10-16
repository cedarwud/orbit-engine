#!/usr/bin/env python3
"""
Stage 6: 驗證快照管理器 (重構版本 - 使用 BaseResultManager)

核心職責:
1. 保存驗證快照到 data/validation_snapshots/
2. 加載歷史驗證快照
3. 提取核心指標摘要

Author: ORBIT Engine Team
Created: 2025-10-02 (重構自 stage6_research_optimization_processor.py)
Refactored: 2025-10-12 (Phase 3: Template Method Pattern Migration)
"""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Phase 3 Refactoring: Import base class
from shared.base import BaseResultManager


class Stage6SnapshotManager(BaseResultManager):
    """Stage 6 驗證快照管理器 (重構版)

    繼承自 BaseResultManager，使用 Template Method Pattern
    標準化快照管理流程，同時保留 Stage 6 專用功能。

    職責:
    - ✅ 保存驗證快照 (使用基類 template method)
    - ✅ 加載歷史快照 (Stage 6 專用功能)
    - ✅ 提取核心指標摘要 (Stage 6 專用功能)

    重構亮點:
    - 消除與其他階段的重複代碼 (目錄創建、JSON保存、時間戳生成)
    - 使用 Fail-Fast 字段檢查工具
    - 保留所有原有功能，100% 向後兼容
    """

    def __init__(self, logger: logging.Logger = None, snapshot_dir: Optional[Path] = None):
        """初始化快照管理器

        Args:
            logger: 日誌記錄器，如未提供則創建新的
            snapshot_dir: 快照目錄，默認為 data/validation_snapshots (保留向後兼容性)
        """
        # 初始化基類
        super().__init__(logger_instance=logger)

        # Stage 6 專用配置 (保留原有接口)
        self.snapshot_dir = snapshot_dir or Path('data/validation_snapshots')

    # ==================== Abstract Methods Implementation (Required by BaseResultManager) ====================

    def get_stage_number(self) -> int:
        """返回階段編號"""
        return 6

    def get_stage_identifier(self) -> str:
        """返回階段識別字串"""
        return 'stage6_research_optimization'

    def build_stage_results(self, **kwargs) -> Dict[str, Any]:
        """
        構建 Stage 6 結果結構 (暫未使用，Stage 6 主要使用快照功能)

        Note:
            Stage 6 的結果構建由 stage6_research_optimization_processor.py 負責
            這個方法保留作為接口一致性，但通常不直接調用
        """
        processing_results = kwargs.get('processing_results', {})
        return processing_results

    def build_snapshot_data(
        self,
        processing_results: Dict[str, Any],
        processing_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        構建 Stage 6 專用驗證快照數據

        基類會自動添加: stage, stage_number, timestamp, validation_passed

        Args:
            processing_results: Stage 6 完整處理結果
            processing_stats: 處理統計 (Stage 6 通常直接從 metadata 提取)

        Returns:
            Stage 6 專用快照字段
        """
        # 提取驗證結果
        validation_results = processing_results.get('validation_results', {})

        # 提取核心數據區塊
        metadata = processing_results.get('metadata', {})
        gpp_events = processing_results.get('gpp_events', {})
        pool_verification = processing_results.get('pool_verification', {})
        ml_training_data = processing_results.get('ml_training_data', {})
        decision_support = processing_results.get('decision_support', {})

        # 構建 Stage 6 專用快照數據
        return {
            'stage_name': 'research_optimization',
            'status': 'success' if validation_results.get('overall_status') == 'PASS' else 'failed',
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
            'validation_status': 'passed' if validation_results.get('overall_status') == 'PASS' else 'failed',
            'next_stage_ready': validation_results.get('overall_status') == 'PASS'
        }

    # ==================== Public Interface (Backward Compatibility) ====================

    def save_validation_snapshot(
        self,
        processing_results: Dict[str, Any],
        validation_results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        保存驗證快照到 data/validation_snapshots/stage6_validation.json

        ✅ 重構後使用基類 template method，保留原有接口簽名

        Args:
            processing_results: Stage 6 處理結果
            validation_results: 驗證結果 (可選，如未提供則從 processing_results 中提取)

        Returns:
            bool: 保存是否成功
        """
        try:
            # 如果提供了外部 validation_results，注入到 processing_results
            # (保持原有接口行為)
            if validation_results is not None:
                processing_results = {
                    **processing_results,
                    'validation_results': validation_results
                }

            # 使用基類的 template method (標準化流程)
            # processing_stats 留空字典 (Stage 6 從 metadata 提取統計數據)
            return super().save_validation_snapshot(
                processing_results=processing_results,
                processing_stats={}
            )

        except Exception as e:
            self.logger.error(f"保存驗證快照失敗: {e}", exc_info=True)
            return False

    # ==================== Stage 6 Specific Methods (Not in Base Class) ====================

    def load_validation_snapshot(
        self,
        snapshot_name: str = 'stage6_validation.json'
    ) -> Optional[Dict[str, Any]]:
        """
        加載驗證快照

        ⚠️ Stage 6 專用功能 (基類不提供，其他階段通常不需要載入快照)

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
        """
        提取核心指標摘要

        ⚠️ Stage 6 專用功能 (用於生成簡報或摘要報告)

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


# ==================== Backward Compatibility Helper ====================

def create_stage6_snapshot_manager(
    logger: logging.Logger = None,
    snapshot_dir: Optional[Path] = None
) -> Stage6SnapshotManager:
    """
    工廠函數: 創建 Stage 6 快照管理器實例

    Args:
        logger: 日誌記錄器
        snapshot_dir: 快照目錄路徑

    Returns:
        Stage6SnapshotManager 實例
    """
    return Stage6SnapshotManager(logger=logger, snapshot_dir=snapshot_dir)
