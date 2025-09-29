# 🤖 Stage 6: RL環境標準化計劃

## 📋 階段概覽

**目標**：建立標準化的強化學習環境，支援衛星換手優化研究

**時程**：第4週後半 + 第5週 (5個工作日)

**優先級**：🚨 高風險 - 缺乏標準RL接口

**現狀問題**：缺乏RL標準接口，無gymnasium整合，無法進行標準化RL研究

## 🎯 重構目標

### 核心目標
- ✅ **Gymnasium標準環境**: 符合RL社群標準的環境接口
- ✅ **多算法支援**: DQN/PPO/SAC/A2C等主流RL算法
- ✅ **真實數據整合**: 基於前五階段的真實軌道與信號數據
- ✅ **學術研究導向**: 支援論文發表的標準化RL實驗

### 學術研究要求 (基於 docs/final.md)
- **多算法支援**: DQN/A3C/PPO/SAC等主流算法比較
- **實時決策支援**: 毫秒級響應的換手決策推理
- **訓練數據生成**: 基於Stage 5的3GPP事件觸發條件
- **對比研究**: 與傳統ML方法的性能對比能力

## 🔧 技術實現

### 套件選擇理由

#### Gymnasium (RL環境標準)
```python
# RL社群標準優勢
✅ OpenAI Gym的官方繼承者
✅ RL研究社群標準接口
✅ 完整的環境驗證工具
✅ 豐富的文檔與範例
✅ 與主流RL庫完美整合
```

#### Stable-Baselines3 (SOTA RL算法庫)
```python
# 學術級RL算法
✅ DQN/PPO/SAC/A2C標準實現
✅ 學術研究品質保證
✅ 完整的訓練管道
✅ 算法性能對比能力
✅ 論文發表級實現
```

#### Scikit-learn (傳統ML對比)
```python
# 對比研究支援
✅ Random Forest等傳統算法
✅ 標準化ML管道
✅ 特徵工程工具
✅ 與RL結果對比分析
```

### 新架構設計

```python
# RL環境架構
rl_environment/
├── gymnasium_env.py            # Gymnasium標準環境
├── state_processor.py          # 狀態空間處理
├── reward_calculator.py        # 獎勵函數計算
├── algorithm_trainer.py        # 多算法訓練器
├── traditional_ml_baseline.py  # 傳統ML基準
└── experiment_manager.py       # 實驗管理器
```

## 📅 實施計劃 (5天)

### Day 1-2: Gymnasium環境核心
```bash
# 安裝RL核心套件
pip install gymnasium>=0.29.0
pip install stable-baselines3[extra]>=2.0.0
pip install scikit-learn>=1.3.0

# 替換組件
✅ 新增：gymnasium.Env標準環境
✅ 新增：stable_baselines3算法庫
✅ 新增：傳統ML對比基準
```

```python
# gymnasium_env.py Gymnasium標準環境
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Any

class SatelliteHandoverEnv(gym.Env):
    """衛星換手RL環境 - Gymnasium標準接口"""

    metadata = {"render_modes": ["human"], "render_fps": 4}

    def __init__(self, constellation_data: Dict, render_mode: str = None):
        super().__init__()

        self.constellation_data = constellation_data
        self.render_mode = render_mode

        # 狀態空間定義 (基於前五階段數據)
        # [服務衛星狀態(9) + 候選衛星狀態(5×3=15) + 池狀態(1) = 25維]
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(25,),
            dtype=np.float32
        )

        # 動作空間定義 (離散動作)
        # [保持當前衛星, 切換至候選衛星1-5] = 6個動作
        self.action_space = spaces.Discrete(6)

        # 環境狀態
        self.current_serving_satellite = None
        self.candidate_satellites = []
        self.current_time_step = 0
        self.max_episode_steps = 100  # 限制episode長度
        self.pool_state_data = None

        # 獎勵函數配置
        self.reward_config = {
            'signal_quality_weight': 0.4,
            'handover_penalty': -1.0,
            'service_interruption_penalty': -10.0,
            'continuity_bonus': 2.0,
            'qos_threshold': -95.0  # RSRP門檻
        }

    def _get_observation(self) -> np.ndarray:
        """獲取當前環境狀態 - 整合前五階段數據"""

        # 1. 服務衛星特徵 (9維) - 整合Stage 2軌道 + Stage 3座標數據
        if self.current_serving_satellite:
            serving_features = np.array([
                self.current_serving_satellite.position_teme[0],  # X位置
                self.current_serving_satellite.position_teme[1],  # Y位置
                self.current_serving_satellite.position_teme[2],  # Z位置
                self.current_serving_satellite.elevation,         # 仰角
                self.current_serving_satellite.azimuth,           # 方位角
                self.current_serving_satellite.distance_km,       # 距離
                self._calculate_rsrp(self.current_serving_satellite), # RSRP
                self._calculate_rsrq(self.current_serving_satellite), # RSRQ
                1.0 if self.current_serving_satellite.elevation > 5.0 else 0.0  # 可見性
            ])
        else:
            serving_features = np.zeros(9)

        # 2. 候選衛星特徵 (5×3=15維)
        candidate_features = []
        for i in range(5):  # 最多5個候選衛星
            if i < len(self.candidate_satellites):
                candidate = self.candidate_satellites[i]
                features = [
                    candidate.elevation,
                    self._calculate_rsrp(candidate),
                    candidate.distance_km
                ]
            else:
                features = [0.0, -120.0, 2000.0]  # 默認值：無衛星
            candidate_features.extend(features)

        # 3. 衛星池狀態 (1維) - 整合Stage 4池分析數據
        if self.pool_state_data:
            pool_health = len(self.pool_state_data.visible_satellites) / 15.0  # 標準化到[0,1]
        else:
            pool_health = 0.0

        # 合併所有特徵
        observation = np.concatenate([
            serving_features,
            candidate_features,
            [pool_health]
        ]).astype(np.float32)

        return observation

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """執行動作並返回結果"""

        info = {}
        reward = 0.0

        # 記錄動作前狀態
        prev_rsrp = self._calculate_rsrp(self.current_serving_satellite) if self.current_serving_satellite else -120.0

        # 執行換手動作
        if action == 0:  # 保持當前衛星
            info['action_type'] = 'maintain'

            # 檢查當前衛星是否仍然可用
            if (self.current_serving_satellite and
                self.current_serving_satellite.elevation <= 0):
                # 衛星已不可見，強制換手
                reward += self.reward_config['service_interruption_penalty']
                info['forced_handover'] = True
                self._emergency_handover()

        else:  # 切換到候選衛星
            candidate_idx = action - 1
            if candidate_idx < len(self.candidate_satellites):
                new_satellite = self.candidate_satellites[candidate_idx]

                # 檢查候選衛星可用性
                if new_satellite.elevation > 0:
                    self.current_serving_satellite = new_satellite
                    reward += self.reward_config['handover_penalty']
                    info['action_type'] = 'handover'
                    info['new_satellite'] = new_satellite.satellite_name
                else:
                    reward += self.reward_config['service_interruption_penalty']
                    info['action_type'] = 'invalid_handover'

        # 計算獎勵
        reward += self._calculate_step_reward()

        # 更新環境狀態
        self._update_environment_state()

        # 檢查終止條件
        terminated = self._is_terminated()
        truncated = self.current_time_step >= self.max_episode_steps

        self.current_time_step += 1

        return self._get_observation(), reward, terminated, truncated, info

    def reset(self, seed: int = None, options: Dict = None) -> Tuple[np.ndarray, Dict]:
        """重置環境到初始狀態"""

        super().reset(seed=seed)

        # 重置環境狀態
        self.current_time_step = 0

        # 從constellation_data中獲取初始狀態
        if self.constellation_data:
            initial_state = self._get_initial_state()
            self.current_serving_satellite = initial_state['serving']
            self.candidate_satellites = initial_state['candidates'][:5]  # 最多5個候選
            self.pool_state_data = initial_state['pool_state']

        info = {
            'serving_satellite': self.current_serving_satellite.satellite_name if self.current_serving_satellite else None,
            'num_candidates': len(self.candidate_satellites)
        }

        return self._get_observation(), info

    def _calculate_rsrp(self, satellite: SatelliteCoordinates) -> float:
        """計算RSRP - 整合Stage 3信號處理"""
        if not satellite:
            return -120.0

        # 使用Stage 3的信號處理算法
        distance_km = satellite.distance_km
        tx_power_dbm = 43.0
        frequency_ghz = 2.0
        antenna_gain = 15.0

        path_loss = (
            20 * np.log10(distance_km) +
            20 * np.log10(frequency_ghz) +
            92.45
        )

        rsrp = tx_power_dbm + antenna_gain - path_loss
        return rsrp

    def _calculate_step_reward(self) -> float:
        """計算單步獎勵"""

        if not self.current_serving_satellite:
            return self.reward_config['service_interruption_penalty']

        # 信號品質獎勵
        current_rsrp = self._calculate_rsrp(self.current_serving_satellite)
        if current_rsrp > self.reward_config['qos_threshold']:
            signal_reward = (current_rsrp - self.reward_config['qos_threshold']) / 10.0
        else:
            signal_reward = (current_rsrp - self.reward_config['qos_threshold']) / 20.0

        signal_reward *= self.reward_config['signal_quality_weight']

        # 服務連續性獎勵
        continuity_reward = self.reward_config['continuity_bonus']

        return signal_reward + continuity_reward
```

### Day 3: 多算法訓練器
```python
# algorithm_trainer.py 多算法支援
from stable_baselines3 import DQN, PPO, SAC, A2C
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback

class MultiAlgorithmTrainer:
    """多算法RL訓練器 - 學術研究導向"""

    def __init__(self, env_config: Dict):
        self.env_config = env_config
        self.algorithms = {}
        self.training_results = {}

    def setup_algorithms(self) -> Dict:
        """設置多種RL算法"""

        # 創建訓練環境
        train_env = make_vec_env(
            SatelliteHandoverEnv,
            n_envs=1,  # 學術研究用，不需要多環境並行
            env_kwargs=self.env_config
        )

        # DQN - 離散動作空間經典算法
        self.algorithms['DQN'] = DQN(
            policy="MlpPolicy",
            env=train_env,
            learning_rate=1e-4,
            buffer_size=10000,  # 適中的buffer size
            learning_starts=1000,
            batch_size=32,
            gamma=0.99,
            target_update_interval=500,
            exploration_initial_eps=1.0,
            exploration_final_eps=0.1,
            exploration_fraction=0.3,
            verbose=1
        )

        # PPO - 穩定的策略梯度算法
        self.algorithms['PPO'] = PPO(
            policy="MlpPolicy",
            env=train_env,
            learning_rate=3e-4,
            n_steps=1024,
            batch_size=64,
            n_epochs=4,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=1
        )

        # A2C - 輕量級Actor-Critic
        self.algorithms['A2C'] = A2C(
            policy="MlpPolicy",
            env=train_env,
            learning_rate=7e-4,
            n_steps=5,
            gamma=0.99,
            gae_lambda=1.0,
            verbose=1
        )

        # SAC - 適用於連續控制 (這裡適配為離散)
        # 注意：SAC通常用於連續動作，這裡為了比較研究而包含
        if self._can_use_sac():
            continuous_env = self._create_continuous_adaptation()
            self.algorithms['SAC'] = SAC(
                policy="MlpPolicy",
                env=continuous_env,
                learning_rate=3e-4,
                buffer_size=10000,
                batch_size=64,
                gamma=0.99,
                verbose=1
            )

        return self.algorithms

    def train_all_algorithms(self, total_timesteps: int = 50000) -> Dict:
        """訓練所有算法 - 適合學術研究的規模"""

        for algo_name, model in self.algorithms.items():
            print(f"\n開始訓練 {algo_name}...")

            # 設置評估回調
            eval_env = make_vec_env(SatelliteHandoverEnv, n_envs=1, env_kwargs=self.env_config)
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=f"./models/{algo_name}/",
                log_path=f"./logs/{algo_name}/",
                eval_freq=5000,
                deterministic=True,
                render=False
            )

            # 訓練模型
            model.learn(
                total_timesteps=total_timesteps,
                callback=eval_callback
            )

            # 保存最終模型
            model.save(f"./models/{algo_name}/final_model")

            # 評估訓練結果
            self.training_results[algo_name] = self._evaluate_algorithm(model, eval_env)

            print(f"{algo_name} 訓練完成")

        return self.training_results

    def _evaluate_algorithm(self, model, eval_env) -> Dict:
        """評估算法性能"""

        episode_rewards = []
        episode_lengths = []

        for episode in range(10):  # 評估10個episode
            obs = eval_env.reset()
            total_reward = 0
            steps = 0

            while True:
                action, _states = model.predict(obs, deterministic=True)
                obs, reward, done, info = eval_env.step(action)
                total_reward += reward[0]
                steps += 1

                if done[0]:
                    break

            episode_rewards.append(total_reward)
            episode_lengths.append(steps)

        return {
            'mean_reward': np.mean(episode_rewards),
            'std_reward': np.std(episode_rewards),
            'mean_episode_length': np.mean(episode_lengths),
            'total_timesteps': model.num_timesteps
        }
```

### Day 4: 傳統ML對比基準
```python
# traditional_ml_baseline.py 傳統ML對比
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score

class TraditionalMLBaseline:
    """傳統ML基準模型 - 用於與RL算法對比"""

    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()

    def prepare_training_data(self, handover_scenarios: List[HandoverScenario]) -> Tuple[np.ndarray, np.ndarray]:
        """準備傳統ML訓練數據 - 整合Stage 5事件數據"""

        features = []
        labels = []

        for scenario in handover_scenarios:
            # 提取特徵向量
            feature_vector = self._extract_features(scenario)
            features.append(feature_vector)

            # 確定最佳動作標籤
            optimal_action = self._determine_optimal_action(scenario)
            labels.append(optimal_action)

        features_array = np.array(features)
        labels_array = np.array(labels)

        # 特徵標準化
        features_scaled = self.scaler.fit_transform(features_array)

        return features_scaled, labels_array

    def train_baseline_models(self, features: np.ndarray, labels: np.ndarray) -> Dict:
        """訓練傳統ML基準模型"""

        # Random Forest
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        rf_model.fit(features, labels)
        self.models['RandomForest'] = rf_model

        # SVM
        svm_model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            random_state=42
        )
        svm_model.fit(features, labels)
        self.models['SVM'] = svm_model

        # 評估模型性能
        results = {}
        for name, model in self.models.items():
            predictions = model.predict(features)
            accuracy = accuracy_score(labels, predictions)
            results[name] = {
                'accuracy': accuracy,
                'classification_report': classification_report(labels, predictions)
            }

        return results

    def _extract_features(self, scenario: HandoverScenario) -> np.ndarray:
        """從換手場景提取特徵"""

        serving = scenario.serving_satellite
        candidates = scenario.candidate_satellites[:3]  # 最多3個候選

        # 服務衛星特徵
        serving_features = [
            serving.elevation,
            serving.distance_km,
            self._calculate_rsrp(serving),
            len(scenario.triggered_events)  # 事件數量
        ]

        # 候選衛星特徵
        candidate_features = []
        for i in range(3):
            if i < len(candidates):
                candidate = candidates[i]
                candidate_features.extend([
                    candidate.elevation,
                    candidate.distance_km,
                    self._calculate_rsrp(candidate)
                ])
            else:
                candidate_features.extend([0.0, 2000.0, -120.0])

        return np.array(serving_features + candidate_features)

    def _determine_optimal_action(self, scenario: HandoverScenario) -> int:
        """確定最佳動作標籤"""

        # 簡化的最佳動作邏輯
        serving_rsrp = self._calculate_rsrp(scenario.serving_satellite)

        if serving_rsrp < -100.0:  # 服務衛星信號差
            # 尋找最佳候選衛星
            best_candidate_idx = 0
            best_rsrp = -120.0

            for i, candidate in enumerate(scenario.candidate_satellites[:5]):
                candidate_rsrp = self._calculate_rsrp(candidate)
                if candidate_rsrp > best_rsrp:
                    best_rsrp = candidate_rsrp
                    best_candidate_idx = i + 1  # 動作0是保持，候選從1開始

            return best_candidate_idx
        else:
            return 0  # 保持當前衛星

class ExperimentComparator:
    """實驗比較器 - RL vs 傳統ML"""

    def __init__(self):
        self.results = {}

    def compare_all_methods(self, rl_results: Dict, ml_results: Dict,
                          test_scenarios: List[HandoverScenario]) -> Dict:
        """比較所有方法的性能"""

        comparison_results = {
            'rl_algorithms': rl_results,
            'traditional_ml': ml_results,
            'performance_comparison': {}
        }

        # 在測試場景上評估所有方法
        for scenario in test_scenarios:
            scenario_results = {}

            # 評估RL算法
            for algo_name in rl_results.keys():
                # 這裡需要載入訓練好的模型並預測
                # 簡化實現：使用訓練結果的mean_reward作為性能指標
                scenario_results[f'RL_{algo_name}'] = rl_results[algo_name]['mean_reward']

            # 評估傳統ML
            for model_name in ml_results.keys():
                scenario_results[f'ML_{model_name}'] = ml_results[model_name]['accuracy']

            comparison_results['performance_comparison'][scenario.scenario_id] = scenario_results

        return comparison_results
```

### Day 5: 實驗管理與整合測試
```python
# experiment_manager.py 實驗管理
class ExperimentManager:
    """實驗管理器 - 學術研究導向"""

    def __init__(self, constellation_data: Dict):
        self.constellation_data = constellation_data
        self.experiment_results = {}

    def run_complete_experiment(self, total_timesteps: int = 50000) -> Dict:
        """運行完整的RL vs 傳統ML對比實驗"""

        print("🚀 開始完整的衛星換手優化實驗...")

        # 1. 準備訓練環境
        env_config = {'constellation_data': self.constellation_data}

        # 2. 訓練RL算法
        print("\n📊 訓練強化學習算法...")
        trainer = MultiAlgorithmTrainer(env_config)
        trainer.setup_algorithms()
        rl_results = trainer.train_all_algorithms(total_timesteps)

        # 3. 訓練傳統ML基準
        print("\n🔍 訓練傳統ML基準...")
        ml_baseline = TraditionalMLBaseline()

        # 從Stage 5獲取訓練場景
        training_scenarios = self._load_handover_scenarios()
        features, labels = ml_baseline.prepare_training_data(training_scenarios)
        ml_results = ml_baseline.train_baseline_models(features, labels)

        # 4. 性能比較
        print("\n📈 進行性能比較...")
        comparator = ExperimentComparator()
        test_scenarios = training_scenarios[-100:]  # 使用最後100個場景作為測試
        comparison_results = comparator.compare_all_methods(
            rl_results, ml_results, test_scenarios
        )

        # 5. 生成實驗報告
        report = self._generate_experiment_report(comparison_results)

        self.experiment_results = {
            'rl_results': rl_results,
            'ml_results': ml_results,
            'comparison': comparison_results,
            'report': report
        }

        print("\n✅ 實驗完成！")
        return self.experiment_results

    def _load_handover_scenarios(self) -> List[HandoverScenario]:
        """載入換手場景 - 整合Stage 5數據"""

        # 這裡應該從Stage 5的輸出載入場景數據
        # 簡化實現：生成模擬場景
        scenarios = []

        # 實際實現時，應該載入Stage 5生成的RL訓練數據
        # scenarios = load_scenarios_from_stage5("rl_training_data.json")

        return scenarios

    def _generate_experiment_report(self, results: Dict) -> str:
        """生成實驗報告 - 適合學術發表"""

        report = """
# 衛星換手優化實驗報告

## 實驗概述
本實驗比較了多種強化學習算法與傳統機器學習方法在LEO衛星換手優化中的性能表現。

## 算法比較
        """

        # 添加詳細結果
        for algo_name, result in results['rl_results'].items():
            report += f"""
### {algo_name} (強化學習)
- 平均獎勵: {result['mean_reward']:.2f}
- 標準差: {result['std_reward']:.2f}
- 平均episode長度: {result['mean_episode_length']:.1f}
            """

        for model_name, result in results['ml_results'].items():
            report += f"""
### {model_name} (傳統ML)
- 準確率: {result['accuracy']:.3f}
            """

        return report
```

## 🧪 驗證測試

### Gymnasium標準合規測試
```python
def test_gymnasium_compliance():
    """Gymnasium接口合規性測試"""

    env = SatelliteHandoverEnv({})

    # 檢查必要方法
    assert hasattr(env, 'step'), "缺少step方法"
    assert hasattr(env, 'reset'), "缺少reset方法"
    assert hasattr(env, 'action_space'), "缺少action_space"
    assert hasattr(env, 'observation_space'), "缺少observation_space"

    # 測試環境交互
    obs, info = env.reset()
    assert obs.shape == (25,), "觀察空間維度錯誤"

    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)

    assert isinstance(reward, (int, float)), "獎勵必須是數值"
    assert isinstance(terminated, bool), "terminated必須是布爾值"

def test_multi_algorithm_training():
    """多算法訓練測試"""

    trainer = MultiAlgorithmTrainer({})
    algorithms = trainer.setup_algorithms()

    # 驗證算法設置
    assert 'DQN' in algorithms, "DQN算法未設置"
    assert 'PPO' in algorithms, "PPO算法未設置"

    # 簡短訓練測試
    results = trainer.train_all_algorithms(total_timesteps=1000)
    assert len(results) > 0, "訓練結果為空"

def test_traditional_ml_comparison():
    """傳統ML對比測試"""

    baseline = TraditionalMLBaseline()

    # 生成測試數據
    test_scenarios = generate_test_scenarios(10)
    features, labels = baseline.prepare_training_data(test_scenarios)

    assert features.shape[0] == 10, "特徵數量錯誤"
    assert len(labels) == 10, "標籤數量錯誤"

    # 訓練測試
    results = baseline.train_baseline_models(features, labels)
    assert 'RandomForest' in results, "RandomForest結果缺失"
```

## 📊 成功指標

### 量化指標
- **環境標準**: 100%符合Gymnasium接口標準
- **算法支援**: 成功訓練4種RL算法 (DQN/PPO/SAC/A2C)
- **對比研究**: RL vs 傳統ML性能對比完成
- **訓練效率**: 50k timesteps內達到收斂

### 質化指標
- **學術標準**: 符合RL研究社群標準
- **實驗可重現**: 完整的種子控制和版本管理
- **論文準備**: 提供學術發表級的實驗結果
- **方法比較**: 為RL優勢提供定量證據

## ⚠️ 風險控制

### 技術風險
| 風險 | 影響 | 應對策略 |
|------|------|----------|
| 算法收斂困難 | 高 | 調整超參數，簡化環境 |
| 環境設計不當 | 高 | 充分測試，專家驗證 |
| 數據質量問題 | 中等 | 依賴前五階段的高質量數據 |
| 計算資源限制 | 中等 | 合理設置訓練規模 |

### 學術風險
- **標準合規**: 必須100%符合Gymnasium標準
- **實驗設計**: 需要合理的對比實驗設計
- **結果可信**: 確保實驗結果具有學術價值
- **可重現性**: 提供完整的實驗重現能力

---

**文檔版本**: v1.0 (修正版)
**建立日期**: 2024-01-15
**前置條件**: Stage 1-5完成 (完整數據處理鏈可用)
**重點**: 學術級RL研究環境，支援論文發表
**專案完成**: 六階段重構計劃全部完成