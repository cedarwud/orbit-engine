"""
數據類型定義

定義 ML Training Data Generator 使用的數據結構
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np


@dataclass
class SatelliteState:
    """單個衛星的狀態

    SOURCE: Badini et al. (2024) IEEE TAES, Section III.B
            "State Space Definition"

    ENHANCED (2025-10-24): Added temporal features for D2 predictive handover
    """
    # Instant features (7)
    satellite_id: int
    rsrp_dbm: float  # Reference Signal Received Power
    rsrq_db: float   # Reference Signal Received Quality
    snr_db: float    # Signal-to-Noise Ratio
    distance_km: float
    elevation_deg: float
    azimuth_deg: float
    load_percent: float  # Satellite load (0-100%)

    # Temporal features (4) - NEW
    rsrp_velocity: float = 0.0  # dB/s (signal quality trend)
    distance_velocity: float = 0.0  # km/s (satellite approach/recession)
    predicted_rsrp_30s: float = 0.0  # dBm (predicted RSRP at t+30s)
    predicted_rsrp_60s: float = 0.0  # dBm (predicted RSRP at t+60s)

    # SOURCE: Badini et al. (2024) - Velocity features capture signal dynamics
    # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a - D2 predictive intent

    def to_numpy(self) -> np.ndarray:
        """轉換為 numpy array (11 features)

        Feature order:
        [rsrp, rsrq, snr, distance, elevation, azimuth, load,
         rsrp_velocity, distance_velocity, predicted_rsrp_30s, predicted_rsrp_60s]
        """
        return np.array([
            self.rsrp_dbm,
            self.rsrq_db,
            self.snr_db,
            self.distance_km,
            self.elevation_deg,
            self.azimuth_deg,
            self.load_percent,
            self.rsrp_velocity,
            self.distance_velocity,
            self.predicted_rsrp_30s,
            self.predicted_rsrp_60s
        ], dtype=np.float32)


@dataclass
class QoSRequirements:
    """QoS 需求

    SOURCE: 3GPP TS 22.261 v19.5.0 Section 7
            "Performance requirements"
    """
    traffic_type: str  # 'voip', 'video', 'iot', 'best_effort'
    min_throughput_mbps: float
    max_latency_ms: float
    max_packet_loss_rate: float

    def to_numpy(self) -> np.ndarray:
        """轉換為 numpy array（編碼 traffic_type）"""
        # Traffic type encoding: voip=0, video=1, iot=2, best_effort=3
        traffic_type_map = {
            'voip': 0, 'video': 1, 'iot': 2, 'best_effort': 3
        }
        traffic_type_encoded = traffic_type_map.get(self.traffic_type, 3)

        return np.array([
            traffic_type_encoded,
            self.min_throughput_mbps,
            self.max_latency_ms,
            self.max_packet_loss_rate
        ], dtype=np.float32)


@dataclass
class NetworkLoadState:
    """網絡負載狀態

    SOURCE: Proposal 002 - Scenario Diversity
    """
    load_pattern: str  # 'uniform', 'concentrated', 'dynamic'
    avg_load_percent: float
    max_load_percent: float

    def to_numpy(self) -> np.ndarray:
        """轉換為 numpy array（編碼 load_pattern）"""
        # Load pattern encoding: uniform=0, concentrated=1, dynamic=2
        load_pattern_map = {
            'uniform': 0, 'concentrated': 1, 'dynamic': 2
        }
        load_pattern_encoded = load_pattern_map.get(self.load_pattern, 0)

        return np.array([
            load_pattern_encoded,
            self.avg_load_percent,
            self.max_load_percent
        ], dtype=np.float32)


@dataclass
class TimeFeatures:
    """時間特徵

    用於捕捉時間模式（如晝夜、週末效應）
    """
    timestamp: float  # Unix timestamp
    hour_of_day: int  # 0-23
    day_of_week: int  # 0-6 (Monday=0)

    def to_numpy(self) -> np.ndarray:
        """轉換為 numpy array（週期編碼）"""
        # Cyclic encoding for hour and day
        hour_sin = np.sin(2 * np.pi * self.hour_of_day / 24)
        hour_cos = np.cos(2 * np.pi * self.hour_of_day / 24)
        day_sin = np.sin(2 * np.pi * self.day_of_week / 7)
        day_cos = np.cos(2 * np.pi * self.day_of_week / 7)

        return np.array([
            hour_sin, hour_cos,
            day_sin, day_cos
        ], dtype=np.float32)


@dataclass
class RLState:
    """RL 狀態表示

    SOURCE: Badini et al. (2024) IEEE TAES, Section III.B
    """
    serving_satellite: SatelliteState
    candidate_satellites: List[SatelliteState] = field(default_factory=list)
    qos_requirements: Optional[QoSRequirements] = None
    network_load: Optional[NetworkLoadState] = None
    time_features: Optional[TimeFeatures] = None

    def to_numpy(self) -> np.ndarray:
        """轉換為 numpy array（用於神經網絡輸入）

        State vector composition (UPDATED 2025-10-24):
        - Serving satellite: 11 features (7 instant + 4 temporal)
        - Candidate satellites: 5 × 11 = 55 features (padded if < 5)
        - QoS requirements: 4 features
        - Network load: 3 features
        - Time features: 4 features
        Total: 11 + 55 + 4 + 3 + 4 = 77 features (+24 from baseline)
        """
        state_components = []

        # Serving satellite (11 features)
        state_components.append(self.serving_satellite.to_numpy())

        # Candidate satellites (5 × 11 = 55 features)
        max_candidates = 5
        for i in range(max_candidates):
            if i < len(self.candidate_satellites):
                state_components.append(self.candidate_satellites[i].to_numpy())
            else:
                # Padding with zeros
                state_components.append(np.zeros(11, dtype=np.float32))

        # QoS requirements (4 features)
        if self.qos_requirements:
            state_components.append(self.qos_requirements.to_numpy())
        else:
            state_components.append(np.zeros(4, dtype=np.float32))

        # Network load (3 features)
        if self.network_load:
            state_components.append(self.network_load.to_numpy())
        else:
            state_components.append(np.zeros(3, dtype=np.float32))

        # Time features (4 features)
        if self.time_features:
            state_components.append(self.time_features.to_numpy())
        else:
            state_components.append(np.zeros(4, dtype=np.float32))

        return np.concatenate(state_components)

    @property
    def state_dim(self) -> int:
        """返回狀態維度

        UPDATED (2025-10-24): 53 → 77 features
        Added 24 temporal features (4 per satellite × 6 satellites)
        """
        return 77


@dataclass
class Transition:
    """RL Transition (s, a, r, s', done)

    SOURCE: Sutton & Barto (2018) "Reinforcement Learning: An Introduction"
            Chapter 3: Finite Markov Decision Processes
    """
    state: RLState
    action: int  # 0=stay, 1-5=handover to candidate i
    reward: float
    next_state: RLState
    done: bool

    # Metadata (optional)
    timestamp: Optional[float] = None
    scenario_variant_id: Optional[str] = None
    episode_id: Optional[int] = None


@dataclass
class Stage6Output:
    """Stage 6 輸出數據結構（只讀）

    這個類只用於讀取 Stage 6 JSON 輸出，不修改原始數據。
    """
    file_path: str
    constellation: str
    start_time: str
    end_time: str
    signal_analysis: Dict[str, Any]
    scenario_variants: Optional[Dict[str, Any]] = None
    gpp_events: Optional[Dict[str, Any]] = None
    pool_verification: Optional[Dict[str, Any]] = None

    def get_available_satellites(self) -> List[int]:
        """獲取可用衛星列表"""
        if not self.signal_analysis:
            return []
        return [int(sat_id) for sat_id in self.signal_analysis.keys()]

    def get_time_series_length(self, satellite_id: int) -> int:
        """獲取時間序列長度"""
        sat_id_str = str(satellite_id)
        if sat_id_str not in self.signal_analysis:
            return 0
        return len(self.signal_analysis[sat_id_str].get('time_series', []))

    def get_a4_events_at_time(self, timestamp: str, serving_satellite_id: int) -> List[Dict[str, Any]]:
        """獲取指定時間和服務衛星的 A4 事件

        A4: Neighbour becomes better than threshold
        SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.5

        Args:
            timestamp: 時間戳
            serving_satellite_id: 服務衛星 ID

        Returns:
            A4 事件列表（可能有多個鄰居觸發）
        """
        if not self.gpp_events or 'a4_events' not in self.gpp_events:
            return []

        serving_id_str = str(serving_satellite_id)
        matching_events = []

        for event in self.gpp_events['a4_events']:
            if (event.get('timestamp') == timestamp and
                event.get('serving_satellite') == serving_id_str):
                matching_events.append(event)

        return matching_events

    def get_d2_events_at_time(self, timestamp: str, serving_satellite_id: int) -> List[Dict[str, Any]]:
        """獲取指定時間和服務衛星的 D2 事件

        D2: 換手決策事件（基於距離）
        SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a

        Args:
            timestamp: 時間戳
            serving_satellite_id: 服務衛星 ID

        Returns:
            D2 事件列表
        """
        if not self.gpp_events or 'd2_events' not in self.gpp_events:
            return []

        serving_id_str = str(serving_satellite_id)
        matching_events = []

        for event in self.gpp_events['d2_events']:
            if (event.get('timestamp') == timestamp and
                event.get('serving_satellite') == serving_id_str):
                matching_events.append(event)

        return matching_events


@dataclass
class DatasetStatistics:
    """數據集統計信息"""
    total_transitions: int
    num_episodes: int
    avg_episode_length: float
    scenario_variant_distribution: Dict[str, int]
    action_distribution: Dict[int, int]
    reward_stats: Dict[str, float]  # mean, std, min, max

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典（用於保存到 HDF5 metadata）"""
        return {
            'total_transitions': self.total_transitions,
            'num_episodes': self.num_episodes,
            'avg_episode_length': self.avg_episode_length,
            'scenario_variant_distribution': self.scenario_variant_distribution,
            'action_distribution': self.action_distribution,
            'reward_stats': self.reward_stats
        }
