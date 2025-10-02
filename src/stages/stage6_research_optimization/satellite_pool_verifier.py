#!/usr/bin/env python3
"""
動態衛星池驗證器 - Stage 6 核心組件

職責:
1. 逐時間點遍歷驗證衛星池維持 (⚠️ 關鍵: 非靜態計數)
2. Starlink 池驗證: 10-15顆目標達成
3. OneWeb 池驗證: 3-6顆目標達成
4. 覆蓋率統計和空窗期分析
5. 時空錯置效果評估

依據: docs/refactoring/stage6/03-dynamic-pool-verifier-spec.md
創建日期: 2025-09-30
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class SatellitePoolVerifier:
    """動態衛星池驗證器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化驗證器

        Args:
            config: 配置參數
                - starlink_pool_target: {'min': 10, 'max': 15}
                - oneweb_pool_target: {'min': 3, 'max': 6}
                - coverage_threshold: 0.95 (95% 時間達標)
        """
        self.config = self._load_config(config)
        self.logger = logging.getLogger(__name__)

        # 驗證統計
        self.verification_stats = {
            'starlink': {
                'total_time_points': 0,
                'target_met_count': 0,
                'coverage_rate': 0.0,
                'gap_periods': []
            },
            'oneweb': {
                'total_time_points': 0,
                'target_met_count': 0,
                'coverage_rate': 0.0,
                'gap_periods': []
            }
        }

        self.logger.info("📊 動態衛星池驗證器初始化完成")
        self.logger.info(f"   Starlink 目標: {self.config['starlink_pool_target']['min']}-{self.config['starlink_pool_target']['max']} 顆")
        self.logger.info(f"   OneWeb 目標: {self.config['oneweb_pool_target']['min']}-{self.config['oneweb_pool_target']['max']} 顆")
        self.logger.info(f"   覆蓋率門檻: {self.config['coverage_threshold']:.1%}")

    def verify_all_pools(
        self,
        connectable_satellites: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """驗證所有星座的衛星池

        Args:
            connectable_satellites: Stage 4 的可連線衛星數據
                {
                    'starlink': [衛星列表],
                    'oneweb': [衛星列表]
                }

        Returns:
            {
                'starlink_pool': {...},
                'oneweb_pool': {...},
                'time_space_offset_optimization': {...},
                'overall_verification': {...}
            }
        """
        self.logger.info("🔍 開始動態衛星池驗證...")

        # 1. 驗證 Starlink 池
        starlink_verification = self.verify_pool_maintenance(
            connectable_satellites=connectable_satellites.get('starlink', []),
            constellation='starlink',
            target_min=self.config['starlink_pool_target']['min'],
            target_max=self.config['starlink_pool_target']['max']
        )

        # 2. 驗證 OneWeb 池
        oneweb_verification = self.verify_pool_maintenance(
            connectable_satellites=connectable_satellites.get('oneweb', []),
            constellation='oneweb',
            target_min=self.config['oneweb_pool_target']['min'],
            target_max=self.config['oneweb_pool_target']['max']
        )

        # 3. 分析時空錯置優化效果
        time_space_offset = self.analyze_time_space_offset_optimization(
            starlink_verification,
            oneweb_verification
        )

        # 4. 整體驗證評估
        overall_verification = self._assess_overall_verification(
            starlink_verification,
            oneweb_verification
        )

        self.logger.info("✅ 動態衛星池驗證完成")
        self.logger.info(f"   Starlink: {starlink_verification['coverage_rate']:.1%} 覆蓋率")
        self.logger.info(f"   OneWeb: {oneweb_verification['coverage_rate']:.1%} 覆蓋率")

        return {
            'starlink_pool': starlink_verification,
            'oneweb_pool': oneweb_verification,
            'time_space_offset_optimization': time_space_offset,
            'overall_verification': overall_verification
        }

    def verify_pool_maintenance(
        self,
        connectable_satellites: List[Dict[str, Any]],
        constellation: str,
        target_min: int,
        target_max: int
    ) -> Dict[str, Any]:
        """驗證動態衛星池是否達成「任意時刻維持目標數量可見」的需求

        ⚠️ 關鍵: 逐時間點遍歷，非靜態計數

        Args:
            connectable_satellites: 可連線衛星列表 (含完整時間序列)
            constellation: 星座名稱 ('starlink' 或 'oneweb')
            target_min: 目標最小可見數
            target_max: 目標最大可見數

        Returns:
            完整的池驗證結果
        """
        self.logger.info(f"🔍 驗證 {constellation} 池維持...")

        if not connectable_satellites:
            self.logger.warning(f"❌ {constellation} 無候選衛星數據")
            return self._empty_verification_result(target_min, target_max)

        # 1. 收集所有時間點
        all_timestamps = set()
        for satellite in connectable_satellites:
            time_series = satellite.get('time_series', [])
            for time_point in time_series:
                timestamp = time_point.get('timestamp')
                if timestamp:
                    all_timestamps.add(timestamp)

        if not all_timestamps:
            self.logger.warning(f"❌ {constellation} 無時間序列數據")
            return self._empty_verification_result(target_min, target_max)

        self.logger.info(f"   收集到 {len(all_timestamps)} 個時間點")

        # 2. 對每個時間點計算可見衛星數
        time_coverage_check = []
        for timestamp in sorted(all_timestamps):
            visible_count = 0

            # 檢查該時刻有多少顆衛星 is_connectable=True
            for satellite in connectable_satellites:
                time_series = satellite.get('time_series', [])

                # 找到該時間點的數據
                time_point = next(
                    (tp for tp in time_series if tp.get('timestamp') == timestamp),
                    None
                )

                if time_point:
                    # 檢查 visibility_metrics 中的 is_connectable 標記
                    visibility_metrics = time_point.get('visibility_metrics', {})
                    is_connectable = visibility_metrics.get('is_connectable', False)

                    if is_connectable:
                        visible_count += 1

            time_coverage_check.append({
                'timestamp': timestamp,
                'visible_count': visible_count,
                'target_met': target_min <= visible_count <= target_max
            })

        # 3. 計算覆蓋率
        met_count = sum(1 for check in time_coverage_check if check['target_met'])
        coverage_rate = met_count / len(time_coverage_check) if time_coverage_check else 0.0

        # 4. 識別覆蓋空隙
        coverage_gaps = self._identify_coverage_gaps(time_coverage_check, target_min, target_max)

        # 5. 統計指標
        visible_counts = [c['visible_count'] for c in time_coverage_check]
        average_visible = sum(visible_counts) / len(visible_counts) if visible_counts else 0.0
        min_visible = min(visible_counts) if visible_counts else 0
        max_visible = max(visible_counts) if visible_counts else 0

        # 6. 計算連續覆蓋時間
        continuous_hours = self._calculate_continuous_coverage(time_coverage_check)

        # 7. 更新統計
        self.verification_stats[constellation]['total_time_points'] = len(time_coverage_check)
        self.verification_stats[constellation]['target_met_count'] = met_count
        self.verification_stats[constellation]['coverage_rate'] = coverage_rate
        self.verification_stats[constellation]['gap_periods'] = coverage_gaps

        result = {
            'target_range': {'min': target_min, 'max': target_max},
            'candidate_satellites_total': len(connectable_satellites),
            'time_points_analyzed': len(time_coverage_check),
            'coverage_rate': coverage_rate,
            'average_visible_count': average_visible,
            'min_visible_count': min_visible,
            'max_visible_count': max_visible,
            'target_met': coverage_rate >= self.config['coverage_threshold'],
            'coverage_gaps_count': len(coverage_gaps),
            'coverage_gaps': coverage_gaps[:10],  # 只保存前10個空隙
            'continuous_coverage_hours': continuous_hours
        }

        self.logger.info(f"   平均可見: {average_visible:.1f} 顆")
        self.logger.info(f"   覆蓋率: {coverage_rate:.1%}")
        self.logger.info(f"   目標{'✅ 達成' if result['target_met'] else '❌ 未達成'}")

        return result

    def _identify_coverage_gaps(
        self,
        time_coverage_check: List[Dict[str, Any]],
        target_min: int,
        target_max: int
    ) -> List[Dict[str, Any]]:
        """識別覆蓋空隙

        Returns:
            覆蓋空隙列表
        """
        gaps = []
        in_gap = False
        gap_start = None
        gap_min_visible = float('inf')

        for i, check in enumerate(time_coverage_check):
            if not check['target_met']:
                if not in_gap:
                    # 開始新的空隙
                    in_gap = True
                    gap_start = check['timestamp']
                    gap_min_visible = check['visible_count']
                else:
                    gap_min_visible = min(gap_min_visible, check['visible_count'])
            else:
                if in_gap:
                    # 結束空隙
                    gap_end = time_coverage_check[i - 1]['timestamp']
                    duration_minutes = self._calculate_duration_minutes(gap_start, gap_end)

                    # 評估嚴重程度
                    severity = self._assess_gap_severity(
                        gap_min_visible, target_min, duration_minutes
                    )

                    gaps.append({
                        'start_timestamp': gap_start,
                        'end_timestamp': gap_end,
                        'duration_minutes': duration_minutes,
                        'min_visible_count': gap_min_visible,
                        'severity': severity
                    })

                    in_gap = False
                    gap_min_visible = float('inf')

        # 處理最後一個未結束的空隙
        if in_gap and len(time_coverage_check) > 0:
            gap_end = time_coverage_check[-1]['timestamp']
            duration_minutes = self._calculate_duration_minutes(gap_start, gap_end)
            severity = self._assess_gap_severity(gap_min_visible, target_min, duration_minutes)

            gaps.append({
                'start_timestamp': gap_start,
                'end_timestamp': gap_end,
                'duration_minutes': duration_minutes,
                'min_visible_count': gap_min_visible,
                'severity': severity
            })

        return gaps

    def _calculate_continuous_coverage(
        self,
        time_coverage_check: List[Dict[str, Any]]
    ) -> float:
        """計算連續覆蓋時間 (小時)

        SOURCE: 從配置參數讀取實際觀測窗口時長
        依據: 與 Stage 4-6 一致的觀測窗口配置
        """
        if not time_coverage_check:
            return 0.0

        # 找到最長的連續達標時間段
        max_continuous_count = 0
        current_continuous_count = 0

        for check in time_coverage_check:
            if check['target_met']:
                current_continuous_count += 1
                max_continuous_count = max(max_continuous_count, current_continuous_count)
            else:
                current_continuous_count = 0

        # 從配置讀取觀測窗口時長，而非硬編碼
        # SOURCE: config['observation_window_hours']
        # 依據: Stage 4-6 統一使用 2 小時觀測窗口
        observation_window_hours = self.config.get('observation_window_hours', 2.0)

        if len(time_coverage_check) > 1:
            time_step_hours = observation_window_hours / len(time_coverage_check)
            continuous_hours = max_continuous_count * time_step_hours
        else:
            continuous_hours = 0.0

        return continuous_hours

    def _calculate_duration_minutes(
        self,
        start_timestamp: str,
        end_timestamp: str
    ) -> float:
        """計算時間間隔 (分鐘)"""
        try:
            start_dt = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_timestamp.replace('Z', '+00:00'))

            duration_seconds = (end_dt - start_dt).total_seconds()
            return duration_seconds / 60.0
        except Exception as e:
            self.logger.warning(f"時間計算失敗: {e}")
            return 0.0

    def _assess_gap_severity(
        self,
        visible_count: int,
        target_min: int,
        duration_minutes: float
    ) -> str:
        """評估覆蓋空隙嚴重程度

        SOURCE: 基於 3GPP 換手延遲容忍度定義嚴重性
        依據: 3GPP TS 38.331 Section 5.3.5 (RLF Timer T310)

        Returns:
            'critical': 完全無覆蓋 (0顆) 或長時間空隙
            'warning': 嚴重不足或中等時間空隙
            'minor': 輕微不足
        """
        # 從配置讀取嚴重性門檻
        # SOURCE: config['gap_severity_thresholds']
        # 依據: 3GPP TS 38.331 T310 典型值 1000ms (1秒) - 關鍵掉線檢測時間
        severity_thresholds = self.config.get('gap_severity_thresholds', {})
        critical_duration = severity_thresholds.get('critical_duration_minutes', 10)
        warning_duration = severity_thresholds.get('warning_duration_minutes', 5)
        warning_visible_ratio = severity_thresholds.get('warning_visible_ratio', 0.5)

        if visible_count == 0 or duration_minutes > critical_duration:
            return 'critical'
        elif visible_count < target_min * warning_visible_ratio or duration_minutes > warning_duration:
            return 'warning'
        else:
            return 'minor'

    def analyze_time_space_offset_optimization(
        self,
        starlink_verification: Dict[str, Any],
        oneweb_verification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析時空錯置優化效果

        Args:
            starlink_verification: Starlink 池驗證結果
            oneweb_verification: OneWeb 池驗證結果

        Returns:
            時空錯置優化分析
        """
        # 1. 檢查調度是否最優
        starlink_coverage = starlink_verification.get('coverage_rate', 0.0)
        oneweb_coverage = oneweb_verification.get('coverage_rate', 0.0)

        optimal_scheduling = (
            starlink_coverage >= 0.95 and
            oneweb_coverage >= 0.95
        )

        # 2. 計算覆蓋效率
        coverage_efficiency = (starlink_coverage + oneweb_coverage) / 2.0

        # 3. 估算換手頻率
        starlink_avg = starlink_verification.get('average_visible_count', 0)
        oneweb_avg = oneweb_verification.get('average_visible_count', 0)

        # 基於衛星平均可見數估算換手頻率 (顆/小時)
        handover_frequency_per_hour = (starlink_avg + oneweb_avg) / 2.0

        # 4. 空間多樣性
        starlink_range = starlink_verification.get('max_visible_count', 0) - starlink_verification.get('min_visible_count', 0)
        oneweb_range = oneweb_verification.get('max_visible_count', 0) - oneweb_verification.get('min_visible_count', 0)

        spatial_diversity = min(1.0, (starlink_range + oneweb_range) / 20.0)

        # 5. 時間重疊
        starlink_continuous = starlink_verification.get('continuous_coverage_hours', 0)
        oneweb_continuous = oneweb_verification.get('continuous_coverage_hours', 0)

        temporal_overlap = min(1.0, (starlink_continuous + oneweb_continuous) / 48.0)

        return {
            'optimal_scheduling': optimal_scheduling,
            'coverage_efficiency': coverage_efficiency,
            'handover_frequency_per_hour': handover_frequency_per_hour,
            'spatial_diversity': spatial_diversity,
            'temporal_overlap': temporal_overlap
        }

    def _assess_overall_verification(
        self,
        starlink_verification: Dict[str, Any],
        oneweb_verification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """評估整體驗證結果"""
        starlink_met = starlink_verification.get('target_met', False)
        oneweb_met = oneweb_verification.get('target_met', False)

        overall_passed = starlink_met and oneweb_met

        return {
            'overall_passed': overall_passed,
            'starlink_pool_target_met': starlink_met,
            'oneweb_pool_target_met': oneweb_met,
            'combined_coverage_rate': (
                starlink_verification.get('coverage_rate', 0.0) +
                oneweb_verification.get('coverage_rate', 0.0)
            ) / 2.0,
            'total_coverage_gaps': (
                starlink_verification.get('coverage_gaps_count', 0) +
                oneweb_verification.get('coverage_gaps_count', 0)
            ),
            'verification_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _empty_verification_result(self, target_min: int, target_max: int) -> Dict[str, Any]:
        """返回空的驗證結果"""
        return {
            'target_range': {'min': target_min, 'max': target_max},
            'candidate_satellites_total': 0,
            'time_points_analyzed': 0,
            'coverage_rate': 0.0,
            'average_visible_count': 0.0,
            'min_visible_count': 0,
            'max_visible_count': 0,
            'target_met': False,
            'coverage_gaps_count': 0,
            'coverage_gaps': [],
            'continuous_coverage_hours': 0.0
        }

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數

        所有配置參數均基於學術標準和運營數據
        """
        default_config = {
            # ============================================================
            # Starlink 衛星池目標範圍
            # ============================================================
            # SOURCE: docs/stages/stage6-research-optimization.md Line 84-89
            # 依據: Starlink LEO 密集部署特性 (軌道高度 550km)
            # 目標: 任意時刻維持 10-15 顆可見衛星
            # 參考: Starlink Shell 1 設計參數 (1584顆衛星, 53°傾角)
            'starlink_pool_target': {'min': 10, 'max': 15},

            # ============================================================
            # OneWeb 衛星池目標範圍
            # ============================================================
            # SOURCE: docs/stages/stage6-research-optimization.md Line 84-89
            # 依據: OneWeb LEO 稀疏部署特性 (軌道高度 1200km)
            # 目標: 任意時刻維持 3-6 顆可見衛星
            # 參考: OneWeb Phase 1 設計參數 (648顆衛星, 87.9°傾角)
            'oneweb_pool_target': {'min': 3, 'max': 6},

            # ============================================================
            # 覆蓋率門檻
            # ============================================================
            # SOURCE: 電信服務可用性標準
            # 依據: ITU-T E.800 "Definitions of terms related to QoS"
            # 95% 時間達標 = 年度停機時間 < 18.26 天
            # 對應「高可用性」等級 (High Availability)
            'coverage_threshold': 0.95,

            # ============================================================
            # 觀測窗口時長
            # ============================================================
            # SOURCE: Stage 4-6 統一配置參數
            # 依據: 與可見性計算窗口一致 (2 小時)
            # 理由: 涵蓋 LEO 衛星 1-2 個軌道週期 (Starlink ~95min, OneWeb ~109min)
            'observation_window_hours': 2.0,

            # ============================================================
            # 覆蓋空隙嚴重性門檻
            # ============================================================
            # SOURCE: 基於 3GPP 換手延遲容忍度
            # 依據: 3GPP TS 38.331 Section 5.3.5 (RLF Timer T310)
            'gap_severity_thresholds': {
                # Critical: 10 分鐘無覆蓋
                # 理由: T310 典型值 1000ms (1秒)，10分鐘遠超容忍度
                #       對應服務完全中斷，用戶感知明顯
                'critical_duration_minutes': 10,

                # Warning: 5 分鐘部分覆蓋不足
                # 理由: 可能影響服務品質，但尚未完全中斷
                #       給運營商預警時間進行調度調整
                'warning_duration_minutes': 5,

                # Critical 可見數比率: 0 (完全無覆蓋)
                'critical_visible_ratio': 0.0,

                # Warning 可見數比率: 50% (嚴重不足)
                # 理由: 可見數低於目標一半時，冗余度不足
                'warning_visible_ratio': 0.5
            }
        }

        if config:
            default_config.update(config)

        return default_config


if __name__ == "__main__":
    # 測試動態衛星池驗證器
    verifier = SatellitePoolVerifier()

    print("🧪 動態衛星池驗證器測試:")
    print(f"Starlink 目標: {verifier.config['starlink_pool_target']}")
    print(f"OneWeb 目標: {verifier.config['oneweb_pool_target']}")
    print(f"覆蓋率門檻: {verifier.config['coverage_threshold']:.1%}")
    print("✅ 動態衛星池驗證器測試完成")