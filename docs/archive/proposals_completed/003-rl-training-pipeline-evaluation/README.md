# Proposal 003: RL Training Pipeline & Evaluation Framework (DQN Baseline)

**提案狀態**: 🔄 進行中 (Phase 1 已完成, Phase 2-4 待實施)
**提案日期**: 2025-10-23
**Phase 1 完成日期**: 2025-10-24
**預計總工期**: 7-10 天
**優先級**: 🔴 高 (High)

**實施進度**:
- ✅ **Phase 1 已完成** (2025-10-24): ML Data Generator 已實現
  - 位置: `tools/ml_training_data_generator/`
  - 功能: 從 Stage 6 JSON 生成 HDF5 訓練數據集
  - 時間特徵: ✅ 已整合 (velocity, predicted RSRP)
  - 測試: ✅ 已驗證（89K+ transitions, 77-dim states）
- 📋 **Phase 2 規劃中**: DQN Baseline 實現
- 📋 **Phase 3 規劃中**: Training Pipeline
- 📋 **Phase 4 規劃中**: Evaluation Framework

---

## 📚 文檔導航

### 核心文檔

| 文檔 | 內容 | 狀態 |
|------|------|------|
| [00-OVERVIEW.md](00-OVERVIEW.md) | 提案總覽與目標 | ✅ 完成 |
| [01-REQUIREMENTS.md](01-REQUIREMENTS.md) | 需求分析與範圍定義 | ✅ 完成 |
| [02-ARCHITECTURE.md](02-ARCHITECTURE.md) | 系統架構設計 | ✅ 完成 |
| [03-PHASE1-DATA-GENERATOR.md](03-PHASE1-DATA-GENERATOR.md) | Phase 1: ML Data Generator | ✅ 完成 |
| [04-PHASE2-DQN-BASELINE.md](04-PHASE2-DQN-BASELINE.md) | Phase 2: DQN Baseline 實現 | ✅ 完成 |
| [05-PHASE3-TRAINING.md](05-PHASE3-TRAINING.md) | Phase 3: Training Pipeline | ✅ 完成 |
| [06-PHASE4-EVALUATION.md](06-PHASE4-EVALUATION.md) | Phase 4: Evaluation Framework | ✅ 完成 |
| [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) | 實施計畫與時間線 | ✅ 完成 |

### 廢棄文檔

| 文檔 | 說明 |
|------|------|
| [PROPOSAL.md](PROPOSAL.md) | ⚠️ **已廢棄** - 舊版提案（包含錯誤設計，僅供參考） |

---

## 🎯 快速摘要

### 核心目標

**建立 DQN baseline 訓練和評估體系**，為未來的算法開發（您的算法）提供對比基準。

### 關鍵決策

✅ **只實現 DQN** - 其他算法（A3C, PPO, SAC）等未來需要時再添加
✅ **獨立工具設計** - ML Data Generator 不修改 Stage 6 輸出
✅ **使用 Gymnasium** - 不使用已廢棄的 OpenAI Gym
✅ **保持前端兼容** - Stage 6 JSON 格式完全不變

### 四個階段

| 階段 | 時間 | 核心產出 |
|------|------|---------|
| Phase 1 | 2 天 | ML Data Generator（獨立工具） |
| Phase 2 | 3-4 天 | DQN Baseline 實現（僅 DQN） |
| Phase 3 | 2 天 | Training Pipeline |
| Phase 4 | 2 天 | Evaluation Framework（基本版） |

**總工期**: 7-10 天

---

## 📋 文檔閱讀順序

### 對於項目管理者

1. **先讀**: [00-OVERVIEW.md](00-OVERVIEW.md) - 了解整體目標
2. **再讀**: [01-REQUIREMENTS.md](01-REQUIREMENTS.md) - 確認需求範圍
3. **最後**: [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) - 審批時間線

### 對於開發者

1. **先讀**: [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - 理解系統設計
2. **按需**: Phase 1-4 詳細設計文檔
3. **參考**: [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) - 任務分配

### 對於審查者

1. **關注**: [01-REQUIREMENTS.md](01-REQUIREMENTS.md) - 範圍是否明確
2. **檢查**: [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - 設計是否合理
3. **評估**: [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) - 工期是否可行

---

## 🔗 與其他 Proposal 的關係

### 依賴 Proposal 002

**Proposal 002 提供**:
- ✅ 12 種場景變體（4 traffic × 3 load）
- ✅ 動態傳播條件
- ✅ Stage 6 豐富輸出

**Proposal 003 使用**:
- ✅ 讀取 Stage 6 JSON 輸出
- ✅ 利用場景多樣性進行訓練
- ✅ 評估各場景下的性能

### 為未來鋪路

**Proposal 003 完成後**:
- ✅ DQN baseline 可用於對比
- ✅ 評估框架已建立
- ✅ 您的算法可直接整合並對比

---

## ⚠️ 重要說明

### 與舊版 PROPOSAL.md 的差異

**舊版（已廢棄）包含的錯誤**:
- ❌ 實現 4 種 RL 算法（DQN, A3C, PPO, SAC）
- ❌ 使用舊的 OpenAI Gym
- ❌ 可能修改 Stage 6 輸出
- ❌ 工期過長（14-21 天）

**新版（本文檔集）的修正**:
- ✅ 僅實現 DQN baseline
- ✅ 使用 Gymnasium
- ✅ ML Data Generator 是獨立工具
- ✅ 工期優化為 7-10 天

---

## 📞 聯繫與審批

**提案負責人**: Orbit Engine Development Team
**審批狀態**: ⏳ 待審批
**預計開始**: 待批准後立即開始

### 審批清單

- [ ] 技術方案審查（關注：獨立工具設計、Gymnasium 使用）
- [ ] 資源分配確認（GPU、開發人員）
- [ ] 時間線批准（7-10 天可行性）
- [ ] 開始實施

---

**文檔版本**: v2.0
**最後更新**: 2025-10-23
**更新說明**: 結構化重寫，反映技術討論修正
