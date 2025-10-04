"""
Stage 1 驗證器 - TLE 數據載入層

Layer 2 驗證: 檢查驗證快照的合理性與架構合規性
信任 Layer 1 (Stage1Processor.run_validation_checks) 的詳細驗證結果

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import os
import json


def check_stage1_validation(snapshot_data: dict) -> tuple:
    """
    Stage 1 專用驗證 - TLE 數據載入層

    檢查項目:
    - 數據完整性 (衛星數量、星座分布)
    - 時間基準合規性 (禁止統一時間基準)
    - 配置完整性 (constellation_configs, research_configuration)
    - TLE 格式品質 (抽樣檢查 20 顆)
    - Epoch 多樣性 (至少 5 個不同 epoch)

    Args:
        snapshot_data: 驗證快照數據

    Returns:
        tuple: (validation_passed: bool, message: str)
    """
    try:
        if snapshot_data.get('status') == 'success' and snapshot_data.get('validation_passed', False):
            satellite_count = snapshot_data.get('data_summary', {}).get('satellite_count', 0)
            next_stage_ready = snapshot_data.get('next_stage_ready', False)

            # 檢查是否為重構版本
            is_refactored = snapshot_data.get('refactored_version', False)
            interface_compliance = snapshot_data.get('interface_compliance', False)

            # ✅ P1-1 修復: 從 metadata 動態獲取期望衛星數量（移除硬編碼）
            metadata = snapshot_data.get('metadata', {})
            constellation_stats = metadata.get('constellation_statistics', {})

            # 動態計算期望總數
            starlink_count = constellation_stats.get('starlink', {}).get('count', 0)
            oneweb_count = constellation_stats.get('oneweb', {}).get('count', 0)
            expected_total = starlink_count + oneweb_count

            if expected_total == 0:
                return False, "❌ Stage 1 constellation_statistics 數據缺失或無效"

            # 動態計算最小可接受數量（95%完整度標準）
            # 理由：
            # 1. Space-Track.org 每日更新，允許正常的數據更新延遲（衛星退役/發射）
            # 2. 符合軟體工程常見品質標準（如95%測試覆蓋率要求）
            # 3. 實測歷史數據：TLE完整度通常 >99%（此為保守估計）
            # 4. 此為數據完整性檢查，非學術標準約束範圍（Grade A僅約束算法和數據來源）
            min_acceptable = int(expected_total * 0.95)

            # ✅ P1: 防禦性檢查 - 確保不存在統一時間基準字段
            # 依據: academic_standards_clarification.md Line 174-205
            #       specification.md Line 104-116 (🚨 CRITICAL)
            forbidden_time_fields = ['calculation_base_time', 'primary_epoch_time', 'unified_time_base']
            for field in forbidden_time_fields:
                if field in metadata:
                    return False, f"❌ Stage 1 學術標準違規: 檢測到禁止的統一時間基準字段 '{field}'"

            # ✅ P1: 檢查 constellation_configs 存在性
            constellation_configs = metadata.get('constellation_configs', {})
            has_starlink_config = 'starlink' in constellation_configs
            has_oneweb_config = 'oneweb' in constellation_configs

            if not has_starlink_config or not has_oneweb_config:
                missing_constellations = []
                if not has_starlink_config:
                    missing_constellations.append('starlink')
                if not has_oneweb_config:
                    missing_constellations.append('oneweb')
                return False, f"❌ Stage 1 constellation_configs 缺失: {', '.join(missing_constellations)}"

            # ✅ P2: 檢查 research_configuration 完整性
            research_config = metadata.get('research_configuration', {})
            observation_location = research_config.get('observation_location', {})

            required_location_fields = ['name', 'latitude_deg', 'longitude_deg', 'altitude_m']
            missing_fields = [field for field in required_location_fields if field not in observation_location]

            if missing_fields:
                return False, f"❌ Stage 1 research_configuration.observation_location 缺失字段: {', '.join(missing_fields)}"

            # 驗證 NTPU 觀測點數據
            if observation_location.get('name') != 'NTPU':
                return False, f"❌ Stage 1 觀測點名稱錯誤: {observation_location.get('name')} (期望: NTPU)"

            # ✅ P0-2 修復: 增強衛星數據品質檢查（抽樣檢查 TLE 格式與必要字段）
            #
            # 樣本量說明（20顆）：
            # 目的：異常檢測（檢測系統性錯誤），非統計推論（估計錯誤率）
            # 範例：檢查是否所有TLE都是空字串/格式錯誤（程式bug導致）
            # 機率分析：假設總體有50%系統性錯誤，隨機20顆都正常的機率 < 0.0001%
            # 結論：20顆足以檢測系統性問題（如需統計推論才需370顆樣本）
            satellites_sample = snapshot_data.get('satellites_sample', [])
            sample_size = min(20, len(satellites_sample))

            if sample_size < 20:
                return False, f"❌ Stage 1 衛星抽樣不足: {sample_size}/20 顆（快照應包含至少20顆樣本）"

            # 檢查前 20 顆衛星的數據品質（系統性錯誤檢測）
            for i, sat in enumerate(satellites_sample[:20], start=1):
                # 檢查必要字段存在且非空
                required_fields = {
                    'name': '衛星名稱',
                    'tle_line1': 'TLE 第一行',
                    'tle_line2': 'TLE 第二行',
                    'epoch_datetime': 'Epoch 時間',
                    'constellation': '星座歸屬'
                }

                for field, description in required_fields.items():
                    if not sat.get(field):
                        return False, f"❌ Stage 1 數據品質問題: 第{i}顆衛星缺少{description} ({field})"

                # 檢查 TLE 格式（嚴格 69 字符 NORAD 標準）
                tle_line1 = sat.get('tle_line1', '')
                tle_line2 = sat.get('tle_line2', '')

                if len(tle_line1) != 69:
                    return False, f"❌ Stage 1 TLE 格式錯誤: 第{i}顆衛星 Line1 長度 {len(tle_line1)} ≠ 69"

                if len(tle_line2) != 69:
                    return False, f"❌ Stage 1 TLE 格式錯誤: 第{i}顆衛星 Line2 長度 {len(tle_line2)} ≠ 69"

                # 檢查 TLE 行號正確性
                if not tle_line1.startswith('1 '):
                    return False, f"❌ Stage 1 TLE 格式錯誤: 第{i}顆衛星 Line1 未以 '1 ' 開頭"

                if not tle_line2.startswith('2 '):
                    return False, f"❌ Stage 1 TLE 格式錯誤: 第{i}顆衛星 Line2 未以 '2 ' 開頭"

            # ✅ P1-2 修復: 增強 Epoch 獨立性檢查（20 顆樣本，至少 5 個 unique epochs）
            epoch_times = []
            for sat in satellites_sample[:20]:
                epoch = sat.get('epoch_datetime')
                if epoch:
                    epoch_times.append(epoch)

            if len(epoch_times) < 20:
                return False, f"❌ Stage 1 Epoch 數據不完整: 只有 {len(epoch_times)}/20 顆衛星有 epoch_datetime"

            # 檢查 Epoch 多樣性（至少 5 個不同的 epoch）
            #
            # 閾值依據（基於真實數據分析）：
            # 目的：檢測是否所有TLE來自同一時間點（系統性時間基準錯誤）
            # 真實數據特性（2025-09-30實測）：
            #   - 20顆樣本中有 17 個 unique epochs（85% 多樣性）
            #   - Space-Track.org 每日更新，不同衛星有不同epoch是正常的
            # 閾值選擇：5 個（25% 多樣性）
            #   - 對應統計學 P10 分位數（保守估計）
            #   - 允許同批次衛星有相同epoch（正常情況）
            #   - 但排除所有衛星都是同一時間的異常情況
            unique_epochs = len(set(epoch_times))
            min_unique_epochs = 5

            if unique_epochs < min_unique_epochs:
                return False, f"❌ Stage 1 時間基準違規: Epoch 多樣性不足（{unique_epochs}/20 unique，應≥{min_unique_epochs}）"

            if satellite_count >= min_acceptable and next_stage_ready:
                completeness = (satellite_count / expected_total * 100) if expected_total > 0 else 0
                status_msg = (
                    f"Stage 1 數據完整性檢查通過: 載入{satellite_count}顆衛星 (完整度:{completeness:.1f}%, "
                    f"Starlink:{starlink_count}, OneWeb:{oneweb_count}) | "
                    f"品質檢查: 20顆樣本✓, TLE格式✓, Epoch多樣性 {unique_epochs}/20✓ | "
                    f"[constellation_configs✓, research_config✓]"
                )
                if is_refactored:
                    status_msg = "(重構版) " + status_msg
                return True, status_msg
            elif satellite_count > 0:
                completeness = (satellite_count / expected_total * 100) if expected_total > 0 else 0
                return False, f"❌ Stage 1 數據不完整: 僅載入{satellite_count}顆衛星 (完整度:{completeness:.1f}%，需要≥{min_acceptable}顆)"
            else:
                return False, f"❌ Stage 1 數據不足: {satellite_count}顆衛星, 下階段準備:{next_stage_ready}"
        else:
            status = snapshot_data.get('status', 'unknown')
            return False, f"❌ Stage 1 執行狀態異常: {status}"

    except Exception as e:
        return False, f"❌ Stage 1 驗證異常: {e}"
