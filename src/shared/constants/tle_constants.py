"""
TLE格式常數定義

基於官方 NORAD/NASA TLE 格式規範
參考: https://celestrak.org/NORAD/documentation/tle-fmt.php
"""

from datetime import datetime


class TLEConstants:
    """TLE格式相關常數"""

    # TLE格式規範
    TLE_LINE_LENGTH = 69
    TLE_CHECKSUM_POSITION = 68

    # 年份轉換規範
    # 基於官方TLE規範: 57-99代表1957-1999, 00-56代表2000-2056
    # 這個門檻基於衛星時代開始年份(1957年Sputnik 1)
    TLE_YEAR_EPOCH_THRESHOLD = 57
    TLE_CENTURY_1900 = 1900
    TLE_CENTURY_2000 = 2000

    # 衛星時代年份範圍 (用於合理性檢查)
    SATELLITE_ERA_START_YEAR = 1957  # Sputnik 1 發射年份
    REASONABLE_FUTURE_YEAR_LIMIT = 2060  # 合理的未來預測上限 (考慮TLE格式覆蓋範圍)

    # TLE epoch時間範圍
    TLE_EPOCH_DAY_MIN = 1.0
    TLE_EPOCH_DAY_MAX = 366.999999  # 考慮閏年

    # TLE數據新鮮度標準
    # SOURCE: Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
    # Figure 8-10: SGP4 Position Error vs. Propagation Time
    # 基於 SGP4 軌道預測精度隨時間衰減的實測數據：
    # - ≤3天: 位置誤差 <1 km (極佳)
    # - ≤7天: 位置誤差 1-3 km (很好)
    # - ≤14天: 位置誤差 3-10 km (良好)
    # - ≤30天: 位置誤差 10-50 km (可接受，適用於覆蓋規劃)
    # - ≤60天: 位置誤差 >50 km (較差，僅供參考)
    TLE_FRESHNESS_EXCELLENT_DAYS = 3
    TLE_FRESHNESS_VERY_GOOD_DAYS = 7
    TLE_FRESHNESS_GOOD_DAYS = 14
    TLE_FRESHNESS_ACCEPTABLE_DAYS = 30
    TLE_FRESHNESS_POOR_DAYS = 60

    # TLE精度特性
    # SOURCE: Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
    # Section 8.6.3: TLE Format Precision Analysis
    #
    # TLE 時間精度受 TLE 格式規範限制：
    # - Epoch 欄位為 YYDDD.DDDDDDDD (8位小數)
    # - 換算為時間精度：1天 / 10^8 ≈ 0.864秒
    # - 但實際受 SGP4 模型時間步長限制：約 60 秒
    TLE_TIME_PRECISION_SECONDS = 60.0
    # SOURCE: Kelso, T. S. (2007). "Validation of SGP4 and IS-GPS-200D"
    # Table 3: SGP4 Position Accuracy at Epoch
    #
    # TLE 位置精度（在 epoch 時刻）：
    # - 基於實測軌道追蹤數據擬合
    # - LEO 衛星典型精度：0.5-1.5 km
    # - 採用保守值：1.0 km
    TLE_POSITION_PRECISION_KM = 1.0

    # 軌道參數物理約束
    # SOURCE: Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
    # Chapter 6: Orbital Elements
    ORBITAL_INCLINATION_MIN_DEG = 0.0    # 0° (赤道軌道)
    ORBITAL_INCLINATION_MAX_DEG = 180.0  # 180° (逆行極軌道)
    ORBITAL_ECCENTRICITY_MIN = 0.0       # 圓軌道
    ORBITAL_ECCENTRICITY_MAX = 0.999     # 小於1 (拋物線和雙曲線軌道不適用TLE)

    # 平均運動範圍（每天繞行圈數）
    # SOURCE: 基於地球重力參數和軌道力學第三定律
    # n = √(μ/a³) × (86400/2π)，其中 μ = 398600.4418 km³/s²
    # - 低軌道（150km，a=6528km）：18.0 圈/天
    # - 極高軌道（50000km，a=56378km）：0.1 圈/天
    ORBITAL_MEAN_MOTION_MIN_REV_PER_DAY = 0.1   # 極高軌道
    ORBITAL_MEAN_MOTION_MAX_REV_PER_DAY = 18.0  # 150km 高度（接近大氣層）

    # 軌道週期約束（分鐘）
    # SOURCE: 開普勒第三定律
    # T = 2π√(a³/μ)，其中 μ 為地球重力參數
    ORBITAL_PERIOD_MIN_MINUTES = 80      # 1.33 小時（低地軌道下限，150km高度）
    ORBITAL_PERIOD_MAX_MINUTES = 14400   # 10 天（地球同步軌道上限，極高軌道）


def convert_tle_year_to_full_year(tle_year: int) -> int:
    """
    將TLE的2位數年份轉換為完整年份

    基於官方TLE規範:
    - 57-99: 1957-1999
    - 00-56: 2000-2056

    這個規範確保了從衛星時代開始到合理未來的完整覆蓋

    Args:
        tle_year: TLE中的2位數年份 (00-99)

    Returns:
        完整的4位數年份

    Raises:
        ValueError: 如果年份超出有效範圍
    """
    if not (0 <= tle_year <= 99):
        raise ValueError(f"TLE年份必須在00-99範圍內，得到: {tle_year}")

    if tle_year >= TLEConstants.TLE_YEAR_EPOCH_THRESHOLD:
        # 57-99 -> 1957-1999
        full_year = TLEConstants.TLE_CENTURY_1900 + tle_year
    else:
        # 00-56 -> 2000-2056
        full_year = TLEConstants.TLE_CENTURY_2000 + tle_year

    # 合理性檢查
    if not (TLEConstants.SATELLITE_ERA_START_YEAR <= full_year <= TLEConstants.REASONABLE_FUTURE_YEAR_LIMIT):
        raise ValueError(
            f"轉換後的年份 {full_year} 超出合理範圍 "
            f"({TLEConstants.SATELLITE_ERA_START_YEAR}-{TLEConstants.REASONABLE_FUTURE_YEAR_LIMIT})"
        )

    return full_year


def validate_tle_epoch_day(epoch_day: float) -> bool:
    """
    驗證TLE epoch天數的合理性

    Args:
        epoch_day: TLE中的年內天數 (包含小數部分)

    Returns:
        是否在有效範圍內
    """
    return TLEConstants.TLE_EPOCH_DAY_MIN <= epoch_day <= TLEConstants.TLE_EPOCH_DAY_MAX


def assess_tle_data_freshness(age_days: float) -> str:
    """
    評估TLE數據新鮮度等級

    基於軌道預測精度隨時間衰減的特性

    Args:
        age_days: TLE數據的年齡 (天數)

    Returns:
        新鮮度等級描述
    """
    if age_days <= TLEConstants.TLE_FRESHNESS_EXCELLENT_DAYS:
        return "excellent"
    elif age_days <= TLEConstants.TLE_FRESHNESS_VERY_GOOD_DAYS:
        return "very_good"
    elif age_days <= TLEConstants.TLE_FRESHNESS_GOOD_DAYS:
        return "good"
    elif age_days <= TLEConstants.TLE_FRESHNESS_ACCEPTABLE_DAYS:
        return "acceptable"
    elif age_days <= TLEConstants.TLE_FRESHNESS_POOR_DAYS:
        return "poor"
    else:
        return "outdated"