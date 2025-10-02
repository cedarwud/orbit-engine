#!/usr/bin/env python3
"""
Stage 6: 輸入輸出驗證器

核心職責:
1. 驗證 Stage 5 輸出格式與完整性
2. 驗證時間序列數據存在性
3. 驗證 Stage 6 輸出格式

Author: ORBIT Engine Team
Created: 2025-10-02 (重構自 stage6_research_optimization_processor.py)
"""

import logging
from typing import Dict, Any, List


class Stage6InputOutputValidator:
    """Stage 6 輸入輸出驗證器

    負責驗證:
    - Stage 5 輸出格式 (signal_analysis, connectable_satellites, metadata)
    - 時間序列數據完整性
    - Stage 6 輸出格式
    """

    def __init__(self, logger: logging.Logger = None):
        """初始化驗證器

        Args:
            logger: 日誌記錄器，如未提供則創建新的
        """
        self.logger = logger or logging.getLogger(__name__)

    def validate_stage5_output(self, input_data: Any) -> bool:
        """驗證 Stage 5 輸出格式

        依據: stage6-research-optimization.md Lines 220-260
        必要字段: signal_analysis, analysis_summary, connectable_satellites, metadata

        Args:
            input_data: Stage 5 輸出數據

        Returns:
            bool: 驗證是否通過
        """
        if not isinstance(input_data, dict):
            self.logger.error("❌ 輸入數據必須是字典格式")
            return False

        # 🚨 P0: 檢查必要字段存在性
        required_fields = {
            'signal_analysis': '信號品質分析數據 (3GPP事件檢測核心)',
            'connectable_satellites': '可連線衛星池 (動態池驗證核心)',
            'metadata': '元數據 (constellation_configs 傳遞)'
        }

        missing_fields = []
        for field, description in required_fields.items():
            if field not in input_data:
                missing_fields.append(f"{field} ({description})")
                self.logger.error(f"❌ 缺少必要字段: {field} - {description}")

        if missing_fields:
            self.logger.error(f"❌ Stage 5 輸出驗證失敗: 缺少 {len(missing_fields)} 個必要字段")
            return False

        # 檢查 signal_analysis 格式
        signal_analysis = input_data.get('signal_analysis', {})
        if not isinstance(signal_analysis, dict) or len(signal_analysis) == 0:
            self.logger.error("❌ signal_analysis 必須是非空字典")
            return False

        # 抽樣檢查 signal_analysis 數據結構
        sample_satellite_id = next(iter(signal_analysis.keys()), None)
        if sample_satellite_id:
            sample_data = signal_analysis[sample_satellite_id]
            # 🔧 修復: Stage 5 v3.0 輸出格式為 'summary', 'time_series', 'physical_parameters'
            # 不是 'signal_quality', 'quality_assessment'
            required_sub_fields = ['summary', 'time_series', 'physical_parameters']
            for sub_field in required_sub_fields:
                if sub_field not in sample_data:
                    self.logger.error(f"❌ signal_analysis[{sample_satellite_id}] 缺少字段: {sub_field}")
                    return False

            # 檢查 RSRP 字段 (3GPP 事件核心) - 在 summary 中
            summary = sample_data.get('summary', {})
            if 'average_rsrp_dbm' not in summary:
                self.logger.error(f"❌ summary 缺少 average_rsrp_dbm (3GPP 事件檢測必要)")
                return False

        # 檢查 connectable_satellites 格式
        connectable_satellites = input_data.get('connectable_satellites', {})
        if not isinstance(connectable_satellites, dict):
            self.logger.error("❌ connectable_satellites 必須是字典")
            return False

        # 檢查星座分類
        expected_constellations = ['starlink', 'oneweb']
        for constellation in expected_constellations:
            if constellation not in connectable_satellites:
                self.logger.warning(f"⚠️ connectable_satellites 缺少星座: {constellation}")

        # 檢查 metadata 中的 constellation_configs
        metadata = input_data.get('metadata', {})
        if 'constellation_configs' not in metadata:
            self.logger.warning("⚠️ metadata 缺少 constellation_configs (將嘗試從 Stage 1 回退)")

        self.logger.info(f"✅ Stage 5 輸出驗證通過")
        self.logger.info(f"   - signal_analysis: {len(signal_analysis)} 顆衛星")
        self.logger.info(f"   - connectable_satellites: {sum(len(sats) for sats in connectable_satellites.values())} 顆")
        return True

    def validate_time_series_presence(self, connectable_satellites: Dict[str, List]) -> bool:
        """驗證 connectable_satellites 是否包含時間序列數據

        依據: stage6-research-optimization.md Lines 267-316
        正確格式: satellites[]['time_series'][] 包含多個時間點

        Args:
            connectable_satellites: 可連線衛星池數據

        Returns:
            bool: 是否包含有效的時間序列數據
        """
        try:
            for constellation, satellites in connectable_satellites.items():
                if not satellites or len(satellites) == 0:
                    continue

                # 抽樣檢查第一顆衛星
                sample_sat = satellites[0]
                if 'time_series' in sample_sat:
                    time_series = sample_sat['time_series']
                    if isinstance(time_series, list) and len(time_series) > 0:
                        self.logger.info(
                            f"✅ {constellation} 包含時間序列數據 "
                            f"({len(time_series)}個時間點/顆衛星)"
                        )
                        return True
                    else:
                        self.logger.warning(f"⚠️ {constellation} time_series 為空")
                else:
                    self.logger.warning(f"⚠️ {constellation} 缺少 time_series 字段")

            return False

        except Exception as e:
            self.logger.error(f"時間序列驗證異常: {e}")
            return False

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證 Stage 6 輸出數據

        Args:
            output_data: Stage 6 輸出數據

        Returns:
            Dict: 驗證結果
                {
                    'is_valid': bool,
                    'errors': List[str],
                    'warnings': List[str]
                }
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            if not isinstance(output_data, dict):
                validation_result['errors'].append("輸出數據必須是字典格式")
                return validation_result

            required_keys = ['stage', 'gpp_events', 'metadata']
            for key in required_keys:
                if key not in output_data:
                    validation_result['errors'].append(f"缺少必要字段: {key}")

            if output_data.get('stage') != 'stage6_research_optimization':
                validation_result['errors'].append("stage 標識不正確")

            validation_result['is_valid'] = len(validation_result['errors']) == 0

        except Exception as e:
            validation_result['errors'].append(f"驗證過程異常: {str(e)}")

        return validation_result
