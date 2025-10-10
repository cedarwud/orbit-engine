# 文檔同步防護機制使用指南

**目的**: 防止文檔與代碼脫鉤，確保 AI 助手不會因文檔錯誤聲明而犯錯

**創建日期**: 2025-10-01
**適用範圍**: 所有 Stage 文檔

---

## 🎯 問題背景

### AI 助手曾犯的錯誤

在 2025-10-01 的文檔同步檢查中，AI 助手犯了以下錯誤：

1. **假設驗證已實現**: 看到文檔列出 6 項驗證，就假設都已實現，沒有核對驗證腳本
2. **過度專注主要問題**: 只修正了"階段 4.2 是否實現"，忽略了驗證框架的細節
3. **缺乏驗證依據**: 沒有快速的方法驗證"文檔聲稱的功能是否真的存在"

### 根本原因

- **文檔與代碼脫鉤**: 文檔聲稱有功能，但沒有指向實際代碼位置
- **單一真相來源缺失**: 沒有權威的狀態記錄文件
- **缺乏自動化驗證**: 依賴人工檢查，容易遺漏

---

## ✅ 四層防護機制

### 🛡️ **第 1 層：驗證狀態矩陣 (唯一真相來源)**

**文件**: `docs/stages/STAGE4_VERIFICATION_MATRIX.md`

**用途**: 作為驗證狀態的**唯一真相來源**，明確記錄每項功能的實現與驗證狀態

**內容**:
```markdown
| # | 驗證項目 | 代碼實現位置 | 驗證腳本位置 | 強制執行 | 狀態 | 最後驗證 |
|---|---------|------------|------------|---------|------|---------|
| 6 | stage_4_2_pool_optimization | pool_optimizer.py:1-535 | run_six_stages_with_validation.py:746-801 | ✅ | ✅ 已實現 | 2025-10-01 |
```

**使用規則**:
- ✅ **此文件是驗證狀態的唯一真相來源**
- ❌ 其他文檔不得重複聲明驗證狀態
- ✅ AI 助手檢查驗證狀態時**必須先讀取此文件**

---

### 🛡️ **第 2 層：主文檔引用指令**

**文件**: `docs/stages/stage4-link-feasibility.md`

**添加內容**:
```markdown
## 🔬 驗證框架

⚠️ **唯一真相來源**: 驗證狀態請查閱 [STAGE4_VERIFICATION_MATRIX.md](./STAGE4_VERIFICATION_MATRIX.md)

🤖 **AI 助手注意**: 檢查驗證狀態時，**必須先讀取 STAGE4_VERIFICATION_MATRIX.md**，
禁止假設本文檔聲稱的功能都已實現。
```

**目的**:
- 提醒 AI 助手查閱矩陣文件
- 防止 AI 直接相信主文檔聲稱的狀態

---

### 🛡️ **第 3 層：驗證腳本映射註釋**

**文件**: `scripts/run_six_stages_with_validation.py`

**添加內容**:
```python
# Stage 4 專用檢查 - 鏈路可行性評估與時空錯置池規劃
#
# ⚠️ 驗證狀態映射 (參考: docs/stages/STAGE4_VERIFICATION_MATRIX.md)
# ✅ 已實現: #6 stage_4_2_pool_optimization (本段代碼 746-801 行)
# ❌ 未實現: #1 constellation_threshold_validation
# ❌ 未實現: #2 visibility_calculation_accuracy
# ❌ 未實現: #3 link_budget_constraints
# ❌ 未實現: #4 ntpu_coverage_analysis
# ❌ 未實現: #5 service_window_optimization
elif stage_num == 4:
    # 實際驗證代碼...
```

**目的**:
- 在代碼中明確標記哪些驗證已實現
- 方便 AI 助手快速核對
- 提供反向引用到矩陣文件

---

### 🛡️ **第 4 層：自動化驗證工具**

**文件**: `scripts/verify_documentation_sync.py`

**功能**:
1. 讀取驗證矩陣 (唯一真相來源)
2. 讀取主文檔聲稱的驗證項目
3. 讀取驗證腳本實際實現
4. 交叉驗證三個來源的一致性
5. 報告不一致問題

**使用方法**:
```bash
# 驗證 Stage 4 文檔同步性
python3 scripts/verify_documentation_sync.py --stage 4

# 輸出範例:
# ✅ 所有檢查通過！文檔與代碼完全同步。
# 或
# ❌ 發現不一致問題，請修正後再提交。
```

**集成到 CI/CD**:
```yaml
# .github/workflows/doc-sync.yml
- name: Verify Documentation Sync
  run: python3 scripts/verify_documentation_sync.py --stage 4
```

---

## 📝 工作流程

### **添加新驗證項目時**

1. **更新驗證矩陣** (`STAGE4_VERIFICATION_MATRIX.md`)
   ```markdown
   | 7 | new_validation | processor.py:100-150 | ❌ 無 | ❌ | ⚠️ **未驗證** | - |
   ```

2. **實現驗證邏輯** (`run_six_stages_with_validation.py`)
   ```python
   # 添加實際驗證代碼
   def validate_new_feature(data):
       # ...驗證邏輯
   ```

3. **更新腳本註釋**
   ```python
   # ✅ 已實現: #7 new_validation (本段代碼 850-900 行)
   ```

4. **更新矩陣狀態**
   ```markdown
   | 7 | new_validation | processor.py:100-150 | run_six_stages_with_validation.py:850-900 | ✅ | ✅ **已實現** | 2025-10-01 |
   ```

5. **運行驗證工具**
   ```bash
   python3 scripts/verify_documentation_sync.py --stage 4
   ```

---

### **AI 助手檢查驗證狀態時**

**❌ 錯誤做法** (導致之前的失誤):
```
1. 讀取 stage4-link-feasibility.md
2. 看到列出 6 項驗證
3. 假設都已實現 ❌
```

**✅ 正確做法** (新的工作流程):
```
1. 首先讀取 STAGE4_VERIFICATION_MATRIX.md (唯一真相來源)
2. 查看"狀態"欄: ✅ 已實現 or ⚠️ 未驗證
3. 如需確認，查看"驗證腳本位置"欄的代碼行號
4. 如有疑問，運行 verify_documentation_sync.py 驗證
```

---

## 🚨 關鍵原則

### 單一真相來源 (Single Source of Truth)

| 問題 | 答案來源 |
|------|---------|
| 某個驗證是否已實現？ | **STAGE4_VERIFICATION_MATRIX.md** |
| 驗證代碼在哪裡？ | **STAGE4_VERIFICATION_MATRIX.md** "驗證腳本位置"欄 |
| 代碼邏輯在哪裡？ | **STAGE4_VERIFICATION_MATRIX.md** "代碼實現位置"欄 |

### 禁止的做法

- ❌ 在主文檔中聲稱驗證狀態而不引用矩陣
- ❌ 假設文檔聲稱的功能都已實現
- ❌ 不運行驗證工具就提交文檔修改

### 強制的做法

- ✅ 修改驗證狀態時必須更新矩陣文件
- ✅ AI 助手檢查狀態時必須先讀矩陣
- ✅ 提交前必須運行 `verify_documentation_sync.py`

---

## 🎯 效果驗證

### 測試案例：AI 助手檢查驗證狀態

**場景**: 用戶問"Stage 4 的所有驗證項目都實現了嗎？"

**之前的行為** (容易犯錯):
```
AI: 讀取 stage4-link-feasibility.md
AI: 看到列出 6 項驗證
AI: 回答"是的，6 項驗證都已實現" ❌ 錯誤
```

**現在的行為** (防護機制生效):
```
AI: 看到文檔頂部提醒"唯一真相來源: STAGE4_VERIFICATION_MATRIX.md"
AI: 讀取 STAGE4_VERIFICATION_MATRIX.md
AI: 查看表格"狀態"欄
AI: 發現只有 1 項 ✅ 已實現，5 項 ⚠️ 未驗證
AI: 回答"不，只有 #6 pool_optimization 已實現並強制執行，
     前 5 項驗證代碼已存在但驗證腳本未實現" ✅ 正確
```

---

## 📊 維護檢查清單

### 每次修改 Stage 4 代碼後

- [ ] 更新 `STAGE4_VERIFICATION_MATRIX.md` (如果驗證狀態改變)
- [ ] 運行 `python3 scripts/verify_documentation_sync.py --stage 4`
- [ ] 確認輸出 "✅ 所有檢查通過"

### 每月定期檢查

- [ ] 檢查矩陣中"最後驗證"欄是否過期
- [ ] 重新運行所有驗證項目
- [ ] 更新"最後驗證"日期

---

## 🔮 未來擴展

### 擴展到其他 Stage

1. 創建 `STAGE{N}_VERIFICATION_MATRIX.md`
2. 在 `verify_documentation_sync.py` 添加對應驗證邏輯
3. 在主文檔添加引用指令
4. 在驗證腳本添加映射註釋

### 自動化程度提升

- [ ] Pre-commit hook: 提交前自動運行驗證工具
- [ ] CI/CD 集成: PR 時自動檢查文檔同步性
- [ ] 定期報告: 每週生成文檔健康度報告

---

## 📚 參考文件

- 驗證矩陣: `docs/stages/STAGE4_VERIFICATION_MATRIX.md`
- 主文檔: `docs/stages/stage4-link-feasibility.md`
- 驗證腳本: `scripts/run_six_stages_with_validation.py`
- 同步驗證工具: `scripts/verify_documentation_sync.py`

---

**維護負責**: Orbit Engine Team
**最後更新**: 2025-10-01
**版本**: v1.0
