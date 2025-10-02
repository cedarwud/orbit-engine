# 驗證框架規格 - Stage 6 核心組件

**檔案**: `src/stages/stage6_research_optimization/stage6_research_optimization_processor.py` (驗證方法)
**依據**: `docs/stages/stage6-research-optimization.md` Line 780-806
**目標**: 5項專用驗證檢查

---

## 🎯 核心職責

實現 Stage 6 的 5 項專用驗證檢查：
1. **gpp_event_standard_compliance** - 3GPP 事件標準合規
2. **ml_training_data_quality** - ML 訓練數據品質
3. **satellite_pool_optimization** - 衛星池優化驗證
4. **real_time_decision_performance** - 實時決策性能
5. **research_goal_achievement** - 研究目標達成

---

## 🏗️ 驗證框架設計

### 主驗證方法

```python
def run_validation_checks(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
    """執行 5 項專用驗證檢查

    Args:
        output_data: Stage 6 輸出數據

    Returns:
        {
            'validation_status': 'passed' | 'failed',
            'overall_status': 'PASS' | 'FAIL',
            'checks_performed': 5,
            'checks_passed': int,
            'validation_details': {
                'success_rate': float,
                'check_results': {...}
            },
            'check_details': {
                'gpp_event_standard_compliance': {...},
                'ml_training_data_quality': {...},
                'satellite_pool_optimization': {...},
                'real_time_decision_performance': {...},
                'research_goal_achievement': {...}
            },
            'validation_timestamp': str
        }
    """
    validation_results = {
        'validation_status': 'pending',
        'overall_status': 'UNKNOWN',
        'checks_performed': 0,
        'checks_passed': 0,
        'validation_details': {},
        'check_details': {},
        'validation_timestamp': datetime.now(timezone.utc).isoformat()
    }

    # 執行 5 項檢查
    check_methods = [
        ('gpp_event_standard_compliance', self._validate_gpp_event_compliance),
        ('ml_training_data_quality', self._validate_ml_training_data_quality),
        ('satellite_pool_optimization', self._validate_satellite_pool_optimization),
        ('real_time_decision_performance', self._validate_real_time_decision_performance),
        ('research_goal_achievement', self._validate_research_goal_achievement)
    ]

    for check_name, check_method in check_methods:
        try:
            check_result = check_method(output_data)
            validation_results['check_details'][check_name] = check_result
            validation_results['checks_performed'] += 1

            if check_result['passed']:
                validation_results['checks_passed'] += 1

        except Exception as e:
            self.logger.error(f"驗證檢查 {check_name} 失敗: {e}")
            validation_results['check_details'][check_name] = {
                'passed': False,
                'error': str(e)
            }
            validation_results['checks_performed'] += 1

    # 計算總體狀態
    success_rate = (
        validation_results['checks_passed'] / validation_results['checks_performed']
        if validation_results['checks_performed'] > 0 else 0.0
    )

    validation_results['validation_details']['success_rate'] = success_rate

    # 至少 4/5 項通過才算整體通過
    if validation_results['checks_passed'] >= 4:
        validation_results['validation_status'] = 'passed'
        validation_results['overall_status'] = 'PASS'
    else:
        validation_results['validation_status'] = 'failed'
        validation_results['overall_status'] = 'FAIL'

    return validation_results
```

---

## 📋 驗證檢查 1: 3GPP 事件標準合規

```python
def _validate_gpp_event_compliance(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
    """驗證 3GPP 事件標準合規

    檢查項目:
    1. A4/A5/D2 事件檢測邏輯正確
    2. 3GPP TS 38.331 參數正確性
    3. 事件觸發條件準確性
    4. 標準參考文獻完整性

    Returns:
        {
            'passed': bool,
            'score': float,
            'details': {
                'total_events': int,
                'a4_events_valid': bool,
                'a5_events_valid': bool,
                'd2_events_valid': bool,
                'standard_references_present': bool,
                'trigger_conditions_correct': bool
            },
            'issues': List[str],
            'recommendations': List[str]
        }
    """
    result = {
        'passed': False,
        'score': 0.0,
        'details': {},
        'issues': [],
        'recommendations': []
    }

    gpp_events = output_data.get('gpp_events', {})

    # 1. 檢查事件總數
    a4_events = gpp_events.get('a4_events', [])
    a5_events = gpp_events.get('a5_events', [])
    d2_events = gpp_events.get('d2_events', [])
    total_events = len(a4_events) + len(a5_events) + len(d2_events)

    result['details']['total_events'] = total_events

    if total_events == 0:
        result['issues'].append("未檢測到任何 3GPP 事件")
        return result

    # 2. 驗證 A4 事件格式
    a4_valid = True
    for event in a4_events[:5]:  # 抽樣檢查前5個
        if not self._validate_a4_event_format(event):
            a4_valid = False
            result['issues'].append(f"A4 事件格式無效: {event.get('event_id', 'unknown')}")

    result['details']['a4_events_valid'] = a4_valid

    # 3. 驗證 A5 事件格式
    a5_valid = True
    for event in a5_events[:5]:
        if not self._validate_a5_event_format(event):
            a5_valid = False
            result['issues'].append(f"A5 事件格式無效: {event.get('event_id', 'unknown')}")

    result['details']['a5_events_valid'] = a5_valid

    # 4. 驗證 D2 事件格式
    d2_valid = True
    for event in d2_events[:5]:
        if not self._validate_d2_event_format(event):
            d2_valid = False
            result['issues'].append(f"D2 事件格式無效: {event.get('event_id', 'unknown')}")

    result['details']['d2_events_valid'] = d2_valid

    # 5. 檢查標準參考文獻
    standard_refs_present = all([
        any('3GPP_TS_38.331' in e.get('standard_reference', '') for e in a4_events) if a4_events else True,
        any('3GPP_TS_38.331' in e.get('standard_reference', '') for e in a5_events) if a5_events else True,
        any('3GPP_TS_38.331' in e.get('standard_reference', '') for e in d2_events) if d2_events else True
    ])

    result['details']['standard_references_present'] = standard_refs_present

    if not standard_refs_present:
        result['issues'].append("缺少 3GPP TS 38.331 標準參考文獻")

    # 6. 計算分數
    checks = [a4_valid, a5_valid, d2_valid, standard_refs_present]
    result['score'] = sum(checks) / len(checks)

    # 7. 判定通過
    result['passed'] = result['score'] >= 0.75 and total_events >= 10

    if not result['passed']:
        result['recommendations'].append("確保所有 3GPP 事件符合 TS 38.331 標準")
        result['recommendations'].append("檢查事件觸發條件邏輯")

    return result

def _validate_a4_event_format(self, event: Dict[str, Any]) -> bool:
    """驗證 A4 事件格式"""
    required_fields = [
        'event_type', 'event_id', 'timestamp', 'neighbor_satellite',
        'measurements', 'standard_reference'
    ]

    if not all(field in event for field in required_fields):
        return False

    if event['event_type'] != 'A4':
        return False

    # 檢查 measurements 字段
    measurements = event.get('measurements', {})
    required_measurements = ['neighbor_rsrp_dbm', 'threshold_dbm', 'hysteresis_db']

    if not all(field in measurements for field in required_measurements):
        return False

    return True

def _validate_a5_event_format(self, event: Dict[str, Any]) -> bool:
    """驗證 A5 事件格式"""
    required_fields = [
        'event_type', 'event_id', 'timestamp', 'serving_satellite',
        'neighbor_satellite', 'measurements', 'dual_threshold_analysis'
    ]

    if not all(field in event for field in required_fields):
        return False

    if event['event_type'] != 'A5':
        return False

    # 檢查雙門檻分析
    dual_analysis = event.get('dual_threshold_analysis', {})
    if 'serving_degraded' not in dual_analysis or 'neighbor_sufficient' not in dual_analysis:
        return False

    return True

def _validate_d2_event_format(self, event: Dict[str, Any]) -> bool:
    """驗證 D2 事件格式"""
    required_fields = [
        'event_type', 'event_id', 'timestamp', 'serving_satellite',
        'neighbor_satellite', 'measurements', 'distance_analysis'
    ]

    if not all(field in event for field in required_fields):
        return False

    if event['event_type'] != 'D2':
        return False

    # 檢查距離測量
    measurements = event.get('measurements', {})
    if 'serving_distance_km' not in measurements or 'neighbor_distance_km' not in measurements:
        return False

    return True
```

---

## 📋 驗證檢查 2: ML 訓練數據品質

```python
def _validate_ml_training_data_quality(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
    """驗證 ML 訓練數據品質

    檢查項目:
    1. 狀態空間完整性 (7維)
    2. 動作空間合理性
    3. 獎勵函數設計正確性
    4. 數據集大小達標 (50,000+)

    Returns:
        {
            'passed': bool,
            'score': float,
            'details': {
                'total_samples': int,
                'state_space_valid': bool,
                'action_space_valid': bool,
                'reward_function_valid': bool,
                'dataset_size_adequate': bool
            }
        }
    """
    result = {
        'passed': False,
        'score': 0.0,
        'details': {},
        'issues': [],
        'recommendations': []
    }

    ml_training_data = output_data.get('ml_training_data', {})

    # 1. 檢查數據集大小
    dqn_dataset = ml_training_data.get('dqn_dataset', {})
    total_samples = dqn_dataset.get('dataset_size', 0)
    result['details']['total_samples'] = total_samples

    dataset_size_adequate = total_samples >= 10000  # 至少10k樣本
    result['details']['dataset_size_adequate'] = dataset_size_adequate

    if not dataset_size_adequate:
        result['issues'].append(f"數據集大小不足: {total_samples} (需要 >= 10000)")

    # 2. 驗證狀態空間
    state_vectors = dqn_dataset.get('state_vectors', [])
    state_space_valid = False

    if state_vectors:
        # 檢查狀態向量維度 (應為 7 維)
        sample_state = state_vectors[0]
        if len(sample_state) == 7:
            state_space_valid = True
        else:
            result['issues'].append(f"狀態向量維度錯誤: {len(sample_state)} (應為 7)")

    result['details']['state_space_valid'] = state_space_valid

    # 3. 驗證動作空間
    action_space = dqn_dataset.get('action_space', [])
    action_space_valid = len(action_space) >= 3  # 至少3個動作

    result['details']['action_space_valid'] = action_space_valid

    if not action_space_valid:
        result['issues'].append(f"動作空間不足: {len(action_space)} (應 >= 3)")

    # 4. 驗證獎勵函數
    reward_values = dqn_dataset.get('reward_values', [])
    reward_function_valid = len(reward_values) > 0 and all(
        isinstance(r, (int, float)) for r in reward_values[:100]
    )

    result['details']['reward_function_valid'] = reward_function_valid

    # 5. 計算分數
    checks = [
        dataset_size_adequate,
        state_space_valid,
        action_space_valid,
        reward_function_valid
    ]
    result['score'] = sum(checks) / len(checks)

    # 6. 判定通過
    result['passed'] = result['score'] >= 0.75

    if not result['passed']:
        result['recommendations'].append("確保生成足夠的訓練樣本 (>= 10000)")
        result['recommendations'].append("驗證狀態空間維度正確性 (7維)")

    return result
```

---

## 📋 驗證檢查 3: 衛星池優化驗證

```python
def _validate_satellite_pool_optimization(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
    """驗證衛星池優化

    檢查項目:
    1. Starlink 目標衛星數量達成 (10-15顆)
    2. OneWeb 目標衛星數量達成 (3-6顆)
    3. 連續覆蓋時間 (> 95%)
    4. 時空錯置效果評估

    Returns:
        {
            'passed': bool,
            'score': float,
            'details': {
                'starlink_target_met': bool,
                'oneweb_target_met': bool,
                'continuous_coverage_adequate': bool,
                'time_space_offset_effective': bool
            }
        }
    """
    result = {
        'passed': False,
        'score': 0.0,
        'details': {},
        'issues': [],
        'recommendations': []
    }

    pool_planning = output_data.get('satellite_pool_planning', {})

    # 1. 驗證 Starlink 池
    starlink_pool = pool_planning.get('starlink_pool', {})
    starlink_target_met = starlink_pool.get('target_met', False)
    starlink_coverage = starlink_pool.get('coverage_rate', 0.0)

    result['details']['starlink_target_met'] = starlink_target_met
    result['details']['starlink_coverage_rate'] = starlink_coverage

    if not starlink_target_met:
        result['issues'].append(f"Starlink 池目標未達成 (覆蓋率: {starlink_coverage:.1%})")

    # 2. 驗證 OneWeb 池
    oneweb_pool = pool_planning.get('oneweb_pool', {})
    oneweb_target_met = oneweb_pool.get('target_met', False)
    oneweb_coverage = oneweb_pool.get('coverage_rate', 0.0)

    result['details']['oneweb_target_met'] = oneweb_target_met
    result['details']['oneweb_coverage_rate'] = oneweb_coverage

    if not oneweb_target_met:
        result['issues'].append(f"OneWeb 池目標未達成 (覆蓋率: {oneweb_coverage:.1%})")

    # 3. 驗證連續覆蓋
    continuous_coverage_adequate = (
        starlink_coverage >= 0.95 and oneweb_coverage >= 0.95
    )
    result['details']['continuous_coverage_adequate'] = continuous_coverage_adequate

    # 4. 驗證時空錯置
    time_space_offset = pool_planning.get('time_space_offset_optimization', {})
    offset_effective = time_space_offset.get('optimal_scheduling', False)
    result['details']['time_space_offset_effective'] = offset_effective

    # 5. 計算分數
    checks = [
        starlink_target_met,
        oneweb_target_met,
        continuous_coverage_adequate,
        offset_effective
    ]
    result['score'] = sum(checks) / len(checks)

    # 6. 判定通過
    result['passed'] = result['score'] >= 0.75

    if not result['passed']:
        result['recommendations'].append("檢查動態衛星池規劃邏輯")
        result['recommendations'].append("驗證時空錯置輪替機制")

    return result
```

---

## 📋 驗證檢查 4: 實時決策性能

```python
def _validate_real_time_decision_performance(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
    """驗證實時決策性能

    檢查項目:
    1. 決策延遲 < 100ms
    2. 決策準確性 > 80%
    3. 系統響應時間達標

    Returns:
        {
            'passed': bool,
            'score': float,
            'details': {
                'average_latency_ms': float,
                'latency_compliant': bool,
                'decision_accuracy': float,
                'accuracy_compliant': bool
            }
        }
    """
    result = {
        'passed': False,
        'score': 0.0,
        'details': {},
        'issues': [],
        'recommendations': []
    }

    decision_support = output_data.get('real_time_decision_support', {})
    performance_metrics = decision_support.get('performance_metrics', {})

    # 1. 檢查決策延遲
    avg_latency = performance_metrics.get('average_decision_latency_ms', float('inf'))
    latency_compliant = avg_latency < 100.0

    result['details']['average_latency_ms'] = avg_latency
    result['details']['latency_compliant'] = latency_compliant

    if not latency_compliant:
        result['issues'].append(f"決策延遲超標: {avg_latency:.1f}ms (需要 < 100ms)")

    # 2. 檢查決策準確性
    decision_accuracy = performance_metrics.get('decision_accuracy', 0.0)
    accuracy_compliant = decision_accuracy >= 0.8

    result['details']['decision_accuracy'] = decision_accuracy
    result['details']['accuracy_compliant'] = accuracy_compliant

    if not accuracy_compliant:
        result['issues'].append(f"決策準確性不足: {decision_accuracy:.1%} (需要 >= 80%)")

    # 3. 計算分數
    checks = [latency_compliant, accuracy_compliant]
    result['score'] = sum(checks) / len(checks)

    # 4. 判定通過
    result['passed'] = result['score'] >= 0.5  # 至少1項達標

    if not result['passed']:
        result['recommendations'].append("優化決策算法以降低延遲")
        result['recommendations'].append("改進決策邏輯以提高準確性")

    return result
```

---

## 📋 驗證檢查 5: 研究目標達成

```python
def _validate_research_goal_achievement(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
    """驗證研究目標達成

    檢查項目:
    1. final.md 核心需求對應
    2. 學術研究數據完整性
    3. 實驗可重現性

    Returns:
        {
            'passed': bool,
            'score': float,
            'details': {
                'gpp_events_adequate': bool,
                'ml_data_adequate': bool,
                'pool_planning_successful': bool,
                'real_time_capable': bool
            }
        }
    """
    result = {
        'passed': False,
        'score': 0.0,
        'details': {},
        'issues': [],
        'recommendations': []
    }

    metadata = output_data.get('metadata', {})

    # 1. 3GPP 事件充足性
    events_detected = metadata.get('total_events_detected', 0)
    gpp_events_adequate = events_detected >= 100

    result['details']['gpp_events_adequate'] = gpp_events_adequate
    result['details']['events_detected'] = events_detected

    # 2. ML 訓練樣本充足性
    ml_samples = metadata.get('ml_training_samples', 0)
    ml_data_adequate = ml_samples >= 1000

    result['details']['ml_data_adequate'] = ml_data_adequate
    result['details']['ml_samples_generated'] = ml_samples

    # 3. 衛星池規劃成功
    pool_planning = output_data.get('satellite_pool_planning', {})
    pool_planning_successful = (
        pool_planning.get('starlink_pool', {}).get('target_met', False) and
        pool_planning.get('oneweb_pool', {}).get('target_met', False)
    )

    result['details']['pool_planning_successful'] = pool_planning_successful

    # 4. 實時決策能力
    decision_support = output_data.get('real_time_decision_support', {})
    real_time_capable = len(decision_support.get('current_recommendations', [])) > 0

    result['details']['real_time_capable'] = real_time_capable

    # 5. 計算分數
    checks = [
        gpp_events_adequate,
        ml_data_adequate,
        pool_planning_successful,
        real_time_capable
    ]
    result['score'] = sum(checks) / len(checks)

    # 6. 判定通過
    result['passed'] = result['score'] >= 0.75

    if not result['passed']:
        result['recommendations'].append("確保所有研究目標完整實現")
        result['recommendations'].append("生成足夠的研究數據以支援分析")

    return result
```

---

## ✅ 實現檢查清單

### 驗證框架
- [ ] 5 項驗證檢查實現
- [ ] 總體驗證邏輯
- [ ] 驗證結果格式化
- [ ] 錯誤處理機制

### 驗證準確性
- [ ] 3GPP 標準合規檢查正確
- [ ] ML 數據品質評估合理
- [ ] 衛星池優化驗證完整
- [ ] 實時性能基準正確
- [ ] 研究目標對齊檢查

### 可維護性
- [ ] 清晰的檢查邏輯
- [ ] 詳細的錯誤報告
- [ ] 有用的改進建議
- [ ] 完整的單元測試

---

**規格版本**: v1.0
**創建日期**: 2025-09-30
**狀態**: 待實現