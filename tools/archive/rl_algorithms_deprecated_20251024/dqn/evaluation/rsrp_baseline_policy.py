"""
RSRP Baseline Policy

貪婪 RSRP 策略，作為 DQN 的比較基準。

SOURCE: Proposal 003, Phase 4 - Evaluation Framework
"""

import numpy as np


class RSRPBaselinePolicy:
    """RSRP 貪婪策略 Baseline

    策略邏輯: 始終選擇 RSRP 最高的鄰居衛星（若優於當前服務衛星 + 遲滯門檻）

    這是一個簡單的貪婪策略，用於與 DQN 比較。

    SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.2
            "A3: Neighbour becomes offset better than serving"
            (簡化為貪婪策略，無時間窗和測量報告延遲)
    """

    def __init__(self, hysteresis_db: float = 3.0):
        """初始化 RSRP Baseline 策略

        Args:
            hysteresis_db: 遲滯門檻（避免乒乓效應）
                預設 3.0 dB 是 3GPP 典型值

        SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4
                "hysteresis" parameter in ReportConfigNR
        """
        self.hysteresis_db = hysteresis_db

    def select_action(self, state: np.ndarray) -> int:
        """選擇切換動作（貪婪策略）

        Args:
            state: 環境狀態向量 (53 維)
                狀態組成（參考 SatelliteHandoverEnv）:
                - [0:7]: Serving satellite 特徵 (RSRP, RSRQ, SNR, ...)
                - [7:42]: Candidate satellites 特徵 (5 candidates × 7 features)
                - [42:]: QoS, Network Load, Time features

        Returns:
            action (int): 0=保持當前衛星, 1-5=切換到候選衛星 1-5

        策略邏輯:
        1. 提取服務衛星和候選衛星的 RSRP
        2. 找到 RSRP 最高的候選衛星
        3. 如果 max_neighbor_rsrp > serving_rsrp + hysteresis_db，則切換
        4. 否則保持當前衛星

        SOURCE: 簡化版 3GPP A3 事件判斷邏輯
        """
        # 提取 RSRP 值（假設 RSRP 是每個衛星特徵的第一個值）
        # Serving satellite RSRP
        serving_rsrp = state[0]

        # Candidate satellites RSRP (5 candidates, each has 7 features)
        # Candidate 1: state[7], Candidate 2: state[14], ..., Candidate 5: state[35]
        candidate_rsrp = []
        for i in range(5):
            start_idx = 7 + i * 7
            rsrp = state[start_idx]
            candidate_rsrp.append(rsrp)

        candidate_rsrp = np.array(candidate_rsrp)

        # 找到 RSRP 最高的候選衛星
        max_neighbor_rsrp = np.max(candidate_rsrp)
        max_neighbor_idx = np.argmax(candidate_rsrp)

        # 貪婪策略 + 遲滯門檻
        # 只有當鄰居 RSRP 明顯優於當前服務衛星時才切換
        if max_neighbor_rsrp > serving_rsrp + self.hysteresis_db:
            return int(max_neighbor_idx + 1)  # Action 1-5 對應候選衛星 1-5
        else:
            return 0  # Action 0 = 保持當前衛星

    def select_action_greedy(self, state: np.ndarray) -> int:
        """Greedy action selection（與 select_action 相同，提供統一接口）

        這個方法提供與 DQN Agent 一致的接口，方便評估管道統一調用。

        Args:
            state: 環境狀態向量

        Returns:
            action: 選擇的動作
        """
        return self.select_action(state)


def test_rsrp_baseline():
    """測試 RSRP Baseline 策略"""
    print("Testing RSRPBaselinePolicy...\n")

    policy = RSRPBaselinePolicy(hysteresis_db=3.0)

    # 構建測試狀態（53 維）
    # 簡化: [serving_rsrp, candidate1_rsrp, ..., candidate5_rsrp, ...]

    # Test Case 1: 鄰居明顯更好 → 應該切換
    print("1️⃣ Test Case 1: Neighbor significantly better")
    state = np.zeros(53)
    state[0] = -40.0  # Serving satellite RSRP = -40 dBm
    state[7] = -30.0   # Candidate 1 RSRP = -30 dBm (better by 10 dB)
    state[14] = -50.0  # Candidate 2 RSRP = -50 dBm
    state[21] = -60.0  # Candidate 3 RSRP = -60 dBm
    state[28] = -70.0  # Candidate 4 RSRP = -70 dBm
    state[35] = -80.0  # Candidate 5 RSRP = -80 dBm

    action = policy.select_action(state)
    print(f"   Serving RSRP: {state[0]:.1f} dBm")
    print(f"   Best neighbor RSRP: {state[7]:.1f} dBm")
    print(f"   Selected action: {action} (expected: 1)")
    assert action == 1, f"Expected action 1, got {action}"
    print("   ✅ Correctly switched to best neighbor\n")

    # Test Case 2: 鄰居僅略優 → 遲滯機制保持當前
    print("2️⃣ Test Case 2: Neighbor slightly better (within hysteresis)")
    state[0] = -40.0  # Serving satellite RSRP = -40 dBm
    state[7] = -38.0  # Candidate 1 RSRP = -38 dBm (better by 2 dB < 3 dB hysteresis)

    action = policy.select_action(state)
    print(f"   Serving RSRP: {state[0]:.1f} dBm")
    print(f"   Best neighbor RSRP: {state[7]:.1f} dBm")
    print(f"   Hysteresis: {policy.hysteresis_db:.1f} dB")
    print(f"   Selected action: {action} (expected: 0)")
    assert action == 0, f"Expected action 0, got {action}"
    print("   ✅ Correctly stayed with current satellite\n")

    # Test Case 3: 所有鄰居都差 → 保持當前
    print("3️⃣ Test Case 3: All neighbors worse")
    state[0] = -30.0   # Serving satellite RSRP = -30 dBm (best)
    state[7] = -50.0   # Candidate 1 RSRP = -50 dBm
    state[14] = -60.0  # Candidate 2 RSRP = -60 dBm
    state[21] = -70.0  # Candidate 3 RSRP = -70 dBm
    state[28] = -80.0  # Candidate 4 RSRP = -80 dBm
    state[35] = -90.0  # Candidate 5 RSRP = -90 dBm

    action = policy.select_action(state)
    print(f"   Serving RSRP: {state[0]:.1f} dBm")
    print(f"   Best neighbor RSRP: {state[7]:.1f} dBm")
    print(f"   Selected action: {action} (expected: 0)")
    assert action == 0, f"Expected action 0, got {action}"
    print("   ✅ Correctly stayed with current satellite\n")

    # Test Case 4: 候選衛星 3 最好
    print("4️⃣ Test Case 4: Candidate 3 is best")
    state[0] = -50.0   # Serving satellite RSRP = -50 dBm
    state[7] = -60.0   # Candidate 1 RSRP = -60 dBm
    state[14] = -55.0  # Candidate 2 RSRP = -55 dBm
    state[21] = -40.0  # Candidate 3 RSRP = -40 dBm (best, better by 10 dB)
    state[28] = -70.0  # Candidate 4 RSRP = -70 dBm
    state[35] = -80.0  # Candidate 5 RSRP = -80 dBm

    action = policy.select_action(state)
    print(f"   Serving RSRP: {state[0]:.1f} dBm")
    print(f"   Best neighbor RSRP: {state[21]:.1f} dBm (Candidate 3)")
    print(f"   Selected action: {action} (expected: 3)")
    assert action == 3, f"Expected action 3, got {action}"
    print("   ✅ Correctly switched to candidate 3\n")

    # Test greedy interface
    print("5️⃣ Test greedy interface")
    action_greedy = policy.select_action_greedy(state)
    action_normal = policy.select_action(state)
    assert action_greedy == action_normal
    print(f"   select_action_greedy() == select_action(): {action_greedy} == {action_normal}")
    print("   ✅ Greedy interface works correctly\n")

    print("✅ All tests passed!")


if __name__ == "__main__":
    test_rsrp_baseline()
