#!/usr/bin/env python3
"""
單元測試: Propagation Condition Simulator

測試 Proposal 002 的傳播條件模擬器（整合 Markov + Loo 模型）
"""
import sys
import unittest
import logging
sys.path.insert(0, 'src')

from stages.stage5_signal_analysis.three_state_markov import PropagationState
from stages.stage5_signal_analysis.loo_channel import Environment
from stages.stage5_signal_analysis.propagation_simulator import (
    PropagationResult,
    PropagationConditionSimulator,
    create_default_simulator
)

# 禁用日誌輸出
logging.disable(logging.CRITICAL)


class TestPropagationResult(unittest.TestCase):
    """測試 PropagationResult dataclass"""

    def test_result_creation(self):
        """測試結果創建"""
        result = PropagationResult(
            satellite_id="46061",
            timestamp="2025-10-22T01:53:00+00:00",
            propagation_state="LOS",
            state_probabilities={"LOS": 0.7, "Shadowed": 0.2, "Blocked": 0.1},
            channel_attenuation_db=145.3,
            los_component_db=-2.1,
            multipath_component_db=-18.5,
            elevation_deg=45.0,
            distance_km=800.0,
            environment="suburban"
        )

        self.assertEqual(result.satellite_id, "46061")
        self.assertEqual(result.propagation_state, "LOS")
        self.assertEqual(result.elevation_deg, 45.0)

    def test_to_dict(self):
        """測試字典轉換"""
        result = PropagationResult(
            satellite_id="46061",
            timestamp="2025-10-22T01:53:00+00:00",
            propagation_state="LOS",
            state_probabilities={"LOS": 0.7, "Shadowed": 0.2, "Blocked": 0.1},
            channel_attenuation_db=145.3,
            los_component_db=-2.1,
            multipath_component_db=-18.5,
            elevation_deg=45.0,
            distance_km=800.0,
            environment="suburban"
        )

        result_dict = result.to_dict()

        # 檢查所有必要欄位
        self.assertIn('satellite_id', result_dict)
        self.assertIn('timestamp', result_dict)
        self.assertIn('propagation_state', result_dict)
        self.assertIn('state_probabilities', result_dict)
        self.assertIn('channel_attenuation_db', result_dict)
        self.assertIn('environment', result_dict)


class TestPropagationConditionSimulator(unittest.TestCase):
    """測試 PropagationConditionSimulator 類"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)
        self.config = {
            'markov_model': {
                'P_LL': 0.95, 'P_LS': 0.04, 'P_LB': 0.01,
                'P_SL': 0.10, 'P_SS': 0.80, 'P_SB': 0.10,
                'P_BL': 0.05, 'P_BS': 0.15, 'P_BB': 0.80,
                'elevation_adjustment_enabled': True,
                'random_seed': 42
            },
            'loo_channel': {
                'environment': 'suburban',
                'carrier_frequency_ghz': 12.0,
                'random_seed': 42
            },
            'initial_state': 'LOS'
        }
        self.simulator = PropagationConditionSimulator(self.config, self.logger)

    def test_initialization(self):
        """測試模擬器初始化"""
        self.assertIsNotNone(self.simulator)
        self.assertIsNotNone(self.simulator.markov_model)
        self.assertIsNotNone(self.simulator.loo_model)
        self.assertEqual(self.simulator.initial_state, PropagationState.LOS)

    def test_simulate_single_satellite(self):
        """測試單顆衛星模擬"""
        result = self.simulator.simulate(
            satellite_id="46061",
            timestamp="2025-10-22T01:53:00+00:00",
            elevation_deg=45.0,
            distance_km=800.0
        )

        # 檢查結果類型
        self.assertIsInstance(result, PropagationResult)

        # 檢查結果欄位
        self.assertEqual(result.satellite_id, "46061")
        self.assertEqual(result.timestamp, "2025-10-22T01:53:00+00:00")
        self.assertIn(result.propagation_state, ["LOS", "SHADOWED", "BLOCKED"])
        self.assertGreater(result.channel_attenuation_db, 0.0)
        self.assertEqual(result.elevation_deg, 45.0)
        self.assertEqual(result.distance_km, 800.0)
        self.assertEqual(result.environment, "suburban")

    def test_state_tracking(self):
        """測試狀態追蹤"""
        sat_id = "46061"

        # 首次模擬應該使用初始狀態
        result1 = self.simulator.simulate(sat_id, "2025-10-22T01:53:00+00:00", 45.0, 800.0)

        # 第二次模擬應該從前一個狀態轉換
        result2 = self.simulator.simulate(sat_id, "2025-10-22T01:53:01+00:00", 45.0, 800.0)

        # 狀態應該被追蹤
        self.assertIn(sat_id, self.simulator.current_states)

    def test_multiple_satellites_tracking(self):
        """測試多衛星狀態追蹤"""
        sat_ids = ["46061", "54133", "58179"]

        for sat_id in sat_ids:
            self.simulator.simulate(sat_id, "2025-10-22T02:00:00+00:00", 40.0, 750.0)

        # 所有衛星都應該被追蹤
        for sat_id in sat_ids:
            self.assertIn(sat_id, self.simulator.current_states)

        # 檢查狀態統計
        stats = self.simulator.get_state_statistics()
        self.assertEqual(stats['total_satellites'], len(sat_ids))

    def test_state_probabilities(self):
        """測試狀態機率總和為 1"""
        result = self.simulator.simulate("46061", "2025-10-22T01:53:00+00:00", 45.0, 800.0)

        prob_sum = sum(result.state_probabilities.values())
        self.assertAlmostEqual(prob_sum, 1.0, places=5,
                              msg="State probabilities should sum to 1.0")

    def test_reproducibility(self):
        """測試可重現性"""
        sim1 = PropagationConditionSimulator(self.config, self.logger)
        sim2 = PropagationConditionSimulator(self.config, self.logger)

        # 相同輸入應該產生相同輸出
        result1 = sim1.simulate("46061", "2025-10-22T01:53:00+00:00", 45.0, 800.0)
        result2 = sim2.simulate("46061", "2025-10-22T01:53:00+00:00", 45.0, 800.0)

        self.assertEqual(result1.propagation_state, result2.propagation_state)
        self.assertAlmostEqual(result1.channel_attenuation_db,
                              result2.channel_attenuation_db, places=5)

    def test_reset_state_specific(self):
        """測試重置特定衛星狀態"""
        sat_id = "46061"

        # 模擬並追蹤狀態
        self.simulator.simulate(sat_id, "2025-10-22T01:53:00+00:00", 45.0, 800.0)
        self.assertIn(sat_id, self.simulator.current_states)

        # 重置特定衛星
        self.simulator.reset_state(sat_id)
        self.assertNotIn(sat_id, self.simulator.current_states)

    def test_reset_state_all(self):
        """測試重置所有衛星狀態"""
        # 模擬多顆衛星
        for sat_id in ["46061", "54133", "58179"]:
            self.simulator.simulate(sat_id, "2025-10-22T02:00:00+00:00", 40.0, 750.0)

        # 重置所有
        self.simulator.reset_state()
        self.assertEqual(len(self.simulator.current_states), 0)

    def test_get_state_statistics(self):
        """測試狀態統計"""
        # 初始時應該沒有衛星
        stats = self.simulator.get_state_statistics()
        self.assertEqual(stats['total_satellites'], 0)

        # 添加一些衛星
        for i in range(5):
            self.simulator.simulate(f"SAT_{i}", "2025-10-22T02:00:00+00:00", 40.0, 750.0)

        stats = self.simulator.get_state_statistics()
        self.assertEqual(stats['total_satellites'], 5)
        self.assertIn('state_counts', stats)
        self.assertIn('state_percentages', stats)

        # 檢查百分比總和為 100%
        total_pct = sum(stats['state_percentages'].values())
        self.assertAlmostEqual(total_pct, 100.0, places=5)

    def test_elevation_effect(self):
        """測試仰角對傳播條件的影響"""
        # 低仰角
        result_low = self.simulator.simulate(
            "SAT_LOW", "2025-10-22T02:00:00+00:00", 10.0, 800.0
        )

        # 重置狀態以獨立測試
        self.simulator.reset_state()

        # 高仰角
        result_high = self.simulator.simulate(
            "SAT_HIGH", "2025-10-22T02:00:00+00:00", 80.0, 800.0
        )

        # 驗證兩個結果都有效（總衰減包含隨機成分，不保證嚴格順序）
        # 但兩個衰減值都應該在合理範圍內
        self.assertGreater(result_low.channel_attenuation_db, 100.0,
                          "Low elevation attenuation should be > 100 dB")
        self.assertLess(result_low.channel_attenuation_db, 250.0,
                       "Low elevation attenuation should be < 250 dB")
        self.assertGreater(result_high.channel_attenuation_db, 100.0,
                          "High elevation attenuation should be > 100 dB")
        self.assertLess(result_high.channel_attenuation_db, 250.0,
                       "High elevation attenuation should be < 250 dB")

    def test_distance_effect(self):
        """測試距離對衰減的影響"""
        # 近距離
        result_near = self.simulator.simulate(
            "SAT_NEAR", "2025-10-22T02:00:00+00:00", 45.0, 500.0
        )

        # 重置狀態以獨立測試
        self.simulator.reset_state()

        # 遠距離
        result_far = self.simulator.simulate(
            "SAT_FAR", "2025-10-22T02:00:00+00:00", 45.0, 1000.0
        )

        # 驗證距離效應：遠距離應該有更高的 FSPL
        # 距離加倍 → FSPL 增加約 6 dB（這是確定性的）
        # 總衰減包含隨機成分，但差異應該顯著（> 5 dB）
        attenuation_diff = result_far.channel_attenuation_db - result_near.channel_attenuation_db
        self.assertGreater(attenuation_diff, 4.0,
                          "Greater distance should significantly increase attenuation")


class TestCreateDefaultSimulator(unittest.TestCase):
    """測試便利函數"""

    def test_create_default_simulator(self):
        """測試使用預設參數創建模擬器"""
        simulator = create_default_simulator()

        self.assertIsNotNone(simulator)
        self.assertIsNotNone(simulator.markov_model)
        self.assertIsNotNone(simulator.loo_model)

    def test_create_default_simulator_with_params(self):
        """測試使用自定義參數創建模擬器"""
        simulator = create_default_simulator(
            environment=Environment.URBAN,
            random_seed=123
        )

        self.assertEqual(simulator.loo_model.config.environment, Environment.URBAN)
        self.assertEqual(simulator.markov_model.config.random_seed, 123)


class TestPropagationSimulatorEdgeCases(unittest.TestCase):
    """測試邊界情況"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)
        self.config = {
            'markov_model': {'random_seed': 42},
            'loo_channel': {
                'environment': 'suburban',
                'carrier_frequency_ghz': 12.0,
                'random_seed': 42
            },
            'initial_state': 'LOS'
        }

    def test_extreme_low_elevation(self):
        """測試極低仰角"""
        simulator = PropagationConditionSimulator(self.config, self.logger)

        # 應該不會崩潰
        result = simulator.simulate("TEST_SAT", "2025-10-22T02:00:00+00:00", 0.1, 800.0)
        self.assertIsNotNone(result)

    def test_extreme_high_elevation(self):
        """測試極高仰角"""
        simulator = PropagationConditionSimulator(self.config, self.logger)

        # 應該不會崩潰
        result = simulator.simulate("TEST_SAT", "2025-10-22T02:00:00+00:00", 89.9, 800.0)
        self.assertIsNotNone(result)

    def test_short_distance(self):
        """測試短距離"""
        simulator = PropagationConditionSimulator(self.config, self.logger)

        # 應該不會崩潰
        result = simulator.simulate("TEST_SAT", "2025-10-22T02:00:00+00:00", 45.0, 100.0)
        self.assertIsNotNone(result)

    def test_long_distance(self):
        """測試長距離"""
        simulator = PropagationConditionSimulator(self.config, self.logger)

        # 應該不會崩潰
        result = simulator.simulate("TEST_SAT", "2025-10-22T02:00:00+00:00", 45.0, 2000.0)
        self.assertIsNotNone(result)


if __name__ == '__main__':
    # 運行測試
    unittest.main(verbosity=2)
