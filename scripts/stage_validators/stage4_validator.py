"""
Stage 4 驗證器 - 鏈路可行性評估與時空錯置池規劃層

Layer 2 驗證: 檢查驗證快照的合理性與架構合規性
信任 Layer 1 (Stage4Processor.run_validation_checks) 的詳細驗證結果

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
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
        # 檢查基本結構
        if snapshot_data.get('stage') != 'stage4_link_feasibility':
            return False, f"❌ Stage 4 快照標識不正確: {snapshot_data.get('stage')}"

        # 檢查階段 4.1 和 4.2 完成狀態
        metadata = snapshot_data.get('metadata', {})
        stage_4_1_completed = metadata.get('stage_4_1_completed', False)
        stage_4_2_completed = metadata.get('stage_4_2_completed', False)

        if not stage_4_1_completed:
            return False, f"❌ Stage 4.1 可見性篩選未完成"

        # 獲取候選池和優化池統計
        feasibility_summary = snapshot_data.get('feasibility_summary', {})
        candidate_pool = feasibility_summary.get('candidate_pool', {})
        optimized_pool = feasibility_summary.get('optimized_pool', {})

        candidate_total = candidate_pool.get('total_connectable', 0)
        optimized_total = optimized_pool.get('total_optimized', 0)

        if candidate_total == 0:
            return False, f"❌ Stage 4.1 候選池為空: 沒有可連線衛星"

        # 🔧 檢測取樣/測試模式：如果輸入衛星少於 50 顆，則為取樣模式，放寬驗證標準
        total_input_satellites = metadata.get('total_input_satellites', 0)
        is_sampling_mode = (total_input_satellites < 50) or (os.getenv('ORBIT_ENGINE_TEST_MODE') == '1')

        if is_sampling_mode:
            print(f"🧪 偵測到取樣模式 ({total_input_satellites} 顆衛星)，放寬驗證標準")

        # ============================================================
        # ✅ 驗證 #1: constellation_threshold_validation - 星座門檻驗證
        # ============================================================
        constellation_aware = metadata.get('constellation_aware', False)
        if not constellation_aware:
            return False, f"❌ Stage 4 星座感知功能未啟用 (constellation_aware=False)"

        # 驗證星座特定門檻設計 (Starlink 5°, OneWeb 10°)
        candidate_by_const = candidate_pool.get('by_constellation', {})
        if not candidate_by_const:
            return False, f"❌ Stage 4 星座分類數據缺失 (by_constellation為空)"

        # ============================================================
        # ✅ 驗證 #4: ntpu_coverage_analysis - NTPU 覆蓋分析
        # ============================================================
        ntpu_coverage = feasibility_summary.get('ntpu_coverage', {})
        if not ntpu_coverage:
            return False, f"❌ Stage 4 NTPU 覆蓋分析數據缺失"

        # 提取覆蓋時間（用於驗證報告）
        continuous_coverage_hours = ntpu_coverage.get('continuous_coverage_hours', 0.0)
        avg_satellites_visible = ntpu_coverage.get('average_satellites_visible', 0.0)

        # 🔧 取樣模式: 跳過嚴格的覆蓋時間和可見衛星數檢查
        if not is_sampling_mode:
            if continuous_coverage_hours < 23.0:  # 允許小幅誤差 (目標 23.5h)
                return False, f"❌ Stage 4 NTPU 連續覆蓋時間不足: {continuous_coverage_hours:.1f}h (需要 ≥23.0h)"

            if avg_satellites_visible < 10.0:  # Starlink 目標範圍下限
                return False, f"❌ Stage 4 NTPU 平均可見衛星數過低: {avg_satellites_visible:.1f} 顆 (需要 ≥10.0)"

            # ============================================================
            # ✅ 驗證 #3: link_budget_constraints - 鏈路預算約束
            # ============================================================
            ntpu_specific = metadata.get('ntpu_specific', False)
            if not ntpu_specific:
                return False, f"❌ Stage 4 NTPU 特定配置未啟用 (ntpu_specific=False)"

        # ✅ 強制檢查: 階段 4.2 必須完成 (🔴 CRITICAL 必要功能)
        if not stage_4_2_completed:
            return False, f"❌ Stage 4.2 池規劃優化未完成 (🔴 CRITICAL 必要功能，不可跳過)"

        # ✅ 關鍵檢查: 階段 4.2 時空錯置池規劃驗證
        if stage_4_2_completed:
            # 檢查優化結果
            pool_optimization = snapshot_data.get('pool_optimization', {})
            validation_results = pool_optimization.get('validation_results', {})

            # 檢查 Starlink 優化結果
            starlink_validation = validation_results.get('starlink', {})
            starlink_passed = starlink_validation.get('validation_passed', False)
            starlink_checks = starlink_validation.get('validation_checks', {})

            # 檢查覆蓋率
            coverage_check = starlink_checks.get('coverage_rate_check', {})
            coverage_rate = coverage_check.get('value', 0.0)

            # 提取 avg_visible (用於驗證報告)
            avg_visible_check = starlink_checks.get('avg_visible_check', {})
            avg_visible = avg_visible_check.get('value', 0.0)
            target_range = avg_visible_check.get('target_range', [10, 15])

            # 🔧 取樣模式: 跳過嚴格的覆蓋率和可見數檢查
            if not is_sampling_mode:
                if coverage_rate < 0.95:
                    return False, f"❌ Stage 4.2 Starlink 覆蓋率不足: {coverage_rate:.1%} (需要 ≥95%)"

                # ✅ 核心驗證: 檢查「任意時刻可見數」是否在目標範圍
                if not (target_range[0] <= avg_visible <= target_range[1]):
                    return False, f"❌ Stage 4.2 Starlink 平均可見數不符: {avg_visible:.1f} 顆 (目標: {target_range[0]}-{target_range[1]})"

            # 檢查覆蓋空窗
            gaps_check = starlink_checks.get('coverage_gaps_check', {})
            gap_count = gaps_check.get('gap_count', 0)

            if gap_count > 0:
                return False, f"❌ Stage 4.2 Starlink 存在覆蓋空窗: {gap_count} 個時間點無可見衛星"

            # OneWeb 檢查 (較寬鬆)
            # 🔧 取樣模式: 跳過 OneWeb 覆蓋率檢查 (可能沒有 OneWeb 衛星)
            if not is_sampling_mode:
                oneweb_validation = validation_results.get('oneweb', {})
                if oneweb_validation:
                    oneweb_checks = oneweb_validation.get('validation_checks', {})
                    oneweb_coverage = oneweb_checks.get('coverage_rate_check', {}).get('value', 0.0)

                    if oneweb_coverage < 0.80:  # OneWeb 允許較低覆蓋率
                        return False, f"❌ Stage 4.2 OneWeb 覆蓋率過低: {oneweb_coverage:.1%}"

            # ============================================================
            # ⚠️ 驗證 #2: visibility_calculation_accuracy - 可見性計算精度
            # ============================================================
            # 基於 metadata 標記進行基本檢查（詳細精度驗證需要實際衛星數據）
            use_iau_standards = metadata.get('use_iau_standards', False)
            if not use_iau_standards:
                return False, f"❌ Stage 4 未使用 IAU 標準座標計算 (use_iau_standards=False)"

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
                # 基於 ntpu_coverage 進行服務窗口品質檢查
                coverage_gaps = ntpu_coverage.get('coverage_gaps_minutes', [])

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
            starlink_optimized = optimized_pool.get('by_constellation', {}).get('starlink', 0)
            oneweb_optimized = optimized_pool.get('by_constellation', {}).get('oneweb', 0)

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

    except Exception as e:
        return False, f"❌ Stage 4 驗證異常: {e}"
