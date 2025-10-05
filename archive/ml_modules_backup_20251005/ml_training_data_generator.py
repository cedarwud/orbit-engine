"""
ML 訓練數據生成器 - Stage 6 核心組件

生成用於強化學習換手優化的訓練數據。

依據:
- docs/stages/stage6-research-optimization.md Line 91-96, 597-623
- docs/refactoring/stage6/02-ml-training-data-generator-spec.md

學術參考:
1. Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. Nature, 518(7540), 529-533.
2. Mnih, V., et al. (2016). Asynchronous methods for deep reinforcement learning. ICML.
3. Schulman, J., et al. (2017). Proximal policy optimization algorithms. arXiv:1707.06347.
4. Haarnoja, T., et al. (2018). Soft actor-critic: Off-policy maximum entropy deep RL. ICML.

Author: ORBIT Engine Team
Created: 2025-09-30
Refactored: 2025-10-02

🎓 學術合規性檢查提醒:
- 修改此文件前，請先閱讀: docs/stages/STAGE6_COMPLIANCE_CHECKLIST.md
- 重點檢查: 禁止使用 np.random() 生成數據、所有ML超參數必須有論文引用
- 已修正: P0-1 移除隨機數生成、P0-3 使用Softmax策略、P2-2 添加ML超參數引用
- 禁用詞: 假設、估計、簡化、模擬
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .state_action_encoder import StateActionEncoder
from .reward_calculator import RewardCalculator
from .policy_value_estimator import PolicyValueEstimator
from .datasets import (
    DQNDatasetGenerator,
    A3CDatasetGenerator,
    PPODatasetGenerator,
    SACDatasetGenerator
)


class MLTrainingDataGenerator:
    """ML 訓練數據生成器

    主協調器，負責:
    1. 初始化所有組件 (編碼器、計算器、估計器、數據集生成器)
    2. 協調各組件生成訓練數據
    3. 管理配置和統計信息

    支援強化學習算法:
    - DQN (Deep Q-Network)
    - A3C (Asynchronous Advantage Actor-Critic)
    - PPO (Proximal Policy Optimization)
    - SAC (Soft Actor-Critic)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化生成器

        Args:
            config: 配置參數
                - state_space_dimensions: 狀態空間維度 (預設 7)
                - action_space_size: 動作空間大小 (預設 5)
                - reward_function_type: 獎勵函數類型
                - experience_replay_size: 經驗回放緩衝區大小
        """
        self.config = self._load_config(config)
        self.logger = logging.getLogger(__name__)

        # 動作空間定義
        self.action_space = [
            'maintain',
            'handover_to_candidate_1',
            'handover_to_candidate_2',
            'handover_to_candidate_3',
            'handover_to_candidate_4'
        ]

        # 初始化組件
        self.state_encoder = StateActionEncoder(self.action_space)
        self.reward_calculator = RewardCalculator()
        self.policy_value_estimator = PolicyValueEstimator(
            self.action_space,
            self.config
        )

        # 初始化數據集生成器
        self.dqn_generator = DQNDatasetGenerator(
            self.state_encoder,
            self.reward_calculator,
            self.policy_value_estimator,
            self.action_space
        )

        self.a3c_generator = A3CDatasetGenerator(
            self.state_encoder,
            self.reward_calculator,
            self.policy_value_estimator,
            self.config
        )

        self.ppo_generator = PPODatasetGenerator(
            self.state_encoder,
            self.reward_calculator,
            self.policy_value_estimator,
            self.action_space,
            self.config
        )

        self.sac_generator = SACDatasetGenerator(
            self.state_encoder,
            self.reward_calculator,
            self.policy_value_estimator
        )

        # 訓練樣本緩衝區
        self.training_buffer = {
            'dqn_samples': [],
            'a3c_samples': [],
            'ppo_samples': [],
            'sac_samples': []
        }

        # 統計
        self.generation_stats = {
            'total_samples': 0,
            'dqn_samples': 0,
            'a3c_samples': 0,
            'ppo_samples': 0,
            'sac_samples': 0
        }

        self.logger.info("ML 訓練數據生成器初始化完成")

    def generate_all_training_data(
        self,
        signal_analysis: Dict[str, Any],
        gpp_events: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成所有算法的訓練數據

        Args:
            signal_analysis: Stage 5 信號分析數據
            gpp_events: 3GPP 事件數據

        Returns:
            {
                'dqn_dataset': {...},
                'a3c_dataset': {...},
                'ppo_dataset': {...},
                'sac_dataset': {...},
                'dataset_summary': {...}
            }
        """
        self.logger.info("開始生成所有 ML 訓練數據")

        try:
            # 生成各算法數據集
            dqn_dataset = self.dqn_generator.generate(signal_analysis, gpp_events)
            a3c_dataset = self.a3c_generator.generate(signal_analysis, gpp_events)
            ppo_dataset = self.ppo_generator.generate(signal_analysis, gpp_events)
            sac_dataset = self.sac_generator.generate(signal_analysis, gpp_events)

            # 更新統計
            self.generation_stats['dqn_samples'] = dqn_dataset['dataset_size']
            self.generation_stats['a3c_samples'] = a3c_dataset['dataset_size']
            self.generation_stats['ppo_samples'] = ppo_dataset['dataset_size']
            self.generation_stats['sac_samples'] = sac_dataset['dataset_size']
            self.generation_stats['total_samples'] = sum([
                dqn_dataset['dataset_size'],
                a3c_dataset['dataset_size'],
                ppo_dataset['dataset_size'],
                sac_dataset['dataset_size']
            ])

            # 數據集摘要
            dataset_summary = {
                'total_samples': self.generation_stats['total_samples'],
                'dqn_samples': self.generation_stats['dqn_samples'],
                'a3c_samples': self.generation_stats['a3c_samples'],
                'ppo_samples': self.generation_stats['ppo_samples'],
                'sac_samples': self.generation_stats['sac_samples'],
                'generation_timestamp': datetime.utcnow().isoformat() + 'Z',
                'state_space_dimensions': self.config['state_space_dimensions'],
                'action_space_size': self.config['action_space_size']
            }

            self.logger.info(f"ML 訓練數據生成完成 - 總樣本數: {self.generation_stats['total_samples']}")

            return {
                'dqn_dataset': dqn_dataset,
                'a3c_dataset': a3c_dataset,
                'ppo_dataset': ppo_dataset,
                'sac_dataset': sac_dataset,
                'dataset_summary': dataset_summary
            }

        except Exception as e:
            self.logger.error(f"生成 ML 訓練數據時發生錯誤: {str(e)}", exc_info=True)
            return {
                'dqn_dataset': {},
                'a3c_dataset': {},
                'ppo_dataset': {},
                'sac_dataset': {},
                'dataset_summary': {'error': str(e)}
            }

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數

        所有超參數均基於學術論文的標準實驗設置
        """
        default_config = {
            # ============================================================
            # 強化學習環境定義
            # ============================================================
            # SOURCE: docs/stages/stage6-research-optimization.md Line 597-623
            # 依據: 衛星換手決策 MDP 建模
            'state_space_dimensions': 7,  # [lat, lon, alt, rsrp, elev, dist, sinr]
            'action_space_size': 5,       # [maintain, ho_1, ho_2, ho_3, ho_4]

            # ============================================================
            # 獎勵函數配置
            # ============================================================
            # SOURCE: Stage 6 換手決策目標
            # 複合獎勵: QoS改善 + 中斷懲罰 + 信號品質 + 換手成本
            'reward_function_type': 'composite_qos_interruption_quality',

            # ============================================================
            # DQN 超參數
            # ============================================================
            # SOURCE: Mnih et al. (2015) "Human-level control through deep RL"
            #         Nature 518(7540), 529-533
            # 經驗回放緩衝區大小: 100,000 transitions
            'experience_replay_size': 100000,

            # 批次大小: 256
            # SOURCE: Rainbow DQN 改進版本的標準設置
            'batch_size': 256,

            # 學習率: 0.001 (Adam optimizer)
            # SOURCE: 深度強化學習標準學習率
            'learning_rate': 0.001,

            # 折扣因子 γ: 0.99
            # SOURCE: 強化學習標準折扣因子，適合長期規劃任務
            'discount_factor': 0.99,

            # ============================================================
            # PPO 超參數
            # ============================================================
            # SOURCE: Schulman et al. (2017) "Proximal Policy Optimization"
            #         arXiv:1707.06347v2, Section 6.1, Table 3
            # 裁剪參數 ε: 0.2 (論文標準值)
            # 依據: 在 Atari、MuJoCo、Roboschool 環境中驗證
            'ppo_clip_epsilon': 0.2,

            # ============================================================
            # SAC 超參數
            # ============================================================
            # SOURCE: Haarnoja et al. (2018) "Soft Actor-Critic"
            #         ICML 2018, Algorithm 2, Section 5
            # 溫度參數 α: 0.2 (自動調整版本的初始值)
            # 依據: 控制探索與利用的平衡，適合連續控制任務
            'sac_temperature_alpha': 0.2
        }

        if config:
            default_config.update(config)

        return default_config
