#!/usr/bin/env python3
"""
3GPP 事件檢測器 - Stage 6 核心組件

職責:
1. A3 事件: 鄰近衛星變得優於服務衛星加偏移 (3GPP TS 38.331 Section 5.5.4.4)
2. A4 事件: 鄰近衛星變得優於門檻值 (3GPP TS 38.331 Section 5.5.4.5)
3. A5 事件: 服務衛星劣於門檻1且鄰近衛星優於門檻2 (Section 5.5.4.6)
4. D2 事件: 基於距離的換手觸發 (Section 5.5.4.15a)

標準: 3GPP TS 38.331 v18.5.1
創建日期: 2025-09-30

🎓 學術合規性檢查提醒:
- 修改此文件前，請先閱讀: docs/stages/STAGE6_COMPLIANCE_CHECKLIST.md
- 重點檢查: 所有3GPP門檻值必須有完整的TS編號和Section引用
- 禁用詞: 假設、估計、簡化、模擬
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.shared.utils.coordinate_converter import ecef_to_geodetic
from src.shared.utils import haversine_distance
from .gpp_event_helpers import GPPEventHelpers


class GPPEventDetector(GPPEventHelpers):
    """3GPP NTN 事件檢測器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化檢測器

        Args:
            config: 配置參數，包含 A4/A5/D2 門檻值
        """
        self.config = self._load_config(config)
        self.logger = logging.getLogger(__name__)

        # 事件統計
        self.event_stats = {
            'a3_events': 0,
            'a4_events': 0,
            'a5_events': 0,
            'd2_events': 0,
            'total_events': 0
        }

        self.logger.info("📡 3GPP 事件檢測器初始化完成")
        self.logger.info(f"   A3 偏移: {self.config.get('a3_offset_db', 3.0)} dB")
        self.logger.info(f"   A4 門檻: {self.config['a4_threshold_dbm']} dBm")
        self.logger.info(f"   A5 門檻1: {self.config['a5_threshold1_dbm']} dBm")
        self.logger.info(f"   A5 門檻2: {self.config['a5_threshold2_dbm']} dBm")
        self.logger.info(f"   D2 門檻1: {self.config['d2_threshold1_km']} km")

    def detect_all_events(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """檢測所有類型的 3GPP 事件 - 遍歷時間序列

        Args:
            signal_analysis: Stage 5 的信號分析數據
            serving_satellite_id: 當前服務衛星 ID (可選)

        Returns:
            包含 a3/a4/a5/d2 事件列表和統計摘要的字典
        """
        self.logger.info("🔍 開始 3GPP 事件檢測...")
        self.logger.info("   模式: 遍歷完整時間序列 (修正版)")

        # Step 1: 收集所有唯一時間戳
        all_timestamps = self._collect_all_timestamps(signal_analysis)
        self.logger.info(f"   收集到 {len(all_timestamps)} 個唯一時間點")

        if len(all_timestamps) == 0:
            raise ValueError(
                "❌ signal_analysis 中沒有可用的時間點數據\n"
                "3GPP 事件檢測需要完整的時間序列數據\n"
                "請確保 Stage 5 提供所有衛星的 time_series 數據\n"
                "Grade A 標準禁止使用空結果作為回退"
            )

        # Step 2: 初始化事件列表
        all_a3_events = []
        all_a4_events = []
        all_a5_events = []
        all_d2_events = []
        time_points_processed = 0
        time_points_with_events = 0
        satellites_participating = set()

        # Step 3: 遍歷每個時間點
        for timestamp in all_timestamps:
            visible_satellites = self._get_visible_satellites_at(
                signal_analysis, timestamp
            )

            if len(visible_satellites) < 2:
                continue

            time_points_processed += 1

            serving_sat = self._select_serving_satellite(visible_satellites)
            neighbors = [s for s in visible_satellites if s['satellite_id'] != serving_sat['satellite_id']]

            if len(neighbors) == 0:
                continue

            # 檢測該時間點的所有事件類型
            a3_events_at_t = self.detect_a3_events(serving_sat, neighbors, timestamp)
            a4_events_at_t = self.detect_a4_events(serving_sat, neighbors, timestamp)
            a5_events_at_t = self.detect_a5_events(serving_sat, neighbors, timestamp)

            # 額外 A5 檢測: 嘗試信號較差的衛星作為服務衛星
            threshold_a5_1 = self.config['a5_threshold1_dbm']
            hysteresis = self.config['hysteresis_db']
            required_rsrp = threshold_a5_1 - hysteresis

            poor_signal_satellites = [s for s in visible_satellites
                                     if s.get('signal_quality', {}).get('rsrp_dbm', 0) < required_rsrp]

            if len(poor_signal_satellites) > 0:
                for poor_sat in poor_signal_satellites[:5]:
                    poor_neighbors = [s for s in visible_satellites
                                    if s['satellite_id'] != poor_sat['satellite_id']]
                    if len(poor_neighbors) > 0:
                        additional_a5 = self.detect_a5_events(poor_sat, poor_neighbors, timestamp)
                        a5_events_at_t.extend(additional_a5)

            d2_events_at_t = self.detect_d2_events(serving_sat, neighbors, timestamp)

            # 累加事件
            all_a3_events.extend(a3_events_at_t)
            all_a4_events.extend(a4_events_at_t)
            all_a5_events.extend(a5_events_at_t)
            all_d2_events.extend(d2_events_at_t)

            events_at_t = len(a3_events_at_t) + len(a4_events_at_t) + len(a5_events_at_t) + len(d2_events_at_t)
            if events_at_t > 0:
                time_points_with_events += 1

            for sat in visible_satellites:
                satellites_participating.add(sat['satellite_id'])

        # Step 4: 統計結果
        total_events = len(all_a3_events) + len(all_a4_events) + len(all_a5_events) + len(all_d2_events)

        self.event_stats['a3_events'] = len(all_a3_events)
        self.event_stats['a4_events'] = len(all_a4_events)
        self.event_stats['a5_events'] = len(all_a5_events)
        self.event_stats['d2_events'] = len(all_d2_events)
        self.event_stats['total_events'] = total_events

        self.logger.info(f"✅ 檢測完成:")
        self.logger.info(f"   時間點: {time_points_processed}/{len(all_timestamps)} 個有效")
        self.logger.info(f"   參與衛星: {len(satellites_participating)} 顆")
        self.logger.info(f"   總事件: {total_events} 個")
        self.logger.info(f"   A3: {len(all_a3_events)}, A4: {len(all_a4_events)}, A5: {len(all_a5_events)}, D2: {len(all_d2_events)}")

        time_coverage_rate = time_points_processed / len(all_timestamps) if len(all_timestamps) > 0 else 0.0

        return {
            'a3_events': all_a3_events,
            'a4_events': all_a4_events,
            'a5_events': all_a5_events,
            'd2_events': all_d2_events,
            'total_events': total_events,
            'event_summary': {
                'a3_count': len(all_a3_events),
                'a4_count': len(all_a4_events),
                'a5_count': len(all_a5_events),
                'd2_count': len(all_d2_events),
                'total_time_points': len(all_timestamps),
                'time_points_processed': time_points_processed,
                'time_points_with_events': time_points_with_events,
                'time_coverage_rate': time_coverage_rate,
                'participating_satellites': len(satellites_participating)
            },
            'time_series_coverage': {
                'total_timestamps': len(all_timestamps),
                'processed_timestamps': time_points_processed,
                'coverage_rate': time_coverage_rate,
                'participating_satellites': list(satellites_participating)
            }
        }

    def detect_a3_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]],
        actual_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """檢測 A3 事件: 鄰近衛星變得優於服務衛星加偏移

        3GPP TS 38.331 Section 5.5.4.4
        觸發條件: Mn + Ofn + Ocn - Hys > Mp + Ofp + Ocp + Off
        """
        a3_events = []

        hysteresis = self.config['hysteresis_db']
        a3_offset = self.config['a3_offset_db']

        serving_rsrp = serving_satellite['signal_quality']['rsrp_dbm']

        # 3GPP 標準預設值: offsetMO = 0.0, cellIndividualOffset = 0.0
        serving_offset_mo = serving_satellite['signal_quality'].get('offset_mo_db', 0.0)
        serving_cell_offset = serving_satellite['signal_quality'].get('cell_offset_db', 0.0)

        for neighbor in neighbor_satellites:
            neighbor_rsrp = neighbor['signal_quality']['rsrp_dbm']
            neighbor_offset_mo = neighbor['signal_quality'].get('offset_mo_db', 0.0)
            neighbor_cell_offset = neighbor['signal_quality'].get('cell_offset_db', 0.0)

            left_side = neighbor_rsrp + neighbor_offset_mo + neighbor_cell_offset - hysteresis
            right_side = serving_rsrp + serving_offset_mo + serving_cell_offset + a3_offset
            trigger_condition = left_side > right_side

            if trigger_condition:
                trigger_margin = left_side - right_side
                a3_event = {
                    'event_type': 'A3',
                    'event_id': f"A3_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                    'timestamp': actual_timestamp or datetime.now(timezone.utc).isoformat(),
                    'serving_satellite': serving_satellite['satellite_id'],
                    'neighbor_satellite': neighbor['satellite_id'],
                    'measurements': {
                        'serving_rsrp_dbm': serving_rsrp,
                        'neighbor_rsrp_dbm': neighbor_rsrp,
                        'serving_offset_mo_db': serving_offset_mo,
                        'serving_cell_offset_db': serving_cell_offset,
                        'neighbor_offset_mo_db': neighbor_offset_mo,
                        'neighbor_cell_offset_db': neighbor_cell_offset,
                        'hysteresis_db': hysteresis,
                        'a3_offset_db': a3_offset,
                        'trigger_margin_db': trigger_margin,
                        'left_side': left_side,
                        'right_side': right_side
                    },
                    'relative_comparison': {
                        'rsrp_difference': neighbor_rsrp - serving_rsrp,
                        'neighbor_better': True,
                        'handover_recommended': True
                    },
                    'gpp_parameters': {
                        'time_to_trigger_ms': self.config['time_to_trigger_ms']
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.4'
                }
                a3_events.append(a3_event)

        return a3_events

    def detect_a4_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]],
        actual_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """檢測 A4 事件: 鄰近衛星變得優於門檻值

        3GPP TS 38.331 Section 5.5.4.5
        觸發條件: Mn + Ofn + Ocn - Hys > Thresh
        """
        a4_events = []

        threshold_a4 = self.config['a4_threshold_dbm']
        hysteresis = self.config['hysteresis_db']
        offset_freq = self.config['offset_frequency']
        offset_cell = self.config['offset_cell']

        for neighbor in neighbor_satellites:
            neighbor_rsrp = neighbor['signal_quality']['rsrp_dbm']

            trigger_value = neighbor_rsrp + offset_freq + offset_cell - hysteresis
            trigger_condition = trigger_value > threshold_a4

            if trigger_condition:
                a4_event = {
                    'event_type': 'A4',
                    'event_id': f"A4_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                    'timestamp': actual_timestamp or datetime.now(timezone.utc).isoformat(),
                    'serving_satellite': serving_satellite['satellite_id'],
                    'neighbor_satellite': neighbor['satellite_id'],
                    'measurements': {
                        'neighbor_rsrp_dbm': neighbor_rsrp,
                        'threshold_dbm': threshold_a4,
                        'hysteresis_db': hysteresis,
                        'trigger_margin_db': neighbor_rsrp - threshold_a4,
                        'trigger_value': trigger_value
                    },
                    'gpp_parameters': {
                        'offset_frequency': offset_freq,
                        'offset_cell': offset_cell,
                        'time_to_trigger_ms': self.config['time_to_trigger_ms']
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.5'
                }
                a4_events.append(a4_event)

        return a4_events

    def detect_a5_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]],
        actual_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """檢測 A5 事件: 服務衛星劣化且鄰近衛星良好

        3GPP TS 38.331 Section 5.5.4.6
        條件1: Mp + Hys < Thresh1 (服務衛星劣化)
        條件2: Mn + Ofn + Ocn - Hys > Thresh2 (鄰近衛星良好)
        """
        a5_events = []

        threshold1_a5 = self.config['a5_threshold1_dbm']
        threshold2_a5 = self.config['a5_threshold2_dbm']
        hysteresis = self.config['hysteresis_db']
        offset_freq = self.config['offset_frequency']
        offset_cell = self.config['offset_cell']

        serving_rsrp = serving_satellite['signal_quality']['rsrp_dbm']

        serving_condition = (serving_rsrp + hysteresis) < threshold1_a5

        if not serving_condition:
            return a5_events

        for neighbor in neighbor_satellites:
            neighbor_rsrp = neighbor['signal_quality']['rsrp_dbm']

            neighbor_trigger_value = neighbor_rsrp + offset_freq + offset_cell - hysteresis
            neighbor_condition = neighbor_trigger_value > threshold2_a5

            if neighbor_condition:
                a5_event = {
                    'event_type': 'A5',
                    'event_id': f"A5_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                    'timestamp': actual_timestamp or datetime.now(timezone.utc).isoformat(),
                    'serving_satellite': serving_satellite['satellite_id'],
                    'neighbor_satellite': neighbor['satellite_id'],
                    'measurements': {
                        'serving_rsrp_dbm': serving_rsrp,
                        'neighbor_rsrp_dbm': neighbor_rsrp,
                        'threshold1_dbm': threshold1_a5,
                        'threshold2_dbm': threshold2_a5,
                        'serving_margin_db': threshold1_a5 - serving_rsrp,
                        'neighbor_margin_db': neighbor_rsrp - threshold2_a5
                    },
                    'dual_threshold_analysis': {
                        'serving_degraded': serving_condition,
                        'neighbor_sufficient': neighbor_condition,
                        'handover_recommended': True,
                        'serving_trigger_value': serving_rsrp + hysteresis,
                        'neighbor_trigger_value': neighbor_trigger_value
                    },
                    'gpp_parameters': {
                        'offset_frequency': offset_freq,
                        'offset_cell': offset_cell,
                        'time_to_trigger_ms': self.config['time_to_trigger_ms']
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.6'
                }
                a5_events.append(a5_event)

        return a5_events

    def detect_d2_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]],
        actual_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """檢測 D2 事件: 基於 2D 地面距離的換手觸發

        3GPP TS 38.331 v18.5.1 Section 5.5.4.15a
        條件1: Ml1 - Hys > Thresh1 (服務衛星地面距離劣於門檻1)
        條件2: Ml2 + Hys < Thresh2 (鄰居衛星地面距離優於門檻2)
        """
        d2_events = []

        if 'constellation' not in serving_satellite:
            raise ValueError(
                f"服務衛星 {serving_satellite.get('satellite_id', 'unknown')} 缺少 constellation 字段"
            )

        constellation = serving_satellite['constellation']

        if constellation in self.config and isinstance(self.config[constellation], dict):
            if 'd2_threshold1_km' not in self.config[constellation]:
                raise ValueError(f"星座 {constellation} 配置缺少 d2_threshold1_km")
            if 'd2_threshold2_km' not in self.config[constellation]:
                raise ValueError(f"星座 {constellation} 配置缺少 d2_threshold2_km")
            threshold1_km = self.config[constellation]['d2_threshold1_km']
            threshold2_km = self.config[constellation]['d2_threshold2_km']
        else:
            self.logger.warning(
                f"星座 {constellation} 沒有特定配置，使用全局默認閾值"
            )
            threshold1_km = self.config['d2_threshold1_km']
            threshold2_km = self.config['d2_threshold2_km']

        hysteresis_km = self.config['hysteresis_km']

        threshold1_m = threshold1_km * 1000.0
        threshold2_m = threshold2_km * 1000.0
        hysteresis_m = hysteresis_km * 1000.0

        # NTPU 地面站座標 (SOURCE: GPS Survey 2025-10-02)
        UE_LAT = 24.94388888
        UE_LON = 121.37083333

        if 'position_ecef_m' not in serving_satellite['physical_parameters']:
            raise ValueError(
                f"服務衛星 {serving_satellite['satellite_id']} 缺少 position_ecef_m"
            )

        serving_ecef = serving_satellite['physical_parameters']['position_ecef_m']
        serving_lat, serving_lon, _ = ecef_to_geodetic(
            serving_ecef[0], serving_ecef[1], serving_ecef[2]
        )
        serving_ground_distance_m = haversine_distance(
            UE_LAT, UE_LON, serving_lat, serving_lon
        )

        serving_condition = (serving_ground_distance_m - hysteresis_m) > threshold1_m

        if not serving_condition:
            return d2_events

        for neighbor in neighbor_satellites:
            if 'position_ecef_m' not in neighbor['physical_parameters']:
                raise ValueError(
                    f"鄰居衛星 {neighbor['satellite_id']} 缺少 position_ecef_m"
                )

            neighbor_ecef = neighbor['physical_parameters']['position_ecef_m']
            neighbor_lat, neighbor_lon, _ = ecef_to_geodetic(
                neighbor_ecef[0], neighbor_ecef[1], neighbor_ecef[2]
            )
            neighbor_ground_distance_m = haversine_distance(
                UE_LAT, UE_LON, neighbor_lat, neighbor_lon
            )

            neighbor_condition = (neighbor_ground_distance_m + hysteresis_m) < threshold2_m

            if neighbor_condition:
                d2_event = {
                    'event_type': 'D2',
                    'event_id': f"D2_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                    'timestamp': actual_timestamp or datetime.now(timezone.utc).isoformat(),
                    'serving_satellite': serving_satellite['satellite_id'],
                    'neighbor_satellite': neighbor['satellite_id'],
                    'measurements': {
                        'serving_ground_distance_km': serving_ground_distance_m / 1000.0,
                        'neighbor_ground_distance_km': neighbor_ground_distance_m / 1000.0,
                        'threshold1_km': threshold1_km,
                        'threshold2_km': threshold2_km,
                        'hysteresis_km': hysteresis_km,
                        'ground_distance_improvement_km': (serving_ground_distance_m - neighbor_ground_distance_m) / 1000.0,
                        'serving_ground_point': {'lat': serving_lat, 'lon': serving_lon},
                        'neighbor_ground_point': {'lat': neighbor_lat, 'lon': neighbor_lon}
                    },
                    'distance_analysis': {
                        'neighbor_closer': neighbor_condition,
                        'serving_far': serving_condition,
                        'handover_recommended': True,
                        'distance_ratio': neighbor_ground_distance_m / serving_ground_distance_m if serving_ground_distance_m > 0 else 0.0,
                        'measurement_method': '2D_ground_distance_haversine'
                    },
                    'gpp_parameters': {
                        'time_to_trigger_ms': self.config['time_to_trigger_ms']
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.15a',
                    'implementation_reference': {
                        'coordinate_conversion': 'Bowring_1985_geodetic_algorithm',
                        'distance_calculation': 'Sinnott_1984_haversine_formula'
                    }
                }
                d2_events.append(d2_event)

        return d2_events


if __name__ == "__main__":
    detector = GPPEventDetector()

    print("🧪 3GPP 事件檢測器測試:")
    print(f"A4 門檻: {detector.config['a4_threshold_dbm']} dBm")
    print(f"A5 門檻1: {detector.config['a5_threshold1_dbm']} dBm")
    print(f"A5 門檻2: {detector.config['a5_threshold2_dbm']} dBm")
    print(f"D2 門檻1: {detector.config['d2_threshold1_km']} km")
    print(f"D2 門檻2: {detector.config['d2_threshold2_km']} km")
    print("✅ 3GPP 事件檢測器測試完成")
