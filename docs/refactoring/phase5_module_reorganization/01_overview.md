# Phase 5: 模塊重組 - 概述

**優先級**: 🟡 P2 (可以執行)
**預估時間**: 2-3 天
**風險等級**: 🟠 中高
**依賴關係**: Phase 1-4 完成

---

## 📋 問題描述

`src/shared/` 模塊職責不清晰：
- `utils/` 太寬泛
- `validation_framework/` 有冗餘
- 部分驗證器位置錯誤

---

## 🎯 解決方案

重組為:
```
src/shared/
├── base/              # 基礎類和接口
├── constants/         # 常量（保持不變）
├── coordinate_systems/ # 座標系統（整合）
├── validation/        # 驗證框架（重構）
├── configs/           # 配置管理（新增）
└── utils/             # 通用工具（精簡）
```

---

## 📊 預期收益

- 模塊職責清晰
- 減少耦合
- 代碼減少: 1500行 → 1300行 (-13%)

---

## ⚠️ 風險

影響範圍廣，需要更新所有import路徑。
建議使用deprecation警告逐步遷移。

---

## 相關文檔

- [02_directory_structure.md](02_directory_structure.md)
- [03_migration_strategy.md](03_migration_strategy.md)

**狀態**: 📋 待開始
