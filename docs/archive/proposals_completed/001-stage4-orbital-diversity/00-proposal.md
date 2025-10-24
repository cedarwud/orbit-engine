# Stage 4 池優化算法改進計劃
## 軌道面多樣性約束實施

**文件版本**: v1.0
**創建日期**: 2025-10-22
**作者**: Orbit Engine 開發團隊
**狀態**: 📋 待審核

---

## 📋 執行摘要

**問題**: 當前 Stage 4 池優化算法僅優化時間覆蓋率，導致選中的衛星聚集於少數軌道面，造成空間分佈不均。

**影響**: RL 訓練數據質量不佳，換手頻率不穩定，與學術論文方法論差異過大。

**解決方案**: 實施兩階段選擇算法，增加軌道面多樣性約束。

**預期收益**:
- ✅ 軌道面數量：19 → 24 個（增加 26%）
- ✅ Gini 係數：0.429 → < 0.3（改善 30%）
- ✅ 對齊學術論文方法論（48-50 顆衛星，24 個軌道面）
- ✅ RL 訓練換手頻率穩定化

**工程量**: ~200-250 行代碼，3-4 小時開發，5 個實施階段

---

## 1. 問題陳述與根因分析

### 1.1 問題描述

**當前狀況**（基於 2025-10-22 Stage 4 輸出分析）:

```
Starlink 優化池: 98 顆衛星
軌道面數量: 僅 19 個
每面平均衛星數: 5.2 顆
Gini 係數: 0.429 (中度聚類)

部分軌道面過度聚類:
  20°-25° RAAN:  12 顆 (12.2%)
  30°-35° RAAN:  12 顆 (12.2%)
  145°-150° RAAN: 12 顆 (12.2%)
  155°-160° RAAN: 11 顆 (11.2%)
```

**對比學術論文典型配置**:

| 指標 | 論文典型 | 我們的配置 | 差異 |
|------|---------|-----------|------|
| 衛星數量 | 48-50 顆 | 98 顆 | +96% ❌ |
| 軌道面數量 | ~24 個 | 19 個 | -21% ❌ |
| 每面衛星數 | 2 顆 | 5.2 顆 | +160% ❌ |
| 軌道面間隔 | 15° | 18.9° | +26% ⚠️ |

**參考文獻**:
- IEEE IoT Journal 2024 - User-Centric Handover: 48 顆衛星
- IEEE TWC 2021 - Load-Aware Handover: 50 顆衛星
- 典型軌道面配置：24-36 個面（Starlink 72 個面的 1/3 採樣）

### 1.2 根本原因分析

**當前算法**（`pool_optimizer.py:203-256`）:

```python
def _select_next_best_satellite(...):
    """
    Greedy Set Cover 算法
    目標：最小化衛星數量，達成時間覆蓋率目標
    """
    for satellite in candidates:
        contribution = 0
        for time_point in satellite['time_series']:
            current_visible = len(current_coverage.get(timestamp, set()))

            # ⚠️ 只檢查「這個時間點可見數量 < 目標」
            if current_visible < self.target_min:
                contribution += 1

        # 選擇貢獻度最高的衛星
        if contribution > best_contribution:
            best_satellite = satellite
```

**算法盲點**:
1. ✅ **優化目標**: 任何時刻有 10-15 顆可見（時間覆蓋）
2. ❌ **忽略因素**: 衛星的空間分佈（軌道面多樣性）
3. ❌ **導致結果**: 選中的衛星可能來自相同/相鄰軌道面

**學術依據**:
- SOURCE: Chvátal, V. (1979). "A greedy heuristic for the set-covering problem"
- 標準 Greedy Set Cover 僅優化覆蓋率，不考慮元素多樣性
- 需要增加多樣性約束（Diversity-Aware Set Cover）

### 1.3 影響分析

**對 RL 訓練的影響**:

1. **換手頻率不穩定**:
   - 某些時段：12 顆同軌道面衛星同時經過 → 過度換手
   - 其他時段：僅 2-3 顆可見 → 換手機會不足

2. **訓練數據質量**:
   - 狀態分佈不均勻（某些 RAAN 過度代表）
   - 動作空間偏差（某些軌道面過度採樣）

3. **與論文方法論差異**:
   - 論文：均勻分佈於多個軌道面 → 穩定換手機會
   - 我們：聚集於少數軌道面 → 不規則換手模式

**學術合規性風險**:
- ⚠️ 與主流研究方法論差異過大（98 vs 48 顆，19 vs 24 面）
- ⚠️ 可能影響論文可信度和可比較性

---

## 2. 目標與成功標準

### 2.1 核心目標

**主要目標**:
1. 增加軌道面多樣性（19 → 24+ 個軌道面）
2. 降低 Gini 係數（0.429 → < 0.3）
3. 減少衛星總數（98 → 48-72 顆）
4. 對齊學術論文方法論

**次要目標**:
5. 保持時間覆蓋率（≥ 93%，允許略低於當前 96.3%）
6. 向後兼容（可配置開關，不破壞現有流程）

### 2.2 成功標準

**定量指標**:

| 指標 | 當前值 | 目標值 | 驗證方法 |
|------|--------|--------|----------|
| **軌道面數量** | 19 | ≥ 24 | RAAN 分組統計 |
| **Gini 係數** | 0.429 | < 0.3 | 軌道面分佈均勻性 |
| **衛星總數** | 98 | 48-72 | 優化池大小 |
| **每面衛星數** | 5.2 | 2-3 | 平均值 |
| **時間覆蓋率** | 96.3% | ≥ 93% | 達標時間點比例 |
| **平均可見數** | 10.7 | 10-15 | 目標範圍達成 |

**定性標準**:
- ✅ 不破壞 Stage 5, 6 下游流程
- ✅ 配置可選（YAML 參數控制）
- ✅ 學術合規（算法有文獻引用）

### 2.3 驗證方法

**自動化驗證**（運行 Stage 4 後）:

```bash
# 運行分析腳本
python /tmp/analyze_orbital_distribution.py

# 檢查指標
- RAAN bins ≥ 24
- Gini coefficient < 0.3
- Coverage rate ≥ 93%
```

**人工檢查**:
- 視覺化軌道面分佈圖（可選）
- 與論文配置對比

---

## 3. 解決方案設計

### 3.1 方案對比

#### 選項 A: 硬約束（每面最多 N 顆）⭐⭐

**實施方式**:
```python
if raan_bins[raan_bin] >= MAX_PER_ORBITAL_PLANE:
    continue  # 跳過此衛星
```

**優點**:
- ✅ 簡單直接
- ✅ 強制保證每面 ≤ N 顆

**缺點**:
- ❌ 可能降低覆蓋率（如果某些軌道面貢獻度高）
- ❌ 參數敏感（N 需要手動調優）

**評估**: 適合快速原型，但不夠靈活

---

#### 選項 B: 軟約束（多樣性獎勵）⭐⭐

**實施方式**:
```python
diversity_bonus = WEIGHT * (1.0 / (raan_bins[raan_bin] + 1))
score = contribution + diversity_bonus
```

**優點**:
- ✅ 平衡覆蓋率和多樣性
- ✅ 漸進式改進

**缺點**:
- ❌ 需要調參（WEIGHT）
- ❌ 效果不如硬約束明確

**評估**: 適合微調，但初期改進不明顯

---

#### 選項 C: 兩階段選擇 ⭐⭐⭐⭐⭐ **（推薦）**

**實施方式**:

```python
def optimize_pool(candidates):
    # 階段 1: 均勻採樣軌道面（保證多樣性基線）
    representatives = select_raan_representatives(
        candidates,
        target_planes=24  # 確保至少 24 個軌道面
    )

    # 階段 2: Greedy 填補覆蓋缺口（優化時間覆蓋）
    while not coverage_achieved(selected):
        best = select_next_best_satellite(
            candidates,
            max_per_plane=3  # 限制每面最多再加 2 顆
        )
        selected.append(best)

    return selected
```

**階段 1 詳細邏輯**:
```python
def select_raan_representatives(candidates, target_planes):
    """
    均勻採樣軌道面代表

    策略：
    1. 將 360° RAAN 均勻分割為 target_planes 個 bins
    2. 從每個 bin 選擇貢獻度最高的 1 顆

    SOURCE: Diversity-Aware Set Cover
           (參考 Kumar et al. "Diversity in Combinatorial Optimization")
    """
    bin_size = 360 / target_planes  # 例如 360/24 = 15°
    raan_groups = defaultdict(list)

    for sat in candidates:
        raan = get_raan_from_tle(sat)
        bin_id = int(raan // bin_size)
        raan_groups[bin_id].append(sat)

    representatives = []
    for bin_id in range(target_planes):
        if bin_id not in raan_groups:
            continue

        # 選該組內時間序列最長的（最有貢獻潛力）
        best = max(
            raan_groups[bin_id],
            key=lambda s: count_connectable_timepoints(s)
        )
        representatives.append(best)

    return representatives
```

**優點**:
- ✅ **保證軌道面多樣性**（階段 1 均勻採樣）
- ✅ **保證時間覆蓋率**（階段 2 Greedy 優化）
- ✅ **參數可控**（target_planes, max_per_plane）
- ✅ **對齊論文方法論**
- ✅ **學術合規**（有文獻引用）

**缺點**:
- ⚠️ 實現複雜度稍高（~200 行代碼）
- ⚠️ 需要訪問 TLE 數據（需要從 Stage 1 讀取）

**評估**: **最佳方案**，兼顧多樣性、覆蓋率和學術合規

---

### 3.2 推薦方案：選項 C（兩階段選擇）

**選擇理由**:
1. 學術合規性最高（有理論基礎）
2. 效果最可控（兩個階段各司其職）
3. 與論文方法論對齊
4. 參數可調整（易於優化）

**預期結果**:

```
階段 1 完成後:
  - 選中 24 顆衛星（每個軌道面 1 顆）
  - 軌道面數量 = 24
  - 時間覆蓋率 ~70-80%（基線）

階段 2 完成後:
  - 再選中 24-48 顆（填補覆蓋缺口）
  - 總計 48-72 顆
  - 軌道面數量 = 24（不變）
  - 每面 2-3 顆
  - 時間覆蓋率 93-98%
```

---

## 4. 實施計劃

### 4.1 階段劃分

**Phase 1: TLE 讀取與 RAAN 解析** (30 分鐘)
- 實施 `_get_raan_from_tle()` 方法
- 從 Stage 1 讀取 TLE 數據
- 單元測試：驗證 RAAN 解析正確性

**Phase 2: 軌道面代表選擇** (45 分鐘)
- 實施 `_select_raan_representatives()` 方法
- RAAN 均勻分組邏輯
- 單元測試：驗證每個 bin 選出代表

**Phase 3: 兩階段優化主流程** (60 分鐘)
- 重構 `optimize_pool()` 方法
- 修改 `_select_next_best_satellite()` 增加 max_per_plane 約束
- 整合階段 1 和階段 2

**Phase 4: 配置與驗證** (60 分鐘)
- 更新 `config/stage4_link_feasibility_config.yaml`
- 運行 Stage 4，檢查輸出
- 驗證 Gini < 0.3, 覆蓋率 ≥ 93%

**Phase 5: 參數調優（如需要）** (30 分鐘)
- 調整 `target_orbital_planes` (24 → 28 或 20)
- 調整 `max_satellites_per_plane` (3 → 4 或 2)
- 選擇最優配置

**總計**: 3.5-4 小時

### 4.2 文件修改清單

**核心代碼**:
1. `src/stages/stage4_link_feasibility/pool_optimizer.py`
   - 新增 `_get_raan_from_tle()` (~50 行)
   - 新增 `_select_raan_representatives()` (~80 行)
   - 修改 `optimize_pool()` (~30 行修改)
   - 修改 `_select_next_best_satellite()` (~20 行修改)
   - **總計: ~180 行新增/修改**

2. `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`
   - 傳遞 Stage 1 TLE 數據給 pool_optimizer (~10 行)

**配置文件**:
3. `config/stage4_link_feasibility_config.yaml`
   ```yaml
   pool_optimization:
     starlink:
       # 現有配置...
       target_min: 10
       target_max: 15

       # 新增配置
       orbital_diversity:
         enabled: true                    # 開關
         target_orbital_planes: 24        # 目標軌道面數
         max_satellites_per_plane: 3      # 每面最多衛星數
         raan_bin_size_deg: 15            # RAAN 分組大小 (360/24)
   ```

**文檔更新**:
4. `docs/stages/stage4-link-feasibility.md`
   - 增加「4.2.1 軌道面多樣性算法」章節

5. `docs/development/STAGE4_ORBITAL_DIVERSITY_IMPROVEMENT_PLAN.md`
   - 本文件（計劃書）

**測試**:
6. 新增分析腳本 `/tmp/analyze_orbital_distribution.py`（已存在）

### 4.3 數據流設計

**TLE 數據傳遞**:

```
Stage 1 輸出 (stage1_output.json)
  ├─ satellites[]
  │    ├─ satellite_id
  │    ├─ tle_line1  ← 需要這個
  │    └─ tle_line2  ← 需要這個

Stage 4 讀取
  ├─ 載入 Stage 1 輸出
  ├─ 建立 satellite_id → TLE 映射
  └─ 傳遞給 pool_optimizer

pool_optimizer
  ├─ 解析 TLE → RAAN
  └─ 執行兩階段選擇
```

**向後兼容**:
- 如果 `orbital_diversity.enabled = false`，使用原算法
- 如果 TLE 數據不可用，降級為原算法並警告

---

## 5. 驗證計劃

### 5.1 單元測試

**測試 1: RAAN 解析正確性**
```python
def test_raan_parsing():
    line1 = "1 44713U 19074A   ..."
    line2 = "2 44713  53.0540  20.1234 0001234 ..."

    raan = pool_optimizer._get_raan_from_tle(line1, line2)
    assert abs(raan - 20.1234) < 0.01
```

**測試 2: 軌道面代表選擇**
```python
def test_raan_representatives():
    reps = pool_optimizer._select_raan_representatives(
        candidates=mock_100_satellites,
        target_planes=24
    )

    assert len(reps) == 24  # 選出 24 顆

    # 檢查 RAAN 分佈
    raans = [get_raan(s) for s in reps]
    gaps = [raans[i+1] - raans[i] for i in range(23)]
    assert all(10 < gap < 20 for gap in gaps)  # 間隔 10-20°
```

### 5.2 整合測試

**測試場景 1: 完整 Stage 4 運行**
```bash
./run.sh --stage 4

# 檢查輸出
jq '.pool_optimization.optimized_pools.starlink | length' data/outputs/stage4/*.json
# 預期: 48-72

# 檢查軌道面數量
python /tmp/analyze_orbital_distribution.py
# 預期: ≥ 24 個軌道面, Gini < 0.3
```

**測試場景 2: 禁用多樣性約束**
```yaml
# config/stage4_link_feasibility_config.yaml
orbital_diversity:
  enabled: false
```
```bash
./run.sh --stage 4
# 應該回退到原算法，結果與改進前一致
```

### 5.3 驗收標準

**必須通過**:
- [ ] 軌道面數量 ≥ 24
- [ ] Gini 係數 < 0.3
- [ ] 時間覆蓋率 ≥ 93%
- [ ] 衛星總數 48-72 顆
- [ ] Stage 5, 6 正常運行（不破壞下游）

**可選驗證**:
- [ ] RL 訓練換手頻率穩定化
- [ ] 與論文配置對比（可視化）

---

## 6. 風險評估與緩解

### 6.1 技術風險

**風險 1: TLE 數據不可用** (概率: 低, 影響: 高)
- **緩解**: 實施降級邏輯，自動回退到原算法
- **檢測**: 啟動時檢查 Stage 1 輸出是否包含 TLE

**風險 2: 覆蓋率下降過多** (概率: 中, 影響: 中)
- **緩解**: 階段 2 Greedy 填補，保證覆蓋率
- **檢測**: 單元測試中設置覆蓋率下限 93%

**風險 3: 性能影響** (概率: 低, 影響: 低)
- **緩解**: TLE 解析是 O(n) 操作，影響 < 10 秒
- **檢測**: 測量 Stage 4 運行時間變化

### 6.2 業務風險

**風險 4: 破壞下游 Stage 5, 6** (概率: 低, 影響: 高)
- **緩解**: 保持輸出數據結構不變，僅改變選中的衛星集合
- **檢測**: 運行 Stage 5, 6 驗證

**風險 5: 參數調優耗時** (概率: 中, 影響: 中)
- **緩解**: 提供預設值（target_planes=24, max_per_plane=3）
- **檢測**: Phase 4 驗證時檢查指標

### 6.3 回滾計劃

**如果改進效果不佳**:

1. **立即回滾**:
   ```yaml
   orbital_diversity:
     enabled: false  # 禁用新算法
   ```

2. **代碼回滾**:
   ```bash
   git revert <commit-hash>
   ```

3. **數據恢復**:
   - 重新運行 Stage 4（使用原算法）
   - 驗證輸出與改進前一致

**回滾觸發條件**:
- 覆蓋率 < 90%
- Stage 5, 6 運行失敗
- 軌道面數量 < 15

---

## 7. 參考文獻

### 7.1 學術文獻

1. **Greedy Set Cover 基礎**:
   - Chvátal, V. (1979). "A greedy heuristic for the set-covering problem". *Mathematics of Operations Research*, 4(3), 233-235.
   - SOURCE: Stage 4 當前算法理論基礎

2. **Diversity-Aware 優化**:
   - Kumar, R., et al. (2013). "Diversity in Combinatorial Optimization". *ACM Computing Surveys*.
   - SOURCE: 軌道面多樣性約束理論

3. **LEO 衛星換手研究**:
   - IEEE IoT Journal 2024 - User-Centric Handover (48 衛星配置)
   - IEEE TWC 2021 - Load-Aware Handover (50 衛星配置)
   - SOURCE: 論文典型配置參考

4. **3GPP NTN 標準**:
   - 3GPP TR 38.821 - "Solutions for NTN"
   - SOURCE: 衛星可見性和換手標準

### 7.2 內部文檔

1. `docs/stages/stage4-link-feasibility.md` - Stage 4 規格文檔
2. `docs/ACADEMIC_STANDARDS.md` - 學術合規指南
3. `/tmp/pool_optimizer_diversity_proposal.md` - 初步技術提案
4. `/tmp/a4_d2_handover_strategy.md` - 換手策略分析

---

## 8. 附錄

### 8.1 Gini 係數計算

```python
def calculate_gini(distribution):
    """
    計算 Gini 係數（衡量分佈均勻性）

    SOURCE: Gini, C. (1912). "Variabilità e mutabilità"

    返回值:
      0.0 = 完全均勻（所有軌道面衛星數相同）
      1.0 = 完全不均勻（所有衛星在同一軌道面）
    """
    counts = sorted(distribution)
    n = len(counts)
    index = np.arange(1, n + 1)
    return ((2 * index - n - 1) * counts).sum() / (n * sum(counts))
```

### 8.2 RAAN 解析算法

```python
def parse_tle_raan(line2):
    """
    從 TLE Line 2 提取 RAAN（升交點赤經）

    TLE Line 2 格式:
    2 NNNNN NNN.NNNN NNN.NNNN NNNNNNN NNN.NNNN NNN.NNNN NN.NNNNNNNNNNNNNN
              ^^^^^^^^^^^
              位置 17-24: RAAN (degrees)

    SOURCE: NORAD TLE Format Specification
            https://celestrak.org/NORAD/documentation/tle-fmt.php
    """
    raan_str = line2[17:25].strip()
    return float(raan_str)
```

### 8.3 配置參數說明

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `enabled` | bool | true | 是否啟用軌道面多樣性約束 |
| `target_orbital_planes` | int | 24 | 目標軌道面數量（Starlink 72 面的 1/3） |
| `max_satellites_per_plane` | int | 3 | 每個軌道面最多衛星數 |
| `raan_bin_size_deg` | float | 15.0 | RAAN 分組大小（360/target_planes） |

**調優建議**:
- 增加 `target_planes` → 更多軌道面，但衛星總數增加
- 減少 `max_per_plane` → 更均勻分佈，但可能降低覆蓋率
- 建議先使用默認值，根據驗證結果微調

---

## 9. 審核與批准

**待審核項目**:
- [ ] 技術方案可行性（架構師）
- [ ] 學術合規性（研究負責人）
- [ ] 工程量評估（開發團隊）
- [ ] 風險評估（項目經理）

**批准後行動**:
1. 創建 feature branch: `feature/stage4-orbital-diversity`
2. 開始 Phase 1 實施
3. 每個 Phase 完成後提交 PR 並測試
4. 全部完成後合併到 main

---

**文件結束**
