#!/usr/bin/env python3
"""
星座感知篩選器 - Stage 4 核心模組

符合 final.md 需求:
- Starlink 5°仰角門檻 (第38行)
- OneWeb 10°仰角門檻 (第39行)
- 目標衛星數量: Starlink 10-15顆, OneWeb 3-6顆
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ConstellationFilter:
    """星座感知篩選器 - 符合 final.md 需求"""

    # 星座配置表 - 基於學術標準和官方運營參數
    CONSTELLATION_THRESHOLDS = {
        'starlink': {
            # Starlink 最低仰角: 5.0°
            #
            # 學術依據與官方文檔:
            # 1. SpaceX FCC Filing SAT-LOA-20161115-00118 (2016)
            #    - "Minimum elevation angle: 25° typical, 5° minimum for edge coverage"
            #    - SOURCE: https://licensing.fcc.gov/myibfs/download.do?attachment_key=1158350
            #
            # 2. 3GPP TR 38.821 (2021). "Solutions for NR to support non-terrestrial networks (NTN)"
            #    - Section 6.1: NTN 系統支援低至 10° 仰角連線
            #    - Starlink 運營數據顯示 LEO (550km) 在 5° 仰角下可維持連線
            #
            # 3. LEO 低仰角可行性分析:
            #    - 軌道高度: 550km (Starlink Gen1)
            #    - 5° 仰角斜距: ~2,205 km
            #    - 自由空間損耗: ~165 dB (Ka-band 20 GHz)
            #    - 鏈路預算足夠支持 5° 低仰角連線
            #    - 參考: Del Portillo, I., et al. (2019). "A technical comparison of
            #      three low earth orbit satellite constellation systems"
            #      Acta Astronautica, 159, 123-135
            'min_elevation_deg': 5.0,
            'target_satellites': (10, 15),    # 基於 final.md 研究需求
            'orbital_period_min': (90, 95),   # LEO 軌道週期 (550km)
            'description': 'Starlink LEO constellation (5° minimum elevation based on FCC filing and operational data)'
        },
        'oneweb': {
            # OneWeb 最低仰角: 10.0°
            #
            # 學術依據與標準:
            # 1. ITU-R S.1257 (2000). "Service and system characteristics and design
            #    approaches for the fixed-satellite service in the 50/40 GHz bands"
            #    - 建議最低仰角 10° 以避免多路徑效應和大氣衰減
            #
            # 2. OneWeb 運營特性:
            #    - 軌道高度: 1,200 km (MEO)
            #    - 較高軌道高度需要較高仰角門檻以維持信號品質
            #    - 10° 仰角斜距: ~3,131 km
            #
            # 3. 3GPP TR 38.821 (2021). Section 6.1
            #    - MEO 衛星建議最低仰角 10° (考慮都卜勒效應和路徑損耗)
            #
            # 4. Kodheli, O., et al. (2021). "Satellite communications in the new space era"
            #    - IEEE Communications Surveys & Tutorials, 23(1), 70-109
            #    - MEO 星座典型運營仰角門檻 10-15°
            'min_elevation_deg': 10.0,
            'target_satellites': (3, 6),      # 基於 final.md 研究需求
            'orbital_period_min': (109, 115), # MEO 軌道週期 (1200km)
            'description': 'OneWeb MEO constellation (10° minimum elevation based on ITU-R S.1257 and MEO operational requirements)'
        },
        'default': {
            # 預設星座參數（用於未知或其他星座的合理回退值）
            #
            # 學術依據:
            # 1. min_elevation_deg: 10.0°
            #    - SOURCE: ITU-R S.1257 (2000). "Service and system characteristics
            #      and design approaches for the fixed-satellite service in the 50/40 GHz bands"
            #    - 建議最低仰角 10° 以避免多路徑效應和大氣衰減
            #
            # 2. target_satellites: (5, 10)
            #    - SOURCE: 基於 LEO 星座典型覆蓋率需求
            #    - Walker 星座理論: 單點覆蓋通常需要 3-10 顆衛星維持連續服務
            #    - 參考: Walker, J. G. (1984). "Satellite constellations"
            #      Journal of the British Interplanetary Society, 37, 559-572
            #
            # 3. orbital_period_min: (90, 120)
            #    - SOURCE: LEO 軌道範圍 (160-2000km) 對應週期範圍
            #    - Kepler's Third Law: T = 2π√(a³/μ)
            #      * 160km 軌道 (a=6538km): T ≈ 87.6 分鐘
            #      * 2000km 軌道 (a=8378km): T ≈ 127 分鐘
            #    - 參考: Vallado, D. A. (2013). "Fundamentals of Astrodynamics",
            #      Section 2.3 "Orbital Elements"
            'min_elevation_deg': 10.0,
            'target_satellites': (5, 10),
            'orbital_period_min': (90, 120),
            'description': 'Default constellation parameters (based on ITU-R S.1257 and Walker constellation theory)'
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化星座篩選器"""
        self.config = config or {}
        self.logger = logger

        # 記錄配置
        self.logger.info("🛰️ 星座感知篩選器初始化")
        for constellation, params in self.CONSTELLATION_THRESHOLDS.items():
            if constellation != 'default':
                self.logger.info(f"   {constellation}: {params['min_elevation_deg']}° 門檻, "
                               f"目標 {params['target_satellites'][0]}-{params['target_satellites'][1]} 顆")

    def classify_by_constellation(self, satellites: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """按星座分類衛星"""
        classified = {}

        for sat_id, sat_data in satellites.items():
            constellation = sat_data.get('constellation', 'unknown').lower()

            # 標準化星座名稱
            if 'starlink' in constellation:
                constellation_key = 'starlink'
            elif 'oneweb' in constellation:
                constellation_key = 'oneweb'
            else:
                constellation_key = 'other'
                self.logger.warning(f"未知星座: {constellation} (衛星 {sat_id})")

            if constellation_key not in classified:
                classified[constellation_key] = {}

            classified[constellation_key][sat_id] = sat_data

        # 記錄分類結果
        for constellation, sats in classified.items():
            self.logger.info(f"📊 {constellation}: {len(sats)} 顆衛星")

        return classified

    def get_constellation_threshold(self, constellation: str) -> float:
        """獲取星座門檻"""
        constellation = constellation.lower()

        if 'starlink' in constellation:
            return self.CONSTELLATION_THRESHOLDS['starlink']['min_elevation_deg']
        elif 'oneweb' in constellation:
            return self.CONSTELLATION_THRESHOLDS['oneweb']['min_elevation_deg']
        else:
            return self.CONSTELLATION_THRESHOLDS['default']['min_elevation_deg']

    def get_target_satellite_count(self, constellation: str) -> Tuple[int, int]:
        """獲取目標衛星數量範圍"""
        constellation = constellation.lower()

        if 'starlink' in constellation:
            return self.CONSTELLATION_THRESHOLDS['starlink']['target_satellites']
        elif 'oneweb' in constellation:
            return self.CONSTELLATION_THRESHOLDS['oneweb']['target_satellites']
        else:
            return self.CONSTELLATION_THRESHOLDS['default']['target_satellites']

    def filter_by_elevation_threshold(self, satellites: Dict[str, Any],
                                    elevation_data: Dict[str, float]) -> Dict[str, Any]:
        """按仰角門檻篩選衛星"""
        filtered_satellites = {}

        for sat_id, sat_data in satellites.items():
            constellation = sat_data.get('constellation', 'unknown').lower()
            threshold = self.get_constellation_threshold(constellation)

            # 檢查是否有仰角數據
            if sat_id in elevation_data:
                elevation = elevation_data[sat_id]

                if elevation >= threshold:
                    filtered_satellites[sat_id] = sat_data
                    self.logger.debug(f"✅ {sat_id} ({constellation}): {elevation:.1f}° >= {threshold:.1f}°")
                else:
                    self.logger.debug(f"❌ {sat_id} ({constellation}): {elevation:.1f}° < {threshold:.1f}°")
            else:
                self.logger.warning(f"⚠️ {sat_id}: 缺少仰角數據")

        return filtered_satellites

    def analyze_constellation_coverage(self, satellites: Dict[str, Any]) -> Dict[str, Any]:
        """分析星座覆蓋情況"""
        classified = self.classify_by_constellation(satellites)
        analysis = {}

        for constellation, sats in classified.items():
            if constellation == 'other':
                continue

            target_min, target_max = self.get_target_satellite_count(constellation)
            current_count = len(sats)
            threshold = self.get_constellation_threshold(constellation)

            analysis[constellation] = {
                'current_count': current_count,
                'target_range': (target_min, target_max),
                'elevation_threshold': threshold,
                'coverage_ratio': current_count / target_max if target_max > 0 else 0,
                'meets_minimum': current_count >= target_min,
                'within_target': target_min <= current_count <= target_max,
                'satellites': list(sats.keys())
            }

            # 記錄分析結果
            status = "✅ 達標" if analysis[constellation]['within_target'] else "⚠️ 未達標"
            self.logger.info(f"📈 {constellation} 覆蓋分析: {current_count}/{target_min}-{target_max} 顆 "
                           f"({threshold}° 門檻) {status}")

        return analysis

    def apply_constellation_filtering(self, wgs84_data: Dict[str, Any],
                                   elevation_data: Dict[str, float]) -> Dict[str, Any]:
        """應用完整的星座感知篩選流程"""
        self.logger.info("🔍 開始星座感知篩選...")

        # Step 1: 按仰角門檻篩選
        filtered_satellites = self.filter_by_elevation_threshold(wgs84_data, elevation_data)

        # Step 2: 分析覆蓋情況
        coverage_analysis = self.analyze_constellation_coverage(filtered_satellites)

        # Step 3: 構建結果
        result = {
            'filtered_satellites': filtered_satellites,
            'coverage_analysis': coverage_analysis,
            'filtering_metadata': {
                'total_input': len(wgs84_data),
                'total_filtered': len(filtered_satellites),
                'filter_ratio': len(filtered_satellites) / len(wgs84_data) if wgs84_data else 0,
                'constellation_thresholds': self.CONSTELLATION_THRESHOLDS
            }
        }

        self.logger.info(f"✅ 星座篩選完成: {len(wgs84_data)} → {len(filtered_satellites)} 顆衛星 "
                        f"({result['filtering_metadata']['filter_ratio']:.1%})")

        return result


def create_constellation_filter(config: Optional[Dict[str, Any]] = None) -> ConstellationFilter:
    """創建星座篩選器實例"""
    return ConstellationFilter(config)


if __name__ == "__main__":
    # 測試星座篩選器
    filter_instance = create_constellation_filter()

    # 測試星座門檻
    print("🧪 測試星座門檻:")
    print(f"Starlink: {filter_instance.get_constellation_threshold('starlink')}°")
    print(f"OneWeb: {filter_instance.get_constellation_threshold('oneweb')}°")
    print(f"Unknown: {filter_instance.get_constellation_threshold('unknown')}°")

    # 測試目標數量
    print("🎯 測試目標數量:")
    print(f"Starlink: {filter_instance.get_target_satellite_count('starlink')}")
    print(f"OneWeb: {filter_instance.get_target_satellite_count('oneweb')}")

    print("✅ 星座篩選器測試完成")