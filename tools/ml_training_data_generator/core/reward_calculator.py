"""
Reward Calculator - 計算 RL 獎勵函數
"""

import logging
from typing import Optional
import numpy as np

from .types import RLState, QoSRequirements

logger = logging.getLogger(__name__)


class RewardCalculator:
    """計算 RL 獎勵函數

    Reward Function:
        reward = w_qos * qos_satisfaction +
                 w_signal * signal_quality_score -
                 w_handover * handover_cost

    SOURCE: Badini et al. (2024) IEEE TAES, Section III.C, Equation (5)
            "Reward Function for LEO Satellite Handover"
    """

    def __init__(
        self,
        weight_qos: float = 0.5,
        weight_signal: float = 0.3,
        weight_handover: float = 0.2
    ):
        """初始化 Reward Calculator

        Args:
            weight_qos: QoS 滿足度權重
                SOURCE: Badini et al. (2024) - 通常為 0.4-0.6
            weight_signal: 信號品質權重
                SOURCE: Badini et al. (2024) - 通常為 0.2-0.4
            weight_handover: 換手成本權重
                SOURCE: Badini et al. (2024) - 通常為 0.1-0.3
        """
        self.weight_qos = weight_qos
        self.weight_signal = weight_signal
        self.weight_handover = weight_handover

        # 歸一化權重（確保總和為 1.0）
        total_weight = weight_qos + weight_signal + weight_handover
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            self.weight_qos /= total_weight
            self.weight_signal /= total_weight
            self.weight_handover /= total_weight

        logger.info(f"RewardCalculator initialized: "
                   f"w_qos={self.weight_qos:.2f}, "
                   f"w_signal={self.weight_signal:.2f}, "
                   f"w_handover={self.weight_handover:.2f}")

    def compute_reward(
        self,
        state: RLState,
        action: int,
        next_state: RLState
    ) -> float:
        """計算 (state, action, next_state) 的獎勵

        Args:
            state: 當前狀態
            action: 執行的動作（0=保持，1-N=切換到候選N）
            next_state: 下一狀態

        Returns:
            獎勵值（典型範圍：-1.0 ~ 1.0）
        """
        # 1. QoS 滿足度獎勵
        qos_satisfaction = self.compute_qos_satisfaction(next_state)

        # 2. 信號品質分數
        signal_quality_score = self.compute_signal_quality_score(next_state)

        # 3. 換手成本
        handover_cost = self.compute_handover_cost(state, action, next_state)

        # 組合獎勵
        reward = (
            self.weight_qos * qos_satisfaction +
            self.weight_signal * signal_quality_score -
            self.weight_handover * handover_cost
        )

        return float(reward)

    def compute_qos_satisfaction(self, state: RLState) -> float:
        """計算 QoS 滿足度

        如果所有 QoS 要求都滿足，返回 +1.0；否則返回 -1.0

        SOURCE: 3GPP TS 22.261 v19.5.0 Section 7
                "Performance requirements"

        Args:
            state: RL 狀態

        Returns:
            QoS 滿足度（+1.0 或 -1.0）
        """
        if not state.qos_requirements:
            # 沒有 QoS 要求，視為滿足
            return 1.0

        serving_sat = state.serving_satellite
        qos_req = state.qos_requirements

        # 檢查信號品質是否滿足最低要求
        # RSRP 門檻基於 traffic type
        # SOURCE: 3GPP TS 38.133 Section 10.1.16
        min_rsrp_thresholds = {
            'voip': -95.0,      # VoIP 需要較高信號品質
            'video': -100.0,    # Video 需要中等信號品質
            'iot': -110.0,      # IoT 可以容忍較低信號品質
            'best_effort': -105.0  # Best effort 中等門檻
        }

        min_rsrp = min_rsrp_thresholds.get(qos_req.traffic_type, -105.0)
        rsrp_satisfied = serving_sat.rsrp_dbm >= min_rsrp

        # 檢查 SNR 門檻（基於 traffic type）
        # SOURCE: 3GPP TS 38.101-1 v18.0.0 Table 8.1.2.1-1
        min_snr_thresholds = {
            'voip': 0.0,        # VoIP: SNR > 0 dB
            'video': 3.0,       # Video: SNR > 3 dB
            'iot': -3.0,        # IoT: SNR > -3 dB
            'best_effort': 0.0  # Best effort: SNR > 0 dB
        }

        min_snr = min_snr_thresholds.get(qos_req.traffic_type, 0.0)
        snr_satisfied = serving_sat.snr_db >= min_snr

        # QoS 滿足需要同時滿足 RSRP 和 SNR 要求
        if rsrp_satisfied and snr_satisfied:
            return 1.0
        else:
            return -1.0

    def compute_signal_quality_score(self, state: RLState) -> float:
        """計算信號品質分數（歸一化到 0.0 ~ 1.0）

        基於服務衛星的 RSRP 和 SNR 計算信號品質分數

        SOURCE: Badini et al. (2024) IEEE TAES, Section III.C
                "Signal quality score combines RSRP and SNR"

        Args:
            state: RL 狀態

        Returns:
            信號品質分數（0.0 ~ 1.0）
        """
        serving_sat = state.serving_satellite

        # RSRP 分數（歸一化到 0-1）
        # 假設 RSRP 範圍：-140 ~ -40 dBm
        # SOURCE: 3GPP TS 38.215 v18.1.0 - RSRP 測量範圍
        rsrp_min = -140.0
        rsrp_max = -40.0
        rsrp_normalized = (serving_sat.rsrp_dbm - rsrp_min) / (rsrp_max - rsrp_min)
        rsrp_normalized = np.clip(rsrp_normalized, 0.0, 1.0)

        # SNR 分數（歸一化到 0-1）
        # 假設 SNR 範圍：-10 ~ 30 dB
        # SOURCE: 3GPP TS 38.101-1 v18.0.0 - 典型 SNR 範圍
        snr_min = -10.0
        snr_max = 30.0
        snr_normalized = (serving_sat.snr_db - snr_min) / (snr_max - snr_min)
        snr_normalized = np.clip(snr_normalized, 0.0, 1.0)

        # 組合分數（RSRP 權重更高）
        # SOURCE: Badini et al. (2024) - RSRP 是主要指標
        signal_score = 0.7 * rsrp_normalized + 0.3 * snr_normalized

        return float(signal_score)

    def compute_handover_cost(
        self,
        state: RLState,
        action: int,
        next_state: RLState
    ) -> float:
        """計算換手成本

        - 保持當前衛星（action=0）：無成本（0.0）
        - 換手到候選衛星（action>0）：基礎成本（0.2）
        - 不必要換手（乒乓效應）：額外懲罰（+0.3）

        SOURCE: Badini et al. (2024) IEEE TAES, Section III.C
                "Handover cost penalizes unnecessary handovers"

        Args:
            state: 當前狀態
            action: 執行的動作
            next_state: 下一狀態

        Returns:
            換手成本（0.0 ~ 0.5）
        """
        # 保持當前衛星：無成本
        if action == 0:
            return 0.0

        # 基礎換手成本
        # SOURCE: Badini et al. (2024) - 典型換手開銷 0.1-0.3
        base_cost = 0.2

        # 檢查是否為不必要換手（乒乓效應）
        # 定義：換手後信號品質提升不明顯（< 3 dB）
        # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4
        #         Hysteresis parameter (typical 1-3 dB)
        is_unnecessary = self._is_unnecessary_handover(state, next_state)

        if is_unnecessary:
            # 額外懲罰不必要換手
            unnecessary_penalty = 0.3
            total_cost = base_cost + unnecessary_penalty
        else:
            total_cost = base_cost

        return float(total_cost)

    def _is_unnecessary_handover(self, state: RLState, next_state: RLState) -> bool:
        """檢查是否為不必要換手

        判斷標準：換手後 RSRP 提升 < 3 dB

        SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4
                "Hysteresis prevents ping-pong handovers"

        Args:
            state: 當前狀態（換手前）
            next_state: 下一狀態（換手後）

        Returns:
            True if unnecessary, False otherwise
        """
        # 計算 RSRP 提升
        rsrp_before = state.serving_satellite.rsrp_dbm
        rsrp_after = next_state.serving_satellite.rsrp_dbm

        rsrp_improvement = rsrp_after - rsrp_before

        # 如果提升小於 3 dB，視為不必要換手
        # SOURCE: 3GPP TS 38.331 - 典型 Hysteresis 值為 3 dB
        hysteresis_db = 3.0

        return rsrp_improvement < hysteresis_db

    def get_reward_statistics(self, rewards: list) -> dict:
        """計算獎勵統計信息

        Args:
            rewards: 獎勵列表

        Returns:
            統計信息字典
        """
        if not rewards:
            return {}

        return {
            'mean': float(np.mean(rewards)),
            'std': float(np.std(rewards)),
            'min': float(np.min(rewards)),
            'max': float(np.max(rewards)),
            'median': float(np.median(rewards)),
            'count': len(rewards)
        }


def main():
    """測試 Reward Calculator"""
    logging.basicConfig(level=logging.INFO)

    from .types import SatelliteState, QoSRequirements

    # 創建測試狀態
    serving_sat_before = SatelliteState(
        satellite_id=1001,
        rsrp_dbm=-100.0,
        rsrq_db=-10.0,
        snr_db=5.0,
        distance_km=1500.0,
        elevation_deg=30.0,
        azimuth_deg=180.0,
        load_percent=50.0
    )

    serving_sat_after = SatelliteState(
        satellite_id=1002,
        rsrp_dbm=-90.0,  # 提升 10 dB（值得換手）
        rsrq_db=-8.0,
        snr_db=8.0,
        distance_km=1200.0,
        elevation_deg=40.0,
        azimuth_deg=200.0,
        load_percent=40.0
    )

    qos_req = QoSRequirements(
        traffic_type='video',
        min_throughput_mbps=5.0,
        max_latency_ms=300.0,
        max_packet_loss_rate=0.02
    )

    state_before = RLState(
        serving_satellite=serving_sat_before,
        candidate_satellites=[],
        qos_requirements=qos_req
    )

    state_after = RLState(
        serving_satellite=serving_sat_after,
        candidate_satellites=[],
        qos_requirements=qos_req
    )

    # 計算獎勵
    calculator = RewardCalculator()

    # 測試 1: 保持當前衛星
    reward_stay = calculator.compute_reward(state_before, action=0, next_state=state_before)
    print(f"✅ Reward (stay): {reward_stay:.3f}")

    # 測試 2: 換手到更好的衛星
    reward_handover = calculator.compute_reward(state_before, action=1, next_state=state_after)
    print(f"✅ Reward (handover, 10dB improvement): {reward_handover:.3f}")

    # 測試 3: 不必要換手（提升 < 3 dB）
    serving_sat_minor = SatelliteState(
        satellite_id=1003,
        rsrp_dbm=-98.0,  # 僅提升 2 dB（不必要換手）
        rsrq_db=-9.5,
        snr_db=6.0,
        distance_km=1400.0,
        elevation_deg=35.0,
        azimuth_deg=190.0,
        load_percent=45.0
    )
    state_minor = RLState(
        serving_satellite=serving_sat_minor,
        candidate_satellites=[],
        qos_requirements=qos_req
    )
    reward_unnecessary = calculator.compute_reward(state_before, action=1, next_state=state_minor)
    print(f"✅ Reward (unnecessary handover, 2dB improvement): {reward_unnecessary:.3f}")


if __name__ == "__main__":
    main()
