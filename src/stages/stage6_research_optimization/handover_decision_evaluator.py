#!/usr/bin/env python3
"""
換手決策評估器 - Stage 6 核心組件

提供歷史資料重現場景的換手決策評估。

依據:
- docs/stages/stage6-research-optimization.md Line 103-107, 649-669
- 3GPP TS 38.331 換手決策標準

Author: ORBIT Engine Team
Created: 2025-10-03

🎓 學術合規性檢查提醒:
- 修改此文件前，請先閱讀: docs/stages/STAGE6_COMPLIANCE_CHECKLIST.md
- 重點檢查: RSRP改善門檻必須有明確學術依據
- 所有判斷門檻必須從 handover_constants.py 載入或有明確學術依據
- 禁用詞: 假設、估計、簡化、模擬
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# 導入換手決策常數 (學術標準合規)
from src.shared.constants.handover_constants import (
    get_handover_weights,
    get_handover_config
)


class HandoverDecisionEvaluator:
    """換手決策評估器

    專為歷史資料重現設計的批次決策評估工具：
    1. 多候選評估: 評估 3-5 個換手候選的優劣
    2. 標準門檻: 使用固定的 3GPP/ITU 學術標準門檻
    3. 決策可追溯: 完整的決策過程記錄和分析
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化決策評估器

        Args:
            config: 配置參數
                - confidence_threshold: 信心門檻 (預設 0.8)
                - candidate_evaluation_count: 候選評估數量 (預設 5)
        """
        self.config = self._load_config(config)
        self.logger = logging.getLogger(__name__)

        # 載入學術標準權重和配置
        # SOURCE: src/shared/constants/handover_constants.py
        self.weights = get_handover_weights()
        self.standard_config = get_handover_config()

        self.logger.info("換手決策評估器初始化完成")
        self.logger.info(f"   學術標準權重: 信號{self.weights.SIGNAL_QUALITY_WEIGHT} + 幾何{self.weights.GEOMETRY_WEIGHT} + 穩定{self.weights.STABILITY_WEIGHT}")

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
                'recommendation': 'maintain' | 'handover_to_{satellite_id}',
                'target_satellite_id': Optional[str],
                'confidence_score': float,
                'reasoning': {...},
                'evaluated_candidates': [...],
                'decision_trace': {...}
            }
        """
        try:
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

            # 5. 構建決策結果
            result = {
                'decision_id': decision_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'recommendation': decision['recommendation'],
                'target_satellite_id': decision.get('target_satellite_id'),
                'confidence_score': decision['confidence'],
                'reasoning': decision['reasoning'],
                'evaluated_candidates': candidate_evaluations,
                'decision_trace': decision['trace']
            }

            self.logger.debug(
                f"決策完成 - ID: {decision_id}, "
                f"建議: {decision['recommendation']}"
            )

            return result

        except Exception as e:
            self.logger.error(f"做出換手決策時發生錯誤: {str(e)}", exc_info=True)

            return {
                'decision_id': self._generate_decision_id(),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'recommendation': 'maintain',
                'target_satellite_id': None,
                'confidence_score': 0.0,
                'reasoning': {'error': str(e)},
                'evaluated_candidates': [],
                'decision_trace': {}
            }

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

        try:
            for candidate in candidate_satellites:
                evaluation = {
                    'satellite_id': candidate.get('satellite_id', 'UNKNOWN'),
                    'overall_score': 0.0,
                    'signal_quality_score': 0.0,
                    'geometry_score': 0.0,
                    'stability_score': 0.0,
                    'improvement_metrics': {},
                    'handover_feasibility': False
                }

                # 提取必要數據
                signal_quality = candidate.get('signal_quality', {})
                visibility_metrics = candidate.get('visibility_metrics', {})
                physical_parameters = candidate.get('physical_parameters', {})
                quality_assessment = candidate.get('quality_assessment', {})

                serving_signal = serving_satellite.get('signal_quality', {})
                serving_physical = serving_satellite.get('physical_parameters', {})
                serving_quality = serving_satellite.get('quality_assessment', {})

                candidate_rsrp = signal_quality.get('rsrp_dbm', -120.0)
                serving_rsrp = serving_signal.get('rsrp_dbm', -120.0)

                # 1. 信號品質評分 (0-1)
                # 標準化到 [0, 1] 範圍 (-120dBm ~ -60dBm)
                rsrp_normalized = (candidate_rsrp + 120) / 60.0
                evaluation['signal_quality_score'] = max(0.0, min(1.0, rsrp_normalized))

                # 2. 幾何評分 (基於仰角和距離)
                elevation = visibility_metrics.get('elevation_deg', 0.0)
                distance = physical_parameters.get('distance_km', 9999.0)

                # 仰角越高越好 (0-90度 -> 0-1)
                elevation_score = elevation / 90.0

                # 距離適中最好
                # SOURCE: HandoverDecisionWeights.OPTIMAL_DISTANCE_MIN/MAX_KM
                # 依據: LEO 衛星覆蓋範圍分析
                optimal_min = self.weights.OPTIMAL_DISTANCE_MIN_KM
                optimal_max = self.weights.OPTIMAL_DISTANCE_MAX_KM

                if optimal_min <= distance <= optimal_max:
                    distance_score = 1.0
                elif distance < optimal_min:
                    distance_score = distance / optimal_min
                else:
                    distance_score = max(0.0, 1.0 - (distance - optimal_max) / 1000.0)

                evaluation['geometry_score'] = (elevation_score + distance_score) / 2.0

                # 3. 穩定性評分 (基於 SINR 和鏈路裕度)
                sinr = signal_quality.get('rs_sinr_db', -10.0)
                link_margin = quality_assessment.get('link_margin_db', 0.0)

                # SINR 標準化 (-10dB ~ +30dB)
                sinr_score = (sinr + 10) / 40.0
                sinr_score = max(0.0, min(1.0, sinr_score))

                # 鏈路裕度標準化 (0 ~ 20dB)
                margin_score = link_margin / 20.0
                margin_score = max(0.0, min(1.0, margin_score))

                evaluation['stability_score'] = (sinr_score + margin_score) / 2.0

                # 4. 計算總體評分 (學術標準加權平均)
                # SOURCE: HandoverDecisionWeights (AHP 理論)
                # 依據: Saaty (1980) "The Analytic Hierarchy Process"
                evaluation['overall_score'] = (
                    self.weights.SIGNAL_QUALITY_WEIGHT * evaluation['signal_quality_score'] +
                    self.weights.GEOMETRY_WEIGHT * evaluation['geometry_score'] +
                    self.weights.STABILITY_WEIGHT * evaluation['stability_score']
                )

                # 5. 改善指標
                serving_sinr = serving_signal.get('rs_sinr_db', -10.0)
                serving_distance = serving_physical.get('distance_km', 0.0)

                evaluation['improvement_metrics'] = {
                    'rsrp_improvement_db': candidate_rsrp - serving_rsrp,
                    'sinr_improvement_db': sinr - serving_sinr,
                    'distance_change_km': distance - serving_distance
                }

                # 6. 換手可行性判斷
                # SOURCE: HandoverDecisionWeights 門檻值
                # 依據: 3GPP TS 36.300 Section 10.1.2.2.1
                is_usable = quality_assessment.get('is_usable', False)
                rsrp_improvement = evaluation['improvement_metrics']['rsrp_improvement_db']

                evaluation['handover_feasibility'] = (
                    evaluation['overall_score'] > self.weights.HANDOVER_THRESHOLD and
                    rsrp_improvement > self.weights.MIN_RSRP_IMPROVEMENT_DB and
                    is_usable
                )

                evaluations.append(evaluation)

            # 按總體評分排序
            evaluations.sort(key=lambda x: x['overall_score'], reverse=True)

            return evaluations

        except Exception as e:
            self.logger.error(f"評估候選衛星時發生錯誤: {str(e)}", exc_info=True)
            return []

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
            'event_count': len(gpp_events) if gpp_events else 0,
            'recommended_action': 'maintain'
        }

        if not gpp_events:
            return analysis

        try:
            # 檢查事件類型和嚴重程度
            a4_events = [e for e in gpp_events if e.get('event_type') == 'A4']
            a5_events = [e for e in gpp_events if e.get('event_type') == 'A5']
            d2_events = [e for e in gpp_events if e.get('event_type') == 'D2']

            if a5_events:
                # A5 事件表示服務衛星劣化且有更好候選 (最嚴重)
                analysis['handover_urgency'] = 'high'
                analysis['triggering_events'].extend(a5_events)
                analysis['recommended_action'] = 'handover'
            elif d2_events:
                # D2 事件表示基於距離的換手觸發
                analysis['handover_urgency'] = 'medium'
                analysis['triggering_events'].extend(d2_events)
                analysis['recommended_action'] = 'handover'
            elif a4_events:
                # A4 事件表示鄰近衛星變得優於門檻值
                analysis['handover_urgency'] = 'medium'
                analysis['triggering_events'].extend(a4_events)
                analysis['recommended_action'] = 'evaluate'

            return analysis

        except Exception as e:
            self.logger.error(f"分析 3GPP 事件時發生錯誤: {str(e)}", exc_info=True)
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

        try:
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
                decision['trace'] = {
                    'total_candidates_evaluated': len(candidate_evaluations),
                    'feasible_candidates_count': 0
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
                # SOURCE: 3GPP TS 36.300 Section 10.1.2.2.1 - A3/A4 事件門檻
                # 依據: 典型 RSRP 改善門檻 3-6 dB (考慮測量不確定性 ±2dB)
                # 選擇 5.0 dB 的理由: 平衡響應速度和測量誤差容忍度
                RSRP_IMPROVEMENT_THRESHOLD = 5.0  # dB
                if rsrp_improvement > RSRP_IMPROVEMENT_THRESHOLD:
                    handover_recommended = True
                    confidence = 0.85

            # 基於服務衛星劣化的決策
            serving_quality_assessment = serving_satellite.get('quality_assessment', {})
            serving_quality = serving_quality_assessment.get('quality_level', 'unknown')

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
                'feasible_candidates_count': len(feasible_candidates),
                'total_candidates_evaluated': len(candidate_evaluations)
            }

            return decision

        except Exception as e:
            self.logger.error(f"計算決策時發生錯誤: {str(e)}", exc_info=True)
            return {
                'recommendation': 'maintain',
                'target_satellite_id': None,
                'confidence': 0.0,
                'reasoning': {'error': str(e)},
                'trace': {}
            }

    def _generate_decision_id(self) -> str:
        """生成決策ID"""
        import time
        timestamp_ms = int(time.time() * 1000)
        return f"HO_DECISION_{timestamp_ms}"

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數

        SOURCE: HandoverDecisionConfig 提供學術標準默認值
        """
        # 從學術標準配置讀取默認值
        std_config = get_handover_config()

        default_config = {
            # SOURCE: HandoverDecisionConfig.CONFIDENCE_THRESHOLD
            # 依據: 統計決策理論，80% 信心對應 95% 成功率
            'confidence_threshold': std_config.CONFIDENCE_THRESHOLD,

            # SOURCE: HandoverDecisionConfig.CANDIDATE_EVALUATION_COUNT
            # 依據: 計算複雜度與決策質量平衡
            'candidate_evaluation_count': std_config.CANDIDATE_EVALUATION_COUNT
        }

        if config:
            default_config.update(config)

        return default_config
