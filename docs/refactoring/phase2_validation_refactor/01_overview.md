# Phase 2: 驗證邏輯重組 - 概述

**優先級**: 🟠 P1 (應該執行)
**預估時間**: 2-3 天
**風險等級**: 🟡 中
**依賴關係**: Phase 1 完成

---

## 📋 問題描述

驗證邏輯分散在3處，職責重疊：

1. **處理器內部驗證** (`processor.validate_input/validate_output`)
2. **快照驗證器** (`scripts/stage_validators/stageN_validator.py`)
3. **專用合規驗證器** (部分階段有，如 Stage 5)

**問題**:
- 職責不清晰（epoch檢查在多處重複）
- 命名不一致
- 維護困難

---

## 🎯 解決方案：三層驗證架構

```
Layer 1: 數據結構驗證 (BaseStageProcessor)
  → 檢查字段存在性、類型正確性
  → 時機: 處理前後立即執行

Layer 2: 學術合規驗證 (StageComplianceValidator)
  → 檢查ITU-R/3GPP參數範圍
  → 時機: 處理器內調用

Layer 3: 回歸測試驗證 (scripts/stage_validators)
  → 檢查衛星數量一致性、格式
  → 時機: 管道執行完成後
```

---

## 📊 預期收益

- 代碼減少: 1200行 → 800行 (-33%)
- 職責清晰化
- 維護性提升

---

## 相關文檔

- [02_three_layer_architecture.md](02_three_layer_architecture.md)
- [03_compliance_validator_base.md](03_compliance_validator_base.md)

**狀態**: 📋 待開始
