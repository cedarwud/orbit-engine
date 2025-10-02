"""
DQN 數據集生成器 - Stage 6 ML 訓練數據生成組件

生成 Deep Q-Network 訓練數據集。

學術參考:
- Mnih, V., et al. (2015). Human-level control through deep reinforcement learning.
  Nature, 518(7540), 529-533.

依據:
- docs/stages/stage6-research-optimization.md Line 597-623

Author: ORBIT Engine Team
Created: 2025-10-02

🎓 學術合規性檢查提醒:
- 使用標準 DQN 數據格式 (state, action, reward, next_state, done)
- Q值估計基於線性價值函數近似
"""

import logging
from typing import Dict, Any, List


class DQNDatasetGenerator:
    """DQN 數據集生成器

    生成 Deep Q-Network 訓練所需的數據集。

    DQN 需要:
    - state: 當前狀態
    - action: 執行的動作
    - reward: 獲得的獎勵
    - next_state: 下一狀態
    - done: 終止標記
    """

    def __init__(
        self,
        state_encoder,
        reward_calculator,
        policy_value_estimator,
        action_space: List[str]
    ):
        """初始化生成器

        Args:
            state_encoder: 狀態編碼器
            reward_calculator: 獎勵計算器
            policy_value_estimator: 策略價值估計器
            action_space: 動作空間定義
        """
        self.state_encoder = state_encoder
        self.reward_calculator = reward_calculator
        self.policy_value_estimator = policy_value_estimator
        self.action_space = action_space
        self.logger = logging.getLogger(__name__)

    def generate(
        self,
        signal_analysis: Dict[str, Any],
        gpp_events: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成 DQN 訓練數據集

        Returns:
            {
                'state_vectors': List[List[float]],  # (N, 7) 狀態向量
                'action_space': List[str],            # 動作名稱
                'q_values': List[List[float]],        # (N, action_space_size) Q值
                'reward_values': List[float],         # (N,) 獎勵值
                'next_state_vectors': List[List[float]], # (N, 7) 下一狀態
                'done_flags': List[bool],             # (N,) 終止標記
                'dataset_size': int
            }
        """
        self.logger.info("開始生成 DQN 數據集")

        state_vectors = []
        q_values = []
        reward_values = []
        next_state_vectors = []
        done_flags = []

        try:
            # 從 signal_analysis 提取衛星數據
            satellites = signal_analysis.get('satellites', [])

            for i, satellite in enumerate(satellites):
                # 檢查是否有時間序列數據
                time_series = satellite.get('time_series', [])

                for j in range(len(time_series) - 1):
                    current_time_point = time_series[j]
                    next_time_point = time_series[j + 1]

                    # 構建當前狀態向量
                    state_vector = self.state_encoder.build_state_vector(current_time_point)
                    if state_vector is None:
                        continue

                    # 構建下一狀態向量
                    next_state_vector = self.state_encoder.build_state_vector(next_time_point)
                    if next_state_vector is None:
                        continue

                    # 計算獎勵
                    action = 'maintain' if i == 0 else 'handover_to_candidate_1'
                    reward, _ = self.reward_calculator.calculate_reward(
                        current_time_point,
                        action,
                        next_time_point
                    )

                    # 計算 Q 值 (基於信號品質和獎勵估計)
                    q_value_vector = self.policy_value_estimator.estimate_q_values(
                        state_vector,
                        next_state_vector,
                        reward
                    )

                    # 判斷是否終止 (信號中斷)
                    quality_assessment = next_time_point.get('quality_assessment', {})
                    is_done = not quality_assessment.get('is_usable', True)

                    # 添加到數據集
                    state_vectors.append(state_vector)
                    q_values.append(q_value_vector)
                    reward_values.append(reward)
                    next_state_vectors.append(next_state_vector)
                    done_flags.append(is_done)

            dataset_size = len(state_vectors)

            self.logger.info(f"DQN 數據集生成完成 - 樣本數: {dataset_size}")

            return {
                'state_vectors': state_vectors,
                'action_space': self.action_space,
                'q_values': q_values,
                'reward_values': reward_values,
                'next_state_vectors': next_state_vectors,
                'done_flags': done_flags,
                'dataset_size': dataset_size
            }

        except Exception as e:
            self.logger.error(f"生成 DQN 數據集時發生錯誤: {str(e)}", exc_info=True)
            return {
                'state_vectors': [],
                'action_space': self.action_space,
                'q_values': [],
                'reward_values': [],
                'next_state_vectors': [],
                'done_flags': [],
                'dataset_size': 0
            }
