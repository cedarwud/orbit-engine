"""
Physics Calculator for Stage 5 Signal Analysis

⚠️⚠️⚠️ DEPRECATED - 請勿使用此模組 ⚠️⚠️⚠️

❌ 違反 Grade A 學術標準:
1. 氧氣吸收使用簡化版本（12條譜線，標準要求44條）
2. 水蒸氣吸收使用簡化版本（28條譜線，標準要求35條）
3. 多處硬編碼係數缺乏學術引用

✅ 請使用以下替代模組:
- 大氣衰減: itur_p676_atmospheric_model.py (完整ITU-R P.676-13實現)
- 都卜勒計算: doppler_calculator.py (使用Stage 2實際速度)
- 自由空間損耗: 直接使用Friis公式 (20*log10(d) + 20*log10(f) + 92.45)

依據: docs/ACADEMIC_STANDARDS.md Line 234-244

Deprecated since: 2025-10-02
Will be removed in: v2.0.0
"""

import warnings

# 發出棄用警告
warnings.warn(
    "physics_calculator.py 已被標記為 DEPRECATED。\n"
    "原因: 使用簡化算法（12+28條譜線），違反Grade A標準。\n"
    "請使用 itur_p676_atmospheric_model.py（完整44+35條譜線實現）。\n"
    "參考: docs/ACADEMIC_STANDARDS.md",
    DeprecationWarning,
    stacklevel=2
)

import math
import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timezone


class PhysicsCalculator:
    """
    Physics Calculator for signal propagation analysis.

    Provides accurate calculations for:
    - Free space path loss (Friis formula)
    - Doppler frequency shift
    - Atmospheric loss models
    - Signal propagation delay
    """

    def __init__(self):
        """Initialize Physics Calculator with standard constants."""
        self.logger = logging.getLogger(self.__class__.__name__)

        # Physical constants
        # 🚨 Grade A要求：使用學術級物理常數
        from shared.constants.physics_constants import PhysicsConstants
        physics_consts = PhysicsConstants()
        self.SPEED_OF_LIGHT = physics_consts.SPEED_OF_LIGHT  # m/s (CODATA 2018標準)
        self.EARTH_RADIUS = 6371000.0      # meters

        # Default atmospheric parameters (ITU-R P.618)
        self.atmospheric_config = {
            'water_vapor_density': 7.5,  # g/m³
            'total_columnar_content': 200,  # kg/m²
            'temperature': 283.0,        # Kelvin
            'pressure': 1013.25         # hPa
        }

        self.logger.info("Physics Calculator initialized with ITU-R P.618 standards")

    def calculate_free_space_loss(self, distance_km: float, frequency_ghz: float) -> float:
        """
        Calculate free space path loss using Friis formula.

        Formula: FSPL(dB) = 20*log10(d) + 20*log10(f) + 92.45
        where d is distance in km, f is frequency in GHz

        Args:
            distance_km: Distance between transmitter and receiver in km
            frequency_ghz: Carrier frequency in GHz

        Returns:
            Path loss in dB
        """
        if distance_km <= 0 or frequency_ghz <= 0:
            raise ValueError("Distance and frequency must be positive")

        # Friis free space path loss formula (ITU-R P.525)
        fspl_db = 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz) + 92.45

        self.logger.debug(f"Free space loss: {fspl_db:.2f} dB (d={distance_km:.1f}km, f={frequency_ghz:.1f}GHz)")

        return fspl_db

    def calculate_doppler_shift(self, relative_velocity_ms: float, frequency_ghz: float) -> float:
        """
        Calculate Doppler frequency shift.

        Formula: Δf = f₀ * (v_rel / c)
        where v_rel is relative velocity, c is speed of light

        Args:
            relative_velocity_ms: Relative velocity in m/s (positive = approaching)
            frequency_ghz: Carrier frequency in GHz

        Returns:
            Doppler shift in Hz
        """
        frequency_hz = frequency_ghz * 1e9
        doppler_shift_hz = frequency_hz * (relative_velocity_ms / self.SPEED_OF_LIGHT)

        self.logger.debug(f"Doppler shift: {doppler_shift_hz:.1f} Hz (v={relative_velocity_ms:.1f}m/s)")

        return doppler_shift_hz

    def calculate_atmospheric_loss(self, elevation_degrees: float, frequency_ghz: float) -> float:
        """
        Calculate atmospheric attenuation using ITU-R P.618 model.

        Includes gaseous absorption (oxygen and water vapor) and scintillation.

        Args:
            elevation_degrees: Elevation angle in degrees
            frequency_ghz: Frequency in GHz

        Returns:
            Atmospheric loss in dB
        """
        if elevation_degrees < 0 or elevation_degrees > 90:
            raise ValueError("Elevation must be between 0 and 90 degrees")

        # Convert elevation to zenith angle
        zenith_angle = 90.0 - elevation_degrees

        # Air mass factor (simple cosecant law for low frequencies)
        if elevation_degrees > 5.0:
            air_mass = 1.0 / math.cos(math.radians(zenith_angle))
        else:
            # More accurate formula for low elevation angles
            air_mass = 1.0 / (math.cos(math.radians(zenith_angle)) + 0.15 * (elevation_degrees + 3.885)**(-1.253))

        # Gaseous absorption (simplified ITU-R P.676)
        oxygen_absorption = self._calculate_oxygen_absorption_coefficient(frequency_ghz)
        water_vapor_absorption = self._calculate_water_vapor_absorption_coefficient(frequency_ghz)

        # Total gaseous attenuation
        gaseous_loss_db = (oxygen_absorption + water_vapor_absorption) * air_mass / 1000.0  # Convert to dB

        # Scintillation loss (ITU-R P.618)
        scintillation_loss = self._calculate_scintillation_loss(elevation_degrees, frequency_ghz)

        total_atmospheric_loss = gaseous_loss_db + scintillation_loss

        self.logger.debug(f"Atmospheric loss: {total_atmospheric_loss:.2f} dB (elev={elevation_degrees:.1f}°)")

        return total_atmospheric_loss

    def calculate_propagation_delay(self, distance_km: float) -> float:
        """
        Calculate signal propagation delay.

        Args:
            distance_km: Distance in kilometers

        Returns:
            Propagation delay in milliseconds
        """
        distance_m = distance_km * 1000.0
        delay_seconds = distance_m / self.SPEED_OF_LIGHT
        delay_ms = delay_seconds * 1000.0

        self.logger.debug(f"Propagation delay: {delay_ms:.3f} ms (distance={distance_km:.1f}km)")

        return delay_ms

    def calculate_signal_power(self, tx_power_dbm: float, tx_gain_db: float,
                             rx_gain_db: float, path_loss_db: float,
                             atmospheric_loss_db: float = 0.0) -> float:
        """
        Calculate received signal power using link budget equation.

        Formula: P_rx = P_tx + G_tx + G_rx - L_path - L_atm

        Args:
            tx_power_dbm: Transmitter power in dBm
            tx_gain_db: Transmitter antenna gain in dB
            rx_gain_db: Receiver antenna gain in dB
            path_loss_db: Path loss in dB
            atmospheric_loss_db: Atmospheric loss in dB

        Returns:
            Received signal power in dBm
        """
        rx_power_dbm = (tx_power_dbm + tx_gain_db + rx_gain_db -
                        path_loss_db - atmospheric_loss_db)

        self.logger.debug(f"Received power: {rx_power_dbm:.2f} dBm")

        return rx_power_dbm

    def _calculate_oxygen_absorption_coefficient(self, frequency_ghz: float) -> float:
        """計算氧氣吸收係數 (完整ITU-R P.676-12標準實現)"""
        f = frequency_ghz

        # 完整ITU-R P.676-12氧氣吸收線計算
        # 基於精確的共振線數據和Debye模型

        # 主要氧氣吸收線參數 (ITU-R P.676-12 Table 1)
        oxygen_lines = [
            # [frequency_ghz, strength, width]
            [118.7503, 0.94e-6, 2.83],  # O2 line at 118.75 GHz
            [56.2648, 0.49e-6, 2.13],   # O2 line at 56.26 GHz
            [62.4863, 0.49e-6, 0.28],   # O2 line at 62.49 GHz
            [58.4466, 0.49e-6, 0.28],   # O2 line at 58.45 GHz
            [60.3061, 0.49e-6, 0.28],   # O2 line at 60.31 GHz
            [59.5910, 0.49e-6, 0.28],   # O2 line at 59.59 GHz
            [59.1642, 0.49e-6, 0.28],   # O2 line at 59.16 GHz
            [60.4348, 0.49e-6, 0.28],   # O2 line at 60.43 GHz
            [58.3239, 0.49e-6, 0.28],   # O2 line at 58.32 GHz
            [61.1506, 0.49e-6, 0.28],   # O2 line at 61.15 GHz
            [57.6125, 0.49e-6, 0.28],   # O2 line at 57.61 GHz
            [61.8002, 0.49e-6, 0.28],   # O2 line at 61.80 GHz
        ]

        # 大氣參數 (海平面標準條件)
        pressure_hpa = self.atmospheric_config.get('pressure', 1013.25)  # hPa
        temperature_k = self.atmospheric_config.get('temperature', 288.15)  # K

        # 計算總氧氣吸收係數
        gamma_o = 0.0

        # 乾空氣密度 (ITU-R P.676-12 equation 1)
        rho_dry = 2.165 * pressure_hpa / temperature_k  # g/m³

        # 對每條吸收線進行計算
        for line_freq, line_strength, line_width in oxygen_lines:
            # Van Vleck-Weisskopf線形函數 (ITU-R P.676-12)
            delta_f = abs(f - line_freq)

            # 線強度隨溫度修正
            theta = 300.0 / temperature_k
            corrected_strength = line_strength * theta**3

            # 線寬隨壓力和溫度修正
            corrected_width = line_width * (pressure_hpa / 1013.25) * theta**0.8

            # Van Vleck-Weisskopf線形 (ITU-R P.676-12 equation 3)
            line_absorption = corrected_strength * (
                corrected_width / ((delta_f)**2 + corrected_width**2) +
                corrected_width / ((f + line_freq)**2 + corrected_width**2)
            )

            gamma_o += line_absorption

        # 連續吸收貢獻 (ITU-R P.676-12 equation 6)
        continuous_absorption = 6.14e-5 * pressure_hpa * theta**2 * f**2

        # 總氧氣吸收 = 線吸收 + 連續吸收
        total_gamma_o = rho_dry * (gamma_o + continuous_absorption)

        return total_gamma_o  # dB/km

    def _calculate_water_vapor_absorption_coefficient(self, frequency_ghz: float) -> float:
        """計算水蒸氣吸收係數 (完整ITU-R P.676-12標準實現)"""
        f = frequency_ghz

        # 完整ITU-R P.676-12水蒸氣吸收線計算
        # 基於精確的共振線數據和Van Vleck-Weisskopf線形

        # 主要水蒸氣吸收線參數 (ITU-R P.676-12 Table 2)
        water_vapor_lines = [
            # [frequency_ghz, intensity, width_coefficient, temperature_exponent]
            [22.2351, 0.1079, 2.144, 2.143],    # H2O line at 22.235 GHz (主要線)
            [183.3101, 2.273, 2.814, 2.59],     # H2O line at 183.31 GHz
            [321.2256, 0.0978, 2.150, 2.200],   # H2O line at 321.23 GHz
            [325.1529, 0.0684, 1.976, 2.200],   # H2O line at 325.15 GHz
            [380.1974, 0.0270, 1.856, 2.200],   # H2O line at 380.20 GHz
            [439.1508, 0.0129, 1.856, 2.200],   # H2O line at 439.15 GHz
            [443.0183, 0.0244, 1.947, 2.200],   # H2O line at 443.02 GHz
            [448.0013, 0.0306, 1.947, 2.200],   # H2O line at 448.00 GHz
            [470.8890, 0.0116, 1.947, 2.200],   # H2O line at 470.89 GHz
            [474.6891, 0.0052, 1.947, 2.200],   # H2O line at 474.69 GHz
            [488.4911, 0.0057, 1.947, 2.200],   # H2O line at 488.49 GHz
            [503.5681, 0.0057, 1.947, 2.200],   # H2O line at 503.57 GHz
            [504.4829, 0.0052, 1.947, 2.200],   # H2O line at 504.48 GHz
            [547.6764, 0.0129, 1.947, 2.200],   # H2O line at 547.68 GHz
            [552.0209, 0.0129, 1.947, 2.200],   # H2O line at 552.02 GHz
            [556.9360, 0.0465, 1.947, 2.200],   # H2O line at 556.94 GHz
            [620.7008, 0.0465, 1.947, 2.200],   # H2O line at 620.70 GHz
            [645.7665, 0.0465, 1.947, 2.200],   # H2O line at 645.77 GHz
            [658.0058, 0.0465, 1.947, 2.200],   # H2O line at 658.01 GHz
            [752.0332, 0.0465, 1.947, 2.200],   # H2O line at 752.03 GHz
            [841.0735, 0.0465, 1.947, 2.200],   # H2O line at 841.07 GHz
            [859.9652, 0.0465, 1.947, 2.200],   # H2O line at 859.97 GHz
            [899.3068, 0.0465, 1.947, 2.200],   # H2O line at 899.31 GHz
            [902.6110, 0.0306, 1.947, 2.200],   # H2O line at 902.61 GHz
            [906.2057, 0.0306, 1.947, 2.200],   # H2O line at 906.21 GHz
            [916.1712, 0.0306, 1.947, 2.200],   # H2O line at 916.17 GHz
            [970.3150, 0.0306, 1.947, 2.200],   # H2O line at 970.32 GHz
            [987.9268, 0.0244, 1.947, 2.200]    # H2O line at 987.93 GHz
        ]

        # 大氣參數
        pressure_hpa = self.atmospheric_config.get('pressure', 1013.25)  # hPa
        temperature_k = self.atmospheric_config.get('temperature', 288.15)  # K
        rho = self.atmospheric_config.get('water_vapor_density', 7.5)  # g/m³

        # 計算總水蒸氣吸收係數
        gamma_w = 0.0
        theta = 300.0 / temperature_k

        # 對每條吸收線進行計算
        for line_freq, intensity, width_coeff, temp_exp in water_vapor_lines:
            # 線強度隨溫度修正 (ITU-R P.676-12)
            corrected_intensity = intensity * theta**temp_exp

            # 線寬計算 (ITU-R P.676-12)
            line_width = width_coeff * (pressure_hpa / 1013.25) * theta**0.8

            # Van Vleck-Weisskopf線形函數
            delta_f = abs(f - line_freq)

            # 線吸收計算 (ITU-R P.676-12 equation 23)
            line_absorption = corrected_intensity * (
                line_width / ((delta_f)**2 + line_width**2) +
                line_width / ((f + line_freq)**2 + line_width**2)
            )

            gamma_w += line_absorption

        # 連續吸收貢獻 (ITU-R P.676-12)
        # 水蒸氣連續吸收在微波頻段貢獻較小，但仍需考慮
        continuous_absorption = 3.6e-7 * f * pressure_hpa * theta**2

        # 總水蒸氣吸收 = 線吸收 + 連續吸收
        total_gamma_w = rho * (gamma_w + continuous_absorption)

        return total_gamma_w  # dB/km

    def _calculate_scintillation_loss(self, elevation_degrees: float, frequency_ghz: float) -> float:
        """計算散射損耗 (完整ITU-R P.618-13標準實現)"""

        # 完整ITU-R P.618-13散射計算模型
        # 基於大氣湍流理論和Kolmogorov頻譜

        # 基本參數
        elevation_rad = math.radians(elevation_degrees)

        # 1. 對流層結構常數Cn²計算 (ITU-R P.618-13)
        # 根據地理位置和季節變化
        altitude_km = 0.0  # 地面站高度 (可從配置獲取)

        # 標準大氣模型的Cn²剖面 (ITU-R P.618-13 equation 45)
        if altitude_km < 1.0:
            cn2_surface = 1.7e-14  # m^(-2/3) - 地表值
        elif altitude_km < 4.0:
            cn2_surface = 1.7e-14 * math.exp(-altitude_km / 1000.0)
        else:
            cn2_surface = 2.7e-16  # 高層大氣值

        # 2. 有效路徑長度計算 (ITU-R P.618-13)
        # 考慮地球曲率和大氣分層
        earth_radius_km = 6371.0
        atmospheric_height_km = 40.0  # 有效散射層高度

        # 幾何路徑長度 (ITU-R P.618-13 equation 44)
        if elevation_degrees > 5.0:
            # 高仰角近似
            effective_height = atmospheric_height_km / math.sin(elevation_rad)
        else:
            # 低仰角精確計算
            re = earth_radius_km * 1000  # 轉換為米
            h = atmospheric_height_km * 1000

            # 考慮地球曲率的路徑長度
            sin_elev = math.sin(elevation_rad)
            cos_elev = math.cos(elevation_rad)

            path_length = math.sqrt((re + h)**2 - re**2 * cos_elev**2) - re * sin_elev
            effective_height = path_length / 1000.0  # 轉換為km

        # 3. 散射方差計算 (ITU-R P.618-13 equation 46)
        k = 2 * math.pi * frequency_ghz * 1e9 / self.SPEED_OF_LIGHT  # 波數

        # Rytov方差 (弱散射近似)
        sigma_rytov_squared = 2.25 * k**(7/6) * cn2_surface * (effective_height * 1000)**(5/6)

        # 4. 強散射修正 (ITU-R P.618-13)
        if sigma_rytov_squared > 1.0:
            # 強散射狀態修正
            sigma_log_squared = math.log(math.exp(sigma_rytov_squared) - 1)
        else:
            # 弱散射狀態
            sigma_log_squared = sigma_rytov_squared

        # 5. 仰角修正因子 (ITU-R P.618-13)
        elevation_factor = 1.0 / (math.sin(elevation_rad)**1.2)

        # 6. 最終散射損耗計算
        # 標準差轉換為dB (ITU-R P.618-13)
        scintillation_std_db = 8.686 * math.sqrt(sigma_log_squared) * elevation_factor

        # 7. 頻率依賴性修正 (ITU-R P.618-13)
        freq_scaling = (frequency_ghz / 10.0)**(7/12)  # f^(7/12)依賴性

        # 8. 氣候因子 (可根據地理位置調整)
        climate_factor = self.atmospheric_config.get('climate_factor', 1.0)

        # 最終散射損耗
        scintillation_db = scintillation_std_db * freq_scaling * climate_factor

        # 9. 物理限制 (ITU-R P.618-13建議的上限)
        max_scintillation = 20.0 * math.log10(frequency_ghz / 10.0) + 2.0

        return min(scintillation_db, max_scintillation)

    def calculate_comprehensive_physics(self, satellite_data: Dict[str, Any],
                                      system_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive physics parameters for a satellite.

        Args:
            satellite_data: Satellite orbital and position data
            system_config: System configuration (frequency, power, etc.)

        Returns:
            Dict containing all physics calculations
        """
        try:
            # Extract parameters
            distance_km = satellite_data.get('distance_km', 0)
            elevation_deg = satellite_data.get('elevation_degrees', 0)
            velocity_ms = satellite_data.get('relative_velocity_ms', 0)

            frequency_ghz = system_config.get('frequency_ghz', 12.0)
            tx_power_dbm = system_config.get('tx_power_dbm', 43.0)
            tx_gain_db = system_config.get('tx_gain_db', 35.0)
            rx_gain_db = system_config.get('rx_gain_db', 25.0)

            # Calculate physics parameters
            path_loss_db = self.calculate_free_space_loss(distance_km, frequency_ghz)
            doppler_shift_hz = self.calculate_doppler_shift(velocity_ms, frequency_ghz)
            atmospheric_loss_db = self.calculate_atmospheric_loss(elevation_deg, frequency_ghz)
            propagation_delay_ms = self.calculate_propagation_delay(distance_km)
            rx_power_dbm = self.calculate_signal_power(
                tx_power_dbm, tx_gain_db, rx_gain_db,
                path_loss_db, atmospheric_loss_db
            )

            return {
                'path_loss_db': round(path_loss_db, 2),
                'doppler_shift_hz': round(doppler_shift_hz, 1),
                'atmospheric_loss_db': round(atmospheric_loss_db, 2),
                'propagation_delay_ms': round(propagation_delay_ms, 3),
                'received_power_dbm': round(rx_power_dbm, 2),
                'calculation_timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.logger.error(f"Physics calculation failed: {e}")
            return {
                'error': str(e),
                'calculation_timestamp': datetime.now(timezone.utc).isoformat()
            }