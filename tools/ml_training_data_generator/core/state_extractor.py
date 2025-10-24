"""
State Extractor - 從 Stage 6 輸出提取 RL 狀態
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np

from .types import (
    Stage6Output, RLState, SatelliteState,
    QoSRequirements, NetworkLoadState, TimeFeatures
)
from .temporal_feature_calculator import create_temporal_feature_calculator

logger = logging.getLogger(__name__)


class StateExtractor:
    """從 Stage 6 輸出提取 RL 狀態

    SOURCE: Badini et al. (2024) IEEE TAES, Section III.B
            "State Space Definition"
    """

    def __init__(self, max_candidates: int = 5):
        """初始化 State Extractor

        Args:
            max_candidates: 最大候選衛星數量
                SOURCE: Badini et al. (2024) - 典型為 3-5 個候選
        """
        self.max_candidates = max_candidates
        # NEW (2025-10-24): Initialize temporal feature calculator
        self.temporal_calculator = create_temporal_feature_calculator(time_interval_sec=30.0)
        logger.info(f"StateExtractor initialized (max_candidates={max_candidates}, temporal_features=enabled)")

    def extract_state(
        self,
        stage6_output: Stage6Output,
        timestamp_idx: int
    ) -> Optional[RLState]:
        """提取指定時間點的 RL 狀態

        Args:
            stage6_output: Stage 6 輸出數據
            timestamp_idx: 時間序列索引

        Returns:
            RLState 或 None（提取失敗時）
        """
        try:
            # 提取服務衛星（選擇 RSRP 最高的衛星）
            serving_satellite = self.extract_serving_satellite(
                stage6_output, timestamp_idx
            )
            if not serving_satellite:
                logger.warning(f"Failed to extract serving satellite at idx {timestamp_idx}")
                return None

            # 提取時間特徵（需要先提取以獲取 timestamp）
            time_features = self.extract_time_features(
                stage6_output, timestamp_idx, serving_satellite.satellite_id
            )

            # 提取候選衛星（RSRP 次高的 K 個）
            # FIXED (2025-10-24): Pass timestamp to ensure correct matching
            timestamp = time_features.timestamp if time_features else None
            candidate_satellites = self.extract_candidates(
                stage6_output, timestamp_idx, serving_satellite.satellite_id, timestamp=timestamp
            )

            # 提取 QoS 需求（從 scenario_variants）
            qos_requirements = self.extract_qos_requirements(stage6_output)

            # 提取網絡負載（從 scenario_variants）
            network_load = self.extract_network_load(stage6_output)

            # 構建 RLState
            rl_state = RLState(
                serving_satellite=serving_satellite,
                candidate_satellites=candidate_satellites,
                qos_requirements=qos_requirements,
                network_load=network_load,
                time_features=time_features
            )

            return rl_state

        except Exception as e:
            logger.error(f"Error extracting state at idx {timestamp_idx}: {e}")
            return None

    def extract_state_for_satellite(
        self,
        stage6_output: Stage6Output,
        serving_satellite_id: int,
        timestamp_idx: int
    ) -> Optional[RLState]:
        """提取指定時間點的 RL 狀態（指定服務衛星）

        NEW方法: 支持 per-satellite episode 生成

        Args:
            stage6_output: Stage 6 輸出數據
            serving_satellite_id: 指定的服務衛星 ID
            timestamp_idx: 時間序列索引

        Returns:
            RLState 或 None（提取失敗時）

        SOURCE: 修復 Proposal 003 數據生成瓶頸
                允許為每顆衛星生成獨立的 episode
        """
        try:
            # 檢查該衛星在此時間點是否有數據
            sat_id_str = str(serving_satellite_id)
            if sat_id_str not in stage6_output.signal_analysis:
                return None

            time_series = stage6_output.signal_analysis[sat_id_str].get('time_series', [])
            if timestamp_idx >= len(time_series):
                return None

            entry = time_series[timestamp_idx]

            # 構建服務衛星狀態 (with temporal features)
            serving_satellite = self._build_satellite_state(
                serving_satellite_id, entry, stage6_output, timestamp_idx=timestamp_idx
            )
            if not serving_satellite:
                return None

            # 提取候選衛星（RSRP 次高的 K 個，排除服務衛星）
            # FIXED (2025-10-24): Pass timestamp to ensure correct matching
            timestamp = entry.get('timestamp')
            candidate_satellites = self.extract_candidates(
                stage6_output, timestamp_idx, serving_satellite_id, timestamp=timestamp
            )

            # 提取 QoS 需求
            qos_requirements = self.extract_qos_requirements(stage6_output)

            # 提取網絡負載
            network_load = self.extract_network_load(stage6_output)

            # 提取時間特徵
            time_features = self.extract_time_features(
                stage6_output, timestamp_idx, serving_satellite_id
            )

            # 構建 RLState
            rl_state = RLState(
                serving_satellite=serving_satellite,
                candidate_satellites=candidate_satellites,
                qos_requirements=qos_requirements,
                network_load=network_load,
                time_features=time_features
            )

            return rl_state

        except Exception as e:
            logger.error(f"Error extracting state for satellite {serving_satellite_id} at idx {timestamp_idx}: {e}")
            return None

    def extract_serving_satellite(
        self,
        stage6_output: Stage6Output,
        timestamp_idx: int
    ) -> Optional[SatelliteState]:
        """提取服務衛星（RSRP 最強）

        策略：選擇當前時間點 RSRP 最強的衛星作為服務衛星

        SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.1
                "Serving cell selection based on RSRP"

        Args:
            stage6_output: Stage 6 輸出數據
            timestamp_idx: 時間序列索引

        Returns:
            SatelliteState 或 None
        """
        signal_analysis = stage6_output.signal_analysis
        if not signal_analysis:
            return None

        best_rsrp = float('-inf')
        best_satellite_id = None
        best_satellite_data = None

        # 遍歷所有衛星，找到 RSRP 最強的
        for sat_id_str, sat_data in signal_analysis.items():
            time_series = sat_data.get('time_series', [])

            if timestamp_idx >= len(time_series):
                continue

            entry = time_series[timestamp_idx]
            signal_quality = entry.get('signal_quality', {})
            rsrp = signal_quality.get('rsrp_dbm', float('-inf'))

            if rsrp > best_rsrp:
                best_rsrp = rsrp
                best_satellite_id = int(sat_id_str)
                best_satellite_data = entry

        if not best_satellite_id:
            return None

        # 構建 SatelliteState (with temporal features)
        return self._build_satellite_state(
            best_satellite_id, best_satellite_data, stage6_output, timestamp_idx=timestamp_idx
        )

    def extract_candidates(
        self,
        stage6_output: Stage6Output,
        timestamp_idx: int,
        serving_id: int,
        timestamp: Optional[str] = None
    ) -> List[SatelliteState]:
        """提取候選衛星（RSRP 次強的 K 個）

        SOURCE: Badini et al. (2024) IEEE TAES, Section III.B
                "Candidate satellites are the top-K neighbors by RSRP"

        FIXED (2025-10-24): Match candidates by timestamp instead of index
        - Old bug: Used timestamp_idx which caused misalignment between satellites
        - Example: Sat 53010 time_series[0] = "00:30:00", Sat 55316 time_series[0] = "01:01:00"
        - Fix: Match by actual timestamp string to ensure same time point

        Args:
            stage6_output: Stage 6 輸出數據
            timestamp_idx: 時間序列索引 (deprecated, kept for backward compatibility)
            serving_id: 服務衛星 ID（排除）
            timestamp: 實際時間戳 (NEW, preferred method)

        Returns:
            候選衛星列表（最多 max_candidates 個）
        """
        signal_analysis = stage6_output.signal_analysis
        if not signal_analysis:
            return []

        # 收集所有候選衛星（排除服務衛星）
        candidates = []
        for sat_id_str, sat_data in signal_analysis.items():
            sat_id = int(sat_id_str)
            if sat_id == serving_id:
                continue

            time_series = sat_data.get('time_series', [])

            # FIXED: Match by timestamp if provided, otherwise fall back to index
            entry = None
            if timestamp:
                # Find entry with matching timestamp
                for ts_entry in time_series:
                    if ts_entry.get('timestamp') == timestamp:
                        entry = ts_entry
                        break

                if not entry:
                    # This satellite doesn't have data at this timestamp
                    continue
            else:
                # Legacy behavior: use index
                if timestamp_idx >= len(time_series):
                    continue
                entry = time_series[timestamp_idx]

            signal_quality = entry.get('signal_quality', {})
            rsrp = signal_quality.get('rsrp_dbm', float('-inf'))

            # 最低 RSRP 門檻：-110 dBm
            # SOURCE: 3GPP TS 38.133 Section 10.1.16
            if rsrp < -110:
                continue

            satellite_state = self._build_satellite_state(
                sat_id, entry, stage6_output, timestamp_idx=timestamp_idx
            )
            if satellite_state:
                candidates.append((rsrp, satellite_state))

        # 按 RSRP 降序排序，取前 K 個
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_k_candidates = [sat for _, sat in candidates[:self.max_candidates]]

        return top_k_candidates

    def _build_satellite_state(
        self,
        satellite_id: int,
        time_entry: dict,
        stage6_output: Stage6Output,
        timestamp_idx: Optional[int] = None
    ) -> Optional[SatelliteState]:
        """構建 SatelliteState 對象（包含時間特徵）

        Args:
            satellite_id: 衛星 ID
            time_entry: 時間序列條目
            stage6_output: Stage 6 輸出（用於提取負載信息）
            timestamp_idx: 時間序列索引（用於計算時間特徵，None 時特徵為 0）

        Returns:
            SatelliteState 或 None
        """
        try:
            signal_quality = time_entry.get('signal_quality', {})
            # Note: actual field is 'physical_parameters', not 'geometry'
            physical_parameters = time_entry.get('physical_parameters', {})

            # Note: actual field is 'rs_sinr_db', not 'snr_db'
            snr_db = signal_quality.get('rs_sinr_db', signal_quality.get('snr_db', -10.0))

            # 提取負載信息（從 scenario_variants 或使用默認值）
            load_percent = self._get_satellite_load(satellite_id, stage6_output)

            # NEW (2025-10-24): Calculate temporal features
            temporal_features = {
                'rsrp_velocity': 0.0,
                'distance_velocity': 0.0,
                'predicted_rsrp_30s': signal_quality.get('rsrp_dbm', 0.0),
                'predicted_rsrp_60s': signal_quality.get('rsrp_dbm', 0.0)
            }

            # 如果有時間索引和時間序列，計算實際時間特徵
            if timestamp_idx is not None and timestamp_idx >= 0:
                sat_id_str = str(satellite_id)
                if sat_id_str in stage6_output.signal_analysis:
                    time_series = stage6_output.signal_analysis[sat_id_str].get('time_series', [])
                    if 0 <= timestamp_idx < len(time_series):
                        temporal_features = self.temporal_calculator.calculate_all_temporal_features(
                            time_series, timestamp_idx
                        )

            # Note: azimuth_deg is not available in actual data, using 0.0
            satellite_state = SatelliteState(
                satellite_id=satellite_id,
                rsrp_dbm=signal_quality.get('rsrp_dbm', -140.0),
                rsrq_db=signal_quality.get('rsrq_db', -20.0),
                snr_db=snr_db,
                distance_km=physical_parameters.get('distance_km', 0.0),
                elevation_deg=physical_parameters.get('elevation_deg', 0.0),
                azimuth_deg=0.0,  # Not available in actual data
                load_percent=load_percent,
                # NEW: Temporal features
                rsrp_velocity=temporal_features['rsrp_velocity'],
                distance_velocity=temporal_features['distance_velocity'],
                predicted_rsrp_30s=temporal_features['predicted_rsrp_30s'],
                predicted_rsrp_60s=temporal_features['predicted_rsrp_60s']
            )

            return satellite_state

        except Exception as e:
            logger.error(f"Error building satellite state for {satellite_id}: {e}")
            return None

    def _get_satellite_load(
        self,
        satellite_id: int,
        stage6_output: Stage6Output
    ) -> float:
        """獲取衛星負載百分比

        如果 scenario_variants 包含負載信息，則使用；否則使用默認值

        Args:
            satellite_id: 衛星 ID
            stage6_output: Stage 6 輸出

        Returns:
            負載百分比 (0-100)
        """
        # 嘗試從 scenario_variants 提取負載
        if stage6_output.scenario_variants:
            satellite_load = stage6_output.scenario_variants.get('satellite_load', {})
            sat_id_str = str(satellite_id)
            if sat_id_str in satellite_load:
                return satellite_load[sat_id_str].get('load_percent', 50.0)

        # 默認負載：50%
        # SOURCE: Proposal 002 - 均勻負載默認值
        return 50.0

    def extract_qos_requirements(
        self,
        stage6_output: Stage6Output
    ) -> Optional[QoSRequirements]:
        """從 scenario_variants 提取 QoS 需求

        SOURCE: Proposal 002 - Scenario Diversity
                4 traffic types: voip, video, iot, best_effort

        Args:
            stage6_output: Stage 6 輸出

        Returns:
            QoSRequirements 或 None
        """
        if not stage6_output.scenario_variants:
            # 使用默認 QoS（best_effort）
            return QoSRequirements(
                traffic_type='best_effort',
                min_throughput_mbps=1.0,
                max_latency_ms=1000.0,
                max_packet_loss_rate=0.05
            )

        traffic_profile = stage6_output.scenario_variants.get('traffic_profile', {})
        traffic_type = traffic_profile.get('type', 'best_effort')

        # 根據 traffic type 設置 QoS 參數
        # SOURCE: 3GPP TS 22.261 v19.5.0 Table 7.2.1-1
        qos_params = {
            'voip': {
                'min_throughput_mbps': 0.1,  # 100 kbps
                'max_latency_ms': 100.0,      # < 100 ms
                'max_packet_loss_rate': 0.01  # < 1%
            },
            'video': {
                'min_throughput_mbps': 5.0,   # 5 Mbps
                'max_latency_ms': 300.0,       # < 300 ms
                'max_packet_loss_rate': 0.02   # < 2%
            },
            'iot': {
                'min_throughput_mbps': 0.01,  # 10 kbps
                'max_latency_ms': 1000.0,      # < 1 s
                'max_packet_loss_rate': 0.05   # < 5%
            },
            'best_effort': {
                'min_throughput_mbps': 1.0,   # 1 Mbps
                'max_latency_ms': 1000.0,      # < 1 s
                'max_packet_loss_rate': 0.05   # < 5%
            }
        }

        params = qos_params.get(traffic_type, qos_params['best_effort'])

        return QoSRequirements(
            traffic_type=traffic_type,
            **params
        )

    def extract_network_load(
        self,
        stage6_output: Stage6Output
    ) -> Optional[NetworkLoadState]:
        """從 scenario_variants 提取網絡負載狀態

        SOURCE: Proposal 002 - Scenario Diversity
                3 load patterns: uniform, concentrated, dynamic

        Args:
            stage6_output: Stage 6 輸出

        Returns:
            NetworkLoadState 或 None
        """
        if not stage6_output.scenario_variants:
            # 使用默認負載（uniform, 50%）
            return NetworkLoadState(
                load_pattern='uniform',
                avg_load_percent=50.0,
                max_load_percent=50.0
            )

        satellite_load = stage6_output.scenario_variants.get('satellite_load', {})
        load_pattern = satellite_load.get('pattern', 'uniform')

        # 計算平均和最大負載
        load_values = [
            sat_data.get('load_percent', 50.0)
            for sat_data in satellite_load.get('satellites', {}).values()
        ]

        if not load_values:
            avg_load = 50.0
            max_load = 50.0
        else:
            avg_load = np.mean(load_values)
            max_load = np.max(load_values)

        return NetworkLoadState(
            load_pattern=load_pattern,
            avg_load_percent=float(avg_load),
            max_load_percent=float(max_load)
        )

    def extract_time_features(
        self,
        stage6_output: Stage6Output,
        timestamp_idx: int,
        satellite_id: int
    ) -> Optional[TimeFeatures]:
        """提取時間特徵

        Args:
            stage6_output: Stage 6 輸出
            timestamp_idx: 時間序列索引
            satellite_id: 衛星 ID

        Returns:
            TimeFeatures 或 None
        """
        try:
            sat_id_str = str(satellite_id)
            time_series = stage6_output.signal_analysis[sat_id_str]['time_series']
            entry = time_series[timestamp_idx]

            timestamp = entry.get('timestamp', 0)

            # 解析為 datetime
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromtimestamp(timestamp)

            return TimeFeatures(
                timestamp=timestamp if isinstance(timestamp, (int, float)) else dt.timestamp(),
                hour_of_day=dt.hour,
                day_of_week=dt.weekday()
            )

        except Exception as e:
            logger.error(f"Error extracting time features: {e}")
            # 返回默認值（避免失敗）
            return TimeFeatures(
                timestamp=0.0,
                hour_of_day=12,
                day_of_week=0
            )


def main():
    """測試 State Extractor"""
    logging.basicConfig(level=logging.INFO)

    from .json_parser import Stage6OutputParser

    # 解析測試文件
    parser = Stage6OutputParser()
    test_file = "data/outputs/stage6/stage6_research_optimization_20251020_122405.json"

    output = parser.parse_file(test_file)
    if not output:
        print("❌ Failed to parse test file")
        return

    # 提取狀態
    extractor = StateExtractor(max_candidates=5)
    state = extractor.extract_state(output, timestamp_idx=0)

    if state:
        print(f"✅ Extracted RL State:")
        print(f"   Serving Satellite: {state.serving_satellite.satellite_id}")
        print(f"     RSRP: {state.serving_satellite.rsrp_dbm:.2f} dBm")
        print(f"   Candidates: {len(state.candidate_satellites)}")
        for i, cand in enumerate(state.candidate_satellites, 1):
            print(f"     {i}. Sat {cand.satellite_id}: RSRP={cand.rsrp_dbm:.2f} dBm")
        print(f"   QoS: {state.qos_requirements.traffic_type if state.qos_requirements else 'None'}")
        print(f"   State Vector Shape: {state.to_numpy().shape}")
    else:
        print("❌ Failed to extract state")


if __name__ == "__main__":
    main()
