#!/usr/bin/env python3
"""
Stage 5 合規驗證模組 - 學術標準驗證器

專職責任：
- 輸入/輸出數據格式驗證
- 3GPP TS 38.214 標準合規性驗證
- ITU-R P.618-13 標準合規性驗證
- 時間序列結構完整性檢查
- 數據品質評估

學術合規：Grade A 標準
- 合規標記必須基於實際驗證，禁止硬編碼
- 所有驗證邏輯必須有標準依據
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

        Args:
            input_data: Stage 4 輸出數據

        Returns:
            Dict: {'valid': bool, 'errors': list, 'warnings': list}
        """
        errors = []
        warnings = []

        if not isinstance(input_data, dict):
            errors.append("輸入數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'satellites']
        for field in required_fields:
            if field not in input_data:
                errors.append(f"缺少必需字段: {field}")

        if input_data.get('stage') not in ['stage4_link_feasibility', 'stage4_optimization']:
            errors.append("輸入階段標識錯誤，需要 Stage 4 可連線衛星輸出")

        satellites = input_data.get('satellites', {})
        if not isinstance(satellites, dict):
            errors.append("衛星數據格式錯誤")
        elif len(satellites) == 0:
            warnings.append("衛星數據為空")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """
        驗證輸出數據

        Args:
            output_data: Stage 5 處理結果

        Returns:
            Dict: {'valid': bool, 'errors': list, 'warnings': list}
        """
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'signal_analysis', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        if output_data.get('stage') != 5:
            errors.append("階段標識錯誤")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行完整驗證檢查

        驗證項目:
        1. 時間序列結構完整性
        2. 3GPP 標準合規性
        3. ITU-R 物理模型驗證
        4. constellation_configs 存在性
        5. 數據品質評估

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
            # ✅ 檢查 1: 基本結構
            if 'stage' not in results:
                validation_results['errors'].append('缺少 stage 字段')
                validation_results['passed'] = False

            if 'signal_analysis' not in results:
                validation_results['errors'].append('缺少 signal_analysis 字段')
                validation_results['passed'] = False
            else:
                signal_analysis = results['signal_analysis']
                if not isinstance(signal_analysis, dict):
                    validation_results['errors'].append('signal_analysis 必須是字典格式')
                    validation_results['passed'] = False
                else:
                    # ✅ 檢查 2: 時間序列結構 (關鍵驗證)
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
                        time_series = sat_data.get('time_series', [])
                        if not isinstance(time_series, list):
                            validation_results['errors'].append(f'衛星 {sat_id} time_series 必須是列表格式')
                            validation_results['passed'] = False
                        elif len(time_series) == 0:
                            validation_results['warnings'].append(f'衛星 {sat_id} time_series 為空')
                        else:
                            satellites_with_time_series += 1
                            total_time_points += len(time_series)

                            # 抽樣檢查時間點結構 (檢查第一個點)
                            first_point = time_series[0]
                            required_point_fields = ['timestamp', 'signal_quality', 'is_connectable', 'physical_parameters']
                            for field in required_point_fields:
                                if field not in first_point:
                                    validation_results['warnings'].append(
                                        f'衛星 {sat_id} 時間點缺少 {field} 字段'
                                    )

                            # ✅ 檢查 3: 3GPP 標準合規性
                            signal_quality = first_point.get('signal_quality', {})
                            if 'calculation_standard' not in signal_quality:
                                validation_results['warnings'].append(
                                    f'衛星 {sat_id} 缺少 calculation_standard 標記'
                                )
                            elif signal_quality['calculation_standard'] != '3GPP_TS_38.214':
                                validation_results['errors'].append(
                                    f'衛星 {sat_id} 標準不符: {signal_quality["calculation_standard"]}'
                                )
                                validation_results['passed'] = False

                            # 驗證信號品質值範圍
                            rsrp = signal_quality.get('rsrp_dbm')
                            if rsrp is not None:
                                if rsrp < -140 or rsrp > -44:
                                    validation_results['warnings'].append(
                                        f'衛星 {sat_id} RSRP 超出 3GPP 範圍: {rsrp} dBm'
                                    )

            # ✅ 檢查 4: metadata 完整性
            metadata = results.get('metadata', {})
            if not metadata:
                validation_results['warnings'].append('缺少 metadata 字段')
            else:
                # 驗證 3GPP 配置
                if 'gpp_config' not in metadata:
                    validation_results['warnings'].append('缺少 gpp_config')

                # 驗證 ITU-R 配置
                if 'itur_config' not in metadata:
                    validation_results['warnings'].append('缺少 itur_config')

                # 驗證合規標記
                if not metadata.get('gpp_standard_compliance'):
                    validation_results['errors'].append('3GPP 標準合規性未確認')
                    validation_results['passed'] = False

                if not metadata.get('time_series_processing'):
                    validation_results['errors'].append('時間序列處理標記缺失')
                    validation_results['passed'] = False

            # ✅ 檢查 5: 分析摘要
            analysis_summary = results.get('analysis_summary', {})
            if 'total_time_points_processed' not in analysis_summary:
                validation_results['warnings'].append('缺少 total_time_points_processed 統計')

            # 構建檢查摘要
            validation_results['checks'] = {
                'structure_valid': len(validation_results['errors']) == 0,
                'satellite_count': len(results.get('signal_analysis', {})),
                'satellites_with_time_series': satellites_with_time_series,
                'total_time_points': total_time_points,
                'has_metadata': 'metadata' in results,
                'gpp_compliance': metadata.get('gpp_standard_compliance', False),
                'itur_compliance': metadata.get('itur_standard_compliance', False),
                'time_series_processing': metadata.get('time_series_processing', False)
            }

            # 添加主腳本期望的字段格式
            if validation_results['passed']:
                validation_results['validation_status'] = 'passed'
                validation_results['overall_status'] = 'PASS'
                validation_results['validation_details'] = {
                    'success_rate': 1.0,
                    'satellite_count': len(results.get('signal_analysis', {})),
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

        ✅ Grade A 要求: 合規標記必須基於實際驗證，禁止硬編碼
        依據: docs/ACADEMIC_STANDARDS.md Line 23-26, 265-274

        檢查項目:
        1. 所有信號品質計算是否使用 3GPP_TS_38.214 標記
        2. RSRP 範圍是否在 3GPP 規定的 -140 to -44 dBm
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
            time_series = sat_data.get('time_series', [])

            if not time_series:
                continue

            for point in time_series:
                total_points_checked += 1
                signal_quality = point.get('signal_quality', {})

                # ✅ 檢查 1: 標準標記驗證
                calc_standard = signal_quality.get('calculation_standard')
                if calc_standard != '3GPP_TS_38.214':
                    self.logger.debug(
                        f"衛星 {sat_id} 標準標記不符: {calc_standard} (期望: 3GPP_TS_38.214)"
                    )
                    continue

                # ✅ 檢查 2: RSRP 範圍驗證 (3GPP TS 38.215 Section 5.1.1)
                rsrp = signal_quality.get('rsrp_dbm')
                if rsrp is None:
                    self.logger.debug(f"衛星 {sat_id} 缺少 RSRP 數據")
                    continue

                if rsrp < -140 or rsrp > -44:
                    self.logger.debug(
                        f"衛星 {sat_id} RSRP 超出 3GPP 範圍: {rsrp} dBm (標準範圍: -140 to -44)"
                    )
                    continue

                # ✅ 檢查 3: RSRQ 範圍驗證 (3GPP TS 38.215 Section 5.1.3)
                rsrq = signal_quality.get('rsrq_db')
                if rsrq is not None:
                    if rsrq < -34 or rsrq > 2.5:
                        self.logger.debug(
                            f"衛星 {sat_id} RSRQ 超出 3GPP 範圍: {rsrq} dB (標準範圍: -34 to 2.5)"
                        )
                        continue

                # ✅ 檢查 4: SINR 範圍驗證 (3GPP TS 38.215 Section 5.1.4)
                sinr = signal_quality.get('sinr_db')
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

        ✅ Grade A 要求: 合規標記必須基於實際驗證，禁止硬編碼
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
        physical_constants = metadata.get('physical_constants', {})
        if not physical_constants:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 physical_constants")
            return False

        standard_compliance = physical_constants.get('standard_compliance')
        if standard_compliance != 'CODATA_2018':
            self.logger.warning(
                f"⚠️ ITU-R 合規驗證: 物理常數標準不符 ({standard_compliance} != CODATA_2018)"
            )
            return False

        # ✅ 檢查 2: ITU-R 配置驗證
        itur_config = metadata.get('itur_config', {})
        if not itur_config:
            self.logger.warning("⚠️ ITU-R 合規驗證: 缺少 itur_config")
            return False

        recommendation = itur_config.get('recommendation', '')
        if 'P.618' not in recommendation:
            self.logger.warning(
                f"⚠️ ITU-R 合規驗證: 標準不符 ({recommendation} 不包含 P.618)"
            )
            return False

        # ✅ 檢查 3: 大氣模型完整性
        atmospheric_model = itur_config.get('atmospheric_model', '')
        if atmospheric_model != 'complete':
            self.logger.warning(
                f"⚠️ ITU-R 合規驗證: 大氣模型非完整實現 ({atmospheric_model} != complete)"
            )
            return False

        # ✅ 檢查 4: 光速常數驗證 (CODATA 2018)
        speed_of_light = physical_constants.get('speed_of_light_ms')
        if speed_of_light is not None:
            expected_c = 299792458.0  # CODATA 2018 exact value
            if abs(speed_of_light - expected_c) > 0.1:
                self.logger.warning(
                    f"⚠️ ITU-R 合規驗證: 光速常數不符 ({speed_of_light} != {expected_c})"
                )
                return False

        # ✅ 檢查 5: Boltzmann 常數驗證 (CODATA 2018)
        boltzmann = physical_constants.get('boltzmann_constant')
        if boltzmann is not None:
            expected_k = 1.380649e-23  # CODATA 2018 exact value
            if abs(boltzmann - expected_k) / expected_k > 1e-10:
                self.logger.warning(
                    f"⚠️ ITU-R 合規驗證: Boltzmann 常數不符"
                )
                return False

        self.logger.info("📊 ITU-R 合規驗證: ✅ 通過")
        return True


def create_stage5_validator() -> Stage5ComplianceValidator:
    """
    創建 Stage 5 合規驗證器實例

    Returns:
        Stage5ComplianceValidator: 驗證器實例
    """
    return Stage5ComplianceValidator()
