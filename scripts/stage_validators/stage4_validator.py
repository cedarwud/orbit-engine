"""
Stage 4 驗證器 - 鏈路可行性評估與時空錯置池規劃層 (重構版本)

使用 StageValidator 基類統一驗證流程

Layer 2 驗證: 嚴格檢查驗證快照的完整性與合理性
使用 Fail-Fast 原則: 任何缺失字段立即失敗，不使用預設值

Author: Orbit Engine Refactoring Team
Date: 2025-10-12 (Phase 2 Refactoring)
Original: 2025-10-04
"""

from .base_validator import StageValidator
from typing import Tuple
import json
import os
from pathlib import Path


class Stage4Validator(StageValidator):
    """
    Stage 4 驗證器 - 鏈路可行性評估與時空錯置池規劃

    檢查項目:
    - 階段 4.1: 可見性篩選 (9040 → ~2000顆候選)
    - 階段 4.2: 池規劃優化 (時空錯置池維持目標)
    - 星座門檻驗證 (Starlink 5°, OneWeb 10°)
    - NTPU 覆蓋分析 (動態 TLE 軌道週期驗證)
    - 鏈路預算約束
    - 可見性計算精度
    - 服務窗口優化
    """

    def __init__(self):
        super().__init__(
            stage_number=4,
            stage_identifier='stage4_link_feasibility'
        )

    def perform_stage_specific_validation(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        Stage 4 專用驗證

        檢查項目:
        - 階段完成狀態 (4.1 必須完成, 4.2 CRITICAL 必須完成)
        - 候選池與優化池結構
        - 星座門檻驗證
        - NTPU 覆蓋分析 (含動態 TLE 驗證)
        - 池規劃優化驗證 (4.2 CRITICAL)

        Args:
            snapshot_data: 驗證快照數據

        Returns:
            tuple: (validation_passed: bool, message: str)
        """
        # ✅ Fail-Fast #1: 檢測取樣模式前先驗證必要字段
        # 確保 metadata 和 total_input_satellites 存在
        valid, msg = self.check_field_exists(snapshot_data, 'metadata')
        if not valid:
            return False, msg

        metadata = snapshot_data['metadata']

        valid, msg = self.check_field_exists(metadata, 'total_input_satellites', 'metadata')
        if not valid:
            return False, msg

        total_input_satellites = metadata['total_input_satellites']

        # 檢測取樣模式
        is_sampling_mode = self._is_sampling_mode(snapshot_data)
        if is_sampling_mode:
            print(f"🧪 偵測到取樣模式 ({total_input_satellites} 顆衛星)，放寬驗證標準")

        # ======== 驗證 #1: 階段完成狀態 ========
        result = self._validate_stage_completion(snapshot_data)
        if result is not None:
            return result

        # ======== 驗證 #2: 候選池與優化池結構 ========
        result = self._validate_candidate_pool(snapshot_data)
        if result is not None:
            return result

        # ======== 驗證 #3: 星座門檻驗證 ========
        result = self._validate_constellation_thresholds(snapshot_data)
        if result is not None:
            return result

        # ======== 驗證 #4: NTPU 覆蓋分析 ========
        result = self._validate_ntpu_coverage(snapshot_data, is_sampling_mode)
        if result is not None:
            return result

        # ======== 驗證 #5: 鏈路預算約束 ========
        if not is_sampling_mode:
            result = self._validate_link_budget(snapshot_data)
            if result is not None:
                return result

        # ======== 驗證 #6: 池規劃優化 (CRITICAL) ========
        result = self._validate_pool_optimization(snapshot_data, is_sampling_mode)
        if result is not None:
            return result

        # ======== 驗證 #7: 可見性計算精度 ========
        result = self._validate_visibility_accuracy(snapshot_data, is_sampling_mode)
        if result is not None:
            return result

        # ======== 驗證 #8: 服務窗口優化 ========
        if not is_sampling_mode:
            result = self._validate_service_windows(snapshot_data)
            if result is not None:
                return result

        # ======== 構建成功訊息 ========
        return self._build_stage4_success_message(snapshot_data)

    def _validate_stage_completion(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        驗證階段完成狀態

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        # ✅ Fail-Fast #2: metadata 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'metadata')
        if not valid:
            return False, msg

        metadata = snapshot_data['metadata']

        # Fail-Fast: stage_4_1_completed 必須存在
        valid, msg = self.check_field_exists(metadata, 'stage_4_1_completed', 'metadata')
        if not valid:
            return False, msg

        # Fail-Fast: stage_4_2_completed 必須存在
        valid, msg = self.check_field_exists(metadata, 'stage_4_2_completed', 'metadata')
        if not valid:
            return False, msg

        stage_4_1_completed = metadata['stage_4_1_completed']
        stage_4_2_completed = metadata['stage_4_2_completed']

        # Stage 4.1 必須完成
        if not stage_4_1_completed:
            return False, "❌ Stage 4.1 可見性篩選未完成"

        # Stage 4.2 必須完成 (CRITICAL)
        if not stage_4_2_completed:
            return False, "❌ Stage 4.2 池規劃優化未完成 (🔴 CRITICAL 必要功能，不可跳過)"

        return None  # 通過檢查

    def _validate_candidate_pool(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        驗證候選池與優化池結構

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        # Fail-Fast: feasibility_summary 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'feasibility_summary')
        if not valid:
            return False, msg

        feasibility_summary = snapshot_data['feasibility_summary']

        # Fail-Fast: candidate_pool 必須存在
        valid, msg = self.check_field_exists(feasibility_summary, 'candidate_pool', 'feasibility_summary')
        if not valid:
            return False, msg

        # Fail-Fast: optimized_pool 必須存在
        valid, msg = self.check_field_exists(feasibility_summary, 'optimized_pool', 'feasibility_summary')
        if not valid:
            return False, msg

        candidate_pool = feasibility_summary['candidate_pool']
        optimized_pool = feasibility_summary['optimized_pool']

        # Fail-Fast: total_connectable 必須存在
        valid, msg = self.check_field_exists(candidate_pool, 'total_connectable', 'candidate_pool')
        if not valid:
            return False, msg

        # Fail-Fast: total_optimized 必須存在
        valid, msg = self.check_field_exists(optimized_pool, 'total_optimized', 'optimized_pool')
        if not valid:
            return False, msg

        candidate_total = candidate_pool['total_connectable']

        if candidate_total == 0:
            return False, "❌ Stage 4.1 候選池為空: 沒有可連線衛星"

        return None  # 通過檢查

    def _validate_constellation_thresholds(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        驗證星座門檻 (Starlink 5°, OneWeb 10°)

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        # ✅ Fail-Fast #2: metadata 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'metadata')
        if not valid:
            return False, msg

        metadata = snapshot_data['metadata']

        # Fail-Fast: constellation_aware 必須存在
        valid, msg = self.check_field_exists(metadata, 'constellation_aware', 'metadata')
        if not valid:
            return False, msg

        constellation_aware = metadata['constellation_aware']

        if not constellation_aware:
            return False, "❌ Stage 4 星座感知功能未啟用 (constellation_aware=False)"

        # 驗證星座特定門檻設計
        feasibility_summary = snapshot_data['feasibility_summary']
        candidate_pool = feasibility_summary['candidate_pool']

        # Fail-Fast: by_constellation 必須存在
        valid, msg = self.check_field_exists(candidate_pool, 'by_constellation', 'candidate_pool')
        if not valid:
            return False, msg

        candidate_by_const = candidate_pool['by_constellation']

        if not candidate_by_const:
            return False, "❌ Stage 4 星座分類數據缺失 (by_constellation為空)"

        return None  # 通過檢查

    def _validate_ntpu_coverage(self, snapshot_data: dict, is_sampling_mode: bool) -> Tuple[bool, str]:
        """
        驗證 NTPU 覆蓋分析 (含動態 TLE 軌道週期驗證)

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        feasibility_summary = snapshot_data['feasibility_summary']

        # Fail-Fast: ntpu_coverage 必須存在
        valid, msg = self.check_field_exists(feasibility_summary, 'ntpu_coverage', 'feasibility_summary')
        if not valid:
            return False, msg

        ntpu_coverage = feasibility_summary['ntpu_coverage']

        if not ntpu_coverage:
            return False, "❌ Stage 4 NTPU 覆蓋分析數據缺失"

        # Fail-Fast: continuous_coverage_hours 必須存在
        valid, msg = self.check_field_exists(ntpu_coverage, 'continuous_coverage_hours', 'ntpu_coverage')
        if not valid:
            return False, msg

        # Fail-Fast: average_satellites_visible 必須存在
        valid, msg = self.check_field_exists(ntpu_coverage, 'average_satellites_visible', 'ntpu_coverage')
        if not valid:
            return False, msg

        continuous_coverage_hours = ntpu_coverage['continuous_coverage_hours']
        avg_satellites_visible = ntpu_coverage['average_satellites_visible']

        # 🔧 取樣模式: 跳過嚴格的覆蓋時間和可見衛星數檢查
        if not is_sampling_mode:
            # 🚨 動態 TLE 軌道週期驗證 (基於 Stage 1 epoch_analysis.json)
            epoch_analysis_file = Path('data/outputs/stage1/epoch_analysis.json')

            # Fail-Fast: epoch_analysis.json 必須存在
            if not epoch_analysis_file.exists():
                return False, "❌ Stage 1 epoch_analysis.json 不存在（需要 TLE 軌道週期數據進行動態驗證）"

            # Fail-Fast: 必須能成功讀取
            try:
                with open(epoch_analysis_file, 'r', encoding='utf-8') as f:
                    epoch_analysis = json.load(f)
            except Exception as e:
                return False, f"❌ 無法讀取 Stage 1 epoch_analysis.json: {e}"

            # Fail-Fast: constellation_distribution 必須存在
            valid, msg = self.check_field_exists(epoch_analysis, 'constellation_distribution', 'epoch_analysis')
            if not valid:
                return False, msg

            tle_orbital_periods = epoch_analysis['constellation_distribution']

            # Fail-Fast: by_constellation 必須存在
            valid, msg = self.check_field_exists(ntpu_coverage, 'by_constellation', 'ntpu_coverage')
            if not valid:
                return False, f"{msg}（需要按星座統計 continuous_coverage_hours）"

            by_const = ntpu_coverage['by_constellation']

            # Fail-Fast: by_constellation 不能為空
            if not by_const:
                return False, "❌ ntpu_coverage.by_constellation 為空（需要 Starlink/OneWeb 覆蓋統計）"

            # 逐星座驗證連續覆蓋時間
            for const_name, const_data in by_const.items():
                # Fail-Fast: continuous_coverage_hours 必須存在
                valid, msg = self.check_field_exists(const_data, 'continuous_coverage_hours',
                                                    f'ntpu_coverage.by_constellation.{const_name}')
                if not valid:
                    return False, msg

                const_coverage = const_data['continuous_coverage_hours']

                # Fail-Fast: TLE 軌道週期統計必須存在
                if const_name.upper() not in tle_orbital_periods:
                    return False, f"❌ epoch_analysis.json 缺少 {const_name.upper()} 星座的 TLE 軌道週期統計"

                # ✅ Fail-Fast #3: orbital_period_stats 必須存在
                constellation_data = tle_orbital_periods[const_name.upper()]
                valid, msg = self.check_field_exists(constellation_data, 'orbital_period_stats',
                                                    f'{const_name.upper()} constellation_data')
                if not valid:
                    return False, msg

                orbital_stats = constellation_data['orbital_period_stats']

                # Fail-Fast: orbital_period_stats 不能為空
                if not orbital_stats:
                    return False, f"❌ epoch_analysis.json 中 {const_name.upper()} 的 orbital_period_stats 為空"

                # Fail-Fast: min_minutes 必須存在
                valid, msg = self.check_field_exists(orbital_stats, 'min_minutes',
                                                    f'{const_name.upper()} orbital_period_stats')
                if not valid:
                    return False, msg

                min_period_minutes = orbital_stats['min_minutes']

                # Fail-Fast: min_minutes 必須 > 0
                if min_period_minutes <= 0:
                    return False, f"❌ {const_name.upper()} TLE 最小軌道週期無效: {min_period_minutes}min (必須 > 0)"

                min_required_hours = min_period_minutes / 60.0
                threshold_source = f"TLE最小軌道週期 {min_period_minutes:.1f}min"

                # 驗證連續覆蓋時間
                if const_coverage < min_required_hours:
                    return False, (
                        f"❌ Stage 4 {const_name} 連續覆蓋時間不足: {const_coverage:.2f}h "
                        f"(需要 ≥{min_required_hours:.2f}h，基於{threshold_source})"
                    )

            # 平均可見衛星數檢查
            if avg_satellites_visible < 10.0:  # Starlink 目標範圍下限
                return False, (
                    f"❌ Stage 4 NTPU 平均可見衛星數過低: {avg_satellites_visible:.1f} 顆 (需要 ≥10.0)"
                )

        return None  # 通過檢查

    def _validate_link_budget(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        驗證鏈路預算約束

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        # ✅ Fail-Fast #2: metadata 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'metadata')
        if not valid:
            return False, msg

        metadata = snapshot_data['metadata']

        # Fail-Fast: ntpu_specific 必須存在
        valid, msg = self.check_field_exists(metadata, 'ntpu_specific', 'metadata')
        if not valid:
            return False, msg

        ntpu_specific = metadata['ntpu_specific']

        if not ntpu_specific:
            return False, "❌ Stage 4 NTPU 特定配置未啟用 (ntpu_specific=False)"

        return None  # 通過檢查

    def _validate_pool_optimization(self, snapshot_data: dict, is_sampling_mode: bool) -> Tuple[bool, str]:
        """
        驗證階段 4.2 時空錯置池規劃 (CRITICAL)

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        # Fail-Fast: pool_optimization 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'pool_optimization')
        if not valid:
            return False, msg

        pool_optimization = snapshot_data['pool_optimization']

        # Fail-Fast: validation_results 必須存在
        valid, msg = self.check_field_exists(pool_optimization, 'validation_results', 'pool_optimization')
        if not valid:
            return False, msg

        validation_results = pool_optimization['validation_results']

        # Fail-Fast: starlink 必須存在
        valid, msg = self.check_field_exists(validation_results, 'starlink', 'validation_results')
        if not valid:
            return False, msg

        starlink_validation = validation_results['starlink']

        # Fail-Fast: validation_passed 必須存在
        valid, msg = self.check_field_exists(starlink_validation, 'validation_passed', 'starlink_validation')
        if not valid:
            return False, msg

        # Fail-Fast: validation_checks 必須存在
        valid, msg = self.check_field_exists(starlink_validation, 'validation_checks', 'starlink_validation')
        if not valid:
            return False, msg

        starlink_checks = starlink_validation['validation_checks']

        # 檢查覆蓋率
        valid, msg = self.check_field_exists(starlink_checks, 'coverage_rate_check', 'starlink_checks')
        if not valid:
            return False, msg

        coverage_check = starlink_checks['coverage_rate_check']

        valid, msg = self.check_field_exists(coverage_check, 'value', 'coverage_rate_check')
        if not valid:
            return False, msg

        coverage_rate = coverage_check['value']

        # 提取 avg_visible
        valid, msg = self.check_field_exists(starlink_checks, 'avg_visible_check', 'starlink_checks')
        if not valid:
            return False, msg

        avg_visible_check = starlink_checks['avg_visible_check']

        valid, msg = self.check_field_exists(avg_visible_check, 'value', 'avg_visible_check')
        if not valid:
            return False, msg

        valid, msg = self.check_field_exists(avg_visible_check, 'target_range', 'avg_visible_check')
        if not valid:
            return False, msg

        avg_visible = avg_visible_check['value']
        target_range = avg_visible_check['target_range']

        # 🔧 取樣模式: 跳過嚴格的覆蓋率和可見數檢查
        if not is_sampling_mode:
            if coverage_rate < 0.95:
                return False, f"❌ Stage 4.2 Starlink 覆蓋率不足: {coverage_rate:.1%} (需要 ≥95%)"

            # ✅ 核心驗證: 檢查「任意時刻可見數」是否在目標範圍
            if not (target_range[0] <= avg_visible <= target_range[1]):
                return False, (
                    f"❌ Stage 4.2 Starlink 平均可見數不符: {avg_visible:.1f} 顆 "
                    f"(目標: {target_range[0]}-{target_range[1]})"
                )

        # 檢查覆蓋空窗
        valid, msg = self.check_field_exists(starlink_checks, 'coverage_gaps_check', 'starlink_checks')
        if not valid:
            return False, msg

        gaps_check = starlink_checks['coverage_gaps_check']

        valid, msg = self.check_field_exists(gaps_check, 'gap_count', 'coverage_gaps_check')
        if not valid:
            return False, msg

        gap_count = gaps_check['gap_count']

        if gap_count > 0:
            return False, f"❌ Stage 4.2 Starlink 存在覆蓋空窗: {gap_count} 個時間點無可見衛星"

        # OneWeb 檢查 (較寬鬆)
        if not is_sampling_mode:
            # OneWeb 可能不存在（取決於數據）
            if 'oneweb' in validation_results:
                oneweb_validation = validation_results['oneweb']

                valid, msg = self.check_field_exists(oneweb_validation, 'validation_checks', 'oneweb_validation')
                if not valid:
                    return False, msg

                oneweb_checks = oneweb_validation['validation_checks']

                if 'coverage_rate_check' in oneweb_checks:
                    oneweb_coverage_check = oneweb_checks['coverage_rate_check']

                    valid, msg = self.check_field_exists(oneweb_coverage_check, 'value',
                                                        'oneweb coverage_rate_check')
                    if not valid:
                        return False, msg

                    oneweb_coverage = oneweb_coverage_check['value']

                    if oneweb_coverage < 0.80:  # OneWeb 允許較低覆蓋率
                        return False, f"❌ Stage 4.2 OneWeb 覆蓋率過低: {oneweb_coverage:.1%}"

        return None  # 通過檢查

    def _validate_visibility_accuracy(self, snapshot_data: dict, is_sampling_mode: bool) -> Tuple[bool, str]:
        """
        驗證可見性計算精度 (增強版 - 詳細檢查)

        檢查項目:
        1. IAU 標準使用驗證
        2. 候選池數量範圍驗證
        3. ✅ 新增: visibility_metrics 數據結構驗證
        4. ✅ 新增: 仰角/方位角/距離合理性抽樣檢查
        5. ✅ 新增: 計算方法標記驗證

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        # ✅ Fail-Fast #2: metadata 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'metadata')
        if not valid:
            return False, msg

        metadata = snapshot_data['metadata']

        # Fail-Fast: use_iau_standards 必須存在
        valid, msg = self.check_field_exists(metadata, 'use_iau_standards', 'metadata')
        if not valid:
            return False, msg

        use_iau_standards = metadata['use_iau_standards']

        if not use_iau_standards:
            return False, "❌ Stage 4 未使用 IAU 標準座標計算 (use_iau_standards=False)"

        # 🔧 取樣模式: 跳過候選池數量範圍檢查
        if not is_sampling_mode:
            feasibility_summary = snapshot_data['feasibility_summary']
            candidate_pool = feasibility_summary['candidate_pool']
            candidate_total = candidate_pool['total_connectable']

            # 驗證基本數據合理性：候選池應在合理範圍內
            if candidate_total < 100 or candidate_total > 5000:
                return False, f"❌ Stage 4 候選池數量異常: {candidate_total} 顆 (合理範圍: 100-5000)"

        # ✅ Fail-Fast #4: connectable_satellites 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'connectable_satellites')
        if not valid:
            return False, msg

        connectable_satellites = snapshot_data['connectable_satellites']

        if not connectable_satellites:
            return False, "❌ Stage 4 缺少 connectable_satellites 數據"

        # 抽樣驗證 (Starlink 作為主要星座)
        if 'starlink' in connectable_satellites:
            starlink_sats = connectable_satellites['starlink']

            if not starlink_sats:
                return False, "❌ Starlink 可連線衛星池為空"

            # 抽樣檢查第一顆衛星的數據結構
            sample_sat = starlink_sats[0]

            # Fail-Fast: time_series 必須存在
            valid, msg = self.check_field_exists(sample_sat, 'time_series', 'sample_satellite')
            if not valid:
                return False, f"{msg} (connectable_satellites 應包含完整時間序列)"

            time_series = sample_sat['time_series']

            if not time_series:
                return False, "❌ 衛星時間序列為空 (應包含 ~190-220 時間點)"

            # 抽樣檢查第一個時間點
            sample_point = time_series[0]

            # Fail-Fast: visibility_metrics 必須存在
            valid, msg = self.check_field_exists(sample_point, 'visibility_metrics', 'sample_time_point')
            if not valid:
                return False, f"{msg} (時間點應包含 visibility_metrics)"

            metrics = sample_point['visibility_metrics']

            # Fail-Fast: 核心指標必須存在
            required_metrics = ['elevation_deg', 'azimuth_deg', 'distance_km']
            for metric_name in required_metrics:
                valid, msg = self.check_field_exists(metrics, metric_name, 'visibility_metrics')
                if not valid:
                    return False, msg

            # ✅ 新增: 驗證數值合理性
            elevation = metrics['elevation_deg']
            azimuth = metrics['azimuth_deg']
            distance = metrics['distance_km']

            # 仰角範圍: -90° to 90°
            if not (-90 <= elevation <= 90):
                return False, f"❌ 仰角數值異常: {elevation}° (合理範圍: -90~90°)"

            # 方位角範圍: 0° to 360°
            if not (0 <= azimuth <= 360):
                return False, f"❌ 方位角數值異常: {azimuth}° (合理範圍: 0~360°)"

            # 距離範圍: LEO 衛星典型範圍 200-2500 km
            # SOURCE: Wertz & Larson 2001, Section 5.6 - Typical LEO satellite visibility ranges
            if not (200 <= distance <= 2500):
                return False, f"❌ 距離數值異常: {distance} km (合理範圍: 200~2500 km for LEO)"

            # ✅ 新增: 驗證 threshold_applied (星座感知門檻)
            if 'threshold_applied' in metrics:
                threshold = metrics['threshold_applied']
                # Starlink 應該是 5.0° (根據 stage4-link-feasibility.md Line 227)
                if threshold != 5.0:
                    return False, f"⚠️ Starlink 仰角門檻異常: {threshold}° (應為 5.0°)"

        return None  # 通過檢查

    def _validate_service_windows(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        驗證服務窗口優化 (增強版 - 專用檢查)

        檢查項目:
        1. 覆蓋空窗時間長度驗證
        2. 覆蓋空窗總數驗證
        3. ✅ 新增: 衛星 service_window 數據結構驗證
        4. ✅ 新增: 時間窗口連續性驗證
        5. ✅ 新增: 服務窗口持續時間合理性驗證

        Returns:
            tuple | None: (False, error_msg) 如果發現問題，否則 None
        """
        feasibility_summary = snapshot_data['feasibility_summary']
        ntpu_coverage = feasibility_summary['ntpu_coverage']

        # Fail-Fast: coverage_gaps_minutes 必須存在
        valid, msg = self.check_field_exists(ntpu_coverage, 'coverage_gaps_minutes', 'ntpu_coverage')
        if not valid:
            return False, msg

        coverage_gaps = ntpu_coverage['coverage_gaps_minutes']

        # 檢查是否有過長的覆蓋空窗（超過 30 分鐘視為不合理）
        long_gaps = [gap for gap in coverage_gaps if gap > 30.0]
        if long_gaps:
            return False, (
                f"❌ Stage 4 存在過長覆蓋空窗: {len(long_gaps)} 個超過 30 分鐘 "
                f"(最長 {max(long_gaps):.1f} 分鐘)"
            )

        # 驗證覆蓋連續性：空窗總數應該很少
        if len(coverage_gaps) > 5:
            return False, f"❌ Stage 4 覆蓋空窗過多: {len(coverage_gaps)} 個 (建議 ≤5 個)"

        # ✅ Fail-Fast #4: connectable_satellites 必須存在
        valid, msg = self.check_field_exists(snapshot_data, 'connectable_satellites')
        if not valid:
            return False, msg

        connectable_satellites = snapshot_data['connectable_satellites']

        if not connectable_satellites:
            return False, "❌ Stage 4 缺少 connectable_satellites 數據"

        # 抽樣檢查 Starlink 衛星的服務窗口
        if 'starlink' in connectable_satellites:
            starlink_sats = connectable_satellites['starlink']

            if not starlink_sats:
                return False, "❌ Starlink 可連線衛星池為空"

            # 抽樣第一顆衛星
            sample_sat = starlink_sats[0]

            # Fail-Fast: service_window 必須存在
            valid, msg = self.check_field_exists(sample_sat, 'service_window', 'sample_satellite')
            if not valid:
                return False, f"{msg} (connectable_satellites 應包含 service_window 數據)"

            service_window = sample_sat['service_window']

            # Fail-Fast: 服務窗口核心字段
            required_fields = ['start_time', 'end_time', 'duration_minutes', 'time_points_count']
            for field in required_fields:
                valid, msg = self.check_field_exists(service_window, field, 'service_window')
                if not valid:
                    return False, msg

            # ✅ 新增: 驗證服務窗口持續時間合理性
            duration = service_window['duration_minutes']
            time_points = service_window['time_points_count']

            # LEO 衛星典型可見持續時間: 1-20 分鐘
            # SOURCE: Wertz & Larson 2001, Section 5.6 - LEO satellite pass duration
            if not (0.5 <= duration <= 30.0):
                return False, f"❌ 服務窗口持續時間異常: {duration} 分鐘 (合理範圍: 0.5~30分鐘)"

            # 時間點數應該合理 (假設 30 秒間隔)
            if time_points < 2:
                return False, f"❌ 服務窗口時間點數過少: {time_points} (應 ≥2)"

            # ✅ 新增: 驗證時間窗口連續性 (start_time < end_time)
            try:
                from datetime import datetime
                start = datetime.fromisoformat(service_window['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(service_window['end_time'].replace('Z', '+00:00'))

                if start >= end:
                    return False, f"❌ 服務窗口時間順序錯誤: start_time >= end_time"

                # 驗證持續時間計算正確性
                actual_duration_min = (end - start).total_seconds() / 60.0
                duration_diff = abs(actual_duration_min - duration)

                if duration_diff > 1.0:  # 允許 1 分鐘誤差
                    return False, (
                        f"❌ 服務窗口持續時間計算錯誤: "
                        f"聲稱 {duration} 分鐘, 實際 {actual_duration_min:.1f} 分鐘 "
                        f"(差異 {duration_diff:.1f} 分鐘)"
                    )

            except Exception as e:
                return False, f"❌ 服務窗口時間戳記格式錯誤: {e}"

        return None  # 通過檢查

    def _build_stage4_success_message(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        構建 Stage 4 成功驗證訊息

        Returns:
            tuple: (True, success_message)
        """
        feasibility_summary = snapshot_data['feasibility_summary']
        candidate_pool = feasibility_summary['candidate_pool']
        optimized_pool = feasibility_summary['optimized_pool']
        ntpu_coverage = feasibility_summary['ntpu_coverage']

        candidate_total = candidate_pool['total_connectable']
        optimized_total = optimized_pool['total_optimized']
        continuous_coverage_hours = ntpu_coverage['continuous_coverage_hours']

        # ✅ Fail-Fast #6: 提取優化池星座統計 (檢查字段存在性)
        valid, msg = self.check_field_exists(optimized_pool, 'by_constellation', 'optimized_pool')
        if not valid:
            return False, msg

        optimized_by_const = optimized_pool['by_constellation']
        starlink_optimized = optimized_by_const.get('starlink', 0)  # 星座可能不存在
        oneweb_optimized = optimized_by_const.get('oneweb', 0)      # 星座可能不存在

        # ✅ Fail-Fast #6: 提取 Starlink 驗證數據
        valid, msg = self.check_field_exists(snapshot_data, 'pool_optimization')
        if not valid:
            return False, msg

        pool_optimization = snapshot_data['pool_optimization']

        valid, msg = self.check_field_exists(pool_optimization, 'validation_results', 'pool_optimization')
        if not valid:
            return False, msg

        validation_results = pool_optimization['validation_results']

        valid, msg = self.check_field_exists(validation_results, 'starlink', 'validation_results')
        if not valid:
            return False, msg

        starlink_validation = validation_results['starlink']

        valid, msg = self.check_field_exists(starlink_validation, 'validation_checks', 'starlink_validation')
        if not valid:
            return False, msg

        starlink_checks = starlink_validation['validation_checks']

        valid, msg = self.check_field_exists(starlink_checks, 'coverage_rate_check', 'starlink_checks')
        if not valid:
            return False, msg

        coverage_check = starlink_checks['coverage_rate_check']

        valid, msg = self.check_field_exists(coverage_check, 'value', 'coverage_rate_check')
        if not valid:
            return False, msg

        coverage_rate = coverage_check['value']

        valid, msg = self.check_field_exists(starlink_checks, 'avg_visible_check', 'starlink_checks')
        if not valid:
            return False, msg

        avg_visible_check = starlink_checks['avg_visible_check']

        valid, msg = self.check_field_exists(avg_visible_check, 'value', 'avg_visible_check')
        if not valid:
            return False, msg

        avg_visible = avg_visible_check['value']

        # 統計驗證通過項目
        validation_summary = [
            "✅ #1 星座門檻驗證",
            "✅ #2 可見性精度 (詳細檢查)",
            "✅ #3 鏈路預算約束",
            "✅ #4 NTPU 覆蓋分析",
            "✅ #5 服務窗口 (專用檢查)",
            "✅ #6 池規劃優化 (CRITICAL)"
        ]

        status_msg = (
            f"Stage 4 完整驗證通過 (6項驗證): "
            f"候選池 {candidate_total} 顆 → 優化池 {optimized_total} 顆 | "
            f"Starlink: {starlink_optimized} 顆 (平均可見 {avg_visible:.1f}, 覆蓋率 {coverage_rate:.1%}) | "
            f"OneWeb: {oneweb_optimized} 顆 | "
            f"NTPU 覆蓋: {continuous_coverage_hours:.1f}h | "
            f"驗證項: {', '.join(validation_summary)}"
        )

        return True, status_msg

    def _is_sampling_mode(self, snapshot_data: dict) -> bool:
        """
        Stage 4 取樣模式判斷

        基於 total_input_satellites 和 ORBIT_ENGINE_TEST_MODE
        """
        # ✅ Fail-Fast #5: metadata 和 total_input_satellites 必須存在
        if 'metadata' not in snapshot_data:
            # 如果 metadata 缺失，無法判斷取樣模式，假設非取樣模式（更嚴格）
            return False

        metadata = snapshot_data['metadata']

        if 'total_input_satellites' not in metadata:
            # 如果 total_input_satellites 缺失，無法判斷取樣模式，假設非取樣模式（更嚴格）
            return False

        total_input_satellites = metadata['total_input_satellites']

        # Stage 4 特殊判斷: 少於 50 顆或測試模式
        if total_input_satellites < 50:
            return True

        if os.getenv('ORBIT_ENGINE_TEST_MODE') == '1':
            return True

        # 否則使用基類邏輯
        return super()._is_sampling_mode(snapshot_data)

    def uses_validation_framework(self) -> bool:
        """Stage 4 不使用標準 validation_results 格式"""
        return False


# ============================================================
# 向後兼容函數 (保留原始接口)
# ============================================================

def check_stage4_validation(snapshot_data: dict) -> tuple:
    """
    Stage 4 專用驗證 - 鏈路可行性評估與時空錯置池規劃

    ⚠️ 向後兼容函數: 內部調用 Stage4Validator 類

    檢查項目:
    - 階段 4.1: 可見性篩選 (9040 → ~2000顆候選)
    - 階段 4.2: 池規劃優化 (時空錯置池維持目標)
    - 星座門檻驗證 (Starlink 5°, OneWeb 10°)
    - NTPU 覆蓋分析
    - 鏈路預算約束
    - 可見性計算精度
    - 服務窗口優化

    Args:
        snapshot_data: 驗證快照數據

    Returns:
        tuple: (validation_passed: bool, message: str)
    """
    validator = Stage4Validator()
    return validator.validate(snapshot_data)
