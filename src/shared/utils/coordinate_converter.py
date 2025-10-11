#!/usr/bin/env python3
"""
ECEF → WGS84 Geodetic 坐标转换模块

用途: 将地心地固坐标系（ECEF）转换为 WGS84 大地坐标系
适用于: D2 事件地面距离计算（需要卫星地面投影点）

学术依据:
- WGS84 椭球参数: NIMA TR8350.2 (2000)
- 转换算法: Bowring, B. R. (1985). "The accuracy of geodetic latitude and height equations"
  Survey Review, 28(218), 202-206.

符合: docs/ACADEMIC_STANDARDS.md Grade A 标准
创建日期: 2025-10-10
"""

import math
from typing import Tuple


class CoordinateConverter:
    """
    ECEF ↔ WGS84 Geodetic 坐标转换器

    使用 Bowring (1985) 快速迭代法，精度优于 1e-6 度
    """

    def __init__(self):
        """
        初始化转换器

        WGS84 椭球参数来源:
        - SOURCE: NIMA TR8350.2 (2000) "Department of Defense World Geodetic System 1984"
          https://earth-info.nga.mil/php/download.php?file=coord-wgs84
        """
        # WGS84 椭球参数 - SOURCE: NIMA TR8350.2 Table 3.1
        self.a = 6378137.0  # 长半轴 (m)
        self.f = 1.0 / 298.257223563  # 扁率 1/f
        self.b = self.a * (1 - self.f)  # 短半轴 (m) = 6356752.314245

        # 第一偏心率平方
        self.e_sq = 2 * self.f - self.f ** 2  # e² = 2f - f²

        # 第二偏心率平方
        self.ep_sq = self.e_sq / (1 - self.e_sq)  # e'² = e²/(1-e²)

    def ecef_to_geodetic(self, x_m: float, y_m: float, z_m: float) -> Tuple[float, float, float]:
        """
        ECEF → WGS84 Geodetic 坐标转换

        算法: Bowring (1985) 快速迭代法
        - 精度: < 1e-6 度，< 0.1 m
        - 迭代次数: 通常 2-3 次收敛

        SOURCE:
        Bowring, B. R. (1985). "The accuracy of geodetic latitude and height equations"
        Survey Review, 28(218), 202-206.

        Args:
            x_m: ECEF X 坐标 (米)
            y_m: ECEF Y 坐标 (米)
            z_m: ECEF Z 坐标 (米)

        Returns:
            (latitude_deg, longitude_deg, altitude_m):
                - latitude_deg: 大地纬度 (度，-90 ~ +90)
                - longitude_deg: 大地经度 (度，-180 ~ +180)
                - altitude_m: 椭球高度 (米)

        Raises:
            ValueError: 如果输入坐标非法（如全为零）
        """
        # 验证输入
        r = math.sqrt(x_m**2 + y_m**2 + z_m**2)
        if r < 1.0:
            raise ValueError(
                f"ECEF 坐标过小 (r={r:.3f}m)，可能是无效输入\n"
                f"请检查坐标单位是否为米"
            )

        # Step 1: 计算经度 (直接计算，无需迭代)
        lon_rad = math.atan2(y_m, x_m)
        lon_deg = math.degrees(lon_rad)

        # Step 2: 计算纬度和高度（Bowring 迭代法）
        p = math.sqrt(x_m**2 + y_m**2)  # 距 Z 轴的距离

        # 初始猜测纬度（使用简化公式）
        lat_rad = math.atan2(z_m, p * (1 - self.e_sq))

        # Bowring 迭代（通常 2-3 次收敛）
        for _ in range(5):  # 最多 5 次迭代
            sin_lat = math.sin(lat_rad)
            cos_lat = math.cos(lat_rad)

            # 卯酉圈曲率半径
            N = self.a / math.sqrt(1 - self.e_sq * sin_lat**2)

            # 新的高度估计
            h_m = p / cos_lat - N

            # 新的纬度估计
            lat_rad_new = math.atan2(z_m, p * (1 - self.e_sq * N / (N + h_m)))

            # 检查收敛（< 1e-9 弧度 ≈ 5e-8 度）
            if abs(lat_rad_new - lat_rad) < 1e-9:
                lat_rad = lat_rad_new
                break

            lat_rad = lat_rad_new

        lat_deg = math.degrees(lat_rad)

        # 最终高度计算
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        N = self.a / math.sqrt(1 - self.e_sq * sin_lat**2)

        if abs(cos_lat) > 1e-10:
            h_m = p / cos_lat - N
        else:
            h_m = abs(z_m) - self.b  # 极点情况

        return lat_deg, lon_deg, h_m

    def geodetic_to_ecef(self, lat_deg: float, lon_deg: float, alt_m: float) -> Tuple[float, float, float]:
        """
        WGS84 Geodetic → ECEF 坐标转换（反向转换）

        SOURCE: NIMA TR8350.2 (2000) Section 4.3

        Args:
            lat_deg: 大地纬度 (度)
            lon_deg: 大地经度 (度)
            alt_m: 椭球高度 (米)

        Returns:
            (x_m, y_m, z_m): ECEF 坐标 (米)
        """
        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)

        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)

        # 卯酉圈曲率半径
        N = self.a / math.sqrt(1 - self.e_sq * sin_lat**2)

        # ECEF 坐标
        x_m = (N + alt_m) * cos_lat * cos_lon
        y_m = (N + alt_m) * cos_lat * sin_lon
        z_m = (N * (1 - self.e_sq) + alt_m) * sin_lat

        return x_m, y_m, z_m


# 创建全局实例（避免重复初始化）
_converter = CoordinateConverter()


def ecef_to_geodetic(x_m: float, y_m: float, z_m: float) -> Tuple[float, float, float]:
    """
    ECEF → WGS84 Geodetic 坐标转换（便捷函数）

    Args:
        x_m, y_m, z_m: ECEF 坐标 (米)

    Returns:
        (lat_deg, lon_deg, alt_m): 大地坐标 (度, 度, 米)
    """
    return _converter.ecef_to_geodetic(x_m, y_m, z_m)


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> Tuple[float, float, float]:
    """
    WGS84 Geodetic → ECEF 坐标转换（便捷函数）

    Args:
        lat_deg, lon_deg: 大地坐标 (度)
        alt_m: 椭球高度 (米)

    Returns:
        (x_m, y_m, z_m): ECEF 坐标 (米)
    """
    return _converter.geodetic_to_ecef(lat_deg, lon_deg, alt_m)


if __name__ == "__main__":
    # 测试用例
    print("🧪 测试 ECEF ↔ Geodetic 坐标转换")
    print("=" * 60)

    # 测试 1: 赤道（lat=0, lon=0, h=0）
    print("\n测试 1: 赤道点")
    x, y, z = geodetic_to_ecef(0.0, 0.0, 0.0)
    print(f"  Geodetic → ECEF: ({x:.3f}, {y:.3f}, {z:.3f})")
    lat, lon, h = ecef_to_geodetic(x, y, z)
    print(f"  ECEF → Geodetic: ({lat:.6f}°, {lon:.6f}°, {h:.3f}m)")

    # 测试 2: NTPU 地面站
    print("\n测试 2: NTPU 地面站")
    ntpu_lat, ntpu_lon, ntpu_alt = 24.94388888, 121.37083333, 36.0
    x, y, z = geodetic_to_ecef(ntpu_lat, ntpu_lon, ntpu_alt)
    print(f"  Geodetic → ECEF: ({x:.3f}, {y:.3f}, {z:.3f})")
    lat, lon, h = ecef_to_geodetic(x, y, z)
    print(f"  ECEF → Geodetic: ({lat:.6f}°, {lon:.6f}°, {h:.3f}m)")
    print(f"  误差: Δlat={abs(lat-ntpu_lat)*3600:.3e}″, Δlon={abs(lon-ntpu_lon)*3600:.3e}″, Δh={abs(h-ntpu_alt):.3e}m")

    # 测试 3: Starlink 卫星（550km 轨道高度）
    print("\n测试 3: Starlink 卫星")
    sat_lat, sat_lon, sat_alt = 25.0, 121.5, 550000.0
    x, y, z = geodetic_to_ecef(sat_lat, sat_lon, sat_alt)
    print(f"  Geodetic → ECEF: ({x:.3f}, {y:.3f}, {z:.3f})")
    lat, lon, h = ecef_to_geodetic(x, y, z)
    print(f"  ECEF → Geodetic: ({lat:.6f}°, {lon:.6f}°, {h:.3f}m)")
    print(f"  误差: Δlat={abs(lat-sat_lat)*3600:.3e}″, Δlon={abs(lon-sat_lon)*3600:.3e}″, Δh={abs(h-sat_alt):.3e}m")

    print("\n✅ 坐标转换测试完成")
