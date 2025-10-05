# ML 文檔清理計劃

**日期**: 2025-10-05
**目的**: 移除 ML 相關代碼後，同步清理所有文檔中的 ML 引用
**範圍**: 所有階段文檔 + 項目級文檔

---

## 📊 ML 引用統計

### 文檔中的 ML 引用次數

| 文檔 | ML 引用次數 | 清理優先級 |
|------|-------------|-----------|
| **stage6-research-optimization.md** | 40 次 | **CRITICAL** |
| **stage5-signal-analysis.md** | 7 次 | HIGH |
| **stage1-specification.md** | 3 次 | MEDIUM |
| **stage4-link-feasibility.md** | 2 次 | LOW |
| **final.md** | 未統計 | MEDIUM |
| **STAGES_OVERVIEW.md** | 未統計 | HIGH |

---

## 🎯 清理策略

### 策略 A: 完全移除 ML 引用 ❌ **不推薦**

**理由**:
- ML 是未來研究方向，應保留說明
- 文檔應指引未來工作，而非僅描述當前狀態

### 策略 B: 標註為"未來工作" ✅ **推薦**

**理由**:
- 保留研究完整性
- 明確說明 ML 不在六階段範圍內
- 指向獨立 ML 工具（未來實現）

---

## 📝 具體清理方案

### 1. **Stage 6 文檔** - CRITICAL 清理

**文件**: `docs/stages/stage6-research-optimization.md`

#### 需要修改的章節

##### 1.1 核心職責 (Line 4-18)

**原文**:
```markdown
**核心職責**: 3GPP NTN 事件檢測與強化學習訓練數據生成
**輸出**: 3GPP NTN 事件數據 + 強化學習訓練集
**學術標準**: 3GPP TS 38.331 標準事件檢測，支援多種 ML 算法
```

**修改為**:
```markdown
**核心職責**: 3GPP NTN 事件檢測與動態池驗證
**輸出**: 3GPP NTN 事件數據 (A3/A4/A5/D2)
**學術標準**: 3GPP TS 38.331 v18.5.1 標準事件檢測

**未來工作**: 強化學習訓練數據生成
  - 定位: 獨立於六階段的 ML 研究工具
  - 路徑: `tools/ml_training_data_generator/` (待實現)
  - 依據: 基於 Stage 6 的 3GPP 事件數據
```

##### 1.2 Stage 6 職責說明 (Line 10-18)

**刪除**:
```markdown
- **ML 訓練數據**: 為 DQN/A3C/PPO/SAC 算法準備訓練集
```

**保留並標註**:
```markdown
**當前職責** (六階段核心):
1. 3GPP 事件檢測 (A3/A4/A5/D2)
2. 動態池驗證 (維持覆蓋率 > 95%)
3. 換手決策評估 (基於 3GPP 標準)

**未來擴展** (獨立 ML 工具):
- ML 訓練數據生成 (DQN/A3C/PPO/SAC)
- 詳見: `tools/ml_training_data_generator/README.md` (待實現)
```

##### 1.3 架構圖 (Line 38-96)

**修改架構圖**:
```markdown
## Stage 6 核心架構

┌─────────────────────────────────────────────────────┐
│                Stage 6 處理器                        │
├─────────────────────────────────────────────────────┤
│  ① 3GPP Event Detector                              │ ✅ 核心
│     - A3/A4/A5/D2 事件檢測                          │
│     - 基於 3GPP TS 38.331 標準                      │
│                                                     │
│  ② Satellite Pool Verifier                         │ ✅ 核心
│     - 動態池維持驗證                                │
│     - 覆蓋率監控 (> 95%)                            │
│                                                     │
│  ③ Handover Decision Evaluator                     │ ✅ 核心
│     - 換手決策評估                                  │
│     - 基於 3GPP 標準參數                            │
└─────────────────────────────────────────────────────┘
         ↓ 輸出: 3GPP 事件 JSON
         ↓
┌─────────────────────────────────────────────────────┐
│  未來工作: ML Training Data Generator (獨立)        │ ⏳ 待實現
│  - 基於 Stage 6 輸出生成 RL 訓練集                  │
│  - 詳見: tools/ml_training_data_generator/          │
└─────────────────────────────────────────────────────┘
```

##### 1.4 ML 訓練數據章節 (Line 425-870)

**不刪除，改為"未來工作"章節**:
```markdown
## ML 訓練數據生成 (未來工作)

> ⚠️ **注意**: 此功能已移至獨立 ML 工具 `tools/ml_training_data_generator/`
>
> **狀態**: 規劃中，待六階段論文完成後實現
>
> **設計文檔**: 參考 `archive/ml_modules_backup_20251005/design_docs/`

### 設計概念 (保留供未來參考)

ML 訓練數據生成將基於 Stage 6 的 3GPP 事件數據，生成強化學習訓練集。

#### 狀態空間設計 (草案)
```python
state_vector = [
    rsrp_dbm,           # 當前 RSRP
    rsrq_db,            # 當前 RSRQ
    rs_sinr_db,         # 當前 SINR
    distance_km,        # 衛星距離
    elevation_deg,      # 仰角
    velocity_kmh,       # 相對速度 (需計算)
    handover_count      # 換手次數 (從 3GPP 事件統計)
]
```

#### 動作空間設計 (草案)
基於 3GPP 事件的動態動作空間:
- A3 事件 → handover_to_best_neighbor
- A4 事件 → handover_to_candidates
- A5 事件 → emergency_handover
- 無事件 → maintain

#### 獎勵函數設計 (草案)
基於衛星換手論文 (Liu et al. 2020, Zhang et al. 2021):
- QoS 維持: +1.0
- 換手成功: +0.5
- 換手失敗: -1.0
- 不必要換手: -0.2

**詳細設計**: 待文獻調查後確定
```

##### 1.5 Checklist (Line 1034)

**刪除**:
```markdown
- [ ] 50,000+ ML 訓練樣本生成
```

**或改為**:
```markdown
- [ ] ~~50,000+ ML 訓練樣本生成~~ (移至獨立 ML 工具)
```

---

### 2. **Stage 5 文檔** - HIGH 清理

**文件**: `docs/stages/stage5-signal-analysis.md`

#### 需要修改的位置

##### 2.1 非職責說明 (Line 127)

**原文**:
```markdown
- ❌ **ML 數據**: 強化學習訓練數據 (移至 Stage 6)
```

**修改為**:
```markdown
- ❌ **ML 訓練數據生成**: 獨立於六階段 (詳見 `tools/ml_training_data_generator/`)
```

##### 2.2 數據流說明 (Line 651-676)

**原文**:
```markdown
# ML 訓練數據生成
RSRP/RSRQ/SINR 數據
    ↓
    → Stage 6 ML 訓練數據生成 (狀態空間/獎勵函數)
```

**修改為**:
```markdown
# 3GPP 事件檢測 (Stage 6)
RSRP/RSRQ/SINR 數據
    ↓
    → Stage 6 3GPP 事件檢測 (A3/A4/A5/D2)
    → (未來) ML 工具基於事件生成訓練集
```

##### 2.3 輸出用途 (Line 676)

**原文**:
```markdown
- **ML 訓練**: 需要完整的信號品質指標組合
```

**修改為**:
```markdown
- **3GPP 事件檢測**: 需要完整的信號品質指標組合 (RSRP/RSRQ/SINR)
- **未來 ML 應用**: 可基於信號品質數據生成訓練集 (獨立工具)
```

---

### 3. **Stage 1 文檔** - MEDIUM 清理

**文件**: `docs/stages/stage1-specification.md`

#### 需要修改的位置

##### 3.1 時間窗口用途 (Line 179)

**原文**:
```markdown
- **用途區分**: 衛星池規劃用 ±24h，強化學習訓練可禁用或 ±12h/天
```

**修改為**:
```markdown
- **用途區分**: 衛星池規劃用 ±24h，研究分析可調整為 ±12h/天
- **未來 ML 研究**: 可配置更短時間窗口 (±6h) 提升訓練速度
```

##### 3.2 配置參數 (Line 642)

**原文**:
```python
'reinforcement_learning_training': True  # ML 訓練數據生成
```

**修改為**:
```python
# 'reinforcement_learning_training': True  # ⚠️ 已移除，ML 工具獨立實現
```

或直接刪除此行。

---

### 4. **Stage 4 文檔** - LOW 清理

**文件**: `docs/stages/stage4-link-feasibility.md`

#### 需要修改的位置

##### 4.1 非職責說明 (Line 287)

**原文**:
```markdown
- ❌ **ML 訓練**: 強化學習數據生成 (移至 Stage 6)
```

**修改為**:
```markdown
- ❌ **ML 訓練數據生成**: 獨立於六階段 (未來工作)
```

##### 4.2 數據流 (Line 563)

**原文**:
```markdown
→ Stage 6 研究數據生成 (3GPP 事件 + ML 訓練)
```

**修改為**:
```markdown
→ Stage 6 研究數據生成 (3GPP 事件檢測)
→ (未來) ML 工具基於 Stage 6 輸出生成訓練集
```

---

### 5. **項目級文檔** - MEDIUM 清理

#### 5.1 `docs/final.md`

**檢查並修改**:
```bash
grep -n "ML\|強化學習" docs/final.md
```

**預期修改**:
- 研究目標: 保留 ML 作為未來方向
- 實施範圍: 明確六階段不包含 ML 實現

#### 5.2 `docs/stages/STAGES_OVERVIEW.md`

**檢查並修改**:
```bash
grep -n "ML\|強化學習" docs/stages/STAGES_OVERVIEW.md
```

**預期修改**:
- Stage 6 描述: 移除 ML 訓練數據生成
- 新增"未來工作"章節: 說明 ML 工具計劃

---

## 🔧 自動化清理腳本

```bash
#!/bin/bash
# ml_doc_cleanup.sh - 自動清理 ML 文檔引用

echo "開始清理 ML 文檔引用..."

# 1. 備份所有文檔
mkdir -p archive/docs_backup_20251005
cp -r docs archive/docs_backup_20251005/

# 2. Stage 6: 標註為未來工作 (手動修改，太複雜)
echo "⚠️  Stage 6 文檔需手動修改 (40 處引用)"
echo "   文件: docs/stages/stage6-research-optimization.md"
echo "   參考: ML_DOCUMENTATION_CLEANUP_PLAN.md"

# 3. Stage 5: 簡單替換
sed -i 's/強化學習訓練數據 (移至 Stage 6)/獨立於六階段 (詳見 tools\/ml_training_data_generator\/)/g' \
    docs/stages/stage5-signal-analysis.md

sed -i 's/ML 訓練數據生成/3GPP 事件檢測/g' \
    docs/stages/stage5-signal-analysis.md

# 4. Stage 1: 註釋掉 ML 配置
sed -i "s/'reinforcement_learning_training': True/#'reinforcement_learning_training': True  # ⚠️ 已移除，ML 工具獨立實現/g" \
    docs/stages/stage1-specification.md

# 5. Stage 4: 簡單替換
sed -i 's/強化學習數據生成 (移至 Stage 6)/獨立於六階段 (未來工作)/g' \
    docs/stages/stage4-link-feasibility.md

sed -i 's/3GPP 事件 + ML 訓練/3GPP 事件檢測/g' \
    docs/stages/stage4-link-feasibility.md

echo "✅ 自動清理完成 (部分項目需手動修改)"
echo "📋 待手動修改:"
echo "   1. docs/stages/stage6-research-optimization.md (CRITICAL)"
echo "   2. docs/final.md (檢查研究目標)"
echo "   3. docs/stages/STAGES_OVERVIEW.md (檢查總覽)"
```

---

## 📊 清理檢查清單

### Phase 1: 自動清理 (優先)

- [ ] 備份所有文檔 (`archive/docs_backup_20251005/`)
- [ ] Stage 5: 替換 ML 引用 (7 處)
- [ ] Stage 1: 註釋 ML 配置 (3 處)
- [ ] Stage 4: 替換 ML 引用 (2 處)

### Phase 2: 手動修改 (CRITICAL)

- [ ] **Stage 6 文檔** (40 處引用)
  - [ ] 核心職責說明
  - [ ] 架構圖
  - [ ] ML 訓練數據章節 → 改為"未來工作"
  - [ ] Checklist

### Phase 3: 驗證 (必要)

- [ ] 檢查所有 markdown 連結有效性
- [ ] 檢查所有 SOURCE 引用仍然正確
- [ ] 檢查文檔內部一致性

---

## 🎯 最終文檔結構

### Stage 6 文檔應呈現

```markdown
# Stage 6: 3GPP 事件檢測與動態池驗證

## 核心職責 (六階段範圍)
1. 3GPP NTN 事件檢測 (A3/A4/A5/D2)
2. 動態池維持驗證
3. 換手決策評估

## 未來工作 (獨立 ML 工具)
- ML 訓練數據生成
- 強化學習算法應用
- 詳見: tools/ml_training_data_generator/

## 架構
[只包含 3GPP 檢測 + 池驗證 + 決策評估]

## 實現細節
[3GPP 事件檢測細節...]

## 附錄: ML 設計草案 (未來參考)
[保留 ML 設計概念供未來實現...]
```

---

## 📝 實施時程

| 階段 | 任務 | 預估時間 | 優先級 |
|------|------|----------|--------|
| **Phase 1** | 自動清理腳本執行 | 10 分鐘 | HIGH |
| **Phase 2** | Stage 6 文檔手動修改 | 30-45 分鐘 | CRITICAL |
| **Phase 3** | 項目級文檔檢查 | 15-20 分鐘 | MEDIUM |
| **Phase 4** | 文檔驗證與測試 | 10-15 分鐘 | HIGH |
| **總計** | - | **65-90 分鐘** | - |

---

## ✅ 完成標準

### 文檔清理合格標準

1. ✅ **無誤導性引用**: 文檔不應暗示 ML 功能已實現
2. ✅ **明確未來方向**: ML 標註為"未來工作"
3. ✅ **保留研究價值**: ML 設計概念保留供參考
4. ✅ **內部一致性**: 所有文檔對 Stage 6 職責描述一致
5. ✅ **連結有效性**: 所有 markdown 連結可訪問

### 驗證命令

```bash
# 1. 檢查是否還有誤導性 ML 引用
grep -r "ML 訓練數據生成" docs/stages/ | grep -v "未來工作"
grep -r "DQN.*生成.*完成" docs/

# 2. 檢查 Stage 6 職責描述一致性
grep "核心職責" docs/stages/stage6-research-optimization.md
grep "Stage 6" docs/stages/STAGES_OVERVIEW.md

# 3. 檢查 markdown 語法
markdownlint docs/**/*.md
```

---

**撰寫**: Claude Code
**日期**: 2025-10-05
**目的**: 同步清理 ML 代碼移除後的文檔引用
**預估時間**: 65-90 分鐘
