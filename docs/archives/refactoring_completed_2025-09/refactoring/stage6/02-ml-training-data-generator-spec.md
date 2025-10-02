# ML 訓練數據生成器規格 - Stage 6 核心組件

**檔案**: `src/stages/stage6_research_optimization/ml_training_data_generator.py`
**依據**: `docs/stages/stage6-research-optimization.md` Line 91-96, 597-623
**目標**: 生成 50,000+ 高品質 ML 訓練樣本

---

## 🎯 核心職責

生成用於強化學習換手優化的訓練數據：
1. **狀態空間構建**: 7維+ 衛星狀態向量
2. **動作空間編碼**: 換手決策 (保持/切換至候選1/2/3...)
3. **獎勵函數計算**: 基於 QoS、中斷時間、信號品質的複合獎勵
4. **經驗回放**: 大量真實換手場景存儲供算法學習

支援算法：
- **DQN** (Deep Q-Network)
- **A3C** (Asynchronous Advantage Actor-Critic)
- **PPO** (Proximal Policy Optimization)
- **SAC** (Soft Actor-Critic)

---

## 🏗️ 類別設計

```python
class MLTrainingDataGenerator:
    """ML 訓練數據生成器"""

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
        pass

    def generate_dqn_dataset(
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
        pass

    def generate_a3c_dataset(
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
        pass

    def generate_ppo_dataset(
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
        pass

    def generate_sac_dataset(
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
        pass

    def build_state_vector(
        self,
        satellite_data: Dict[str, Any]
    ) -> List[float]:
        """構建狀態向量 (7維標準)

        Args:
            satellite_data: 單顆衛星的信號分析數據

        Returns:
            [latitude, longitude, altitude, rsrp, elevation, distance, sinr]
        """
        state_vector = [
            satellite_data['current_position']['latitude_deg'],
            satellite_data['current_position']['longitude_deg'],
            satellite_data['current_position']['altitude_km'],
            satellite_data['signal_quality']['rsrp_dbm'],
            satellite_data['visibility_metrics']['elevation_deg'],
            satellite_data['physical_parameters']['distance_km'],
            satellite_data['signal_quality']['rs_sinr_db']
        ]

        return state_vector

    def encode_action(
        self,
        action_type: str,
        candidate_satellite_id: Optional[str] = None
    ) -> Tuple[int, List[int]]:
        """編碼動作

        Args:
            action_type: 'maintain' 或 'handover'
            candidate_satellite_id: 目標衛星 ID (換手時)

        Returns:
            (action_index, one_hot_encoding)
        """
        pass

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

        # 1. QoS 改善
        current_rsrp = current_state['signal_quality']['rsrp_dbm']
        next_rsrp = next_state['signal_quality']['rsrp_dbm']
        rsrp_improvement = (next_rsrp - current_rsrp) / 20.0  # 標準化到 [-1, 1]
        reward_components['qos_improvement'] = max(0, rsrp_improvement)

        # 2. 中斷懲罰
        if next_state['quality_assessment']['is_usable'] == False:
            reward_components['interruption_penalty'] = -0.5
        else:
            reward_components['interruption_penalty'] = 0.0

        # 3. 信號品質獎勵
        quality_score = next_state['quality_assessment']['quality_score']
        reward_components['signal_quality_gain'] = quality_score

        # 4. 換手成本
        if action == 'handover':
            reward_components['handover_cost'] = -0.1
        else:
            reward_components['handover_cost'] = 0.0

        total_reward = sum(reward_components.values())

        return total_reward, reward_components

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數"""
        default_config = {
            'state_space_dimensions': 7,
            'action_space_size': 5,
            'reward_function_type': 'composite_qos_interruption_quality',
            'experience_replay_size': 100000,
            'batch_size': 256,
            'learning_rate': 0.001,
            'discount_factor': 0.99
        }

        if config:
            default_config.update(config)

        return default_config
```

---

## 📊 輸出數據格式

### DQN 數據集範例
```python
{
    'state_vectors': [
        [25.1234, 121.5678, 550.123, -85.2, 15.5, 750.2, 12.8],  # 衛星1狀態
        [25.2345, 121.6789, 555.234, -88.1, 18.3, 820.5, 10.2],  # 衛星2狀態
        # ... 50,000+ 樣本
    ],
    'action_space': ['maintain', 'handover_to_candidate_1', 'handover_to_candidate_2',
                     'handover_to_candidate_3', 'handover_to_candidate_4'],
    'q_values': [
        [0.89, -0.12, 0.76, 0.45, 0.23],  # 5個動作的Q值
        [0.92, -0.08, 0.71, 0.38, 0.15],
        # ... 對應每個狀態
    ],
    'reward_values': [0.89, 0.76, 0.45, ...],  # 實際獎勵
    'next_state_vectors': [
        [25.1235, 121.5679, 550.124, -84.8, 15.6, 748.5, 13.1],
        # ... 下一狀態
    ],
    'done_flags': [False, False, True, ...],  # 終止標記
    'dataset_size': 50000
}
```

### ML 訓練樣本詳細格式
```python
{
    'sample_id': 'SAMPLE_1695024000789',
    'timestamp': '2025-09-27T08:00:00.789123+00:00',
    'state_vector': {
        'serving_satellite': {
            'latitude_deg': 25.1234,
            'longitude_deg': 121.5678,
            'altitude_km': 550.123,
            'rsrp_dbm': -85.2,
            'elevation_deg': 15.5,
            'distance_km': 750.2,
            'sinr_db': 12.8
        },
        'candidate_satellites': [
            # 候選衛星狀態向量
        ],
        'system_state': {
            'current_qos': 0.89,
            'handover_count_last_hour': 3,
            'coverage_gap_risk': 0.12
        }
    },
    'action_taken': 'handover_to_candidate_1',
    'action_encoding': [0, 1, 0, 0, 0],  # one-hot encoding
    'reward_received': 0.76,
    'reward_components': {
        'qos_improvement': 0.15,
        'interruption_penalty': -0.02,
        'signal_quality_gain': 0.63,
        'handover_cost': 0.0
    },
    'next_state_vector': {
        # 下一狀態向量
    },
    'algorithm_metadata': {
        'dqn_q_value': 0.76,
        'a3c_policy_prob': 0.83,
        'ppo_advantage': 0.21,
        'sac_entropy': 0.67
    }
}
```

---

## ✅ 實現檢查清單

### 功能完整性
- [ ] DQN 數據集生成
- [ ] A3C 數據集生成
- [ ] PPO 數據集生成
- [ ] SAC 數據集生成
- [ ] 狀態向量構建 (7維)
- [ ] 動作編碼 (one-hot)
- [ ] 複合獎勵函數計算
- [ ] 經驗回放緩衝區管理

### 數據品質
- [ ] 50,000+ 樣本生成能力
- [ ] 狀態向量完整性檢查
- [ ] 動作空間合理性驗證
- [ ] 獎勵函數設計正確性
- [ ] 數據標準化處理

### 算法支援
- [ ] DQN 格式正確
- [ ] A3C 格式正確
- [ ] PPO 格式正確
- [ ] SAC 格式正確
- [ ] 跨算法數據一致性

### 性能要求
- [ ] < 0.1秒 生成 1000 樣本
- [ ] 記憶體效率優化
- [ ] 大規模數據集支援

### 單元測試
- [ ] 狀態向量構建測試
- [ ] 動作編碼測試
- [ ] 獎勵函數測試
- [ ] 各算法數據集測試
- [ ] 邊界條件測試

---

## 📚 學術參考

1. Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. *Nature*, 518(7540), 529-533.

2. Mnih, V., et al. (2016). Asynchronous methods for deep reinforcement learning. *ICML*.

3. Schulman, J., et al. (2017). Proximal policy optimization algorithms. *arXiv preprint arXiv:1707.06347*.

4. Haarnoja, T., et al. (2018). Soft actor-critic: Off-policy maximum entropy deep reinforcement learning with a stochastic actor. *ICML*.

---

**規格版本**: v1.0
**創建日期**: 2025-09-30
**狀態**: 待實現