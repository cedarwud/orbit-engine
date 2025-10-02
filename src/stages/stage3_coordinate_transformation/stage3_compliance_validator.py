#!/usr/bin/env python3
"""
Stage 3: 學術合規檢查器 - 真實算法驗證模組

職責：
- 執行真實算法合規性檢查
- 座標轉換精度驗證
- 真實數據源驗證
- IAU 標準合規檢查
- Skyfield 專業庫使用驗證

學術合規：Grade A 標準
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Stage3ComplianceValidator:
    """Stage 3 學術合規檢查器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化合規檢查器

        Args:
            config: 檢查配置（可選）
        """
        self.config = config or {}
        self.logger = logger

    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行完整的驗證檢查

        Args:
            results: Stage 3 處理結果數據

        Returns:
            驗證結果字典
        """
        self.logger.debug(f"🔍 驗證檢查 - results 類型: {type(results)}")
        self.logger.debug(
            f"🔍 驗證檢查 - results keys: "
            f"{list(results.keys()) if isinstance(results, dict) else 'NOT A DICT'}"
        )

        validation_results = {
            'passed': True,
            'checks': {},
            'errors': [],
            'warnings': []
        }

        try:
            # 1. 真實算法合規性檢查
            real_algo_check = self._check_real_algorithm_compliance(results)
            validation_results['checks']['real_algorithm_compliance'] = real_algo_check

            # 2. 座標轉換精度檢查
            coord_check = self._check_coordinate_transformation_accuracy(results)
            validation_results['checks']['coordinate_transformation_accuracy'] = coord_check

            # 3. 真實數據源驗證
            data_source_check = self._check_real_data_sources(results)
            validation_results['checks']['real_data_sources'] = data_source_check

            # 4. IAU 標準合規檢查
            iau_check = self._check_iau_standard_compliance(results)
            validation_results['checks']['iau_standard_compliance'] = iau_check

            # 5. Skyfield 專業庫驗證
            skyfield_check = self._check_skyfield_professional_usage(results)
            validation_results['checks']['skyfield_professional_usage'] = skyfield_check

            # 總體評估
            all_passed = all(
                check.get('passed', False)
                for check in validation_results['checks'].values()
            )
            validation_results['passed'] = all_passed

            if all_passed:
                validation_results['validation_status'] = 'passed'
                validation_results['overall_status'] = 'PASS'
                validation_results['validation_details'] = {
                    'success_rate': 1.0,
                    'checks_passed': len(validation_results['checks']),
                    'checks_performed': len(validation_results['checks'])
                }
            else:
                validation_results['validation_status'] = 'failed'
                validation_results['overall_status'] = 'FAIL'
                failed_checks = sum(
                    1 for check in validation_results['checks'].values()
                    if not check.get('passed', False)
                )
                validation_results['validation_details'] = {
                    'success_rate': (
                        (len(validation_results['checks']) - failed_checks) /
                        len(validation_results['checks'])
                    ),
                    'checks_failed': failed_checks
                }

        except Exception as e:
            validation_results['errors'].append(f'驗證檢查執行失敗: {str(e)}')
            validation_results['passed'] = False
            validation_results['validation_status'] = 'error'
            validation_results['overall_status'] = 'ERROR'

        return validation_results

    def _check_real_algorithm_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查真實算法合規性"""
        try:
            metadata = results.get('metadata', {})
            real_algo_compliance = metadata.get('real_algorithm_compliance', {})

            hardcoded_used = real_algo_compliance.get('hardcoded_constants_used', True)
            simplified_used = real_algo_compliance.get('simplified_algorithms_used', True)
            mock_data_used = real_algo_compliance.get('mock_data_used', True)
            official_standards = real_algo_compliance.get('official_standards_used', False)

            # 嚴格的真實算法檢查
            violations = []
            if hardcoded_used:
                violations.append("使用了硬編碼常數")
            if simplified_used:
                violations.append("使用了簡化算法")
            if mock_data_used:
                violations.append("使用了模擬數據")
            if not official_standards:
                violations.append("未使用官方標準")

            passed = len(violations) == 0

            return {
                'passed': passed,
                'hardcoded_constants_used': hardcoded_used,
                'simplified_algorithms_used': simplified_used,
                'mock_data_used': mock_data_used,
                'official_standards_used': official_standards,
                'violations': violations,
                'message': (
                    '真實算法完全合規' if passed
                    else f'違反真實算法原則: {", ".join(violations)}'
                )
            }

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _check_coordinate_transformation_accuracy(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """檢查座標轉換精度"""
        try:
            geographic_coords = results.get('geographic_coordinates', {})

            if not geographic_coords:
                return {'passed': False, 'message': '沒有地理座標數據'}

            # 檢查座標範圍合理性
            valid_coords = 0
            total_coords = 0
            accuracy_estimates = []

            for satellite_id, coord_data in geographic_coords.items():
                time_series = coord_data.get('time_series', [])
                for point in time_series:
                    total_coords += 1
                    lat = point.get('latitude_deg')
                    lon = point.get('longitude_deg')
                    alt = point.get('altitude_m')

                    # 檢查合理範圍
                    if (lat is not None and -90 <= lat <= 90 and
                        lon is not None and -180 <= lon <= 180 and
                        alt is not None and 200000 <= alt <= 2000000):  # LEO 範圍 200-2000km
                        valid_coords += 1

                    # 收集精度估計
                    accuracy_m = point.get('accuracy_estimate_m')
                    if accuracy_m is not None:
                        accuracy_estimates.append(accuracy_m)

            if total_coords == 0:
                return {'passed': False, 'message': '沒有座標點數據'}

            accuracy_rate = valid_coords / total_coords
            avg_accuracy = (
                sum(accuracy_estimates) / len(accuracy_estimates)
                if accuracy_estimates else 999
            )

            # ✅ 基於真實 IERS 數據質量的合理閾值
            # 專業級標準：< 50m (Grade A), < 100m (Grade B)
            passed = accuracy_rate >= 0.95 and avg_accuracy <= 50.0

            return {
                'passed': passed,
                'accuracy_rate': accuracy_rate,
                'valid_coordinates': valid_coords,
                'total_coordinates': total_coords,
                'average_accuracy_m': avg_accuracy,
                'message': (
                    f'座標轉換: {accuracy_rate:.2%} 準確率, '
                    f'{avg_accuracy:.3f}m 平均精度'
                )
            }

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _check_real_data_sources(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查真實數據源使用"""
        try:
            metadata = results.get('metadata', {})
            real_data_sources = metadata.get('real_data_sources', {})

            skyfield_status = real_data_sources.get('skyfield_engine', {})
            iers_status = real_data_sources.get('iers_data_quality', {})
            wgs84_status = real_data_sources.get('wgs84_parameters', {})

            skyfield_ok = skyfield_status.get('skyfield_available', False)
            iers_ok = iers_status.get('cache_size', 0) > 0
            wgs84_ok = 'Emergency_Hardcoded' not in wgs84_status.get('source', '')

            # 檢查實際使用統計
            stats = metadata
            iers_used = stats.get('real_iers_data_used', 0)
            wgs84_used = stats.get('official_wgs84_used', 0)
            total_processed = stats.get('total_coordinate_points', 0)

            usage_rate = (
                (iers_used + wgs84_used) / (2 * total_processed)
                if total_processed > 0 else 0
            )

            passed = skyfield_ok and iers_ok and wgs84_ok and usage_rate > 0.9

            return {
                'passed': passed,
                'skyfield_available': skyfield_ok,
                'iers_data_available': iers_ok,
                'official_wgs84_used': wgs84_ok,
                'real_data_usage_rate': usage_rate,
                'message': (
                    f'真實數據源: Skyfield({skyfield_ok}), IERS({iers_ok}), '
                    f'WGS84({wgs84_ok}), 使用率{usage_rate:.1%}'
                )
            }

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _check_iau_standard_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查 IAU 標準合規"""
        try:
            metadata = results.get('metadata', {})

            # 檢查 IAU 合規標記
            iau_compliance = metadata.get('iau_standard_compliance', False)
            academic_standard = metadata.get('academic_standard')

            transformation_config = metadata.get('transformation_config', {})
            nutation_model = transformation_config.get('nutation_model')
            polar_motion = transformation_config.get('polar_motion', False)
            time_corrections = transformation_config.get('time_corrections', False)

            passed = (
                iau_compliance and
                academic_standard == 'Grade_A_Real_Algorithms' and
                nutation_model == 'IAU2000A' and
                polar_motion and time_corrections
            )

            return {
                'passed': passed,
                'iau_compliance': iau_compliance,
                'academic_standard': academic_standard,
                'nutation_model': nutation_model,
                'polar_motion': polar_motion,
                'time_corrections': time_corrections,
                'message': (
                    'IAU 標準完全合規 + 真實算法' if passed
                    else 'IAU 標準合規檢查失敗'
                )
            }

        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _check_skyfield_professional_usage(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """檢查 Skyfield 專業庫使用"""
        try:
            metadata = results.get('metadata', {})
            real_data_sources = metadata.get('real_data_sources', {})
            skyfield_engine = real_data_sources.get('skyfield_engine', {})

            # 檢查 Skyfield 配置
            skyfield_available = skyfield_engine.get('skyfield_available', False)
            ephemeris_loaded = skyfield_engine.get('ephemeris_loaded', False)

            # 使用抽樣檢查以提升效能（檢查前50顆衛星）
            geographic_coords = results.get('geographic_coordinates', {})
            total_satellites = len(geographic_coords)

            # 抽樣檢查
            sample_size = min(50, total_satellites)
            sample_sat_ids = list(geographic_coords.keys())[:sample_size]

            total_conversion_time = 0.0
            valid_conversions = 0
            sample_points = 0

            for sat_id in sample_sat_ids:
                sat_data = geographic_coords[sat_id]
                time_series = sat_data.get('time_series', [])
                sample_points += len(time_series)

                for point in time_series:
                    # 檢查是否有有效座標
                    if (point.get('latitude_deg') is not None and
                        point.get('longitude_deg') is not None and
                        point.get('altitude_m') is not None):
                        valid_conversions += 1
                        total_conversion_time += point.get('conversion_time_ms', 0)

            # 從抽樣推算總數
            avg_points_per_sat = sample_points / sample_size if sample_size > 0 else 0
            total_points = int(avg_points_per_sat * total_satellites)

            success_rate = (
                (valid_conversions / sample_points * 100)
                if sample_points > 0 else 0
            )
            avg_conversion_time = (
                (total_conversion_time / valid_conversions)
                if valid_conversions > 0 else 0
            )

            # 檢查實際使用證據
            coordinates_generated = sample_points > 0

            # 放寬標準：只要有成功轉換即可（支援取樣模式）
            passed = (
                skyfield_available and ephemeris_loaded and
                success_rate > 95 and coordinates_generated
            )

            return {
                'passed': passed,
                'skyfield_available': skyfield_available,
                'ephemeris_loaded': ephemeris_loaded,
                'success_rate': success_rate,
                'average_conversion_time_ms': avg_conversion_time,
                'coordinates_generated': coordinates_generated,
                'total_coordinate_points': total_points,
                'message': (
                    f'Skyfield 專業使用: {success_rate:.2f}% 成功率, '
                    f'{avg_conversion_time:.2f}ms 平均時間, '
                    f'~{total_points:,} 座標點 (抽樣{sample_size}顆)'
                    if passed else
                    f'Skyfield 專業庫使用檢查失敗 (成功率: {success_rate:.2f}%)'
                )
            }

        except Exception as e:
            return {'passed': False, 'error': str(e)}


def create_compliance_validator(
    config: Optional[Dict[str, Any]] = None
) -> Stage3ComplianceValidator:
    """創建學術合規檢查器實例"""
    return Stage3ComplianceValidator(config)
