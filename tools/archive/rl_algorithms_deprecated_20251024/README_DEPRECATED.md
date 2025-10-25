# RL Algorithms - DEPRECATED

**歸檔日期**: 2025-10-24
**原位置**: `orbit-engine/tools/rl_algorithms/`
**歸檔原因**: 功能重複，已由 handover-rl 專案完整實現

---

## 廢棄原因

### 問題

1. **功能重複** ⚠️
   - orbit-engine/tools/rl_algorithms/dqn/ 與 handover-rl/src/agents/dqn/ 完全重複
   - 維護兩份相同功能的代碼違反 DRY 原則
   - 容易導致不一致和維護困難

2. **職責不清** ⚠️
   - orbit-engine 的職責是**數據生成**，不是 RL 訓練
   - RL 算法實現應該在 handover-rl 專案中

3. **未被使用** ⚠️
   - 沒有被 orbit-engine 主代碼引用
   - 沒有被 handover-rl 引用
   - handover-rl/train.py 已有更完整的實現

---

## 替代方案

### 使用 handover-rl 的 DQN 實現

**位置**: `/home/sat/satellite/handover-rl/`

**功能對照**:

| 此歸檔版本 | handover-rl 對應實現 | 狀態 |
|-----------|---------------------|------|
| `agents/dqn_agent.py` | `src/agents/dqn/dqn_agent.py` | ✅ 更完整 |
| `networks/q_network.py` | `src/models/` | ✅ 更完整 |
| `envs/satellite_handover_env.py` | `src/environments/satellite_handover_env.py` | ✅ 更完整 |
| `utils/replay_buffer.py` | `src/utils/replay_buffer.py` | ✅ 更完整 |
| `utils/checkpoint_manager.py` | `src/trainers/` | ✅ 更完整 |
| `train.py` | `train.py` | ✅ 更完整（支援多算法） |

**handover-rl 的優勢**:
- ✅ 支援多種 RL 算法（DQN, A3C, PPO, SAC）
- ✅ Multi-Level Training Strategy
- ✅ 完整的評估管道
- ✅ TensorBoard 整合
- ✅ 更好的模組化設計

---

## 歸檔內容

### 文件結構

```
rl_algorithms_deprecated_20251024/
├── dqn/
│   ├── agents/
│   │   └── dqn_agent.py          # DQN agent 實現
│   ├── networks/
│   │   └── q_network.py          # Q-network
│   ├── envs/
│   │   └── satellite_handover_env.py  # 環境
│   ├── evaluation/
│   │   ├── evaluation_pipeline.py
│   │   ├── evaluation_metrics.py
│   │   ├── report_generator.py
│   │   └── rsrp_baseline_policy.py
│   ├── utils/
│   │   ├── replay_buffer.py      # Replay buffer
│   │   └── checkpoint_manager.py # 檢查點管理
│   ├── train.py                  # 訓練腳本
│   └── evaluate.py               # 評估腳本
└── README_DEPRECATED.md          # 本文件
```

### 代碼統計

- **總行數**: ~2,301 行
- **文件數**: 18 個 Python 文件
- **創建日期**: 2025-10-23
- **最後修改**: 2025-10-23

---

## 歷史價值

### 保留此歸檔的原因

雖然功能已由 handover-rl 取代，但保留歸檔有以下價值：

1. **歷史記錄**: 記錄 Proposal 003 Phase 2-3 的開發過程
2. **設計參考**: 可作為未來架構設計的參考
3. **學術追溯**: 保留完整的開發歷史，符合學術研究要求

---

## 職責劃分（清理後）

### orbit-engine 職責 ✅
- ✅ TLE 數據載入（Stage 1）
- ✅ 軌道計算（Stage 2: SGP4）
- ✅ 座標轉換（Stage 3）
- ✅ 鏈路可行性分析（Stage 4）
- ✅ 信號品質分析（Stage 5: 3GPP, ITU-R）
- ✅ 換手事件生成（Stage 6: A3, A4, A5, D2）
- ✅ **ML 訓練數據生成**（tools/ml_training_data_generator）

### handover-rl 職責 ✅
- ✅ RL 算法實現（DQN, A3C, PPO, SAC）
- ✅ RL 訓練管道
- ✅ 環境定義
- ✅ Agent 實現
- ✅ 評估與測試

---

## 如果需要恢復

如果未來需要恢復此代碼（不建議），執行：

```bash
# 恢復到 tools/
mv /home/sat/satellite/orbit-engine/tools/archive/rl_algorithms_deprecated_20251024 \
   /home/sat/satellite/orbit-engine/tools/rl_algorithms

# 但建議：直接使用 handover-rl 的實現
```

---

**歸檔狀態**: ✅ 已歸檔，功能已由 handover-rl 完整取代
**維護狀態**: ❌ 不再維護
**建議操作**: 使用 handover-rl 的 RL 算法實現
