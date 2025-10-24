# Handover-RL DQN Training Prompt (Phase 1b)

**新對話起始提示** - 在 handover-rl 專案中使用

**Date**: 2025-10-24
**Context**: Phase 1 (orbit-engine 數據生成) 已完成，開始 Phase 1b (handover-rl DQN 訓練)

---

## 📋 背景概要

我們正在進行 **D2 Event Integration 專案**，目標是提升 3GPP D2 (距離事件) 在 DQN 訓練數據中的利用率。

### Phase 1 (orbit-engine) 已完成 ✅

**成果**:
- D2 使用率從 0.4% 提升至 **34.4%** (目標 15-20%) 🎯
- 實現了 A4+D2 加權組合策略 (RSRP 0.6 + Distance 0.4)
- 生成新 HDF5 數據集: `data/ml_training/rl_training_dataset_20251024_020730.h5`

**數據集統計**:
```
總 transitions: 2590
Episodes: 123
換手率: 7.3% (189 handovers)

A4/D2 事件使用:
├─ A4-only: 124 actions (65.6%)
├─ D2-only: 1 action (0.5%)
└─ A4+D2 combined: 64 actions (33.9%) ✨

D2 使用率: 34.4% ✅
```

**詳細報告**:
- `orbit-engine/docs/development_plans/d2_integration/PHASE1_COMPLETION_SUMMARY.md`
- `orbit-engine/docs/development_plans/d2_integration/README.md` (已更新進度)

---

## 🎯 Phase 1b 任務 (handover-rl 專案)

你現在需要在 **handover-rl 專案**中使用新數據集訓練 DQN 模型並評估性能。

### 任務清單

1. **數據集整合** ⏳
   - 從 orbit-engine 複製新數據集到 handover-rl
   - 路徑: `orbit-engine/data/ml_training/rl_training_dataset_20251024_020730.h5`
   - 目標: `handover-rl/data/datasets/rl_training_dataset_phase1.h5`

2. **DQN 訓練配置** ⏳
   - 檢查現有 DQN 配置是否需要調整
   - 確認訓練參數 (learning rate, batch size, episodes, etc.)
   - 驗證數據集相容性 (state_dim=53, action_space=6)

3. **模型訓練** ⏳
   - 訓練 DQN 模型使用新數據集
   - 監控訓練曲線 (loss, reward, epsilon)
   - 保存最佳模型

4. **模型評估** ⏳
   - 在測試集上評估模型
   - 計算關鍵指標:
     - 總獎勵改進 (vs RSRP baseline, vs Stage 6 greedy)
     - 換手率
     - 不必要換手率
     - D2 事件利用情況

5. **結果分析** ⏳
   - 對比三種策略:
     - RSRP baseline (legacy)
     - Stage 6 greedy (weighted A4+D2, 34.4% D2 usage)
     - DQN learned policy (expected to be optimal)
   - 生成評估報告

---

## ✅ 成功標準

| 指標 | 目標 |
|------|------|
| **總獎勵改進** | > +20% vs RSRP baseline |
| **D2 使用率** | 保持 ~30-40% (繼承 Stage 6 數據) |
| **不必要換手率** | < 5% |
| **訓練穩定性** | Loss 收斂，無發散 |

---

## 📂 文件路徑參考

### Orbit-Engine (數據生成層)

```
orbit-engine/
├─ data/ml_training/rl_training_dataset_20251024_020730.h5  # 新數據集 ✅
├─ tools/ml_training_data_generator/
│  ├─ core/dataset_builder.py  # 加權組合實現
│  ├─ config/data_generator_config.yaml  # action_selection 配置
│  └─ generate_dataset.py  # 主入口
└─ docs/development_plans/d2_integration/
   ├─ README.md  # 總覽（已更新）
   ├─ PHASE1_COMPLETION_SUMMARY.md  # Phase 1 成果
   └─ HANDOVER_RL_PROMPT.md  # 本文件
```

### Handover-RL (訓練層)

```
handover-rl/  # 你現在應該在這個專案中
├─ data/datasets/
│  └─ rl_training_dataset_phase1.h5  # 從 orbit-engine 複製
├─ tools/rl_algorithms/dqn/
│  ├─ train.py  # DQN 訓練腳本
│  ├─ evaluate.py  # 評估腳本
│  └─ config/dqn_config.yaml  # DQN 配置
└─ results/
   └─ evaluation_reports/dqn_phase1_xxx/  # 評估報告輸出
```

---

## 🚀 開始命令參考

### 1. 複製數據集

```bash
# 在 handover-rl 專案根目錄
mkdir -p data/datasets
cp ../orbit-engine/data/ml_training/rl_training_dataset_20251024_020730.h5 \
   data/datasets/rl_training_dataset_phase1.h5
```

### 2. 驗證數據集

```bash
# 檢查數據集結構
PYTHONPATH=. python -c "
import h5py
with h5py.File('data/datasets/rl_training_dataset_phase1.h5', 'r') as f:
    print('Splits:', list(f.keys()))
    print('Train samples:', len(f['train']['states']))
    print('State dim:', f['train']['states'].shape[1])
    print('Max actions:', f['train']['actions'][:].max())
"
```

### 3. 訓練 DQN

```bash
# 使用新數據集訓練
PYTHONPATH=. python tools/rl_algorithms/dqn/train.py \
    --dataset data/datasets/rl_training_dataset_phase1.h5 \
    --output-dir results/models/dqn_phase1
```

### 4. 評估模型

```bash
# 評估訓練好的模型
PYTHONPATH=. python tools/rl_algorithms/dqn/evaluate.py \
    --model results/models/dqn_phase1/best_model.pth \
    --dataset data/datasets/rl_training_dataset_phase1.h5 \
    --output-dir results/evaluation_reports/dqn_phase1
```

---

## 📊 預期結果

根據 Phase 1 數據改進，我們預期 DQN 訓練後:

1. **學習到加權組合策略的優勢**
   - DQN 應該能識別 A4+D2 結合的價值
   - 換手決策更加多樣化（非單一依賴 RSRP）

2. **總獎勵顯著改進**
   - 預期 > +20% vs RSRP baseline
   - 可能 > +10% vs Stage 6 weighted greedy

3. **D2 事件利用保持高水平**
   - 數據集已內建 34.4% D2 使用率
   - DQN 應繼承這個特性

4. **不必要換手率低**
   - 加權組合策略有 min_score_threshold=1.0 防護
   - DQN 應學習到何時 stay 更優

---

## 🔬 Debug 指南

### 問題 1: 數據集不相容

**症狀**: `ValueError: Expected state_dim=X, got Y`

**解決**:
- 檢查 DQN config 中的 state_dim 是否為 53
- 檢查數據集是否正確生成 (h5dump 查看結構)

### 問題 2: 訓練不收斂

**症狀**: Loss 持續上升或震盪

**解決**:
- 降低 learning rate (試試 1e-4 → 5e-5)
- 增加 replay buffer size
- 檢查 reward normalization

### 問題 3: DQN 不使用 D2

**症狀**: 評估顯示 DQN 只學到 A4 策略

**分析**:
- 這是數據集問題，不是 DQN 問題
- 檢查訓練數據的 action distribution
- 應該看到 34.4% D2 貢獻的動作

---

## 📝 提交給我的信息

完成 Phase 1b 後，請準備以下資訊：

1. **訓練統計**
   - 訓練時間
   - 最終 loss
   - 收斂 episode

2. **評估結果**
   - 總獎勵改進 (vs baselines)
   - 換手率統計
   - D2 使用情況

3. **對比報告**
   - RSRP baseline vs Stage 6 weighted vs DQN learned
   - 關鍵指標對比表

4. **下一步建議**
   - 是否需要超參數調優
   - 是否可以進入 Phase 2 (狀態擴展)

---

## 🎓 學術合規性提醒

所有實驗和結果必須符合學術標準：

- **可重現性**: 設置隨機種子，記錄所有超參數
- **公平對比**: 使用相同測試集評估所有方法
- **統計顯著性**: 如果可能，進行多次訓練取平均
- **文檔完整**: 保存所有日誌、配置、模型

**SOURCE References**:
- 3GPP TS 38.331 v18.5.1 - A4/D2 事件定義
- Badini et al. (2024) IEEE TAES - Multi-objective handover
- Mnih et al. (2015) Nature - DQN algorithm

---

**準備好了嗎？讓我們開始 Phase 1b！** 🚀

---

**快速摘要（給 Claude 的提示）**:

```
任務: 使用 orbit-engine 新生成的數據集在 handover-rl 專案中訓練 DQN

數據集位置: orbit-engine/data/ml_training/rl_training_dataset_20251024_020730.h5
數據集特性: D2 使用率 34.4%, 2590 transitions, state_dim=53

步驟:
1. 複製數據集到 handover-rl/data/datasets/
2. 訓練 DQN (tools/rl_algorithms/dqn/train.py)
3. 評估模型 (tools/rl_algorithms/dqn/evaluate.py)
4. 驗證總獎勵改進 > +20% vs baseline

成功標準: 總獎勵改進 >+20%, D2 使用率 ~30-40%, 不必要換手率 <5%
```
