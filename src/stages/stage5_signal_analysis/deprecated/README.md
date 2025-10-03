# Deprecated Modules - Stage 5

## 已棄用模組說明

本目錄包含已棄用或移至其他階段的模組。

### gpp_event_detector_moved_to_stage6.py

**原檔名**: `gpp_event_detector.py`
**棄用日期**: 2025-10-03
**棄用理由**: 
- 3GPP 換手事件檢測器（A4/A5/D2）
- 屬於即時系統特性，不適合歷史資料重現研究
- 已移至 Stage 6 研究優化層

**移動原因**:
- Stage 5 專注於信號品質計算（RSRP/RSRQ/SINR）
- 事件檢測屬於動態換手決策，適合 Stage 6

**參考**:
- 審查報告: `docs/STAGE5_OVER_ENGINEERING_AUDIT.md`
- Stage 6 實現: `src/stages/stage6_research_optimization/gpp_event_detector.py`
