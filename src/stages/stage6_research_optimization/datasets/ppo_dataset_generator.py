"""
PPO 數據集生成器 - Stage 6 ML 訓練數據生成組件

生成 Proximal Policy Optimization 訓練數據集。

學術參考:
- Schulman, J., et al. (2017). Proximal policy optimization algorithms.
  arXiv:1707.06347.

依據:
- docs/stages/stage6-research-optimization.md Line 597-623

Author: ORBIT Engine Team
Created: 2025-10-02

🎓 學術合規性檢查提醒:
- 使用標準 PPO 數據格式
- clip_epsilon = 0.2 來自論文標準設置
"""

import logging
from typing import Dict, Any, List
import numpy as np


class PPODatasetGenerator:
    """PPO 數據集生成器

    生成 Proximal Policy Optimization 訓練所需的數據集。

    PPO 需要:
    - state: 當前狀態
    - actions_taken: 實際執行的動作
    - old_policy_probs: 舊策略概率
    - new_policy_probs: 新策略概率
    - advantages: 優勢函數
    - returns: 回報
    """

    def __init__(
        self,
        state_encoder,
        reward_calculator,
        policy_value_estimator,
        action_space: List[str],
        config: Dict[str, Any]
    ):
        """初始化生成器

        Args:
            state_encoder: 狀態編碼器
            reward_calculator: 獎勵計算器
            policy_value_estimator: 策略價值估計器
            action_space: 動作空間定義
            config: 配置參數 (包含 discount_factor, ppo_clip_epsilon)
        """
        self.state_encoder = state_encoder
        self.reward_calculator = reward_calculator
        self.policy_value_estimator = policy_value_estimator
        self.action_space = action_space
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate(
        self,
        signal_analysis: Dict[str, Any],
        gpp_events: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成 PPO 訓練數據集

        Returns:
            {
                'state_vectors': List[List[float]],
                'actions_taken': List[int],            # 實際動作
                'old_policy_probs': List[float],       # 舊策略概率
                'new_policy_probs': List[float],       # 新策略概率
                'advantages': List[float],             # 優勢函數
                'returns': List[float],                # 回報
                'clipped_ratios': List[float],         # 裁剪比率
                'dataset_size': int
            }
        """
        self.logger.info("開始生成 PPO 數據集")

        state_vectors = []
        actions_taken = []
        old_policy_probs = []
        new_policy_probs = []
        advantages = []
        returns = []
        clipped_ratios = []

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

                    # 決定動作 (基於信號品質)
                    action_idx = self.policy_value_estimator.select_action_from_state(state_vector)

                    # 計算舊策略概率
                    old_action_probs = self.policy_value_estimator.estimate_action_probs(state_vector)
                    old_prob = old_action_probs[action_idx]

                    # 計算新策略概率 (加入探索噪音)
                    new_action_probs = self.policy_value_estimator.estimate_action_probs_with_noise(state_vector)
                    new_prob = new_action_probs[action_idx]

                    # 計算優勢函數和回報
                    reward, _ = self.reward_calculator.calculate_reward(
                        current_time_point,
                        self.action_space[action_idx],
                        next_time_point
                    )

                    value_estimate = self.policy_value_estimator.estimate_state_value(state_vector)
                    next_value = self.policy_value_estimator.estimate_state_value(
                        self.state_encoder.build_state_vector(next_time_point) or [0] * 7
                    )
                    advantage = reward + self.config['discount_factor'] * next_value - value_estimate
                    return_value = reward + self.config['discount_factor'] * next_value

                    # 計算裁剪比率 (PPO 核心機制)
                    # SOURCE: Schulman et al. (2017) "Proximal Policy Optimization Algorithms"
                    #         arXiv:1707.06347v2, Section 6.1, Table 3
                    # clip_epsilon = 0.2 是原始論文的標準超參數
                    # 依據: 在 Atari、MuJoCo 等環境中驗證有效
                    ratio = new_prob / (old_prob + 1e-8)
                    clip_epsilon = self.config.get('ppo_clip_epsilon', 0.2)
                    clipped_ratio = np.clip(ratio, 1 - clip_epsilon, 1 + clip_epsilon)

                    # 添加到數據集
                    state_vectors.append(state_vector)
                    actions_taken.append(action_idx)
                    old_policy_probs.append(old_prob)
                    new_policy_probs.append(new_prob)
                    advantages.append(advantage)
                    returns.append(return_value)
                    clipped_ratios.append(clipped_ratio)

            dataset_size = len(state_vectors)

            self.logger.info(f"PPO 數據集生成完成 - 樣本數: {dataset_size}")

            return {
                'state_vectors': state_vectors,
                'actions_taken': actions_taken,
                'old_policy_probs': old_policy_probs,
                'new_policy_probs': new_policy_probs,
                'advantages': advantages,
                'returns': returns,
                'clipped_ratios': clipped_ratios,
                'dataset_size': dataset_size
            }

        except Exception as e:
            self.logger.error(f"生成 PPO 數據集時發生錯誤: {str(e)}", exc_info=True)
            return {
                'state_vectors': [],
                'actions_taken': [],
                'old_policy_probs': [],
                'new_policy_probs': [],
                'advantages': [],
                'returns': [],
                'clipped_ratios': [],
                'dataset_size': 0
            }
