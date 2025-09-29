"""
Stage 6 Scientific Validation Engine - 階段六科學驗證引擎

此模組實現階段六的零容忍科學驗證框架：
- 動態池算法正確性驗證
- 真實物理定律一致性檢查
- 學術級數據質量驗證
- 已知場景基準測試
- 算法收斂性和穩定性檢查

遵循學術級數據使用標準，基於真實物理定律和官方標準參數，確保計算精度和科學可靠性。
"""

import json
import logging
import math
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """科學驗證結果"""
    test_name: str
    status: str  # PASS, FAIL, WARNING
    actual_value: float
    expected_value: float
    tolerance: float
    scientific_basis: str
    compliance_level: str  # Grade_A, Grade_B, Grade_C

@dataclass
class BenchmarkScenario:
    """基準測試場景"""
    scenario_name: str
    input_data: Dict[str, Any]
    expected_results: Dict[str, Any]
    validation_criteria: Dict[str, Any]
    scientific_reference: str

class ScientificValidationEngine:
    """階段六科學驗證引擎 - 零容忍學術標準"""

    # 物理常數 (官方ITU-R和3GPP標準)
    EARTH_RADIUS_KM = 6371.0
    EARTH_GM = 3.986004418e14  # m³/s² (WGS84)
    # 🚨 Grade A要求：使用學術級物理常數
    from shared.constants.physics_constants import PhysicsConstants
    _physics_consts = PhysicsConstants()
    LIGHT_SPEED_MS = _physics_consts.SPEED_OF_LIGHT  # m/s (CODATA 2018標準)

    # LEO衛星星座標準參數 (基於官方技術文件)
    STARLINK_ORBITAL_HEIGHT_KM = 550.0  # ±10km
    ONEWEB_ORBITAL_HEIGHT_KM = 1200.0   # ±50km
    STARLINK_INCLINATION_DEG = 53.0     # ±2°
    ONEWEB_INCLINATION_DEG = 87.4       # ±1°

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.validation_stats = {
            "tests_executed": 0,
            "tests_passed": 0,
            "critical_failures": 0,
            "scientific_grade": "Unknown"
        }

        # 載入基準測試場景
        self.benchmark_scenarios = self._load_benchmark_scenarios()

        logger.info("Scientific Validation Engine initialized with zero-tolerance standards")

    def execute_comprehensive_scientific_validation(self,
                                                  dynamic_pool: List[Dict[str, Any]],
                                                  physics_results: Dict[str, Any],
                                                  selection_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行全面科學驗證"""

        logger.info("🔬 開始零容忍科學驗證")

        validation_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_framework": "zero_tolerance_scientific_v1.0",
            "tests": []
        }

        try:
            # 1. 動態池算法正確性驗證
            pool_validation = self._validate_dynamic_pool_algorithm(dynamic_pool, selection_results)
            validation_results["tests"].extend(pool_validation)

            # 2. 物理定律一致性檢查
            physics_validation = self._validate_physics_consistency(physics_results)
            validation_results["tests"].extend(physics_validation)

            # 3. 軌道力學真實性驗證
            orbital_validation = self._validate_orbital_mechanics_reality(dynamic_pool)
            validation_results["tests"].extend(orbital_validation)

            # 4. 信號傳播計算驗證
            signal_validation = self._validate_signal_propagation_accuracy(physics_results)
            validation_results["tests"].extend(signal_validation)

            # 5. 基準場景測試
            benchmark_validation = self._execute_benchmark_scenarios(dynamic_pool, physics_results)
            validation_results["tests"].extend(benchmark_validation)

            # 6. 算法收斂性和穩定性測試
            stability_validation = self._validate_algorithm_stability(selection_results)
            validation_results["tests"].extend(stability_validation)

            # 7. 數據來源真實性檢查
            authenticity_validation = self._validate_data_authenticity_real(dynamic_pool)
            validation_results["tests"].extend(authenticity_validation)

            # 計算整體科學等級
            overall_assessment = self._assess_overall_scientific_quality(validation_results["tests"])
            validation_results.update(overall_assessment)

            self._update_validation_stats(validation_results)

            logger.info(f"✅ 科學驗證完成 - 等級: {overall_assessment['scientific_grade']}")

            return validation_results

        except Exception as e:
            logger.error(f"❌ 科學驗證執行失敗: {e}")
            return {
                "error": True,
                "error_message": str(e),
                "scientific_grade": "F",
                "validation_status": "CRITICAL_FAILURE"
            }

    def _validate_dynamic_pool_algorithm(self, dynamic_pool: List[Dict[str, Any]],
                                       selection_results: Dict[str, Any]) -> List[ValidationResult]:
        """驗證動態池算法正確性"""

        results = []

        # 檢查1: 衛星選擇合理性
        total_satellites = len(dynamic_pool)
        selected_pool = selection_results.get("final_dynamic_pool", [])

        if isinstance(selected_pool, dict):
            selected_count = sum(len(sats) for sats in selected_pool.values())
        else:
            selected_count = len(selected_pool)

        selection_ratio = selected_count / total_satellites if total_satellites > 0 else 0

        # 基於LEO衛星換手研究，最優選擇率應在15-35%範圍內
        if 0.15 <= selection_ratio <= 0.35:
            results.append(ValidationResult(
                test_name="dynamic_pool_selection_ratio",
                status="PASS",
                actual_value=selection_ratio,
                expected_value=0.25,  # 25%最優比例
                tolerance=0.10,
                scientific_basis="LEO衛星換手研究最佳實踐 (15-35%選擇率)",
                compliance_level="Grade_A"
            ))
        else:
            results.append(ValidationResult(
                test_name="dynamic_pool_selection_ratio",
                status="FAIL",
                actual_value=selection_ratio,
                expected_value=0.25,
                tolerance=0.10,
                scientific_basis="LEO衛星換手研究最佳實踐違反",
                compliance_level="Grade_C"
            ))

        # 檢查2: 星座間平衡性
        if isinstance(selected_pool, dict):
            starlink_count = len(selected_pool.get("starlink", []))
            oneweb_count = len(selected_pool.get("oneweb", []))

            if starlink_count > 0 and oneweb_count > 0:
                balance_ratio = min(starlink_count, oneweb_count) / max(starlink_count, oneweb_count)

                # 平衡比例應大於0.3以確保多星座覆蓋優勢
                if balance_ratio >= 0.3:
                    results.append(ValidationResult(
                        test_name="constellation_balance",
                        status="PASS",
                        actual_value=balance_ratio,
                        expected_value=0.5,
                        tolerance=0.2,
                        scientific_basis="多星座協作覆蓋理論要求平衡分佈",
                        compliance_level="Grade_A"
                    ))
                else:
                    results.append(ValidationResult(
                        test_name="constellation_balance",
                        status="WARNING",
                        actual_value=balance_ratio,
                        expected_value=0.5,
                        tolerance=0.2,
                        scientific_basis="星座間平衡性不足，可能影響覆蓋多樣性",
                        compliance_level="Grade_B"
                    ))

        return results

    def _validate_physics_consistency(self, physics_results: Dict[str, Any]) -> List[ValidationResult]:
        """驗證物理定律一致性"""

        results = []

        # 檢查軌道動力學
        orbital_data = physics_results.get("orbital_dynamics", {})
        individual_orbits = orbital_data.get("individual_orbits", {})

        for sat_id, orbit_params in individual_orbits.items():
            # 開普勒第三定律驗證: T² ∝ a³
            semi_major_axis_km = orbit_params.get("semi_major_axis_km", 0)
            period_minutes = orbit_params.get("orbital_period_minutes", 0)

            if semi_major_axis_km > 0 and period_minutes > 0:
                # 計算理論軌道週期
                semi_major_axis_m = semi_major_axis_km * 1000
                theoretical_period_s = 2 * math.pi * math.sqrt(
                    (semi_major_axis_m ** 3) / self.EARTH_GM
                )
                theoretical_period_min = theoretical_period_s / 60

                period_error = abs(period_minutes - theoretical_period_min) / theoretical_period_min

                # 容忍誤差3% (考慮地球扁率等因素)
                if period_error <= 0.03:
                    results.append(ValidationResult(
                        test_name=f"keplers_third_law_{sat_id}",
                        status="PASS",
                        actual_value=period_minutes,
                        expected_value=theoretical_period_min,
                        tolerance=theoretical_period_min * 0.03,
                        scientific_basis="開普勒第三定律: T² = (4π²/GM) × a³",
                        compliance_level="Grade_A"
                    ))
                else:
                    results.append(ValidationResult(
                        test_name=f"keplers_third_law_{sat_id}",
                        status="FAIL",
                        actual_value=period_minutes,
                        expected_value=theoretical_period_min,
                        tolerance=theoretical_period_min * 0.03,
                        scientific_basis="違反開普勒第三定律 - 軌道計算錯誤",
                        compliance_level="Grade_F"
                    ))

        return results

    def _validate_orbital_mechanics_reality(self, dynamic_pool: List[Dict[str, Any]]) -> List[ValidationResult]:
        """驗證軌道力學真實性"""

        results = []

        # 按星座分組檢查
        starlink_sats = [sat for sat in dynamic_pool if sat.get("constellation") == "starlink"]
        oneweb_sats = [sat for sat in dynamic_pool if sat.get("constellation") == "oneweb"]

        # Starlink軌道高度檢查
        if starlink_sats:
            starlink_altitudes = []
            for sat in starlink_sats:
                altitude = sat.get("altitude_km", 0)
                if altitude > 0:
                    starlink_altitudes.append(altitude)

            if starlink_altitudes:
                avg_altitude = np.mean(starlink_altitudes)
                altitude_std = np.std(starlink_altitudes)

                # Starlink標準軌道高度550km ±10km
                if abs(avg_altitude - self.STARLINK_ORBITAL_HEIGHT_KM) <= 10:
                    results.append(ValidationResult(
                        test_name="starlink_orbital_altitude",
                        status="PASS",
                        actual_value=avg_altitude,
                        expected_value=self.STARLINK_ORBITAL_HEIGHT_KM,
                        tolerance=10.0,
                        scientific_basis="Starlink官方軌道高度規格550km",
                        compliance_level="Grade_A"
                    ))
                else:
                    results.append(ValidationResult(
                        test_name="starlink_orbital_altitude",
                        status="FAIL",
                        actual_value=avg_altitude,
                        expected_value=self.STARLINK_ORBITAL_HEIGHT_KM,
                        tolerance=10.0,
                        scientific_basis="違反Starlink官方軌道高度規格",
                        compliance_level="Grade_F"
                    ))

        # OneWeb軌道高度檢查
        if oneweb_sats:
            oneweb_altitudes = []
            for sat in oneweb_sats:
                altitude = sat.get("altitude_km", 0)
                if altitude > 0:
                    oneweb_altitudes.append(altitude)

            if oneweb_altitudes:
                avg_altitude = np.mean(oneweb_altitudes)

                # OneWeb標準軌道高度1200km ±50km
                if abs(avg_altitude - self.ONEWEB_ORBITAL_HEIGHT_KM) <= 50:
                    results.append(ValidationResult(
                        test_name="oneweb_orbital_altitude",
                        status="PASS",
                        actual_value=avg_altitude,
                        expected_value=self.ONEWEB_ORBITAL_HEIGHT_KM,
                        tolerance=50.0,
                        scientific_basis="OneWeb官方軌道高度規格1200km",
                        compliance_level="Grade_A"
                    ))
                else:
                    results.append(ValidationResult(
                        test_name="oneweb_orbital_altitude",
                        status="FAIL",
                        actual_value=avg_altitude,
                        expected_value=self.ONEWEB_ORBITAL_HEIGHT_KM,
                        tolerance=50.0,
                        scientific_basis="違反OneWeb官方軌道高度規格",
                        compliance_level="Grade_F"
                    ))

        return results

    def _validate_signal_propagation_accuracy(self, physics_results: Dict[str, Any]) -> List[ValidationResult]:
        """驗證信號傳播計算準確性"""

        results = []

        signal_data = physics_results.get("signal_propagation", {})

        # 檢查自由空間路徑損耗計算
        individual_signals = signal_data.get("individual_signals", {})

        for sat_id, signal_params in individual_signals.items():
            distance_km = signal_params.get("distance_km", 0)
            frequency_ghz = signal_params.get("frequency_ghz", 0)
            path_loss_db = signal_params.get("free_space_path_loss_db", 0)

            if distance_km > 0 and frequency_ghz > 0:
                # Friis公式: FSPL = 20log₁₀(d) + 20log₁₀(f) + 92.45
                distance_km_corrected = max(distance_km, 1.0)  # 避免log(0)
                theoretical_fspl = (20 * math.log10(distance_km_corrected) +
                                  20 * math.log10(frequency_ghz) + 92.45)

                fspl_error = abs(path_loss_db - theoretical_fspl) / theoretical_fspl

                # 容忍誤差2% (Friis公式為精確公式)
                if fspl_error <= 0.02:
                    results.append(ValidationResult(
                        test_name=f"friis_formula_accuracy_{sat_id}",
                        status="PASS",
                        actual_value=path_loss_db,
                        expected_value=theoretical_fspl,
                        tolerance=theoretical_fspl * 0.02,
                        scientific_basis="Friis自由空間路徑損耗公式",
                        compliance_level="Grade_A"
                    ))
                else:
                    results.append(ValidationResult(
                        test_name=f"friis_formula_accuracy_{sat_id}",
                        status="FAIL",
                        actual_value=path_loss_db,
                        expected_value=theoretical_fspl,
                        tolerance=theoretical_fspl * 0.02,
                        scientific_basis="Friis公式計算錯誤 - 信號傳播模型問題",
                        compliance_level="Grade_F"
                    ))

        return results

    def _execute_benchmark_scenarios(self, dynamic_pool: List[Dict[str, Any]],
                                   physics_results: Dict[str, Any]) -> List[ValidationResult]:
        """執行基準場景測試"""

        results = []

        for scenario in self.benchmark_scenarios:
            try:
                # 執行場景測試邏輯
                scenario_result = self._run_benchmark_scenario(scenario, dynamic_pool, physics_results)
                results.append(scenario_result)

            except Exception as e:
                results.append(ValidationResult(
                    test_name=f"benchmark_{scenario.scenario_name}",
                    status="FAIL",
                    actual_value=0.0,
                    expected_value=1.0,
                    tolerance=0.0,
                    scientific_basis=f"基準測試執行失敗: {e}",
                    compliance_level="Grade_F"
                ))

        return results

    def _validate_algorithm_stability(self, selection_results: Dict[str, Any]) -> List[ValidationResult]:
        """驗證算法收斂性和穩定性"""

        results = []

        # 檢查優化收斂性
        optimization_stats = selection_results.get("optimization_statistics", {})
        convergence_iterations = optimization_stats.get("iterations_to_convergence", 0)

        # 算法應在合理迭代次數內收斂 (通常<100次)
        if 0 < convergence_iterations <= 100:
            results.append(ValidationResult(
                test_name="algorithm_convergence",
                status="PASS",
                actual_value=convergence_iterations,
                expected_value=50.0,  # 期望50次內收斂
                tolerance=50.0,
                scientific_basis="優化算法收斂性理論",
                compliance_level="Grade_A"
            ))
        else:
            results.append(ValidationResult(
                test_name="algorithm_convergence",
                status="FAIL",
                actual_value=convergence_iterations,
                expected_value=50.0,
                tolerance=50.0,
                scientific_basis="算法收斂性問題 - 可能存在數值不穩定",
                compliance_level="Grade_D"
            ))

        return results

    def _validate_data_authenticity_real(self, dynamic_pool: List[Dict[str, Any]]) -> List[ValidationResult]:
        """真實數據來源驗證 (非虛假硬編碼)"""

        results = []

        # 檢查TLE數據時間戳真實性
        tle_timestamps = []
        mock_data_count = 0
        total_satellites = len(dynamic_pool)

        for sat in dynamic_pool:
            tle_data = sat.get("tle_data", {})
            epoch_timestamp = tle_data.get("epoch_timestamp")

            if epoch_timestamp:
                # 檢查是否為真實TLE時間戳格式
                try:
                    epoch_dt = datetime.fromisoformat(epoch_timestamp.replace('Z', '+00:00'))
                    tle_timestamps.append(epoch_dt)

                    # 檢查是否為明顯虛假數據 (例如固定時間或明顯模式)
                    if epoch_timestamp in ["2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z"]:
                        mock_data_count += 1

                except (ValueError, AttributeError):
                    mock_data_count += 1
            else:
                mock_data_count += 1

        authentic_data_ratio = (total_satellites - mock_data_count) / total_satellites if total_satellites > 0 else 0

        # 要求95%以上為真實數據
        if authentic_data_ratio >= 0.95:
            results.append(ValidationResult(
                test_name="data_authenticity_verification",
                status="PASS",
                actual_value=authentic_data_ratio,
                expected_value=1.0,
                tolerance=0.05,
                scientific_basis="學術級研究要求真實數據來源",
                compliance_level="Grade_A"
            ))
        else:
            results.append(ValidationResult(
                test_name="data_authenticity_verification",
                status="FAIL",
                actual_value=authentic_data_ratio,
                expected_value=1.0,
                tolerance=0.05,
                scientific_basis="檢測到模擬或虛假數據 - 違反學術標準",
                compliance_level="Grade_F"
            ))

        return results

    def _assess_overall_scientific_quality(self, validation_tests: List[ValidationResult]) -> Dict[str, Any]:
        """評估整體科學質量等級"""

        if not validation_tests:
            return {
                "scientific_grade": "F",
                "validation_status": "NO_TESTS_EXECUTED",
                "quality_score": 0.0
            }

        total_tests = len(validation_tests)
        passed_tests = sum(1 for test in validation_tests if test.status == "PASS")
        failed_tests = sum(1 for test in validation_tests if test.status == "FAIL")

        # 計算加權分數 (失敗測試嚴重扣分)
        pass_rate = passed_tests / total_tests
        fail_penalty = (failed_tests / total_tests) * 0.5  # 失敗測試額外扣分
        quality_score = max(0.0, pass_rate - fail_penalty)

        # 科學等級判定 (更嚴格標準)
        if quality_score >= 0.95 and failed_tests == 0:
            scientific_grade = "A"
            status = "EXCELLENT"
        elif quality_score >= 0.85 and failed_tests <= 1:
            scientific_grade = "B"
            status = "GOOD"
        elif quality_score >= 0.70:
            scientific_grade = "C"
            status = "ACCEPTABLE"
        elif quality_score >= 0.50:
            scientific_grade = "D"
            status = "POOR"
        else:
            scientific_grade = "F"
            status = "UNACCEPTABLE"

        return {
            "scientific_grade": scientific_grade,
            "validation_status": status,
            "quality_score": quality_score,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "critical_issues": failed_tests
        }

    def _load_benchmark_scenarios(self) -> List[BenchmarkScenario]:
        """載入基準測試場景"""

        scenarios = []

        # 場景1: 台北上空單衛星覆蓋測試
        scenarios.append(BenchmarkScenario(
            scenario_name="taipei_single_satellite_coverage",
            input_data={
                "observer_lat": 25.0330,
                "observer_lon": 121.5654,
                "test_satellites": ["starlink_test_sat"],
                "test_duration_hours": 1.0
            },
            expected_results={
                "min_elevation_deg": 10.0,
                "max_elevation_deg": 90.0,
                "visibility_windows": {"min_count": 1}
            },
            validation_criteria={
                "elevation_accuracy_deg": 1.0,
                "timing_accuracy_sec": 30.0
            },
            scientific_reference="ITU-R P.618標準衛星覆蓋計算"
        ))

        return scenarios

    def _run_benchmark_scenario(self, scenario: BenchmarkScenario,
                              dynamic_pool: List[Dict[str, Any]],
                              physics_results: Dict[str, Any]) -> ValidationResult:
        """執行單個基準測試場景 - 完整實現版本"""

        scenario_name = scenario.scenario_name

        try:
            if scenario_name == "taipei_single_satellite_coverage":
                return self._validate_taipei_coverage_scenario(scenario, dynamic_pool, physics_results)
            else:
                # 對於其他場景，實現通用驗證邏輯
                return self._validate_generic_scenario(scenario, dynamic_pool, physics_results)

        except Exception as e:
            logger.error(f"基準場景執行失敗 {scenario_name}: {e}")
            return ValidationResult(
                test_name=f"benchmark_{scenario_name}",
                status="FAIL",
                actual_value=0.0,
                expected_value=1.0,
                tolerance=0.0,
                scientific_basis=f"場景執行異常: {str(e)}",
                compliance_level="Grade_F"
            )

    def _validate_taipei_coverage_scenario(self, scenario: BenchmarkScenario,
                                         dynamic_pool: List[Dict[str, Any]],
                                         physics_results: Dict[str, Any]) -> ValidationResult:
        """驗證台北覆蓋場景 - 完整實現"""

        observer_lat = scenario.input_data.get("observer_lat", 25.0330)
        observer_lon = scenario.input_data.get("observer_lon", 121.5654)
        min_elevation = scenario.expected_results.get("min_elevation_deg", 10.0)

        # 計算實際的衛星可見性
        visibility_results = self._calculate_satellite_visibility(
            observer_lat, observer_lon, dynamic_pool, min_elevation
        )

        visible_satellites = visibility_results["visible_count"]
        max_elevation_achieved = visibility_results["max_elevation"]
        visibility_windows = visibility_results["visibility_windows"]

        # 檢查是否滿足最小要求
        min_windows_required = scenario.expected_results.get("visibility_windows", {}).get("min_count", 1)

        if (visible_satellites > 0 and
            max_elevation_achieved >= min_elevation and
            len(visibility_windows) >= min_windows_required):

            return ValidationResult(
                test_name=f"benchmark_{scenario.scenario_name}",
                status="PASS",
                actual_value=max_elevation_achieved,
                expected_value=min_elevation,
                tolerance=5.0,  # 5度容忍度
                scientific_basis=f"{scenario.scientific_reference} - 台北地區覆蓋驗證通過",
                compliance_level="Grade_A"
            )
        else:
            return ValidationResult(
                test_name=f"benchmark_{scenario.scenario_name}",
                status="FAIL",
                actual_value=max_elevation_achieved,
                expected_value=min_elevation,
                tolerance=5.0,
                scientific_basis=f"台北覆蓋要求未滿足: 可見衛星{visible_satellites}, 最大仰角{max_elevation_achieved:.2f}度",
                compliance_level="Grade_F"
            )

    def _validate_generic_scenario(self, scenario: BenchmarkScenario,
                                 dynamic_pool: List[Dict[str, Any]],
                                 physics_results: Dict[str, Any]) -> ValidationResult:
        """通用場景驗證"""

        # 檢查物理計算結果的完整性和準確性
        coverage_data = physics_results.get("coverage_geometry", {})
        orbital_data = physics_results.get("orbital_dynamics", {})
        signal_data = physics_results.get("signal_propagation", {})

        # 計算場景完成度分數
        completeness_score = 0.0

        if coverage_data and len(coverage_data) > 0:
            completeness_score += 0.4

        if orbital_data and len(orbital_data) > 0:
            completeness_score += 0.3

        if signal_data and len(signal_data) > 0:
            completeness_score += 0.3

        # 驗證數據一致性
        consistency_passed = self._check_data_consistency(
            dynamic_pool, coverage_data, orbital_data, signal_data
        )

        if consistency_passed:
            completeness_score += 0.1

        if completeness_score >= 0.8:
            return ValidationResult(
                test_name=f"benchmark_{scenario.scenario_name}",
                status="PASS",
                actual_value=completeness_score,
                expected_value=0.8,
                tolerance=0.1,
                scientific_basis=scenario.scientific_reference,
                compliance_level="Grade_A"
            )
        else:
            return ValidationResult(
                test_name=f"benchmark_{scenario.scenario_name}",
                status="FAIL",
                actual_value=completeness_score,
                expected_value=0.8,
                tolerance=0.1,
                scientific_basis=f"場景完成度不足: {completeness_score:.2f}",
                compliance_level="Grade_C"
            )

    def _update_validation_stats(self, validation_results: Dict[str, Any]) -> None:
        """更新驗證統計"""

        tests = validation_results.get("tests", [])
        self.validation_stats["tests_executed"] = len(tests)
        self.validation_stats["tests_passed"] = sum(1 for test in tests if test.status == "PASS")
        self.validation_stats["critical_failures"] = sum(1 for test in tests if test.status == "FAIL")
        self.validation_stats["scientific_grade"] = validation_results.get("scientific_grade", "Unknown")

        logger.info(f"驗證統計更新: {self.validation_stats}")

    def _calculate_satellite_visibility(self, observer_lat: float, observer_lon: float,
                                       dynamic_pool: List[Dict[str, Any]],
                                       min_elevation: float) -> Dict[str, Any]:
        """計算衛星可見性 - 完整實現版本"""

        import math

        visibility_results = {
            "visible_count": 0,
            "max_elevation": 0.0,
            "visibility_windows": [],
            "calculation_details": []
        }

        # 地球半徑 (WGS84)
        earth_radius_km = 6378.137

        for sat in dynamic_pool:
            try:
                # 提取衛星軌道參數
                altitude_km = sat.get("altitude_km", 0)
                lat_deg = sat.get("latitude_deg", 0)
                lon_deg = sat.get("longitude_deg", 0)

                if altitude_km <= 0:
                    continue

                # 計算衛星到觀測者的距離和仰角
                # 使用球面三角學計算
                observer_lat_rad = math.radians(observer_lat)
                observer_lon_rad = math.radians(observer_lon)
                sat_lat_rad = math.radians(lat_deg)
                sat_lon_rad = math.radians(lon_deg)

                # 計算角距離
                angular_distance = math.acos(
                    math.sin(observer_lat_rad) * math.sin(sat_lat_rad) +
                    math.cos(observer_lat_rad) * math.cos(sat_lat_rad) *
                    math.cos(abs(observer_lon_rad - sat_lon_rad))
                )

                # 計算地表距離
                ground_distance_km = earth_radius_km * angular_distance

                # 計算仰角 (使用幾何關係)
                sat_height_km = earth_radius_km + altitude_km

                if ground_distance_km < sat_height_km:
                    # 使用餘弦定理計算仰角
                    observer_to_sat_distance = math.sqrt(
                        ground_distance_km**2 + altitude_km**2
                    )

                    # 仰角計算
                    elevation_rad = math.asin(altitude_km / observer_to_sat_distance)
                    elevation_deg = math.degrees(elevation_rad)

                    if elevation_deg >= min_elevation:
                        visibility_results["visible_count"] += 1
                        visibility_results["max_elevation"] = max(
                            visibility_results["max_elevation"], elevation_deg
                        )

                        # 記錄可見性窗口
                        visibility_results["visibility_windows"].append({
                            "satellite_id": sat.get("id", "unknown"),
                            "elevation_deg": elevation_deg,
                            "azimuth_deg": self._calculate_azimuth(
                                observer_lat_rad, observer_lon_rad,
                                sat_lat_rad, sat_lon_rad
                            ),
                            "distance_km": observer_to_sat_distance
                        })

                    visibility_results["calculation_details"].append({
                        "satellite_id": sat.get("id", "unknown"),
                        "altitude_km": altitude_km,
                        "elevation_deg": elevation_deg,
                        "ground_distance_km": ground_distance_km,
                        "is_visible": elevation_deg >= min_elevation
                    })

            except Exception as e:
                logger.warning(f"衛星可見性計算失敗 {sat.get('id', 'unknown')}: {e}")
                continue

        return visibility_results

    def _calculate_azimuth(self, observer_lat_rad: float, observer_lon_rad: float,
                          sat_lat_rad: float, sat_lon_rad: float) -> float:
        """計算方位角"""
        import math

        try:
            delta_lon = sat_lon_rad - observer_lon_rad

            y = math.sin(delta_lon) * math.cos(sat_lat_rad)
            x = (math.cos(observer_lat_rad) * math.sin(sat_lat_rad) -
                 math.sin(observer_lat_rad) * math.cos(sat_lat_rad) * math.cos(delta_lon))

            azimuth_rad = math.atan2(y, x)
            azimuth_deg = (math.degrees(azimuth_rad) + 360) % 360

            return azimuth_deg
        except Exception:
            return 0.0

    def _check_data_consistency(self, dynamic_pool: List[Dict[str, Any]],
                              coverage_data: Dict[str, Any],
                              orbital_data: Dict[str, Any],
                              signal_data: Dict[str, Any]) -> bool:
        """檢查數據一致性"""

        try:
            # 檢查衛星數量一致性
            pool_sat_count = len(dynamic_pool)

            coverage_sat_count = len(coverage_data.get("individual_coverage", {}))
            orbital_sat_count = len(orbital_data.get("individual_orbits", {}))
            signal_sat_count = len(signal_data.get("individual_signals", {}))

            # 允許10%的數據差異（考慮到過濾和處理過程）
            tolerance = 0.1
            max_count = max(pool_sat_count, coverage_sat_count, orbital_sat_count, signal_sat_count)
            min_count = min(pool_sat_count, coverage_sat_count, orbital_sat_count, signal_sat_count)

            if max_count > 0:
                consistency_ratio = min_count / max_count
                return consistency_ratio >= (1.0 - tolerance)

            return True  # 如果所有數據都為空，認為是一致的

        except Exception as e:
            logger.warning(f"數據一致性檢查失敗: {e}")
            return False

    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計信息"""
        return self.validation_stats.copy()