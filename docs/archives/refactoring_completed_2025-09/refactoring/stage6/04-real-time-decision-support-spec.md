# 實時決策支援系統規格 - Stage 6 核心組件

**檔案**: `src/stages/stage6_research_optimization/real_time_decision_support.py`
**依據**: `docs/stages/stage6-research-optimization.md` Line 103-107, 649-669
**目標**: < 100ms 換手決策響應

---

## 🎯 核心職責

提供毫秒級的實時換手決策支援：
1. **多候選評估**: 同時評估 3-5 個換手候選的優劣
2. **自適應門檻**: 根據環境動態調整 RSRP/距離門檻
3. **決策可追溯**: 完整的決策過程記錄和分析
4. **性能保證**: < 100ms 決策延遲

---

## 🏗️ 類別設計

```python
class RealTimeDecisionSupport:
    """實時決策支援系統"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化決策支援系統

        Args:
            config: 配置參數
                - decision_latency_target_ms: 決策延遲目標 (預設 100ms)
                - confidence_threshold: 信心門檻 (預設 0.8)
                - candidate_evaluation_count: 候選評估數量 (預設 5)
                - adaptive_thresholds: 是否啟用自適應門檻 (預設 True)
        """
        self.config = self._load_config(config)
        self.logger = logging.getLogger(__name__)

        # 決策歷史記錄
        self.decision_history = []

        # 性能統計
        self.performance_stats = {
            'total_decisions': 0,
            'average_latency_ms': 0.0,
            'max_latency_ms': 0.0,
            'successful_decisions': 0,
            'failed_decisions': 0
        }

        # 自適應門檻
        self.adaptive_thresholds = {
            'rsrp_threshold_dbm': -95.0,
            'distance_threshold_km': 1500.0,
            'elevation_threshold_deg': 10.0
        }

    def make_handover_decision(
        self,
        serving_satellite: Dict[str, Any],
        candidate_satellites: List[Dict[str, Any]],
        gpp_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """做出換手決策

        Args:
            serving_satellite: 當前服務衛星數據
            candidate_satellites: 候選衛星列表 (3-5顆)
            gpp_events: 相關的 3GPP 事件

        Returns:
            {
                'decision_id': str,
                'timestamp': str,
                'decision_latency_ms': float,
                'recommendation': 'maintain' | 'handover_to_{satellite_id}',
                'target_satellite_id': Optional[str],
                'confidence_score': float,
                'reasoning': {...},
                'evaluated_candidates': [...],
                'decision_trace': {...}
            }
        """
        import time
        decision_start = time.time()

        # 1. 生成決策ID
        decision_id = self._generate_decision_id()

        # 2. 評估所有候選衛星
        candidate_evaluations = self._evaluate_candidates(
            serving_satellite,
            candidate_satellites
        )

        # 3. 結合 3GPP 事件分析
        gpp_analysis = self._analyze_gpp_events(gpp_events, serving_satellite)

        # 4. 計算決策
        decision = self._calculate_decision(
            serving_satellite,
            candidate_evaluations,
            gpp_analysis
        )

        # 5. 計算決策延遲
        decision_latency_ms = (time.time() - decision_start) * 1000

        # 6. 構建決策結果
        result = {
            'decision_id': decision_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_latency_ms': decision_latency_ms,
            'recommendation': decision['recommendation'],
            'target_satellite_id': decision.get('target_satellite_id'),
            'confidence_score': decision['confidence'],
            'reasoning': decision['reasoning'],
            'evaluated_candidates': candidate_evaluations,
            'decision_trace': decision['trace'],
            'performance_benchmark': {
                'latency_met': decision_latency_ms < self.config['decision_latency_target_ms'],
                'confidence_met': decision['confidence'] >= self.config['confidence_threshold']
            }
        }

        # 7. 記錄決策歷史
        self._record_decision(result)

        # 8. 更新性能統計
        self._update_performance_stats(result)

        return result

    def _evaluate_candidates(
        self,
        serving_satellite: Dict[str, Any],
        candidate_satellites: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """評估候選衛星

        Returns:
            [
                {
                    'satellite_id': str,
                    'overall_score': float,  # 0-1
                    'signal_quality_score': float,
                    'geometry_score': float,
                    'stability_score': float,
                    'improvement_metrics': {...},
                    'handover_feasibility': bool
                }
            ]
        """
        evaluations = []

        for candidate in candidate_satellites:
            evaluation = {
                'satellite_id': candidate['satellite_id'],
                'overall_score': 0.0,
                'signal_quality_score': 0.0,
                'geometry_score': 0.0,
                'stability_score': 0.0,
                'improvement_metrics': {},
                'handover_feasibility': False
            }

            # 1. 信號品質評分 (0-1)
            candidate_rsrp = candidate['signal_quality']['rsrp_dbm']
            serving_rsrp = serving_satellite['signal_quality']['rsrp_dbm']

            # 標準化到 [0, 1] 範圍 (-120dBm ~ -60dBm)
            rsrp_normalized = (candidate_rsrp + 120) / 60.0
            evaluation['signal_quality_score'] = max(0.0, min(1.0, rsrp_normalized))

            # 2. 幾何評分 (基於仰角和距離)
            elevation = candidate['visibility_metrics']['elevation_deg']
            distance = candidate['physical_parameters']['distance_km']

            # 仰角越高越好 (0-90度 -> 0-1)
            elevation_score = elevation / 90.0

            # 距離適中最好 (500-1500km最優)
            if 500 <= distance <= 1500:
                distance_score = 1.0
            elif distance < 500:
                distance_score = distance / 500.0
            else:
                distance_score = max(0.0, 1.0 - (distance - 1500) / 1000.0)

            evaluation['geometry_score'] = (elevation_score + distance_score) / 2.0

            # 3. 穩定性評分 (基於 SINR 和鏈路裕度)
            sinr = candidate['signal_quality']['rs_sinr_db']
            link_margin = candidate['quality_assessment']['link_margin_db']

            # SINR 標準化 (-10dB ~ +30dB)
            sinr_score = (sinr + 10) / 40.0
            sinr_score = max(0.0, min(1.0, sinr_score))

            # 鏈路裕度標準化 (0 ~ 20dB)
            margin_score = link_margin / 20.0
            margin_score = max(0.0, min(1.0, margin_score))

            evaluation['stability_score'] = (sinr_score + margin_score) / 2.0

            # 4. 計算總體評分 (加權平均)
            evaluation['overall_score'] = (
                0.5 * evaluation['signal_quality_score'] +
                0.3 * evaluation['geometry_score'] +
                0.2 * evaluation['stability_score']
            )

            # 5. 改善指標
            evaluation['improvement_metrics'] = {
                'rsrp_improvement_db': candidate_rsrp - serving_rsrp,
                'sinr_improvement_db': sinr - serving_satellite['signal_quality']['rs_sinr_db'],
                'distance_change_km': distance - serving_satellite['physical_parameters']['distance_km']
            }

            # 6. 換手可行性判斷
            evaluation['handover_feasibility'] = (
                evaluation['overall_score'] > 0.6 and
                evaluation['improvement_metrics']['rsrp_improvement_db'] > 3.0 and
                candidate['quality_assessment']['is_usable']
            )

            evaluations.append(evaluation)

        # 按總體評分排序
        evaluations.sort(key=lambda x: x['overall_score'], reverse=True)

        return evaluations

    def _analyze_gpp_events(
        self,
        gpp_events: List[Dict[str, Any]],
        serving_satellite: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析 3GPP 事件對決策的影響

        Returns:
            {
                'handover_urgency': 'critical' | 'high' | 'medium' | 'low',
                'triggering_events': [...],
                'event_count': int,
                'recommended_action': str
            }
        """
        analysis = {
            'handover_urgency': 'low',
            'triggering_events': [],
            'event_count': len(gpp_events),
            'recommended_action': 'maintain'
        }

        if not gpp_events:
            return analysis

        # 檢查事件類型和嚴重程度
        a5_events = [e for e in gpp_events if e['event_type'] == 'A5']
        d2_events = [e for e in gpp_events if e['event_type'] == 'D2']

        if a5_events:
            # A5 事件表示服務衛星劣化且有更好候選
            analysis['handover_urgency'] = 'high'
            analysis['triggering_events'].extend(a5_events)
            analysis['recommended_action'] = 'handover'
        elif d2_events:
            # D2 事件表示基於距離的換手觸發
            analysis['handover_urgency'] = 'medium'
            analysis['triggering_events'].extend(d2_events)
            analysis['recommended_action'] = 'handover'

        return analysis

    def _calculate_decision(
        self,
        serving_satellite: Dict[str, Any],
        candidate_evaluations: List[Dict[str, Any]],
        gpp_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """計算最終決策

        Returns:
            {
                'recommendation': str,
                'target_satellite_id': Optional[str],
                'confidence': float,
                'reasoning': {...},
                'trace': {...}
            }
        """
        decision = {
            'recommendation': 'maintain',
            'target_satellite_id': None,
            'confidence': 0.0,
            'reasoning': {},
            'trace': {}
        }

        # 1. 檢查是否有可行的候選
        feasible_candidates = [
            c for c in candidate_evaluations if c['handover_feasibility']
        ]

        if not feasible_candidates:
            decision['confidence'] = 0.9
            decision['reasoning'] = {
                'no_feasible_candidates': True,
                'serving_satellite_adequate': True
            }
            return decision

        # 2. 獲取最佳候選
        best_candidate = feasible_candidates[0]

        # 3. 決策邏輯
        handover_recommended = False
        confidence = 0.0

        # 基於 3GPP 事件的決策
        if gpp_analysis['handover_urgency'] in ['critical', 'high']:
            handover_recommended = True
            confidence = 0.95

        # 基於評分差異的決策
        elif best_candidate['overall_score'] > 0.8:
            rsrp_improvement = best_candidate['improvement_metrics']['rsrp_improvement_db']
            if rsrp_improvement > 5.0:
                handover_recommended = True
                confidence = 0.85

        # 基於服務衛星劣化的決策
        serving_quality = serving_satellite['quality_assessment']['quality_level']
        if serving_quality in ['poor', 'fair'] and best_candidate['overall_score'] > 0.7:
            handover_recommended = True
            confidence = 0.8

        # 4. 構建決策
        if handover_recommended:
            decision['recommendation'] = f"handover_to_{best_candidate['satellite_id']}"
            decision['target_satellite_id'] = best_candidate['satellite_id']
            decision['confidence'] = confidence
            decision['reasoning'] = {
                'current_rsrp_degraded': serving_quality in ['poor', 'fair'],
                'candidate_rsrp_superior': best_candidate['overall_score'] > 0.7,
                'distance_acceptable': best_candidate['improvement_metrics']['distance_change_km'] < 500,
                'qos_improvement_expected': best_candidate['improvement_metrics']['rsrp_improvement_db'] > 3.0,
                'gpp_event_triggered': len(gpp_analysis['triggering_events']) > 0
            }
        else:
            decision['recommendation'] = 'maintain'
            decision['confidence'] = 0.85
            decision['reasoning'] = {
                'serving_satellite_adequate': True,
                'insufficient_improvement': True
            }

        # 5. 決策追蹤
        decision['trace'] = {
            'best_candidate_score': best_candidate['overall_score'],
            'rsrp_improvement': best_candidate['improvement_metrics']['rsrp_improvement_db'],
            'gpp_urgency': gpp_analysis['handover_urgency'],
            'feasible_candidates_count': len(feasible_candidates)
        }

        return decision

    def update_adaptive_thresholds(
        self,
        decision_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """更新自適應門檻

        基於歷史決策成功率動態調整門檻
        """
        if not self.config['adaptive_thresholds']:
            return self.adaptive_thresholds

        # 分析最近100個決策的成功率
        recent_decisions = decision_history[-100:]
        if not recent_decisions:
            return self.adaptive_thresholds

        success_rate = sum(
            1 for d in recent_decisions if d.get('success', False)
        ) / len(recent_decisions)

        # 根據成功率調整門檻
        if success_rate < 0.8:
            # 成功率低，放寬門檻
            self.adaptive_thresholds['rsrp_threshold_dbm'] += 2.0
            self.adaptive_thresholds['distance_threshold_km'] += 100.0
        elif success_rate > 0.95:
            # 成功率高，提高門檻
            self.adaptive_thresholds['rsrp_threshold_dbm'] -= 1.0
            self.adaptive_thresholds['distance_threshold_km'] -= 50.0

        return self.adaptive_thresholds

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            'average_decision_latency_ms': self.performance_stats['average_latency_ms'],
            'max_decision_latency_ms': self.performance_stats['max_latency_ms'],
            'total_decisions': self.performance_stats['total_decisions'],
            'decision_accuracy': (
                self.performance_stats['successful_decisions'] /
                self.performance_stats['total_decisions']
                if self.performance_stats['total_decisions'] > 0 else 0.0
            ),
            'latency_target_compliance': (
                self.performance_stats['average_latency_ms'] <
                self.config['decision_latency_target_ms']
            )
        }

    def _generate_decision_id(self) -> str:
        """生成決策ID"""
        import time
        timestamp_ms = int(time.time() * 1000)
        return f"HO_DECISION_{timestamp_ms}"

    def _record_decision(self, decision: Dict[str, Any]):
        """記錄決策歷史"""
        self.decision_history.append(decision)

        # 保持最近1000條記錄
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]

    def _update_performance_stats(self, decision: Dict[str, Any]):
        """更新性能統計"""
        self.performance_stats['total_decisions'] += 1

        latency = decision['decision_latency_ms']
        total = self.performance_stats['total_decisions']

        # 更新平均延遲
        self.performance_stats['average_latency_ms'] = (
            (self.performance_stats['average_latency_ms'] * (total - 1) + latency) / total
        )

        # 更新最大延遲
        if latency > self.performance_stats['max_latency_ms']:
            self.performance_stats['max_latency_ms'] = latency

        # 更新成功/失敗計數
        if decision['performance_benchmark']['latency_met'] and \
           decision['performance_benchmark']['confidence_met']:
            self.performance_stats['successful_decisions'] += 1
        else:
            self.performance_stats['failed_decisions'] += 1

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數"""
        default_config = {
            'decision_latency_target_ms': 100,
            'confidence_threshold': 0.8,
            'candidate_evaluation_count': 5,
            'adaptive_thresholds': True,
            'decision_history_size': 1000
        }

        if config:
            default_config.update(config)

        return default_config
```

---

## 📊 輸出數據格式

```python
{
    'current_recommendations': [
        {
            'decision_id': 'HO_DECISION_1695024000456',
            'timestamp': '2025-09-27T08:00:00.456789+00:00',
            'decision_latency_ms': 45.3,
            'recommendation': 'handover_to_STARLINK-1234',
            'target_satellite_id': 'STARLINK-1234',
            'confidence_score': 0.92,
            'reasoning': {
                'current_rsrp_degraded': True,
                'candidate_rsrp_superior': True,
                'distance_acceptable': True,
                'qos_improvement_expected': 0.15,
                'gpp_event_triggered': True
            },
            'evaluated_candidates': [
                {
                    'satellite_id': 'STARLINK-1234',
                    'overall_score': 0.89,
                    'signal_quality_score': 0.92,
                    'geometry_score': 0.85,
                    'stability_score': 0.90,
                    'handover_feasibility': True
                }
                # ... 更多候選
            ],
            'performance_benchmark': {
                'latency_met': True,  # < 100ms
                'confidence_met': True  # > 0.8
            }
        }
    ],
    'performance_metrics': {
        'average_decision_latency_ms': 47.3,
        'max_decision_latency_ms': 89.2,
        'total_decisions': 24,
        'decision_accuracy': 0.94,
        'handover_success_rate': 0.96,
        'latency_target_compliance': True
    },
    'adaptive_thresholds': {
        'current_rsrp_threshold_dbm': -93.5,
        'current_distance_threshold_km': 1550.0,
        'current_elevation_threshold_deg': 9.5,
        'adjustment_history': [...]
    }
}
```

---

## ✅ 實現檢查清單

### 功能完整性
- [ ] 多候選評估邏輯
- [ ] 3GPP 事件分析整合
- [ ] 決策計算邏輯
- [ ] 自適應門檻調整
- [ ] 決策歷史記錄
- [ ] 性能統計追蹤

### 性能要求
- [ ] < 100ms 決策延遲
- [ ] 5 個候選同時評估
- [ ] 記憶體效率優化
- [ ] 實時響應能力

### 決策品質
- [ ] 信心分數計算
- [ ] 推理過程可追溯
- [ ] 決策成功率追蹤
- [ ] 自適應優化能力

### 單元測試
- [ ] 候選評估測試
- [ ] 決策邏輯測試
- [ ] 性能基準測試
- [ ] 自適應門檻測試

---

**規格版本**: v1.0
**創建日期**: 2025-09-30
**狀態**: 待實現