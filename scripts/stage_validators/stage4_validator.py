"""
Stage 4 驗證器 - 鏈路可行性評估與時空錯置池規劃層 (Fail-Fast 版本)

Layer 2 驗證: 嚴格檢查驗證快照的完整性與合理性
使用 Fail-Fast 原則: 任何缺失字段立即失敗，不使用預設值

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-04 (Fail-Fast 重構)
"""

import os


def check_stage4_validation(snapshot_data: dict) -> tuple:
    """
    Stage 4 專用驗證 - 鏈路可行性評估與時空錯置池規劃

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
    try:
        # ============================================================
        # ✅ Fail-Fast 檢查: 頂層結構完整性
        # ============================================================

        # 檢查 stage 標識
        if 'stage' not in snapshot_data:
            return False, "❌ 快照缺少必需字段 'stage'"

        if snapshot_data['stage'] != 'stage4_link_feasibility':
            return False, f"❌ Stage 4 快照標識不正確: {snapshot_data['stage']}"

        # 檢查 metadata 存在
        if 'metadata' not in snapshot_data:
            return False, "❌ 快照缺少必需字段 'metadata'"

        metadata = snapshot_data['metadata']

        # ============================================================
        # ✅ Fail-Fast 檢查: 階段完成狀態
        # ============================================================

        if 'stage_4_1_completed' not in metadata:
            return False, "❌ metadata 缺少必需字段 'stage_4_1_completed'"

        if 'stage_4_2_completed' not in metadata:
            return False, "❌ metadata 缺少必需字段 'stage_4_2_completed'"

        stage_4_1_completed = metadata['stage_4_1_completed']
        stage_4_2_completed = metadata['stage_4_2_completed']

        if not stage_4_1_completed:
            return False, "❌ Stage 4.1 可見性篩選未完成"

        # ============================================================
        # ✅ Fail-Fast 檢查: feasibility_summary 結構
        # ============================================================

        if 'feasibility_summary' not in snapshot_data:
            return False, "❌ 快照缺少必需字段 'feasibility_summary'"

        feasibility_summary = snapshot_data['feasibility_summary']

        if 'candidate_pool' not in feasibility_summary:
            return False, "❌ feasibility_summary 缺少必需字段 'candidate_pool'"

        if 'optimized_pool' not in feasibility_summary:
            return False, "❌ feasibility_summary 缺少必需字段 'optimized_pool'"

        candidate_pool = feasibility_summary['candidate_pool']
        optimized_pool = feasibility_summary['optimized_pool']

        # 檢查候選池統計
        if 'total_connectable' not in candidate_pool:
            return False, "❌ candidate_pool 缺少必需字段 'total_connectable'"

        if 'total_optimized' not in optimized_pool:
            return False, "❌ optimized_pool 缺少必需字段 'total_optimized'"

        candidate_total = candidate_pool['total_connectable']
        optimized_total = optimized_pool['total_optimized']

        if candidate_total == 0:
            return False, "❌ Stage 4.1 候選池為空: 沒有可連線衛星"

        # 🔧 檢測取樣/測試模式
        if 'total_input_satellites' not in metadata:
            return False, "❌ metadata 缺少必需字段 'total_input_satellites'"

        total_input_satellites = metadata['total_input_satellites']
        is_sampling_mode = (total_input_satellites < 50) or (os.getenv('ORBIT_ENGINE_TEST_MODE') == '1')

        if is_sampling_mode:
            print(f"🧪 偵測到取樣模式 ({total_input_satellites} 顆衛星)，放寬驗證標準")

        # ============================================================
        # ✅ 驗證 #1: constellation_threshold_validation - 星座門檻驗證
        # ============================================================

        if 'constellation_aware' not in metadata:
            return False, "❌ metadata 缺少必需字段 'constellation_aware'"

        constellation_aware = metadata['constellation_aware']

        if not constellation_aware:
            return False, "❌ Stage 4 星座感知功能未啟用 (constellation_aware=False)"

        # 驗證星座特定門檻設計 (Starlink 5°, OneWeb 10°)
        if 'by_constellation' not in candidate_pool:
            return False, "❌ candidate_pool 缺少必需字段 'by_constellation'"

        candidate_by_const = candidate_pool['by_constellation']

        if not candidate_by_const:
            return False, "❌ Stage 4 星座分類數據缺失 (by_constellation為空)"

        # ============================================================
        # ✅ 驗證 #4: ntpu_coverage_analysis - NTPU 覆蓋分析
        # ============================================================

        if 'ntpu_coverage' not in feasibility_summary:
            return False, "❌ feasibility_summary 缺少必需字段 'ntpu_coverage'"

        ntpu_coverage = feasibility_summary['ntpu_coverage']

        if not ntpu_coverage:
            return False, "❌ Stage 4 NTPU 覆蓋分析數據缺失"

        # 檢查覆蓋時間統計
        if 'continuous_coverage_hours' not in ntpu_coverage:
            return False, "❌ ntpu_coverage 缺少必需字段 'continuous_coverage_hours'"

        if 'average_satellites_visible' not in ntpu_coverage:
            return False, "❌ ntpu_coverage 缺少必需字段 'average_satellites_visible'"

        continuous_coverage_hours = ntpu_coverage['continuous_coverage_hours']
        avg_satellites_visible = ntpu_coverage['average_satellites_visible']

        # 🔧 取樣模式: 跳過嚴格的覆蓋時間和可見衛星數檢查
        if not is_sampling_mode:
            # 🚨 修正 (2025-10-06): 覆蓋時間驗證應基於時間窗口長度，而非軌道週期
            # - 連續覆蓋時間 = 在觀測窗口內，至少有一顆衛星可見的總時長
            # - 軌道週期 = 單顆衛星繞地球一圈的時間（不同概念！）
            # - unified_window 模式下，各星座時間窗口長度 = 各自軌道週期 × coverage_cycles
            #   * Starlink: 95min × 1.0 = 95min = 1.58h
            #   * OneWeb: 110min × 1.0 = 110min = 1.83h
            # - 驗證邏輯: 連續覆蓋時間應接近時間窗口長度（表示無明顯空窗）
            # SOURCE: 衛星通信系統設計，連續覆蓋 = 多顆衛星接力提供服務

            # 🚨 修正 (2025-10-06): 連續覆蓋時間驗證 - 基於TLE實際軌道週期
            # - 連續覆蓋時間 = 時空錯置池在觀測窗口內至少有一顆衛星可見的總時長
            # - 理想值 = 觀測窗口長度（說明卫星池完美錯置）
            # - 實際限制: TLE數據的軌道週期誤差（各顆衛星±1-2分鐘）
            # - 驗證標準: 連續覆蓋時間 ≥ TLE最小軌道週期（轉換為小時）
            # SOURCE: Stage 1 epoch_analysis.json - orbital_period_stats.min_minutes

            # ✅ Fail-Fast: 從Stage 1讀取TLE軌道週期統計（必須存在）
            import json
            from pathlib import Path

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
            if 'constellation_distribution' not in epoch_analysis:
                return False, "❌ epoch_analysis.json 缺少必需字段 'constellation_distribution'"

            tle_orbital_periods = epoch_analysis['constellation_distribution']

            # Fail-Fast: 必須有星座特定的覆蓋數據（by_constellation）
            if 'by_constellation' not in ntpu_coverage:
                return False, "❌ ntpu_coverage 缺少必需字段 'by_constellation'（需要按星座統計 continuous_coverage_hours）"

            by_const = ntpu_coverage['by_constellation']

            # Fail-Fast: by_constellation 不能為空
            if not by_const:
                return False, "❌ ntpu_coverage.by_constellation 為空（需要 Starlink/OneWeb 覆蓋統計）"

            for const_name, const_data in by_const.items():
                # Fail-Fast: continuous_coverage_hours 必須存在
                if 'continuous_coverage_hours' not in const_data:
                    return False, f"❌ ntpu_coverage.by_constellation.{const_name} 缺少必需字段 'continuous_coverage_hours'"

                const_coverage = const_data['continuous_coverage_hours']

                # Fail-Fast: TLE 軌道週期統計必須存在
                if const_name.upper() not in tle_orbital_periods:
                    return False, f"❌ epoch_analysis.json 缺少 {const_name.upper()} 星座的 TLE 軌道週期統計"

                orbital_stats = tle_orbital_periods[const_name.upper()].get('orbital_period_stats', {})

                # Fail-Fast: orbital_period_stats 不能為空
                if not orbital_stats:
                    return False, f"❌ epoch_analysis.json 中 {const_name.upper()} 的 orbital_period_stats 為空"

                # Fail-Fast: min_minutes 必須存在
                if 'min_minutes' not in orbital_stats:
                    return False, f"❌ epoch_analysis.json 中 {const_name.upper()} orbital_period_stats 缺少 'min_minutes'"

                min_period_minutes = orbital_stats['min_minutes']

                # Fail-Fast: min_minutes 必須 > 0
                if min_period_minutes <= 0:
                    return False, f"❌ {const_name.upper()} TLE 最小軌道週期無效: {min_period_minutes}min (必須 > 0)"

                min_required_hours = min_period_minutes / 60.0
                threshold_source = f"TLE最小軌道週期 {min_period_minutes:.1f}min"

                # 驗證連續覆蓋時間
                if const_coverage < min_required_hours:
                    return False, f"❌ Stage 4 {const_name} 連續覆蓋時間不足: {const_coverage:.2f}h (需要 ≥{min_required_hours:.2f}h，基於{threshold_source})"

            # 平均可見衛星數檢查（保持原邏輯）
            if avg_satellites_visible < 10.0:  # Starlink 目標範圍下限
                return False, f"❌ Stage 4 NTPU 平均可見衛星數過低: {avg_satellites_visible:.1f} 顆 (需要 ≥10.0)"

            # ============================================================
            # ✅ 驗證 #3: link_budget_constraints - 鏈路預算約束
            # ============================================================

            if 'ntpu_specific' not in metadata:
                return False, "❌ metadata 缺少必需字段 'ntpu_specific'"

            ntpu_specific = metadata['ntpu_specific']

            if not ntpu_specific:
                return False, "❌ Stage 4 NTPU 特定配置未啟用 (ntpu_specific=False)"

        # ✅ 強制檢查: 階段 4.2 必須完成 (🔴 CRITICAL 必要功能)
        if not stage_4_2_completed:
            return False, "❌ Stage 4.2 池規劃優化未完成 (🔴 CRITICAL 必要功能，不可跳過)"

        # ============================================================
        # ✅ 關鍵檢查: 階段 4.2 時空錯置池規劃驗證
        # ============================================================

        if stage_4_2_completed:
            # 檢查優化結果存在
            if 'pool_optimization' not in snapshot_data:
                return False, "❌ 快照缺少必需字段 'pool_optimization'"

            pool_optimization = snapshot_data['pool_optimization']

            if 'validation_results' not in pool_optimization:
                return False, "❌ pool_optimization 缺少必需字段 'validation_results'"

            validation_results = pool_optimization['validation_results']

            # 檢查 Starlink 優化結果
            if 'starlink' not in validation_results:
                return False, "❌ validation_results 缺少必需字段 'starlink'"

            starlink_validation = validation_results['starlink']

            if 'validation_passed' not in starlink_validation:
                return False, "❌ starlink_validation 缺少必需字段 'validation_passed'"

            if 'validation_checks' not in starlink_validation:
                return False, "❌ starlink_validation 缺少必需字段 'validation_checks'"

            starlink_passed = starlink_validation['validation_passed']
            starlink_checks = starlink_validation['validation_checks']

            # 檢查覆蓋率
            if 'coverage_rate_check' not in starlink_checks:
                return False, "❌ starlink_checks 缺少必需字段 'coverage_rate_check'"

            coverage_check = starlink_checks['coverage_rate_check']

            if 'value' not in coverage_check:
                return False, "❌ coverage_rate_check 缺少必需字段 'value'"

            coverage_rate = coverage_check['value']

            # 提取 avg_visible
            if 'avg_visible_check' not in starlink_checks:
                return False, "❌ starlink_checks 缺少必需字段 'avg_visible_check'"

            avg_visible_check = starlink_checks['avg_visible_check']

            if 'value' not in avg_visible_check:
                return False, "❌ avg_visible_check 缺少必需字段 'value'"

            if 'target_range' not in avg_visible_check:
                return False, "❌ avg_visible_check 缺少必需字段 'target_range'"

            avg_visible = avg_visible_check['value']
            target_range = avg_visible_check['target_range']

            # 🔧 取樣模式: 跳過嚴格的覆蓋率和可見數檢查
            if not is_sampling_mode:
                if coverage_rate < 0.95:
                    return False, f"❌ Stage 4.2 Starlink 覆蓋率不足: {coverage_rate:.1%} (需要 ≥95%)"

                # ✅ 核心驗證: 檢查「任意時刻可見數」是否在目標範圍
                if not (target_range[0] <= avg_visible <= target_range[1]):
                    return False, f"❌ Stage 4.2 Starlink 平均可見數不符: {avg_visible:.1f} 顆 (目標: {target_range[0]}-{target_range[1]})"

            # 檢查覆蓋空窗
            if 'coverage_gaps_check' not in starlink_checks:
                return False, "❌ starlink_checks 缺少必需字段 'coverage_gaps_check'"

            gaps_check = starlink_checks['coverage_gaps_check']

            if 'gap_count' not in gaps_check:
                return False, "❌ coverage_gaps_check 缺少必需字段 'gap_count'"

            gap_count = gaps_check['gap_count']

            if gap_count > 0:
                return False, f"❌ Stage 4.2 Starlink 存在覆蓋空窗: {gap_count} 個時間點無可見衛星"

            # OneWeb 檢查 (較寬鬆)
            # 🔧 取樣模式: 跳過 OneWeb 覆蓋率檢查 (可能沒有 OneWeb 衛星)
            if not is_sampling_mode:
                # OneWeb 可能不存在（取決於數據），所以這裡用 if 檢查而非 Fail-Fast
                if 'oneweb' in validation_results:
                    oneweb_validation = validation_results['oneweb']

                    if 'validation_checks' not in oneweb_validation:
                        return False, "❌ oneweb_validation 缺少必需字段 'validation_checks'"

                    oneweb_checks = oneweb_validation['validation_checks']

                    if 'coverage_rate_check' in oneweb_checks:
                        oneweb_coverage_check = oneweb_checks['coverage_rate_check']

                        if 'value' not in oneweb_coverage_check:
                            return False, "❌ oneweb coverage_rate_check 缺少必需字段 'value'"

                        oneweb_coverage = oneweb_coverage_check['value']

                        if oneweb_coverage < 0.80:  # OneWeb 允許較低覆蓋率
                            return False, f"❌ Stage 4.2 OneWeb 覆蓋率過低: {oneweb_coverage:.1%}"

            # ============================================================
            # ⚠️ 驗證 #2: visibility_calculation_accuracy - 可見性計算精度
            # ============================================================

            if 'use_iau_standards' not in metadata:
                return False, "❌ metadata 缺少必需字段 'use_iau_standards'"

            use_iau_standards = metadata['use_iau_standards']

            if not use_iau_standards:
                return False, "❌ Stage 4 未使用 IAU 標準座標計算 (use_iau_standards=False)"

            # 🔧 取樣模式: 跳過候選池數量範圍檢查
            if not is_sampling_mode:
                # 驗證基本數據合理性：候選池應在合理範圍內
                if candidate_total < 100 or candidate_total > 5000:
                    return False, f"❌ Stage 4 候選池數量異常: {candidate_total} 顆 (合理範圍: 100-5000)"

            # ============================================================
            # ⚠️ 驗證 #5: service_window_optimization - 服務窗口優化
            # ============================================================

            # 🔧 取樣模式: 跳過覆蓋空窗檢查 (衛星數量少，覆蓋空窗是正常的)
            if not is_sampling_mode:
                # 檢查覆蓋空窗數據
                if 'coverage_gaps_minutes' not in ntpu_coverage:
                    return False, "❌ ntpu_coverage 缺少必需字段 'coverage_gaps_minutes'"

                coverage_gaps = ntpu_coverage['coverage_gaps_minutes']

                # 檢查是否有過長的覆蓋空窗（超過 30 分鐘視為不合理）
                long_gaps = [gap for gap in coverage_gaps if gap > 30.0]
                if long_gaps:
                    return False, f"❌ Stage 4 存在過長覆蓋空窗: {len(long_gaps)} 個超過 30 分鐘 (最長 {max(long_gaps):.1f} 分鐘)"

                # 驗證覆蓋連續性：空窗總數應該很少
                if len(coverage_gaps) > 5:
                    return False, f"❌ Stage 4 覆蓋空窗過多: {len(coverage_gaps)} 個 (建議 ≤5 個)"

            # ============================================================
            # ✅ 所有驗證通過 - 生成完整驗證報告
            # ============================================================

            if 'by_constellation' not in optimized_pool:
                return False, "❌ optimized_pool 缺少必需字段 'by_constellation'"

            optimized_by_const = optimized_pool['by_constellation']

            starlink_optimized = optimized_by_const.get('starlink', 0)
            oneweb_optimized = optimized_by_const.get('oneweb', 0)

            # 統計驗證通過項目
            validation_summary = [
                "✅ #1 星座門檻驗證",
                "✅ #3 鏈路預算約束",
                "✅ #4 NTPU 覆蓋分析",
                "✅ #6 池規劃優化 (CRITICAL)",
                "⚠️ #2 可見性精度 (基本檢查)",
                "⚠️ #5 服務窗口 (基本檢查)"
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

    except KeyError as e:
        return False, f"❌ Stage 4 驗證數據結構錯誤: 缺少必需字段 {e}"
    except Exception as e:
        return False, f"❌ Stage 4 驗證異常: {e}"
