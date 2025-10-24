# 實施計劃：訓練數據多樣性增強

## 📅 時間表總覽

| 階段 | 任務 | 工期 | 負責人 | 狀態 |
|------|------|------|--------|------|
| **Phase 1** | Stage 5 擴充 | 3-5 天 | Dev Team | 🔄 規劃中 |
| **Phase 2** | Stage 6 擴充 | 3-5 天 | Dev Team | ⏳ 待開始 |
| **Phase 3** | 整合測試 | 2-3 天 | QA Team | ⏳ 待開始 |
| **Phase 4** | 文檔完善 | 1-2 天 | Doc Team | ⏳ 待開始 |
| **總計** | - | **2-3 週** | - | - |

---

## 📦 Phase 1: Stage 5 擴充（動態傳播條件）

### Day 1: 三態 Markov 模型實現

#### 任務清單
- [x] 創建 `propagation_state_simulator.py` 檔案
- [ ] 實現 `ThreeStateMarkovModel` 類別
  - [ ] `__init__()` - 初始化轉換矩陣
  - [ ] `transition()` - 狀態轉換邏輯
  - [ ] `_adjust_by_elevation()` - 仰角調整
  - [ ] `get_transition_prob()` - 取得轉換機率
- [ ] 實現單元測試
  - [ ] 測試轉換矩陣驗證
  - [ ] 測試狀態轉換正確性
  - [ ] 測試仰角影響
- [ ] Code Review

#### 驗收標準
- ✅ 所有單元測試通過
- ✅ 轉換矩陣符合 3GPP TR 38.901
- ✅ 代碼通過 `make compliance` 檢查

#### 檔案清單
```
src/stages/stage5_signal_analysis/
├── propagation_state_simulator.py  (新建)
└── tests/
    └── test_markov_model.py         (新建)
```

---

### Day 2: Loo 通道模型實現

#### 任務清單
- [ ] 在 `propagation_state_simulator.py` 新增 `LooChannelModel` 類別
  - [ ] `__init__()` - 初始化參數
  - [ ] `calculate_attenuation()` - 計算通道衰減
  - [ ] `_multipath_component()` - Rayleigh fading
  - [ ] `_shadowing_component()` - Lognormal shadowing
  - [ ] `get_parameters()` - 取得當前參數
- [ ] 實現單元測試
  - [ ] 測試 LOS 狀態衰減
  - [ ] 測試 Shadowed 狀態衰減
  - [ ] 測試 Blocked 狀態（返回 inf）
- [ ] Code Review

#### 驗收標準
- ✅ 參數符合 Loo (1985) Table II
- ✅ 衰減計算符合 Equation (5)
- ✅ 單元測試覆蓋率 > 80%

---

### Day 3: PropagationConditionSimulator 整合器

#### 任務清單
- [ ] 實現 `PropagationConditionSimulator` 類別
  - [ ] `__init__()` - 初始化 Markov + Loo 模型
  - [ ] `simulate_propagation()` - 主要模擬接口
  - [ ] `reset_state()` - 重置衛星狀態
  - [ ] `get_statistics()` - 取得統計資訊
- [ ] 整合到 `stage5_signal_analysis_processor.py`
  - [ ] 在 `__init__()` 初始化模擬器
  - [ ] 在 `_calculate_signal_quality()` 調用模擬
  - [ ] 更新輸出格式（新增 `propagation_condition` 欄位）
- [ ] 實現整合測試
  - [ ] 測試完整 Stage 5 流程
  - [ ] 驗證輸出格式正確
- [ ] Code Review

#### 驗收標準
- ✅ 模擬器正確整合到 Stage 5
- ✅ 輸出包含 `propagation_condition` 欄位
- ✅ 向後兼容（現有欄位不變）

---

### Day 4: 配置與文檔

#### 任務清單
- [ ] 更新 `config/stage5_signal_analysis_config.yaml`
  - [ ] 新增 `enable_propagation_simulation` 開關
  - [ ] 新增 `markov_model` 配置區塊
  - [ ] 新增 `loo_channel` 配置區塊
  - [ ] 新增 SOURCE 註解
- [ ] 更新 Stage 5 文檔
  - [ ] `docs/stages/stage5-signal-quality-analysis.md`
  - [ ] 新增動態傳播章節
  - [ ] 新增 API 參考
  - [ ] 新增配置範例
- [ ] 創建範例腳本
  - [ ] `examples/stage5_propagation_demo.py`
- [ ] Code Review

#### 驗收標準
- ✅ 配置檔案完整有效
- ✅ 文檔清晰完整
- ✅ 範例可執行

---

### Day 5: Stage 5 測試與優化

#### 任務清單
- [ ] 端到端測試
  - [ ] 執行完整 Stage 1-5 流程
  - [ ] 驗證輸出格式
  - [ ] 檢查性能指標
- [ ] 性能優化
  - [ ] Profile 執行時間
  - [ ] 優化熱點代碼
  - [ ] 記憶體使用分析
- [ ] 學術合規性檢查
  - [ ] 執行 `make compliance`
  - [ ] 驗證所有 SOURCE 註解
  - [ ] 檢查引用完整性
- [ ] Bug 修復與調整
- [ ] 最終 Code Review

#### 驗收標準
- ✅ 執行時間增加 < 20%
- ✅ 記憶體使用增加 < 15%
- ✅ 學術合規性檢查通過

---

## 📦 Phase 2: Stage 6 擴充（場景多樣性）

### Day 1: 流量類型生成器

#### 任務清單
- [ ] 創建 `traffic_profile_generator.py` 檔案
- [ ] 定義 `TrafficProfile` dataclass
  - [ ] 欄位：type, max_delay_ms, min_bandwidth_kbps, min_reliability, priority
  - [ ] 驗證邏輯
  - [ ] SOURCE 註解
- [ ] 實現 `TrafficProfileGenerator` 類別
  - [ ] `__init__()` - 初始化預定義 profiles
  - [ ] `generate_variants()` - 生成流量變體
  - [ ] `get_profile()` - 取得單個 profile
  - [ ] `validate_profile()` - 驗證 profile
- [ ] 實現單元測試
  - [ ] 測試所有預定義 profiles
  - [ ] 測試變體生成
  - [ ] 測試驗證邏輯
- [ ] Code Review

#### 驗收標準
- ✅ 4 種流量類型定義正確
- ✅ QoS 參數符合 3GPP TS 22.261
- ✅ 單元測試通過

---

### Day 2: 衛星負載模擬器

#### 任務清單
- [ ] 創建 `satellite_load_simulator.py` 檔案
- [ ] 定義 `LoadPattern` enum
  - [ ] UNIFORM / CONCENTRATED / DYNAMIC
- [ ] 實現 `SatelliteLoadSimulator` 類別
  - [ ] `__init__()` - 初始化容量參數
  - [ ] `generate_loads()` - 主要接口
  - [ ] `_generate_uniform()` - 均勻負載
  - [ ] `_generate_concentrated()` - 集中負載
  - [ ] `_generate_dynamic()` - 動態負載
- [ ] 實現單元測試
  - [ ] 測試 3 種負載模式
  - [ ] 測試負載合理性
  - [ ] 測試邊界條件
- [ ] Code Review

#### 驗收標準
- ✅ 3 種負載模式實現正確
- ✅ 容量參數符合 3GPP TR 38.821
- ✅ 單元測試通過

---

### Day 3: 場景變體生成器

#### 任務清單
- [ ] 創建 `scenario_variant_generator.py` 檔案
- [ ] 實現 `ScenarioVariantGenerator` 類別
  - [ ] `__init__()` - 初始化 Traffic + Load 生成器
  - [ ] `generate_variants()` - 組合生成變體
  - [ ] `_combine_conditions()` - 組合流量×負載
  - [ ] `_assign_variant_id()` - 生成唯一 ID
- [ ] 整合到 `stage6_research_optimizer.py`
  - [ ] 在 `__init__()` 初始化變體生成器
  - [ ] 在 `optimize()` 調用變體生成
  - [ ] 更新輸出格式
- [ ] 實現整合測試
  - [ ] 測試完整 Stage 6 流程
  - [ ] 驗證變體數量正確（4×3=12）
- [ ] Code Review

#### 驗收標準
- ✅ 變體生成邏輯正確
- ✅ 變體 ID 唯一性
- ✅ 整合測試通過

---

### Day 4: 配置與文檔

#### 任務清單
- [ ] 更新 `config/stage6_research_optimization_config.yaml`
  - [ ] 新增場景多樣性配置區塊
  - [ ] 新增流量類型配置
  - [ ] 新增負載模擬配置
- [ ] 更新 Stage 6 文檔
  - [ ] `docs/stages/stage6-research-optimization.md`
  - [ ] 新增場景多樣性章節
  - [ ] 新增輸出格式說明
- [ ] 創建範例腳本
  - [ ] `examples/stage6_scenario_demo.py`
- [ ] Code Review

#### 驗收標準
- ✅ 配置檔案完整
- ✅ 文檔清晰
- ✅ 範例可執行

---

### Day 5: Stage 6 測試與優化

#### 任務清單
- [ ] 端到端測試
  - [ ] 執行完整 Stage 1-6 流程
  - [ ] 驗證變體輸出
  - [ ] 檢查檔案大小
- [ ] 性能優化
  - [ ] 並行變體生成
  - [ ] 記憶體優化
- [ ] 學術合規性檢查
- [ ] Bug 修復
- [ ] 最終 Code Review

#### 驗收標準
- ✅ 執行時間增加 < 30%
- ✅ 輸出檔案大小增加 < 50%
- ✅ 學術合規性檢查通過

---

## 📦 Phase 3: 整合測試（2-3 天）

### Day 1-2: 完整流程測試

#### 任務清單
- [ ] 準備測試環境
  - [ ] 清理輸出目錄
  - [ ] 準備測試配置
  - [ ] 備份現有數據
- [ ] 執行完整 6 階段流程
  - [ ] `./run.sh` (all stages)
  - [ ] 記錄執行時間
  - [ ] 記錄記憶體使用
- [ ] 驗證輸出
  - [ ] 檢查所有輸出檔案存在
  - [ ] 驗證輸出格式正確
  - [ ] 抽樣檢查數據合理性
- [ ] 性能基準測試
  - [ ] 與擴充前對比
  - [ ] 記錄性能指標
  - [ ] 生成性能報告

#### 驗收標準
- ✅ 完整流程無錯誤
- ✅ 所有輸出檔案格式正確
- ✅ 性能指標符合要求

---

### Day 3: 邊界條件與錯誤處理

#### 任務清單
- [ ] 測試邊界條件
  - [ ] 空數據輸入
  - [ ] 極端參數值
  - [ ] 配置錯誤
- [ ] 測試降級機制
  - [ ] 停用傳播模擬
  - [ ] 停用場景生成
  - [ ] 部分功能故障
- [ ] 測試向後兼容性
  - [ ] 使用舊版配置
  - [ ] 檢查現有功能不受影響
- [ ] Bug 修復與調整

#### 驗收標準
- ✅ 邊界條件處理正確
- ✅ 降級機制運作正常
- ✅ 向後兼容性保持

---

## 📦 Phase 4: 文檔完善（1-2 天）

### Day 1: 文檔更新

#### 任務清單
- [ ] 更新 `docs/ACADEMIC_STANDARDS.md`
  - [ ] 新增傳播模型章節
  - [ ] 新增場景生成章節
- [ ] 更新 `docs/stages/stage5-signal-quality-analysis.md`
  - [ ] 詳細動態傳播說明
  - [ ] API 參考
  - [ ] 配置範例
- [ ] 更新 `docs/stages/stage6-research-optimization.md`
  - [ ] 場景多樣性說明
  - [ ] 輸出格式文檔
  - [ ] 使用指南
- [ ] 更新 `README.md`
  - [ ] 新增功能說明
  - [ ] 更新執行範例
- [ ] 更新 `CHANGELOG.md`
  - [ ] 記錄版本更新
  - [ ] 列出新功能
  - [ ] 列出 Breaking Changes（無）

#### 驗收標準
- ✅ 所有文檔更新完整
- ✅ 文檔風格一致
- ✅ 無拼寫錯誤

---

### Day 2: Code Review 與發布準備

#### 任務清單
- [ ] 最終 Code Review
  - [ ] 代碼風格檢查
  - [ ] 註解完整性
  - [ ] SOURCE 引用檢查
- [ ] 創建 PR (Pull Request)
  - [ ] 撰寫 PR 描述
  - [ ] 附上測試報告
  - [ ] 請求審核
- [ ] 準備發布筆記
  - [ ] 功能摘要
  - [ ] 使用指南
  - [ ] 已知問題
- [ ] 更新版本號
  - [ ] `__version__` 更新
  - [ ] Git tag 創建

#### 驗收標準
- ✅ Code Review 通過
- ✅ PR 創建完成
- ✅ 發布筆記準備完成

---

## 🎯 里程碑

| 里程碑 | 預計日期 | 完成標準 | 狀態 |
|--------|---------|---------|------|
| M1: Stage 5 擴充完成 | Week 1 結束 | Stage 5 輸出包含 `propagation_condition` | 🔄 規劃中 |
| M2: Stage 6 擴充完成 | Week 2 結束 | Stage 6 輸出包含 `scenario_variants` | ⏳ 待開始 |
| M3: 整合測試通過 | Week 3 中 | 完整流程無錯誤，性能達標 | ⏳ 待開始 |
| M4: 文檔完善發布 | Week 3 結束 | 所有文檔更新，PR 合併 | ⏳ 待開始 |

---

## ⚠️ 風險管理

### 高風險項目

1. **3GPP 標準理解困難**
   - **風險**: Markov/Loo 參數理解錯誤
   - **緩解**: 預先閱讀論文原文，請教領域專家
   - **應變**: 使用簡化模型（但標註為簡化）

2. **性能超標**
   - **風險**: 執行時間增加 > 30%
   - **緩解**: 及早 profiling，優化熱點
   - **應變**: 提供高性能模式（降低變體數量）

3. **測試覆蓋不足**
   - **風險**: 未發現邊界條件 bug
   - **緩解**: 編寫詳細測試計劃，使用 property-based testing
   - **應變**: 增加測試時間（Phase 3 延長）

### 中風險項目

4. **配置複雜度**
   - **風險**: 用戶配置錯誤導致運行失敗
   - **緩解**: 提供詳細文檔、驗證邏輯、預設值
   - **應變**: 創建配置檢查工具

5. **輸出檔案過大**
   - **風險**: 變體數量導致檔案 > 100MB
   - **緩解**: 使用 HDF5 或壓縮格式
   - **應變**: 支援分檔輸出

---

## 📊 進度追蹤

### 每日 Standup

**時間**: 每天 10:00 AM
**參與人員**: Dev Team, QA Team
**議程**:
1. 昨日完成任務
2. 今日計劃任務
3. 遇到的阻礙

### 每週 Review

**時間**: 每週五 3:00 PM
**參與人員**: 全體成員
**議程**:
1. 本週里程碑檢查
2. 性能指標回顧
3. 風險評估更新
4. 下週計劃

---

## 📝 文檔清單（詳見 07-DOCUMENTATION-UPDATES.md）

- 10+ 份文檔需要更新
- 5+ 份新文檔需要創建
- 詳細清單見專門文檔

---

**下一步**: 檢閱實施計劃，確認資源與時間後開始 Phase 1 開發。
