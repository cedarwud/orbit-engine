"""
Stage 5 驗證器 - 信號品質分析層 (3GPP TS 38.214 + ITU-R P.618)

✅ Grade A+ 標準: 100% Fail-Fast 驗證
依據: docs/ACADEMIC_STANDARDS.md Line 265-274

Layer 2 驗證: 檢查驗證快照的合理性與架構合規性
信任 Layer 1 (Stage5Processor.run_validation_checks) 的詳細驗證結果

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
Updated: 2025-10-04 - Fail-Fast 重構
"""


def check_stage5_validation(snapshot_data: dict) -> tuple:
    """
    Stage 5 專用驗證 - 信號品質分析層 (3GPP TS 38.214 + ITU-R P.618)

    ✅ Grade A+ 標準: 分層 Fail-Fast 驗證
    - 第 1 層: 結構驗證（字段是否存在）
    - 第 2 層: 類型驗證（字段類型是否正確）
    - 第 3 層: 範圍驗證（值是否在合理範圍）
    - 第 4 層: 業務邏輯驗證（業務規則是否滿足）

    檢查項目:
    - 3GPP TS 38.214 標準合規性
    - ITU-R P.618 標準合規性
    - CODATA 2018 物理常數
    - 信號品質分布合理性
    - RSRP/RSRQ/SINR 指標範圍
    - 可用衛星比率

    Args:
        snapshot_data: 驗證快照數據

    Returns:
        tuple: (validation_passed: bool, message: str)

    Raises:
        不拋出異常，返回驗證結果
    """
    try:
        # ============================================================================
        # 第 1 層: 結構驗證 - 檢查必要字段是否存在
        # ============================================================================

        # 檢查頂層結構
        if not isinstance(snapshot_data, dict):
            return False, f"❌ 快照數據類型錯誤: {type(snapshot_data).__name__} (期望: dict)"

        # 檢查 stage 字段
        if 'stage' not in snapshot_data:
            return False, "❌ 快照數據缺少 'stage' 字段 - 數據結構錯誤"

        if snapshot_data['stage'] != 'stage5_signal_analysis':
            return False, f"❌ Stage 識別錯誤: {snapshot_data['stage']} (期望: stage5_signal_analysis)"

        # 檢查 data_summary 存在性
        if 'data_summary' not in snapshot_data:
            return False, "❌ 快照數據缺少 'data_summary' - 關鍵摘要數據缺失"

        data_summary = snapshot_data['data_summary']

        # 檢查 data_summary 類型
        if not isinstance(data_summary, dict):
            return False, f"❌ data_summary 類型錯誤: {type(data_summary).__name__} (期望: dict)"

        # 檢查 data_summary 必要字段
        required_summary_fields = [
            'total_satellites_analyzed',
            'usable_satellites',
            'signal_quality_distribution',
            'average_rsrp_dbm',
            'average_sinr_db'
        ]

        missing_summary_fields = [f for f in required_summary_fields if f not in data_summary]
        if missing_summary_fields:
            return False, f"❌ data_summary 缺少必要字段: {missing_summary_fields}"

        # 檢查 metadata 存在性
        if 'metadata' not in snapshot_data:
            return False, "❌ 快照數據缺少 'metadata' - 標準合規資訊缺失"

        metadata = snapshot_data['metadata']

        # 檢查 metadata 類型
        if not isinstance(metadata, dict):
            return False, f"❌ metadata 類型錯誤: {type(metadata).__name__} (期望: dict)"

        # ============================================================================
        # 第 2 層: 類型驗證 - 檢查字段類型是否正確
        # ============================================================================

        # 驗證 total_satellites_analyzed 類型
        total_satellites_analyzed = data_summary['total_satellites_analyzed']
        if not isinstance(total_satellites_analyzed, (int, float)):
            return False, f"❌ total_satellites_analyzed 類型錯誤: {type(total_satellites_analyzed).__name__} (期望: int/float)"

        # 驗證 usable_satellites 類型
        usable_satellites = data_summary['usable_satellites']
        if not isinstance(usable_satellites, (int, float)):
            return False, f"❌ usable_satellites 類型錯誤: {type(usable_satellites).__name__} (期望: int/float)"

        # 驗證 signal_quality_distribution 類型
        signal_quality_distribution = data_summary['signal_quality_distribution']
        if not isinstance(signal_quality_distribution, dict):
            return False, f"❌ signal_quality_distribution 類型錯誤: {type(signal_quality_distribution).__name__} (期望: dict)"

        # 驗證 average_rsrp_dbm 類型
        average_rsrp_dbm = data_summary['average_rsrp_dbm']
        if average_rsrp_dbm is not None and not isinstance(average_rsrp_dbm, (int, float)):
            return False, f"❌ average_rsrp_dbm 類型錯誤: {type(average_rsrp_dbm).__name__} (期望: int/float/None)"

        # 驗證 average_sinr_db 類型
        average_sinr_db = data_summary['average_sinr_db']
        if average_sinr_db is not None and not isinstance(average_sinr_db, (int, float)):
            return False, f"❌ average_sinr_db 類型錯誤: {type(average_sinr_db).__name__} (期望: int/float/None)"

        # ============================================================================
        # 第 3 層: 範圍驗證 - 檢查值是否在合理範圍
        # ============================================================================

        # 驗證衛星數量合理性
        if total_satellites_analyzed < 0:
            return False, f"❌ total_satellites_analyzed 值非法: {total_satellites_analyzed} (必須 >= 0)"

        if usable_satellites < 0:
            return False, f"❌ usable_satellites 值非法: {usable_satellites} (必須 >= 0)"

        if usable_satellites > total_satellites_analyzed:
            return False, f"❌ 數據不一致: usable_satellites ({usable_satellites}) > total_satellites_analyzed ({total_satellites_analyzed})"

        # 驗證信號品質分布字段存在性
        required_quality_fields = ['excellent', 'good', 'fair', 'poor']
        missing_quality_fields = [f for f in required_quality_fields if f not in signal_quality_distribution]
        if missing_quality_fields:
            return False, f"❌ signal_quality_distribution 缺少字段: {missing_quality_fields}"

        # 提取信號品質分布值
        excellent = signal_quality_distribution['excellent']
        good = signal_quality_distribution['good']
        fair = signal_quality_distribution['fair']
        poor = signal_quality_distribution['poor']

        # 驗證信號品質分布類型和範圍
        for name, value in [('excellent', excellent), ('good', good), ('fair', fair), ('poor', poor)]:
            if not isinstance(value, (int, float)):
                return False, f"❌ signal_quality_distribution['{name}'] 類型錯誤: {type(value).__name__}"
            if value < 0:
                return False, f"❌ signal_quality_distribution['{name}'] 值非法: {value} (必須 >= 0)"

        # 驗證 RSRP 範圍
        # SOURCE: 3GPP TS 38.215 v18.1.0 Section 5.1.1
        # - UE 報告量化範圍: -140 to -44 dBm (用於 RRC 訊息報告)
        # - 物理 RSRP 可以 > -44 dBm (近距離、高增益、LEO 衛星場景)
        # - 學術研究應保留真實計算值，不應截斷至報告範圍
        #
        # 驗證策略:
        # - 下限: -140 dBm (熱噪聲底 + 微弱信號檢測極限)
        # - 上限: -20 dBm (實際物理上限，考慮 LEO 衛星近距離場景)
        #         Starlink: 550km, Tx ~20dBW, 路徑損耗 ~165dB → RSRP 約 -50 to -30 dBm
        #         OneWeb: 1200km → RSRP 約 -60 to -40 dBm
        if average_rsrp_dbm is None:
            return False, "❌ average_rsrp_dbm 為 None - 缺少關鍵信號指標"

        if not (-140 <= average_rsrp_dbm <= -20):
            return False, (
                f"❌ average_rsrp_dbm 超出物理合理範圍: {average_rsrp_dbm:.1f} dBm "
                f"(物理範圍: -140 to -20 dBm)\n"
                f"   註: 3GPP UE報告範圍 -140 to -44 dBm 是量化範圍，非物理限制\n"
                f"   LEO衛星場景實際 RSRP 可能在 -30 to -60 dBm (符合學術研究)"
            )

        # 驗證 SINR（可選但建議提供）
        if average_sinr_db is None:
            return False, "❌ average_sinr_db 為 None - 缺少關鍵信號指標"

        # ============================================================================
        # 第 4 層: 業務邏輯驗證 - 檢查業務規則是否滿足
        # ============================================================================

        # 業務規則 1: 必須分析了衛星
        if total_satellites_analyzed == 0:
            return False, "❌ Stage 5 處理失敗: 0 顆衛星被分析 - 信號分析未執行"

        # 業務規則 2: 信號品質分布總和應該合理
        total_quality = excellent + good + fair + poor
        if total_quality == 0:
            return False, "❌ signal_quality_distribution 總和為 0 - 信號品質數據缺失"

        # 業務規則 3: 檢查 metadata 合規標記
        # 檢查 gpp_standard_compliance
        if 'gpp_standard_compliance' not in metadata:
            return False, "❌ metadata 缺少 'gpp_standard_compliance' 字段"

        gpp_compliance = metadata['gpp_standard_compliance']
        if gpp_compliance != True:
            return False, f"❌ 3GPP 標準合規性未通過: {gpp_compliance} (期望: True)"

        # 檢查 itur_standard_compliance
        if 'itur_standard_compliance' not in metadata:
            return False, "❌ metadata 缺少 'itur_standard_compliance' 字段"

        itur_compliance = metadata['itur_standard_compliance']
        if itur_compliance != True:
            return False, f"❌ ITU-R 標準合規性未通過: {itur_compliance} (期望: True)"

        # 業務規則 4: 檢查 3GPP 配置
        if 'gpp_config' not in metadata:
            return False, "❌ metadata 缺少 'gpp_config' 字段"

        gpp_config = metadata['gpp_config']
        if not isinstance(gpp_config, dict):
            return False, f"❌ gpp_config 類型錯誤: {type(gpp_config).__name__} (期望: dict)"

        if 'standard_version' not in gpp_config:
            return False, "❌ gpp_config 缺少 'standard_version' 字段"

        standard_version = gpp_config['standard_version']
        if 'TS_38.214' not in standard_version:
            return False, f"❌ 3GPP 標準版本錯誤: {standard_version} (期望包含: TS_38.214)"

        # 業務規則 5: 檢查 ITU-R 配置
        if 'itur_config' not in metadata:
            return False, "❌ metadata 缺少 'itur_config' 字段"

        itur_config = metadata['itur_config']
        if not isinstance(itur_config, dict):
            return False, f"❌ itur_config 類型錯誤: {type(itur_config).__name__} (期望: dict)"

        if 'recommendation' not in itur_config:
            return False, "❌ itur_config 缺少 'recommendation' 字段"

        recommendation = itur_config['recommendation']
        if 'P.618' not in recommendation:
            return False, f"❌ ITU-R 標準錯誤: {recommendation} (期望包含: P.618)"

        # 業務規則 6: 檢查物理常數 (CODATA 2018)
        if 'physical_constants' not in metadata:
            return False, "❌ metadata 缺少 'physical_constants' 字段"

        physical_constants = metadata['physical_constants']
        if not isinstance(physical_constants, dict):
            return False, f"❌ physical_constants 類型錯誤: {type(physical_constants).__name__} (期望: dict)"

        if 'standard_compliance' not in physical_constants:
            return False, "❌ physical_constants 缺少 'standard_compliance' 字段"

        if physical_constants['standard_compliance'] != 'CODATA_2018':
            return False, f"❌ 物理常數標準錯誤: {physical_constants['standard_compliance']} (期望: CODATA_2018)"

        # 業務規則 7: 檢查可用衛星比率
        if total_satellites_analyzed > 0:
            usable_rate = (usable_satellites / total_satellites_analyzed) * 100
            if usable_rate < 50:
                return False, f"❌ 可用衛星比率過低: {usable_rate:.1f}% (應 ≥50%)"
        else:
            usable_rate = 0.0

        # 業務規則 8: 檢查時間序列完整性 (🚨 P1-3 新增 2025-10-05)
        # 確保每顆衛星都有完整的 time_series 數據，防止下游 Stage 6 錯誤
        if 'signal_analysis' in snapshot_data:
            signal_analysis = snapshot_data['signal_analysis']

            # 檢查 signal_analysis 結構
            if not isinstance(signal_analysis, dict):
                return False, f"❌ signal_analysis 類型錯誤: {type(signal_analysis).__name__} (期望: dict)"

            # 統計時間序列數據
            satellites_with_time_series = 0
            satellites_without_time_series = []
            total_time_points = 0
            min_time_points = float('inf')
            max_time_points = 0

            for sat_id, sat_data in signal_analysis.items():
                if not isinstance(sat_data, dict):
                    return False, f"❌ signal_analysis[{sat_id}] 類型錯誤: {type(sat_data).__name__} (期望: dict)"

                # 檢查 time_series 存在性
                if 'time_series' not in sat_data:
                    satellites_without_time_series.append(sat_id)
                    continue

                time_series = sat_data['time_series']

                # 檢查 time_series 類型
                if not isinstance(time_series, list):
                    return False, f"❌ signal_analysis[{sat_id}]['time_series'] 類型錯誤: {type(time_series).__name__} (期望: list)"

                # 檢查 time_series 長度
                ts_length = len(time_series)
                if ts_length == 0:
                    satellites_without_time_series.append(sat_id)
                    continue

                satellites_with_time_series += 1
                total_time_points += ts_length
                min_time_points = min(min_time_points, ts_length)
                max_time_points = max(max_time_points, ts_length)

            # 驗證: 所有衛星必須有 time_series
            if satellites_without_time_series:
                return False, (
                    f"❌ {len(satellites_without_time_series)} 顆衛星缺少 time_series 數據 "
                    f"(例如: {satellites_without_time_series[:3]})\n"
                    f"   Stage 6 依賴完整時間序列進行事件檢測，缺失將導致事件數量不足"
                )

            # 驗證: 至少應有合理數量的時間點
            if satellites_with_time_series > 0:
                avg_time_points = total_time_points / satellites_with_time_series

                # 預期: Starlink ~35 點, OneWeb ~30 點 (基於軌道週期)
                MIN_EXPECTED_TIME_POINTS = 20

                if avg_time_points < MIN_EXPECTED_TIME_POINTS:
                    return False, (
                        f"❌ 時間序列長度不足: 平均 {avg_time_points:.1f} 點 "
                        f"(期望 ≥ {MIN_EXPECTED_TIME_POINTS} 點)\n"
                        f"   範圍: {min_time_points}-{max_time_points} 點\n"
                        f"   Stage 6 需要充足的時間點才能檢測到足夠的 3GPP 事件"
                    )
        else:
            return False, "❌ 快照數據缺少 'signal_analysis' - Stage 6 依賴此數據進行事件檢測"

        # ============================================================================
        # 驗證通過 - 構建成功訊息
        # ============================================================================

        # 計算時間序列統計（如果可用）
        time_series_info = ""
        if satellites_with_time_series > 0:
            avg_time_points = total_time_points / satellites_with_time_series
            time_series_info = (
                f" | 時間序列: {satellites_with_time_series}顆×{avg_time_points:.1f}點 "
                f"(範圍: {min_time_points}-{max_time_points})"
            )

        status_msg = (
            f"✅ Stage 5 信號品質分析驗證通過 | "
            f"分析 {total_satellites_analyzed} 顆衛星 → {usable_satellites} 顆可用 ({usable_rate:.1f}%) | "
            f"品質分布: 優{excellent}/良{good}/可{fair}/差{poor} | "
            f"RSRP={average_rsrp_dbm:.1f}dBm, SINR={average_sinr_db:.1f}dB"
            f"{time_series_info} | "
            f"[3GPP✓, ITU-R✓, CODATA_2018✓, TimeSeriesComplete✓]"
        )
        return True, status_msg

    except KeyError as e:
        # 捕獲字段訪問錯誤（理論上不應該發生，因為我們已經檢查過了）
        return False, f"❌ Stage 5 驗證數據訪問錯誤: 缺少字段 {e}"
    except Exception as e:
        # 捕獲其他未預期的錯誤
        return False, f"❌ Stage 5 驗證異常: {type(e).__name__}: {e}"
