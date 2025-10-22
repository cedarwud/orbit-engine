# Proposal 002: 訓練數據多樣性增強計畫

> **提案狀態**: 🔄 規劃中
> **創建日期**: 2025-10-22
> **預估工期**: 2-3 週
> **影響範圍**: Stage 5 & Stage 6

---

## 📖 文檔導覽

按順序閱讀以下文檔以全面了解本提案：

### 1. 總覽與背景
📄 **[00-OVERVIEW.md](./00-OVERVIEW.md)** - 從這裡開始
- 提案目標與動機
- 文獻依據總結
- 架構決策理由
- 可交付成果清單
- 時間線與成功標準

### 2. 需求分析
📄 **[01-REQUIREMENTS.md](./01-REQUIREMENTS.md)**
- 9 篇論文的文獻研究結果
- 5 種多樣性類型詳細分析
- 功能需求（FR-1, FR-2, FR-3）
- 非功能需求（NFR-1 到 NFR-4）
- 需求追溯矩陣
- 學術引用與技術標準

### 3. 架構設計
📄 **[02-ARCHITECTURE.md](./02-ARCHITECTURE.md)**
- 擴充前後架構對比
- Stage 5 新增模組設計
- Stage 6 新增模組設計
- 數據流設計
- API 接口設計（含代碼範例）
- 配置設計（YAML 範例）
- 錯誤處理與性能優化策略

### 4. Stage 5 詳細設計
📄 **[03-STAGE5-PROPAGATION.md](./03-STAGE5-PROPAGATION.md)** ⭐ 重點
- 三態 Markov 模型詳細設計
- Loo 通道模型詳細設計
- PropagationConditionSimulator 實現
- 整合到現有 Stage 5 流程
- 測試策略

### 5. Stage 6 詳細設計
📄 **[04-STAGE6-SCENARIOS.md](./04-STAGE6-SCENARIOS.md)** ⭐ 重點
- TrafficProfileGenerator 詳細設計
- SatelliteLoadSimulator 詳細設計
- ScenarioVariantGenerator 詳細設計
- 整合到現有 Stage 6 流程
- 測試策略

### 6. 實施計劃
📄 **[05-IMPLEMENTATION-PLAN.md](./05-IMPLEMENTATION-PLAN.md)** ⭐ 重點
- 3 週詳細時間表（Day-by-Day）
- Phase 1: Stage 5 擴充（5 天）
- Phase 2: Stage 6 擴充（5 天）
- Phase 3: 整合測試（2-3 天）
- Phase 4: 文檔完善（1-2 天）
- 里程碑與風險管理
- 進度追蹤機制

### 7. 測試計劃
📄 **[06-TEST-PLAN.md](./06-TEST-PLAN.md)** ⭐ 重點
- 單元測試策略
- 整合測試策略
- 性能測試基準
- 學術合規性測試
- 測試用例清單

### 8. 文檔更新清單
📄 **[07-DOCUMENTATION-UPDATES.md](./07-DOCUMENTATION-UPDATES.md)** ⭐ 重點
- 15 份文檔需要更新/創建
- 按優先級分類（高/中/低）
- 每份文檔的預估時間
- 總計 27 小時文檔工作
- 詳細檢查清單

---

## 🎯 快速參考

### 核心問題
**Q: 為什麼需要這個提案？**
A: Starlink 101 顆衛星訓練池的時空錯置已達標（96.3% 覆蓋率），但 RL 訓練效果不佳。文獻研究（9 篇論文）發現缺少 3 種關鍵多樣性：
1. ❌ 動態傳播條件（LOS/Shadowed/Blocked）
2. ❌ 流量類型多樣性（VoIP/Video/IoT）
3. ❌ 衛星負載多樣性（Uniform/Concentrated/Dynamic）

---

### 解決方案
**擴充 Stage 5 和 Stage 6，不新增階段**

| 階段 | 擴充內容 | 論文依據 |
|------|---------|---------|
| **Stage 5** | 三態 Markov + Loo 通道 | 2024_06 Dynamic Propagation |
| **Stage 6** | 流量類型 + 負載模擬 | 2024_07 Traffic Profiles + 2021_01 Load-Aware |

---

### 關鍵指標

| 指標 | 目標 |
|------|------|
| 執行時間增加 | < 30% |
| 記憶體使用增加 | < 15% |
| 輸出檔案增加 | < 50% |
| 場景變體數量 | 12 個/樣本（4 流量 × 3 負載） |
| 測試覆蓋率 | > 80% |
| 學術合規性 | 100% 通過 |

---

### 時間線

```
Week 1: Stage 5 擴充 (動態傳播條件)
├── Day 1-2: Markov 模型 + Loo 通道
├── Day 3:   整合器實現
├── Day 4:   配置與文檔
└── Day 5:   測試與優化

Week 2: Stage 6 擴充 (場景多樣性)
├── Day 1:   流量類型生成器
├── Day 2:   負載模擬器
├── Day 3:   場景變體生成器
├── Day 4:   配置與文檔
└── Day 5:   測試與優化

Week 3: 整合測試與發布
├── Day 1-2: 完整流程測試
├── Day 3:   邊界條件測試
└── Day 4-5: 文檔完善與發布
```

---

## 📚 學術依據

### 主要論文

1. **2024_06** - Liu, H., et al. "Multi-Agent Deep Reinforcement Learning-Based Handover Scheme for Mega-Constellation **Under Dynamic Propagation Conditions**." IEEE TWC.
   → **要求**: 三態 Markov 模型 + Loo 通道

2. **2024_07** - Badini, I., et al. "User-Centric Satellite Handover for **Multiple Traffic Profiles** Using Deep Q-Learning." IEEE TAES.
   → **要求**: VoIP/Video/IoT 流量類型

3. **2021_01** - He, S., et al. "**Load-Aware** Satellite Handover Strategy Based on Multi-Agent Reinforcement Learning." IEEE ICC.
   → **要求**: 衛星負載狀態多樣性

### 技術標準

- **3GPP TR 38.901** - Channel model (Markov 轉換率)
- **3GPP TS 22.261** - Service requirements (QoS 參數)
- **3GPP TR 38.821** - NTN systems (容量假設)
- **ITU-R P.1410** - Propagation data
- **Loo (1985)** - Land mobile satellite channel model

---

## 🎓 學術合規性

本提案嚴格遵循 `docs/ACADEMIC_STANDARDS.md` 要求：
- ✅ 所有參數有官方來源（SOURCE 註解）
- ✅ 不使用簡化算法或估計值
- ✅ 完整實現學術標準模型
- ✅ 可重現性（配置驅動）
- ✅ 引用格式符合規範

---

## ⚠️ 風險與緩解

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|---------|
| 3GPP 標準理解困難 | 中 | 高 | 預先閱讀論文原文 |
| 性能超標 | 低 | 中 | 及早 profiling |
| 測試覆蓋不足 | 中 | 中 | 詳細測試計劃 |
| 配置複雜度 | 低 | 低 | 詳細文檔 + 驗證邏輯 |

---

## 📞 聯絡資訊

**提案人**: Claude Code
**審核人**: User
**開發團隊**: TBD
**QA 團隊**: TBD

---

## 🔗 相關連結

### 內部文檔
- [Proposal 001: Stage 4 軌道面多樣性](../001-stage4-orbital-diversity/) - 已完成
- [Bug Fix: 軌道面多樣性](../../../bugfix/ORBITAL_DIVERSITY_BUG_FIX.md) - 2025-10-22
- [Stage 5 現有文檔](../../../stages/stage5-signal-quality-analysis.md)
- [Stage 6 現有文檔](../../../stages/stage6-research-optimization.md)
- [學術標準指南](../../../ACADEMIC_STANDARDS.md)

### 外部資源
- [rl-paper/ 目錄](/home/sat/satellite/rl-paper/) - 9 篇參考論文
- [3GPP TR 38.901](https://www.3gpp.org/ftp/Specs/archive/38_series/38.901/) - 通道模型
- [3GPP TS 22.261](https://www.3gpp.org/ftp/Specs/archive/22_series/22.261/) - 服務要求
- [3GPP TR 38.821](https://www.3gpp.org/ftp/Specs/archive/38_series/38.821/) - NTN 系統

---

## 📝 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|---------|------|
| 0.1 | 2025-10-22 | 初始版本，創建規劃文檔 | Claude Code |
| - | - | - | - |

---

## ✅ 下一步行動

1. **立即**: 閱讀 [00-OVERVIEW.md](./00-OVERVIEW.md) 了解提案全貌
2. **5 分鐘後**: 檢視 [05-IMPLEMENTATION-PLAN.md](./05-IMPLEMENTATION-PLAN.md) 了解詳細時間表
3. **15 分鐘後**: 閱讀 [01-REQUIREMENTS.md](./01-REQUIREMENTS.md) 了解文獻依據
4. **決策**: 確認是否開始實施
5. **開始**: 進入 Phase 1 - Stage 5 擴充開發

---

**提案狀態**: 🔄 等待審核與批准
