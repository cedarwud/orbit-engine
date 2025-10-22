#!/usr/bin/env python3
"""
單元測試: Three-State Markov Model

測試 Proposal 002 的三態 Markov 模型實現
SOURCE: 3GPP TR 38.901 v17.0.0 (2020) Table 7.6.3-1
"""
import sys
import unittest
import logging
sys.path.insert(0, 'src')

from stages.stage5_signal_analysis.three_state_markov import (
    PropagationState,
    MarkovConfig,
    ThreeStateMarkovModel
)

# 禁用日誌輸出
logging.disable(logging.CRITICAL)


class TestPropagationState(unittest.TestCase):
    """測試 PropagationState enum"""

    def test_state_values(self):
        """測試狀態值正確"""
        self.assertEqual(PropagationState.LOS.value, 0)
        self.assertEqual(PropagationState.SHADOWED.value, 1)
        self.assertEqual(PropagationState.BLOCKED.value, 2)

    def test_state_names(self):
        """測試狀態名稱正確"""
        self.assertEqual(PropagationState.LOS.name, "LOS")
        self.assertEqual(PropagationState.SHADOWED.name, "SHADOWED")
        self.assertEqual(PropagationState.BLOCKED.name, "BLOCKED")


class TestMarkovConfig(unittest.TestCase):
    """測試 MarkovConfig dataclass"""

    def test_default_config(self):
        """測試預設配置符合 3GPP 標準"""
        config = MarkovConfig()

        # LOS state transitions (3GPP TR 38.901 Table 7.6.3-1)
        self.assertEqual(config.P_LL, 0.95)
        self.assertEqual(config.P_LS, 0.04)
        self.assertEqual(config.P_LB, 0.01)

        # Shadowed state transitions
        self.assertEqual(config.P_SL, 0.10)
        self.assertEqual(config.P_SS, 0.80)
        self.assertEqual(config.P_SB, 0.10)

        # Blocked state transitions
        self.assertEqual(config.P_BL, 0.05)
        self.assertEqual(config.P_BS, 0.15)
        self.assertEqual(config.P_BB, 0.80)

    def test_custom_config(self):
        """測試自定義配置"""
        config = MarkovConfig(
            P_LL=0.90, P_LS=0.08, P_LB=0.02,
            random_seed=123
        )
        self.assertEqual(config.P_LL, 0.90)
        self.assertEqual(config.P_LS, 0.08)
        self.assertEqual(config.P_LB, 0.02)
        self.assertEqual(config.random_seed, 123)

    def test_transition_probabilities_sum_to_one(self):
        """測試轉換機率總和為 1（每個狀態）"""
        config = MarkovConfig()

        # From LOS
        self.assertAlmostEqual(config.P_LL + config.P_LS + config.P_LB, 1.0, places=10)

        # From Shadowed
        self.assertAlmostEqual(config.P_SL + config.P_SS + config.P_SB, 1.0, places=10)

        # From Blocked
        self.assertAlmostEqual(config.P_BL + config.P_BS + config.P_BB, 1.0, places=10)


class TestThreeStateMarkovModel(unittest.TestCase):
    """測試 ThreeStateMarkovModel 類"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)
        self.config = MarkovConfig(random_seed=42)
        self.model = ThreeStateMarkovModel(self.config, self.logger)

    def test_initialization(self):
        """測試模型初始化"""
        self.assertIsNotNone(self.model)
        self.assertEqual(self.model.config.random_seed, 42)
        self.assertTrue(self.model.config.elevation_adjustment_enabled)

    def test_transition_matrix_shape(self):
        """測試轉換矩陣形狀"""
        P = self.model.get_transition_matrix(elevation_deg=45.0)
        self.assertEqual(P.shape, (3, 3))

    def test_transition_matrix_rows_sum_to_one(self):
        """測試轉換矩陣每行總和為 1"""
        P = self.model.get_transition_matrix(elevation_deg=45.0)
        for i in range(3):
            row_sum = sum(P[i, :])
            self.assertAlmostEqual(row_sum, 1.0, places=10,
                                 msg=f"Row {i} sum should be 1.0")

    def test_elevation_adjustment(self):
        """測試仰角調整效果"""
        # 高仰角應該有更高的 LOS 機率
        P_low = self.model.get_transition_matrix(elevation_deg=10.0)
        P_high = self.model.get_transition_matrix(elevation_deg=80.0)

        # 從 LOS 狀態：高仰角應該有更高的 P_LL
        # （因為高仰角路徑更短，障礙物更少）
        self.assertGreaterEqual(P_high[0, 0], P_low[0, 0],
                               "Higher elevation should have higher P(LOS→LOS)")

    def test_simulate_next_state_reproducibility(self):
        """測試狀態模擬可重現性"""
        model1 = ThreeStateMarkovModel(MarkovConfig(random_seed=42), self.logger)
        model2 = ThreeStateMarkovModel(MarkovConfig(random_seed=42), self.logger)

        current_state = PropagationState.LOS
        elevation = 45.0

        # 兩個模型應該產生相同的狀態序列
        states1 = []
        states2 = []

        for _ in range(10):
            next_state1 = model1.simulate_next_state(current_state, elevation)
            next_state2 = model2.simulate_next_state(current_state, elevation)
            states1.append(next_state1)
            states2.append(next_state2)
            current_state = next_state1

        self.assertEqual(states1, states2,
                        "Same random seed should produce same state sequence")

    def test_simulate_next_state_transitions(self):
        """測試狀態轉換執行"""
        current_state = PropagationState.LOS

        # 執行多次模擬
        next_states = []
        for _ in range(100):
            next_state = self.model.simulate_next_state(current_state, 45.0)
            next_states.append(next_state)

        # 檢查所有狀態都是有效的
        for state in next_states:
            self.assertIn(state, [PropagationState.LOS,
                                 PropagationState.SHADOWED,
                                 PropagationState.BLOCKED])

        # 統計分布應該接近轉換機率
        los_count = sum(1 for s in next_states if s == PropagationState.LOS)

        # 從 LOS 狀態出發，大部分應該保持 LOS (P_LL = 0.95)
        self.assertGreater(los_count, 80,  # 至少 80% 應該是 LOS
                          "Most transitions from LOS should stay in LOS")

    def test_steady_state_distribution(self):
        """測試穩態分佈計算"""
        pi = self.model.get_steady_state_distribution(elevation_deg=45.0)

        # 檢查形狀
        self.assertEqual(len(pi), 3)

        # 檢查總和為 1
        self.assertAlmostEqual(sum(pi), 1.0, places=10,
                              msg="Steady-state probabilities should sum to 1")

        # 檢查所有機率為正
        for prob in pi:
            self.assertGreater(prob, 0.0,
                             msg="All steady-state probabilities should be positive")

        # 檢查 LOS 機率最高（因為 P_LL 很高）
        self.assertEqual(pi[0], max(pi),
                        msg="LOS should have highest steady-state probability")

    def test_expected_dwell_time(self):
        """測試預期停留時間計算"""
        dwell_times = self.model.get_expected_dwell_time(elevation_deg=45.0)

        # 檢查形狀
        self.assertEqual(len(dwell_times), 3)

        # 所有停留時間應該 >= 1（至少停留一個時間步）
        for time in dwell_times:
            self.assertGreaterEqual(time, 1.0,
                                   msg="Dwell time should be at least 1")

        # LOS 狀態應該有最長的停留時間（因為 P_LL = 0.95）
        self.assertEqual(dwell_times[0], max(dwell_times),
                        msg="LOS should have longest expected dwell time")

    def test_elevation_adjustment_disabled(self):
        """測試停用仰角調整"""
        config_no_adj = MarkovConfig(elevation_adjustment_enabled=False, random_seed=42)
        model_no_adj = ThreeStateMarkovModel(config_no_adj, self.logger)

        # 不同仰角應該產生相同的轉換矩陣
        P_low = model_no_adj.get_transition_matrix(elevation_deg=10.0)
        P_high = model_no_adj.get_transition_matrix(elevation_deg=80.0)

        import numpy as np
        np.testing.assert_array_almost_equal(P_low, P_high,
            err_msg="With elevation adjustment disabled, matrices should be identical")


class TestMarkovModelEdgeCases(unittest.TestCase):
    """測試邊界情況"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)

    def test_extreme_low_elevation(self):
        """測試極低仰角"""
        config = MarkovConfig(random_seed=42)
        model = ThreeStateMarkovModel(config, self.logger)

        # 應該不會崩潰
        P = model.get_transition_matrix(elevation_deg=0.1)
        self.assertEqual(P.shape, (3, 3))

    def test_extreme_high_elevation(self):
        """測試極高仰角"""
        config = MarkovConfig(random_seed=42)
        model = ThreeStateMarkovModel(config, self.logger)

        # 應該不會崩潰
        P = model.get_transition_matrix(elevation_deg=89.9)
        self.assertEqual(P.shape, (3, 3))

    def test_negative_elevation(self):
        """測試負仰角（應該使用絕對值）"""
        config = MarkovConfig(random_seed=42)
        model = ThreeStateMarkovModel(config, self.logger)

        # 應該不會崩潰
        P = model.get_transition_matrix(elevation_deg=-10.0)
        self.assertEqual(P.shape, (3, 3))


if __name__ == '__main__':
    # 運行測試
    unittest.main(verbosity=2)
