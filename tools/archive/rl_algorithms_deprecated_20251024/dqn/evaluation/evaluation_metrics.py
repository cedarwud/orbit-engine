"""
Evaluation Metrics

標準化評估指標計算器，用於評估換手策略性能。

SOURCE: Proposal 003, Phase 4 - Evaluation Framework
"""

import numpy as np
from typing import List, Dict


class EvaluationMetrics:
    """標準評估指標計算器

    SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B
            "Performance Evaluation Metrics"
    """

    @staticmethod
    def calculate_handover_metrics(handover_events: List[dict]) -> dict:
        """計算換手相關指標

        Args:
            handover_events: 換手事件列表，每個事件包含:
                - source_satellite: 源衛星 ID
                - target_satellite: 目標衛星 ID
                - timestamp: 時間戳（秒）

        Returns:
            metrics (dict): 換手指標
                - total_handovers: 總換手次數
                - handover_rate: 每分鐘換手率
                - unnecessary_handovers: 不必要換手次數
                - unnecessary_handover_rate: 不必要換手率

        SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B.1
                "Handover Performance Metrics"
        """
        if not handover_events:
            return {
                'total_handovers': 0,
                'handover_rate': 0.0,
                'unnecessary_handovers': 0,
                'unnecessary_handover_rate': 0.0
            }

        total_handovers = len(handover_events)

        # 計算不必要換手（乒乓效應）
        # 定義: 60秒內切回原衛星
        # SOURCE: 3GPP TS 36.839 Section 6.1.2.2 - Ping-pong handover
        unnecessary_handovers = 0
        for i, event in enumerate(handover_events[:-1]):
            next_event = handover_events[i + 1]
            time_diff = next_event['timestamp'] - event['timestamp']

            # 檢查是否在 60 秒內切回原衛星
            if (next_event['target_satellite'] == event['source_satellite'] and
                time_diff < 60):
                unnecessary_handovers += 1

        # 計算換手率（每分鐘）
        total_time = handover_events[-1]['timestamp'] - handover_events[0]['timestamp']
        handover_rate = (total_handovers / total_time) * 60 if total_time > 0 else 0.0

        return {
            'total_handovers': total_handovers,
            'handover_rate': handover_rate,
            'unnecessary_handovers': unnecessary_handovers,
            'unnecessary_handover_rate': unnecessary_handovers / total_handovers if total_handovers > 0 else 0.0
        }

    @staticmethod
    def calculate_qos_metrics(signal_quality_data: List[dict]) -> dict:
        """計算 QoS 相關指標

        Args:
            signal_quality_data: 信號品質數據列表，每個包含:
                - rsrp_dbm: RSRP (dBm)
                - snr_db: SNR (dB)

        Returns:
            metrics (dict): QoS 指標
                - avg_rsrp: 平均 RSRP (dBm)
                - avg_snr: 平均 SNR (dB)
                - min_rsrp: 最小 RSRP (dBm)
                - max_rsrp: 最大 RSRP (dBm)
                - coverage_rate: 覆蓋率（RSRP > -110 dBm）
                - qos_satisfaction_rate: QoS 滿足率

        SOURCE: 3GPP TS 38.133 Section 10.1.16 - RSRP measurement requirements
        """
        if not signal_quality_data:
            return {
                'avg_rsrp': 0.0,
                'avg_snr': 0.0,
                'min_rsrp': 0.0,
                'max_rsrp': 0.0,
                'coverage_rate': 0.0,
                'qos_satisfaction_rate': 0.0
            }

        rsrp_values = [d['rsrp_dbm'] for d in signal_quality_data]
        snr_values = [d['snr_db'] for d in signal_quality_data]

        # 3GPP 覆蓋門檻: RSRP > -110 dBm 視為可服務
        # SOURCE: 3GPP TS 38.133 Section 10.1.16
        coverage_threshold = -110.0
        coverage_count = sum(1 for rsrp in rsrp_values if rsrp > coverage_threshold)

        # QoS 滿足條件: RSRP > -95 dBm AND SNR > 0 dB
        # SOURCE: 3GPP TS 38.331 Section 5.5.4.2 - Measurement report criteria
        qos_rsrp_threshold = -95.0
        qos_snr_threshold = 0.0
        qos_satisfied = sum(
            1 for rsrp, snr in zip(rsrp_values, snr_values)
            if rsrp > qos_rsrp_threshold and snr > qos_snr_threshold
        )

        return {
            'avg_rsrp': float(np.mean(rsrp_values)),
            'avg_snr': float(np.mean(snr_values)),
            'min_rsrp': float(np.min(rsrp_values)),
            'max_rsrp': float(np.max(rsrp_values)),
            'coverage_rate': coverage_count / len(rsrp_values),
            'qos_satisfaction_rate': qos_satisfied / len(rsrp_values)
        }

    @staticmethod
    def calculate_reward_metrics(rewards: List[float]) -> dict:
        """計算獎勵相關指標

        Args:
            rewards: 獎勵值列表

        Returns:
            metrics (dict): 獎勵指標
                - total_reward: 總獎勵
                - avg_reward: 平均獎勵
                - reward_std: 獎勵標準差
                - min_reward: 最小獎勵
                - max_reward: 最大獎勵

        SOURCE: Henderson et al. (2018) AAAI
                "Deep Reinforcement Learning that Matters"
        """
        if not rewards:
            return {
                'total_reward': 0.0,
                'avg_reward': 0.0,
                'reward_std': 0.0,
                'min_reward': 0.0,
                'max_reward': 0.0
            }

        return {
            'total_reward': float(np.sum(rewards)),
            'avg_reward': float(np.mean(rewards)),
            'reward_std': float(np.std(rewards)),
            'min_reward': float(np.min(rewards)),
            'max_reward': float(np.max(rewards))
        }


def test_evaluation_metrics():
    """測試評估指標計算"""
    print("Testing EvaluationMetrics...\n")

    # 測試換手指標
    print("1️⃣ Testing handover metrics...")
    handover_events = [
        {'source_satellite': 1, 'target_satellite': 2, 'timestamp': 0.0},
        {'source_satellite': 2, 'target_satellite': 1, 'timestamp': 30.0},  # 不必要換手
        {'source_satellite': 1, 'target_satellite': 3, 'timestamp': 100.0},
        {'source_satellite': 3, 'target_satellite': 4, 'timestamp': 200.0},
    ]
    metrics = EvaluationMetrics.calculate_handover_metrics(handover_events)
    print(f"   Total handovers: {metrics['total_handovers']}")
    print(f"   Unnecessary handovers: {metrics['unnecessary_handovers']}")
    print(f"   Unnecessary HO rate: {metrics['unnecessary_handover_rate']:.2%}")
    print(f"   Handover rate: {metrics['handover_rate']:.3f} per minute")

    assert metrics['total_handovers'] == 4
    assert metrics['unnecessary_handovers'] == 1
    assert abs(metrics['unnecessary_handover_rate'] - 0.25) < 0.01
    print("   ✅ Handover metrics test passed\n")

    # 測試 QoS 指標
    print("2️⃣ Testing QoS metrics...")
    qos_data = [
        {'rsrp_dbm': -35.0, 'snr_db': 5.0},
        {'rsrp_dbm': -90.0, 'snr_db': 2.0},
        {'rsrp_dbm': -120.0, 'snr_db': -5.0},  # 不滿足 coverage
        {'rsrp_dbm': -100.0, 'snr_db': -2.0},  # 滿足 coverage，不滿足 QoS
    ]
    metrics = EvaluationMetrics.calculate_qos_metrics(qos_data)
    print(f"   Avg RSRP: {metrics['avg_rsrp']:.2f} dBm")
    print(f"   Avg SNR: {metrics['avg_snr']:.2f} dB")
    print(f"   Coverage rate: {metrics['coverage_rate']:.2%}")
    print(f"   QoS satisfaction rate: {metrics['qos_satisfaction_rate']:.2%}")

    assert abs(metrics['avg_rsrp'] - (-86.25)) < 0.1
    assert abs(metrics['coverage_rate'] - 0.75) < 0.01  # 3/4 滿足 coverage
    assert abs(metrics['qos_satisfaction_rate'] - 0.5) < 0.01  # 2/4 滿足 QoS
    print("   ✅ QoS metrics test passed\n")

    # 測試獎勵指標
    print("3️⃣ Testing reward metrics...")
    rewards = [10.0, 15.0, 8.0, 12.0, 20.0]
    metrics = EvaluationMetrics.calculate_reward_metrics(rewards)
    print(f"   Total reward: {metrics['total_reward']:.2f}")
    print(f"   Avg reward: {metrics['avg_reward']:.2f}")
    print(f"   Reward std: {metrics['reward_std']:.2f}")
    print(f"   Min/Max: {metrics['min_reward']:.2f} / {metrics['max_reward']:.2f}")

    assert abs(metrics['total_reward'] - 65.0) < 0.1
    assert abs(metrics['avg_reward'] - 13.0) < 0.1
    print("   ✅ Reward metrics test passed\n")

    print("✅ All tests passed!")


if __name__ == "__main__":
    test_evaluation_metrics()
