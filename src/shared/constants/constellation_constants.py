"""
星座配置常數
基於研究目標和軌道特性定義

Academic Compliance:
- 配置基於 final.md 研究需求
- 軌道參數基於實際物理特性
- 服務參數基於 3GPP NTN 標準

Data Provenance (數據來源):
- 射頻參數: 基於FCC/ITU公開文件和同行評審學術論文
- 詳細引用: 見 docs/data_sources/RF_PARAMETERS.md
- 版本: v1.0 (2025-10-01)
- 狀態: 研究估計值（適用於學術研究和系統級分析）

⚠️ 重要提醒:
精確衛星級參數受商業保密限制，本配置使用基於公開來源的合理工程估計。
所有參數已通過鏈路預算合理性驗證（見RF_PARAMETERS.md）。
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

    # 信號傳輸參數（Stage 5 需求，基於官方規格）
    tx_power_dbw: float                    # 發射功率 (dBW)
    tx_antenna_gain_db: float              # 發射天線增益 (dB)
    frequency_ghz: float                   # 工作頻率 (GHz)
    rx_antenna_diameter_m: float           # 接收天線直徑 (m)
    rx_antenna_efficiency: float           # 接收天線效率 (0-1)

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
        # 信號傳輸參數（研究估計值，基於公開文獻）
        # 數據來源: FCC DA-24-222 (2024) + UT Austin RadioNav Lab (2023)
        # 詳細引用: docs/data_sources/RF_PARAMETERS.md
        # 不確定性: tx_power ±3dB, tx_gain ±5dB
        tx_power_dbw=40.0,                     # 基於FCC用戶終端EIRP 42.1-43.4 dBW推算
        tx_antenna_gain_db=35.0,               # 基於學術文獻40dBi保守調整
        frequency_ghz=12.5,                    # Ku頻段下行（學術文獻標準值）
        rx_antenna_diameter_m=1.2,             # 標準Dishy用戶終端（公開規格）
        rx_antenna_efficiency=0.65,            # 相控陣典型效率（工程估計）
        data_source='Space-Track.org',
        tle_directory='starlink/tle',
        sample_ratio=0.5,
        sample_max=30  # 🧪 取樣模式: 增加到 30 顆以滿足驗證需求（最少 20 顆）
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
        # 信號傳輸參數（研究估計值，基於公開文獻）
        # 數據來源: FCC SAT-MPL-20200526-00062 + ITU SISS-2016
        # 詳細引用: docs/data_sources/RF_PARAMETERS.md
        # 不確定性: tx_power ±4dB, tx_gain ±5dB
        tx_power_dbw=38.0,                     # 基於Ka頻段EIRP密度+8.0 dBW/MHz推算
        tx_antenna_gain_db=33.0,               # 基於PFD和軌道高度反推
        frequency_ghz=12.75,                   # Ku頻段下行（Ku頻段中心頻率）
        rx_antenna_diameter_m=1.0,             # OneWeb用戶終端（公開規格）
        rx_antenna_efficiency=0.60,            # Ka頻段典型效率（工程估計）
        data_source='Space-Track.org',
        tle_directory='oneweb/tle',
        sample_ratio=0.25,
        sample_max=15  # 🧪 取樣模式: 增加到 15 顆以滿足驗證需求
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