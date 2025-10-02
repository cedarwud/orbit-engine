"""
A3C 數據集生成器 - Stage 6 ML 訓練數據生成組件

生成 Asynchronous Advantage Actor-Critic 訓練數據集。

學術參考:
- Mnih, V., et al. (2016). Asynchronous methods for deep reinforcement learning.
  ICML.

依據:
- docs/stages/stage6-research-optimization.md Line 597-623

Author: ORBIT Engine Team
Created: 2025-10-02

🎓 學術合規性檢查提醒:
- 使用標準 Actor-Critic 數據格式
- 優勢函數 A(s,a) = Q(s,a) - V(s)
"""

import logging
from typing import Dict, Any, List


class A3CDatasetGenerator:
    """A3C 數據集生成器

    生成 Asynchronous Advantage Actor-Critic 訓練所需的數據集。

    A3C 需要:
    - state: 當前狀態
    - action_probs: 策略概率分佈
    - value_estimates: 價值估計
    - advantage_functions: 優勢函數 A(s,a) = Q(s,a) - V(s)
    """

    def __init__(
        self,
        state_encoder,
        reward_calculator,
        policy_value_estimator,
        config: Dict[str, Any]
    ):
        """初始化生成器

        Args:
            state_encoder: 狀態編碼器
            reward_calculator: 獎勵計算器
            policy_value_estimator: 策略價值估計器
            config: 配置參數 (包含 discount_factor)
        """
        self.state_encoder = state_encoder
        self.reward_calculator = reward_calculator
        self.policy_value_estimator = policy_value_estimator
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate(
        self,
        signal_analysis: Dict[str, Any],
        gpp_events: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成 A3C 訓練數據集

        Returns:
            {
                'state_vectors': List[List[float]],
                'action_probs': List[List[float]],    # 策略概率
                'value_estimates': List[float],        # 價值估計
                'advantage_functions': List[float],    # 優勢函數
                'policy_gradients': List[List[float]], # 策略梯度
                'dataset_size': int
            }
        """
        self.logger.info("開始生成 A3C 數據集")

        state_vectors = []
        action_probs = []
        value_estimates = []
        advantage_functions = []
        policy_gradients = []

        try:
            satellites = signal_analysis.get('satellites', [])

            for satellite in satellites:
                time_series = satellite.get('time_series', [])

                for j in range(len(time_series) - 1):
                    current_time_point = time_series[j]
                    next_time_point = time_series[j + 1]

                    # 構建狀態向量
                    state_vector = self.state_encoder.build_state_vector(current_time_point)
                    if state_vector is None:
                        continue

                    # 計算策略概率 (基於信號品質)
                    action_prob_vector = self.policy_value_estimator.estimate_action_probs(state_vector)

                    # 計算價值估計 V(s)
                    value_estimate = self.policy_value_estimator.estimate_state_value(state_vector)

                    # 計算優勢函數
                    reward, _ = self.reward_calculator.calculate_reward(
                        current_time_point,
                        'maintain',
                        next_time_point
                    )
                    next_value = self.policy_value_estimator.estimate_state_value(
                        self.state_encoder.build_state_vector(next_time_point) or [0] * 7
                    )
                    advantage = reward + self.config['discount_factor'] * next_value - value_estimate

                    # 計算策略梯度
                    policy_gradient = self.policy_value_estimator.estimate_policy_gradient(
                        action_prob_vector,
                        advantage
                    )

                    # 添加到數據集
                    state_vectors.append(state_vector)
                    action_probs.append(action_prob_vector)
                    value_estimates.append(value_estimate)
                    advantage_functions.append(advantage)
                    policy_gradients.append(policy_gradient)

            dataset_size = len(state_vectors)

            self.logger.info(f"A3C 數據集生成完成 - 樣本數: {dataset_size}")

            return {
                'state_vectors': state_vectors,
                'action_probs': action_probs,
                'value_estimates': value_estimates,
                'advantage_functions': advantage_functions,
                'policy_gradients': policy_gradients,
                'dataset_size': dataset_size
            }

        except Exception as e:
            self.logger.error(f"生成 A3C 數據集時發生錯誤: {str(e)}", exc_info=True)
            return {
                'state_vectors': [],
                'action_probs': [],
                'value_estimates': [],
                'advantage_functions': [],
                'policy_gradients': [],
                'dataset_size': 0
            }
