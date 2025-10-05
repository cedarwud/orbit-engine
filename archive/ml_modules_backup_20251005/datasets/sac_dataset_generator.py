"""
SAC 數據集生成器 - Stage 6 ML 訓練數據生成組件

生成 Soft Actor-Critic 訓練數據集。

學術參考:
- Haarnoja, T., et al. (2018). Soft actor-critic: Off-policy maximum entropy deep RL.
  ICML.

依據:
- docs/stages/stage6-research-optimization.md Line 597-623

Author: ORBIT Engine Team
Created: 2025-10-02

🎓 學術合規性檢查提醒:
- 使用標準 SAC 數據格式
- 軟Q值包含熵正則化項
- 溫度參數 α = 0.2 來自論文
"""

import logging
from typing import Dict, Any, List


class SACDatasetGenerator:
    """SAC 數據集生成器

    生成 Soft Actor-Critic 訓練所需的數據集。

    SAC 需要:
    - state: 當前狀態
    - continuous_actions: 連續動作 (轉換為連續空間)
    - rewards: 獎勵
    - next_state: 下一狀態
    - soft_q_values: 軟 Q 值
    - policy_entropy: 策略熵 (探索度量)
    """

    def __init__(
        self,
        state_encoder,
        reward_calculator,
        policy_value_estimator
    ):
        """初始化生成器

        Args:
            state_encoder: 狀態編碼器
            reward_calculator: 獎勵計算器
            policy_value_estimator: 策略價值估計器
        """
        self.state_encoder = state_encoder
        self.reward_calculator = reward_calculator
        self.policy_value_estimator = policy_value_estimator
        self.logger = logging.getLogger(__name__)

    def generate(
        self,
        signal_analysis: Dict[str, Any],
        gpp_events: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成 SAC 訓練數據集

        Returns:
            {
                'state_vectors': List[List[float]],
                'continuous_actions': List[List[float]], # 連續動作
                'rewards': List[float],
                'next_state_vectors': List[List[float]],
                'done_flags': List[bool],
                'soft_q_values': List[List[float]],    # 軟 Q 值
                'policy_entropy': List[float],          # 策略熵
                'dataset_size': int
            }
        """
        self.logger.info("開始生成 SAC 數據集")

        state_vectors = []
        continuous_actions = []
        rewards = []
        next_state_vectors = []
        done_flags = []
        soft_q_values = []
        policy_entropy = []

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

                    next_state_vector = self.state_encoder.build_state_vector(next_time_point)
                    if next_state_vector is None:
                        continue

                    # 生成連續動作 (將離散動作映射到連續空間)
                    continuous_action = self.policy_value_estimator.generate_continuous_action(state_vector)

                    # 計算獎勵
                    reward, _ = self.reward_calculator.calculate_reward(
                        current_time_point,
                        'maintain',
                        next_time_point
                    )

                    # 計算軟 Q 值 (加入熵正則化)
                    soft_q_value_vector = self.policy_value_estimator.estimate_soft_q_values(
                        state_vector,
                        continuous_action
                    )

                    # 計算策略熵 (探索度量)
                    entropy = self.policy_value_estimator.calculate_policy_entropy(state_vector)

                    # 判斷終止
                    quality_assessment = next_time_point.get('quality_assessment', {})
                    is_done = not quality_assessment.get('is_usable', True)

                    # 添加到數據集
                    state_vectors.append(state_vector)
                    continuous_actions.append(continuous_action)
                    rewards.append(reward)
                    next_state_vectors.append(next_state_vector)
                    done_flags.append(is_done)
                    soft_q_values.append(soft_q_value_vector)
                    policy_entropy.append(entropy)

            dataset_size = len(state_vectors)

            self.logger.info(f"SAC 數據集生成完成 - 樣本數: {dataset_size}")

            return {
                'state_vectors': state_vectors,
                'continuous_actions': continuous_actions,
                'rewards': rewards,
                'next_state_vectors': next_state_vectors,
                'done_flags': done_flags,
                'soft_q_values': soft_q_values,
                'policy_entropy': policy_entropy,
                'dataset_size': dataset_size
            }

        except Exception as e:
            self.logger.error(f"生成 SAC 數據集時發生錯誤: {str(e)}", exc_info=True)
            return {
                'state_vectors': [],
                'continuous_actions': [],
                'rewards': [],
                'next_state_vectors': [],
                'done_flags': [],
                'soft_q_values': [],
                'policy_entropy': [],
                'dataset_size': 0
            }
