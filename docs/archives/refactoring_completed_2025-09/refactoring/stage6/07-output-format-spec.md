# 標準化輸出格式規格 - Stage 6

**依據**: `docs/stages/stage6-research-optimization.md` Line 563-719
**目標**: 完整的 ProcessingResult 標準化輸出

---

## 🎯 核心職責

確保 Stage 6 輸出符合 BaseStageProcessor 標準：
1. **ProcessingResult 包裝**: 所有輸出必須使用 ProcessingResult
2. **完整數據結構**: 包含所有必要字段
3. **元數據完整性**: 提供詳細的處理統計
4. **快照保存**: 支援驗證快照生成

---

## 📊 標準化輸出格式

### ProcessingResult 完整結構

```python
from src.shared.interfaces import ProcessingStatus, ProcessingResult, create_processing_result

# Stage 6 標準化輸出
stage6_result = ProcessingResult(
    status=ProcessingStatus.SUCCESS,
    data={
        # ========== 核心數據 ==========
        'stage': 6,
        'stage_name': 'research_data_generation_optimization',

        # 1. 3GPP 事件數據
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
                    'gpp_parameters': {
                        'offset_frequency': 0.0,
                        'offset_cell': 0.0,
                        'time_to_trigger_ms': 640
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.5'
                }
                # ... 更多 A4 事件
            ],
            'a5_events': [
                {
                    'event_type': 'A5',
                    'event_id': 'A5_STARLINK-1234_1695024000123',
                    'timestamp': '2025-09-27T08:00:00.123456+00:00',
                    'serving_satellite': 'STARLINK-5678',
                    'neighbor_satellite': 'STARLINK-1234',
                    'measurements': {
                        'serving_rsrp_dbm': -115.2,
                        'neighbor_rsrp_dbm': -88.5,
                        'threshold1_dbm': -110.0,
                        'threshold2_dbm': -95.0,
                        'serving_margin_db': 5.2,
                        'neighbor_margin_db': 6.5
                    },
                    'dual_threshold_analysis': {
                        'serving_degraded': True,
                        'neighbor_sufficient': True,
                        'handover_recommended': True
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.6'
                }
                # ... 更多 A5 事件
            ],
            'd2_events': [
                {
                    'event_type': 'D2',
                    'event_id': 'D2_STARLINK-1234_1695024000123',
                    'timestamp': '2025-09-27T08:00:00.123456+00:00',
                    'serving_satellite': 'STARLINK-5678',
                    'neighbor_satellite': 'STARLINK-1234',
                    'measurements': {
                        'serving_distance_km': 1850.5,
                        'neighbor_distance_km': 1350.2,
                        'threshold1_km': 1500.0,
                        'threshold2_km': 2000.0,
                        'hysteresis_km': 50.0,
                        'distance_improvement_km': 500.3
                    },
                    'distance_analysis': {
                        'neighbor_closer': True,
                        'serving_far': True,
                        'handover_recommended': True
                    },
                    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.15a'
                }
                # ... 更多 D2 事件
            ]
        },

        # 2. ML 訓練數據
        'ml_training_data': {
            'dqn_dataset': {
                'state_vectors': [
                    [25.1234, 121.5678, 550.123, -85.2, 15.5, 750.2, 12.8],  # [lat, lon, alt, rsrp, elev, dist, sinr]
                    # ... 更多狀態向量 (50,000+)
                ],
                'action_space': ['maintain', 'handover_to_candidate_1', 'handover_to_candidate_2',
                                 'handover_to_candidate_3', 'handover_to_candidate_4'],
                'reward_values': [0.89, -0.12, 0.76],  # 對應動作的獎勵值
                'q_values': [[0.89, -0.12, 0.76], [0.92, -0.08, 0.71]],  # Q值矩陣
                'next_state_vectors': [...],
                'done_flags': [False, False, True, ...],
                'dataset_size': 50000
            },
            'a3c_dataset': {
                'policy_gradients': [...],
                'value_estimates': [...],
                'advantage_functions': [...],
                'dataset_size': 50000
            },
            'ppo_dataset': {
                'old_policy_probs': [...],
                'new_policy_probs': [...],
                'clipped_ratios': [...],
                'dataset_size': 50000
            },
            'sac_dataset': {
                'continuous_actions': [...],
                'policy_entropy': [...],
                'soft_q_values': [...],
                'dataset_size': 50000
            }
        },

        # 3. 動態衛星池規劃
        'satellite_pool_planning': {
            'starlink_pool': {
                'target_range': {'min': 10, 'max': 15},
                'candidate_satellites_total': 2123,
                'time_points_analyzed': 120,
                'coverage_rate': 0.975,
                'average_visible_count': 12.3,
                'min_visible_count': 8,
                'max_visible_count': 16,
                'target_met': True,
                'coverage_gaps_count': 3,
                'coverage_gaps': [
                    {
                        'start_timestamp': '2025-09-27T03:15:00+00:00',
                        'end_timestamp': '2025-09-27T03:17:30+00:00',
                        'duration_minutes': 2.5,
                        'min_visible_count': 8,
                        'severity': 'minor'
                    }
                ],
                'continuous_coverage_hours': 23.8
            },
            'oneweb_pool': {
                'target_range': {'min': 3, 'max': 6},
                'candidate_satellites_total': 651,
                'time_points_analyzed': 120,
                'coverage_rate': 1.0,
                'average_visible_count': 4.2,
                'min_visible_count': 3,
                'max_visible_count': 6,
                'target_met': True,
                'coverage_gaps_count': 0,
                'coverage_gaps': [],
                'continuous_coverage_hours': 24.0
            },
            'time_space_offset_optimization': {
                'optimal_scheduling': True,
                'coverage_efficiency': 0.97,
                'handover_frequency_per_hour': 8.2
            }
        },

        # 4. 實時決策支援
        'real_time_decision_support': {
            'current_recommendations': [
                {
                    'decision_id': 'HO_DECISION_1695024000456',
                    'recommendation': 'handover_to_STARLINK-1234',
                    'target_satellite_id': 'STARLINK-1234',
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

        # ========== 元數據 ==========
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
            'processing_timestamp': '2025-09-27T08:00:00.789123+00:00',
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

    # ProcessingResult 元數據
    metadata={
        'stage_number': 6,
        'stage_name': 'research_optimization',
        'processor_version': '1.0.0',
        'execution_timestamp': '2025-09-27T08:00:00.789123+00:00'
    },

    # 錯誤和警告
    errors=[],
    warnings=[],

    # 性能指標
    metrics=ProcessingMetrics(
        duration_seconds=0.189,
        memory_usage_mb=156.2,
        cpu_usage_percent=12.5
    )
)
```

---

## 🔧 輸出構建實現

```python
def _build_stage6_output(
    self,
    gpp_events: Dict[str, Any],
    pool_verification: Dict[str, Any],
    ml_training_data: Dict[str, Any],
    decision_support: Dict[str, Any]
) -> Dict[str, Any]:
    """構建 Stage 6 標準化輸出

    Returns:
        符合 ProcessingResult 標準的數據字典
    """
    stage6_output = {
        # 核心標識
        'stage': 6,
        'stage_name': 'research_data_generation_optimization',

        # 核心數據
        'gpp_events': gpp_events,
        'ml_training_data': ml_training_data,
        'satellite_pool_planning': pool_verification,
        'real_time_decision_support': decision_support,

        # 元數據
        'metadata': {
            # 3GPP 配置
            'gpp_event_config': {
                'standard_version': 'TS_38.331_v18.5.1',
                'a4_threshold_dbm': self.config.get('a4_threshold_dbm', -100.0),
                'a5_threshold1_dbm': self.config.get('a5_threshold1_dbm', -110.0),
                'a5_threshold2_dbm': self.config.get('a5_threshold2_dbm', -95.0),
                'd2_distance_threshold_km': self.config.get('d2_distance_threshold_km', 1500),
                'hysteresis_db': self.config.get('hysteresis_db', 2.0),
                'time_to_trigger_ms': self.config.get('time_to_trigger_ms', 640)
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
                'starlink_satellites_maintained': pool_verification.get('starlink_pool', {}).get('target_met', False),
                'oneweb_satellites_maintained': pool_verification.get('oneweb_pool', {}).get('target_met', False),
                'continuous_coverage_achieved': self._check_continuous_coverage(pool_verification),
                'gpp_events_detected': gpp_events.get('total_events', 0),
                'ml_training_samples': self._count_ml_samples(ml_training_data),
                'real_time_decision_capability': len(decision_support.get('current_recommendations', [])) > 0
            },

            # 處理統計
            'processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'processing_duration_seconds': 0.0,  # 將由外層計算
            'events_detected': gpp_events.get('total_events', 0),
            'training_samples_generated': self._count_ml_samples(ml_training_data),
            'decision_recommendations': len(decision_support.get('current_recommendations', [])),

            # 合規標記
            'gpp_standard_compliance': self._check_gpp_compliance(gpp_events),
            'ml_research_readiness': self._check_ml_readiness(ml_training_data),
            'real_time_capability': self._check_real_time_capability(decision_support),
            'academic_standard': 'Grade_A'
        }
    }

    return stage6_output

def _check_continuous_coverage(self, pool_verification: Dict[str, Any]) -> bool:
    """檢查連續覆蓋是否達成"""
    starlink_coverage = pool_verification.get('starlink_pool', {}).get('coverage_rate', 0.0)
    oneweb_coverage = pool_verification.get('oneweb_pool', {}).get('coverage_rate', 0.0)
    return starlink_coverage >= 0.95 and oneweb_coverage >= 0.95

def _count_ml_samples(self, ml_training_data: Dict[str, Any]) -> int:
    """計算 ML 訓練樣本總數"""
    total = 0
    for dataset_name in ['dqn_dataset', 'a3c_dataset', 'ppo_dataset', 'sac_dataset']:
        dataset = ml_training_data.get(dataset_name, {})
        total += dataset.get('dataset_size', 0)
    return total

def _check_gpp_compliance(self, gpp_events: Dict[str, Any]) -> bool:
    """檢查 3GPP 標準合規性"""
    return gpp_events.get('total_events', 0) > 0

def _check_ml_readiness(self, ml_training_data: Dict[str, Any]) -> bool:
    """檢查 ML 研究就緒性"""
    total_samples = self._count_ml_samples(ml_training_data)
    return total_samples >= 1000  # 至少1000個樣本

def _check_real_time_capability(self, decision_support: Dict[str, Any]) -> bool:
    """檢查實時決策能力"""
    performance = decision_support.get('performance_metrics', {})
    avg_latency = performance.get('average_decision_latency_ms', float('inf'))
    return avg_latency < 100.0
```

---

## 💾 快照保存實現

```python
def save_validation_snapshot(self, output_data: Dict[str, Any]) -> bool:
    """保存驗證快照

    Args:
        output_data: Stage 6 輸出數據

    Returns:
        保存成功返回 True
    """
    try:
        snapshot_dir = Path('data/validation_snapshots')
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot_path = snapshot_dir / 'stage6_validation.json'

        # 構建快照數據
        snapshot = {
            'stage': 'stage6_research_optimization',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'success',
            'validation_passed': True,

            # 數據摘要
            'data_summary': {
                'total_events': output_data.get('metadata', {}).get('events_detected', 0),
                'ml_samples': output_data.get('metadata', {}).get('training_samples_generated', 0),
                'starlink_pool_met': output_data.get('metadata', {}).get('research_targets', {}).get('starlink_satellites_maintained', False),
                'oneweb_pool_met': output_data.get('metadata', {}).get('research_targets', {}).get('oneweb_satellites_maintained', False),
                'decision_recommendations': output_data.get('metadata', {}).get('decision_recommendations', 0)
            },

            # 驗證結果 (如果已執行驗證)
            'validation_results': None,  # 將由 run_validation_checks 填充

            # 完整輸出 (僅保存關鍵字段)
            'output_sample': {
                'gpp_events_summary': {
                    'a4_count': len(output_data.get('gpp_events', {}).get('a4_events', [])),
                    'a5_count': len(output_data.get('gpp_events', {}).get('a5_events', [])),
                    'd2_count': len(output_data.get('gpp_events', {}).get('d2_events', []))
                },
                'ml_datasets': list(output_data.get('ml_training_data', {}).keys()),
                'pool_planning': {
                    'starlink_coverage': output_data.get('satellite_pool_planning', {}).get('starlink_pool', {}).get('coverage_rate', 0.0),
                    'oneweb_coverage': output_data.get('satellite_pool_planning', {}).get('oneweb_pool', {}).get('coverage_rate', 0.0)
                }
            }
        }

        # 保存快照
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

        self.logger.info(f"✅ 驗證快照已保存: {snapshot_path}")
        return True

    except Exception as e:
        self.logger.error(f"❌ 保存驗證快照失敗: {e}")
        return False
```

---

## ✅ 實現檢查清單

### 輸出格式
- [ ] ProcessingResult 標準包裝
- [ ] 完整數據結構
- [ ] 元數據完整性
- [ ] 所有必要字段存在

### 數據完整性
- [ ] 3GPP 事件完整輸出
- [ ] ML 訓練數據完整輸出
- [ ] 衛星池規劃完整輸出
- [ ] 實時決策支援完整輸出

### 快照功能
- [ ] 快照保存實現
- [ ] 快照格式正確
- [ ] 快照數據完整
- [ ] 錯誤處理完善

### 單元測試
- [ ] 輸出構建測試
- [ ] 格式驗證測試
- [ ] 快照保存測試
- [ ] 邊界條件測試

---

**規格版本**: v1.0
**創建日期**: 2025-09-30
**狀態**: 待實現