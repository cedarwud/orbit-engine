# 📋 計劃 A: 核心功能修正 - 實現狀態報告

**實現日期**: 2025-09-30
**狀態**: ✅ 代碼實現完成，待完整測試驗證

---

## ✅ 完成任務摘要

### 任務 A.1: 創建 LinkBudgetAnalyzer 類
**狀態**: ✅ 完成
**檔案**: `src/stages/stage4_link_feasibility/link_budget_analyzer.py`

**實現內容**:
- ✅ 鏈路預算約束參數 (200-2000km)
- ✅ `check_distance_constraint()` 方法
- ✅ `analyze_link_feasibility()` 綜合分析方法
- ✅ `batch_analyze()` 批次分析方法
- ✅ 鏈路品質估計功能
- ✅ 完整的測試案例

**測試結果**:
```
✅ 距離過近檢測 (< 200km): 通過
✅ 距離過遠檢測 (> 2000km): 通過
✅ 正常範圍判斷: 通過
✅ 仰角不足檢測: 通過
```

---

### 任務 A.2: 修改輸出結構為完整時間序列
**狀態**: ✅ 完成
**檔案**: `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`

**實現內容**:
- ✅ 新建 `_calculate_time_series_metrics()` 方法
  - 計算每個時間點的仰角、方位角、距離
  - 使用 LinkBudgetAnalyzer 判斷 `is_connectable`
  - 保留完整時間序列數據

- ✅ 新建 `_filter_connectable_satellites()` 方法
  - 按星座分類 (starlink, oneweb, other)
  - 篩選至少有一個時間點可連線的衛星
  - 計算服務窗口摘要

- ✅ 新建 `_calculate_service_window()` 方法
  - 基於 is_connectable=True 的時間點
  - 計算持續時間和最大仰角

- ✅ 重寫 `_build_stage4_output()` 方法
  - 符合文檔規範的輸出結構
  - 包含完整 `time_series[]` 數組
  - 標記重構版本 (plan_a_v1.0)

**輸出結構**:
```python
{
    'stage': 'stage4_link_feasibility',
    'connectable_satellites': {
        'starlink': [
            {
                'satellite_id': 'STARLINK-1234',
                'name': 'STARLINK-1234',
                'constellation': 'starlink',
                'time_series': [  # ← 完整時間序列
                    {
                        'timestamp': '2025-09-30T10:00:00Z',
                        'latitude_deg': 25.1,
                        'longitude_deg': 121.5,
                        'altitude_km': 550.0,
                        'elevation_deg': 15.2,
                        'azimuth_deg': 245.7,
                        'distance_km': 750.2,
                        'is_connectable': True,  # ← 關鍵標記
                        'elevation_threshold': 5.0,
                        'link_quality': 'good'
                    },
                    # ... 更多時間點
                ],
                'service_window': {
                    'start_time': '...',
                    'end_time': '...',
                    'duration_minutes': 8.0,
                    'time_points_count': 16,
                    'max_elevation_deg': 18.2
                }
            },
            # ... 更多衛星
        ],
        'oneweb': [...],
        'other': [...]
    },
    'feasibility_summary': {
        'total_connectable': 2156,
        'by_constellation': {
            'starlink': 1845,
            'oneweb': 278
        }
    },
    'metadata': {
        'output_format': 'complete_time_series',
        'refactored_version': 'plan_a_v1.0',
        'link_budget_constraints': {...},
        'constellation_thresholds': {...}
    }
}
```

---

### 任務 A.3: 添加方位角計算
**狀態**: ✅ 完成
**檔案**: `src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py`

**實現內容**:
- ✅ 新增 `calculate_azimuth()` 方法
- ✅ 使用球面三角學計算方位角
- ✅ 0-360° 範圍 (北=0°, 順時針)
- ✅ 完整的測試案例

**測試結果**:
```
✅ 東方衛星: 84.3° (正確)
✅ 西方衛星: 279.5° (正確)
✅ 北方衛星: 6.2° (正確)
✅ 南方衛星: 172.9° (正確)
```

---

## 📊 代碼修改統計

### 新增檔案
1. `src/stages/stage4_link_feasibility/link_budget_analyzer.py` (280+ 行)

### 修改檔案
1. `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`
   - 添加 LinkBudgetAnalyzer 導入
   - 重寫 `_process_link_feasibility()` 方法
   - 新建 `_calculate_time_series_metrics()` 方法 (110+ 行)
   - 新建 `_filter_connectable_satellites()` 方法 (50+ 行)
   - 新建 `_calculate_service_window()` 方法 (20+ 行)
   - 重寫 `_build_stage4_output()` 方法 (45+ 行)
   - 刪除舊的 `_calculate_all_elevations()` 方法

2. `src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py`
   - 新增 `calculate_azimuth()` 方法 (40+ 行)
   - 更新測試代碼

### 備份檔案
- `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py.backup`

---

## ✅ 驗收標準檢查

### 功能驗收
- [x] 所有衛星時間點都包含距離檢查 (200-2000km)
- [x] 輸出結構包含完整 `time_series[]` 數組
- [x] 每個時間點都有正確的 `is_connectable` 布爾值
- [x] `is_connectable` 邏輯同時考慮仰角和距離
- [x] 方位角計算準確 (0-360° 範圍)

### 代碼質量
- [x] 無語法錯誤 (`py_compile` 通過)
- [x] 模組導入成功
- [x] 單元測試通過 (LinkBudgetAnalyzer, 方位角)
- [x] 符合文檔規範

### 待完成驗收
- [ ] 完整 Stage 1-4 流程測試
- [ ] 數據量驗證 (9000 顆衛星處理)
- [ ] 性能測試 (處理時間 < 5 秒)
- [ ] 記憶體使用測試 (< 2GB)

---

## 🧪 測試計劃

### 單元測試 (已完成)
- [x] LinkBudgetAnalyzer 類測試
  - 距離約束檢查
  - 鏈路可行性分析
  - 品質估計

- [x] 方位角計算測試
  - 四個方向驗證
  - 角度範圍驗證

### 集成測試 (待執行)
需要在容器環境或測試模式下執行:
```bash
# 方法 1: 容器內執行
docker exec orbit-engine-dev bash
cd /orbit-engine && python scripts/run_six_stages_with_validation.py --stages 1-4

# 方法 2: 測試模式
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py --stages 1-4
```

### 驗收測試 (待執行)
檢查項目:
1. Stage 4 輸出文件存在
2. 輸出結構符合文檔規範
3. `is_connectable` 標記正確
4. 時間序列點數合理 (95-220 範圍)
5. Starlink/OneWeb 分類正確

---

## ⚠️ 已知問題與限制

### 測試環境限制
- 系統要求在 Docker 容器內執行
- 或需要設置 `ORBIT_ENGINE_TEST_MODE=1`
- Stage 4 依賴 Stage 1-3 的輸出文件

### 待優化項目
- 時間序列數據量可能較大 (需監控記憶體)
- 批次處理可進一步優化性能
- 可考慮並行化處理提升速度

---

## 📦 交付物清單

### 代碼檔案
- [x] `link_budget_analyzer.py` (新建)
- [x] `stage4_link_feasibility_processor.py` (修改)
- [x] `ntpu_visibility_calculator.py` (修改)
- [x] `stage4_link_feasibility_processor.py.backup` (備份)

### 文檔檔案
- [x] `docs/refactoring/stage4/plan-a-core-functionality.md`
- [x] `docs/refactoring/stage4/plan-a-implementation-status.md` (本文檔)

### 測試檔案
- [ ] `tests/stages/stage4/test_link_budget.py` (待創建)
- [ ] `tests/stages/stage4/test_time_series_output.py` (待創建)

---

## 🚀 下一步行動

### 立即執行
1. **在容器環境進行完整測試**
   ```bash
   docker exec orbit-engine-dev bash -c "cd /orbit-engine && python scripts/run_six_stages_with_validation.py --stages 1-4"
   ```

2. **檢查輸出數據結構**
   ```bash
   cat data/outputs/stage4/link_feasibility_output_*.json | jq '.connectable_satellites.starlink[0].time_series[0]'
   ```

3. **驗證數據量和性能**
   - 確認處理時間
   - 確認記憶體使用
   - 確認輸出檔案大小

### 後續任務
4. **創建單元測試** (test_link_budget.py, test_time_series_output.py)
5. **代碼審查和優化**
6. **更新文檔實現狀態**
7. **準備開始計劃 B: 學術標準升級**

---

## 📝 實現筆記

### 關鍵設計決策
1. **時間序列保留**: 不再只保留最大仰角，而是保留所有時間點數據
2. **雙重約束**: `is_connectable` 同時檢查仰角和距離 (200-2000km)
3. **星座感知**: 每個衛星使用其專屬的仰角門檻 (Starlink 5°, OneWeb 10°)
4. **鏈路品質**: 添加品質估計 (excellent/good/fair/poor/unavailable)

### 向後兼容性
- 保留原有的 validate_input/validate_output 方法
- 輸出結構添加 `output_format` 和 `refactored_version` 標記
- 舊處理器備份為 `.backup` 文件

### 學術合規
- 鏈路預算約束符合 Kodheli et al. (2021) 建議
- 星座特定門檻符合實際系統設計
- 完整時間序列支援後續 Stage 5/6 分析

---

**文檔版本**: v1.0
**實現負責**: Orbit Engine Team
**審核狀態**: 待代碼審查
**下一步**: 完整流程測試 → 計劃 B 實現