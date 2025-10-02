#!/usr/bin/env python3
"""
Stage 3 幾何預篩選器 - 快速可見性初步判斷

🎯 核心目標：
- 在精密 Skyfield 轉換前快速篩選明顯不可見的衛星
- 減少 77.5% 無效座標計算浪費（基於 Stage 4 基準數據）
- 使用簡單幾何計算，無需 IERS/Skyfield

⚠️ 重要原則：
- 寬鬆篩選，使用安全緩衝，避免誤篩可見衛星（false negatives）
- 只排除明顯不可見的衛星（地平線以下、距離過遠）
- 精確可見性判斷仍在 Stage 4 進行

🔬 幾何判斷方法：
1. 距離檢查：衛星是否在地面站合理通訊範圍內
2. 地平線檢查：衛星是否在地球背面（粗略幾何角度）
3. 高度檢查：排除明顯過低/過高的軌道異常

✅ 符合 CRITICAL DEVELOPMENT PRINCIPLE：
- 真實幾何計算（非模擬數據）
- 使用官方 WGS84 地球半徑
- 輸入為真實 TEME 座標（來自 Skyfield SGP4）
- 僅用於優化，不影響最終精度
"""

import logging
import math
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# 官方 WGS84 參數 (SOURCE: NIMA TR8350.2)
WGS84_SEMI_MAJOR_AXIS_M = 6378137.0  # WGS84 長半軸 (m)
WGS84_FLATTENING = 1.0 / 298.257223563  # WGS84 扁率
WGS84_SEMI_MINOR_AXIS_M = WGS84_SEMI_MAJOR_AXIS_M * (1 - WGS84_FLATTENING)  # 短半軸


class GeometricPrefilter:
    """
    幾何預篩選器 - Stage 3 優化模組

    使用簡單幾何計算快速排除明顯不可見的衛星，
    減少後續精密 Skyfield 座標轉換的計算量。
    """

    def __init__(self, ground_station_lat_deg: float, ground_station_lon_deg: float,
                 ground_station_alt_m: float = 0.0):
        """
        初始化幾何預篩選器

        Args:
            ground_station_lat_deg: 地面站緯度 (度)
            ground_station_lon_deg: 地面站經度 (度)
            ground_station_alt_m: 地面站海拔高度 (米)
        """
        self.ground_station_lat_deg = ground_station_lat_deg
        self.ground_station_lon_deg = ground_station_lon_deg
        self.ground_station_alt_m = ground_station_alt_m

        # 篩選閾值（寬鬆設定，使用安全緩衝）
        # ✅ 基於基準數據：Starlink 5°, OneWeb 10° 實際閾值
        # 安全緩衝：使用 -10° 粗略仰角（確保不誤篩 5°/10° 可見衛星）
        self.min_rough_elevation_deg = -10.0  # 粗略仰角下限（寬鬆）

        # 距離閾值（LEO 衛星典型通訊範圍 + 安全緩衝）
        # 最大視距約 2,600 km (@550km軌道高度, 5°仰角)
        # 安全緩衝：使用 3,000 km
        self.max_slant_range_km = 3000.0  # 最大斜距 (km)

        # 高度合理性檢查（排除軌道異常）
        self.min_altitude_km = 200.0   # LEO 最低高度
        self.max_altitude_km = 2000.0  # LEO 最高高度（OneWeb ~1200km）

        # 計算地面站 ECEF 座標（用於快速距離計算）
        self.ground_station_ecef_km = self._wgs84_to_ecef(
            ground_station_lat_deg, ground_station_lon_deg, ground_station_alt_m
        )

        logger.info(f"🔍 幾何預篩選器初始化")
        logger.info(f"   地面站: {ground_station_lat_deg:.5f}°N, {ground_station_lon_deg:.5f}°E")
        logger.info(f"   粗略仰角閾值: {self.min_rough_elevation_deg}° (安全緩衝)")
        logger.info(f"   最大斜距: {self.max_slant_range_km} km")
        logger.info(f"   高度範圍: {self.min_altitude_km}-{self.max_altitude_km} km")

    def _wgs84_to_ecef(self, lat_deg: float, lon_deg: float, alt_m: float) -> Tuple[float, float, float]:
        """
        WGS84 大地座標轉 ECEF (地心地固座標系)

        SOURCE: WGS84 官方轉換公式

        Returns:
            (x_km, y_km, z_km) ECEF 座標 (公里)
        """
        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)

        # WGS84 橢球卯酉圈曲率半徑
        e_sq = 2 * WGS84_FLATTENING - WGS84_FLATTENING ** 2
        N = WGS84_SEMI_MAJOR_AXIS_M / math.sqrt(1 - e_sq * math.sin(lat_rad) ** 2)

        # ECEF 座標 (m)
        x_m = (N + alt_m) * math.cos(lat_rad) * math.cos(lon_rad)
        y_m = (N + alt_m) * math.cos(lat_rad) * math.sin(lon_rad)
        z_m = (N * (1 - e_sq) + alt_m) * math.sin(lat_rad)

        # 轉換為公里
        return (x_m / 1000.0, y_m / 1000.0, z_m / 1000.0)

    def _calculate_rough_elevation(self, sat_position_ecef_km: Tuple[float, float, float]) -> float:
        """
        計算粗略仰角 (基於簡單幾何，無需精密 IERS 數據)

        Args:
            sat_position_ecef_km: 衛星 ECEF 位置 (公里)

        Returns:
            粗略仰角 (度)，負值表示地平線以下
        """
        # 地面站到衛星的向量
        dx = sat_position_ecef_km[0] - self.ground_station_ecef_km[0]
        dy = sat_position_ecef_km[1] - self.ground_station_ecef_km[1]
        dz = sat_position_ecef_km[2] - self.ground_station_ecef_km[2]

        slant_range_km = math.sqrt(dx**2 + dy**2 + dz**2)

        # 地面站法向量（指向天頂）
        gs_x, gs_y, gs_z = self.ground_station_ecef_km
        gs_radius = math.sqrt(gs_x**2 + gs_y**2 + gs_z**2)

        # 單位法向量
        zenith_x = gs_x / gs_radius
        zenith_y = gs_y / gs_radius
        zenith_z = gs_z / gs_radius

        # 計算衛星方向向量與天頂向量的夾角
        dot_product = (dx * zenith_x + dy * zenith_y + dz * zenith_z)

        # 仰角 = 90° - 天頂角
        zenith_angle_rad = math.acos(dot_product / slant_range_km)
        elevation_rad = math.pi / 2 - zenith_angle_rad

        return math.degrees(elevation_rad)

    def _teme_to_rough_ecef(self, position_teme_km: List[float], datetime_utc: datetime) -> Tuple[float, float, float]:
        """
        TEME 座標粗略轉換為 ECEF (簡化版，無 IERS 數據)

        ⚠️ 注意：此為快速粗略轉換，僅用於預篩選
        精確轉換仍使用 Skyfield + IERS 數據在主流程中進行

        簡化假設：
        - 忽略極移修正（誤差 ~15m @ 地球表面）
        - 忽略章動/歲差高階項（誤差 ~50m）
        - 使用簡化 GMST 計算（誤差 ~1 角秒 ≈ 30m）

        這些誤差對於 3,000 km 距離閾值的粗略判斷影響很小（< 1%）

        Args:
            position_teme_km: TEME 位置向量 (公里)
            datetime_utc: UTC 時間

        Returns:
            粗略 ECEF 座標 (公里)
        """
        # 計算簡化 GMST (格林威治平恆星時)
        # SOURCE: Simplified GMST formula (Meeus, Astronomical Algorithms)
        jd = self._datetime_to_jd(datetime_utc)
        T = (jd - 2451545.0) / 36525.0  # Julian centuries since J2000

        # GMST at 0h UT (度)
        gmst_deg = (280.46061837 + 360.98564736629 * (jd - 2451545.0) +
                    0.000387933 * T**2 - T**3 / 38710000.0) % 360.0

        gmst_rad = math.radians(gmst_deg)

        # TEME → 粗略 ECEF (繞 Z 軸旋轉 GMST)
        cos_gmst = math.cos(gmst_rad)
        sin_gmst = math.sin(gmst_rad)

        x_ecef = position_teme_km[0] * cos_gmst + position_teme_km[1] * sin_gmst
        y_ecef = -position_teme_km[0] * sin_gmst + position_teme_km[1] * cos_gmst
        z_ecef = position_teme_km[2]

        return (x_ecef, y_ecef, z_ecef)

    def _datetime_to_jd(self, dt: datetime) -> float:
        """日期轉儒略日"""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3

        jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        jd_frac = (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0 + dt.microsecond / 86400000000.0

        return jdn + jd_frac

    def filter_satellite_candidates(self, teme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        幾何預篩選：快速排除明顯不可見的衛星

        Args:
            teme_data: TEME 座標數據 {satellite_id: {time_series: [...]}}

        Returns:
            篩選後的 TEME 數據（保留可能可見的衛星）
        """
        logger.info(f"🔍 開始幾何預篩選: {len(teme_data)} 顆衛星")

        filtered_data = {}
        stats = {
            'total_satellites': len(teme_data),
            'filtered_out': 0,
            'retained': 0,
            'rejection_reasons': {
                'altitude_too_low': 0,
                'altitude_too_high': 0,
                'distance_too_far': 0,
                'always_below_horizon': 0,
                'no_valid_points': 0
            }
        }

        for satellite_id, satellite_data in teme_data.items():
            time_series = satellite_data.get('time_series', [])

            if not time_series:
                stats['rejection_reasons']['no_valid_points'] += 1
                stats['filtered_out'] += 1
                continue

            # 檢查衛星在整個時間窗口內是否有任何可能可見的時刻
            has_potential_visibility = False
            rejection_reason = None

            for teme_point in time_series:
                position_teme_km = teme_point.get('position_teme_km', [0, 0, 0])
                timestamp_str = teme_point.get('datetime_utc') or teme_point.get('timestamp')

                if not timestamp_str:
                    continue

                try:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                    # 1. 高度檢查（快速排除異常軌道）
                    altitude_km = math.sqrt(sum(x**2 for x in position_teme_km)) - WGS84_SEMI_MAJOR_AXIS_M / 1000.0

                    if altitude_km < self.min_altitude_km:
                        rejection_reason = 'altitude_too_low'
                        continue
                    if altitude_km > self.max_altitude_km:
                        rejection_reason = 'altitude_too_high'
                        continue

                    # 2. 轉換為粗略 ECEF
                    sat_ecef_km = self._teme_to_rough_ecef(position_teme_km, dt)

                    # 3. 距離檢查
                    dx = sat_ecef_km[0] - self.ground_station_ecef_km[0]
                    dy = sat_ecef_km[1] - self.ground_station_ecef_km[1]
                    dz = sat_ecef_km[2] - self.ground_station_ecef_km[2]
                    slant_range_km = math.sqrt(dx**2 + dy**2 + dz**2)

                    if slant_range_km > self.max_slant_range_km:
                        rejection_reason = 'distance_too_far'
                        continue

                    # 4. 粗略仰角檢查
                    rough_elevation_deg = self._calculate_rough_elevation(sat_ecef_km)

                    if rough_elevation_deg < self.min_rough_elevation_deg:
                        rejection_reason = 'always_below_horizon'
                        continue

                    # ✅ 通過所有檢查，此時刻可能可見
                    has_potential_visibility = True
                    break  # 只要有一個時刻可能可見，就保留這顆衛星

                except Exception as e:
                    logger.debug(f"預篩選計算錯誤 {satellite_id}: {e}")
                    continue

            # 決定是否保留此衛星
            if has_potential_visibility:
                filtered_data[satellite_id] = satellite_data
                stats['retained'] += 1
            else:
                stats['filtered_out'] += 1
                if rejection_reason:
                    stats['rejection_reasons'][rejection_reason] += 1

        # 統計報告
        retention_rate = stats['retained'] / stats['total_satellites'] * 100 if stats['total_satellites'] > 0 else 0

        logger.info(f"✅ 幾何預篩選完成:")
        logger.info(f"   輸入: {stats['total_satellites']} 顆衛星")
        logger.info(f"   保留: {stats['retained']} 顆 ({retention_rate:.1f}%)")
        logger.info(f"   排除: {stats['filtered_out']} 顆 ({100-retention_rate:.1f}%)")
        logger.info(f"   排除原因:")
        for reason, count in stats['rejection_reasons'].items():
            if count > 0:
                logger.info(f"      {reason}: {count} 顆")

        return filtered_data


def create_geometric_prefilter(ground_station_lat_deg: float,
                                ground_station_lon_deg: float,
                                ground_station_alt_m: float = 0.0) -> GeometricPrefilter:
    """創建幾何預篩選器實例"""
    return GeometricPrefilter(ground_station_lat_deg, ground_station_lon_deg, ground_station_alt_m)
