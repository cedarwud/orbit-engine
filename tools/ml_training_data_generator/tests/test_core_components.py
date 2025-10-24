"""
Core Components Unit Tests

測試 ML Data Generator 的核心組件
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import json
import tempfile

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tools.ml_training_data_generator.core.types import (
    SatelliteState, QoSRequirements, NetworkLoadState,
    TimeFeatures, RLState, Transition
)
from tools.ml_training_data_generator.core.state_extractor import StateExtractor
from tools.ml_training_data_generator.core.reward_calculator import RewardCalculator


class TestSatelliteState:
    """測試 SatelliteState 數據類型"""

    def test_satellite_state_creation(self):
        """測試創建 SatelliteState"""
        sat_state = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-100.0,
            rsrq_db=-10.0,
            snr_db=5.0,
            distance_km=1500.0,
            elevation_deg=30.0,
            azimuth_deg=180.0,
            load_percent=50.0
        )

        assert sat_state.satellite_id == 1001
        assert sat_state.rsrp_dbm == -100.0
        assert sat_state.snr_db == 5.0

    def test_satellite_state_to_numpy(self):
        """測試 SatelliteState 轉換為 numpy array"""
        sat_state = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-100.0,
            rsrq_db=-10.0,
            snr_db=5.0,
            distance_km=1500.0,
            elevation_deg=30.0,
            azimuth_deg=180.0,
            load_percent=50.0
        )

        arr = sat_state.to_numpy()

        assert arr.shape == (7,)
        assert arr[0] == -100.0  # RSRP
        assert arr[2] == 5.0     # SNR
        assert arr.dtype == np.float32


class TestQoSRequirements:
    """測試 QoSRequirements 數據類型"""

    def test_qos_requirements_creation(self):
        """測試創建 QoSRequirements"""
        qos = QoSRequirements(
            traffic_type='video',
            min_throughput_mbps=5.0,
            max_latency_ms=300.0,
            max_packet_loss_rate=0.02
        )

        assert qos.traffic_type == 'video'
        assert qos.min_throughput_mbps == 5.0

    def test_qos_to_numpy(self):
        """測試 QoSRequirements 轉換為 numpy array"""
        qos = QoSRequirements(
            traffic_type='video',
            min_throughput_mbps=5.0,
            max_latency_ms=300.0,
            max_packet_loss_rate=0.02
        )

        arr = qos.to_numpy()

        assert arr.shape == (4,)
        assert arr[0] == 1  # video = 1
        assert arr[1] == 5.0


class TestRLState:
    """測試 RLState 數據類型"""

    def test_rl_state_creation(self):
        """測試創建 RLState"""
        serving_sat = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-100.0,
            rsrq_db=-10.0,
            snr_db=5.0,
            distance_km=1500.0,
            elevation_deg=30.0,
            azimuth_deg=180.0,
            load_percent=50.0
        )

        rl_state = RLState(
            serving_satellite=serving_sat,
            candidate_satellites=[]
        )

        assert rl_state.serving_satellite.satellite_id == 1001
        assert len(rl_state.candidate_satellites) == 0

    def test_rl_state_to_numpy(self):
        """測試 RLState 轉換為 numpy array"""
        serving_sat = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-100.0,
            rsrq_db=-10.0,
            snr_db=5.0,
            distance_km=1500.0,
            elevation_deg=30.0,
            azimuth_deg=180.0,
            load_percent=50.0
        )

        candidate_sat = SatelliteState(
            satellite_id=1002,
            rsrp_dbm=-95.0,
            rsrq_db=-9.0,
            snr_db=6.0,
            distance_km=1400.0,
            elevation_deg=35.0,
            azimuth_deg=190.0,
            load_percent=45.0
        )

        qos = QoSRequirements(
            traffic_type='video',
            min_throughput_mbps=5.0,
            max_latency_ms=300.0,
            max_packet_loss_rate=0.02
        )

        rl_state = RLState(
            serving_satellite=serving_sat,
            candidate_satellites=[candidate_sat],
            qos_requirements=qos
        )

        arr = rl_state.to_numpy()

        # 狀態向量應該是 53 維
        assert arr.shape == (53,)
        assert arr.dtype == np.float32

        # 檢查服務衛星 RSRP
        assert arr[0] == -100.0

        # 檢查第一個候選衛星 RSRP
        assert arr[7] == -95.0

    def test_rl_state_padding(self):
        """測試 RLState 候選衛星 padding"""
        serving_sat = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-100.0,
            rsrq_db=-10.0,
            snr_db=5.0,
            distance_km=1500.0,
            elevation_deg=30.0,
            azimuth_deg=180.0,
            load_percent=50.0
        )

        # 只有 1 個候選衛星，應該 padding 到 5 個
        rl_state = RLState(
            serving_satellite=serving_sat,
            candidate_satellites=[]  # 無候選
        )

        arr = rl_state.to_numpy()

        # 候選衛星位置應該是 0（padding）
        assert np.all(arr[7:7+35] == 0.0)


class TestRewardCalculator:
    """測試 RewardCalculator"""

    def test_reward_calculator_initialization(self):
        """測試 RewardCalculator 初始化"""
        calculator = RewardCalculator(
            weight_qos=0.5,
            weight_signal=0.3,
            weight_handover=0.2
        )

        assert calculator.weight_qos == 0.5
        assert calculator.weight_signal == 0.3
        assert calculator.weight_handover == 0.2

    def test_weight_normalization(self):
        """測試權重自動歸一化"""
        calculator = RewardCalculator(
            weight_qos=1.0,
            weight_signal=1.0,
            weight_handover=1.0
        )

        # 應該自動歸一化為 1/3 each
        total_weight = calculator.weight_qos + calculator.weight_signal + calculator.weight_handover
        assert abs(total_weight - 1.0) < 0.01

    def test_qos_satisfaction_satisfied(self):
        """測試 QoS 滿足情況"""
        calculator = RewardCalculator()

        serving_sat = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-90.0,  # Good signal
            rsrq_db=-8.0,
            snr_db=8.0,      # Good SNR
            distance_km=1200.0,
            elevation_deg=40.0,
            azimuth_deg=180.0,
            load_percent=50.0
        )

        qos = QoSRequirements(
            traffic_type='video',
            min_throughput_mbps=5.0,
            max_latency_ms=300.0,
            max_packet_loss_rate=0.02
        )

        state = RLState(
            serving_satellite=serving_sat,
            candidate_satellites=[],
            qos_requirements=qos
        )

        qos_satisfaction = calculator.compute_qos_satisfaction(state)

        # Video requires RSRP > -100 and SNR > 3, both satisfied
        assert qos_satisfaction == 1.0

    def test_qos_satisfaction_not_satisfied(self):
        """測試 QoS 不滿足情況"""
        calculator = RewardCalculator()

        serving_sat = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-115.0,  # Poor signal
            rsrq_db=-15.0,
            snr_db=-2.0,      # Poor SNR
            distance_km=2000.0,
            elevation_deg=15.0,
            azimuth_deg=180.0,
            load_percent=80.0
        )

        qos = QoSRequirements(
            traffic_type='video',
            min_throughput_mbps=5.0,
            max_latency_ms=300.0,
            max_packet_loss_rate=0.02
        )

        state = RLState(
            serving_satellite=serving_sat,
            candidate_satellites=[],
            qos_requirements=qos
        )

        qos_satisfaction = calculator.compute_qos_satisfaction(state)

        # Video requires RSRP > -100 and SNR > 3, both NOT satisfied
        assert qos_satisfaction == -1.0

    def test_signal_quality_score(self):
        """測試信號品質分數計算"""
        calculator = RewardCalculator()

        # Good signal
        good_sat = SatelliteState(
            satellite_id=1001,
            rsrp_dbm=-50.0,  # Near maximum
            rsrq_db=-5.0,
            snr_db=25.0,     # Near maximum
            distance_km=1000.0,
            elevation_deg=60.0,
            azimuth_deg=180.0,
            load_percent=30.0
        )

        good_state = RLState(
            serving_satellite=good_sat,
            candidate_satellites=[]
        )

        good_score = calculator.compute_signal_quality_score(good_state)

        # Good signal should have high score (close to 1.0)
        assert 0.8 < good_score <= 1.0

        # Poor signal
        poor_sat = SatelliteState(
            satellite_id=1002,
            rsrp_dbm=-130.0,  # Near minimum
            rsrq_db=-18.0,
            snr_db=-5.0,      # Near minimum
            distance_km=2500.0,
            elevation_deg=10.0,
            azimuth_deg=180.0,
            load_percent=90.0
        )

        poor_state = RLState(
            serving_satellite=poor_sat,
            candidate_satellites=[]
        )

        poor_score = calculator.compute_signal_quality_score(poor_state)

        # Poor signal should have low score (close to 0.0)
        assert 0.0 <= poor_score < 0.3

    def test_handover_cost_stay(self):
        """測試保持當前衛星的成本（應該為 0）"""
        calculator = RewardCalculator()

        state = RLState(
            serving_satellite=SatelliteState(
                satellite_id=1001,
                rsrp_dbm=-100.0,
                rsrq_db=-10.0,
                snr_db=5.0,
                distance_km=1500.0,
                elevation_deg=30.0,
                azimuth_deg=180.0,
                load_percent=50.0
            ),
            candidate_satellites=[]
        )

        action = 0  # Stay
        handover_cost = calculator.compute_handover_cost(state, action, state)

        assert handover_cost == 0.0

    def test_handover_cost_necessary(self):
        """測試必要換手成本"""
        calculator = RewardCalculator()

        state_before = RLState(
            serving_satellite=SatelliteState(
                satellite_id=1001,
                rsrp_dbm=-100.0,  # Poor signal
                rsrq_db=-12.0,
                snr_db=2.0,
                distance_km=1800.0,
                elevation_deg=25.0,
                azimuth_deg=180.0,
                load_percent=60.0
            ),
            candidate_satellites=[]
        )

        state_after = RLState(
            serving_satellite=SatelliteState(
                satellite_id=1002,
                rsrp_dbm=-85.0,  # Much better signal (+15 dB)
                rsrq_db=-7.0,
                snr_db=10.0,
                distance_km=1200.0,
                elevation_deg=45.0,
                azimuth_deg=200.0,
                load_percent=40.0
            ),
            candidate_satellites=[]
        )

        action = 1  # Handover
        handover_cost = calculator.compute_handover_cost(state_before, action, state_after)

        # Necessary handover: base cost only (0.2)
        assert handover_cost == 0.2

    def test_handover_cost_unnecessary(self):
        """測試不必要換手成本（乒乓效應）"""
        calculator = RewardCalculator()

        state_before = RLState(
            serving_satellite=SatelliteState(
                satellite_id=1001,
                rsrp_dbm=-100.0,
                rsrq_db=-10.0,
                snr_db=5.0,
                distance_km=1500.0,
                elevation_deg=30.0,
                azimuth_deg=180.0,
                load_percent=50.0
            ),
            candidate_satellites=[]
        )

        state_after = RLState(
            serving_satellite=SatelliteState(
                satellite_id=1002,
                rsrp_dbm=-98.0,  # Only +2 dB improvement (< 3 dB hysteresis)
                rsrq_db=-9.5,
                snr_db=6.0,
                distance_km=1450.0,
                elevation_deg=32.0,
                azimuth_deg=190.0,
                load_percent=48.0
            ),
            candidate_satellites=[]
        )

        action = 1  # Handover
        handover_cost = calculator.compute_handover_cost(state_before, action, state_after)

        # Unnecessary handover: base cost (0.2) + penalty (0.3) = 0.5
        assert handover_cost == 0.5

    def test_compute_reward_full(self):
        """測試完整獎勵計算"""
        calculator = RewardCalculator()

        # 創建一個換手場景：從弱信號切換到強信號
        state_before = RLState(
            serving_satellite=SatelliteState(
                satellite_id=1001,
                rsrp_dbm=-105.0,
                rsrq_db=-12.0,
                snr_db=2.0,
                distance_km=1800.0,
                elevation_deg=25.0,
                azimuth_deg=180.0,
                load_percent=70.0
            ),
            candidate_satellites=[],
            qos_requirements=QoSRequirements(
                traffic_type='video',
                min_throughput_mbps=5.0,
                max_latency_ms=300.0,
                max_packet_loss_rate=0.02
            )
        )

        state_after = RLState(
            serving_satellite=SatelliteState(
                satellite_id=1002,
                rsrp_dbm=-90.0,  # +15 dB improvement
                rsrq_db=-8.0,
                snr_db=8.0,
                distance_km=1200.0,
                elevation_deg=40.0,
                azimuth_deg=200.0,
                load_percent=45.0
            ),
            candidate_satellites=[],
            qos_requirements=QoSRequirements(
                traffic_type='video',
                min_throughput_mbps=5.0,
                max_latency_ms=300.0,
                max_packet_loss_rate=0.02
            )
        )

        action = 1  # Handover

        reward = calculator.compute_reward(state_before, action, state_after)

        # 換手到更好的衛星，獎勵應該為正
        assert reward > 0.0

        # 獎勵應該在合理範圍內（-1.0 ~ 1.0）
        assert -1.0 <= reward <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
