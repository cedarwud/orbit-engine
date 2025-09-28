# 🤖 Stage 6: 研究數據生成與優化層 - 完整規格文檔

**最後更新**: 2025-09-28
**核心職責**: 3GPP NTN 事件檢測與強化學習訓練數據生成
**學術合規**: Grade A 標準，符合 3GPP TS 38.331 和 ML 研究需求
**接口標準**: 100% BaseStageProcessor 合規

## 📖 概述與目標

**核心職責**: 基於信號品質數據生成研究級 3GPP 事件和 ML 訓練數據
**輸入**: Stage 5 的信號品質分析結果
**輸出**: 3GPP NTN 事件數據 + 強化學習訓練集
**處理時間**: ~0.2秒 (事件檢測和數據生成)
**學術標準**: 3GPP TS 38.331 標準事件檢測，支援多種 ML 算法

### 🎯 Stage 6 核心價值
- **3GPP NTN 事件**: 完整的 A4/A5/D2 事件檢測和報告
- **ML 訓練數據**: 為 DQN/A3C/PPO/SAC 算法準備訓練集
- **實時決策支援**: 毫秒級換手決策推理支援
- **研究數據完整性**: 連續不間斷的衛星覆蓋環境數據

## 🚨 研究目標對齊

### ✅ **基於 final.md 的核心需求**
```
核心研究目標:
1. 衛星池規劃: Starlink 10-15顆, OneWeb 3-6顆
2. 3GPP NTN 支援: A4/A5/D2 事件完整實現
3. 強化學習優化: DQN/A3C/PPO/SAC 算法支援
4. 實時決策: < 100ms 換手決策響應
```

### ✅ **Stage 6 實現對應**
```
Stage 6 實現:
1. 動態衛星池規劃和維護
2. 標準 3GPP TS 38.331 事件檢測
3. 多算法 ML 訓練數據生成
4. 毫秒級推理決策支援
```

**學術依據**:
> *"LEO satellite handover optimization requires both standardized 3GPP event detection and machine learning-based decision algorithms. The integration of these approaches enables real-time handover decisions in highly dynamic satellite environments."*
> — 3GPP TR 38.821 V16.1.0 (2019-12) Solutions for NR to support non-terrestrial networks

## 🏗️ 架構設計

### 重構後組件架構
```
┌─────────────────────────────────────────────────────────┐
│       Stage 6: 研究數據生成與優化層 (重構版)             │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │3GPP Event   │  │ML Training  │  │Pool         │    │
│  │Detector     │  │Data Gen     │  │Optimizer    │    │
│  │             │  │             │  │             │    │
│  │• A4 事件     │  │• 狀態空間    │  │• 時空錯置    │    │
│  │• A5 事件     │  │• 動作空間    │  │• 動態覆蓋    │    │
│  │• D2 事件     │  │• 獎勵函數    │  │• 連續服務    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│           │              │              │             │
│           └──────────────┼──────────────┘             │
│                          ▼                            │
│  ┌──────────────────────────────────────────────┐    │
│  │      Stage6ResearchOptimizationProcessor     │    │
│  │      (BaseStageProcessor 合規)               │    │
│  │                                              │    │
│  │ • 3GPP TS 38.331 標準事件檢測                │    │
│  │ • DQN/A3C/PPO/SAC 訓練數據                   │    │
│  │ • 實時決策推理支援                           │    │
│  │ • ProcessingResult 標準輸出                  │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 🎯 核心功能與職責

### ✅ **Stage 6 專屬職責**

#### 1. **3GPP NTN 事件檢測**
- **A4 事件**: 鄰近衛星變得優於門檻值
  - 觸發條件: Mn + Ofn + Ocn – Hys > Thresh
  - 標準依據: 3GPP TS 38.331 v18.5.1 Section 5.5.4.5
- **A5 事件**: 服務衛星劣於門檻1且鄰近衛星優於門檻2
  - 觸發條件: (Mp + Hys < Thresh1) AND (Mn + Ofn + Ocn – Hys > Thresh2)
  - 標準依據: 3GPP TS 38.331 v18.5.1 Section 5.5.4.6
- **D2 事件**: 基於距離的換手觸發
  - 觸發條件: (Ml1 – Hys > Thresh1) AND (Ml2 + Hys < Thresh2)
  - 標準依據: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a

#### 2. **強化學習訓練數據生成**
- **狀態空間**: 衛星位置、信號強度、仰角、距離等多維狀態
- **動作空間**: 換手決策(保持/切換至候選衛星1/2/3...)
- **獎勵函數**: 基於QoS、中斷時間、信號品質的複合獎勵
- **經驗回放**: 大量真實換手場景存儲供算法學習

#### 3. **動態衛星池規劃**
- **Starlink 池**: 維持 10-15顆衛星連續可見
- **OneWeb 池**: 維持 3-6顆衛星連續可見
- **時空錯置**: 錯開時間和位置的衛星選擇
- **動態覆蓋**: 整個軌道週期中持續保持目標數量

#### 4. **實時決策支援**
- **毫秒級響應**: 支援真實時間的換手決策推理 (< 100ms)
- **多候選評估**: 同時評估3-5個換手候選的優劣
- **自適應門檻**: 根據環境動態調整RSRP/距離門檻
- **決策可追溯**: 完整的決策過程記錄和分析

### ❌ **明確排除職責** (留給後續研究)
- ❌ **實際換手執行**: 僅生成決策建議，不執行實際換手
- ❌ **硬體控制**: 不涉及實際射頻設備控制
- ❌ **網路協議**: 不處理實際的 NTN 協議棧
- ❌ **用戶數據**: 不處理實際用戶業務數據

## 🔬 3GPP 標準事件實現

### 🚨 **CRITICAL: 3GPP TS 38.331 標準合規**

**✅ 正確的 3GPP 事件檢測實現**:
```python
def detect_a4_event_3gpp_standard(self, serving_satellite, neighbor_satellites):
    """3GPP TS 38.331 A4 事件檢測: 鄰近衛星變得優於門檻值"""

    # 3GPP 標準參數
    threshold_a4 = self.config['a4_threshold_dbm']  # -100 dBm
    hysteresis = self.config['hysteresis_db']       # 2 dB
    offset_freq = self.config['offset_frequency']   # 0 dB (同頻)
    offset_cell = self.config['offset_cell']        # 0 dB

    a4_events = []

    for neighbor in neighbor_satellites:
        neighbor_rsrp = neighbor['signal_quality']['rsrp_dbm']

        # 3GPP 標準 A4 觸發條件
        # Mn + Ofn + Ocn – Hys > Thresh
        trigger_condition = (
            neighbor_rsrp + offset_freq + offset_cell - hysteresis > threshold_a4
        )

        if trigger_condition:
            a4_event = {
                'event_type': 'A4',
                'event_id': f"A4_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                'timestamp': datetime.utcnow().isoformat(),
                'serving_satellite': serving_satellite['satellite_id'],
                'neighbor_satellite': neighbor['satellite_id'],
                'measurements': {
                    'neighbor_rsrp_dbm': neighbor_rsrp,
                    'threshold_dbm': threshold_a4,
                    'hysteresis_db': hysteresis,
                    'trigger_margin_db': neighbor_rsrp - threshold_a4
                },
                'gpp_parameters': {
                    'offset_frequency': offset_freq,
                    'offset_cell': offset_cell,
                    'time_to_trigger_ms': self.config['time_to_trigger_ms']
                },
                'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.5'
            }
            a4_events.append(a4_event)

    return a4_events

def detect_a5_event_3gpp_standard(self, serving_satellite, neighbor_satellites):
    """3GPP TS 38.331 A5 事件檢測: 服務衛星劣化且鄰近衛星良好"""

    # 3GPP 標準 A5 參數
    threshold1_a5 = self.config['a5_threshold1_dbm']  # -110 dBm (服務門檻)
    threshold2_a5 = self.config['a5_threshold2_dbm']  # -95 dBm (鄰近門檻)
    hysteresis = self.config['hysteresis_db']

    serving_rsrp = serving_satellite['signal_quality']['rsrp_dbm']

    # 條件1: 服務衛星劣於門檻1
    serving_condition = (serving_rsrp + hysteresis < threshold1_a5)

    if not serving_condition:
        return []

    a5_events = []

    for neighbor in neighbor_satellites:
        neighbor_rsrp = neighbor['signal_quality']['rsrp_dbm']

        # 條件2: 鄰近衛星優於門檻2
        neighbor_condition = (neighbor_rsrp - hysteresis > threshold2_a5)

        if neighbor_condition:
            a5_event = {
                'event_type': 'A5',
                'event_id': f"A5_{neighbor['satellite_id']}_{int(time.time() * 1000)}",
                'timestamp': datetime.utcnow().isoformat(),
                'serving_satellite': serving_satellite['satellite_id'],
                'neighbor_satellite': neighbor['satellite_id'],
                'measurements': {
                    'serving_rsrp_dbm': serving_rsrp,
                    'neighbor_rsrp_dbm': neighbor_rsrp,
                    'threshold1_dbm': threshold1_a5,
                    'threshold2_dbm': threshold2_a5,
                    'serving_margin_db': threshold1_a5 - serving_rsrp,
                    'neighbor_margin_db': neighbor_rsrp - threshold2_a5
                },
                'dual_threshold_analysis': {
                    'serving_degraded': serving_condition,
                    'neighbor_sufficient': neighbor_condition,
                    'handover_recommended': True
                },
                'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.6'
            }
            a5_events.append(a5_event)

    return a5_events
```

## 📊 標準化輸出格式

### ProcessingResult 結構
```python
ProcessingResult(
    status=ProcessingStatus.SUCCESS,
    data={
        'stage': 6,
        'stage_name': 'research_data_generation_optimization',
        'gpp_events': {
            'a4_events': [
                {
                    'event_type': 'A4',
                    'event_id': 'A4_STARLINK-1234_1695024000123',
                    'timestamp': '2025-09-27T08:00:00.123456+00:00',
                    'serving_satellite': 'STARLINK-5678',
                    'neighbor_satellite': 'STARLINK-1234',
                    'measurements': {
                        'neighbor_rsrp_dbm': -88.5,
                        'threshold_dbm': -100.0,
                        'hysteresis_db': 2.0,
                        'trigger_margin_db': 11.5
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.5'
                }
                # ... 更多 A4 事件
            ],
            'a5_events': [
                # A5 事件列表，格式相同
            ],
            'd2_events': [
                # D2 事件列表，格式相同
            ]
        },
        'ml_training_data': {
            'dqn_dataset': {
                'state_vectors': [
                    [25.1234, 121.5678, 550.123, -85.2, 15.5, 750.2, 12.8],  # [lat, lon, alt, rsrp, elev, dist, sinr]
                    # ... 更多狀態向量
                ],
                'action_space': ['maintain', 'handover_to_candidate_1', 'handover_to_candidate_2'],
                'reward_values': [0.89, -0.12, 0.76],  # 對應動作的獎勵值
                'q_values': [[0.89, -0.12, 0.76], [0.92, -0.08, 0.71]],  # Q值矩陣
                'dataset_size': 50000
            },
            'a3c_dataset': {
                'policy_gradients': [...],
                'value_estimates': [...],
                'advantage_functions': [...]
            },
            'ppo_dataset': {
                'old_policy_probs': [...],
                'new_policy_probs': [...],
                'clipped_ratios': [...]
            },
            'sac_dataset': {
                'continuous_actions': [...],
                'policy_entropy': [...],
                'soft_q_values': [...]
            }
        },
        'satellite_pool_planning': {
            'starlink_pool': {
                'target_range': {'min': 10, 'max': 15},
                'current_count': 12,
                'active_satellites': ['STARLINK-1234', 'STARLINK-5678', ...],
                'coverage_continuity': {
                    'continuous_hours': 23.8,
                    'gap_periods': [{'start': '2025-09-27T03:15:00+00:00', 'duration_minutes': 2.5}]
                }
            },
            'oneweb_pool': {
                'target_range': {'min': 3, 'max': 6},
                'current_count': 4,
                'active_satellites': ['ONEWEB-0123', 'ONEWEB-0456', ...],
                'coverage_continuity': {
                    'continuous_hours': 24.0,
                    'gap_periods': []
                }
            },
            'time_space_offset_optimization': {
                'optimal_scheduling': True,
                'coverage_efficiency': 0.97,
                'handover_frequency_per_hour': 8.2
            }
        },
        'real_time_decision_support': {
            'current_recommendations': [
                {
                    'decision_id': 'HO_DECISION_1695024000456',
                    'recommendation': 'handover_to_starlink_1234',
                    'confidence_score': 0.92,
                    'decision_latency_ms': 45,
                    'reasoning': {
                        'current_rsrp_degraded': True,
                        'candidate_rsrp_superior': True,
                        'distance_acceptable': True,
                        'qos_improvement_expected': 0.15
                    }
                }
            ],
            'performance_metrics': {
                'average_decision_latency_ms': 47.3,
                'decision_accuracy': 0.94,
                'handover_success_rate': 0.96
            }
        },
        'metadata': {
            # 3GPP 配置
            'gpp_event_config': {
                'standard_version': 'TS_38.331_v18.5.1',
                'a4_threshold_dbm': -100.0,
                'a5_threshold1_dbm': -110.0,
                'a5_threshold2_dbm': -95.0,
                'd2_distance_threshold_km': 1500,
                'hysteresis_db': 2.0,
                'time_to_trigger_ms': 640
            },

            # ML 算法配置
            'ml_config': {
                'algorithms_supported': ['DQN', 'A3C', 'PPO', 'SAC'],
                'state_space_dimensions': 7,
                'action_space_size': 5,
                'reward_function': 'composite_qos_interruption_quality',
                'experience_replay_size': 100000
            },

            # 研究目標達成
            'research_targets': {
                'starlink_satellites_maintained': True,
                'oneweb_satellites_maintained': True,
                'continuous_coverage_achieved': True,
                'gpp_events_detected': 1250,
                'ml_training_samples': 50000,
                'real_time_decision_capability': True
            },

            # 處理統計
            'processing_duration_seconds': 0.189,
            'events_detected': 1250,
            'training_samples_generated': 50000,
            'decision_recommendations': 24,

            # 合規標記
            'gpp_standard_compliance': True,
            'ml_research_readiness': True,
            'real_time_capability': True,
            'academic_standard': 'Grade_A'
        }
    },
    metadata={...},
    errors=[],
    warnings=[],
    metrics=ProcessingMetrics(...)
)
```

### ML 訓練數據格式
```python
ml_training_sample = {
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
        'signal_quality_gain': 0.63
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

## ⚡ 性能指標

### 目標性能指標
- **處理時間**: < 0.2秒 (事件檢測和數據生成)
- **事件檢測**: 1000+ 3GPP 事件/小時
- **ML 訓練樣本**: 50,000+ 樣本/天
- **決策延遲**: < 100ms 實時響應
- **覆蓋達成**: Starlink 10-15顆, OneWeb 3-6顆

### 研究數據完整性
- **連續覆蓋**: > 95% 時間連續服務
- **事件多樣性**: 50+ 不同換手場景
- **訓練數據品質**: 高品質標註數據
- **算法支援**: 4種主流 RL 算法完整支援

## 🔬 驗證框架

### 5項專用驗證檢查
1. **gpp_event_standard_compliance** - 3GPP 事件標準合規
   - A4/A5/D2 事件檢測邏輯驗證
   - 3GPP TS 38.331 參數正確性
   - 事件觸發條件準確性

2. **ml_training_data_quality** - ML 訓練數據品質
   - 狀態空間完整性檢查
   - 動作空間合理性驗證
   - 獎勵函數設計正確性

3. **satellite_pool_optimization** - 衛星池優化驗證
   - 目標衛星數量達成檢查
   - 連續覆蓋時間驗證
   - 時空錯置效果評估

4. **real_time_decision_performance** - 實時決策性能
   - 決策延遲基準檢查
   - 決策準確性驗證
   - 系統響應時間監控

5. **research_goal_achievement** - 研究目標達成
   - final.md 需求對應檢查
   - 學術研究數據完整性
   - 實驗可重現性驗證

## 🚀 使用方式與配置

### 標準調用方式
```python
from stages.stage6_research_optimization.stage6_research_optimization_processor import Stage6ResearchOptimizationProcessor

# 接收 Stage 5 結果
stage5_result = stage5_processor.execute()

# 創建 Stage 6 處理器
processor = Stage6ResearchOptimizationProcessor(config)

# 執行研究數據生成和優化
result = processor.execute(stage5_result.data)

# 驗證檢查
validation = processor.run_validation_checks(result.data)

# 研究數據輸出
gpp_events = result.data['gpp_events']
ml_training_data = result.data['ml_training_data']
real_time_decisions = result.data['real_time_decision_support']
```

### 配置選項
```python
config = {
    'gpp_event_config': {
        'standard_version': 'TS_38.331_v18.5.1',
        'a4_threshold_dbm': -100.0,
        'a5_threshold1_dbm': -110.0,
        'a5_threshold2_dbm': -95.0,
        'd2_distance_threshold_km': 1500,
        'hysteresis_db': 2.0,
        'time_to_trigger_ms': 640
    },
    'ml_algorithm_config': {
        'algorithms': ['DQN', 'A3C', 'PPO', 'SAC'],
        'state_space_size': 7,
        'action_space_size': 5,
        'experience_replay_size': 100000,
        'batch_size': 256,
        'learning_rate': 0.001
    },
    'satellite_pool_targets': {
        'starlink': {'min': 10, 'max': 15},
        'oneweb': {'min': 3, 'max': 6},
        'continuous_coverage_threshold': 0.95,
        'time_space_offset_optimization': True
    },
    'real_time_config': {
        'decision_latency_target_ms': 100,
        'confidence_threshold': 0.8,
        'candidate_evaluation_count': 5,
        'adaptive_thresholds': True
    }
}
```

## 📋 部署與驗證

### 部署檢驗標準
**成功指標**:
- [ ] 3GPP TS 38.331 事件檢測正確實現
- [ ] 1000+ 3GPP 事件檢測/小時
- [ ] 50,000+ ML 訓練樣本生成
- [ ] < 100ms 實時決策響應
- [ ] Starlink: 10-15顆池維護
- [ ] OneWeb: 3-6顆池維護

### 測試命令
```bash
# 完整 Stage 6 測試
python scripts/run_six_stages_with_validation.py --stage 6

# 檢查 3GPP 事件檢測
cat data/validation_snapshots/stage6_validation.json | jq '.metadata.events_detected'

# 驗證 ML 訓練數據
cat data/validation_snapshots/stage6_validation.json | jq '.metadata.training_samples_generated'

# 檢查實時決策性能
cat data/validation_snapshots/stage6_validation.json | jq '.real_time_decision_support.performance_metrics'
```

## 🎯 學術標準合規

### Grade A 強制要求
- **✅ 3GPP 標準**: 完全符合 3GPP TS 38.331 事件檢測標準
- **✅ ML 研究**: 支援主流強化學習算法的完整訓練數據
- **✅ 實時性能**: 毫秒級決策響應，符合實際系統需求
- **✅ 研究完整性**: 對應 final.md 所有核心研究目標
- **✅ 數據品質**: 高品質、可重現的學術研究數據

### 零容忍項目
- **❌ 非標準事件**: 禁止使用非 3GPP 標準的事件檢測
- **❌ 簡化 ML**: 禁止簡化 ML 訓練數據格式
- **❌ 延遲超標**: 禁止超過 100ms 決策延遲
- **❌ 池維護失敗**: 禁止無法維持目標衛星池數量
- **❌ 研究偏離**: 禁止偏離 final.md 核心研究目標

---

**文檔版本**: v6.0 (重構版)
**概念狀態**: ✅ 研究數據生成與優化 (全新設計)
**學術合規**: ✅ Grade A 標準
**維護負責**: Orbit Engine Team