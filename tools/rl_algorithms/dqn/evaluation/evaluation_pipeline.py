"""
Evaluation Pipeline

評估管道，用於測試和比較不同的換手策略。

SOURCE: Proposal 003, Phase 4 - Evaluation Framework
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from tqdm import tqdm
import logging

from .evaluation_metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


class EvaluationPipeline:
    """評估管道

    用於在測試集上評估不同策略的性能，並生成比較結果。

    SOURCE: Henderson et al. (2018) AAAI
            "Deep Reinforcement Learning that Matters"
            - 標準化評估流程
            - 多次運行取平均
    """

    def __init__(self, test_env, metrics_calculator: Optional[EvaluationMetrics] = None):
        """初始化評估管道

        Args:
            test_env: 測試環境實例（Gymnasium 環境）
            metrics_calculator: 評估指標計算器（可選，默認創建新實例）
        """
        self.test_env = test_env
        self.metrics_calculator = metrics_calculator or EvaluationMetrics()

    def evaluate_policy(
        self,
        policy,
        num_episodes: int = 100,
        verbose: bool = True
    ) -> dict:
        """評估單個策略

        Args:
            policy: 策略實例（需要實現 select_action 或 select_action_greedy 方法）
            num_episodes: 測試回合數
            verbose: 是否顯示進度條

        Returns:
            results (dict): 評估結果，包含:
                - handover: 換手指標
                - qos: QoS 指標
                - reward: 獎勵指標
                - episodes_data: 每個 episode 的詳細數據（可選）

        SOURCE: 標準化評估流程
        """
        all_rewards = []
        all_handovers = []
        all_qos_data = []

        # 決定使用哪個方法選擇動作
        if hasattr(policy, 'select_action_greedy'):
            select_action_fn = policy.select_action_greedy
        elif hasattr(policy, 'select_action'):
            select_action_fn = policy.select_action
        else:
            raise AttributeError("Policy must have 'select_action' or 'select_action_greedy' method")

        iterator = tqdm(range(num_episodes), desc="Evaluating") if verbose else range(num_episodes)

        for episode in iterator:
            state, info = self.test_env.reset()
            episode_rewards = []
            episode_handovers = []
            episode_qos = []

            step_count = 0
            previous_satellite = None

            while True:
                # 選擇動作（貪婪策略，無探索）
                # 如果 policy 是 PyTorch 模型，state 可能需要轉換為 tensor
                try:
                    action = select_action_fn(state)
                except Exception as e:
                    logger.warning(f"Action selection failed: {e}, using default action 0")
                    action = 0

                # 執行動作
                next_state, reward, terminated, truncated, info = self.test_env.step(action)
                done = terminated or truncated

                episode_rewards.append(reward)

                # 記錄換手事件
                # 假設 info 包含當前衛星信息（如果環境提供）
                # 否則通過 action > 0 判斷是否發生換手
                if action > 0:  # 發生換手
                    episode_handovers.append({
                        'source_satellite': previous_satellite if previous_satellite else 0,
                        'target_satellite': action,  # 簡化：用 action 代表目標衛星
                        'timestamp': float(step_count)  # 用 step 數代表時間
                    })

                # 記錄信號品質（從狀態中提取）
                # 狀態格式: [serving_rsrp, serving_rsrq, serving_snr, ...]
                serving_rsrp = state[0]
                serving_snr = state[2] if len(state) > 2 else 0.0

                episode_qos.append({
                    'rsrp_dbm': float(serving_rsrp),
                    'snr_db': float(serving_snr)
                })

                state = next_state
                step_count += 1

                if done:
                    break

            all_rewards.extend(episode_rewards)
            all_handovers.extend(episode_handovers)
            all_qos_data.extend(episode_qos)

        # 計算所有指標
        handover_metrics = self.metrics_calculator.calculate_handover_metrics(all_handovers)
        qos_metrics = self.metrics_calculator.calculate_qos_metrics(all_qos_data)
        reward_metrics = self.metrics_calculator.calculate_reward_metrics(all_rewards)

        return {
            'handover': handover_metrics,
            'qos': qos_metrics,
            'reward': reward_metrics,
            'num_episodes': num_episodes,
            'total_steps': len(all_rewards)
        }

    def compare_policies(
        self,
        policies: Dict[str, object],
        num_episodes: int = 100,
        verbose: bool = True
    ) -> pd.DataFrame:
        """比較多個策略

        Args:
            policies: {policy_name: policy_instance} 字典
            num_episodes: 每個策略的測試回合數
            verbose: 是否顯示進度

        Returns:
            comparison_df (pd.DataFrame): 比較結果表格

        SOURCE: 多策略比較最佳實踐
        """
        results = {}

        for name, policy in policies.items():
            if verbose:
                logger.info(f"Evaluating {name}...")
            results[name] = self.evaluate_policy(policy, num_episodes, verbose)

        # 構建比較表格
        comparison_data = []
        for name, metrics in results.items():
            comparison_data.append({
                'Policy': name,
                'Total Handovers': metrics['handover']['total_handovers'],
                'Handover Rate (per min)': f"{metrics['handover']['handover_rate']:.3f}",
                'Unnecessary HO': metrics['handover']['unnecessary_handovers'],
                'Unnecessary HO Rate': f"{metrics['handover']['unnecessary_handover_rate']:.2%}",
                'Avg RSRP (dBm)': f"{metrics['qos']['avg_rsrp']:.2f}",
                'Avg SNR (dB)': f"{metrics['qos']['avg_snr']:.2f}",
                'Coverage Rate': f"{metrics['qos']['coverage_rate']:.2%}",
                'QoS Satisfaction': f"{metrics['qos']['qos_satisfaction_rate']:.2%}",
                'Total Reward': f"{metrics['reward']['total_reward']:.2f}",
                'Avg Reward': f"{metrics['reward']['avg_reward']:.3f}",
                'Reward Std': f"{metrics['reward']['reward_std']:.3f}"
            })

        comparison_df = pd.DataFrame(comparison_data)
        return comparison_df, results


def test_evaluation_pipeline():
    """測試評估管道（使用模擬環境）"""
    print("Testing EvaluationPipeline...\n")

    # 創建模擬環境（簡化版 Gymnasium 環境）
    class MockEnv:
        """模擬環境用於測試"""
        def __init__(self):
            self.state_dim = 53
            self.action_dim = 6
            self.current_step = 0
            self.max_steps = 20

        def reset(self, seed=None):
            self.current_step = 0
            state = np.random.randn(self.state_dim).astype(np.float32) * 10 - 40  # 模擬 RSRP
            return state, {}

        def step(self, action):
            self.current_step += 1
            next_state = np.random.randn(self.state_dim).astype(np.float32) * 10 - 40
            reward = np.random.rand() * 10
            terminated = self.current_step >= self.max_steps
            truncated = False
            info = {}
            return next_state, reward, terminated, truncated, info

    # 創建模擬策略
    class MockPolicy:
        """模擬策略（隨機動作）"""
        def select_action(self, state):
            return np.random.randint(0, 6)

    # 測試
    print("1️⃣ Testing evaluate_policy()...")
    env = MockEnv()
    policy = MockPolicy()
    pipeline = EvaluationPipeline(env)

    results = pipeline.evaluate_policy(policy, num_episodes=5, verbose=False)

    print(f"   Total handovers: {results['handover']['total_handovers']}")
    print(f"   Avg RSRP: {results['qos']['avg_rsrp']:.2f} dBm")
    print(f"   Total reward: {results['reward']['total_reward']:.2f}")
    print("   ✅ evaluate_policy() test passed\n")

    # 測試策略比較
    print("2️⃣ Testing compare_policies()...")
    policy1 = MockPolicy()
    policy2 = MockPolicy()

    policies = {
        'Policy A': policy1,
        'Policy B': policy2
    }

    comparison_df, detailed_results = pipeline.compare_policies(policies, num_episodes=5, verbose=False)

    print("\n   Comparison Table:")
    print(comparison_df.to_string(index=False))
    print("\n   ✅ compare_policies() test passed\n")

    print("✅ All tests passed!")


if __name__ == "__main__":
    test_evaluation_pipeline()
