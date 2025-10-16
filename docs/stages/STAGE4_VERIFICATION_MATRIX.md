# Stage 4 驗證狀態矩陣 (唯一真相來源)

**用途**: 明確記錄每項功能的實現與驗證狀態
**更新頻率**: 每次代碼修改後必須同步更新
**最後更新**: 2025-10-16 (✨ 重大更新: 6項完全實現 - 增強項目 #2 和 #5)

---

## 📊 驗證項目對照表

| # | 驗證項目 | 代碼實現位置 | 驗證腳本位置 | 強制執行 | 狀態 | 最後驗證 |
|---|---------|------------|------------|---------|------|---------|
| 1 | constellation_threshold_validation | `stage4_link_feasibility_processor.py:220-250` | `run_six_stages_with_validation.py:786-798` | ✅ | ✅ **完全實現** | 2025-10-02 |
| 2 | visibility_calculation_accuracy | `skyfield_visibility_calculator.py:93-175` | `stage4_validator.py:483-587` | ✅ | ✅ **完全實現** | 2025-10-16 |
| 3 | link_budget_constraints | `stage4_link_feasibility_processor.py:180-200` | `run_six_stages_with_validation.py:819-823` | ✅ | ✅ **完全實現** | 2025-10-02 |
| 4 | ntpu_coverage_analysis | `stage4_link_feasibility_processor.py:300-350` | `run_six_stages_with_validation.py:800-817` | ✅ | ✅ **完全實現** | 2025-10-02 |
| 5 | service_window_optimization | `service_window_calculator.py` + `stage4_link_feasibility_processor.py:510-658` | `stage4_validator.py:589-691` | ✅ | ✅ **完全實現** | 2025-10-16 |
| 6 | stage_4_2_pool_optimization | `pool_optimizer.py:1-585` | `run_six_stages_with_validation.py:785-840` | ✅ | ✅ **完全實現** | 2025-10-01 |

---

## 🔍 詳細驗證規格

### ✅ 項目6: stage_4_2_pool_optimization (CRITICAL)

**代碼實現**:
- 文件: `src/stages/stage4_link_feasibility/pool_optimizer.py`
- 類別: `PoolSelector`, `CoverageOptimizer`, `OptimizationValidator`
- 行號: 1-535

**驗證腳本**:
- 文件: `scripts/run_six_stages_with_validation.py`
- 行號: 746-801
- 檢查項目:
  ```python
  # 行 746: 強制檢查階段 4.2 完成
  if not stage_4_2_completed:
      return False, "❌ Stage 4.2 池規劃優化未完成"

  # 行 764: 覆蓋率檢查
  if coverage_rate < 0.95:
      return False, f"❌ Starlink 覆蓋率不足: {coverage_rate:.1%}"

  # 行 772: 平均可見數檢查
  if not (10 <= avg_visible <= 15):
      return False, f"❌ Starlink 平均可見數不符: {avg_visible:.1f}"

  # 行 779: 覆蓋空窗檢查
  if gap_count > 0:
      return False, f"❌ Starlink 存在覆蓋空窗: {gap_count} 個"
  ```

**測試命令**:
```bash
python scripts/run_six_stages_with_validation.py --stage 4
```

**驗證通過標準**:
- ✅ `stage_4_2_completed = True`
- ✅ Starlink 覆蓋率 ≥ 95%
- ✅ 平均可見數 10-15 顆
- ✅ 無覆蓋空窗 (gap_count = 0)

---

### ✅ 項目1: constellation_threshold_validation (完全實現)

**代碼實現**:
- 文件: `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`
- 函數: `_apply_constellation_threshold()`
- 行號: 約 220-250
- 邏輯: Starlink 5° 門檻, OneWeb 10° 門檻

**驗證腳本**: ✅ **已實現**
- 文件: `scripts/run_six_stages_with_validation.py`
- 行號: 786-798
- 檢查項目:
  ```python
  # 行 788: 檢查星座感知功能
  constellation_aware = metadata.get('constellation_aware', False)
  if not constellation_aware:
      return False, "❌ Stage 4 星座感知功能未啟用"

  # 行 795: 檢查星座分類數據
  candidate_by_const = candidate_pool.get('by_constellation', {})
  if not candidate_by_const:
      return False, "❌ Stage 4 星座分類數據缺失"
  ```

**驗證通過標準**:
- ✅ `constellation_aware = True`
- ✅ `by_constellation` 數據結構完整
- ✅ Starlink 和 OneWeb 正確分類

**狀態**: ✅ 代碼已實現，驗證腳本已實現並強制執行

---

### ✅ 項目2: visibility_calculation_accuracy (完全實現 - 2025-10-16增強)

**代碼實現**:
- 文件: `src/stages/stage4_link_feasibility/skyfield_visibility_calculator.py`
- 函數: `calculate_visibility_metrics()`, `calculate_topocentric_position()`
- 行號: 93-175
- 邏輯: 使用 Skyfield IAU 標準計算仰角、方位角、距離

**驗證腳本**: ✅ **已完整實現**
- 文件: `scripts/stage_validators/stage4_validator.py`
- 函數: `_validate_visibility_accuracy()`
- 行號: 483-587
- 檢查項目:
  ```python
  # 1. IAU 標準使用驗證
  if not use_iau_standards:
      return False, "❌ Stage 4 未使用 IAU 標準座標計算"

  # 2. 候選池數量範圍驗證
  if candidate_total < 100 or candidate_total > 5000:
      return False, f"❌ Stage 4 候選池數量異常: {candidate_total} 顆"

  # 3. ✅ 新增: visibility_metrics 數據結構驗證
  # 4. ✅ 新增: 仰角/方位角/距離合理性檢查
  if not (-90 <= elevation <= 90):
      return False, f"❌ 仰角數值異常: {elevation}°"

  # 5. ✅ 新增: 星座感知門檻驗證
  if threshold != 5.0:  # Starlink
      return False, f"⚠️ Starlink 仰角門檻異常: {threshold}°"
  ```

**驗證通過標準**:
- ✅ `use_iau_standards = True`
- ✅ 候選池數量在 100-5000 範圍
- ✅ visibility_metrics 數據結構完整
- ✅ 仰角 (-90~90°), 方位角 (0~360°), 距離 (200~2500km) 合理
- ✅ Starlink 門檻 = 5.0°

**狀態**: ✅ 代碼已實現，驗證腳本已增強並強制執行

---

### ✅ 項目5: service_window_optimization (完全實現 - 2025-10-16增強)

**代碼實現**:
- 文件: `src/stages/stage4_link_feasibility/data_processing/service_window_calculator.py`
- 文件: `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`
- 函數: `_analyze_ntpu_coverage()`
- 行號: 510-658
- 邏輯: 計算服務窗口、覆蓋連續性、空窗檢測

**驗證腳本**: ✅ **已完整實現**
- 文件: `scripts/stage_validators/stage4_validator.py`
- 函數: `_validate_service_windows()`
- 行號: 589-691
- 檢查項目:
  ```python
  # 1. 覆蓋空窗時間長度驗證
  long_gaps = [gap for gap in coverage_gaps if gap > 30.0]
  if long_gaps:
      return False, f"❌ Stage 4 存在過長覆蓋空窗"

  # 2. 覆蓋空窗總數驗證
  if len(coverage_gaps) > 5:
      return False, f"❌ Stage 4 覆蓋空窗過多"

  # 3. ✅ 新增: service_window 數據結構驗證
  required_fields = ['start_time', 'end_time', 'duration_minutes', 'time_points_count']

  # 4. ✅ 新增: 時間窗口連續性驗證
  if start >= end:
      return False, f"❌ 服務窗口時間順序錯誤"

  # 5. ✅ 新增: 持續時間計算正確性驗證
  if duration_diff > 1.0:
      return False, f"❌ 服務窗口持續時間計算錯誤"
  ```

**驗證通過標準**:
- ✅ 覆蓋空窗 < 30 分鐘
- ✅ 覆蓋空窗總數 ≤ 5 個
- ✅ service_window 數據結構完整
- ✅ start_time < end_time
- ✅ 持續時間計算正確 (誤差 < 1 分鐘)
- ✅ 持續時間合理 (0.5~30 分鐘)

**狀態**: ✅ 代碼已實現，驗證腳本已增強並強制執行

---

### ✅ 項目3-4: 其他完全實現項目

**項目3**: link_budget_constraints ✅ 完全實現
**項目4**: ntpu_coverage_analysis ✅ 完全實現

詳細規格請參考原有文檔章節

---

## 🚨 使用規則 (防止文檔與代碼脫鉤)

### 規則1: 單一真相來源
- ✅ **此文件是驗證狀態的唯一真相來源**
- ❌ 其他文檔（包括 stage4-link-feasibility.md）不得聲稱驗證狀態
- ✅ 其他文檔應**引用此矩陣文件**，而非重複聲明

### 規則2: 同步更新要求
- 添加新驗證項目 → 必須更新此矩陣
- 實現驗證腳本 → 必須更新對應行號和狀態
- 修改代碼位置 → 必須更新代碼實現位置

### 規則3: 狀態定義
- ✅ **已實現**: 代碼實現 + 驗證腳本存在 + 強制執行
- ⚠️ **未驗證**: 代碼實現 + 驗證腳本不存在
- ❌ **未實現**: 代碼未實現 + 驗證腳本不存在

### 規則4: 驗證流程
1. 查看此矩陣確認狀態
2. 找到對應代碼位置
3. 找到驗證腳本位置（如果存在）
4. 執行測試命令驗證
5. 更新"最後驗證"欄位

---

## 📝 更新記錄

| 日期 | 更新內容 | 負責人 |
|------|---------|--------|
| 2025-10-16 | ✨ 增強項目 #2 和 #5 驗證 - 6項全部完全實現 | Claude Code |
| 2025-10-01 | 創建驗證狀態矩陣，記錄當前實際狀態 | Claude Code |

---

**重要提醒**: 當 AI 助手檢查 Stage 4 驗證狀態時，**必須先查閱此文件**，而非假設文檔聲稱的功能都已實現。
