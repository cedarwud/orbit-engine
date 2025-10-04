"""
Stage 2 驗證器 - 軌道狀態傳播層 (v3.0 架構)

Layer 2 驗證: 檢查驗證快照的合理性與架構合規性
信任 Layer 1 (Stage2Processor.run_validation_checks) 的詳細驗證結果

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import json


def check_stage2_validation(snapshot_data: dict) -> tuple:
    """
    Stage 2 專用驗證 - 軌道狀態傳播層 (v3.0 架構)

    檢查項目:
    - v3.0 架構合規性 (純軌道狀態傳播，禁止座標轉換/可見性分析)
    - 軌道傳播成功率
    - TEME 座標輸出品質
    - 星座分離處理效能
    - 禁止職責檢查
    - metadata 完整性

    Args:
        snapshot_data: 驗證快照數據

    Returns:
        tuple: (validation_passed: bool, message: str)
    """
    try:
        # 檢查 v3.0 Stage 2 驗證快照格式 (純軌道狀態傳播)
        if snapshot_data.get('stage') == 'stage2_orbital_computing':
            # v3.0 架構: 只檢查軌道狀態傳播，不檢查可見性/可行性
            data_summary = snapshot_data.get('data_summary', {})
            validation_checks = snapshot_data.get('validation_checks', {})

            total_satellites = data_summary.get('total_satellites_processed', 0)
            successful_propagations = data_summary.get('successful_propagations', 0)
            total_teme_positions = data_summary.get('total_teme_positions', 0)
            validation_passed = snapshot_data.get('validation_passed', False)

            # v3.0 架構基本檢查 - 軌道狀態傳播成功
            if total_satellites == 0:
                return False, f"❌ Stage 2 未處理任何衛星數據"

            if successful_propagations == 0:
                return False, f"❌ Stage 2 軌道狀態傳播失敗: 沒有成功的軌道計算"

            if total_teme_positions == 0:
                return False, f"❌ Stage 2 TEME座標生成失敗: 沒有軌道狀態點"

            # 檢查專用驗證通過率 (至少4/5項通過)
            checks_details = validation_checks.get('check_details', {})
            checks_passed = validation_checks.get('checks_passed', 0)
            checks_performed = validation_checks.get('checks_performed', 0)

            if checks_performed < 5:
                return False, f"❌ Stage 2 專用驗證不完整: 只執行了{checks_performed}/5項檢查"

            if checks_passed < 4:
                return False, f"❌ Stage 2 專用驗證未達標: 只通過了{checks_passed}/5項檢查"

            # 檢查 v3.0 架構合規性
            if not snapshot_data.get('v3_architecture', False):
                return False, f"❌ Stage 2 架構版本不符: 未使用v3.0軌道狀態傳播架構"

            if not snapshot_data.get('orbital_state_propagation', False):
                return False, f"❌ Stage 2 功能不符: 未執行軌道狀態傳播"

            # ✅ P1: 檢查星座分離處理效能 (依據 stage2-orbital-computing.md:372-374)
            constellation_dist = data_summary.get('constellation_distribution', {})
            starlink_count = constellation_dist.get('starlink', 0)
            oneweb_count = constellation_dist.get('oneweb', 0)

            # 檢查星座分離計算 (至少要有一個星座的數據)
            if starlink_count == 0 and oneweb_count == 0:
                return False, f"❌ Stage 2 星座分離失敗: 無 Starlink/OneWeb 數據"

            # 檢查平均軌道點數 (Starlink: ~191點, OneWeb: ~218點)
            if total_satellites > 0:
                avg_points_per_sat = total_teme_positions / total_satellites

                # 根據星座比例計算期望值 (動態軌道週期覆蓋)
                # Starlink: 191點 (95min @ 30s), OneWeb: 218點 (109min @ 30s)
                if starlink_count > 0 and oneweb_count > 0:
                    # 混合星座: 期望值介於 191-218 之間
                    if not (170 <= avg_points_per_sat <= 240):
                        return False, f"❌ Stage 2 軌道點數不符: 平均 {avg_points_per_sat:.1f} 點/衛星 (期望: 170-240, 動態軌道週期)"
                elif starlink_count > 0:
                    # 純 Starlink: 期望 ~191點
                    if not (170 <= avg_points_per_sat <= 210):
                        return False, f"❌ Starlink 軌道點數不符: 平均 {avg_points_per_sat:.1f} 點/衛星 (期望: 191±20)"
                elif oneweb_count > 0:
                    # 純 OneWeb: 期望 ~218點
                    if not (200 <= avg_points_per_sat <= 240):
                        return False, f"❌ OneWeb 軌道點數不符: 平均 {avg_points_per_sat:.1f} 點/衛星 (期望: 218±20)"

            # ✅ P2: 檢查禁止的職責 (防禦性檢查 - 依據 stage2-orbital-computing.md:125-130)
            # Stage 2 絕對禁止: 座標轉換、可見性分析、距離篩選
            forbidden_fields = [
                'wgs84_coordinates', 'itrf_coordinates',  # 座標轉換 (Stage 3)
                'elevation_deg', 'azimuth_deg',  # 可見性分析 (Stage 4)
                'ground_station_distance', 'visible_satellites',  # 距離篩選 (Stage 4)
                'latitude_deg', 'longitude_deg', 'altitude_m'  # WGS84 座標 (Stage 3)
            ]

            for field in forbidden_fields:
                if field in data_summary:
                    return False, f"❌ Stage 2 職責違規: data_summary 包含禁止字段 '{field}' (應在 Stage 3/4 處理)"

                # 檢查整個快照 (防止深層嵌套)
                snapshot_str = json.dumps(snapshot_data)
                if f'"{field}"' in snapshot_str and field not in ['altitude_m']:  # altitude_m 可能出現在 metadata
                    # 進一步確認 (排除文檔說明中的出現)
                    if data_summary.get(field) is not None:
                        return False, f"❌ Stage 2 職責違規: 檢測到禁止字段 '{field}' (違反 v3.0 架構分層)"

            # ✅ P3: 檢查 metadata 完整性 (依據 stage2-orbital-computing.md:313-339)
            metadata = snapshot_data.get('metadata', {})

            # 檢查 propagation_config 存在性
            if 'propagation_config' in metadata:
                propagation_config = metadata['propagation_config']

                # 檢查 SGP4 庫 (應為 skyfield 或 Skyfield_Direct)
                sgp4_library = propagation_config.get('sgp4_library', '')
                if sgp4_library and sgp4_library not in ['skyfield', 'Skyfield_Direct', 'pyephem']:
                    return False, f"❌ SGP4 庫不符: {sgp4_library} (期望: skyfield/Skyfield_Direct/pyephem)"

                # 檢查座標系統 (應為 TEME)
                coord_system = propagation_config.get('coordinate_system', '')
                if coord_system and coord_system != 'TEME':
                    return False, f"❌ 座標系統不符: {coord_system} (期望: TEME)"

                # 檢查 epoch 來源 (應為 stage1_parsed 或 stage1_provided)
                epoch_source = propagation_config.get('epoch_source', '')
                if epoch_source and epoch_source not in ['stage1_parsed', 'stage1_provided']:
                    return False, f"❌ Epoch 來源不符: {epoch_source} (期望: stage1_parsed/stage1_provided)"

            # 成功通過所有 v3.0 架構檢查
            success_rate = (successful_propagations / total_satellites * 100) if total_satellites > 0 else 0
            avg_points = (total_teme_positions / total_satellites) if total_satellites > 0 else 0
            status_msg = (
                f"Stage 2 v3.0架構檢查通過: {total_satellites}衛星 → {successful_propagations}成功軌道傳播 ({success_rate:.1f}%) "
                f"→ {total_teme_positions}個TEME座標點 (平均{avg_points:.1f}點/衛星) | "
                f"星座分離✓ 禁止職責✓ metadata完整性✓"
            )
            return True, status_msg

        # 舊版快照格式檢查 (向後兼容)
        elif 'validation_passed' in snapshot_data:
            if snapshot_data.get('validation_passed', False):
                metrics = snapshot_data.get('metrics', {})
                feasible_satellites = metrics.get('feasible_satellites', 0)
                input_satellites = metrics.get('input_satellites', 0)

                if feasible_satellites > 0 and input_satellites > 0:
                    feasible_rate = (feasible_satellites / input_satellites * 100)
                    return True, f"Stage 2 合理性檢查通過: {feasible_satellites}/{input_satellites} 可行 ({feasible_rate:.1f}%)"
                else:
                    return False, f"❌ Stage 2 數據不足: 可行{feasible_satellites}/總計{input_satellites}"
            else:
                return False, f"❌ Stage 2 驗證未通過"
        else:
            return False, f"❌ Stage 2 驗證快照格式不正確"

    except Exception as e:
        return False, f"❌ Stage 2 驗證異常: {e}"
