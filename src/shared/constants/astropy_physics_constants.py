#!/usr/bin/env python3
"""
Astropy 物理常數適配器

整合 Astropy 官方物理常數 (CODATA 2018/2022)
替代自定義物理常數，確保學術標準合規

學術優勢:
- ✅ Astropy 自動追蹤 CODATA 更新 (2018 → 2022)
- ✅ 單位自動轉換，減少人為錯誤
- ✅ 學術界標準，論文審稿認可
- ✅ 持續維護，無需手動更新常數值

參考文獻:
- Astropy Collaboration (2024): "Astropy: A community Python package for astronomy"
- CODATA 2018/2022: "Recommended values of the fundamental physical constants"
"""

import logging
from dataclasses import dataclass
from typing import Optional

try:
    from astropy import constants as const
    from astropy import units as u
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False
    logging.warning("Astropy 未安裝，使用 CODATA 2018 備用常數")

logger = logging.getLogger(__name__)


@dataclass
class AstropyPhysicsConstants:
    """
    Astropy 物理常數適配器 (CODATA 2018/2022)

    提供與 PhysicsConstants 相同的接口，但使用 Astropy 官方常數
    """

    def __post_init__(self):
        """初始化並記錄 CODATA 版本"""
        if ASTROPY_AVAILABLE:
            # Astropy 7.0+ 使用 CODATA 2022
            codata_version = "CODATA 2022" if hasattr(const, 'codata2022') else "CODATA 2018"
            logger.info(f"✅ Astropy 物理常數已載入 ({codata_version})")
        else:
            logger.warning("⚠️ Astropy 不可用，使用 CODATA 2018 備用值")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 基礎物理常數 (CODATA)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def SPEED_OF_LIGHT(self) -> float:
        """
        光速 (m/s) - 精確定義值

        SOURCE: CODATA 2018/2022
        """
        if ASTROPY_AVAILABLE:
            return float(const.c.value)  # 299792458.0 m/s (exact)
        else:
            return 299792458.0  # CODATA 2018 備用值

    @property
    def BOLTZMANN_CONSTANT(self) -> float:
        """
        玻爾茲曼常數 (J/K)

        SOURCE: CODATA 2019 重新定義
        """
        if ASTROPY_AVAILABLE:
            return float(const.k_B.value)  # 1.380649e-23 J/K (exact since 2019)
        else:
            return 1.380649e-23

    @property
    def PLANCK_CONSTANT(self) -> float:
        """
        普朗克常數 (J·s)

        SOURCE: CODATA 2019 重新定義
        """
        if ASTROPY_AVAILABLE:
            return float(const.h.value)  # 6.62607015e-34 J·s (exact since 2019)
        else:
            return 6.62607015e-34

    @property
    def GRAVITATIONAL_CONSTANT(self) -> float:
        """
        重力常數 (m³ kg⁻¹ s⁻²)

        SOURCE: CODATA 2018/2022
        """
        if ASTROPY_AVAILABLE:
            return float(const.G.value)  # 6.6743e-11 m³ kg⁻¹ s⁻²
        else:
            return 6.6743e-11

    @property
    def ELECTRON_MASS(self) -> float:
        """
        電子質量 (kg)

        SOURCE: CODATA 2018/2022
        """
        if ASTROPY_AVAILABLE:
            return float(const.m_e.value)  # 9.1093837015e-31 kg
        else:
            return 9.1093837015e-31

    @property
    def PROTON_MASS(self) -> float:
        """
        質子質量 (kg)

        SOURCE: CODATA 2018/2022
        """
        if ASTROPY_AVAILABLE:
            return float(const.m_p.value)  # 1.67262192369e-27 kg
        else:
            return 1.67262192369e-27

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 地球相關常數
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def EARTH_RADIUS(self) -> float:
        """
        地球平均半徑 (m)

        SOURCE: Astropy Earth constants
        """
        if ASTROPY_AVAILABLE:
            return float(const.R_earth.value)  # 6378100.0 m (WGS84 equatorial)
        else:
            return 6371000.0  # 平均半徑備用值

    @property
    def EARTH_MASS(self) -> float:
        """
        地球質量 (kg)

        SOURCE: Astropy Earth constants
        """
        if ASTROPY_AVAILABLE:
            return float(const.M_earth.value)  # 5.972168e24 kg
        else:
            return 5.972168e24

    @property
    def EARTH_GM(self) -> float:
        """
        地球重力參數 GM (m³/s²)

        SOURCE: WGS84/EGM96
        """
        if ASTROPY_AVAILABLE:
            return float(const.GM_earth.value)  # 3.986004418e14 m³/s²
        else:
            return 3.986004418e14

    @property
    def EARTH_J2(self) -> float:
        """
        地球 J2 攝動項 (無量綱)

        SOURCE: EGM96 重力場模型

        Note: Astropy 不直接提供 J2，使用 WGS84 標準值
        """
        return 1.08262668e-3  # WGS84 標準

    @property
    def EARTH_ROTATION_RATE(self) -> float:
        """
        地球自轉角速度 (rad/s)

        SOURCE: IAU 2009 標準
        """
        # ω_earth = 2π / (23h 56m 4.0916s sidereal day)
        sidereal_day_seconds = 86164.0916  # IAU 標準恆星日
        return 2.0 * 3.141592653589793 / sidereal_day_seconds  # 7.2921159e-5 rad/s

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 天文常數
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def ASTRONOMICAL_UNIT(self) -> float:
        """
        天文單位 AU (m)

        SOURCE: IAU 2012 精確定義
        """
        if ASTROPY_AVAILABLE:
            return float(const.au.value)  # 1.495978707e11 m (exact)
        else:
            return 1.495978707e11

    @property
    def SOLAR_MASS(self) -> float:
        """
        太陽質量 (kg)

        SOURCE: Astropy solar constants
        """
        if ASTROPY_AVAILABLE:
            return float(const.M_sun.value)  # 1.988409e30 kg
        else:
            return 1.988409e30

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 電磁頻譜常數
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def KU_BAND_FREQUENCY(self) -> float:
        """Ku 波段中心頻率 (Hz)"""
        return 12.0e9  # 12 GHz

    @property
    def KA_BAND_FREQUENCY(self) -> float:
        """Ka 波段中心頻率 (Hz)"""
        return 30.0e9  # 30 GHz

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 熱雜訊參數 (ITU-R P.372-13)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def THERMAL_NOISE_FLOOR_DBM_HZ(self) -> float:
        """
        標準熱雜訊底線 (dBm/Hz)

        SOURCE: ITU-R P.372-13
        計算: N₀ = k_B × T₀ = 1.380649e-23 × 290 = -174 dBm/Hz
        """
        return -174.0  # dBm/Hz at T=290K

    @property
    def SYSTEM_NOISE_TEMPERATURE(self) -> float:
        """
        標準系統雜訊溫度 (K)

        SOURCE: ITU-R P.372-13, ISO 554:1976
        """
        return 290.0  # K (17°C, 標準室溫)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3GPP NTN 標準參數
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def NTN_MIN_ELEVATION(self) -> float:
        """3GPP NTN 最小仰角 (degrees)"""
        return 5.0

    @property
    def NTN_HANDOVER_THRESHOLD(self) -> float:
        """3GPP NTN 換手仰角閾值 (degrees)"""
        return 10.0

    @property
    def NTN_RSRP_MIN(self) -> float:
        """3GPP NTN 最小 RSRP 閾值 (dBm)"""
        return -140.0

    @property
    def NTN_RSRP_MAX(self) -> float:
        """3GPP NTN 最大 RSRP 閾值 (dBm)"""
        return -44.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SGP4 軌道計算常數
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def SGP4_XKE(self) -> float:
        """SGP4 單位轉換常數"""
        return 7.43669161e-2

    @property
    def SGP4_QOMS2T(self) -> float:
        """SGP4 (QOMS)^(2/3) 常數"""
        return 1.88027916e-9

    @property
    def SGP4_S(self) -> float:
        """SGP4 S 常數"""
        return 1.01222928

    def get_metadata(self) -> dict:
        """
        獲取常數來源元數據

        Returns:
            metadata: 包含 CODATA 版本、Astropy 版本等資訊
        """
        metadata = {
            'astropy_available': ASTROPY_AVAILABLE,
            'source': 'Astropy Constants' if ASTROPY_AVAILABLE else 'CODATA 2018 Fallback'
        }

        if ASTROPY_AVAILABLE:
            import astropy
            metadata['astropy_version'] = astropy.__version__
            metadata['codata_version'] = 'CODATA 2022' if hasattr(const, 'codata2022') else 'CODATA 2018'

        return metadata


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 全局實例與便捷訪問
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 創建全局實例
_astropy_constants = AstropyPhysicsConstants()

# 便捷訪問 (與原 PhysicsConstants 兼容)
SPEED_OF_LIGHT = _astropy_constants.SPEED_OF_LIGHT
BOLTZMANN_CONSTANT = _astropy_constants.BOLTZMANN_CONSTANT
PLANCK_CONSTANT = _astropy_constants.PLANCK_CONSTANT
EARTH_RADIUS = _astropy_constants.EARTH_RADIUS
EARTH_GM = _astropy_constants.EARTH_GM
EARTH_J2 = _astropy_constants.EARTH_J2
EARTH_ROTATION_RATE = _astropy_constants.EARTH_ROTATION_RATE


def get_astropy_constants() -> AstropyPhysicsConstants:
    """
    獲取 Astropy 物理常數實例

    Returns:
        AstropyPhysicsConstants: 物理常數對象
    """
    return _astropy_constants


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 學術引用資訊
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

__citation__ = """
@article{astropy2024,
  author = {{Astropy Collaboration}},
  title = {Astropy: A community Python package for astronomy},
  journal = {The Astronomical Journal},
  year = {2024},
  doi = {10.3847/1538-3881/aabc4f}
}

@misc{codata2018,
  title = {CODATA Recommended Values of the Fundamental Physical Constants: 2018},
  author = {Tiesinga, E. and Mohr, P. J. and Newell, D. B. and Taylor, B. N.},
  year = {2021},
  publisher = {National Institute of Standards and Technology},
  doi = {10.18434/T4W30H}
}

@misc{codata2022,
  title = {CODATA Recommended Values of the Fundamental Physical Constants: 2022},
  author = {Tiesinga, E. and Mohr, P. J. and Newell, D. B. and Taylor, B. N.},
  year = {2024},
  publisher = {National Institute of Standards and Technology},
  note = {In preparation}
}
"""

__version__ = "1.0.0"
__author__ = "Orbit Engine Team"
__date__ = "2025-10-03"

if __name__ == "__main__":
    # 測試與驗證
    astropy_const = get_astropy_constants()

    print("=== Astropy 物理常數測試 ===")
    print(f"光速: {astropy_const.SPEED_OF_LIGHT:.1f} m/s")
    print(f"玻爾茲曼常數: {astropy_const.BOLTZMANN_CONSTANT:.6e} J/K")
    print(f"地球半徑: {astropy_const.EARTH_RADIUS:.1f} m")
    print(f"地球 GM: {astropy_const.EARTH_GM:.6e} m³/s²")
    print(f"\n元數據: {astropy_const.get_metadata()}")
