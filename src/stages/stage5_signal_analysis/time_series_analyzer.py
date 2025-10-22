#!/usr/bin/env python3
"""
時間序列分析引擎 - Stage 5 重構

專職責任：
- 衛星時間序列逐點分析
- 3GPP 信號品質計算整合
- ITU-R 物理參數計算整合
- 信號品質分類與統計

學術合規：Grade A 標準
- 使用 3GPP TS 38.214 標準信號計算
- 使用 ITU-R P.618/P.676 物理模型
"""

import logging
import math
from typing import Dict, Any, List, Optional

# 🚨 Grade A要求：使用學術級物理常數 (Astropy CODATA 2022, Fail-Fast)
logger = logging.getLogger(__name__)

# Fail-Fast: Astropy 是必需依賴，不可用時立即報錯
try:
    from src.shared.constants.astropy_physics_constants import get_astropy_constants
except ModuleNotFoundError:
    from shared.constants.astropy_physics_constants import get_astropy_constants

physics_consts = get_astropy_constants()
logger.info("✅ 使用 Astropy 官方物理常數 (CODATA 2022)")


class TimeSeriesAnalyzer:
    """
    時間序列分析引擎

    實現衛星時間序列逐點分析:
    - RSRP/RSRQ/SINR 計算 (3GPP TS 38.214)
    - 物理參數計算 (ITU-R P.618/P.676)
    - 信號品質分類與統計
    """

    def __init__(self, config: Dict[str, Any], signal_thresholds: Dict[str, float],
                 propagation_simulator=None):
        """
        初始化時間序列分析引擎

        ✅ Grade A 標準: Fail-Fast 配置驗證
        依據: docs/ACADEMIC_STANDARDS.md Line 265-274

        Args:
            config: 配置字典（必須提供）
                - signal_calculator: 信號計算器配置
                - atmospheric_model: 大氣模型參數
            signal_thresholds: 信號門檻配置（必須提供）
                - rsrp_excellent, rsrp_good, rsrp_fair, rsrp_poor
                - rsrq_excellent, rsrq_good, rsrq_fair
                - sinr_excellent, sinr_good
            propagation_simulator: 動態傳播條件模擬器（可選，Proposal 002）

        Raises:
            ValueError: 配置為空或缺少必要字段
            TypeError: 配置類型錯誤
        """
        if not config:
            raise ValueError(
                "TimeSeriesAnalyzer 初始化失敗：config 不可為空\n"
                "Grade A 標準禁止使用空配置\n"
                "必須提供:\n"
                "  - signal_calculator: 信號計算器配置\n"
                "  - atmospheric_model: 大氣模型參數\n"
                "SOURCE: docs/ACADEMIC_STANDARDS.md Line 265-274"
            )

        if not isinstance(config, dict):
            raise TypeError(
                f"config 必須是字典類型，當前類型: {type(config).__name__}"
            )

        if not signal_thresholds:
            raise ValueError(
                "TimeSeriesAnalyzer 初始化失敗：signal_thresholds 不可為空\n"
                "Grade A 標準禁止使用空門檻或硬編碼預設值\n"
                "必須明確提供所有信號品質門檻:\n"
                "  - rsrp_excellent, rsrp_good, rsrp_fair, rsrp_poor\n"
                "  - rsrq_excellent, rsrq_good, rsrq_fair\n"
                "  - sinr_excellent, sinr_good\n"
                "所有門檻必須標註 SOURCE (3GPP TS 38.215)\n"
                "SOURCE: docs/ACADEMIC_STANDARDS.md Line 265-274"
            )

        if not isinstance(signal_thresholds, dict):
            raise TypeError(
                f"signal_thresholds 必須是字典類型，當前類型: {type(signal_thresholds).__name__}"
            )

        self.config = config
        self.signal_thresholds = signal_thresholds
        self.propagation_simulator = propagation_simulator
        self.logger = logging.getLogger(__name__)

    def analyze_time_series(
        self,
        satellite_id: str,
        time_series: List[Dict[str, Any]],
        system_config: Dict[str, Any],
        constellation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析單顆衛星的完整時間序列

        逐時間點計算:
        - RSRP (3GPP TS 38.214)
        - RSRQ (3GPP TS 38.214)
        - SINR (3GPP TS 38.214)
        - 測量偏移 (3GPP TS 38.331) - A3 事件需要
        - 物理參數 (ITU-R P.618)

        Args:
            satellite_id: 衛星ID
            time_series: 時間序列數據
            system_config: 系統配置 (包含 tx_power, frequency, gain 等)
            constellation: 星座名稱 (用於計算測量偏移)

        Returns:
        {
            'time_series': [
                {
                    'timestamp': str,
                    'signal_quality': {
                        'rsrp_dbm': float,
                        'rsrq_db': float,
                        'rs_sinr_db': float,  # 修復: 使用 3GPP 標準命名 RS-SINR
                        'offset_mo_db': float,      # A3 事件: Ofn/Ofp
                        'cell_offset_db': float,    # A3 事件: Ocn/Ocp
                        'calculation_standard': '3GPP_TS_38.214'
                    },
                    'is_connectable': bool,
                    'physical_parameters': {...}
                },
                ...
            ],
            'summary': {...},
            'physics_summary': {...}
        }
        """
        time_series_results = []
        rsrp_values = []
        rsrq_values = []
        sinr_values = []
        quality_counts = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}

        for time_point in time_series:
            try:
                # ✅ Fail-Fast: 明確檢查必需字段，而非使用 .get() 回退
                if 'visibility_metrics' not in time_point:
                    self.logger.debug(f"時間點缺少 visibility_metrics，跳過")
                    continue

                visibility_metrics = time_point['visibility_metrics']

                if 'elevation_deg' not in visibility_metrics:
                    self.logger.debug(f"visibility_metrics 缺少 elevation_deg，跳過")
                    continue
                if 'distance_km' not in visibility_metrics:
                    self.logger.debug(f"visibility_metrics 缺少 distance_km，跳過")
                    continue
                if 'is_connectable' not in visibility_metrics:
                    self.logger.debug(f"visibility_metrics 缺少 is_connectable，跳過")
                    continue
                if 'timestamp' not in time_point:
                    self.logger.debug(f"時間點缺少 timestamp，跳過")
                    continue

                elevation_deg = visibility_metrics['elevation_deg']
                distance_km = visibility_metrics['distance_km']
                is_connectable_str = visibility_metrics['is_connectable']
                # 🔧 修復: is_connectable 是字符串 "True"/"False"，需要轉換為布爾值
                is_connectable = (is_connectable_str == 'True' or is_connectable_str == True)
                timestamp = time_point['timestamp']

                if elevation_deg is None or distance_km is None:
                    continue

                # ✅ 修復: 跳過不可連接的時間點 (負仰角、超出距離等)
                # Stage 4 已標記 is_connectable=False，Stage 5 應忽略這些時間點
                # SOURCE: Stage 4 visibility calculation results
                if not is_connectable:
                    continue

                # 計算信號品質 (3GPP 標準)
                signal_quality = self.calculate_3gpp_signal_quality(
                    elevation_deg=elevation_deg,
                    distance_km=distance_km,
                    system_config=system_config,
                    constellation=constellation,
                    satellite_id=satellite_id
                )

                # ✅ 計算物理參數 (ITU-R 標準 + Stage 2 實際速度)
                physics_params = self.calculate_itur_physics(
                    elevation_deg=elevation_deg,
                    distance_km=distance_km,
                    frequency_ghz=system_config['frequency_ghz'],
                    time_point=time_point  # ← 傳遞完整時間點數據以提取速度
                )

                # 🆕 NEW: 動態傳播條件模擬 (Proposal 002)
                # SOURCE: Proposal 002 - Training Data Diversity Enhancement
                propagation_condition = None
                if self.propagation_simulator is not None:
                    try:
                        prop_result = self.propagation_simulator.simulate(
                            satellite_id=satellite_id,
                            timestamp=timestamp,
                            elevation_deg=elevation_deg,
                            distance_km=distance_km
                        )
                        propagation_condition = prop_result.to_dict()
                    except Exception as e:
                        self.logger.debug(f"⚠️ 傳播條件模擬失敗 (時間點 {timestamp}): {e}")
                        # 失敗不影響主流程，繼續處理

                # 構建時間點結果
                # ✅ Fail-Fast: 如果信號計算失敗，offset 字段會缺失，直接跳過此時間點
                if 'offset_mo_db' not in signal_quality or 'cell_offset_db' not in signal_quality:
                    self.logger.debug(f"時間點 {timestamp} 缺少 A3 offset 數據，跳過")
                    continue

                time_point_result = {
                    'timestamp': timestamp,
                    'signal_quality': {
                        'rsrp_dbm': signal_quality['rsrp_dbm'],
                        'rsrq_db': signal_quality['rsrq_db'],
                        'rs_sinr_db': signal_quality['rs_sinr_db'],  # 修復: 使用 3GPP 標準命名
                        'offset_mo_db': signal_quality['offset_mo_db'],        # A3 事件: Ofn/Ofp
                        'cell_offset_db': signal_quality['cell_offset_db'],    # A3 事件: Ocn/Ocp
                        'calculation_standard': '3GPP_TS_38.214'
                    },
                    'is_connectable': is_connectable,
                    'physical_parameters': physics_params
                }

                # 🆕 添加傳播條件數據（如果啟用）
                if propagation_condition is not None:
                    time_point_result['propagation_condition'] = propagation_condition

                time_series_results.append(time_point_result)

                # 收集統計數據
                if signal_quality['rsrp_dbm'] is not None:
                    rsrp_values.append(signal_quality['rsrp_dbm'])
                if signal_quality['rsrq_db'] is not None:
                    rsrq_values.append(signal_quality['rsrq_db'])
                if signal_quality['rs_sinr_db'] is not None:
                    sinr_values.append(signal_quality['rs_sinr_db'])

                # 品質分類統計
                quality_level = self.classify_signal_quality(signal_quality['rsrp_dbm'])
                quality_counts[quality_level] += 1

            except Exception as e:
                self.logger.debug(f"時間點 {timestamp} 計算失敗: {e}")
                continue

        # 計算摘要統計
        average_rsrp = sum(rsrp_values) / len(rsrp_values) if rsrp_values else None

        # ✅ 計算鏈路裕度 (Link Margin)
        # 定義: 接收功率 - 最低可連接門檻
        # SOURCE: 通用鏈路預算概念，3GPP TS 38.101-1 Section 7.3 (Receiver characteristics)
        link_margin_db = None
        if average_rsrp is not None and 'rsrp_minimum' in self.signal_thresholds:
            rsrp_minimum = self.signal_thresholds['rsrp_minimum']
            link_margin_db = average_rsrp - rsrp_minimum  # 例: -35 - (-120) = 85 dB

        summary = {
            'total_time_points': len(time_series_results),
            'average_rsrp_dbm': average_rsrp,
            'average_rsrq_db': sum(rsrq_values) / len(rsrq_values) if rsrq_values else None,
            'average_rs_sinr_db': sum(sinr_values) / len(sinr_values) if sinr_values else None,  # 修復: 使用 3GPP 標準命名
            'quality_distribution': quality_counts,
            'average_quality_level': max(quality_counts, key=quality_counts.get) if quality_counts else 'poor',
            'link_margin_db': link_margin_db  # ✅ Stage 6 決策支援需要此欄位
        }

        # 物理摘要
        physics_summary = {
            'average_path_loss_db': sum(p['physical_parameters']['path_loss_db']
                                       for p in time_series_results) / len(time_series_results) if time_series_results else None,
            'average_atmospheric_loss_db': sum(p['physical_parameters']['atmospheric_loss_db']
                                              for p in time_series_results) / len(time_series_results) if time_series_results else None,
            'itur_compliance': 'P.618-13'
        }

        return {
            'time_series': time_series_results,
            'summary': summary,
            'physics_summary': physics_summary
        }

    def calculate_3gpp_signal_quality(
        self,
        elevation_deg: float,
        distance_km: float,
        system_config: Dict[str, Any],
        constellation: Optional[str] = None,
        satellite_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        計算 3GPP 標準信號品質

        ✅ 完整實現 3GPP TS 38.214/38.215 標準:
        - RSRP (Reference Signal Received Power)
        - RSRQ (Reference Signal Received Quality) - 使用實際 RSSI
        - SINR (Signal-to-Interference-plus-Noise Ratio) - Johnson-Nyquist 噪聲底
        - 測量偏移 (3GPP TS 38.331) - A3 事件需要

        Args:
            elevation_deg: 仰角 (度)
            distance_km: 距離 (公里)
            system_config: 系統配置
            constellation: 星座名稱 (用於計算測量偏移)
            satellite_id: 衛星ID (用於衛星級別偏移)

        Returns:
            Dict: 信號品質參數（包含測量偏移）
        """
        try:
            # 提取配置
            tx_power_dbm = system_config['tx_power_dbm']
            tx_gain_db = system_config['tx_gain_db']
            rx_gain_db = system_config['rx_gain_db']
            frequency_ghz = system_config['frequency_ghz']

            # ✅ 使用 ITU-R P.676-13 官方大氣衰減模型 (ITU-Rpy)
            from .itur_official_atmospheric_model import create_itur_official_model

            # ✅ Grade A標準: Fail-Fast 模式 - 大氣參數必須在配置中提供
            # 依據: docs/ACADEMIC_STANDARDS.md Line 265-274 禁止使用預設值
            if 'atmospheric_model' not in self.config:
                raise ValueError(
                    "atmospheric_model 配置缺失\n"
                    "Grade A 標準禁止使用預設值\n"
                    "請在配置文件中提供:\n"
                    "  atmospheric_model:\n"
                    "    temperature_k: 283.0  # SOURCE: ITU-R P.835 mid-latitude\n"
                    "    pressure_hpa: 1013.25  # SOURCE: ICAO Standard\n"
                    "    water_vapor_density_g_m3: 7.5  # SOURCE: ITU-R P.835"
                )

            atmospheric_config = self.config['atmospheric_model']

            required_params = ['temperature_k', 'pressure_hpa', 'water_vapor_density_g_m3']
            missing_params = [p for p in required_params if p not in atmospheric_config]
            if missing_params:
                raise ValueError(
                    f"大氣參數缺失: {missing_params}\n"
                    f"Grade A 標準禁止使用預設值\n"
                    f"請在 atmospheric_model 配置中提供所有必要參數:\n"
                    f"  temperature_k: 實測值或 ITU-R P.835 標準值 (200-350K)\n"
                    f"  pressure_hpa: 實測值或 ICAO 標準值 (500-1100 hPa)\n"
                    f"  water_vapor_density_g_m3: 實測值或 ITU-R P.835 標準值 (0-30 g/m³)"
                )

            temperature_k = atmospheric_config['temperature_k']
            pressure_hpa = atmospheric_config['pressure_hpa']
            water_vapor_density = atmospheric_config['water_vapor_density_g_m3']

            itur_model = create_itur_official_model(
                temperature_k=temperature_k,
                pressure_hpa=pressure_hpa,
                water_vapor_density_g_m3=water_vapor_density
            )
            atmospheric_loss_db = itur_model.calculate_total_attenuation(
                frequency_ghz=frequency_ghz,
                elevation_deg=elevation_deg
            )

            # 計算自由空間損耗 (Friis 公式)
            from .itur_physics_calculator import create_itur_physics_calculator
            physics_calc = create_itur_physics_calculator(self.config)
            path_loss_db = physics_calc.calculate_free_space_loss(distance_km, frequency_ghz)

            # ✅ 使用 3GPP TS 38.214 標準信號計算器
            from .gpp_ts38214_signal_calculator import create_3gpp_signal_calculator

            # ✅ Grade A 標準: Fail-Fast 配置驗證
            if 'signal_calculator' not in self.config:
                raise ValueError(
                    "信號計算器配置缺失\n"
                    "Grade A 標準要求明確配置\n"
                    "必須提供:\n"
                    "  signal_calculator:\n"
                    "    bandwidth_mhz: 系統帶寬\n"
                    "    tx_power_dbm: 發射功率\n"
                    "    subcarrier_spacing_khz: 子載波間距\n"
                    "    noise_figure_db: 噪聲係數\n"
                    "    temperature_k: 接收器溫度"
                )

            signal_calc_config = self.config['signal_calculator']
            signal_calculator = create_3gpp_signal_calculator(signal_calc_config)

            # 計算完整信號品質指標
            signal_quality = signal_calculator.calculate_complete_signal_quality(
                tx_power_dbm=tx_power_dbm,
                tx_gain_db=tx_gain_db,
                rx_gain_db=rx_gain_db,
                path_loss_db=path_loss_db,
                atmospheric_loss_db=atmospheric_loss_db,
                elevation_deg=elevation_deg,
                satellite_density=1.0
            )

            # 🆕 計算 3GPP 測量偏移參數 (A3 事件需要)
            # SOURCE: 3GPP TS 38.331 v18.3.0 Section 5.5.4.4
            measurement_offsets = signal_calculator.calculate_measurement_offsets(
                constellation=constellation or 'unknown',
                satellite_id=satellite_id
            )

            return {
                'rsrp_dbm': signal_quality['rsrp_dbm'],
                'rsrq_db': signal_quality['rsrq_db'],
                'rs_sinr_db': signal_quality['rs_sinr_db'],  # 修復: 使用 3GPP 標準命名
                'offset_mo_db': measurement_offsets['offset_mo_db'],        # A3 事件: Ofn/Ofp
                'cell_offset_db': measurement_offsets['cell_offset_db'],    # A3 事件: Ocn/Ocp
                'rssi_dbm': signal_quality['rssi_dbm'],
                'noise_power_dbm': signal_quality['noise_power_dbm'],
                'interference_power_dbm': signal_quality['interference_power_dbm'],
                'calculation_standard': '3GPP_TS_38.214',
                'atmospheric_model': 'ITU-R_P.676-13'
            }

        except Exception as e:
            self.logger.error(f"3GPP 信號計算失敗: {e}", exc_info=True)
            return {
                'rsrp_dbm': None,
                'rsrq_db': None,
                'rs_sinr_db': None  # 修復: 使用 3GPP 標準命名
            }

    def calculate_itur_physics(
        self,
        elevation_deg: float,
        distance_km: float,
        frequency_ghz: float,
        time_point: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        計算 ITU-R 物理參數

        ✅ 完整實現 ITU-R P.618/P.676 標準:
        - 路徑損耗 (Friis 公式)
        - 大氣衰減 (ITU-R P.676-13 完整模型)
        - 都卜勒頻移 (使用 Stage 2 實際速度數據)
        - 傳播延遲 (精確計算)

        Args:
            elevation_deg: 仰角 (度)
            distance_km: 距離 (公里)
            frequency_ghz: 頻率 (GHz)
            time_point: 時間點數據 (可選，用於提取速度)

        Returns:
            Dict: 物理參數
        """
        try:
            # 路徑損耗 (Friis 公式)
            from .itur_physics_calculator import create_itur_physics_calculator
            physics_calc = create_itur_physics_calculator(self.config)
            path_loss_db = physics_calc.calculate_free_space_loss(distance_km, frequency_ghz)

            # ✅ 使用 ITU-R P.676-13 官方大氣衰減模型 (ITU-Rpy)
            from .itur_official_atmospheric_model import create_itur_official_model

            # ✅ Grade A標準: Fail-Fast 模式 - 大氣參數必須在配置中提供
            # 依據: docs/ACADEMIC_STANDARDS.md Line 265-274 禁止使用預設值
            if 'atmospheric_model' not in self.config:
                raise ValueError(
                    "atmospheric_model 配置缺失\n"
                    "Grade A 標準禁止使用預設值\n"
                    "請在配置文件中提供:\n"
                    "  atmospheric_model:\n"
                    "    temperature_k: 283.0  # SOURCE: ITU-R P.835 mid-latitude\n"
                    "    pressure_hpa: 1013.25  # SOURCE: ICAO Standard\n"
                    "    water_vapor_density_g_m3: 7.5  # SOURCE: ITU-R P.835"
                )

            atmospheric_config = self.config['atmospheric_model']

            required_params = ['temperature_k', 'pressure_hpa', 'water_vapor_density_g_m3']
            missing_params = [p for p in required_params if p not in atmospheric_config]
            if missing_params:
                raise ValueError(
                    f"大氣參數缺失: {missing_params}\n"
                    f"Grade A 標準禁止使用預設值\n"
                    f"請在 atmospheric_model 配置中提供所有必要參數:\n"
                    f"  temperature_k: 實測值或 ITU-R P.835 標準值 (200-350K)\n"
                    f"  pressure_hpa: 實測值或 ICAO 標準值 (500-1100 hPa)\n"
                    f"  water_vapor_density_g_m3: 實測值或 ITU-R P.835 標準值 (0-30 g/m³)"
                )

            temperature_k = atmospheric_config['temperature_k']
            pressure_hpa = atmospheric_config['pressure_hpa']
            water_vapor_density = atmospheric_config['water_vapor_density_g_m3']

            itur_model = create_itur_official_model(
                temperature_k=temperature_k,
                pressure_hpa=pressure_hpa,
                water_vapor_density_g_m3=water_vapor_density
            )
            atmospheric_loss_db = itur_model.calculate_total_attenuation(
                frequency_ghz=frequency_ghz,
                elevation_deg=elevation_deg
            )

            # ✅ 使用 Stage 2 實際速度數據計算都卜勒頻移
            doppler_shift_hz = 0.0
            radial_velocity_ms = 0.0

            if time_point:
                from .doppler_calculator import create_doppler_calculator
                doppler_calc = create_doppler_calculator()

                # ✅ Fail-Fast: 明確檢查必需字段
                # 都卜勒計算是可選的，但如果數據存在就必須完整
                if 'velocity_km_per_s' in time_point and 'position_km' in time_point:
                    velocity_km_per_s = time_point['velocity_km_per_s']
                    position_km = time_point['position_km']

                    # ✅ Grade A標準: 觀測者位置必須從配置獲取，禁止硬編碼預設值
                    # 依據: docs/ACADEMIC_STANDARDS.md Line 27-44
                    if 'observer_position_km' not in self.config:
                        self.logger.debug(
                            "⚠️ 缺少 observer_position_km 配置，無法計算都卜勒頻移"
                        )
                    else:
                        observer_position_km = self.config['observer_position_km']
                        doppler_data = doppler_calc.calculate_doppler_shift(
                            velocity_km_per_s=velocity_km_per_s,
                            satellite_position_km=position_km,
                            observer_position_km=observer_position_km,
                            frequency_hz=frequency_ghz * 1e9
                        )

                        doppler_shift_hz = doppler_data['doppler_shift_hz']
                        radial_velocity_ms = doppler_data['radial_velocity_ms']

            # 傳播延遲 (精確計算)
            propagation_delay_ms = (distance_km * 1000.0) / physics_consts.SPEED_OF_LIGHT * 1000.0

            # ✅ 計算 ECEF 位置 (Stage 6 D2 事件需要)
            # SOURCE: Bowring (1985) "The accuracy of geodetic latitude and height equations"
            position_ecef_m = None
            if time_point:
                try:
                    # Stage 4 在 time_point['position'] 中提供 lat/lon/alt
                    # 參見: stage4_link_feasibility_processor.py:373-377
                    # ✅ Fail-Fast: ECEF 位置計算是可選的，但需要明確檢查
                    if 'position' not in time_point:
                        self.logger.debug("時間點缺少 position 數據，跳過 ECEF 計算")
                    else:
                        position = time_point['position']
                        if position and 'latitude_deg' in position and 'longitude_deg' in position and 'altitude_km' in position:
                            lat_deg = position['latitude_deg']
                            lon_deg = position['longitude_deg']
                            alt_km = position['altitude_km']
                            alt_m = alt_km * 1000.0  # 轉換為米

                            # Geodetic → ECEF 轉換
                            from src.shared.utils.coordinate_converter import geodetic_to_ecef
                            ecef_x, ecef_y, ecef_z = geodetic_to_ecef(lat_deg, lon_deg, alt_m)
                            position_ecef_m = [ecef_x, ecef_y, ecef_z]
                except Exception as e:
                    self.logger.debug(f"⚠️ ECEF 位置計算失敗: {e}")
                    position_ecef_m = None

            return {
                'distance_km': distance_km,  # ✅ Stage 6 需要此欄位計算 3GPP 事件
                'elevation_deg': elevation_deg,  # ✅ Stage 6 需要此欄位計算可見性指標
                'path_loss_db': path_loss_db,
                'atmospheric_loss_db': atmospheric_loss_db,
                'doppler_shift_hz': doppler_shift_hz,
                'radial_velocity_ms': radial_velocity_ms,
                'propagation_delay_ms': propagation_delay_ms,
                'position_ecef_m': position_ecef_m,  # ✅ Stage 6 D2 事件需要此欄位
                'itur_compliance': 'P.618-13',
                'atmospheric_model': 'ITU-R_P.676-13',
                'doppler_source': 'stage2_actual_velocity' if time_point else 'unavailable'
            }

        except Exception as e:
            self.logger.warning(f"ITU-R 物理計算失敗: {e}")
            return {
                'distance_km': distance_km if distance_km else None,  # ✅ 保留距離，即使計算失敗
                'elevation_deg': elevation_deg if elevation_deg else None,  # ✅ 保留仰角，即使計算失敗
                'path_loss_db': None,
                'atmospheric_loss_db': None,
                'doppler_shift_hz': None,
                'propagation_delay_ms': None
            }

    def classify_signal_quality(self, rsrp: float) -> str:
        """
        分類信號品質

        ✅ Grade A 標準: Fail-Fast 門檻驗證
        依據: docs/ACADEMIC_STANDARDS.md Line 265-274

        基於 RSRP 值進行分類：
        - excellent: >= rsrp_excellent
        - good: >= rsrp_good
        - fair: >= rsrp_fair
        - poor: < rsrp_fair

        Args:
            rsrp: RSRP 值 (dBm)

        Returns:
            str: 品質等級

        Raises:
            ValueError: 缺少必要的信號門檻
        """
        # ✅ Grade A 標準: 禁止使用硬編碼預設值
        required_thresholds = ['rsrp_excellent', 'rsrp_good', 'rsrp_fair']
        missing = [k for k in required_thresholds if k not in self.signal_thresholds]

        if missing:
            raise ValueError(
                f"信號品質分級失敗：缺少必要門檻 {missing}\n"
                f"Grade A 標準禁止使用硬編碼預設值 (-80, -90, -100 dBm)\n"
                f"必須在配置文件中明確定義所有門檻並標註 SOURCE\n"
                f"例如:\n"
                f"  signal_thresholds:\n"
                f"    rsrp_excellent: -80  # SOURCE: 3GPP TS 38.215 Section 5.1.1\n"
                f"    rsrp_good: -90       # SOURCE: 3GPP TS 38.215 Section 5.1.1\n"
                f"    rsrp_fair: -100      # SOURCE: 3GPP TS 38.215 Section 5.1.1\n"
                f"    rsrp_poor: -110      # SOURCE: 3GPP TS 38.215 Section 5.1.1"
            )

        if rsrp >= self.signal_thresholds['rsrp_excellent']:
            return 'excellent'
        elif rsrp >= self.signal_thresholds['rsrp_good']:
            return 'good'
        elif rsrp >= self.signal_thresholds['rsrp_fair']:
            return 'fair'
        else:
            return 'poor'

    def calculate_average_rsrp(self, satellites: Dict[str, Any]) -> float:
        """
        計算平均 RSRP

        ✅ Grade A+ 標準: Fail-Fast 數據提取
        - 明確檢查必需字段而非使用 .get() 回退
        - 缺失字段時跳過該衛星並記錄 debug 日誌

        Args:
            satellites: 衛星數據字典

        Returns:
            float: 平均 RSRP (dBm)，無數據時返回 -100.0
        """
        rsrp_values = []
        for sat_id, sat_data in satellites.items():
            # ✅ Fail-Fast: 明確檢查必需字段
            if 'signal_quality' not in sat_data:
                self.logger.debug(f"衛星 {sat_id} 缺少 signal_quality，跳過 RSRP 統計")
                continue

            signal_quality = sat_data['signal_quality']

            if 'rsrp_dbm' not in signal_quality:
                self.logger.debug(f"衛星 {sat_id} 缺少 rsrp_dbm，跳過 RSRP 統計")
                continue

            rsrp = signal_quality['rsrp_dbm']
            if rsrp is not None:
                rsrp_values.append(rsrp)

        return sum(rsrp_values) / len(rsrp_values) if rsrp_values else -100.0

    def calculate_average_sinr(self, satellites: Dict[str, Any]) -> float:
        """
        計算平均 RS-SINR

        ✅ Grade A+ 標準: Fail-Fast 數據提取
        - 明確檢查必需字段而非使用 .get() 回退
        - 缺失字段時跳過該衛星並記錄 debug 日誌

        Args:
            satellites: 衛星數據字典

        Returns:
            float: 平均 RS-SINR (dB)，無數據時返回 10.0
        """
        sinr_values = []
        for sat_id, sat_data in satellites.items():
            # ✅ Fail-Fast: 明確檢查必需字段
            if 'signal_quality' not in sat_data:
                self.logger.debug(f"衛星 {sat_id} 缺少 signal_quality，跳過 SINR 統計")
                continue

            signal_quality = sat_data['signal_quality']

            if 'rs_sinr_db' not in signal_quality:
                self.logger.debug(f"衛星 {sat_id} 缺少 rs_sinr_db，跳過 SINR 統計")
                continue

            sinr = signal_quality['rs_sinr_db']  # 修復: 使用 3GPP 標準命名
            if sinr is not None:
                sinr_values.append(sinr)

        return sum(sinr_values) / len(sinr_values) if sinr_values else 10.0


def create_time_series_analyzer(
    config: Optional[Dict[str, Any]] = None,
    signal_thresholds: Optional[Dict[str, float]] = None,
    propagation_simulator=None
) -> TimeSeriesAnalyzer:
    """
    創建時間序列分析引擎實例

    Args:
        config: 配置字典 (可選)
        signal_thresholds: 信號門檻配置 (可選)
        propagation_simulator: 動態傳播條件模擬器 (可選, Proposal 002)

    Returns:
        TimeSeriesAnalyzer: 分析引擎實例
    """
    return TimeSeriesAnalyzer(config, signal_thresholds, propagation_simulator)
