#!/usr/bin/env python3
"""
Stage 5 合規驗證模組 - 學術標準驗證器

✅ Grade A+ 標準: 100% Fail-Fast 驗證
依據: docs/ACADEMIC_STANDARDS.md Line 265-274

專職責任：
- 輸入/輸出數據格式驗證
- 3GPP TS 38.214 標準合規性驗證
- ITU-R P.618-13 標準合規性驗證
- 時間序列結構完整性檢查
- 數據品質評估

學術合規：Grade A 標準
- 合規標記必須基於實際驗證，禁止硬編碼
- 所有驗證邏輯必須有標準依據
- 禁止使用 `.get()` 預設值回退

Updated: 2025-10-04 - Fail-Fast 重構
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Stage5ComplianceValidator:
    """
    Stage 5 合規驗證器

    實現學術標準驗證:
    - 3GPP TS 38.214/38.215: NTN 信號品質標準
    - ITU-R P.618-13: 大氣傳播與物理模型
    - CODATA 2018: 物理常數標準
    """

    def __init__(self):
        """初始化合規驗證器"""
        self.logger = logging.getLogger(__name__)

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """
        驗證輸入數據

        ✅ Grade A+ 標準: Fail-Fast 輸入驗證

        Args:
            input_data: Stage 4 輸出數據

        Returns:
            Dict: {'valid': bool, 'errors': list, 'warnings': list}
        """
        errors = []
        warnings = []

        # 第 1 層: 類型驗證
        if not isinstance(input_data, dict):
            errors.append("輸入數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # 第 2 層: 結構驗證
        # 🔧 修復: Stage 4 重構後輸出 connectable_satellites，向後兼容 satellites
        if 'stage' not in input_data:
            errors.append("缺少必需字段: stage")

        # 檢查衛星數據字段 (新格式 connectable_satellites 或舊格式 satellites)
        has_connectable_satellites = 'connectable_satellites' in input_data
        has_satellites = 'satellites' in input_data

        if not has_connectable_satellites and not has_satellites:
            errors.append("缺少必需字段: connectable_satellites 或 satellites")

        # 如果缺少必要字段，提前返回
        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # 第 3 層: 字段值驗證
        # 驗證 stage 字段
        stage_value = input_data['stage']
        if stage_value not in ['stage4_link_feasibility', 'stage4_optimization']:
            errors.append(f"輸入階段標識錯誤: {stage_value} (期望: stage4_link_feasibility 或 stage4_optimization)")

        # ✅ Fail-Fast: 明確檢查衛星數據字段（向後兼容新舊格式）
        if has_connectable_satellites:
            satellites = input_data['connectable_satellites']
        elif has_satellites:
            satellites = input_data['satellites']
        else:
            # 這種情況已在上面的錯誤檢查中捕獲，不應到達這裡
            errors.append("內部錯誤：衛星數據字段檢查邏輯異常")
            satellites = None

        # 驗證衛星數據類型和內容
        if satellites is not None:
            if not isinstance(satellites, dict):
                errors.append(f"衛星數據格式錯誤: {type(satellites).__name__} (期望: dict)")
            elif len(satellites) == 0:
                warnings.append("衛星數據為空 - Stage 5 可能無衛星需要處理")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """
        驗證輸出數據

        ✅ Grade A+ 標準: Fail-Fast 輸出驗證

        Args:
            output_data: Stage 5 處理結果

        Returns:
            Dict: {'valid': bool, 'errors': list, 'warnings': list}
        """
        errors = []
        warnings = []

        # 第 1 層: 類型驗證
        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # 第 2 層: 結構驗證
        required_fields = ['stage', 'signal_analysis', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        # 如果缺少必要字段，提前返回
        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # 第 3 層: 字段值驗證
        stage_value = output_data['stage']
        if stage_value != 5:
            errors.append(f"階段標識錯誤: {stage_value} (期望: 5)")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行完整驗證檢查

        ✅ Grade A+ 標準: Fail-Fast 完整驗證

        驗證項目:
        1. 時間序列結構完整性
        2. 3GPP 標準合規性
        3. ITU-R 物理模型驗證
        4. 數據品質評估

        Args:
            results: Stage 5 處理結果

        Returns:
            Dict: 驗證結果
        """
        validation_results = {
            'passed': True,
            'checks': {},
            'errors': [],
            'warnings': []
        }

        try:
            # ============================================================================
            # 檢查 1: 基本結構驗證
            # ============================================================================

            if 'stage' not in results:
                validation_results['errors'].append('缺少 stage 字段')
                validation_results['passed'] = False

            if 'signal_analysis' not in results:
                validation_results['errors'].append('缺少 signal_analysis 字段')
                validation_results['passed'] = False
                # 如果缺少核心數據，無法繼續驗證
                validation_results['validation_status'] = 'failed'
                validation_results['overall_status'] = 'FAIL'
                return validation_results

            signal_analysis = results['signal_analysis']
            if not isinstance(signal_analysis, dict):
                validation_results['errors'].append('signal_analysis 必須是字典格式')
                validation_results['passed'] = False
                validation_results['validation_status'] = 'failed'
                validation_results['overall_status'] = 'FAIL'
                return validation_results

            # ============================================================================
            # 檢查 2: 時間序列結構驗證
            # ============================================================================

            satellites_with_time_series = 0
            total_time_points = 0

            for sat_id, sat_data in signal_analysis.items():
                # 驗證必要字段
                required_fields = ['satellite_id', 'time_series', 'summary', 'physical_parameters']
                for field in required_fields:
                    if field not in sat_data:
                        validation_results['errors'].append(f'衛星 {sat_id} 缺少 {field} 字段')
                        validation_results['passed'] = False

                # 驗證時間序列結構
                if 'time_series' not in sat_data:
                    continue

                time_series = sat_data['time_series']
                if not isinstance(time_series, list):
                    validation_results['errors'].append(f'衛星 {sat_id} time_series 必須是列表格式')
                    validation_results['passed'] = False
                    continue

                if len(time_series) == 0:
                    validation_results['warnings'].append(f'衛星 {sat_id} time_series 為空')
                    continue

                satellites_with_time_series += 1
                total_time_points += len(time_series)

                # 抽樣檢查第一個時間點結構
                first_point = time_series[0]
                required_point_fields = ['timestamp', 'signal_quality', 'is_connectable', 'physical_parameters']
                for field in required_point_fields:
                    if field not in first_point:
                        validation_results['warnings'].append(
                            f'衛星 {sat_id} 時間點缺少 {field} 字段'
                        )

                # ============================================================================
                # 檢查 3: 3GPP 標準合規性
                # ============================================================================

                if 'signal_quality' in first_point:
                    signal_quality = first_point['signal_quality']

                    if 'calculation_standard' not in signal_quality:
                        validation_results['warnings'].append(
                            f'衛星 {sat_id} 缺少 calculation_standard 標記'
                        )
                    elif signal_quality['calculation_standard'] != '3GPP_TS_38.214':
                        validation_results['errors'].append(
                            f'衛星 {sat_id} 標準不符: {signal_quality["calculation_standard"]} (期望: 3GPP_TS_38.214)'
                        )
                        validation_results['passed'] = False

                    # 驗證信號品質值範圍
                    if 'rsrp_dbm' in signal_quality:
                        rsrp = signal_quality['rsrp_dbm']
                        if rsrp is not None and (rsrp < -140 or rsrp > -44):
                            validation_results['warnings'].append(
                                f'衛星 {sat_id} RSRP 超出 3GPP 範圍: {rsrp} dBm (標準: -140 to -44)'
                            )

            # ============================================================================
            # 檢查 4: metadata 完整性驗證
            # ============================================================================

            if 'metadata' not in results:
                validation_results['errors'].append('缺少 metadata 字段')
                validation_results['passed'] = False
            else:
                metadata = results['metadata']

                # 驗證 3GPP 配置
                if 'gpp_config' not in metadata:
                    validation_results['warnings'].append('缺少 gpp_config')

                # 驗證 ITU-R 配置
                if 'itur_config' not in metadata:
                    validation_results['warnings'].append('缺少 itur_config')

                # 驗證合規標記
                if 'gpp_standard_compliance' not in metadata:
                    validation_results['errors'].append('metadata 缺少 gpp_standard_compliance 字段')
                    validation_results['passed'] = False
                elif metadata['gpp_standard_compliance'] != True:
                    validation_results['errors'].append(
                        f'3GPP 標準合規性未通過: {metadata["gpp_standard_compliance"]}'
                    )
                    validation_results['passed'] = False

                if 'time_series_processing' not in metadata:
                    validation_results['errors'].append('時間序列處理標記缺失')
                    validation_results['passed'] = False
                elif metadata['time_series_processing'] != True:
                    validation_results['errors'].append(
                        f'時間序列處理標記未通過: {metadata["time_series_processing"]}'
                    )
                    validation_results['passed'] = False

            # ============================================================================
            # 檢查 5: 分析摘要驗證
            # ============================================================================

            if 'analysis_summary' in results:
                analysis_summary = results['analysis_summary']
                if 'total_time_points_processed' not in analysis_summary:
                    validation_results['warnings'].append('缺少 total_time_points_processed 統計')

            # ============================================================================
            # 構建檢查摘要
            # ============================================================================

            # ✅ Fail-Fast: 明確檢查 metadata 中的合規字段
            gpp_compliance = False
            itur_compliance = False
            time_series_processing = False

            if 'metadata' in results:
                metadata_local = results['metadata']

                if 'gpp_standard_compliance' in metadata_local:
                    gpp_compliance = metadata_local['gpp_standard_compliance']
                else:
                    validation_results['warnings'].append('metadata 缺少 gpp_standard_compliance 字段')

                if 'itur_standard_compliance' in metadata_local:
                    itur_compliance = metadata_local['itur_standard_compliance']
                else:
                    validation_results['warnings'].append('metadata 缺少 itur_standard_compliance 字段')

                if 'time_series_processing' in metadata_local:
                    time_series_processing = metadata_local['time_series_processing']
                else:
                    validation_results['warnings'].append('metadata 缺少 time_series_processing 字段')

            validation_results['checks'] = {
                'structure_valid': len(validation_results['errors']) == 0,
                'satellite_count': len(signal_analysis),
                'satellites_with_time_series': satellites_with_time_series,
                'total_time_points': total_time_points,
                'has_metadata': 'metadata' in results,
                'gpp_compliance': gpp_compliance,
                'itur_compliance': itur_compliance,
                'time_series_processing': time_series_processing
            }

            # 添加主腳本期望的字段格式
            if validation_results['passed']:
                validation_results['validation_status'] = 'passed'
                validation_results['overall_status'] = 'PASS'
                validation_results['validation_details'] = {
                    'success_rate': 1.0,
                    'satellite_count': len(signal_analysis),
                    'time_points_processed': total_time_points
                }
            else:
                validation_results['validation_status'] = 'failed'
                validation_results['overall_status'] = 'FAIL'
                validation_results['validation_details'] = {
                    'success_rate': 0.0,
                    'error_count': len(validation_results['errors'])
                }

        except Exception as e:
            validation_results['errors'].append(f'驗證檢查執行失敗: {str(e)}')
            validation_results['passed'] = False
            validation_results['validation_status'] = 'error'
            validation_results['overall_status'] = 'ERROR'

        return validation_results

    def verify_3gpp_compliance(self, analyzed_satellites: Dict[str, Any]) -> bool:
        """
        驗證是否真正符合 3GPP TS 38.214 標準

        ✅ Grade A+ 標準: Fail-Fast 合規驗證
        依據: docs/ACADEMIC_STANDARDS.md Line 23-26, 265-274

        檢查項目:
        1. 所有信號品質計算是否使用 3GPP_TS_38.214 標記
        2. RSRP 範圍是否在物理合理範圍 -140 to -20 dBm (LEO場景允許 > -44 dBm)
        3. RSRQ/SINR 是否存在且在合理範圍

        Args:
            analyzed_satellites: 分析後的衛星數據

        Returns:
            True: 完全符合 3GPP 標準
            False: 存在違規
        """
        if not analyzed_satellites:
            self.logger.warning("⚠️ 3GPP 合規驗證: 無衛星數據")
            return False

        total_points_checked = 0
        compliant_points = 0

        for sat_id, sat_data in analyzed_satellites.items():
            # Fail-Fast: 驗證必要字段存在
            if 'time_series' not in sat_data:
                self.logger.warning(f"⚠️ 衛星 {sat_id} 缺少 time_series 字段")
                continue

            time_series = sat_data['time_series']

            if not isinstance(time_series, list):
                self.logger.warning(f"⚠️ 衛星 {sat_id} time_series 不是列表")
                continue

            if not time_series:
                continue

            for point in time_series:
                total_points_checked += 1

                # Fail-Fast: 驗證 signal_quality 存在
                if 'signal_quality' not in point:
                    self.logger.debug(f"時間點缺少 signal_quality")
                    continue

                signal_quality = point['signal_quality']

                # ✅ 檢查 1: 標準標記驗證
                if 'calculation_standard' not in signal_quality:
                    self.logger.debug(f"衛星 {sat_id} 缺少 calculation_standard")
                    continue

                calc_standard = signal_quality['calculation_standard']
                if calc_standard != '3GPP_TS_38.214':
                    self.logger.debug(
                        f"衛星 {sat_id} 標準標記不符: {calc_standard} (期望: 3GPP_TS_38.214)"
                    )
                    continue

                # ✅ 檢查 2: RSRP 範圍驗證 (3GPP TS 38.215 Section 5.1.1)
                if 'rsrp_dbm' not in signal_quality:
                    self.logger.debug(f"衛星 {sat_id} 缺少 RSRP 數據")
                    continue

                rsrp = signal_quality['rsrp_dbm']
                if rsrp is None:
                    self.logger.debug(f"衛星 {sat_id} RSRP 為 None")
                    continue

                # SOURCE: 3GPP TS 38.215 v18.1.0 Section 5.1.1
                # - UE 報告量化範圍: -140 to -44 dBm (用於 RRC 訊息報告)
                # - 物理 RSRP 可以 > -44 dBm (近距離、高增益、LEO 衛星場景)
                # - 學術研究應保留真實計算值，不應截斷至報告範圍
                # - 物理上限: -20 dBm (考慮 LEO 衛星近距離高增益場景)
                if rsrp < -140 or rsrp > -20:
                    self.logger.debug(
                        f"衛星 {sat_id} RSRP 超出物理範圍: {rsrp:.1f} dBm (物理範圍: -140 to -20 dBm，3GPP UE報告範圍: -140 to -44 dBm)"
                    )
                    continue

                # ✅ 檢查 3: RSRQ 範圍驗證 (3GPP TS 38.215 Section 5.1.3)
                if 'rsrq_db' in signal_quality:
                    rsrq = signal_quality['rsrq_db']
                    if rsrq is not None:
                        if rsrq < -34 or rsrq > 2.5:
                            self.logger.debug(
                                f"衛星 {sat_id} RSRQ 超出 3GPP 範圍: {rsrq} dB (標準範圍: -34 to 2.5)"
                            )
                            continue

                # ✅ 檢查 4: SINR 範圍驗證 (3GPP TS 38.215 Section 5.1.4)
                if 'sinr_db' in signal_quality:
                    sinr = signal_quality['sinr_db']
                    if sinr is not None:
                        if sinr < -23 or sinr > 40:
                            self.logger.debug(
                                f"衛星 {sat_id} SINR 超出 3GPP 範圍: {sinr} dB (標準範圍: -23 to 40)"
                            )
                            continue

                # 通過所有檢查
                compliant_points += 1

        # 計算合規率
        if total_points_checked == 0:
            self.logger.warning("⚠️ 3GPP 合規驗證: 無有效時間點數據")
            return False

        compliance_rate = compliant_points / total_points_checked

        # ✅ 要求 95% 以上的數據點符合標準
        is_compliant = compliance_rate >= 0.95

        self.logger.info(
            f"📊 3GPP 合規驗證: {compliant_points}/{total_points_checked} "
            f"({compliance_rate:.1%}) - {'✅ 通過' if is_compliant else '❌ 未通過'}"
        )

        return is_compliant

    def verify_itur_compliance(self, metadata: Dict[str, Any]) -> bool:
        """
        驗證是否真正符合 ITU-R 標準

        ✅ Grade A+ 標準: Fail-Fast 合規驗證
        依據: docs/ACADEMIC_STANDARDS.md Line 23-26, 265-274

        檢查項目:
        1. 物理常數是否符合 CODATA 2018 標準
        2. ITU-R 配置是否使用 P.618-13 完整模型
        3. 大氣模型是否為完整實現

        Args:
            metadata: 處理結果的 metadata

        Returns:
            True: 完全符合 ITU-R 標準
            False: 存在違規
        """
        # ✅ 檢查 1: 物理常數標準
        if 'physical_constants' not in metadata:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 physical_constants")
            return False

        physical_constants = metadata['physical_constants']

        if 'standard_compliance' not in physical_constants:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 standard_compliance")
            return False

        if physical_constants['standard_compliance'] != 'CODATA_2018':
            self.logger.warning(
                f"⚠️ ITU-R 合規驗證: 物理常數標準不符 ({physical_constants['standard_compliance']} != CODATA_2018)"
            )
            return False

        # ✅ 檢查 2: ITU-R 配置驗證
        if 'itur_config' not in metadata:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 itur_config")
            return False

        itur_config = metadata['itur_config']

        if 'recommendation' not in itur_config:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 recommendation")
            return False

        recommendation = itur_config['recommendation']
        if 'P.618' not in recommendation:
            self.logger.warning(
                f"⚠️ ITU-R 合規驗證: 標準不符 ({recommendation} 不包含 P.618)"
            )
            return False

        # ✅ 檢查 3: 大氣模型完整性
        if 'atmospheric_model' not in itur_config:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 atmospheric_model")
            return False

        atmospheric_model = itur_config['atmospheric_model']
        if atmospheric_model != 'complete':
            self.logger.warning(
                f"⚠️ ITU-R 合規驗證: 大氣模型非完整實現 ({atmospheric_model} != complete)"
            )
            return False

        # ✅ 檢查 4: 光速常數驗證 (CODATA 2018)
        if 'speed_of_light_m_s' not in physical_constants:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 speed_of_light_m_s")
            return False

        speed_of_light = physical_constants['speed_of_light_m_s']
        expected_c = 299792458  # CODATA 2018 exact value
        if abs(speed_of_light - expected_c) > 1:  # 容許 1 m/s 誤差
            self.logger.warning(
                f"⚠️ ITU-R 合規驗證: 光速常數不符 CODATA 2018 ({speed_of_light} != {expected_c})"
            )
            return False

        self.logger.info("✅ ITU-R 合規驗證通過")
        return True


def create_stage5_validator() -> Stage5ComplianceValidator:
    """創建 Stage 5 合規驗證器實例"""
    return Stage5ComplianceValidator()
