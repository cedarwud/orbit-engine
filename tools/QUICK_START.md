# 🚀 快速開始 - 5 分鐘設置指南

## 步驟 1：首次安裝（只需執行一次）

```bash
# 在專案根目錄執行
make compliance-install
```

**這會自動完成**：
- ✅ 安裝 Git pre-commit hook
- ✅ 設置學術合規性檢查器
- ✅ 創建快捷命令

---

## 步驟 2：日常使用

### 方案 A：自動檢查（推薦）

```bash
# 正常提交，會自動觸發檢查
git add .
git commit -m "your message"
# 👆 如果有違規，會自動阻止並顯示報告
```

### 方案 B：手動檢查

```bash
# 提交前先檢查
make compliance

# 檢查通過後再提交
git add .
git commit -m "your message"
```

### 方案 C：一鍵提交

```bash
# 自動檢查 + 提交
make compliance-commit
```

---

## 步驟 3：如果發現違規

**會看到類似的輸出**：

```
🔴 src/stages/stage4_link_feasibility/example.py:42
   類型: MISSING_SOURCE
   內容: altitude_m = 200.0
   問題: 硬編碼數值缺少來源標記
```

**修正方法**：

```python
# ❌ 修正前
altitude_m = 200.0

# ✅ 修正後
altitude_m = 36.0  # SOURCE: GPS Survey 2025-10-02, WGS84, ±1.0m
```

**重新檢查**：

```bash
make compliance
```

---

## 常見問題

### Q1: 我一定要安裝 hooks 嗎？

**A**: 是的！這是確保學術合規性的關鍵。安裝後：
- 每次 `git commit` 自動檢查
- 發現違規自動阻止提交
- 不需要記得手動檢查

### Q2: hooks 安裝在哪裡？

**A**: `.git/hooks/pre-commit` (專案本地，不會影響其他 Git 專案)

### Q3: 我想臨時跳過檢查怎麼辦？

**A**: **不建議**，但如果真的需要：

```bash
git commit --no-verify -m "message"
```

⚠️ 注意：跳過檢查的 commit 可能在 CI/CD 階段被拒絕

### Q4: 我只想檢查某個目錄怎麼辦？

**A**:

```bash
# 只檢查階段四
make compliance-stage4

# 或手動指定目錄
python tools/academic_compliance_checker.py src/stages/stage4_link_feasibility/
```

### Q5: 檢查器報告太多誤報怎麼辦？

**A**: 目前版本可能有誤報（如「約束」被誤判為「約」）。我們會持續改進。真正的違規示例：

```python
# 🔴 真正的違規
altitude = 200.0  # 估計值
weight = 10  # 經驗權重

# ✅ 合規寫法
altitude = 36.0  # SOURCE: GPS Survey 2025-10-02
# 依據: Chvátal (1979) Set Cover Algorithm
contribution = count_uncovered_points(satellite)
```

---

## 快速命令參考

| 命令 | 說明 | 何時使用 |
|------|------|---------|
| `make compliance-install` | 安裝工具 | 首次設置、更新 hooks |
| `make compliance` | 檢查合規性 | 提交前檢查 |
| `make compliance-commit` | 安全提交 | 自動檢查 + 提交 |
| `make compliance-quick` | 快速檢查 | 快速掃描關鍵字 |
| `make compliance-help` | 顯示幫助 | 忘記命令時 |

---

## 完整工作流程示例

```bash
# 1. 首次設置（只需一次）
make compliance-install

# 2. 開發代碼
vim src/stages/stage4_link_feasibility/example.py

# 3. 提交前檢查
make compliance

# 4. 如果有違規，修正後重新檢查
vim src/stages/stage4_link_feasibility/example.py
make compliance

# 5. 檢查通過，提交
git add .
git commit -m "Fix: 修正 NTPU 座標為實測值"

# 或使用一鍵提交
make compliance-commit
```

---

## 需要幫助？

- 📖 學術標準指南: [docs/ACADEMIC_STANDARDS.md](../docs/ACADEMIC_STANDARDS.md)
- 🔍 失誤分析: [docs/WHY_I_MISSED_ISSUES.md](../docs/WHY_I_MISSED_ISSUES.md)
- 🛠️ 工具文檔: [tools/academic_compliance_checker.py](academic_compliance_checker.py)

---

**記住**: 學術研究的嚴謹性建立在每一個細節上。🎓
