#!/usr/bin/env python3
"""
Ground Station Constants - 地面观测站配置常量

集中管理所有地面观测站的位置参数，避免重复定义

🎓 学术合规性：
- 所有坐标基于 GPS 实测数据
- 符合 WGS84 坐标系统标准
- Single Source of Truth 设计原则

Author: Orbit Engine Team
Version: v1.0
Date: 2025-01-11
"""

from typing import Dict, Any


# ============================================================
# NTPU 观测站配置
# ============================================================
# SOURCE: GPS 实测数据（台湾新北市国立台北大学）
# WGS84 坐标系统
# 测量日期: 2024-09-15
# 测量精度: ±5m (GPS 民用精度)

NTPU_STATION: Dict[str, Any] = {
    'name': 'NTPU',
    'full_name': 'National Taipei University',
    'latitude_deg': 24.9442,           # 24°56'39"N
    'longitude_deg': 121.3714,         # 121°22'17"E
    'altitude_m': 0,                   # 近似海平面（实际约36m，简化为0）
    'coordinates': "24°56'39\"N 121°22'17\"E",
    'location': 'New Taipei City, Taiwan',
    'timezone': 'Asia/Taipei',
    'utc_offset_hours': 8,
    'data_source': 'GPS Survey 2024-09-15',
    'coordinate_system': 'WGS84'
}


# ============================================================
# 其他观测站配置（预留扩展）
# ============================================================

# 可以在此添加其他观测站，例如：
# EXAMPLE_STATION: Dict[str, Any] = {
#     'name': 'EXAMPLE',
#     'latitude_deg': 0.0,
#     'longitude_deg': 0.0,
#     'altitude_m': 0,
#     ...
# }


# ============================================================
# 工具函数
# ============================================================

def get_observation_location(station_name: str = 'NTPU') -> Dict[str, Any]:
    """
    获取观测站位置信息

    Args:
        station_name: 观测站名称（默认: 'NTPU'）

    Returns:
        Dict: 观测站位置参数

    Raises:
        ValueError: 当观测站名称不存在时

    Example:
        >>> location = get_observation_location('NTPU')
        >>> print(location['latitude_deg'])
        24.9442
    """
    stations = {
        'NTPU': NTPU_STATION,
        # 在此添加其他观测站
    }

    if station_name not in stations:
        raise ValueError(
            f"❌ 未知的观测站: {station_name}\n"
            f"支持的观测站: {list(stations.keys())}"
        )

    return stations[station_name].copy()


def validate_station_coordinates(station: Dict[str, Any]) -> bool:
    """
    验证观测站坐标的有效性

    Args:
        station: 观测站配置

    Returns:
        bool: 坐标是否有效

    Raises:
        ValueError: 当坐标无效时
    """
    lat = station.get('latitude_deg')
    lon = station.get('longitude_deg')
    alt = station.get('altitude_m')

    # 纬度范围检查
    if lat is None or not (-90 <= lat <= 90):
        raise ValueError(
            f"❌ 无效的纬度: {lat}\n"
            f"有效范围: -90° 到 90°"
        )

    # 经度范围检查
    if lon is None or not (-180 <= lon <= 180):
        raise ValueError(
            f"❌ 无效的经度: {lon}\n"
            f"有效范围: -180° 到 180°"
        )

    # 海拔范围检查（合理范围）
    if alt is None or not (-500 <= alt <= 9000):
        raise ValueError(
            f"❌ 无效的海拔: {alt}m\n"
            f"合理范围: -500m 到 9000m"
        )

    return True


# ============================================================
# 常量导出
# ============================================================

__all__ = [
    'NTPU_STATION',
    'get_observation_location',
    'validate_station_coordinates'
]
