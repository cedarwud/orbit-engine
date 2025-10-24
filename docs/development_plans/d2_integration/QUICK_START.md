# D2 Integration - Quick Start Guide

**⏱️ 5 分鐘速覽** | 完整文檔: [README.md](./README.md)

---

## 🎯 專案目標

提升 D2 距離事件使用率：**0.4% → 15-20%**

---

## 📊 當前問題

```
D2 總事件: 261 個
└─ 實際使用: 1 個 (0.4%) ⚠️
   浪費: 260 個 (99.6%) ❌
   
原因: A4 絕對優先，D2 被忽略
```

---

## 🛠️ 解決方案

### 方案 1: 加權組合（短期，1-2 天）

```python
# 當前邏輯
if A4: use A4
elif D2: use D2

# 新邏輯
score = RSRP×0.6 + Distance×0.4
use max(score)
```

**目標**: D2 使用率 > 15%

### 方案 2: 狀態學習（長期，3-5 天）

```python
# 將距離加入狀態空間
state: 53 維 → 57 維
讓 DQN 自動學習最優權重
```

**目標**: 性能 > 方案 1

---

## 📂 文檔結構

```
d2_integration/
├─ README.md                        # 📘 總覽（你在這裡）
├─ QUICK_START.md                   # ⚡ 本文件
├─ PHASE1_WEIGHTED_COMBINATION.md   # 📄 方案 1 詳細計劃
└─ PHASE2_DISTANCE_IN_STATE.md      # 📄 方案 2 詳細計劃
```

---

## 🚀 快速開始

### Step 1: 閱讀計劃（10 分鐘）

```bash
# 閱讀 Phase 1 計劃
cat docs/development_plans/d2_integration/PHASE1_WEIGHTED_COMBINATION.md
```

### Step 2: 實施 Phase 1（4-6 小時）

```bash
# 1. 修改代碼
vim tools/ml_training_data_generator/core/dataset_builder.py

# 2. 生成數據
PYTHONPATH=. venv/bin/python tools/ml_training_data_generator/main.py

# 3. 訓練模型
PYTHONPATH=. venv/bin/python tools/rl_algorithms/dqn/train.py

# 4. 評估
PYTHONPATH=. venv/bin/python tools/rl_algorithms/dqn/evaluate.py
```

### Step 3: 檢查結果

```python
# 驗證 D2 使用率
import json
with open('data/evaluation_reports/dqn_evaluation_XXX/evaluation_report.md') as f:
    report = f.read()
    # 檢查 "D2 使用率" > 15%
```

---

## ✅ 成功標準

| 指標 | 目標 |
|------|------|
| D2 使用率 | > 15% |
| 總獎勵改進 | > +20% |
| 不必要換手 | < 5% |

---

## 🆘 常見問題

**Q: 先做哪個方案？**
A: 先做 Phase 1（簡單快速），再做 Phase 2（深入研究）

**Q: Phase 1 失敗怎麼辦？**
A: 檢查權重設置（0.6/0.4 可能需要調整），嘗試 0.5/0.5 或 0.7/0.3

**Q: Phase 2 訓練不收斂？**
A: 降低學習率、增加 replay buffer、檢查狀態歸一化

---

## 📞 獲取幫助

**詳細文檔**: [README.md](./README.md)
**Phase 1 計劃**: [PHASE1_WEIGHTED_COMBINATION.md](./PHASE1_WEIGHTED_COMBINATION.md)
**Phase 2 計劃**: [PHASE2_DISTANCE_IN_STATE.md](./PHASE2_DISTANCE_IN_STATE.md)

---

**版本**: v1.0 | **日期**: 2025-10-24
