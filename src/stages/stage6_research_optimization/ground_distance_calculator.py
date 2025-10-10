#!/usr/bin/env python3
"""
地面大圆距离计算模块

用途: 计算地球表面两点之间的距离（大圆距离）
适用于: D2 事件地面距离测量（UE 到卫星地面投影点）

学术依据:
- Haversine 公式: Sinnott, R.W. (1984). "Virtues of the Haversine"
  Sky & Telescope, 68(2), 159
- Vincenty 公式: Vincenty, T. (1975). "Direct and inverse solutions of geodesics on the ellipsoid"
  Survey Review, 23(176), 88-93

符合: docs/ACADEMIC_STANDARDS.md Grade A 标准
创建日期: 2025-10-10
"""

import math
from typing import Tuple


class GroundDistanceCalculator:
    """
    地面大圆距离计算器

    提供两种精度级别：
    1. Haversine 公式：快速，精度 ~0.5% (适用于大多数场景)
    2. Vincenty 公式：高精度，精度 ~0.5mm (适用于高精度需求)
    """

    def __init__(self):
        """
        初始化计算器

        地球半径来源:
        - SOURCE: IUGG (International Union of Geodesy and Geophysics)
          Mean radius: R = (2a + b)/3 = 6371008.8 m
          其中 a = 6378137.0 m (WGS84 长半轴)
               b = 6356752.3 m (WGS84 短半轴)
        """
        # 地球平均半径 (m) - SOURCE: IUGG
        self.R_mean = 6371008.8

        # WGS84 椭球参数（用于 Vincenty 公式）
        # SOURCE: NIMA TR8350.2 (2000)
        self.a = 6378137.0  # 长半轴 (m)
        self.f = 1.0 / 298.257223563  # 扁率
        self.b = self.a * (1 - self.f)  # 短半轴 (m)

    def haversine_distance(
        self,
        lat1_deg: float,
        lon1_deg: float,
        lat2_deg: float,
        lon2_deg: float
    ) -> float:
        """
        Haversine 公式计算大圆距离

        算法: R.W. Sinnott (1984) "Virtues of the Haversine"
        - 精度: ~0.5% (对于地球尺度的距离)
        - 速度: 快速（无迭代）
        - 适用: 大多数 LEO 卫星距离计算

        SOURCE:
        Sinnott, R.W. (1984). "Virtues of the Haversine"
        Sky & Telescope, 68(2), 159

        公式:
        a = sin²(Δφ/2) + cos(φ₁) * cos(φ₂) * sin²(Δλ/2)
        c = 2 * atan2(√a, √(1−a))
        d = R * c

        Args:
            lat1_deg, lon1_deg: 第一点大地坐标 (度)
            lat2_deg, lon2_deg: 第二点大地坐标 (度)

        Returns:
            distance_m: 地面大圆距离 (米)
        """
        # 转换为弧度
        lat1_rad = math.radians(lat1_deg)
        lon1_rad = math.radians(lon1_deg)
        lat2_rad = math.radians(lat2_deg)
        lon2_rad = math.radians(lon2_deg)

        # 差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine 公式
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # 距离（米）
        distance_m = self.R_mean * c

        return distance_m

    def vincenty_distance(
        self,
        lat1_deg: float,
        lon1_deg: float,
        lat2_deg: float,
        lon2_deg: float,
        max_iterations: int = 200,
        tolerance: float = 1e-12
    ) -> float:
        """
        Vincenty 公式计算椭球距离（高精度）

        算法: T. Vincenty (1975) 迭代解法
        - 精度: ~0.5mm
        - 速度: 较慢（需要迭代）
        - 适用: 高精度需求（如学术发表）

        SOURCE:
        Vincenty, T. (1975). "Direct and inverse solutions of geodesics on the ellipsoid
        with application of nested equations"
        Survey Review, 23(176), 88-93

        Args:
            lat1_deg, lon1_deg: 第一点大地坐标 (度)
            lat2_deg, lon2_deg: 第二点大地坐标 (度)
            max_iterations: 最大迭代次数（默认 200）
            tolerance: 收敛容差（默认 1e-12）

        Returns:
            distance_m: 椭球大地线距离 (米)

        Raises:
            ValueError: 如果迭代不收敛（极少发生）
        """
        # 转换为弧度
        lat1_rad = math.radians(lat1_deg)
        lon1_rad = math.radians(lon1_deg)
        lat2_rad = math.radians(lat2_deg)
        lon2_rad = math.radians(lon2_deg)

        # 简化处理：如果两点重合
        if abs(lat1_deg - lat2_deg) < 1e-10 and abs(lon1_deg - lon2_deg) < 1e-10:
            return 0.0

        # Vincenty 公式参数
        L = lon2_rad - lon1_rad
        U1 = math.atan((1 - self.f) * math.tan(lat1_rad))
        U2 = math.atan((1 - self.f) * math.tan(lat2_rad))

        sin_U1 = math.sin(U1)
        cos_U1 = math.cos(U1)
        sin_U2 = math.sin(U2)
        cos_U2 = math.cos(U2)

        # 迭代求解
        lambda_rad = L
        for _ in range(max_iterations):
            sin_lambda = math.sin(lambda_rad)
            cos_lambda = math.cos(lambda_rad)

            sin_sigma = math.sqrt(
                (cos_U2 * sin_lambda) ** 2
                + (cos_U1 * sin_U2 - sin_U1 * cos_U2 * cos_lambda) ** 2
            )

            if sin_sigma == 0:
                return 0.0  # 重合点

            cos_sigma = sin_U1 * sin_U2 + cos_U1 * cos_U2 * cos_lambda
            sigma = math.atan2(sin_sigma, cos_sigma)

            sin_alpha = cos_U1 * cos_U2 * sin_lambda / sin_sigma
            cos_sq_alpha = 1 - sin_alpha ** 2

            if cos_sq_alpha == 0:
                cos_2sigma_m = 0
            else:
                cos_2sigma_m = cos_sigma - 2 * sin_U1 * sin_U2 / cos_sq_alpha

            C = self.f / 16 * cos_sq_alpha * (4 + self.f * (4 - 3 * cos_sq_alpha))

            lambda_prev = lambda_rad
            lambda_rad = L + (1 - C) * self.f * sin_alpha * (
                sigma
                + C * sin_sigma * (cos_2sigma_m + C * cos_sigma * (-1 + 2 * cos_2sigma_m ** 2))
            )

            # 检查收敛
            if abs(lambda_rad - lambda_prev) < tolerance:
                break
        else:
            raise ValueError(
                f"Vincenty formula failed to converge after {max_iterations} iterations\n"
                f"Points: ({lat1_deg}, {lon1_deg}) to ({lat2_deg}, {lon2_deg})"
            )

        # 计算距离
        u_sq = cos_sq_alpha * (self.a ** 2 - self.b ** 2) / (self.b ** 2)
        A = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
        B = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

        delta_sigma = (
            B
            * sin_sigma
            * (
                cos_2sigma_m
                + B
                / 4
                * (
                    cos_sigma * (-1 + 2 * cos_2sigma_m ** 2)
                    - B / 6 * cos_2sigma_m * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos_2sigma_m ** 2)
                )
            )
        )

        distance_m = self.b * A * (sigma - delta_sigma)

        return distance_m


# 创建全局实例（避免重复初始化）
_calculator = GroundDistanceCalculator()


def haversine_distance(
    lat1_deg: float, lon1_deg: float, lat2_deg: float, lon2_deg: float
) -> float:
    """
    Haversine 大圆距离计算（便捷函数）

    Args:
        lat1_deg, lon1_deg: 第一点 (度)
        lat2_deg, lon2_deg: 第二点 (度)

    Returns:
        distance_m: 距离 (米)
    """
    return _calculator.haversine_distance(lat1_deg, lon1_deg, lat2_deg, lon2_deg)


def vincenty_distance(
    lat1_deg: float, lon1_deg: float, lat2_deg: float, lon2_deg: float
) -> float:
    """
    Vincenty 椭球距离计算（便捷函数，高精度）

    Args:
        lat1_deg, lon1_deg: 第一点 (度)
        lat2_deg, lon2_deg: 第二点 (度)

    Returns:
        distance_m: 距离 (米)
    """
    return _calculator.vincenty_distance(lat1_deg, lon1_deg, lat2_deg, lon2_deg)


if __name__ == "__main__":
    # 测试用例
    print("🧪 测试地面距离计算")
    print("=" * 60)

    # 测试 1: 赤道 1 度距离
    print("\n测试 1: 赤道 1 度")
    d_haversine = haversine_distance(0, 0, 0, 1)
    d_vincenty = vincenty_distance(0, 0, 0, 1)
    print(f"  Haversine: {d_haversine:.3f} m")
    print(f"  Vincenty:  {d_vincenty:.3f} m")
    print(f"  理论值: ~111,319.5 m (赤道 1 度)")
    print(f"  误差: Haversine {abs(d_haversine-111319.5):.1f}m, Vincenty {abs(d_vincenty-111319.5):.1f}m")

    # 测试 2: NTPU 到台北 101
    print("\n测试 2: NTPU 到台北 101")
    ntpu_lat, ntpu_lon = 24.94388888, 121.37083333
    taipei101_lat, taipei101_lon = 25.0340, 121.5645
    d_haversine = haversine_distance(ntpu_lat, ntpu_lon, taipei101_lat, taipei101_lon)
    d_vincenty = vincenty_distance(ntpu_lat, ntpu_lon, taipei101_lat, taipei101_lon)
    print(f"  Haversine: {d_haversine:.3f} m ({d_haversine/1000:.2f} km)")
    print(f"  Vincenty:  {d_vincenty:.3f} m ({d_vincenty/1000:.2f} km)")
    print(f"  差异: {abs(d_haversine-d_vincenty):.3f} m")

    # 测试 3: NTPU 到 Starlink 卫星地面投影点
    print("\n测试 3: NTPU 到 Starlink 地面投影点")
    sat_lat, sat_lon = 25.0, 121.5  # 假设卫星在附近
    d_haversine = haversine_distance(ntpu_lat, ntpu_lon, sat_lat, sat_lon)
    d_vincenty = vincenty_distance(ntpu_lat, ntpu_lon, sat_lat, sat_lon)
    print(f"  Haversine: {d_haversine:.3f} m ({d_haversine/1000:.2f} km)")
    print(f"  Vincenty:  {d_vincenty:.3f} m ({d_vincenty/1000:.2f} km)")
    print(f"  差异: {abs(d_haversine-d_vincenty):.3f} m")

    # 测试 4: 长距离（台北到东京）
    print("\n测试 4: 台北到东京")
    tokyo_lat, tokyo_lon = 35.6762, 139.6503
    d_haversine = haversine_distance(ntpu_lat, ntpu_lon, tokyo_lat, tokyo_lon)
    d_vincenty = vincenty_distance(ntpu_lat, ntpu_lon, tokyo_lat, tokyo_lon)
    print(f"  Haversine: {d_haversine:.3f} m ({d_haversine/1000:.2f} km)")
    print(f"  Vincenty:  {d_vincenty:.3f} m ({d_vincenty/1000:.2f} km)")
    print(f"  差异: {abs(d_haversine-d_vincenty):.3f} m")
    print(f"  相对误差: {abs(d_haversine-d_vincenty)/d_vincenty*100:.4f}%")

    print("\n✅ 地面距离计算测试完成")
    print("\n💡 建议:")
    print("  - D2 事件使用 Haversine（速度快，精度足够）")
    print("  - 学术发表可选 Vincenty（精度更高）")
