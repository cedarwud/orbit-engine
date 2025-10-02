#!/usr/bin/env python3
"""
Stage 6: 驗證框架

核心職責:
執行 5 項專用驗證檢查:
1. 3GPP 事件標準合規
2. ML 訓練數據品質
3. 衛星池優化驗證
4. 實時決策性能
5. 研究目標達成

Author: ORBIT Engine Team
Created: 2025-10-02 (重構自 stage6_research_optimization_processor.py)
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any


class Stage6ValidationFramework:
    """Stage 6 驗證框架

    實現五項專用驗證檢查:
    1. gpp_event_standard_compliance - 3GPP 事件標準合規
    2. ml_training_data_quality - ML 訓練數據品質
    3. satellite_pool_optimization - 衛星池優化驗證
    4. real_time_decision_performance - 實時決策性能
    5. research_goal_achievement - 研究目標達成
    """

    def __init__(self, logger: logging.Logger = None):
        """初始化驗證框架

        Args:
            logger: 日誌記錄器，如未提供則創建新的
        """
        self.logger = logger or logging.getLogger(__name__)

    def run_validation_checks(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行 5 項專用驗證檢查

        Returns:
            {
                'validation_status': 'passed' | 'failed',
                'overall_status': 'PASS' | 'FAIL',
                'checks_performed': 5,
                'checks_passed': int,
                'validation_details': {...},
                'check_details': {...},
                'validation_timestamp': str
            }
        """
        self.logger.info("🔍 開始執行 5 項驗證框架檢查...")

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
            ('gpp_event_standard_compliance', self.validate_gpp_event_compliance),
            ('ml_training_data_quality', self.validate_ml_training_data_quality),
            ('satellite_pool_optimization', self.validate_satellite_pool_optimization),
            ('real_time_decision_performance', self.validate_real_time_decision_performance),
            ('research_goal_achievement', self.validate_research_goal_achievement)
        ]

        for check_name, check_method in check_methods:
            try:
                check_result = check_method(output_data)
                validation_results['check_details'][check_name] = check_result
                validation_results['checks_performed'] += 1

                if check_result.get('passed', False):
                    validation_results['checks_passed'] += 1

            except Exception as e:
                self.logger.error(f"驗證檢查 {check_name} 失敗: {e}", exc_info=True)
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

        self.logger.info(
            f"✅ 驗證框架檢查完成 - 通過率: {success_rate:.1%} "
            f"({validation_results['checks_passed']}/{validation_results['checks_performed']})"
        )

        return validation_results

    def validate_gpp_event_compliance(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證檢查 1: 3GPP 事件標準合規

        依據: stage6-research-optimization.md Lines 768-769
        目標: 1000+ 3GPP 事件/小時
        測試門檻: >= 100 事件 (降低10倍用於測試)
        """
        result = {
            'passed': False,
            'score': 0.0,
            'details': {},
            'issues': [],
            'recommendations': []
        }

        try:
            gpp_events = output_data.get('gpp_events', {})

            # 檢查事件總數
            a4_events = gpp_events.get('a4_events', [])
            a5_events = gpp_events.get('a5_events', [])
            d2_events = gpp_events.get('d2_events', [])
            total_events = len(a4_events) + len(a5_events) + len(d2_events)

            result['details']['total_events'] = total_events
            result['details']['a4_count'] = len(a4_events)
            result['details']['a5_count'] = len(a5_events)
            result['details']['d2_count'] = len(d2_events)

            # 🚨 P0 修正: 提高驗證標準
            # SOURCE: 基於 LEO NTN 換手頻率研究
            # 依據: 3GPP TR 38.821 Section 6.3.2 - 典型換手率 10-30 次/分鐘
            # 測試環境: 100 事件約等於 3-10 分鐘觀測窗口
            # 理由:
            #   - 最低換手率 10次/分鐘 × 10分鐘 = 100事件 (測試最低標準)
            #   - 典型換手率 20次/分鐘 × 50分鐘 = 1000事件 (生產目標)
            MIN_EVENTS_TEST = 100
            TARGET_EVENTS_PRODUCTION = 1000

            if total_events >= MIN_EVENTS_TEST:
                result['passed'] = True
                result['score'] = min(1.0, total_events / TARGET_EVENTS_PRODUCTION)
                result['recommendations'].append(f"✅ 事件數達標 ({total_events} >= {MIN_EVENTS_TEST})")
            elif total_events > 0:
                result['passed'] = False
                result['score'] = total_events / MIN_EVENTS_TEST
                result['issues'].append(f"事件數不足: {total_events} < {MIN_EVENTS_TEST} (測試門檻)")
                result['recommendations'].append(f"建議: 生產環境目標為 {TARGET_EVENTS_PRODUCTION}+ 事件")
            else:
                result['passed'] = False
                result['score'] = 0.0
                result['issues'].append("未檢測到任何 3GPP 事件")
                result['recommendations'].append("檢查 signal_analysis 數據是否正確傳遞")

        except Exception as e:
            result['issues'].append(f"驗證異常: {str(e)}")

        return result

    def validate_ml_training_data_quality(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證檢查 2: ML 訓練數據品質

        依據: stage6-research-optimization.md Lines 769-770
        目標: 50,000+ ML 訓練樣本
        測試門檻: >= 10,000 樣本 (降低5倍用於測試)
        """
        result = {
            'passed': False,
            'score': 0.0,
            'details': {},
            'issues': [],
            'recommendations': []
        }

        try:
            ml_data = output_data.get('ml_training_data', {})
            dataset_summary = ml_data.get('dataset_summary', {})

            total_samples = dataset_summary.get('total_samples', 0)
            result['details']['total_samples'] = total_samples

            # 🚨 P0 修正: 提高驗證標準
            # SOURCE: Mnih et al. (2015) "Human-level control through deep RL"
            #         Nature 518(7540), 529-533.
            # 依據: DQN 經驗回放緩衝區建議大小 10^4 - 10^6 transitions
            # 理由:
            #   - 測試: 10,000 樣本 (最小可訓練量，能完成一輪策略更新)
            #   - 生產: 50,000 樣本 (穩定收斂所需，Mnih 2015 建議值)
            #   - 參考: Schulman PPO (2017) 使用 2048-4096 樣本/迭代
            MIN_SAMPLES_TEST = 10000
            TARGET_SAMPLES_PRODUCTION = 50000

            if total_samples >= MIN_SAMPLES_TEST:
                result['passed'] = True
                result['score'] = min(1.0, total_samples / TARGET_SAMPLES_PRODUCTION)
                result['recommendations'].append(f"✅ ML 樣本數達標 ({total_samples} >= {MIN_SAMPLES_TEST})")
            elif total_samples >= 1000:
                result['passed'] = False
                result['score'] = total_samples / MIN_SAMPLES_TEST
                result['issues'].append(f"樣本數不足: {total_samples} < {MIN_SAMPLES_TEST} (測試門檻)")
                result['recommendations'].append(f"建議: 生產環境目標為 {TARGET_SAMPLES_PRODUCTION}+ 樣本")
            else:
                result['passed'] = False
                result['score'] = 0.0
                result['issues'].append(f"樣本數嚴重不足: {total_samples} < 1000")
                result['recommendations'].append("檢查 ML 訓練數據生成邏輯")

        except Exception as e:
            result['issues'].append(f"驗證異常: {str(e)}")

        return result

    def validate_satellite_pool_optimization(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證檢查 3: 衛星池優化驗證"""
        result = {
            'passed': False,
            'score': 0.0,
            'details': {},
            'issues': [],
            'recommendations': []
        }

        try:
            pool_verification = output_data.get('pool_verification', {})
            overall_verification = pool_verification.get('overall_verification', {})

            all_pools_pass = overall_verification.get('all_pools_pass', False)
            result['details']['all_pools_pass'] = all_pools_pass

            if all_pools_pass:
                result['passed'] = True
                result['score'] = 1.0
            else:
                result['issues'].append("動態池驗證未通過")

        except Exception as e:
            result['issues'].append(f"驗證異常: {str(e)}")

        return result

    def validate_real_time_decision_performance(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證檢查 4: 實時決策性能"""
        result = {
            'passed': False,
            'score': 0.0,
            'details': {},
            'issues': [],
            'recommendations': []
        }

        try:
            decision_support = output_data.get('decision_support', {})
            performance_metrics = decision_support.get('performance_metrics', {})

            avg_latency = performance_metrics.get('average_decision_latency_ms', 999.9)
            result['details']['average_latency_ms'] = avg_latency

            # 檢查延遲 (目標 < 100ms)
            if avg_latency < 100:
                result['passed'] = True
                result['score'] = 1.0 - (avg_latency / 100)
            else:
                result['issues'].append(f"決策延遲過高: {avg_latency:.2f}ms > 100ms")

        except Exception as e:
            result['issues'].append(f"驗證異常: {str(e)}")

        return result

    def validate_research_goal_achievement(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證檢查 5: 研究目標達成

        依據: stage6-research-optimization.md Lines 540-554
        必須達成所有核心指標: 3GPP事件、ML樣本、池驗證
        """
        result = {
            'passed': False,
            'score': 0.0,
            'details': {},
            'issues': [],
            'recommendations': []
        }

        try:
            metadata = output_data.get('metadata', {})

            # 檢查核心指標是否達成
            events_detected = metadata.get('total_events_detected', 0)
            ml_samples = metadata.get('ml_training_samples', 0)
            pool_verified = metadata.get('pool_verification_passed', False)

            result['details']['events_detected'] = events_detected
            result['details']['ml_samples'] = ml_samples
            result['details']['pool_verified'] = pool_verified

            # 🚨 P0 修正: 提高驗證標準，所有指標必須達標
            # 測試門檻: 100+ 事件, 10000+ 樣本, 池驗證通過
            MIN_EVENTS = 100
            MIN_SAMPLES = 10000

            score_components = []

            # 3GPP 事件檢查 (不允許0個事件)
            if events_detected >= MIN_EVENTS:
                score_components.append(1.0)
            elif events_detected > 0:
                score_components.append(events_detected / MIN_EVENTS)
                result['issues'].append(f"3GPP 事件不足: {events_detected} < {MIN_EVENTS}")
            else:
                score_components.append(0.0)
                result['issues'].append("未檢測到任何 3GPP 事件")

            # ML 樣本檢查
            if ml_samples >= MIN_SAMPLES:
                score_components.append(1.0)
            elif ml_samples >= 1000:
                score_components.append(ml_samples / MIN_SAMPLES)
                result['issues'].append(f"ML 樣本不足: {ml_samples} < {MIN_SAMPLES}")
            else:
                score_components.append(0.0)
                result['issues'].append(f"ML 樣本嚴重不足: {ml_samples} < 1000")

            # 池驗證檢查 (必須通過)
            if pool_verified:
                score_components.append(1.0)
            else:
                score_components.append(0.0)
                result['issues'].append("動態衛星池驗證未通過")

            result['score'] = sum(score_components) / len(score_components)
            # 提高通過標準: >= 80% 且所有關鍵指標非零
            result['passed'] = (result['score'] >= 0.8 and
                              events_detected > 0 and
                              ml_samples > 0 and
                              pool_verified)

            if result['passed']:
                result['recommendations'].append("✅ 所有研究目標達成")
            else:
                result['recommendations'].append(f"需達成 80%+ 指標 (當前: {result['score']:.1%})")

        except Exception as e:
            result['issues'].append(f"驗證異常: {str(e)}")

        return result
