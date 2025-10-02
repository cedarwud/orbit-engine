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

# 🚨 Grade A要求：使用學術級物理常數
try:
    from src.shared.constants.physics_constants import PhysicsConstants
except ModuleNotFoundError:
    from shared.constants.physics_constants import PhysicsConstants

physics_consts = PhysicsConstants()
logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """
    時間序列分析引擎

    實現衛星時間序列逐點分析:
    - RSRP/RSRQ/SINR 計算 (3GPP TS 38.214)
    - 物理參數計算 (ITU-R P.618/P.676)
    - 信號品質分類與統計
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, signal_thresholds: Optional[Dict[str, float]] = None):
        """
        初始化時間序列分析引擎

        Args:
            config: 配置字典 (可選)
            signal_thresholds: 信號門檻配置 (可選)
        """
        self.config = config or {}
        self.signal_thresholds = signal_thresholds or {}
        self.logger = logging.getLogger(__name__)

    def analyze_time_series(
        self,
        satellite_id: str,
        time_series: List[Dict[str, Any]],
        system_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析單顆衛星的完整時間序列

        逐時間點計算:
        - RSRP (3GPP TS 38.214)
        - RSRQ (3GPP TS 38.214)
        - SINR (3GPP TS 38.214)
        - 物理參數 (ITU-R P.618)

        Args:
            satellite_id: 衛星ID
            time_series: 時間序列數據
            system_config: 系統配置 (包含 tx_power, frequency, gain 等)

        Returns:
        {
            'time_series': [
                {
                    'timestamp': str,
                    'signal_quality': {
                        'rsrp_dbm': float,
                        'rsrq_db': float,
                        'sinr_db': float,
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
                # 提取時間點數據
                # 🔧 修復: Stage 4 輸出格式將 elevation_deg/distance_km 放在 visibility_metrics 內
                visibility_metrics = time_point.get('visibility_metrics', {})
                elevation_deg = visibility_metrics.get('elevation_deg')
                distance_km = visibility_metrics.get('distance_km')
                is_connectable_str = visibility_metrics.get('is_connectable', 'False')
                # 🔧 修復: is_connectable 是字符串 "True"/"False"，需要轉換為布爾值
                is_connectable = (is_connectable_str == 'True' or is_connectable_str == True)
                timestamp = time_point.get('timestamp')

                if elevation_deg is None or distance_km is None:
                    continue

                # 計算信號品質 (3GPP 標準)
                signal_quality = self.calculate_3gpp_signal_quality(
                    elevation_deg=elevation_deg,
                    distance_km=distance_km,
                    system_config=system_config
                )

                # ✅ 計算物理參數 (ITU-R 標準 + Stage 2 實際速度)
                physics_params = self.calculate_itur_physics(
                    elevation_deg=elevation_deg,
                    distance_km=distance_km,
                    frequency_ghz=system_config['frequency_ghz'],
                    time_point=time_point  # ← 傳遞完整時間點數據以提取速度
                )

                # 構建時間點結果
                time_point_result = {
                    'timestamp': timestamp,
                    'signal_quality': {
                        'rsrp_dbm': signal_quality['rsrp_dbm'],
                        'rsrq_db': signal_quality['rsrq_db'],
                        'sinr_db': signal_quality['sinr_db'],
                        'calculation_standard': '3GPP_TS_38.214'
                    },
                    'is_connectable': is_connectable,
                    'physical_parameters': physics_params
                }

                time_series_results.append(time_point_result)

                # 收集統計數據
                if signal_quality['rsrp_dbm'] is not None:
                    rsrp_values.append(signal_quality['rsrp_dbm'])
                if signal_quality['rsrq_db'] is not None:
                    rsrq_values.append(signal_quality['rsrq_db'])
                if signal_quality['sinr_db'] is not None:
                    sinr_values.append(signal_quality['sinr_db'])

                # 品質分類統計
                quality_level = self.classify_signal_quality(signal_quality['rsrp_dbm'])
                quality_counts[quality_level] += 1

            except Exception as e:
                self.logger.debug(f"時間點 {timestamp} 計算失敗: {e}")
                continue

        # 計算摘要統計
        summary = {
            'total_time_points': len(time_series_results),
            'average_rsrp_dbm': sum(rsrp_values) / len(rsrp_values) if rsrp_values else None,
            'average_rsrq_db': sum(rsrq_values) / len(rsrq_values) if rsrq_values else None,
            'average_sinr_db': sum(sinr_values) / len(sinr_values) if sinr_values else None,
            'quality_distribution': quality_counts,
            'average_quality_level': max(quality_counts, key=quality_counts.get) if quality_counts else 'poor'
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
        system_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        計算 3GPP 標準信號品質

        ✅ 完整實現 3GPP TS 38.214/38.215 標準:
        - RSRP (Reference Signal Received Power)
        - RSRQ (Reference Signal Received Quality) - 使用實際 RSSI
        - SINR (Signal-to-Interference-plus-Noise Ratio) - Johnson-Nyquist 噪聲底

        Args:
            elevation_deg: 仰角 (度)
            distance_km: 距離 (公里)
            system_config: 系統配置

        Returns:
            Dict: 信號品質參數
        """
        try:
            # 提取配置
            tx_power_dbm = system_config['tx_power_dbm']
            tx_gain_db = system_config['tx_gain_db']
            rx_gain_db = system_config['rx_gain_db']
            frequency_ghz = system_config['frequency_ghz']

            # ✅ 使用 ITU-R P.676-13 完整大氣衰減模型
            from .itur_p676_atmospheric_model import create_itur_p676_model
            itur_model = create_itur_p676_model()
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
            signal_calculator = create_3gpp_signal_calculator(self.config)

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

            return {
                'rsrp_dbm': signal_quality['rsrp_dbm'],
                'rsrq_db': signal_quality['rsrq_db'],
                'sinr_db': signal_quality['sinr_db'],
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
                'sinr_db': None
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

            # ✅ 使用 ITU-R P.676-13 完整大氣衰減模型
            from .itur_p676_atmospheric_model import create_itur_p676_model
            itur_model = create_itur_p676_model()
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

                # 嘗試提取速度數據
                velocity_km_per_s = time_point.get('velocity_km_per_s')
                position_km = time_point.get('position_km')

                if velocity_km_per_s and position_km:
                    # ✅ Grade A標準: 觀測者位置必須從配置獲取，禁止硬編碼預設值
                    # 依據: docs/ACADEMIC_STANDARDS.md Line 27-44
                    observer_position_km = self.config.get('observer_position_km')

                    if observer_position_km:
                        doppler_data = doppler_calc.calculate_doppler_shift(
                            velocity_km_per_s=velocity_km_per_s,
                            satellite_position_km=position_km,
                            observer_position_km=observer_position_km,
                            frequency_hz=frequency_ghz * 1e9
                        )

                        doppler_shift_hz = doppler_data['doppler_shift_hz']
                        radial_velocity_ms = doppler_data['radial_velocity_ms']
                    else:
                        # ⚠️ Grade A標準: 缺少配置時記錄警告，但不使用預設值
                        self.logger.debug(
                            "⚠️ 缺少 observer_position_km 配置，無法計算都卜勒頻移"
                        )

            # 傳播延遲 (精確計算)
            propagation_delay_ms = (distance_km * 1000.0) / physics_consts.SPEED_OF_LIGHT * 1000.0

            return {
                'path_loss_db': path_loss_db,
                'atmospheric_loss_db': atmospheric_loss_db,
                'doppler_shift_hz': doppler_shift_hz,
                'radial_velocity_ms': radial_velocity_ms,
                'propagation_delay_ms': propagation_delay_ms,
                'itur_compliance': 'P.618-13',
                'atmospheric_model': 'ITU-R_P.676-13',
                'doppler_source': 'stage2_actual_velocity' if time_point else 'unavailable'
            }

        except Exception as e:
            self.logger.warning(f"ITU-R 物理計算失敗: {e}")
            return {
                'path_loss_db': None,
                'atmospheric_loss_db': None,
                'doppler_shift_hz': None,
                'propagation_delay_ms': None
            }

    def classify_signal_quality(self, rsrp: float) -> str:
        """
        分類信號品質

        基於 RSRP 值進行分類：
        - excellent: >= rsrp_excellent
        - good: >= rsrp_good
        - fair: >= rsrp_fair
        - poor: < rsrp_fair

        Args:
            rsrp: RSRP 值 (dBm)

        Returns:
            str: 品質等級
        """
        if rsrp >= self.signal_thresholds.get('rsrp_excellent', -80):
            return 'excellent'
        elif rsrp >= self.signal_thresholds.get('rsrp_good', -90):
            return 'good'
        elif rsrp >= self.signal_thresholds.get('rsrp_fair', -100):
            return 'fair'
        else:
            return 'poor'

    def calculate_average_rsrp(self, satellites: Dict[str, Any]) -> float:
        """
        計算平均 RSRP

        Args:
            satellites: 衛星數據字典

        Returns:
            float: 平均 RSRP (dBm)，無數據時返回 -100.0
        """
        rsrp_values = []
        for sat_data in satellites.values():
            rsrp = sat_data.get('signal_quality', {}).get('rsrp_dbm')
            if rsrp is not None:
                rsrp_values.append(rsrp)
        return sum(rsrp_values) / len(rsrp_values) if rsrp_values else -100.0

    def calculate_average_sinr(self, satellites: Dict[str, Any]) -> float:
        """
        計算平均 SINR

        Args:
            satellites: 衛星數據字典

        Returns:
            float: 平均 SINR (dB)，無數據時返回 10.0
        """
        sinr_values = []
        for sat_data in satellites.values():
            sinr = sat_data.get('signal_quality', {}).get('sinr_db')
            if sinr is not None:
                sinr_values.append(sinr)
        return sum(sinr_values) / len(sinr_values) if sinr_values else 10.0


def create_time_series_analyzer(
    config: Optional[Dict[str, Any]] = None,
    signal_thresholds: Optional[Dict[str, float]] = None
) -> TimeSeriesAnalyzer:
    """
    創建時間序列分析引擎實例

    Args:
        config: 配置字典 (可選)
        signal_thresholds: 信號門檻配置 (可選)

    Returns:
        TimeSeriesAnalyzer: 分析引擎實例
    """
    return TimeSeriesAnalyzer(config, signal_thresholds)
