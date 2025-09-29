# 🤖 Stage 6 重組計畫 - 研究數據生成與優化層

**目標**: 整合現有優化功能和事件檢測，建立符合 final.md 的完整研究層

## 🎯 重組目標

### 核心功能整合 (符合 final.md 需求)
1. **3GPP NTN 事件檢測**: A4/A5/D2 事件完整實現
2. **動態衛星池規劃**: Starlink 10-15顆, OneWeb 3-6顆時空錯置
3. **強化學習支援**: DQN/A3C/PPO/SAC 訓練數據生成
4. **實時決策支援**: 毫秒級換手決策推理
5. **多目標優化**: 整合現有 Stage 4 的優化算法

## 📂 重組策略

### 整合來源
```bash
# 主要整合來源:
1. src/stages/stage4_optimization/           → 優化算法和決策邏輯
2. src/stages/stage3_signal_analysis/gpp_*   → 3GPP 事件檢測
3. 新實現功能                               → ML 訓練數據生成
```

## 🏗️ 新架構設計

### 目錄結構
```
src/stages/stage6_research_optimization/
├── stage6_research_optimization_processor.py  # 主處理器
├── gpp_event_detector.py                      # 3GPP 事件檢測 (從 Stage 5 移入)
├── dynamic_pool_planner.py                    # 動態池規劃 (從 Stage 4 移入)
├── handover_optimizer.py                      # 換手優化 (從 Stage 4 移入)
├── multi_objective_optimizer.py               # 多目標優化 (從 Stage 4 移入)
├── ml_training_data_generator.py              # ML 訓練數據生成 (新建)
├── real_time_decision_engine.py               # 實時決策引擎 (新建)
├── research_performance_analyzer.py           # 研究分析 (從 Stage 4 移入)
├── config_manager.py                          # 配置管理 (從 Stage 4 移入)
└── __init__.py                                # 模組初始化
```

### 新增子模組
```
src/stages/stage6_research_optimization/ml_support/
├── dqn_data_generator.py                      # DQN 算法支援
├── a3c_data_generator.py                      # A3C 算法支援
├── ppo_data_generator.py                      # PPO 算法支援
├── sac_data_generator.py                      # SAC 算法支援
├── state_space_builder.py                     # 狀態空間構建
├── action_space_manager.py                    # 動作空間管理
├── reward_function_calculator.py              # 獎勵函數計算
└── experience_replay_buffer.py                # 經驗回放緩衝
```

## 🔧 重組步驟

### Step 1: 建立新 Stage 6 目錄結構
```bash
# 建立新目錄
mkdir -p src/stages/stage6_research_optimization/{ml_support,utils}

# 備份現有 stage6_persistence_api
mv src/stages/stage6_persistence_api/ \
   archives/stage6_persistence_api_backup_$(date +%Y%m%d)/
```

### Step 2: 遷移核心優化功能
```bash
# 從 Stage 4 遷移優化算法
cp src/stages/stage4_optimization/pool_planner.py \
   src/stages/stage6_research_optimization/dynamic_pool_planner.py

cp src/stages/stage4_optimization/handover_optimizer.py \
   src/stages/stage6_research_optimization/

cp src/stages/stage4_optimization/multi_obj_optimizer.py \
   src/stages/stage6_research_optimization/

cp src/stages/stage4_optimization/research_performance_analyzer.py \
   src/stages/stage6_research_optimization/

cp src/stages/stage4_optimization/config_manager.py \
   src/stages/stage6_research_optimization/
```

### Step 3: 遷移 3GPP 事件檢測
```bash
# 從 Stage 5 遷移事件檢測
cp src/stages/stage5_signal_analysis/gpp_event_detector.py \
   src/stages/stage6_research_optimization/
```

### Step 4: 實現主處理器
```python
# stage6_research_optimization_processor.py

class Stage6ResearchOptimizationProcessor(BaseStageProcessor):
    """
    Stage 6: 研究數據生成與優化層處理器 (v3.0 完整版)

    專職責任：
    1. 3GPP NTN 事件檢測 (A4/A5/D2)
    2. 動態衛星池規劃 (時空錯置策略)
    3. 強化學習訓練數據生成
    4. 實時決策支援 (毫秒級)
    5. 多目標優化決策
    """

    def __init__(self, config=None):
        super().__init__(stage_number=6, stage_name="research_optimization", config=config)

        # 初始化 3GPP 事件檢測
        self.gpp_detector = GPPEventDetector()

        # 初始化動態池規劃 (原 Stage 4 功能)
        self.pool_planner = DynamicPoolPlanner()

        # 初始化換手優化 (原 Stage 4 功能)
        self.handover_optimizer = HandoverOptimizer()

        # 初始化多目標優化 (原 Stage 4 功能)
        self.multi_obj_optimizer = MultiObjectiveOptimizer()

        # 新增 ML 訓練數據生成
        self.ml_data_generator = MLTrainingDataGenerator()

        # 新增實時決策引擎
        self.decision_engine = RealTimeDecisionEngine()

        # 研究性能分析 (原 Stage 4 功能)
        self.research_analyzer = ResearchPerformanceAnalyzer()

    def process(self, stage5_input):
        """
        主處理流程 - 接收 Stage 5 的信號品質數據

        Args:
            stage5_input: Stage 5 信號品質分析結果

        Returns:
            ProcessingResult: 研究數據和優化決策結果
        """
        # 1. 3GPP NTN 事件檢測
        gpp_events = self._detect_3gpp_events(stage5_input)

        # 2. 動態衛星池規劃 (符合 final.md 要求)
        dynamic_pools = self._plan_dynamic_satellite_pools(stage5_input, gpp_events)

        # 3. 強化學習訓練數據生成
        ml_training_data = self._generate_ml_training_data(
            stage5_input, gpp_events, dynamic_pools
        )

        # 4. 實時決策支援
        real_time_decisions = self._generate_real_time_decisions(
            gpp_events, dynamic_pools
        )

        # 5. 多目標優化 (整合原 Stage 4 功能)
        optimization_results = self._execute_multi_objective_optimization(
            dynamic_pools, gpp_events
        )

        # 6. 構建研究級輸出
        return self._build_research_output(
            gpp_events, dynamic_pools, ml_training_data,
            real_time_decisions, optimization_results
        )

    def _detect_3gpp_events(self, signal_data):
        """檢測 3GPP NTN 事件 - 符合 final.md 要求"""

        # A4 事件: 鄰近衛星變得優於門檻值
        a4_events = self.gpp_detector.detect_a4_events(signal_data)

        # A5 事件: 服務衛星劣於門檻1且鄰近衛星優於門檻2
        a5_events = self.gpp_detector.detect_a5_events(signal_data)

        # D2 事件: 基於距離的換手觸發
        d2_events = self.gpp_detector.detect_d2_events(signal_data)

        return {
            'a4_events': a4_events,
            'a5_events': a5_events,
            'd2_events': d2_events,
            'total_events': len(a4_events) + len(a5_events) + len(d2_events),
            'detection_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _plan_dynamic_satellite_pools(self, signal_data, gpp_events):
        """動態衛星池規劃 - 符合 final.md 時空錯置要求"""

        # Starlink 池規劃: 10-15顆持續可見
        starlink_pool = self.pool_planner.plan_starlink_pool(
            signal_data, target_satellites=(10, 15)
        )

        # OneWeb 池規劃: 3-6顆持續可見
        oneweb_pool = self.pool_planner.plan_oneweb_pool(
            signal_data, target_satellites=(3, 6)
        )

        # 時空錯置策略
        staggered_pools = self.pool_planner.implement_staggered_strategy(
            starlink_pool, oneweb_pool
        )

        return {
            'starlink_pools': starlink_pool,
            'oneweb_pools': oneweb_pool,
            'staggered_strategy': staggered_pools,
            'pool_effectiveness': self.pool_planner.evaluate_pool_effectiveness(
                starlink_pool, oneweb_pool
            )
        }

    def _generate_ml_training_data(self, signal_data, gpp_events, dynamic_pools):
        """生成強化學習訓練數據 - 支援多算法"""

        # 構建狀態空間
        state_space = self.ml_data_generator.build_state_space(
            signal_data, dynamic_pools
        )

        # 定義動作空間 (換手決策)
        action_space = self.ml_data_generator.define_action_space(dynamic_pools)

        # 計算獎勵函數 (基於 QoS, 中斷時間, 信號品質)
        rewards = self.ml_data_generator.calculate_rewards(
            gpp_events, signal_data, dynamic_pools
        )

        # 生成不同算法的訓練數據
        training_data = {
            'dqn': self.ml_data_generator.generate_dqn_data(
                state_space, action_space, rewards
            ),
            'a3c': self.ml_data_generator.generate_a3c_data(
                state_space, action_space, rewards
            ),
            'ppo': self.ml_data_generator.generate_ppo_data(
                state_space, action_space, rewards
            ),
            'sac': self.ml_data_generator.generate_sac_data(
                state_space, action_space, rewards
            )
        }

        return training_data

    def _generate_real_time_decisions(self, gpp_events, dynamic_pools):
        """生成實時決策支援 - 毫秒級響應"""

        # 基於 3GPP 事件的即時決策
        event_based_decisions = self.decision_engine.process_gpp_events(gpp_events)

        # 基於池狀態的預測性決策
        predictive_decisions = self.decision_engine.predict_pool_changes(
            dynamic_pools
        )

        # 緊急換手決策
        emergency_decisions = self.decision_engine.generate_emergency_handover(
            gpp_events, dynamic_pools
        )

        return {
            'event_based': event_based_decisions,
            'predictive': predictive_decisions,
            'emergency': emergency_decisions,
            'decision_latency_ms': self.decision_engine.get_decision_latency(),
            'confidence_scores': self.decision_engine.get_confidence_scores()
        }
```

## 📊 新的標準化輸出格式

```python
stage6_output = {
    'stage': 'stage6_research_optimization',
    'gpp_events': {
        'a4_events': [...],             # 鄰近衛星優於門檻
        'a5_events': [...],             # 雙門檻換手條件
        'd2_events': [...],             # 距離基礎換手
        'event_statistics': {...},
        'detection_performance': {...}
    },
    'dynamic_satellite_pools': {
        'starlink_pools': {
            'active_satellites': [...],  # 10-15顆目標
            'pool_metrics': {...},
            'continuity_analysis': {...}
        },
        'oneweb_pools': {
            'active_satellites': [...],  # 3-6顆目標
            'pool_metrics': {...},
            'continuity_analysis': {...}
        },
        'staggered_strategy': {...},    # 時空錯置策略
        'pool_performance': {...}
    },
    'ml_training_data': {
        'dqn': {
            'state_space': [...],
            'action_space': [...],
            'rewards': [...],
            'training_samples': int
        },
        'a3c': {...},
        'ppo': {...},
        'sac': {...},
        'data_quality_metrics': {...}
    },
    'real_time_decisions': {
        'immediate_actions': [...],     # 毫秒級決策
        'predictive_actions': [...],
        'emergency_procedures': [...],
        'decision_latency_ms': float,
        'confidence_distribution': {...}
    },
    'optimization_results': {
        'multi_objective_solutions': [...],
        'pareto_front': [...],
        'optimization_convergence': {...},
        'constraint_satisfaction': {...}
    },
    'research_analytics': {
        'algorithm_performance': {...},
        'coverage_effectiveness': {...},
        'handover_efficiency': {...},
        'system_reliability': {...}
    },
    'metadata': {
        'processing_timestamp': str,
        'input_source': 'stage5_signal_analysis',
        'research_mode': 'production',
        'academic_standards': ['3GPP_TS_38_331', 'ITU_R_M_1732'],
        'ml_algorithms_supported': ['DQN', 'A3C', 'PPO', 'SAC'],
        'total_training_samples': int,
        'processing_duration_ms': float
    }
}
```

## ✅ 重組驗證標準

### 功能驗證
- [ ] 3GPP A4/A5/D2 事件檢測準確
- [ ] Starlink 10-15顆池規劃達成
- [ ] OneWeb 3-6顆池規劃達成
- [ ] 4種 ML 算法訓練數據生成
- [ ] 毫秒級實時決策響應

### 研究驗證
- [ ] 訓練數據品質符合學術標準
- [ ] 覆蓋連續性滿足 final.md 要求
- [ ] 多目標優化收斂性良好
- [ ] 決策延遲 < 100ms

### 整合驗證
- [ ] Stage 5 信號數據正確接收
- [ ] 研究輸出格式標準化
- [ ] 所有原 Stage 4 功能正常運作

## 🎯 與 final.md 需求的完美對應

| final.md 需求 | Stage 6 實現 |
|---------------|-------------|
| "A4/A5/D2 事件檢測" | `GPPEventDetector` 完整實現 |
| "10-15顆 Starlink 持續可見" | `DynamicPoolPlanner.starlink_pool` |
| "3-6顆 OneWeb 持續可見" | `DynamicPoolPlanner.oneweb_pool` |
| "DQN/A3C/PPO/SAC 支援" | `MLTrainingDataGenerator` 多算法 |
| "毫秒級換手決策" | `RealTimeDecisionEngine` < 100ms |
| "時空錯置池規劃" | `staggered_strategy` 實現 |

## 🚨 注意事項

1. **保持學術標準**: 所有算法實現必須符合國際標準
2. **性能要求**: 實時決策延遲必須 < 100ms
3. **數據品質**: ML 訓練數據必須具備學術發表等級品質
4. **系統整合**: 確保與前面階段的無縫銜接

完成重組後的 Stage 6 將成為整個研究系統的核心，提供完整的 3GPP NTN 事件檢測、動態池規劃和強化學習支援，完全符合 final.md 的研究目標。