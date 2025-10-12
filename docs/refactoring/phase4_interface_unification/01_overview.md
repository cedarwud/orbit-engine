# Phase 4: 接口統一 - 概述

**優先級**: 🟡 P2 (可以執行)
**預估時間**: 1-2 天
**風險等級**: 🟡 中
**依賴關係**: Phase 1, 2 完成

---

## 📋 問題描述

Stage 5/6 重寫了 `execute()` 方法，違反 Template Method Pattern。

當前:
```python
class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    def execute(self, input_data):
        # 完全重寫，沒有調用super()
```

---

## 🎯 解決方案

統一使用 `process()` 方法:

```python
class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    def process(self, input_data):
        # 只實現主邏輯
        # 基類自動處理驗證和快照
```

---

## 📊 預期收益

- 接口一致性
- 自動獲得基類功能（驗證、快照、錯誤處理）

---

## 相關文檔

- [02_stage5_migration.md](02_stage5_migration.md)
- [03_stage6_migration.md](03_stage6_migration.md)

**狀態**: 📋 待開始
