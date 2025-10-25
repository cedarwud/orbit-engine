# Bug 修復記錄歸檔

**歸檔位置**: `docs/archive/fixes/`
**歸檔原因**: 已完成的 Bug 修復報告歸檔管理

---

## 📚 歸檔內容

本資料夾包含已完成的 Bug 修復報告（3 個文件，31.7KB）：

| 文件 | 大小 | 修復日期 | 問題描述 |
|------|------|----------|----------|
| **CODE_REVIEW_RSRP_CLIPPING_BUGS.md** | 15KB | 2025-10-20 | RSRP 截斷問題代碼審查 |
| **FIX_SUMMARY_RSRP_CLIPPING.md** | 12KB | 2025-10-20 | RSRP 修復摘要與解決方案 |
| **ORBITAL_DIVERSITY_BUG_FIX.md** | 4.7KB | 2025-10-22 | Stage 4 軌道面多樣性 Bug 修復 |

---

## 🐛 Bug 1: RSRP 截斷問題（2025-10-20）

### 問題描述

**症狀**: 所有衛星的 RSRP 都是 -44.0 dBm，無論距離、仰角差異

**根本原因**: `gpp_ts38214_signal_calculator.py:163` 錯誤截斷 RSRP
```python
# ❌ 錯誤: 誤解 3GPP 標準
rsrp_dbm = max(-140.0, min(-44.0, rsrp_dbm))
```

**錯誤理解**:
- 誤認為 3GPP TS 38.215 的測量報告範圍 (-140~-44 dBm) 是物理限制
- 實際上這是 **UE 量化報告範圍**，非物理 RSRP 上限
- 近距離衛星 (1400 km) 的 RSRP 可達 -30 dBm，不應截斷

**修復方法**:
```python
# ✅ 正確: 保留真實計算值
return rsrp_dbm  # 無截斷
```

**影響範圍**:
- ❌ A3 事件完全無法觸發（所有衛星 RSRP 相同）
- ❌ A5 事件檢測失效
- ❌ 換手決策無法區分衛星信號品質
- ❌ ML 訓練數據失去意義（特徵無變化）

**SOURCE**: 3GPP TS 38.215 v18.1.0 Section 5.1.1

**相關文檔**:
- `CODE_REVIEW_RSRP_CLIPPING_BUGS.md` - 詳細代碼審查
- `FIX_SUMMARY_RSRP_CLIPPING.md` - 修復摘要與驗證

---

## 🐛 Bug 2: Stage 4 軌道面多樣性（2025-10-22）

### 問題描述

#### 問題 1: 配置 `enabled: false` 無效

**症狀**: 即使在 `stage4_link_feasibility_config.yaml` 中設置 `orbital_diversity.enabled: false`，程式仍然執行軌道面約束。

**影響範圍**:
- Starlink: 部分影響（自然 Greedy 算法仍能達標）
- OneWeb: 嚴重影響（覆蓋率從 95% 降至 10%）

#### 問題 2: 錯誤的兩階段算法

**症狀**: 程式使用「先選代表，再填補」的兩階段算法，破壞時間覆蓋連續性。

**算法流程**（錯誤）:
```
階段 1: 從每個軌道面選擇 1 顆代表衛星
        → 選出 15 顆（Starlink）或 5 顆（OneWeb）
階段 2: 使用 Greedy 填補到每面上限
        → 選出 45 顆（Starlink）或 9 顆（OneWeb）
```

**為何導致失敗**:
- 階段 1 選出的代表衛星在時間上不重疊
- 階段 2 受限於每面上限，無法選擇時間覆蓋最佳的衛星
- 結果：覆蓋率 0-10%，遠低於 95% 目標

### 修復方法

#### 修復 1: 配置開關

```python
# ✅ 正確檢查配置
if self.orbital_diversity_config.get('enabled', False):
    # 執行軌道面約束
else:
    # 使用標準 Greedy 算法
```

#### 修復 2: 算法修正

**新算法**（正確）:
```
單階段 Greedy + 軌道面約束:
1. 初始化空池
2. 循環選擇最佳衛星（時間覆蓋最大）
3. 檢查軌道面約束（每面上限）
4. 符合約束則加入池，否則跳過
5. 重複直到達到目標數量
```

**結果**:
- Starlink: 覆蓋率 95% ✅（15 個軌道面均勻分布）
- OneWeb: 覆蓋率 95% ✅（5 個軌道面均勻分布）

**SOURCE**: 內部測試與驗證

**相關文檔**:
- `ORBITAL_DIVERSITY_BUG_FIX.md` - 完整修復報告

---

## 🎯 修復驗證

### Bug 1 驗證（RSRP）

**檢查方法**:
```bash
# 檢查 RSRP 是否有變化
jq '.signal_analysis | to_entries | .[0:5] | .[] | {sat: .key, rsrp: .value.time_series[0].signal_quality.rsrp_dbm}' \
  data/outputs/stage5/*.json
```

**預期結果**: 應該看到不同值（-38.2 ~ -31.1 dBm），不應全是 -44.0

### Bug 2 驗證（Orbital Diversity）

**檢查方法**:
```bash
# 檢查 enabled=false 時不執行軌道面約束
grep "orbital_diversity" data/outputs/stage4/*.json
```

**預期結果**:
- `enabled: false`: 覆蓋率 95%，無軌道面約束
- `enabled: true`: 覆蓋率 95%，15 個軌道面均勻分布（Starlink）

---

## 📝 相關文檔

### Bug 修復報告
- `CODE_REVIEW_RSRP_CLIPPING_BUGS.md` - RSRP 截斷問題詳細審查
- `FIX_SUMMARY_RSRP_CLIPPING.md` - RSRP 修復摘要與驗證結果
- `ORBITAL_DIVERSITY_BUG_FIX.md` - 軌道面多樣性 Bug 修復報告

### 主文檔
- `docs/README.md` - 文檔導航中心
- `docs/stages/stage4-link-feasibility.md` - Stage 4 詳細規格
- `docs/stages/stage5-signal-analysis.md` - Stage 5 詳細規格

### 代碼位置
- `src/stages/stage5_signal_analysis/gpp_ts38214_signal_calculator.py` - RSRP 計算（已修復）
- `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py` - 軌道面多樣性（已修復）

---

## 📊 歸檔統計

**文件數**: 3 個
**總大小**: 31.7KB
**修復期間**: 2025-10-20 ~ 2025-10-22
**影響階段**: Stage 4, Stage 5, Stage 6

---

**歸檔日期**: 2025-10-24
**歸檔原因**: Bug 已修復，保留作為歷史記錄
**狀態**: ✅ 完成
