"""
獎勵計算器 - Stage 6 ML 訓練數據生成組件

實現複合獎勵函數，用於強化學習換手決策。

獎勵組成:
1. QoS 改善獎勵 (+0.0 ~ +1.0)
2. 中斷懲罰 (-0.5 ~ 0.0)
3. 信號品質獎勵 (+0.0 ~ +1.0)
4. 換手成本懲罰 (-0.1 ~ 0.0)

依據:
- docs/stages/stage6-research-optimization.md 換手決策目標
- 3GPP TS 38.133 (信號品質評估標準)

Author: ORBIT Engine Team
Created: 2025-10-02

🎓 學術合規性檢查提醒:
- 獎勵函數基於實際信號測量指標
- 所有閾值來自 3GPP 標準
"""

import logging
from typing import Dict, Any, Tuple


class RewardCalculator:
    """獎勵計算器

    負責計算強化學習中的獎勵信號，反映換手決策的品質。
    """

    def __init__(self):
        """初始化計算器"""
        self.logger = logging.getLogger(__name__)

    def calculate_reward(
        self,
        current_state: Dict[str, Any],
        action: str,
        next_state: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """計算複合獎勵函數

        獎勵組成:
        1. QoS 改善獎勵 (+0.0 ~ +1.0)
        2. 中斷懲罰 (-0.5 ~ 0.0)
        3. 信號品質獎勵 (+0.0 ~ +1.0)
        4. 換手成本懲罰 (-0.1 ~ 0.0)

        Returns:
            (total_reward, reward_components)
        """
        reward_components = {}

        try:
            # 1. QoS 改善
            current_signal = current_state.get('signal_quality', {})
            next_signal = next_state.get('signal_quality', {})

            current_rsrp = current_signal.get('rsrp_dbm', -120.0)
            next_rsrp = next_signal.get('rsrp_dbm', -120.0)

            rsrp_improvement = (next_rsrp - current_rsrp) / 20.0  # 標準化到 [-1, 1]
            reward_components['qos_improvement'] = max(0, rsrp_improvement)

            # 2. 中斷懲罰
            next_quality = next_state.get('quality_assessment', {})
            if not next_quality.get('is_usable', True):
                reward_components['interruption_penalty'] = -0.5
            else:
                reward_components['interruption_penalty'] = 0.0

            # 3. 信號品質獎勵
            quality_score = next_quality.get('quality_score', 0.0)
            reward_components['signal_quality_gain'] = quality_score

            # 4. 換手成本
            if 'handover' in action:
                reward_components['handover_cost'] = -0.1
            else:
                reward_components['handover_cost'] = 0.0

            total_reward = sum(reward_components.values())

            return total_reward, reward_components

        except Exception as e:
            self.logger.warning(f"計算獎勵時發生錯誤: {str(e)}")
            return 0.0, {}
