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

    # TLE數據新鮮度標準 (基於軌道預測精度衰減)
    TLE_FRESHNESS_EXCELLENT_DAYS = 3    # 極佳: ≤3天
    TLE_FRESHNESS_VERY_GOOD_DAYS = 7    # 很好: ≤7天
    TLE_FRESHNESS_GOOD_DAYS = 14        # 良好: ≤14天
    TLE_FRESHNESS_ACCEPTABLE_DAYS = 30  # 可接受: ≤30天
    TLE_FRESHNESS_POOR_DAYS = 60        # 較差: ≤60天

    # TLE精度特性 (基於軌道力學和觀測限制)
    # TLE的實際精度受以下因素限制:
    # 1. 軌道預測模型 (SGP4/SDP4) 的固有誤差
    # 2. 大氣阻力變化的不可預測性
    # 3. 太陽輻射壓力的變化
    # 4. 地球重力場模型的精度限制
    TLE_REALISTIC_TIME_PRECISION_SECONDS = 60.0  # 實際時間精度約1分鐘
    TLE_REALISTIC_POSITION_PRECISION_KM = 1.0    # 實際位置精度約1公里

    # 軌道參數物理約束
    ORBITAL_INCLINATION_MIN_DEG = 0.0
    ORBITAL_INCLINATION_MAX_DEG = 180.0
    ORBITAL_ECCENTRICITY_MIN = 0.0
    ORBITAL_ECCENTRICITY_MAX = 0.999  # 小於1 (拋物線和雙曲線軌道不適用TLE)
    ORBITAL_MEAN_MOTION_MIN_REV_PER_DAY = 0.1   # 最低軌道 (極高軌道)
    ORBITAL_MEAN_MOTION_MAX_REV_PER_DAY = 18.0  # 最高軌道 (約150km高度)

    # 軌道週期約束 (分鐘)
    ORBITAL_PERIOD_MIN_MINUTES = 80     # 約1.3小時 (低地軌道下限)
    ORBITAL_PERIOD_MAX_MINUTES = 14400  # 約10天 (地球同步軌道上限)


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