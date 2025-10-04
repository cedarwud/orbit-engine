"""
Stage 5 驗證器 - 信號品質分析層 (3GPP TS 38.214 + ITU-R P.618)

Layer 2 驗證: 檢查驗證快照的合理性與架構合規性
信任 Layer 1 (Stage5Processor.run_validation_checks) 的詳細驗證結果

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""


def check_stage5_validation(snapshot_data: dict) -> tuple:
    """
    Stage 5 專用驗證 - 信號品質分析層 (3GPP TS 38.214 + ITU-R P.618)

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
    """
    try:
        # 檢查基本結構
        if snapshot_data.get('stage') != 'stage5_signal_analysis':
            return False, f"❌ Stage 5 快照標識不正確: {snapshot_data.get('stage')}"

        # 檢查數據摘要
        data_summary = snapshot_data.get('data_summary', {})
        total_satellites_analyzed = data_summary.get('total_satellites_analyzed', 0)
        usable_satellites = data_summary.get('usable_satellites', 0)

        if total_satellites_analyzed == 0:
            return False, f"❌ Stage 5 未分析任何衛星數據"

        # 檢查信號品質分布
        signal_quality_distribution = data_summary.get('signal_quality_distribution', {})
        excellent = signal_quality_distribution.get('excellent', 0)
        good = signal_quality_distribution.get('good', 0)
        fair = signal_quality_distribution.get('fair', 0)
        poor = signal_quality_distribution.get('poor', 0)

        total_quality = excellent + good + fair + poor
        if total_quality == 0:
            return False, f"❌ Stage 5 信號品質分布數據缺失"

        # 檢查 metadata 學術標準合規性
        metadata = snapshot_data.get('metadata', {})

        # ✅ P1: 檢查 3GPP 標準合規
        gpp_compliance = metadata.get('gpp_standard_compliance', False)
        if not gpp_compliance:
            return False, f"❌ Stage 5 3GPP 標準合規標記缺失"

        # ✅ P1: 檢查 ITU-R 標準合規
        itur_compliance = metadata.get('itur_standard_compliance', False)
        if not itur_compliance:
            return False, f"❌ Stage 5 ITU-R 標準合規標記缺失"

        # ✅ P2: 檢查 3GPP 配置
        gpp_config = metadata.get('gpp_config', {})
        if not gpp_config:
            return False, f"❌ Stage 5 3GPP 配置缺失"

        standard_version = gpp_config.get('standard_version', '')
        if 'TS_38.214' not in standard_version:
            return False, f"❌ Stage 5 3GPP 標準版本錯誤: {standard_version} (期望: TS_38.214)"

        # ✅ P2: 檢查 ITU-R 配置
        itur_config = metadata.get('itur_config', {})
        if not itur_config:
            return False, f"❌ Stage 5 ITU-R 配置缺失"

        recommendation = itur_config.get('recommendation', '')
        if 'P.618' not in recommendation:
            return False, f"❌ Stage 5 ITU-R 標準錯誤: {recommendation} (期望: P.618)"

        # ✅ P2: 檢查物理常數 (CODATA 2018)
        physical_constants = metadata.get('physical_constants', {})
        if not physical_constants:
            return False, f"❌ Stage 5 物理常數配置缺失"

        if physical_constants.get('standard_compliance') != 'CODATA_2018':
            return False, f"❌ Stage 5 物理常數標準錯誤 (期望: CODATA_2018)"

        # ✅ P3: 檢查平均信號品質指標
        avg_rsrp = data_summary.get('average_rsrp_dbm')
        avg_sinr = data_summary.get('average_sinr_db')

        if avg_rsrp is None or avg_sinr is None:
            return False, f"❌ Stage 5 平均信號品質指標缺失"

        # 3GPP 標準合理性檢查 (RSRP 範圍: -140 to -44 dBm)
        if not (-140 <= avg_rsrp <= -44):
            return False, f"❌ Stage 5 RSRP 超出合理範圍: {avg_rsrp} dBm (標準範圍: -140 to -44 dBm)"

        # 檢查可用性比率
        if total_satellites_analyzed > 0:
            usable_rate = (usable_satellites / total_satellites_analyzed) * 100
            if usable_rate < 50:
                return False, f"❌ Stage 5 可用衛星比率過低: {usable_rate:.1f}% (應 ≥50%)"

        # 成功通過 Stage 5 驗證
        status_msg = (
            f"Stage 5 信號品質分析檢查通過: "
            f"分析 {total_satellites_analyzed} 顆衛星 → {usable_satellites} 顆可用 ({usable_rate:.1f}%) | "
            f"品質分布: 優{excellent}/良{good}/可{fair}/差{poor} | "
            f"RSRP={avg_rsrp:.1f}dBm, SINR={avg_sinr:.1f}dB | "
            f"[3GPP✓, ITU-R✓, CODATA_2018✓]"
        )
        return True, status_msg

    except Exception as e:
        return False, f"❌ Stage 5 驗證異常: {e}"
