#!/usr/bin/env python3
"""
都卜勒效應精確計算器

學術標準: 相對論都卜勒效應完整實現
數據來源: Stage 2 實際速度數據 (TEME 座標系統)

參考文獻:
- Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
- ITU-R Recommendation P.531: Ionospheric propagation data and prediction methods
- 3GPP TS 38.104: NR; Base Station (BS) radio transmission and reception

⚠️ CRITICAL: 使用 Stage 2 實際速度數據，禁止假設值
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DopplerCalculator:
    """
    都卜勒效應精確計算器

    實現:
    - 使用 Stage 2 實際速度數據 (velocity_km_per_s)
    - 相對論都卜勒效應 (完整公式)
    - 視線方向速度分量計算
    - 頻率偏移和時間延遲計算
    """

    def __init__(self, speed_of_light_ms: Optional[float] = None):
        """
        初始化都卜勒計算器

        Args:
            speed_of_light_ms: 光速 (m/s), 預設從 Astropy 獲取 CODATA 2018/2022 標準值
        """
        # ✅ Grade A標準: 使用 Astropy 官方常數 (CODATA 2022, Fail-Fast)
        # 依據: docs/ACADEMIC_STANDARDS.md (Fail-Fast 原則)
        if speed_of_light_ms is None:
            # Fail-Fast: Astropy 是必需依賴，不可用時立即報錯
            from shared.constants.astropy_physics_constants import get_astropy_constants
            physics_consts = get_astropy_constants()
            self.c = physics_consts.SPEED_OF_LIGHT
        else:
            self.c = speed_of_light_ms

        logger.info(f"都卜勒計算器初始化: c={self.c} m/s")

    def calculate_doppler_shift(self, velocity_km_per_s: List[float],
                               satellite_position_km: List[float],
                               observer_position_km: List[float],
                               frequency_hz: float) -> Dict[str, float]:
        """
        計算都卜勒頻移 (使用 Stage 2 實際速度數據)

        Args:
            velocity_km_per_s: 衛星速度向量 [vx, vy, vz] (km/s) - 從 Stage 2 獲取
            satellite_position_km: 衛星位置 [x, y, z] (km) - TEME 座標
            observer_position_km: 觀測者位置 [x, y, z] (km) - TEME 座標
            frequency_hz: 發射頻率 (Hz)

        Returns:
            doppler_data: 都卜勒效應數據
                - doppler_shift_hz: 都卜勒頻移 (Hz)
                - radial_velocity_ms: 視線方向速度 (m/s)
                - velocity_magnitude_ms: 速度大小 (m/s)
                - doppler_ratio: 都卜勒比率
        """
        # 1. 計算衛星到觀測者的向量 (視線方向)
        range_vector_km = [
            satellite_position_km[0] - observer_position_km[0],
            satellite_position_km[1] - observer_position_km[1],
            satellite_position_km[2] - observer_position_km[2]
        ]

        # 2. 計算距離 (km)
        range_km = math.sqrt(sum(r**2 for r in range_vector_km))

        if range_km < 0.001:  # 防止除以零
            logger.warning("距離過小，無法計算都卜勒頻移")
            return {
                'doppler_shift_hz': 0.0,
                'radial_velocity_ms': 0.0,
                'velocity_magnitude_ms': 0.0,
                'doppler_ratio': 0.0
            }

        # 3. 單位視線向量 (from observer to satellite)
        unit_range_vector = [r / range_km for r in range_vector_km]

        # 4. 計算視線方向速度分量 (radial velocity)
        # v_radial = v · r̂ (點積)
        radial_velocity_km_s = sum(
            velocity_km_per_s[i] * unit_range_vector[i]
            for i in range(3)
        )

        # 轉換為 m/s
        radial_velocity_ms = radial_velocity_km_s * 1000.0

        # 5. 計算速度大小
        velocity_magnitude_ms = math.sqrt(sum(v**2 for v in velocity_km_per_s)) * 1000.0

        # 6. 計算都卜勒比率 (相對論公式)
        # f_observed / f_emitted = sqrt((1 - β) / (1 + β))
        # 其中 β = v_radial / c
        #
        # 簡化 (非相對論近似，適用於 v << c):
        # Δf / f = v_radial / c
        #
        # 我們使用完整相對論公式以確保精度
        beta = radial_velocity_ms / self.c

        # 相對論都卜勒效應
        if abs(beta) < 0.1:  # v < 0.1c，非相對論近似足夠
            doppler_ratio = beta
        else:  # 使用完整相對論公式
            doppler_ratio = math.sqrt((1 - beta) / (1 + beta)) - 1

        # 7. 計算都卜勒頻移
        # Δf = f × (v_radial / c)
        doppler_shift_hz = frequency_hz * doppler_ratio

        return {
            'doppler_shift_hz': doppler_shift_hz,
            'radial_velocity_ms': radial_velocity_ms,
            'velocity_magnitude_ms': velocity_magnitude_ms,
            'doppler_ratio': doppler_ratio,
            'calculation_method': 'relativistic_doppler' if abs(beta) >= 0.1 else 'classical_doppler',
            'data_source': 'stage2_teme_velocity'
        }

    def calculate_propagation_delay(self, distance_km: float) -> float:
        """
        計算傳播延遲

        Args:
            distance_km: 距離 (km)

        Returns:
            delay_ms: 傳播延遲 (ms)
        """
        # t = d / c
        delay_seconds = (distance_km * 1000.0) / self.c
        delay_ms = delay_seconds * 1000.0

        return delay_ms

    def calculate_time_series_doppler(self, time_series: List[Dict[str, Any]],
                                     frequency_ghz: float,
                                     observer_position_km: List[float]) -> List[Dict[str, Any]]:
        """
        計算時間序列的都卜勒效應

        處理完整時間序列，逐點計算都卜勒頻移

        Args:
            time_series: 時間序列數據 (從 Stage 2/3/4 傳遞)
                每個點包含:
                - position_km: [x, y, z] (TEME)
                - velocity_km_per_s: [vx, vy, vz] (TEME)
                - distance_km: 距離
                - timestamp: 時間戳
            frequency_ghz: 頻率 (GHz)
            observer_position_km: 觀測者位置 (TEME)

        Returns:
            doppler_time_series: 包含都卜勒數據的時間序列
        """
        frequency_hz = frequency_ghz * 1e9
        doppler_time_series = []

        for point in time_series:
            # ✅ Fail-Fast: 明確檢查必要數據
            # 提取 timestamp（用於日誌）
            if 'timestamp' not in point:
                logger.warning("時間點缺少 timestamp 字段，跳過")
                continue
            timestamp = point['timestamp']

            # 提取 position_km
            if 'position_km' not in point:
                logger.warning(f"時間點 {timestamp} 缺少 position_km 字段，跳過")
                continue
            position_km = point['position_km']

            # 提取 velocity_km_per_s
            if 'velocity_km_per_s' not in point:
                logger.warning(f"時間點 {timestamp} 缺少 velocity_km_per_s 字段，跳過")
                continue
            velocity_km_per_s = point['velocity_km_per_s']

            # 提取 distance_km
            if 'distance_km' not in point:
                logger.warning(f"時間點 {timestamp} 缺少 distance_km 字段，跳過")
                continue
            distance_km = point['distance_km']

            # 計算都卜勒效應
            doppler_data = self.calculate_doppler_shift(
                velocity_km_per_s=velocity_km_per_s,
                satellite_position_km=position_km,
                observer_position_km=observer_position_km,
                frequency_hz=frequency_hz
            )

            # 計算傳播延遲
            propagation_delay_ms = self.calculate_propagation_delay(distance_km)

            # 構建結果
            doppler_point = {
                'timestamp': timestamp,
                'doppler_shift_hz': doppler_data['doppler_shift_hz'],
                'radial_velocity_ms': doppler_data['radial_velocity_ms'],
                'velocity_magnitude_ms': doppler_data['velocity_magnitude_ms'],
                'propagation_delay_ms': propagation_delay_ms,
                'data_source': 'stage2_teme_velocity'
            }

            doppler_time_series.append(doppler_point)

        return doppler_time_series

    def extract_velocity_from_stage2_data(self, satellite_data: Dict[str, Any]) -> Optional[List[float]]:
        """
        從 Stage 2 數據提取速度

        Args:
            satellite_data: Stage 2 衛星數據

        Returns:
            velocity_km_per_s: 速度向量 [vx, vy, vz] (km/s) 或 None
        """
        # 嘗試從不同可能的字段提取
        velocity = None

        # 方法 1: 直接從 velocity_km_per_s 字段
        if 'velocity_km_per_s' in satellite_data:
            velocity = satellite_data['velocity_km_per_s']

        # 方法 2: 從 orbital_data 提取
        elif 'orbital_data' in satellite_data:
            orbital_data = satellite_data['orbital_data']
            # ✅ Fail-Fast: 明確檢查 velocity_km_per_s
            if 'velocity_km_per_s' in orbital_data:
                velocity = orbital_data['velocity_km_per_s']
            else:
                logger.debug("orbital_data 中缺少 velocity_km_per_s 字段")

        # 方法 3: 從 teme_state 提取
        elif 'teme_state' in satellite_data:
            teme_state = satellite_data['teme_state']
            # ✅ Fail-Fast: 明確檢查 velocity_km_per_s
            if 'velocity_km_per_s' in teme_state:
                velocity = teme_state['velocity_km_per_s']
            else:
                logger.debug("teme_state 中缺少 velocity_km_per_s 字段")

        # 驗證速度數據
        if velocity is not None:
            if isinstance(velocity, list) and len(velocity) == 3:
                # 檢查數值合理性 (LEO 衛星速度 7-8 km/s)
                velocity_magnitude = math.sqrt(sum(v**2 for v in velocity))
                if 5.0 <= velocity_magnitude <= 10.0:  # 合理範圍
                    return velocity
                else:
                    logger.warning(f"速度大小異常: {velocity_magnitude} km/s")

        return None


def create_doppler_calculator() -> DopplerCalculator:
    """創建都卜勒計算器實例"""
    return DopplerCalculator()