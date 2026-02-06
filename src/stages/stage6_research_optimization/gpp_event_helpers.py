#!/usr/bin/env python3
"""
3GPP 事件檢測器 - 輔助方法與配置

從 gpp_event_detector.py 拆分出的基礎類別，包含:
1. 配置載入與預設值 (含 3GPP 標準參數)
2. 時間序列數據處理
3. 衛星選擇與數據提取

標準: 3GPP TS 38.331 v18.5.1
"""

import logging
from typing import Dict, Any, List, Optional

from src.shared.utils.coordinate_converter import ecef_to_geodetic
from src.shared.utils import haversine_distance


class GPPEventHelpers:
    """3GPP 事件檢測輔助方法基礎類別"""

    def _collect_all_timestamps(self, signal_analysis: Dict[str, Any]) -> List[str]:
        """從所有衛星的 time_series 收集所有唯一時間戳

        ✅ Fail-Fast: 確保所有衛星都有 time_series 數據和時間戳

        Args:
            signal_analysis: Stage 5 輸出的信號分析數據

        Returns:
            排序後的唯一時間戳列表
        """
        all_timestamps = set()

        for sat_id, sat_data in signal_analysis.items():
            if 'time_series' not in sat_data:
                raise ValueError(
                    f"衛星 {sat_id} 缺少 time_series 字段\n"
                    "3GPP 事件檢測需要完整的時間序列數據\n"
                    "請確保 Stage 5 提供所有衛星的 time_series"
                )

            time_series = sat_data['time_series']

            for point in time_series:
                if 'timestamp' not in point:
                    raise ValueError(
                        f"衛星 {sat_id} 的 time_series 中發現缺少 timestamp 的數據點\n"
                        "Grade A 標準要求所有時間點必須有時間戳\n"
                        f"問題數據點: {point}"
                    )
                all_timestamps.add(point['timestamp'])

        return sorted(list(all_timestamps))

    def _get_visible_satellites_at(
        self,
        signal_analysis: Dict[str, Any],
        timestamp: str
    ) -> List[Dict[str, Any]]:
        """獲取特定時間點可見的衛星

        ✅ Fail-Fast: 確保所有數據字段完整

        Args:
            signal_analysis: Stage 5 輸出的信號分析數據
            timestamp: 目標時間戳

        Returns:
            該時間點可見的衛星列表
        """
        visible = []

        for sat_id, sat_data in signal_analysis.items():
            if 'time_series' not in sat_data:
                raise ValueError(
                    f"衛星 {sat_id} 缺少 time_series 字段\n"
                    "3GPP 事件檢測需要完整的時間序列數據\n"
                    "請確保 Stage 5 提供所有衛星的 time_series"
                )

            time_series = sat_data['time_series']

            for point in time_series:
                if point.get('timestamp') == timestamp:
                    if point.get('is_connectable', False):
                        if 'constellation' not in sat_data:
                            raise ValueError(
                                f"衛星 {sat_id} 缺少 constellation 字段\n"
                                "D2 事件檢測需要星座資訊"
                            )
                        if 'signal_quality' not in point:
                            raise ValueError(
                                f"衛星 {sat_id} 在時間點 {timestamp} 缺少 signal_quality"
                            )
                        if 'physical_parameters' not in point:
                            raise ValueError(
                                f"衛星 {sat_id} 在時間點 {timestamp} 缺少 physical_parameters"
                            )
                        if 'summary' not in sat_data:
                            raise ValueError(
                                f"衛星 {sat_id} 缺少 summary 字段"
                            )

                        visible.append({
                            'satellite_id': sat_id,
                            'constellation': sat_data['constellation'],
                            'timestamp': timestamp,
                            'signal_quality': point['signal_quality'],
                            'physical_parameters': point['physical_parameters'],
                            'summary': sat_data['summary']
                        })
                    break

        return visible

    def _select_serving_satellite(
        self,
        visible_satellites: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """選擇服務衛星 (使用中位數 RSRP 策略)

        Args:
            visible_satellites: 可見衛星列表

        Returns:
            選中的服務衛星
        """
        if not visible_satellites:
            raise ValueError("沒有可見衛星可供選擇")

        if len(visible_satellites) == 1:
            return visible_satellites[0]

        satellites_with_rsrp = []
        for sat in visible_satellites:
            if 'signal_quality' not in sat:
                raise ValueError(
                    f"衛星 {sat.get('satellite_id', 'unknown')} 缺少 signal_quality 字段"
                )
            if 'rsrp_dbm' not in sat['signal_quality']:
                raise ValueError(
                    f"衛星 {sat.get('satellite_id', 'unknown')} 的 signal_quality 缺少 rsrp_dbm"
                )

            rsrp = sat['signal_quality']['rsrp_dbm']
            satellites_with_rsrp.append((sat, rsrp))

        satellites_with_rsrp.sort(key=lambda x: x[1])
        median_index = len(satellites_with_rsrp) // 2
        return satellites_with_rsrp[median_index][0]

    def _extract_serving_satellite(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """提取服務衛星數據

        策略:
        1. 如果指定 serving_satellite_id，使用該衛星
        2. 選擇 RSRP 中位數的衛星作為服務衛星

        SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4
        """
        if not signal_analysis:
            return None

        if serving_satellite_id and serving_satellite_id in signal_analysis:
            sat_data = signal_analysis[serving_satellite_id]
            return self._extract_satellite_snapshot(serving_satellite_id, sat_data)

        satellite_rsrp = []

        for sat_id, sat_data in signal_analysis.items():
            if 'summary' not in sat_data:
                raise ValueError(f"衛星 {sat_id} 缺少 summary 字段")

            summary = sat_data['summary']

            if 'average_rsrp_dbm' not in summary:
                raise ValueError(f"衛星 {sat_id} 的 summary 缺少 average_rsrp_dbm")

            rsrp = summary['average_rsrp_dbm']
            satellite_rsrp.append((sat_id, rsrp))

        satellite_rsrp.sort(key=lambda x: x[1])
        median_index = len(satellite_rsrp) // 2
        median_satellite_id = satellite_rsrp[median_index][0]
        median_rsrp = satellite_rsrp[median_index][1]

        max_satellite_id = satellite_rsrp[-1][0]
        max_rsrp = satellite_rsrp[-1][1]
        min_satellite_id = satellite_rsrp[0][0]
        min_rsrp = satellite_rsrp[0][1]

        self.logger.info(
            f"📡 服務衛星選擇策略: 中位數 RSRP\n"
            f"   總衛星數: {len(satellite_rsrp)}\n"
            f"   最低 RSRP: {min_satellite_id} ({min_rsrp:.2f} dBm)\n"
            f"   中位數: {median_satellite_id} ({median_rsrp:.2f} dBm) ✅ 選為服務衛星\n"
            f"   最高 RSRP: {max_satellite_id} ({max_rsrp:.2f} dBm)\n"
            f"   RSRP 範圍: {max_rsrp - min_rsrp:.2f} dB"
        )

        sat_data = signal_analysis[median_satellite_id]
        return self._extract_satellite_snapshot(median_satellite_id, sat_data)

    def _extract_neighbor_satellites(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: str
    ) -> List[Dict[str, Any]]:
        """提取鄰近衛星列表 (排除服務衛星)"""
        neighbor_satellites = []

        for sat_id, sat_data in signal_analysis.items():
            if sat_id != serving_satellite_id:
                snapshot = self._extract_satellite_snapshot(sat_id, sat_data)
                neighbor_satellites.append(snapshot)

        return neighbor_satellites

    def _extract_satellite_snapshot(self, sat_id: str, sat_data: Dict[str, Any]) -> Dict[str, Any]:
        """從 time_series 提取最新時間點的衛星數據快照

        ✅ Fail-Fast: 確保所有必需字段存在
        """
        if 'time_series' not in sat_data:
            raise ValueError(f"衛星 {sat_id} 缺少 time_series 字段")

        time_series = sat_data['time_series']

        if not time_series or len(time_series) == 0:
            raise ValueError(f"衛星 {sat_id} 的 time_series 為空")

        if 'summary' not in sat_data:
            raise ValueError(f"衛星 {sat_id} 缺少 summary 字段")

        summary = sat_data['summary']
        latest_point = time_series[-1]

        if 'signal_quality' not in latest_point:
            raise ValueError(f"衛星 {sat_id} 的 time_series 最新點缺少 signal_quality")

        signal_quality = latest_point['signal_quality']

        if 'physical_parameters' not in latest_point:
            raise ValueError(f"衛星 {sat_id} 的 time_series 最新點缺少 physical_parameters")

        physical_parameters = latest_point['physical_parameters']

        if 'constellation' not in sat_data:
            raise ValueError(f"衛星 {sat_id} 缺少 constellation 數據")

        return {
            'satellite_id': sat_id,
            'constellation': sat_data['constellation'],
            'signal_quality': signal_quality,
            'physical_parameters': physical_parameters,
            'summary': summary
        }

    def _empty_event_result(self) -> Dict[str, Any]:
        """返回空的事件檢測結果"""
        return {
            'a3_events': [],
            'a4_events': [],
            'a5_events': [],
            'd2_events': [],
            'total_events': 0,
            'event_summary': {
                'a3_count': 0,
                'a4_count': 0,
                'a5_count': 0,
                'd2_count': 0,
                'events_per_minute': 0.0
            }
        }

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數

        所有門檻值均基於 3GPP 標準和 LEO NTN 場景實測數據
        """
        default_config = {
            # A3 事件偏移 (Neighbour becomes offset better than SpCell)
            # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4
            # LEO NTN 優化: 2.0 dB (等比例調整: 3 × (17/60) ≈ 0.85 → 取 2.0)
            'a3_offset_db': 2.0,

            # A4 事件門檻 (Neighbour becomes better than threshold)
            # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.5
            'a4_threshold_dbm': -100.0,

            # A5 事件雙門檻 (NTN 優化配置)
            # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.6
            # Threshold1: 10th percentile + hysteresis + margin
            'a5_threshold1_dbm': -41.0,
            # Threshold2: 70th percentile - hysteresis - margin
            'a5_threshold2_dbm': -34.0,

            # D2 事件距離門檻
            # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a
            'd2_threshold1_km': 2000.0,
            'd2_threshold2_km': 1500.0,

            # 遲滯參數
            # SOURCE: 3GPP TS 38.331 Section 5.5.3.1
            'hysteresis_db': 1.5,
            'hysteresis_km': 50.0,

            # 偏移參數 (同頻場景)
            # SOURCE: 3GPP TS 38.331 Section 5.5.4
            'offset_frequency': 0.0,
            'offset_cell': 0.0,

            # 時間觸發延遲
            # SOURCE: 3GPP TS 38.331 Section 5.5.6.1
            'time_to_trigger_ms': 640,

            # 觀測窗口時長
            'observation_window_minutes': 120.0
        }

        if config:
            if 'gpp_events' in config:
                gpp_config = config['gpp_events']

                if 'a3' in gpp_config:
                    a3_config = gpp_config['a3']
                    if 'offset_db' in a3_config:
                        default_config['a3_offset_db'] = a3_config['offset_db']
                    if 'time_to_trigger_ms' in a3_config:
                        default_config['time_to_trigger_ms'] = a3_config['time_to_trigger_ms']

                if 'a4' in gpp_config:
                    a4_config = gpp_config['a4']
                    if 'rsrp_threshold_dbm' in a4_config:
                        default_config['a4_threshold_dbm'] = a4_config['rsrp_threshold_dbm']
                    if 'hysteresis_db' in a4_config:
                        default_config['hysteresis_db'] = a4_config['hysteresis_db']
                    if 'time_to_trigger_ms' in a4_config:
                        default_config['time_to_trigger_ms'] = a4_config['time_to_trigger_ms']

                if 'a5' in gpp_config:
                    a5_config = gpp_config['a5']
                    if 'rsrp_threshold1_dbm' in a5_config:
                        default_config['a5_threshold1_dbm'] = a5_config['rsrp_threshold1_dbm']
                    if 'rsrp_threshold2_dbm' in a5_config:
                        default_config['a5_threshold2_dbm'] = a5_config['rsrp_threshold2_dbm']

                if 'd2' in gpp_config:
                    d2_config = gpp_config['d2']
                    if 'distance_threshold1_km' in d2_config:
                        default_config['d2_threshold1_km'] = d2_config['distance_threshold1_km']
                    if 'distance_threshold2_km' in d2_config:
                        default_config['d2_threshold2_km'] = d2_config['distance_threshold2_km']
            else:
                default_config.update(config)

        return default_config
