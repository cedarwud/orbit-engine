# Proposal 002: 訓練數據多樣性增強計畫

## 📋 提案資訊

- **提案編號**: 002
- **提案日期**: 2025-10-22
- **提案狀態**: 規劃中
- **預估工期**: 2-3 週
- **影響範圍**: Stage 5 & Stage 6
- **優先級**: 高（解決 RL 訓練效果不佳問題）

---

## 🎯 目標

根據 9 篇 LEO 衛星換手 RL 論文的文獻研究，增強訓練數據的多樣性，以改善 RL 訓練效果。

### 核心問題

**現況**：
- Starlink 優化池：98 顆衛星，96.3% 時間覆蓋率 ✅
- 時空錯置（Pool Optimization）已達標 ✅
- **但 RL 訓練效果不佳** ❌

**根本原因**（經文獻研究發現）：
- ❌ 缺少動態傳播條件多樣性（靜態幾何可見性不足）
- ❌ 缺少流量類型多樣性（單一地面站場景）
- ❌ 缺少衛星負載多樣性（無負載狀態模擬）

---

## 📚 文獻依據

### 已分析論文（9 篇）

| 論文 | 發表年份 | 關鍵要求 |
|------|---------|---------|
| Dynamic Propagation Conditions | 2024-06 | 三態 Markov 模型（LOS/Shadowed/Blocked） |
| Multiple Traffic Profiles | 2024-07 | 多流量類型（VoIP/Video/IoT） |
| Load-Aware MARL | 2021-01 | 衛星負載狀態多樣性 |
| Handover Protocol Learning | 2023-12 | 時間多樣性（已滿足 ✅） |
| Multi-Agent DRL | 2025-03 | 問題規模多樣性 |

### 文獻要求的多樣性清單

| 多樣性類型 | 六階段現況 | 論文依據 | 優先級 |
|-----------|-----------|---------|--------|
| ✅ **時間多樣性** | 已實現（21 時間點） | 2023_12 | - |
| ❌ **動態傳播條件** | 無（靜態幾何） | 2024_06 | **高** |
| ❌ **流量類型多樣性** | 無（單一場景） | 2024_07 | **高** |
| ❌ **衛星負載多樣性** | 無（無負載模擬） | 2021_01 | **中** |
| ⚠️ **軌道面多樣性** | 自然分布（9 面） | 無文獻支持 | 低 |

**結論**：需優先實現動態傳播條件和流量類型多樣性。

---

## 🏗️ 架構決策

### 方案比較

| 方案 | 優點 | 缺點 | 決策 |
|------|------|------|------|
| **A. 擴充 Stage 5/6** | 職責清晰、維護簡單 | 需修改現有模組 | ✅ **採用** |
| B. 新增 Stage 7/8 | 獨立開發 | 架構複雜、職責重疊 | ❌ 不採用 |
| C. 外部後處理 | 不影響現有系統 | 破壞數據完整性 | ❌ 不採用 |

### 採用方案 A：擴充現有階段

**Stage 5 擴充** - 動態傳播條件層
```
職責：鏈路品質分析 + 動態傳播條件
新增：三態 Markov 模型、Loo 通道模型
輸出：propagation_state, channel_attenuation_db
```

**Stage 6 擴充** - 場景多樣性層
```
職責：RL 訓練數據生成 + 場景變體
新增：流量類型生成器、負載模擬器
輸出：traffic_profile, satellite_loads, scenario_variant_id
```

---

## 📦 可交付成果

### 1. Stage 5 擴充模組
- `propagation_state_simulator.py` - 傳播狀態模擬器
  - `ThreeStateMarkovModel` - 三態 Markov 模型
  - `LooChannelModel` - Loo 通道模型
  - `PropagationConditionSimulator` - 整合器

### 2. Stage 6 擴充模組
- `traffic_profile_generator.py` - 流量類型生成器
  - `TrafficProfile` dataclass
  - `TrafficProfileGenerator` - 多流量類型生成
- `satellite_load_simulator.py` - 負載模擬器
  - `LoadPattern` enum
  - `SatelliteLoadSimulator` - 負載狀態生成

### 3. 配置文件更新
- `config/stage5_signal_analysis_config.yaml` - 新增傳播配置
- `config/stage6_research_optimization_config.yaml` - 新增場景配置

### 4. 測試驗證
- 單元測試（pytest）
- 整合測試（Stage 5 → Stage 6）
- 學術合規性驗證

### 5. 文檔更新
- 10+ 份文檔更新（詳見 07-DOCUMENTATION-UPDATES.md）
- 新增 API 參考文檔
- 更新使用者指南

---

## 🗓️ 實施時間線

### Week 1: Stage 5 擴充（動態傳播條件）
- **Day 1-2**: 三態 Markov 模型實現
- **Day 3-4**: Loo 通道模型實現
- **Day 5**: 整合測試 + 文檔

### Week 2: Stage 6 擴充（場景多樣性）
- **Day 1-2**: 流量類型生成器
- **Day 3-4**: 負載模擬器
- **Day 5**: 整合測試 + 文檔

### Week 3: 整合驗證與優化
- **Day 1-2**: 完整流程測試（Stage 1-6）
- **Day 3**: 學術合規性檢查
- **Day 4-5**: 文檔完善、Code Review

---

## 🎓 學術標準遵循

### 引用標準
- **動態傳播**: ITU-R P.1410, 3GPP TR 38.901
- **Markov 模型**: Gilbert-Elliott Model (1960), Lutz et al. (1991)
- **Loo 通道**: Loo, C. (1985) "A statistical model for a land mobile satellite link"
- **流量類型**: 3GPP TS 22.261, ITU-T Y.1541
- **負載模擬**: 3GPP TR 38.821, ITU-T E.800

### 學術合規檢查點
1. ✅ 所有參數必須有官方來源（SOURCE 註解）
2. ✅ 不使用簡化算法或估計值
3. ✅ 實現完整的學術標準模型
4. ✅ 可重現性（配置驅動，無硬編碼）

---

## 📊 成功標準

### 功能性標準
1. ✅ Stage 5 輸出包含 `propagation_state` 欄位
2. ✅ Stage 6 輸出包含 `traffic_profile` 和 `satellite_loads`
3. ✅ 支援多場景變體生成（同一軌道數據，不同條件）
4. ✅ 向後兼容（不破壞現有流程）

### 多樣性標準
1. ✅ 傳播狀態覆蓋 LOS/Shadowed/Blocked 三態
2. ✅ 流量類型涵蓋 VoIP/Video/IoT/BestEffort
3. ✅ 負載狀態包含 Uniform/Concentrated/Dynamic 模式
4. ✅ 每個訓練樣本有多種場景變體（≥5 種）

### 性能標準
1. ✅ Stage 5 執行時間增加 < 20%
2. ✅ Stage 6 執行時間增加 < 30%
3. ✅ 記憶體使用增加 < 15%
4. ✅ 輸出檔案大小增加 < 50%

---

## 🔗 相關文檔

### 本提案文檔
1. [01-REQUIREMENTS.md](./01-REQUIREMENTS.md) - 需求分析
2. [02-ARCHITECTURE.md](./02-ARCHITECTURE.md) - 架構設計
3. [03-STAGE5-PROPAGATION.md](./03-STAGE5-PROPAGATION.md) - Stage 5 設計
4. [04-STAGE6-SCENARIOS.md](./04-STAGE6-SCENARIOS.md) - Stage 6 設計
5. [05-IMPLEMENTATION-PLAN.md](./05-IMPLEMENTATION-PLAN.md) - 實施計劃
6. [06-TEST-PLAN.md](./06-TEST-PLAN.md) - 測試計劃
7. [07-DOCUMENTATION-UPDATES.md](./07-DOCUMENTATION-UPDATES.md) - 文檔更新清單

### 外部參考
- `docs/development/proposals/001-stage4-orbital-diversity/` - Proposal 001（已完成）
- `docs/stages/stage5-signal-quality-analysis.md` - Stage 5 現有文檔
- `docs/stages/stage6-research-optimization.md` - Stage 6 現有文檔
- `docs/ACADEMIC_STANDARDS.md` - 學術標準指南
- `/home/sat/satellite/rl-paper/*.pdf` - 9 篇參考論文

---

## ⚠️ 風險與限制

### 技術風險
1. **Markov 模型狀態轉換率** - 需要實際測量數據或官方統計
   - 緩解：使用 3GPP TR 38.901 的典型值
2. **Loo 通道參數** - 不同環境參數差異大
   - 緩解：限定 NTPU 場域，使用台灣氣候統計

### 範圍限制
1. **限定 NTPU 單一地面站** - 不支援多地理位置
2. **不考慮多用戶干擾** - 單用戶場景
3. **靜態星座配置** - 不模擬衛星故障或軌道變化

### 時間風險
1. **3GPP 標準複雜度** - 可能需要額外時間理解
   - 緩解：預先閱讀關鍵章節（Stage 5 擴充前）
2. **測試覆蓋不足** - 可能遺漏邊界條件
   - 緩解：編寫詳細測試計劃，使用 pytest fixture

---

## 📝 核准記錄

| 角色 | 姓名 | 日期 | 決策 |
|------|------|------|------|
| 提案人 | Claude Code | 2025-10-22 | 提交 |
| 審核人 | User | - | 待審核 |

---

**下一步**：請審閱本提案總覽，確認方向後進入詳細設計階段。
