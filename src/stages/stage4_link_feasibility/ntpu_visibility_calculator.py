#!/usr/bin/env python3
"""
NTPU 可見性計算器 - Stage 4 核心模組

精確的 NTPU 地面站可見性分析
地面站座標: 24°56'39"N, 121°22'17"E (final.md 第8行)
"""

import math
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class NTPUVisibilityCalculator:
    """NTPU 地面站可見性計算器"""

    # 精確 NTPU 座標 (final.md 第8行)
    NTPU_COORDINATES = {
        'latitude_deg': 24.9441,    # 24°56'39"N
        'longitude_deg': 121.3714,  # 121°22'17"E
        'altitude_m': 200.0,        # 估計海拔 (NTPU 約200公尺)
        'description': 'National Taipei University of Technology'
    }

    # WGS84 橢球參數
    WGS84_PARAMETERS = {
        'semi_major_axis_m': 6378137.0,      # 長半軸 (公尺)
        'flattening': 1.0 / 298.257223563,   # 扁率
        'semi_minor_axis_m': 6356752.314245  # 短半軸 (公尺)
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 NTPU 可見性計算器"""
        self.config = config or {}
        self.logger = logger

        # 計算地球半徑
        self.earth_radius_km = self.WGS84_PARAMETERS['semi_major_axis_m'] / 1000.0

        self.logger.info("🏢 NTPU 可見性計算器初始化")
        self.logger.info(f"   地面站: {self.NTPU_COORDINATES['latitude_deg']}°N, "
                        f"{self.NTPU_COORDINATES['longitude_deg']}°E, "
                        f"{self.NTPU_COORDINATES['altitude_m']}m")

    def calculate_satellite_elevation(self, sat_lat_deg: float, sat_lon_deg: float,
                                    sat_alt_km: float, timestamp: Optional[datetime] = None) -> float:
        """計算衛星相對於 NTPU 的仰角"""
        try:
            # 地面站座標
            obs_lat = self.NTPU_COORDINATES['latitude_deg']
            obs_lon = self.NTPU_COORDINATES['longitude_deg']
            obs_alt_km = self.NTPU_COORDINATES['altitude_m'] / 1000.0

            # 轉換為弧度
            sat_lat_rad = math.radians(sat_lat_deg)
            sat_lon_rad = math.radians(sat_lon_deg)
            obs_lat_rad = math.radians(obs_lat)
            obs_lon_rad = math.radians(obs_lon)

            # 觀測者位置向量 (地心坐標)
            obs_x = (self.earth_radius_km + obs_alt_km) * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
            obs_y = (self.earth_radius_km + obs_alt_km) * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
            obs_z = (self.earth_radius_km + obs_alt_km) * math.sin(obs_lat_rad)

            # 衛星位置向量 (地心坐標)
            sat_x = (self.earth_radius_km + sat_alt_km) * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
            sat_y = (self.earth_radius_km + sat_alt_km) * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
            sat_z = (self.earth_radius_km + sat_alt_km) * math.sin(sat_lat_rad)

            # 觀測者的地心向量 (天頂方向)
            obs_vec_norm = math.sqrt(obs_x*obs_x + obs_y*obs_y + obs_z*obs_z)
            obs_unit_x = obs_x / obs_vec_norm
            obs_unit_y = obs_y / obs_vec_norm
            obs_unit_z = obs_z / obs_vec_norm

            # 衛星相對於觀測者的向量
            rel_x = sat_x - obs_x
            rel_y = sat_y - obs_y
            rel_z = sat_z - obs_z
            rel_norm = math.sqrt(rel_x*rel_x + rel_y*rel_y + rel_z*rel_z)

            if rel_norm == 0:
                return 90.0  # 衛星在地面站正上方

            # 單位向量
            rel_unit_x = rel_x / rel_norm
            rel_unit_y = rel_y / rel_norm
            rel_unit_z = rel_z / rel_norm

            # 計算仰角：觀測者天頂方向與衛星方向的點積
            dot_product = rel_unit_x * obs_unit_x + rel_unit_y * obs_unit_y + rel_unit_z * obs_unit_z
            elevation_rad = math.asin(max(-1.0, min(1.0, dot_product)))

            return math.degrees(elevation_rad)

        except Exception as e:
            self.logger.error(f"仰角計算失敗: {e}")
            return -90.0

    def calculate_satellite_distance(self, sat_lat_deg: float, sat_lon_deg: float,
                                   sat_alt_km: float) -> float:
        """計算衛星與 NTPU 地面站的距離"""
        try:
            # 地面站座標
            obs_lat = self.NTPU_COORDINATES['latitude_deg']
            obs_lon = self.NTPU_COORDINATES['longitude_deg']
            obs_alt_km = self.NTPU_COORDINATES['altitude_m'] / 1000.0

            # 轉換為弧度
            sat_lat_rad = math.radians(sat_lat_deg)
            sat_lon_rad = math.radians(sat_lon_deg)
            obs_lat_rad = math.radians(obs_lat)
            obs_lon_rad = math.radians(obs_lon)

            # 地心坐標計算
            obs_x = (self.earth_radius_km + obs_alt_km) * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
            obs_y = (self.earth_radius_km + obs_alt_km) * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
            obs_z = (self.earth_radius_km + obs_alt_km) * math.sin(obs_lat_rad)

            sat_x = (self.earth_radius_km + sat_alt_km) * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
            sat_y = (self.earth_radius_km + sat_alt_km) * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
            sat_z = (self.earth_radius_km + sat_alt_km) * math.sin(sat_lat_rad)

            # 距離計算
            dx = sat_x - obs_x
            dy = sat_y - obs_y
            dz = sat_z - obs_z

            distance_km = math.sqrt(dx*dx + dy*dy + dz*dz)
            return distance_km

        except Exception as e:
            self.logger.error(f"距離計算失敗: {e}")
            return float('inf')

    def is_satellite_visible(self, sat_lat_deg: float, sat_lon_deg: float, sat_alt_km: float,
                           min_elevation_deg: float = 5.0, timestamp: Optional[datetime] = None) -> bool:
        """判斷衛星是否可見"""
        elevation = self.calculate_satellite_elevation(sat_lat_deg, sat_lon_deg, sat_alt_km, timestamp)
        return elevation >= min_elevation_deg

    def calculate_visibility_for_trajectory(self, satellite_trajectory: List[Dict[str, Any]],
                                          min_elevation_deg: float = 5.0) -> List[Dict[str, Any]]:
        """為整個軌道軌跡計算可見性"""
        visibility_results = []

        for point in satellite_trajectory:
            try:
                # 提取座標
                lat = point.get('latitude_deg')
                lon = point.get('longitude_deg')
                alt = point.get('altitude_m', 0) / 1000.0  # 轉換為 km
                timestamp_str = point.get('timestamp', '')

                if lat is None or lon is None:
                    continue

                # 計算仰角和距離
                elevation = self.calculate_satellite_elevation(lat, lon, alt)
                distance_km = self.calculate_satellite_distance(lat, lon, alt)
                is_visible = elevation >= min_elevation_deg

                visibility_result = {
                    'timestamp': timestamp_str,
                    'latitude_deg': lat,
                    'longitude_deg': lon,
                    'altitude_km': alt,
                    'elevation_deg': elevation,
                    'distance_km': distance_km,
                    'is_visible': is_visible,
                    'min_elevation_threshold': min_elevation_deg
                }

                visibility_results.append(visibility_result)

            except Exception as e:
                self.logger.warning(f"軌跡點可見性計算失敗: {e}")
                continue

        return visibility_results

    def find_visibility_windows(self, satellite_trajectory: List[Dict[str, Any]],
                               min_elevation_deg: float = 5.0,
                               min_duration_minutes: float = 2.0) -> List[Dict[str, Any]]:
        """查找可見性時間窗口"""
        visibility_results = self.calculate_visibility_for_trajectory(
            satellite_trajectory, min_elevation_deg
        )

        windows = []
        current_window = None
        time_interval_seconds = 60  # 假設 1 分鐘間隔

        for result in visibility_results:
            if result['is_visible']:
                if current_window is None:
                    # 開始新的窗口
                    current_window = {
                        'start_time': result['timestamp'],
                        'end_time': result['timestamp'],
                        'max_elevation_deg': result['elevation_deg'],
                        'min_distance_km': result['distance_km'],
                        'points': [result]
                    }
                else:
                    # 延續當前窗口
                    current_window['end_time'] = result['timestamp']
                    current_window['max_elevation_deg'] = max(
                        current_window['max_elevation_deg'], result['elevation_deg']
                    )
                    current_window['min_distance_km'] = min(
                        current_window['min_distance_km'], result['distance_km']
                    )
                    current_window['points'].append(result)
            else:
                if current_window is not None:
                    # 結束當前窗口
                    duration_minutes = len(current_window['points']) * time_interval_seconds / 60.0
                    current_window['duration_minutes'] = duration_minutes

                    # 檢查是否滿足最小持續時間
                    if duration_minutes >= min_duration_minutes:
                        windows.append(current_window)

                    current_window = None

        # 處理最後一個窗口
        if current_window is not None:
            duration_minutes = len(current_window['points']) * time_interval_seconds / 60.0
            current_window['duration_minutes'] = duration_minutes

            if duration_minutes >= min_duration_minutes:
                windows.append(current_window)

        return windows

    def analyze_ntpu_coverage(self, satellites_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析 NTPU 地面站的整體覆蓋情況"""
        coverage_analysis = {
            'ground_station': self.NTPU_COORDINATES,
            'satellites_analysis': {},
            'coverage_summary': {
                'total_satellites': len(satellites_data),
                'visible_satellites': 0,
                'coverage_windows': [],
                'max_simultaneous_visible': 0
            }
        }

        for sat_id, sat_data in satellites_data.items():
            wgs84_coordinates = sat_data.get('wgs84_coordinates', [])
            constellation = sat_data.get('constellation', 'unknown')

            if not wgs84_coordinates:
                continue

            # 計算可見性窗口
            visibility_windows = self.find_visibility_windows(wgs84_coordinates)

            sat_analysis = {
                'constellation': constellation,
                'total_points': len(wgs84_coordinates),
                'visibility_windows': visibility_windows,
                'total_visible_time_minutes': sum(w['duration_minutes'] for w in visibility_windows),
                'max_elevation_deg': max((w['max_elevation_deg'] for w in visibility_windows), default=0)
            }

            coverage_analysis['satellites_analysis'][sat_id] = sat_analysis

            # 更新總覆蓋統計
            if visibility_windows:
                coverage_analysis['coverage_summary']['visible_satellites'] += 1

        self.logger.info(f"📊 NTPU 覆蓋分析: {coverage_analysis['coverage_summary']['visible_satellites']}/{coverage_analysis['coverage_summary']['total_satellites']} 顆衛星可見")

        return coverage_analysis


def create_ntpu_visibility_calculator(config: Optional[Dict[str, Any]] = None) -> NTPUVisibilityCalculator:
    """創建 NTPU 可見性計算器實例"""
    return NTPUVisibilityCalculator(config)


if __name__ == "__main__":
    # 測試 NTPU 可見性計算器
    calculator = create_ntpu_visibility_calculator()

    # 測試仰角計算
    print("🧪 測試 NTPU 仰角計算:")

    # 測試案例：台北上空的衛星
    test_elevation = calculator.calculate_satellite_elevation(
        sat_lat_deg=25.0, sat_lon_deg=121.5, sat_alt_km=550.0
    )
    print(f"台北上空 550km 衛星仰角: {test_elevation:.1f}°")

    # 測試距離計算
    test_distance = calculator.calculate_satellite_distance(
        sat_lat_deg=25.0, sat_lon_deg=121.5, sat_alt_km=550.0
    )
    print(f"台北上空 550km 衛星距離: {test_distance:.1f} km")

    print("✅ NTPU 可見性計算器測試完成")