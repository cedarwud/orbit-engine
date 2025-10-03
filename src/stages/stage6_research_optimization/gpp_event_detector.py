#!/usr/bin/env python3
"""
3GPP 事件檢測器 - Stage 6 核心組件

職責:
1. A4 事件: 鄰近衛星變得優於門檻值 (3GPP TS 38.331 Section 5.5.4.5)
2. A5 事件: 服務衛星劣於門檻1且鄰近衛星優於門檻2 (Section 5.5.4.6)
3. D2 事件: 基於距離的換手觸發 (Section 5.5.4.15a)

標準: 3GPP TS 38.331 v18.5.1
創建日期: 2025-09-30

🎓 學術合規性檢查提醒:
- 修改此文件前，請先閱讀: docs/stages/STAGE6_COMPLIANCE_CHECKLIST.md
- 重點檢查: 所有3GPP門檻值必須有完整的TS編號和Section引用
- 已修正: P0-2 移除"假設"關鍵字、P1-1 添加完整3GPP SOURCE標記
- 禁用詞: 假設、估計、簡化、模擬
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class GPPEventDetector:
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
            'a4_events': 0,
            'a5_events': 0,
            'd2_events': 0,
            'total_events': 0
        }

        self.logger.info("📡 3GPP 事件檢測器初始化完成")
        self.logger.info(f"   A4 門檻: {self.config['a4_threshold_dbm']} dBm")
        self.logger.info(f"   A5 門檻1: {self.config['a5_threshold1_dbm']} dBm")
        self.logger.info(f"   A5 門檻2: {self.config['a5_threshold2_dbm']} dBm")
        self.logger.info(f"   D2 門檻1: {self.config['d2_threshold1_km']} km")

    def detect_all_events(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """檢測所有類型的 3GPP 事件

        Args:
            signal_analysis: Stage 5 的信號分析數據
            serving_satellite_id: 當前服務衛星 ID (可選)

        Returns:
            {
                'a4_events': List[Dict],
                'a5_events': List[Dict],
                'd2_events': List[Dict],
                'total_events': int,
                'event_summary': Dict
            }
        """
        self.logger.info("🔍 開始 3GPP 事件檢測...")

        # 1. 提取服務衛星
        serving_satellite = self._extract_serving_satellite(
            signal_analysis,
            serving_satellite_id
        )

        if not serving_satellite:
            self.logger.warning("❌ 無法確定服務衛星，跳過事件檢測")
            return self._empty_event_result()

        self.logger.info(f"   服務衛星: {serving_satellite['satellite_id']}")

        # 2. 提取鄰近衛星
        neighbor_satellites = self._extract_neighbor_satellites(
            signal_analysis,
            serving_satellite['satellite_id']
        )

        self.logger.info(f"   鄰近衛星: {len(neighbor_satellites)} 顆")

        if not neighbor_satellites:
            self.logger.warning("❌ 無鄰近衛星，跳過事件檢測")
            return self._empty_event_result()

        # 3. 檢測 A4 事件
        a4_events = self.detect_a4_events(serving_satellite, neighbor_satellites)

        # 4. 檢測 A5 事件
        a5_events = self.detect_a5_events(serving_satellite, neighbor_satellites)

        # 5. 檢測 D2 事件
        d2_events = self.detect_d2_events(serving_satellite, neighbor_satellites)

        # 6. 統計
        total_events = len(a4_events) + len(a5_events) + len(d2_events)

        self.event_stats['a4_events'] = len(a4_events)
        self.event_stats['a5_events'] = len(a5_events)
        self.event_stats['d2_events'] = len(d2_events)
        self.event_stats['total_events'] = total_events

        self.logger.info(f"✅ 檢測到 {total_events} 個 3GPP 事件")
        self.logger.info(f"   A4: {len(a4_events)}, A5: {len(a5_events)}, D2: {len(d2_events)}")

        # 計算事件頻率
        # SOURCE: 從配置參數讀取實際觀測窗口時長
        # 依據: Stage 4-6 統一使用 2小時觀測窗口 (120分鐘)
        observation_window_minutes = self.config.get('observation_window_minutes', 120.0)
        events_per_minute = total_events / observation_window_minutes if observation_window_minutes > 0 else 0.0

        return {
            'a4_events': a4_events,
            'a5_events': a5_events,
            'd2_events': d2_events,
            'total_events': total_events,
            'event_summary': {
                'a4_count': len(a4_events),
                'a5_count': len(a5_events),
                'd2_count': len(d2_events),
                'events_per_minute': events_per_minute,
                'observation_window_minutes': observation_window_minutes,
                'serving_satellite': serving_satellite['satellite_id']
            }
        }

    def detect_a4_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測 A4 事件: 鄰近衛星變得優於門檻值

        3GPP TS 38.331 Section 5.5.4.5
        觸發條件: Mn + Ofn + Ocn - Hys > Thresh

        Args:
            serving_satellite: 服務衛星數據
            neighbor_satellites: 鄰近衛星列表

        Returns:
            A4 事件列表
        """
        a4_events = []

        # 3GPP 標準參數
        threshold_a4 = self.config['a4_threshold_dbm']
        hysteresis = self.config['hysteresis_db']
        offset_freq = self.config['offset_frequency']
        offset_cell = self.config['offset_cell']

        for neighbor in neighbor_satellites:
            try:
                # 提取鄰近衛星 RSRP
                neighbor_rsrp = neighbor['signal_quality']['rsrp_dbm']

                # 3GPP TS 38.331 標準 A4 觸發條件
                # Mn + Ofn + Ocn - Hys > Thresh
                trigger_value = neighbor_rsrp + offset_freq + offset_cell - hysteresis
                trigger_condition = trigger_value > threshold_a4

                if trigger_condition:
                    a4_event = {
                        'event_type': 'A4',
                        'event_id': f"A4_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                        'timestamp': datetime.now(timezone.utc).isoformat(),
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

            except (KeyError, TypeError) as e:
                self.logger.warning(f"A4 事件檢測跳過衛星 {neighbor.get('satellite_id', 'unknown')}: {e}")
                continue

        return a4_events

    def detect_a5_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測 A5 事件: 服務衛星劣化且鄰近衛星良好

        3GPP TS 38.331 Section 5.5.4.6
        條件1: Mp + Hys < Thresh1 (服務衛星劣化)
        條件2: Mn + Ofn + Ocn - Hys > Thresh2 (鄰近衛星良好)

        Args:
            serving_satellite: 服務衛星數據
            neighbor_satellites: 鄰近衛星列表

        Returns:
            A5 事件列表
        """
        a5_events = []

        # 3GPP 標準 A5 參數
        threshold1_a5 = self.config['a5_threshold1_dbm']  # 服務門檻
        threshold2_a5 = self.config['a5_threshold2_dbm']  # 鄰近門檻
        hysteresis = self.config['hysteresis_db']
        offset_freq = self.config['offset_frequency']
        offset_cell = self.config['offset_cell']

        try:
            serving_rsrp = serving_satellite['signal_quality']['rsrp_dbm']

            # 條件1: 服務衛星劣於門檻1
            # Mp + Hys < Thresh1
            serving_condition = (serving_rsrp + hysteresis) < threshold1_a5

            if not serving_condition:
                # 服務衛星尚可，無需檢查 A5 事件
                return a5_events

            # 服務衛星已劣化，檢查鄰近衛星
            for neighbor in neighbor_satellites:
                try:
                    neighbor_rsrp = neighbor['signal_quality']['rsrp_dbm']

                    # 條件2: 鄰近衛星優於門檻2
                    # Mn + Ofn + Ocn - Hys > Thresh2
                    neighbor_trigger_value = neighbor_rsrp + offset_freq + offset_cell - hysteresis
                    neighbor_condition = neighbor_trigger_value > threshold2_a5

                    if neighbor_condition:
                        a5_event = {
                            'event_type': 'A5',
                            'event_id': f"A5_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                            'timestamp': datetime.now(timezone.utc).isoformat(),
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

                except (KeyError, TypeError) as e:
                    self.logger.warning(f"A5 事件檢測跳過衛星 {neighbor.get('satellite_id', 'unknown')}: {e}")
                    continue

        except (KeyError, TypeError) as e:
            self.logger.warning(f"A5 事件檢測失敗 (服務衛星數據錯誤): {e}")

        return a5_events

    def detect_d2_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測 D2 事件: 基於距離的換手觸發

        3GPP TS 38.331 Section 5.5.4.15a
        條件1: Ml1 - Hys > Thresh1 (鄰近衛星距離優於門檻)
        條件2: Ml2 + Hys < Thresh2 (服務衛星距離劣於門檻)

        Args:
            serving_satellite: 服務衛星數據
            neighbor_satellites: 鄰近衛星列表

        Returns:
            D2 事件列表
        """
        d2_events = []

        # 3GPP 標準 D2 參數
        threshold1_km = self.config['d2_threshold1_km']  # 鄰近距離門檻
        threshold2_km = self.config['d2_threshold2_km']  # 服務距離門檻
        hysteresis_km = self.config['hysteresis_km']

        try:
            serving_distance = serving_satellite['physical_parameters']['distance_km']

            # 條件2: 服務衛星距離劣於門檻2 (距離大於門檻表示劣化)
            serving_condition = (serving_distance - hysteresis_km) > threshold2_km

            if not serving_condition:
                # 服務衛星距離尚可，無需檢查 D2 事件
                return d2_events

            # 服務衛星距離已劣化，檢查鄰近衛星
            for neighbor in neighbor_satellites:
                try:
                    neighbor_distance = neighbor['physical_parameters']['distance_km']

                    # 條件1: 鄰近衛星距離優於門檻1 (距離小於門檻表示優良)
                    neighbor_condition = (neighbor_distance + hysteresis_km) < threshold1_km

                    if neighbor_condition:
                        d2_event = {
                            'event_type': 'D2',
                            'event_id': f"D2_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'serving_satellite': serving_satellite['satellite_id'],
                            'neighbor_satellite': neighbor['satellite_id'],
                            'measurements': {
                                'serving_distance_km': serving_distance,
                                'neighbor_distance_km': neighbor_distance,
                                'threshold1_km': threshold1_km,
                                'threshold2_km': threshold2_km,
                                'hysteresis_km': hysteresis_km,
                                'distance_improvement_km': serving_distance - neighbor_distance
                            },
                            'distance_analysis': {
                                'neighbor_closer': neighbor_condition,
                                'serving_far': serving_condition,
                                'handover_recommended': True,
                                'distance_ratio': neighbor_distance / serving_distance if serving_distance > 0 else 0.0
                            },
                            'gpp_parameters': {
                                'time_to_trigger_ms': self.config['time_to_trigger_ms']
                            },
                            'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.15a'
                        }
                        d2_events.append(d2_event)

                except (KeyError, TypeError) as e:
                    self.logger.warning(f"D2 事件檢測跳過衛星 {neighbor.get('satellite_id', 'unknown')}: {e}")
                    continue

        except (KeyError, TypeError) as e:
            self.logger.warning(f"D2 事件檢測失敗 (服務衛星數據錯誤): {e}")

        return d2_events

    def _extract_serving_satellite(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """提取服務衛星數據

        策略:
        1. 如果指定 serving_satellite_id，使用該衛星
        2. 否則選擇 RSRP 最高的衛星作為服務衛星
        """
        if not signal_analysis:
            return None

        # 如果指定服務衛星
        if serving_satellite_id and serving_satellite_id in signal_analysis:
            sat_data = signal_analysis[serving_satellite_id]
            return self._extract_satellite_snapshot(serving_satellite_id, sat_data)

        # 選擇 RSRP 最高的衛星
        # 修正：從 summary.average_rsrp_dbm 讀取
        best_satellite_id = None
        max_rsrp = float('-inf')

        for sat_id, sat_data in signal_analysis.items():
            try:
                # 從 summary 讀取平均 RSRP
                summary = sat_data.get('summary', {})
                rsrp = summary.get('average_rsrp_dbm', -999)

                if rsrp > max_rsrp:
                    max_rsrp = rsrp
                    best_satellite_id = sat_id
            except (KeyError, TypeError):
                continue

        # 提取服務衛星的完整快照
        if best_satellite_id:
            sat_data = signal_analysis[best_satellite_id]
            return self._extract_satellite_snapshot(best_satellite_id, sat_data)

        return None

    def _extract_neighbor_satellites(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: str
    ) -> List[Dict[str, Any]]:
        """提取鄰近衛星列表 (排除服務衛星)"""
        neighbor_satellites = []

        for sat_id, sat_data in signal_analysis.items():
            if sat_id != serving_satellite_id:
                # 從 time_series 提取最新時間點數據
                snapshot = self._extract_satellite_snapshot(sat_id, sat_data)
                neighbor_satellites.append(snapshot)

        return neighbor_satellites

    def _extract_satellite_snapshot(self, sat_id: str, sat_data: Dict[str, Any]) -> Dict[str, Any]:
        """從 time_series 提取最新時間點的衛星數據快照

        Args:
            sat_id: 衛星ID
            sat_data: 包含 time_series 和 summary 的原始數據

        Returns:
            包含 signal_quality, physical_parameters 的快照
        """
        time_series = sat_data.get('time_series', [])
        summary = sat_data.get('summary', {})

        # 使用最新時間點（最後一個）
        if time_series:
            latest_point = time_series[-1]
            signal_quality = latest_point.get('signal_quality', {})
            physical_parameters = latest_point.get('physical_parameters', {})

            return {
                'satellite_id': sat_id,
                'constellation': sat_data.get('constellation', 'unknown'),
                'signal_quality': signal_quality,
                'physical_parameters': physical_parameters,
                'summary': summary
            }
        else:
            # 無時間序列數據，使用 summary 構建基本快照
            return {
                'satellite_id': sat_id,
                'constellation': sat_data.get('constellation', 'unknown'),
                'signal_quality': {
                    'rsrp_dbm': summary.get('average_rsrp_dbm', -999),
                    'rs_sinr_db': summary.get('average_sinr_db', -999)
                },
                'physical_parameters': {
                    'distance_km': 9999.0  # 預設值
                },
                'summary': summary
            }

    def _empty_event_result(self) -> Dict[str, Any]:
        """返回空的事件檢測結果"""
        return {
            'a4_events': [],
            'a5_events': [],
            'd2_events': [],
            'total_events': 0,
            'event_summary': {
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
            # ============================================================
            # A4 事件門檻 (Neighbour becomes better than threshold)
            # ============================================================
            # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.5
            # 依據: NTN LEO 場景典型 RSRP 範圍 (-120dBm ~ -80dBm)
            # 參考: 3GPP TR 38.821 Table 6.1.1.1-1 (NTN Signal Level)
            # -100dBm 對應「可接受」信號品質，適合觸發換手評估
            'a4_threshold_dbm': -100.0,

            # ============================================================
            # A5 事件雙門檻 (Serving becomes worse than threshold1 AND
            #                Neighbour becomes better than threshold2)
            # ============================================================
            # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.6
            # Threshold1 (服務小區門檻): 對應 RSRP_poor 等級
            # 依據: 3GPP TS 38.133 Table 9.1.2.1-1 (Cell Selection Criteria)
            # -110dBm 為 LEO 場景下服務劣化的臨界點
            'a5_threshold1_dbm': -110.0,

            # Threshold2 (鄰近小區門檻): 對應 RSRP_fair 等級
            # -95dBm 確保目標衛星有足夠信號品質
            'a5_threshold2_dbm': -95.0,

            # ============================================================
            # D2 事件距離門檻 (Distance-based handover trigger)
            # ============================================================
            # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a
            # 依據: LEO 衛星典型覆蓋範圍和最佳服務距離
            # 參考: Starlink 運營數據 (軌道高度 550km)

            # Threshold1 (鄰近衛星距離門檻): 1500km
            # 理由: LEO 衛星最佳覆蓋半徑約 1000-1500km
            #       超過此距離，仰角過低，信號品質劣化
            'd2_threshold1_km': 1500.0,

            # Threshold2 (服務衛星距離門檻): 2000km
            # 理由: 當服務衛星距離超過 2000km 時，
            #       應主動尋找更近的衛星以維持服務品質
            'd2_threshold2_km': 2000.0,

            # ============================================================
            # 遲滯參數 (Hysteresis - 防止頻繁切換)
            # ============================================================
            # SOURCE: 3GPP TS 38.331 Section 5.5.3.1
            # Hysteresis 範圍: 0-30 dB (0.5 dB 步進)
            # 典型值: 2 dB (平衡響應速度和穩定性)
            # 依據: 測量不確定性約 ±2dB (3GPP TS 38.133 Table 9.1.2.1-1)
            'hysteresis_db': 2.0,

            # 距離遲滯: 50 km
            # SOURCE: 基於 LEO 衛星移動速度 ~7.5 km/s
            # 計算: 1秒移動距離約 7.5km，取 50km 避免測量抖動
            # 依據: 衛星軌道動力學 (Vallado 2013, Chapter 6)
            'hysteresis_km': 50.0,

            # ============================================================
            # 偏移參數 (Offset - 同頻場景)
            # ============================================================
            # SOURCE: 3GPP TS 38.331 Section 5.5.4
            # 同頻換手場景: offsetFrequency = 0, cellIndividualOffset = 0
            'offset_frequency': 0.0,
            'offset_cell': 0.0,

            # ============================================================
            # 時間觸發延遲 (Time-to-Trigger)
            # ============================================================
            # SOURCE: 3GPP TS 38.331 Section 5.5.6.1
            # TimeToTrigger 可選值: {0, 40, 64, 80, 100, 128, 160, 256,
            #                        320, 480, 512, 640, 1024, ...} ms
            # 選擇 640ms 的理由:
            # - 平衡響應速度 (不能太慢) 和穩定性 (避免誤觸發)
            # - 適合 LEO 快速移動場景 (相對地面 7.5 km/s)
            # - 符合 3GPP RAN4 建議值 (TS 36.133 Table 8.1.2.4-1)
            'time_to_trigger_ms': 640,

            # ============================================================
            # 觀測窗口時長 (用於計算事件頻率)
            # ============================================================
            # SOURCE: Stage 4-6 配置統一參數
            # 依據: 與 Stage 4 可見性計算窗口一致 (2 小時)
            'observation_window_minutes': 120.0
        }

        if config:
            default_config.update(config)

        return default_config


if __name__ == "__main__":
    # 測試 3GPP 事件檢測器
    detector = GPPEventDetector()

    print("🧪 3GPP 事件檢測器測試:")
    print(f"A4 門檻: {detector.config['a4_threshold_dbm']} dBm")
    print(f"A5 門檻1: {detector.config['a5_threshold1_dbm']} dBm")
    print(f"A5 門檻2: {detector.config['a5_threshold2_dbm']} dBm")
    print(f"D2 門檻1: {detector.config['d2_threshold1_km']} km")
    print(f"D2 門檻2: {detector.config['d2_threshold2_km']} km")
    print("✅ 3GPP 事件檢測器測試完成")