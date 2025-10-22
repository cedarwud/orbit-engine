# API & 配置變更說明
## Stage 4 軌道面多樣性約束

**版本**: v1.0
**日期**: 2025-10-22
**對應提案**: [00-proposal.md](00-proposal.md)

---

## 1. 配置文件變更

### 1.1 新增配置項

**文件**: `config/stage4_link_feasibility_config.yaml`

```yaml
pool_optimization:
  starlink:
    # === 現有配置（完全不變）===
    target_min: 10
    target_max: 15
    target_coverage_rate: 0.95

    # === 新增配置 ===
    orbital_diversity:
      enabled: true                    # ⚠️ 新增
      target_orbital_planes: 24        # ⚠️ 新增
      max_satellites_per_plane: 3      # ⚠️ 新增
      raan_bin_size_deg: 15.0          # ⚠️ 新增（可選）
```

### 1.2 向後兼容性

**舊配置（無 `orbital_diversity`）**:
```yaml
pool_optimization:
  starlink:
    target_min: 10
    target_max: 15
```

**行為**:
- ✅ 自動檢測缺失配置
- ✅ 降級為原始 Greedy 算法
- ⚠️ 發出警告日誌
- ✅ 不影響運行

**代碼邏輯**:
```python
if not self.config.get('orbital_diversity', {}).get('enabled', False):
    logger.warning("軌道面多樣性約束未啟用，使用原始算法")
    return self._original_optimize_pool(...)
```

---

## 2. 函數接口變更

### 2.1 PoolOptimizer.optimize_pool()

**修改**: 增加 `tle_map` 參數

**舊接口**:
```python
def optimize_pool(
    self,
    candidates: List[Dict],
    target_min: int,
    target_max: int
) -> List[Dict]:
    pass
```

**新接口**:
```python
def optimize_pool(
    self,
    candidates: List[Dict],
    tle_map: Dict[str, Dict],  # ⚠️ 新增參數
    target_min: int,
    target_max: int
) -> List[Dict]:
    pass
```

**向後兼容**:
```python
# 如果 tle_map 為空或 None
if not tle_map:
    logger.warning("TLE 數據不可用，降級為原始算法")
    return self._original_optimize_pool(candidates, target_min, target_max)
```

**調用端修改** (`stage4_link_feasibility_processor.py`):
```python
# 舊調用
optimized = pool_optimizer.optimize_pool(
    candidates=candidates['starlink'],
    target_min=10,
    target_max=15
)

# 新調用
tle_map = self._build_tle_map(stage1_data)  # ⚠️ 新增
optimized = pool_optimizer.optimize_pool(
    candidates=candidates['starlink'],
    tle_map=tle_map,  # ⚠️ 新增參數
    target_min=10,
    target_max=15
)
```

### 2.2 新增函數

所有新增函數為內部函數（`_` 前綴），不影響外部 API：

- `_select_raan_representatives()`
- `_get_raan_from_tle()`
- `_get_raan_bin()`
- `_count_raan_distribution()`
- `_count_connectable_timepoints()`
- `_calculate_gini_coefficient()`

---

## 3. 數據格式變更

### 3.1 輸入格式

**無變更** - Stage 4 繼續使用 Stage 3 輸出作為主要輸入

**額外讀取** - Stage 1 輸出（用於 TLE 數據）：
```json
{
  "satellites": [
    {
      "satellite_id": "44713",
      "tle_line1": "1 44713U ...",  // ← 需要
      "tle_line2": "2 44713  53.0540  20.1234 ...",  // ← 需要
      "constellation": "starlink"
    }
  ]
}
```

### 3.2 輸出格式

**無變更** - Stage 4 輸出結構完全不變：

```json
{
  "pool_optimization": {
    "optimized_pools": {
      "starlink": [
        {
          "satellite_id": "44713",
          "time_series": [...],
          // 所有現有欄位保持不變
        }
      ]
    },
    "optimization_metrics": {
      "starlink": {
        "selected_count": 48,  // ⚠️ 數量可能變化
        "coverage_rate": 95.3,
        "average_visible": 10.7,
        // 其他欄位不變
      }
    }
  }
}
```

**唯一變化**: `selected_count` 可能從 98 減少到 48-72（這是預期改進）

---

## 4. 日誌輸出變更

### 4.1 新增日誌訊息

```
INFO: 🚀 開始兩階段池優化
INFO:    目標軌道面數: 24
INFO:    每面最多衛星數: 3
INFO: 📍 階段 1: 選擇軌道面代表...
INFO:    已選擇 24 顆代表衛星
INFO:    階段 1 覆蓋率: 75.3%
INFO: 🔍 階段 2: Greedy 填補覆蓋缺口...
INFO:    優化進度: 30 顆已選擇 (覆蓋率: 85.2%)
INFO:    優化進度: 40 顆已選擇 (覆蓋率: 91.5%)
INFO:    優化進度: 50 顆已選擇 (覆蓋率: 95.8%)
INFO: ✅ 兩階段優化完成:
INFO:    選擇數量: 52 顆
INFO:    覆蓋率: 95.8%
INFO:    軌道面數量: 24
INFO:    每面平均: 2.2 顆
INFO:    Gini 係數: 0.185
INFO:    ✅ 分佈均勻
```

### 4.2 降級警告訊息

```
WARNING: 軌道面多樣性約束已禁用，使用原始 Greedy 算法
WARNING: TLE 數據不可用，降級為原始算法
WARNING: 衛星 44713 無 TLE 數據，跳過
```

---

## 5. 環境變量

**無新增環境變量** - 所有配置通過 YAML 文件

---

## 6. 依賴變更

**無新增依賴** - 僅使用 Python 標準庫

已有依賴（繼續使用）：
- `numpy` - 用於 Gini 係數計算

---

## 7. 破壞性變更檢查

### 7.1 會破壞什麼？

**無破壞性變更** ✅

理由：
1. 配置向後兼容（舊配置仍可用）
2. 函數新增參數有默認處理（空 tle_map 降級）
3. 輸出格式不變（僅數值變化）
4. 下游 Stage 5, 6 無需修改

### 7.2 需要手動操作？

**可選配置更新**:

如果要啟用新功能，需手動編輯配置文件：

```bash
# 編輯配置
vim config/stage4_link_feasibility_config.yaml

# 添加
pool_optimization:
  starlink:
    orbital_diversity:
      enabled: true
      target_orbital_planes: 24
      max_satellites_per_plane: 3
```

**無需代碼修改** - 功能透明啟用

---

## 8. 遷移指南

### 8.1 啟用新功能

**步驟 1**: 更新配置
```bash
# 備份舊配置
cp config/stage4_link_feasibility_config.yaml config/stage4_link_feasibility_config.yaml.bak

# 編輯配置，添加 orbital_diversity 區塊
vim config/stage4_link_feasibility_config.yaml
```

**步驟 2**: 運行 Stage 4
```bash
./run.sh --stage 4
```

**步驟 3**: 驗證結果
```bash
# 運行分析腳本
python /tmp/analyze_orbital_distribution.py

# 檢查指標
# - 軌道面數量 ≥ 24
# - Gini < 0.3
```

### 8.2 禁用新功能（回滾）

**方法 1**: 配置禁用
```yaml
orbital_diversity:
  enabled: false  # ← 設為 false
```

**方法 2**: 刪除配置區塊
```yaml
pool_optimization:
  starlink:
    target_min: 10
    target_max: 15
    # orbital_diversity 區塊刪除 → 自動降級
```

**方法 3**: 代碼回滾
```bash
git revert <commit-hash>
```

---

## 9. 性能影響

### 9.1 運行時間

```
原算法: ~8-10 分鐘（Stage 4 總時間）
新算法: ~8-12 分鐘（增加 0-2 分鐘）

增加部分:
- TLE 解析: ~1 秒
- RAAN 分組: ~1 秒
- 兩階段優化: ~0-1 分鐘（視約束嚴格程度）
```

**總增加**: < 10% 運行時間（可接受）

### 9.2 內存使用

```
原算法: ~2-3 GB
新算法: ~2-3 GB（增加 < 1 MB，可忽略）

增加部分:
- TLE 映射: ~600 KB
- RAAN 分組: ~24 KB
```

**總增加**: < 0.1% 內存（可忽略）

---

## 10. 監控與日誌

### 10.1 關鍵指標

運行後檢查日誌中的：
```
INFO: 軌道面數量: <value>         # 目標: ≥ 24
INFO: Gini 係數: <value>           # 目標: < 0.3
INFO: 覆蓋率: <value>%              # 目標: ≥ 93%
```

### 10.2 異常情況

如果看到以下警告：
```
WARNING: TLE 數據不可用，降級為原始算法
```

**排查步驟**:
1. 檢查 Stage 1 輸出是否包含 `tle_line1`, `tle_line2`
2. 確認 Stage 1 成功運行
3. 檢查 `stage1_output_*.json` 文件完整性

---

## 11. 常見問題 (FAQ)

**Q1: 是否需要重新運行 Stage 1-3？**

A: 不需要，只需重新運行 Stage 4 即可。

---

**Q2: 下游 Stage 5, 6 需要修改嗎？**

A: 不需要，Stage 4 輸出格式不變。

---

**Q3: 如果不想用新功能，會影響現有流程嗎？**

A: 不會，舊配置完全兼容，自動降級為原算法。

---

**Q4: 新功能會改變論文結果嗎？**

A: 會改善結果質量（更接近論文方法論），但不會破壞可比性。

---

**Q5: 性能影響有多大？**

A: < 10% 運行時間增加（< 2 分鐘），可忽略。

---

## 12. 檢查清單

**部署前**:
- [ ] 備份舊配置文件
- [ ] 測試降級邏輯（禁用 enabled）
- [ ] 驗證 Stage 1 輸出包含 TLE 數據

**部署後**:
- [ ] 檢查日誌無錯誤
- [ ] 驗證軌道面數量 ≥ 24
- [ ] 驗證 Gini < 0.3
- [ ] 運行 Stage 5, 6 確認無破壞

**回滾準備**:
- [ ] 保留舊配置備份
- [ ] 記錄 git commit hash
- [ ] 準備回滾命令

---

**文件結束**
**相關文檔**: [README.md](README.md), [00-proposal.md](00-proposal.md)
