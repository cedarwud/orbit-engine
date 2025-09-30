"""
星座配置常數
基於研究目標和軌道特性定義

Academic Compliance:
- 配置基於 final.md 研究需求
- 軌道參數基於實際物理特性
- 服務參數基於 3GPP NTN 標準
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ConstellationConfig:
    """星座配置數據類"""
    name: str
    display_name: str

    # 軌道特性（基於 final.md 研究需求）
    orbital_period_range_minutes: Tuple[int, int]
    typical_altitude_km: int
    orbital_characteristics: str  # 'LEO_low', 'LEO_high', 'MEO', 'GEO'

    # 服務特性（基於 3GPP NTN 標準）
    service_elevation_threshold_deg: float
    expected_visible_satellites: Tuple[int, int]
    candidate_pool_size: Tuple[int, int]

    # 數據來源
    data_source: str
    tle_directory: str

    # 採樣配置（用於開發/測試）
    sample_ratio: float = 0.1
    sample_max: int = 10


class ConstellationRegistry:
    """星座註冊表 - 集中管理所有支援的星座"""

    # 基於 final.md 的研究星座配置
    STARLINK = ConstellationConfig(
        name='starlink',
        display_name='Starlink',
        orbital_period_range_minutes=(90, 95),
        typical_altitude_km=550,
        orbital_characteristics='LEO_low',
        service_elevation_threshold_deg=5.0,
        expected_visible_satellites=(10, 15),
        candidate_pool_size=(200, 500),
        data_source='Space-Track.org',
        tle_directory='starlink/tle',
        sample_ratio=0.5,
        sample_max=10
    )

    ONEWEB = ConstellationConfig(
        name='oneweb',
        display_name='OneWeb',
        orbital_period_range_minutes=(109, 115),
        typical_altitude_km=1200,
        orbital_characteristics='LEO_high',
        service_elevation_threshold_deg=10.0,
        expected_visible_satellites=(3, 6),
        candidate_pool_size=(50, 100),
        data_source='Space-Track.org',
        tle_directory='oneweb/tle',
        sample_ratio=0.25,
        sample_max=5
    )

    # 支援的星座列表（易於擴展）
    SUPPORTED_CONSTELLATIONS = [STARLINK, ONEWEB]

    @classmethod
    def get_constellation(cls, name: str) -> ConstellationConfig:
        """根據名稱獲取星座配置"""
        for constellation in cls.SUPPORTED_CONSTELLATIONS:
            if constellation.name.lower() == name.lower():
                return constellation
        raise ValueError(f"不支援的星座: {name}")

    @classmethod
    def get_all_names(cls) -> List[str]:
        """獲取所有支援的星座名稱"""
        return [c.name for c in cls.SUPPORTED_CONSTELLATIONS]

    @classmethod
    def get_all_configs(cls) -> List[ConstellationConfig]:
        """獲取所有星座配置"""
        return cls.SUPPORTED_CONSTELLATIONS