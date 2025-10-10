#!/usr/bin/env python3
"""
動態閾值分析器 - Stage 4 組件
Dynamic Threshold Analyzer for D2 Handover Events

職責:
1. 分析候選衛星的地面距離分佈
2. 計算統計分位數（25th%, 50th%, 75th%, 95th%）
3. 生成 D2 事件的建議閾值（自適應於當前 TLE 數據）

學術依據:
- 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a (D2 事件閾值可配置)
- 數據驅動參數選擇（Data-Driven Parameter Selection）
- 自適應網路配置（Adaptive Network Configuration）

創建日期: 2025-10-10
"""

import logging
import math
from typing import Dict, List, Any, Tuple
import numpy as np


class DynamicThresholdAnalyzer:
    """動態閾值分析器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_candidate_distances(
        self,
        candidate_satellites: Dict[str, Any],
        ue_position: Dict[str, float]
    ) -> Dict[str, Any]:
        """分析候選衛星的地面距離分佈並生成閾值建議

        Args:
            candidate_satellites: Stage 4 候選衛星數據
                格式: {
                    'satellite_id': {
                        'time_series': [
                            {'timestamp': ..., 'geographic_coordinates': {...}, ...}
                        ]
                    }
                }
            ue_position: 地面站位置 {'lat': ..., 'lon': ...}

        Returns:
            {
                'starlink': {
                    'distance_statistics': {...},
                    'recommended_thresholds': {
                        'd2_threshold1_km': ...,
                        'd2_threshold2_km': ...
                    }
                },
                'oneweb': {...},
                'analysis_metadata': {...}
            }
        """
        self.logger.info("🔬 開始動態閾值分析（基於當前 TLE 數據）")

        # 分星座分析
        starlink_analysis = self._analyze_constellation(
            candidate_satellites, ue_position, 'starlink'
        )
        oneweb_analysis = self._analyze_constellation(
            candidate_satellites, ue_position, 'oneweb'
        )

        result = {
            'starlink': starlink_analysis,
            'oneweb': oneweb_analysis,
            'analysis_metadata': {
                'ue_position': ue_position,
                'analysis_method': 'data_driven_percentile',
                'threshold_strategy': 'conservative_median',
                'academic_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.15a'
            }
        }

        self.logger.info("✅ 動態閾值分析完成")
        self.logger.info(f"   Starlink 建議: T1={starlink_analysis['recommended_thresholds']['d2_threshold1_km']:.0f} km, "
                        f"T2={starlink_analysis['recommended_thresholds']['d2_threshold2_km']:.0f} km")
        self.logger.info(f"   OneWeb 建議: T1={oneweb_analysis['recommended_thresholds']['d2_threshold1_km']:.0f} km, "
                        f"T2={oneweb_analysis['recommended_thresholds']['d2_threshold2_km']:.0f} km")

        return result

    def _analyze_constellation(
        self,
        candidate_satellites: Dict[str, Any],
        ue_position: Dict[str, float],
        constellation: str
    ) -> Dict[str, Any]:
        """分析單一星座的距離分佈"""

        # 收集所有地面距離
        all_distances = []
        satellite_count = 0
        time_point_count = 0

        # 🔑 修復: connectable_satellites 是 {constellation: [sat_list]} 結構
        # 直接從對應星座的列表中取得衛星數據
        satellites_list = candidate_satellites.get(constellation, [])

        for sat_data in satellites_list:
            satellite_count += 1
            time_series = sat_data.get('time_series', [])

            for point in time_series:
                # 🔑 修復: time_series 中的點有 'position' 和 'visibility_metrics' 嵌套結構
                position = point.get('position', {})
                vis_metrics = point.get('visibility_metrics', {})

                # ✅ 關鍵修復: 只處理可見/可連接的時間點
                # 用戶發現: "為什麼中位數會這麼高?現在是用篩選後的衛星來做計算吧?"
                # 原問題: 包含所有時間點（包括 elevation < threshold 的不可見點）
                # 修復: 只用 is_connectable=True 的時間點計算距離統計
                if not vis_metrics.get('is_connectable', False):
                    continue  # 跳過不可見時間點

                if not position:
                    continue

                sat_lat = position.get('latitude_deg')
                sat_lon = position.get('longitude_deg')

                if sat_lat is None or sat_lon is None:
                    continue

                # 計算 2D 地面距離（Haversine）
                distance_km = self._haversine_distance(
                    ue_position['lat'], ue_position['lon'],
                    sat_lat, sat_lon
                )
                all_distances.append(distance_km)
                time_point_count += 1

        if not all_distances:
            self.logger.warning(f"⚠️ {constellation}: 無距離數據")
            return self._empty_analysis(constellation)

        # 計算統計分位數
        distances_array = np.array(all_distances)
        stats = {
            'satellite_count': satellite_count,
            'sample_count': time_point_count,
            'min': float(np.min(distances_array)),
            'percentile_5': float(np.percentile(distances_array, 5)),
            'percentile_25': float(np.percentile(distances_array, 25)),
            'median': float(np.percentile(distances_array, 50)),
            'percentile_75': float(np.percentile(distances_array, 75)),
            'percentile_95': float(np.percentile(distances_array, 95)),
            'max': float(np.max(distances_array)),
            'mean': float(np.mean(distances_array)),
            'std': float(np.std(distances_array))
        }

        # 生成 D2 閾值建議
        # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a
        # 策略 A (平衡換手頻率):
        # - Threshold1 (服務衛星距離門檻): median (中位數)
        #   學術依據: 服務衛星距離超過 median 時，信號品質開始劣化，應考慮換手
        # - Threshold2 (鄰居衛星距離門檻): 25th percentile
        #   學術依據: 鄰居衛星距離 < 25th 確保明顯改善，避免無意義換手
        recommended_thresholds = {
            'd2_threshold1_km': round(stats['median'], 1),
            'd2_threshold2_km': round(stats['percentile_25'], 1),
            'strategy': 'percentile_based_balanced',
            'rationale': {
                'threshold1': 'median - serving satellite degradation threshold (balanced handover frequency)',
                'threshold2': '25th percentile - ensure significant improvement when switching to neighbor'
            }
        }

        self.logger.info(f"   {constellation}: {satellite_count} 顆, {time_point_count} 個樣本點")
        self.logger.info(f"      距離範圍: {stats['min']:.1f} - {stats['max']:.1f} km")
        self.logger.info(f"      中位數: {stats['median']:.1f} km, 75th%: {stats['percentile_75']:.1f} km")

        return {
            'constellation': constellation,
            'distance_statistics': stats,
            'recommended_thresholds': recommended_thresholds,
            'data_source': 'stage4_candidate_satellites',
            'independent_of_pool_optimization': True
        }

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """計算兩點間的大圓距離（公里）

        SOURCE: Sinnott, R. W. (1984). "Virtues of the Haversine"
        Sky and Telescope, 68(2), 159

        Args:
            lat1, lon1: 第一點的緯度、經度（度）
            lat2, lon2: 第二點的緯度、經度（度）

        Returns:
            距離（公里）
        """
        R = 6371.0  # Earth radius in km

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _empty_analysis(self, constellation: str) -> Dict[str, Any]:
        """返回空的分析結果"""
        return {
            'constellation': constellation,
            'distance_statistics': {},
            'recommended_thresholds': {
                'd2_threshold1_km': None,
                'd2_threshold2_km': None,
                'strategy': 'no_data'
            },
            'data_source': 'none',
            'independent_of_pool_optimization': True
        }
