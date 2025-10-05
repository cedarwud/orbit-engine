# 軌道週期完整性驗證 - 實作完成報告

**日期**: 2025-10-05
**任務**: 實作軌道週期覆蓋驗證，確保時間點涵蓋完整軌道週期
**狀態**: ✅ 完成並測試

---

## 📋 任務背景

### 用戶問題
"所以你要怎麼驗證這2個星座在各自的1個軌道週期內，真的可以平均在 ntpu 上空平均可見這些衛星數量?"

### 核心問題
當前驗證只檢查「所有時間點的平均覆蓋率」，未驗證「時間點是否涵蓋完整軌道週期」。

**潛在風險**:
- 時間點可能集中在短時間段（例如僅 30 分鐘）
- 無法反映完整軌道週期的動態行為
- 平均覆蓋率 95.5% 可能誤導（時間跨度不足）

---

## ✅ 實作內容

### 1. 新增驗證方法

**文件**: `src/stages/stage6_research_optimization/satellite_pool_verifier.py`

**方法**: `_validate_orbital_period_coverage()` (Lines 267-367)

```python
def _validate_orbital_period_coverage(
    self,
    time_points: List[str],
    constellation: str
) -> Dict[str, Any]:
    """驗證時間點是否涵蓋完整軌道週期

    🚨 新增 (2025-10-05): 防止時間點集中在短時間段

    SOURCE: 開普勒第三定律 T = 2π√(a³/μ)
    依據: ORBITAL_PERIOD_VALIDATION_DESIGN.md 方法 1
    """
    # 軌道週期常數
    ORBITAL_PERIODS = {
        'starlink': 95,   # 分鐘 (SOURCE: 6921km 半長軸)
        'oneweb': 110     # 分鐘 (SOURCE: 7571km 半長軸)
    }

    # 計算時間跨度
    time_span = timestamps[-1] - timestamps[0]
    time_span_minutes = time_span.total_seconds() / 60.0

    # 覆蓋比率
    coverage_ratio = time_span_minutes / expected_period

    # 驗證標準: 時間跨度 >= 90% 軌道週期
    MIN_COVERAGE_RATIO = 0.9
    is_complete_period = coverage_ratio >= MIN_COVERAGE_RATIO

    return {
        'time_span_minutes': time_span_minutes,
        'expected_period_minutes': expected_period,
        'coverage_ratio': coverage_ratio,
        'is_complete_period': is_complete_period,
        'validation_passed': is_complete_period,
        'message': '...'
    }
```

**理論依據**:
- **開普勒第三定律**: T = 2π√(a³/μ)
  - Starlink (550km): a = 6921 km → T ≈ 95 分鐘
  - OneWeb (1200km): a = 7571 km → T ≈ 110 分鐘
- **驗證標準**: 時間跨度 >= 90% 軌道週期（允許 10% 容差）

### 2. 整合到池驗證流程

**修改位置**: `verify_pool_maintenance()` (Lines 240-265)

```python
# 🚨 新增 (2025-10-05): 軌道週期完整性驗證
orbital_period_validation = self._validate_orbital_period_coverage(
    sorted(all_timestamps), constellation
)

# 更新結果
result['orbital_period_validation'] = orbital_period_validation

# 軌道週期驗證日誌
if orbital_period_validation['is_complete_period']:
    self.logger.info(
        f"   ✅ 軌道週期覆蓋: {orbital_period_validation['time_span_minutes']:.1f} 分鐘 "
        f"({orbital_period_validation['coverage_ratio']:.1%} 完整週期)"
    )
else:
    self.logger.warning(
        f"   ❌ 軌道週期不足: {orbital_period_validation['time_span_minutes']:.1f} 分鐘 "
        f"< {orbital_period_validation['expected_period_minutes'] * 0.9:.1f} 分鐘最小要求"
    )
```

---

## 🧪 測試結果

### 執行測試
```bash
./run.sh --stage 6 > /tmp/stage6_orbital_period_test.log 2>&1
```

### Starlink 驗證結果

```
✅ 軌道週期覆蓋: 111.5 分鐘 (117.4% 完整週期)
```

**詳細指標**:
```json
{
  "time_span_minutes": 111.5,
  "expected_period_minutes": 95,
  "coverage_ratio": 1.174,
  "is_complete_period": true,
  "validation_passed": true,
  "message": "✅ 時間跨度 111.5 分鐘 >= 85.5 分鐘 (涵蓋 117.4% 軌道週期)"
}
```

**解讀**:
- ✅ 時間跨度 111.5 分鐘超過 Starlink 軌道週期（95 分鐘）
- ✅ 涵蓋 117.4% 完整週期（約 1.17 個軌道週期）
- ✅ 遠超最低要求 85.5 分鐘（90% × 95 分鐘）
- ✅ **驗證通過**: 時間點確實涵蓋完整軌道動態行為

### OneWeb 驗證結果

```
❌ 軌道週期不足: 94.5 分鐘 < 99.0 分鐘最小要求
```

**詳細指標**:
```json
{
  "time_span_minutes": 94.5,
  "expected_period_minutes": 110,
  "coverage_ratio": 0.859,
  "is_complete_period": false,
  "validation_passed": false,
  "message": "❌ 時間跨度不足: 94.5 分鐘 < 99.0 分鐘最小要求 (僅涵蓋 85.9% 軌道週期)"
}
```

**解讀**:
- ❌ 時間跨度 94.5 分鐘未達 OneWeb 軌道週期（110 分鐘）
- ❌ 僅涵蓋 85.9% 軌道週期（低於 90% 最低要求）
- ❌ 未達最低要求 99.0 分鐘（90% × 110 分鐘）
- ❌ **驗證失敗**: 時間點未涵蓋完整軌道週期

---

## 🔍 重要發現

### 發現 1: Starlink 通過，OneWeb 失敗

**現象**:
- Starlink: 224 時間點，111.5 分鐘跨度 ✅
- OneWeb: 190 時間點，94.5 分鐘跨度 ❌

**原因分析**:
1. **時間窗口配置問題**:
   - 當前觀測窗口可能針對 Starlink 軌道週期（95 分鐘）設計
   - OneWeb 軌道週期更長（110 分鐘），需要更長的觀測窗口

2. **可見窗口差異**:
   - Starlink (550km): 軌道更低，過頂更快，但可見時間更短
   - OneWeb (1200km): 軌道更高，過頂更慢，可見時間更長
   - 相同觀測窗口下，OneWeb 可能未完整覆蓋一個軌道週期

### 發現 2: 驗證標準差異

**原有驗證** (僅覆蓋率):
- Starlink: 95.5% 覆蓋率 ✅
- OneWeb: 95.3% 覆蓋率 ✅

**新增驗證** (軌道週期):
- Starlink: 117.4% 週期覆蓋 ✅
- OneWeb: 85.9% 週期覆蓋 ❌

**結論**:
- 覆蓋率不能反映時間跨度的充分性
- 必須結合軌道週期驗證才能確保數據完整性

---

## 📊 驗證快照更新

### 新增字段

**位置**: `data/validation_snapshots/stage6_validation.json`

```json
{
  "pool_verification": {
    "starlink_pool": {
      "orbital_period_validation": {
        "time_span_minutes": 111.5,
        "expected_period_minutes": 95,
        "coverage_ratio": 1.174,
        "is_complete_period": true,
        "validation_passed": true,
        "message": "✅ 時間跨度 111.5 分鐘 >= 85.5 分鐘 (涵蓋 117.4% 軌道週期)"
      }
    },
    "oneweb_pool": {
      "orbital_period_validation": {
        "time_span_minutes": 94.5,
        "expected_period_minutes": 110,
        "coverage_ratio": 0.859,
        "is_complete_period": false,
        "validation_passed": false,
        "message": "❌ 時間跨度不足: 94.5 分鐘 < 99.0 分鐘最小要求 (僅涵蓋 85.9% 軌道週期)"
      }
    }
  }
}
```

---

## 🎯 驗證標準總結

| 驗證項目 | Starlink 標準 | OneWeb 標準 | 當前結果 |
|---------|--------------|-------------|---------|
| **軌道週期** | 95 分鐘 | 110 分鐘 | 理論值 |
| **最小時間跨度** | 85.5 分鐘 (90%) | 99.0 分鐘 (90%) | 驗證門檻 |
| **實際時間跨度** | 111.5 分鐘 | 94.5 分鐘 | 測試數據 |
| **覆蓋比率** | 117.4% ✅ | 85.9% ❌ | 計算結果 |
| **時間點數量** | 224 個 | 190 個 | 觀測數據 |
| **平均可見衛星** | 10.4 顆 ✅ | 3.3 顆 ✅ | 池維持目標 |
| **覆蓋率** | 95.5% ✅ | 95.3% ✅ | 時間點達標率 |

---

## 🔧 建議改進

### 問題: OneWeb 未涵蓋完整軌道週期

**選項 1: 延長觀測窗口（推薦）**
- 將觀測窗口從當前設定延長至至少 2 小時（120 分鐘）
- 確保兩個星座都能涵蓋完整軌道週期
- 修改位置: Stage 2/3/4 的 `observation_window_hours` 參數

**選項 2: 接受當前狀態（臨時）**
- OneWeb 85.9% 覆蓋已接近 90% 門檻
- 仍能反映大部分軌道動態行為
- 在學術論文中說明此限制

**選項 3: 針對星座調整驗證標準**
- Starlink: 90% 門檻（95 分鐘 → 85.5 分鐘）
- OneWeb: 80% 門檻（110 分鐘 → 88 分鐘）
- 理由: OneWeb 軌道更高，可見時間更長，部分週期已足夠

**建議**: 採用選項 1 延長觀測窗口，確保學術嚴謹性。

---

## 📚 相關文件

### 設計文檔
- `ORBITAL_PERIOD_VALIDATION_DESIGN.md` - 驗證方法設計（提案）
- `docs/stages/stage6-research-optimization.md` - Stage 6 規格說明

### 實作代碼
- `src/stages/stage6_research_optimization/satellite_pool_verifier.py`
  - Lines 267-367: `_validate_orbital_period_coverage()` 方法
  - Lines 240-265: 整合到 `verify_pool_maintenance()`

### 驗證快照
- `data/validation_snapshots/stage6_validation.json`
  - `.pool_verification.starlink_pool.orbital_period_validation`
  - `.pool_verification.oneweb_pool.orbital_period_validation`

---

## ✅ 完成標準

### 代碼實作
- [x] 實作 `_validate_orbital_period_coverage()` 方法
- [x] 整合到池驗證流程
- [x] 新增驗證日誌輸出
- [x] 更新驗證快照結構

### 測試驗證
- [x] 運行 Stage 6 完整測試
- [x] 驗證 Starlink 軌道週期覆蓋
- [x] 驗證 OneWeb 軌道週期覆蓋
- [x] 檢查驗證快照輸出

### 文檔
- [x] 代碼註解說明理論依據
- [x] SOURCE 註解標註參考文檔
- [x] 創建實作完成報告

---

## 🎯 總結

### 成果
- ✅ 實作軌道週期完整性驗證
- ✅ 發現 OneWeb 時間跨度不足問題
- ✅ 提供量化指標（時間跨度、覆蓋比率）
- ✅ 完成驗證快照更新

### 驗證能力提升
**修改前**:
- 僅檢查平均覆蓋率（95.5%）
- 無法識別時間跨度不足問題

**修改後**:
- 檢查平均覆蓋率（95.5%）✅
- 檢查軌道週期覆蓋（117.4% / 85.9%）✅
- 量化時間跨度（111.5 / 94.5 分鐘）✅
- 識別 OneWeb 時間窗口問題 ✅

### 學術貢獻
- 確保數據涵蓋完整軌道動態行為
- 防止時間點集中導致的誤導結論
- 符合軌道動力學驗證標準
- 提升研究數據可信度

**軌道週期驗證實作已成功完成！** ✨
