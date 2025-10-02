# 📋 Stage 4 重構計劃總覽

**重構版本**: v2.0
**創建日期**: 2025-09-30
**目標**: 將 Stage 4 實現提升至 100% 文檔合規和學術標準

---

## 🎯 重構目標

當前 Stage 4 實現**約 40% 符合規範**，存在以下關鍵問題:
- ❌ 缺少鏈路預算距離約束 (200-2000km)
- ❌ 輸出結構不符合時間序列規範
- ❌ 使用自製幾何算法 (不符合學術標準)
- ❌ 缺少階段 4.2 動態池規劃功能

**重構後目標**: 100% 符合 `stage4-link-feasibility.md` 和 `academic_standards_clarification.md` 要求

---

## 📦 重構計劃架構

### 三階段漸進式重構

```
┌─────────────────────────────────────────────────────────────┐
│                 Stage 4 重構路線圖                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📍 計劃 A: 核心功能修正 (P0 - 關鍵)                          │
│  ├─ 添加鏈路預算距離檢查 (200-2000km)                        │
│  ├─ 修改輸出結構為完整時間序列格式                            │
│  └─ 每個時間點添加 is_connectable 標記                       │
│                                                             │
│  ⏱️  預估工時: 4-6 小時                                      │
│  📄 文檔: plan-a-core-functionality.md                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📍 計劃 B: 學術標準升級 (P1 - 重要)                          │
│  ├─ 整合 Skyfield 專業天文計算庫                             │
│  ├─ 替換自製幾何算法為 IAU 標準實現                           │
│  └─ 驗證 Stage 1 epoch_datetime 使用                        │
│                                                             │
│  ⏱️  預估工時: 3-4 小時                                      │
│  📄 文檔: plan-b-academic-standards.md                       │
│  🔗 依賴: 計劃 A                                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📍 計劃 C: 動態池規劃 (P2 - 增強)                            │
│  ├─ 實現時空分布分析器                                       │
│  ├─ 實現池優化算法 (貪心算法版本)                             │
│  └─ 確保任意時刻維持目標可見數量                              │
│                                                             │
│  ⏱️  預估工時: 6-8 小時                                      │
│  📄 文檔: plan-c-dynamic-pool-planning.md                    │
│  🔗 依賴: 計劃 A + 計劃 B                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

總工時: 13-18 小時
建議執行: 分 3 次完成，每次執行一個計劃
```

---

## 📋 計劃詳情

### 計劃 A: 核心功能修正

**目標**: 修正基本功能缺失，確保數據結構正確

**關鍵任務**:
- ✅ 任務 A.1: 添加 LinkBudgetAnalyzer 類
- ✅ 任務 A.2: 修改輸出為完整時間序列結構
- ✅ 任務 A.3: 添加方位角計算

**交付物**:
- `link_budget_analyzer.py` (新建)
- `stage4_link_feasibility_processor.py` (修改)
- `constellation_filter.py` (修改)
- `ntpu_visibility_calculator.py` (修改)

**驗收標準**:
- [ ] 所有時間點包含距離檢查 (200-2000km)
- [ ] 輸出包含完整 `time_series[]` 數組
- [ ] 每個時間點有正確的 `is_connectable` 布爾值

📄 **詳細文檔**: [plan-a-core-functionality.md](./plan-a-core-functionality.md)

---

### 計劃 B: 學術標準升級

**目標**: 使用專業庫確保學術標準合規

**關鍵任務**:
- ✅ 任務 B.1: 整合 Skyfield 專業計算庫
- ✅ 任務 B.2: 驗證 Stage 1 epoch_datetime

**交付物**:
- `skyfield_visibility_calculator.py` (新建)
- `epoch_validator.py` (新建)
- `stage4_link_feasibility_processor.py` (修改)
- `requirements.txt` (添加 skyfield 依賴)

**驗收標準**:
- [ ] 使用 Skyfield 進行所有可見性計算
- [ ] 計算精度符合 IAU 標準 (仰角誤差 < 0.1°)
- [ ] Epoch 多樣性驗證通過

📄 **詳細文檔**: [plan-b-academic-standards.md](./plan-b-academic-standards.md)

---

### 計劃 C: 動態池規劃

**目標**: 實現階段 4.2，確保任意時刻目標可見數量

**關鍵任務**:
- ✅ 任務 C.1: 時空分布分析器
- ✅ 任務 C.2: 池優化算法 (貪心版本)
- ✅ 任務 C.3: 整合到主處理器

**交付物**:
- `temporal_spatial_analyzer.py` (新建)
- `pool_optimizer.py` (新建)
- `stage4_link_feasibility_processor.py` (修改)

**驗收標準**:
- [ ] Starlink 最優池: ~500 顆
- [ ] OneWeb 最優池: ~100 顆
- [ ] 覆蓋率 ≥ 95%
- [ ] 任意時刻可見數在目標範圍內

📄 **詳細文檔**: [plan-c-dynamic-pool-planning.md](./plan-c-dynamic-pool-planning.md)

---

## 🚀 執行指南

### 推薦執行順序

#### 第 1 次執行: 計劃 A (4-6 小時)
```bash
# 1. 閱讀計劃文檔
cat docs/refactoring/stage4/plan-a-core-functionality.md

# 2. 創建新分支
git checkout -b feature/stage4-refactor-plan-a

# 3. 執行任務 A.1-A.3
# ... 實現代碼 ...

# 4. 運行測試
python -m pytest tests/stages/stage4/test_link_budget.py
python -m pytest tests/stages/stage4/test_time_series_output.py

# 5. 驗證 Stage 4 單獨運行
python scripts/run_six_stages_with_validation.py --stage 4

# 6. 提交代碼
git add .
git commit -m "feat(stage4): 實現計劃 A - 核心功能修正"
git push origin feature/stage4-refactor-plan-a
```

#### 第 2 次執行: 計劃 B (3-4 小時)
```bash
# 1. 確保計劃 A 已完成並合併
git checkout main
git pull

# 2. 創建新分支
git checkout -b feature/stage4-refactor-plan-b

# 3. 安裝 Skyfield 依賴
pip install skyfield

# 4. 執行任務 B.1-B.2
# ... 實現代碼 ...

# 5. 運行精度測試
python -m pytest tests/stages/stage4/test_skyfield_precision.py
python -m pytest tests/stages/stage4/test_epoch_validation.py

# 6. 驗證 Stage 4
python scripts/run_six_stages_with_validation.py --stage 4

# 7. 提交代碼
git add .
git commit -m "feat(stage4): 實現計劃 B - 學術標準升級"
```

#### 第 3 次執行: 計劃 C (6-8 小時)
```bash
# 1. 確保計劃 A + B 已完成
git checkout main
git pull

# 2. 創建新分支
git checkout -b feature/stage4-refactor-plan-c

# 3. 執行任務 C.1-C.3
# ... 實現代碼 ...

# 4. 運行優化測試
python -m pytest tests/stages/stage4/test_temporal_analysis.py
python -m pytest tests/stages/stage4/test_pool_optimization.py

# 5. 驗證完整流程
python scripts/run_six_stages_with_validation.py

# 6. 提交代碼
git add .
git commit -m "feat(stage4): 實現計劃 C - 動態池規劃"
```

---

## 📊 進度追蹤

### 計劃執行檢查清單

#### 計劃 A: 核心功能修正
- [ ] LinkBudgetAnalyzer 類實現
- [ ] 距離檢查集成到篩選流程
- [ ] 時間序列輸出結構修改
- [ ] `is_connectable` 標記添加
- [ ] 方位角計算實現
- [ ] 單元測試通過
- [ ] Stage 4 獨立運行驗證
- [ ] 代碼審查完成

#### 計劃 B: 學術標準升級
- [ ] Skyfield 庫安裝
- [ ] SkyfieldVisibilityCalculator 類實現
- [ ] 替換舊的可見性計算方法
- [ ] EpochValidator 類實現
- [ ] Epoch 驗證集成
- [ ] 精度測試通過 (誤差 < 0.1°)
- [ ] Stage 4 獨立運行驗證
- [ ] 代碼審查完成

#### 計劃 C: 動態池規劃
- [ ] TemporalSpatialAnalyzer 類實現
- [ ] PoolOptimizer 類實現 (貪心算法)
- [ ] 主處理器集成
- [ ] 時空覆蓋分析測試
- [ ] 池優化算法測試
- [ ] 覆蓋率驗證 (≥ 95%)
- [ ] 完整六階段流程驗證
- [ ] 代碼審查完成

---

## 🧪 測試策略

### 單元測試
- 每個新增類都需要對應的單元測試
- 測試覆蓋率目標: ≥ 80%

### 集成測試
- 每個計劃完成後運行 Stage 4 獨立測試
- 計劃 C 完成後運行完整六階段流程測試

### 驗收測試
- 檢查輸出數據結構符合文檔規範
- 檢查數據量符合預期範圍
- 檢查性能指標符合要求

---

## ⚠️ 風險管理

### 已知風險

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| Skyfield 性能問題 | 計算時間增加 | 並行化處理，預先下載星曆表 |
| 時間序列數據量大 | 記憶體壓力 | 批次處理，使用生成器 |
| 優化算法參數調整 | 多次迭代 | 預留調整時間，使用配置文件 |
| Stage 3 數據不完整 | 無法測試 | 先驗證 Stage 1-3 流程 |

### 依賴關係

```
Stage 1 (數據載入)
    ↓
Stage 2 (軌道傳播)
    ↓
Stage 3 (座標轉換)
    ↓
[計劃 A] → [計劃 B] → [計劃 C]
    ↓
Stage 5 (信號分析)
    ↓
Stage 6 (研究優化)
```

---

## 📈 成功指標

### 功能完整性
- [ ] 所有文檔要求的功能已實現
- [ ] 所有驗收標準通過
- [ ] 所有測試通過

### 學術合規性
- [ ] 使用 Skyfield IAU 標準計算
- [ ] 精度符合研究級標準
- [ ] Epoch 時間基準正確

### 性能指標
- [ ] 處理 9000 顆衛星 < 10 秒
- [ ] 記憶體使用 < 2GB
- [ ] 覆蓋率 ≥ 95%

### 數據質量
- [ ] Starlink 可見數: 10-15 顆 (任意時刻)
- [ ] OneWeb 可見數: 3-6 顆 (任意時刻)
- [ ] 輸出數據結構 100% 符合規範

---

## 📚 參考文檔

### 核心規範文檔
- `docs/stages/stage4-link-feasibility.md` - Stage 4 完整規格
- `docs/academic_standards_clarification.md` - 學術標準要求

### 技術參考
- Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
- Kodheli, O., et al. (2021). Satellite communications in the new space era
- Rhodes, B. (2019). Skyfield: High precision research-grade positions

### 相關代碼
- `src/stages/stage1_orbital_calculation/` - Stage 1 參考實現
- `src/stages/stage2_orbital_computing/` - Stage 2 v3.0 參考
- `src/stages/stage3_coordinate_transformation/` - Stage 3 參考

---

## 🤝 團隊協作

### 代碼審查要求
- 每個計劃完成後需進行代碼審查
- 審查重點: 學術標準合規、性能、可維護性

### 文檔更新
- 實現完成後更新 `stage4-link-feasibility.md` 實現狀態
- 記錄實際數據與估算的差異

### 知識分享
- 每個計劃完成後進行技術分享
- 記錄遇到的問題和解決方案

---

## 📞 聯絡資訊

**負責團隊**: Orbit Engine Team
**創建日期**: 2025-09-30
**文檔版本**: v1.0

---

**重構路線圖**: 計劃 A → 計劃 B → 計劃 C → 100% 合規 ✅