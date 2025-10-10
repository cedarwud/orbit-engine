# Metadata 一致性維護指南

**版本**: v1.0
**創建日期**: 2025-10-01
**目的**: 防止 metadata 聲明與實際數據不一致

---

## 🎯 背景

### 問題起源

在 2025-10-01 的代碼審查中，發現了以下矛盾：

```python
# stage1_main_processor.py (舊版)
metadata['academic_compliance'] = {
    'no_estimated_values': True  # ❌ 聲稱無估算值
}

# constellation_constants.py
tx_power_dbw = 40.0  # ⚠️ 實際上是研究估計值（±3dB）
```

**根本原因**: 修復 RF 參數缺引用問題時，添加了數據來源文檔並誠實標註為「研究估計值」，但忘記同步更新 `academic_compliance` 聲明。

---

## 🔍 問題類型

### 類型 1: 修復創造矛盾

| 修復前 | 修復後 | 結果 |
|--------|--------|------|
| Stage 5 硬編碼 RF 參數（無引用） | 移到 Stage 1，添加完整文檔 | ✅ 提高透明度 |
| Stage 1: `no_estimated_values: True` | Stage 1: `no_estimated_values: True` | ❌ 聲明過時 |

**教訓**: 提高透明度（誠實標註）會暴露舊聲明的矛盾。

### 類型 2: 部分同步

| 應該更新的地方 | 實際是否更新 |
|--------------|------------|
| constellation_constants.py | ✅ 添加引用註釋 |
| RF_PARAMETERS.md | ✅ 創建完整文檔 |
| stage1_main_processor.py | ❌ 忘記更新聲明 |
| stage1-specification.md | ✅ 更新文檔 |

**教訓**: 跨文件修改需要檢查清單確保同步。

---

## ✅ 解決方案

### 1. 代碼層面修復

**升級到 v2.0 三層結構**，區分不同類型的合規性：

```python
# stage1_main_processor.py (新版)
metadata['academic_compliance'] = {
    # TLE 數據層（Stage 1 核心職責）
    'tle_data': {
        'real_data': True,
        'source': 'Space-Track.org',
        'no_estimated_values': True,  # ✅ TLE 確實無估算
        'checksum_algorithm': 'modulo_10_official'
    },
    # 算法層（軌道計算）
    'algorithms': {
        'no_simplified_algorithms': True,
        'sgp4_library': 'skyfield'
    },
    # 系統參數層（RF 配置等）
    'system_parameters': {
        'rf_parameters_status': 'documented_research_estimates',  # ✅ 準確描述
        'rf_parameters_source': 'docs/data_sources/RF_PARAMETERS.md',
        'uncertainty_documented': True,
        'provenance_tracked': True
    }
}
```

**優點**:
- ✅ 語義清晰（區分數據、算法、參數）
- ✅ 誠實透明（RF 參數標註為估計值）
- ✅ 可擴展（未來添加新層級）

---

### 2. 自動化檢查

**創建 `validate_metadata_consistency.py` 腳本**：

```bash
# 運行檢查
python tools/validate_metadata_consistency.py

# 輸出範例
============================================================
📋 Metadata 一致性驗證
============================================================

🔍 檢查 academic_compliance 結構...
   ✅ 使用 v2.0 結構（三層分離）

🔍 檢查 RF 參數文檔...
   📡 starlink 包含 RF 參數
   📡 oneweb 包含 RF 參數

✅ 所有檢查通過！Metadata 一致性良好。
```

**功能**:
1. 檢測舊版結構矛盾（`no_estimated_values: True` 但包含 RF 參數）
2. 驗證 v2.0 結構完整性
3. 檢查 RF 參數文檔存在性
4. 驗證 constellation_constants 與快照一致性

---

### 3. 開發流程改進

**創建 `CODE_REVIEW_CHECKLIST.md`**，包含：

#### 階段 1: 修改前規劃
- [ ] 影響範圍分析
- [ ] 向後兼容性檢查
- [ ] 學術合規性確認

#### 階段 2: 修改實施
- [ ] 代碼實現
- [ ] 數據溯源（新參數必須有引用）
- [ ] 測試覆蓋

#### 階段 3: 一致性檢查 ⚠️ **關鍵步驟**
- [ ] 運行 `validate_metadata_consistency.py`
- [ ] 檢查 `academic_compliance` 聲明
- [ ] 驗證文檔同步
- [ ] 跨階段驗證

#### 階段 4: 提交前檢查
- [ ] 代碼質量
- [ ] Git 提交規範
- [ ] 最終驗證

---

## 🛠️ 使用指南

### 日常開發

```bash
# 1. 修改代碼前：閱讀檢查清單
cat docs/development/CODE_REVIEW_CHECKLIST.md

# 2. 修改代碼後：運行一致性檢查
python tools/validate_metadata_consistency.py

# 3. 修改通過後：運行完整測試
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py --stage 1
```

### CI/CD 集成

在 `.github/workflows/ci.yml` 添加：

```yaml
- name: Metadata 一致性檢查
  run: |
    python tools/validate_metadata_consistency.py
    if [ $? -ne 0 ]; then
      echo "❌ Metadata 一致性檢查失敗"
      exit 1
    fi
```

### Git Hook

在 `.git/hooks/pre-commit` 添加：

```bash
#!/bin/bash
python tools/validate_metadata_consistency.py || exit 1
```

---

## 📊 檢查矩陣

| 檢查項目 | 工具 | 時機 | 必須 |
|---------|------|------|------|
| **Metadata 結構** | `validate_metadata_consistency.py` | 修改後 | ✅ 是 |
| **RF 參數文檔** | 自動檢查腳本 | 添加參數時 | ✅ 是 |
| **一致性驗證** | 自動檢查腳本 | 提交前 | ✅ 是 |
| **完整流程測試** | `run_six_stages_with_validation.py` | 提交前 | ✅ 是 |
| **代碼風格** | flake8/black | 提交前 | ⚠️ 建議 |

---

## 🎓 最佳實踐

### 1. 語義精確性

```python
# ❌ 不精確：籠統的聲明
'no_estimated_values': True  # 什麼數據？什麼層級？

# ✅ 精確：分層描述
'tle_data': {'no_estimated_values': True}  # 明確指 TLE 數據
'system_parameters': {'rf_parameters_status': 'documented_research_estimates'}
```

### 2. 誠實標註

```python
# ❌ 過度聲稱
tx_power_dbw = 40.0  # 官方規格 ← 實際是推算值

# ✅ 誠實標註
tx_power_dbw = 40.0  # 基於FCC文件推算，±3dB不確定性
```

### 3. 可追溯性

```python
# ❌ 無法驗證
'rf_parameters': 'official_specs'

# ✅ 可追溯
'rf_parameters_status': 'documented_research_estimates',
'rf_parameters_source': 'docs/data_sources/RF_PARAMETERS.md',
'rf_parameters_version': 'v1.0',
'rf_parameters_date': '2025-10-01'
```

---

## 🔄 遷移指南

### 從舊版遷移到 v2.0

**步驟 1**: 檢查當前狀態

```bash
python tools/validate_metadata_consistency.py
```

如果輸出：
```
⚠️ 使用舊版結構（單層）
❌ 矛盾：constellation_configs 包含 RF 參數...
```

**步驟 2**: 更新 `stage1_main_processor.py`

將舊版：
```python
metadata['academic_compliance'] = {
    'real_tle_data': True,
    'no_estimated_values': True
}
```

替換為新版（見上述代碼範例）

**步驟 3**: 重新生成驗證快照

```bash
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py --stage 1
```

**步驟 4**: 驗證遷移成功

```bash
python tools/validate_metadata_consistency.py
# 應輸出：✅ 所有檢查通過！
```

---

## 📚 相關文檔

- [代碼審查檢查清單](CODE_REVIEW_CHECKLIST.md)
- [RF 參數數據來源](../data_sources/RF_PARAMETERS.md)
- [學術標準合規指南](../stages/stage1-specification.md)

---

## 🐛 故障排除

### Q: 檢查腳本報錯「無法載入快照」

**A**: 確保已運行 Stage 1 生成驗證快照：
```bash
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py --stage 1
```

### Q: 報錯「矛盾：包含 RF 參數但聲稱無估算值」

**A**: 需要升級到 v2.0 結構，見上述遷移指南。

### Q: 報錯「RF_PARAMETERS.md 不存在」

**A**: 如果代碼包含 RF 參數，必須創建數據來源文檔。參考現有的 `docs/data_sources/RF_PARAMETERS.md` 作為模板。

---

**維護者**: Orbit Engine Team
**反饋**: 如發現問題或改進建議，請提交 issue
