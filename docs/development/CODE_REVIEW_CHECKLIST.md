# 代碼審查檢查清單

**版本**: v1.0
**最後更新**: 2025-10-01
**目的**: 防止修復創造新問題，確保代碼質量和一致性

---

## 🎯 使用時機

### 必須使用此清單的情況：
- ✅ 修改數據結構或 schema
- ✅ 添加/修改 metadata 字段
- ✅ 重構階段間接口
- ✅ 修復學術合規性問題
- ✅ 更新配置文件（constellation_constants 等）

### 可選使用的情況：
- Bug 修復（不涉及接口變更）
- 性能優化（不改變數據格式）
- 日誌/註釋更新

---

## 📋 檢查清單

### 階段 1: 修改前規劃

- [ ] **1.1 影響範圍分析**
  - [ ] 列出所有會直接修改的文件
  - [ ] 列出所有會間接影響的文件（依賴關係）
  - [ ] 識別所有相關的 metadata 聲明

- [ ] **1.2 向後兼容性**
  - [ ] 確認是否破壞現有接口
  - [ ] 計劃數據遷移策略（如需要）
  - [ ] 檢查下游階段的依賴

- [ ] **1.3 學術合規性**
  - [ ] 確認修改不違反零容忍原則
  - [ ] 計劃數據來源文檔更新（如添加新參數）

---

### 階段 2: 修改實施

- [ ] **2.1 代碼實現**
  - [ ] 遵循現有代碼風格
  - [ ] 添加必要的註釋（特別是估算值/假設）
  - [ ] 保持單一職責原則

- [ ] **2.2 數據溯源**
  - [ ] 新增參數必須有來源說明
  - [ ] 估算值必須標註不確定性
  - [ ] 引用具體文檔（FCC 文件編號、論文 DOI 等）

- [ ] **2.3 測試覆蓋**
  - [ ] 添加單元測試（新增功能）
  - [ ] 更新集成測試（接口變更）
  - [ ] 手動驗證關鍵路徑

---

### 階段 3: 一致性檢查 ⚠️ **關鍵步驟**

- [ ] **3.1 Metadata 一致性**
  - [ ] 運行自動化檢查腳本：
    ```bash
    python scripts/validate_metadata_consistency.py
    ```
  - [ ] 檢查 `academic_compliance` 聲明是否準確
  - [ ] 驗證所有聲稱的數據來源都可驗證

- [ ] **3.2 文檔同步**
  - [ ] 更新階段規範文檔（stage*-specification.md）
  - [ ] 更新數據流文檔（如修改接口）
  - [ ] 更新 RF_PARAMETERS.md（如修改射頻參數）

- [ ] **3.3 跨階段驗證**
  - [ ] 檢查下游階段是否能正確消費新數據
  - [ ] 驗證快照格式完整性
  - [ ] 運行完整流程測試（Stage 1-6）

---

### 階段 4: 提交前檢查

- [ ] **4.1 代碼質量**
  - [ ] 移除調試代碼和註釋掉的代碼
  - [ ] 確認無 TODO/FIXME（或已記錄到 issue）
  - [ ] 檢查無硬編碼路徑/值

- [ ] **4.2 Git 提交**
  - [ ] Commit message 清晰描述修改內容
  - [ ] 分離無關修改（一個 commit 做一件事）
  - [ ] 添加相關 issue 引用

- [ ] **4.3 最終驗證**
  - [ ] 重新運行所有測試
  - [ ] 檢查 git diff（確認無意外修改）
  - [ ] 驗證文檔渲染正確（Markdown 格式）

---

## 🔍 常見陷阱與檢查要點

### 陷阱 1: 修改創造矛盾

**情境**: 添加新參數但忘記更新相關聲明

**檢查要點**:
- [ ] 如果添加 RF 參數，是否更新 `academic_compliance`？
- [ ] 如果修改數據格式，是否更新文檔中的範例？
- [ ] 如果更改配置，是否同步所有使用該配置的地方？

**案例**:
```python
# ❌ 錯誤：添加估算值但聲稱無估算
constellation_configs['starlink']['tx_power_dbw'] = 40.0  # 估算值
metadata['academic_compliance']['no_estimated_values'] = True  # 矛盾！

# ✅ 正確：準確反映數據性質
metadata['academic_compliance'] = {
    'system_parameters': {
        'rf_parameters_status': 'documented_research_estimates'
    }
}
```

---

### 陷阱 2: 部分更新

**情境**: 只更新代碼，忘記更新文檔

**檢查要點**:
- [ ] 代碼中移除的參數，是否也從文檔中移除？
- [ ] 新增的驗證邏輯，是否更新文檔中的驗證章節？
- [ ] 修改的接口，是否更新 API 文檔和範例？

---

### 陷阱 3: 假設下游行為

**情境**: 修改輸出格式，假設下游會自動適配

**檢查要點**:
- [ ] 測試所有下游階段是否能處理新格式
- [ ] 檢查是否有隱式依賴（如欄位順序）
- [ ] 驗證錯誤處理路徑（缺少欄位時的行為）

---

## 🛠️ 自動化工具

### 運行所有檢查

```bash
# 1. Metadata 一致性檢查
python scripts/validate_metadata_consistency.py

# 2. 運行完整流程測試
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py --stages 1-6

# 3. 檢查代碼風格（如有配置）
# flake8 src/
# black --check src/
```

### 集成到 Git Hook

在 `.git/hooks/pre-commit` 添加：

```bash
#!/bin/bash
echo "🔍 運行 Metadata 一致性檢查..."
python scripts/validate_metadata_consistency.py

if [ $? -ne 0 ]; then
    echo "❌ Metadata 檢查失敗，請修正後再提交"
    exit 1
fi
```

---

## 📊 檢查清單總結

| 階段 | 關鍵步驟 | 工具 |
|------|---------|------|
| **修改前** | 影響範圍分析 | 手動 |
| **修改中** | 數據溯源、註釋 | 手動 |
| **修改後** | Metadata 一致性 | `validate_metadata_consistency.py` |
| **提交前** | 完整流程測試 | `run_six_stages_with_validation.py` |

---

## 🎓 最佳實踐

### 1. 小步提交
- ✅ 一次修改解決一個問題
- ✅ 每個 commit 都能獨立運行
- ❌ 避免大型重構 + 功能添加混合

### 2. 文檔優先
- ✅ 修改代碼前先更新設計文檔
- ✅ 代碼註釋解釋「為什麼」而非「做什麼」
- ✅ 複雜邏輯附帶範例

### 3. 防禦性編程
- ✅ 添加參數驗證（類型、範圍）
- ✅ 明確錯誤訊息
- ✅ 記錄假設和限制

### 4. 可追溯性
- ✅ 引用具體的規範文檔（FCC 文件編號、3GPP 章節）
- ✅ 標註數據來源和查詢日期
- ✅ 記錄不確定性和局限性

---

## 📚 相關文檔

- [學術標準合規指南](../stages/stage1-specification.md#學術標準合規)
- [RF 參數數據來源](../data_sources/RF_PARAMETERS.md)
- [驗證框架設計](../stages/stage1-specification.md#驗證架構設計)

---

**維護者**: Orbit Engine Team
**反饋**: 如發現檢查清單遺漏，請提交 issue
