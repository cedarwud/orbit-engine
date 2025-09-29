# ✅ 重構驗證檢查清單

**目標**: 提供完整的驗證標準，確保重構後系統滿足所有要求

## 🎯 驗證層級

### Level 1: 基礎功能驗證 (Must Pass)
### Level 2: 性能標準驗證 (Must Pass)
### Level 3: final.md 需求驗證 (Must Pass)
### Level 4: 學術標準驗證 (Recommended)
### Level 5: 整合穩定性驗證 (Critical)

---

## 📋 Level 1: 基礎功能驗證

### 1.1 Stage 3 座標轉換驗證
- [ ] **純座標轉換功能**: 只包含 TEME→WGS84 轉換
- [ ] **移除可見性功能**: 無任何仰角計算和可見性篩選
- [ ] **Skyfield 專業庫**: 正確調用 IAU 標準實現
- [ ] **輸出格式正確**: WGS84 地理座標 (經度/緯度/高度)

```bash
# 驗證腳本
python -c "
from src.stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
import inspect

processor = Stage3CoordinateTransformProcessor()
methods = [method for method in dir(processor) if 'visibility' in method.lower() or 'elevation' in method.lower()]

assert len(methods) == 0, f'仍包含可見性方法: {methods}'
print('✅ Stage 3 可見性功能已完全移除')

# 檢查核心方法存在
assert hasattr(processor, 'process'), 'process 方法缺失'
print('✅ Stage 3 核心功能完整')
"
```

### 1.2 Stage 4 鏈路可行性驗證
- [ ] **星座感知篩選**: Starlink 5° vs OneWeb 10° 正確實現
- [ ] **NTPU 地面站**: 24°56'39"N, 121°22'17"E 精確座標
- [ ] **可見性計算**: 基於 WGS84 座標的準確計算
- [ ] **服務窗口**: 連續覆蓋時間窗口分析

```bash
# 驗證腳本
python -c "
from src.stages.stage4_link_feasibility.constellation_filter import ConstellationFilter
from src.stages.stage4_link_feasibility.ntpu_visibility_calculator import NTPUVisibilityCalculator

# 檢查星座門檻
cf = ConstellationFilter()
starlink_threshold = cf.CONSTELLATION_THRESHOLDS['starlink']['min_elevation_deg']
oneweb_threshold = cf.CONSTELLATION_THRESHOLDS['oneweb']['min_elevation_deg']

assert starlink_threshold == 5.0, f'Starlink 門檻錯誤: {starlink_threshold}° (應為 5°)'
assert oneweb_threshold == 10.0, f'OneWeb 門檻錯誤: {oneweb_threshold}° (應為 10°)'
print('✅ 星座感知門檻正確')

# 檢查 NTPU 座標
calc = NTPUVisibilityCalculator()
ntpu_lat = calc.NTPU_COORDINATES['latitude_deg']
ntpu_lon = calc.NTPU_COORDINATES['longitude_deg']

assert abs(ntpu_lat - 24.9441) < 0.0001, f'NTPU 緯度錯誤: {ntpu_lat}'
assert abs(ntpu_lon - 121.3714) < 0.0001, f'NTPU 經度錯誤: {ntpu_lon}'
print('✅ NTPU 座標精確')
"
```

### 1.3 Stage 5 信號分析驗證
- [ ] **3GPP 標準**: TS 38.214 RSRP/RSRQ/SINR 計算
- [ ] **ITU-R 模型**: P.618 物理傳播模型
- [ ] **移除事件檢測**: 無 3GPP A4/A5/D2 事件檢測功能
- [ ] **輸入正確**: 只處理 Stage 4 的可連線衛星

```bash
# 驗證腳本
python -c "
from src.stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor
from src.stages.stage5_signal_analysis.signal_quality_calculator import SignalQualityCalculator

processor = Stage5SignalAnalysisProcessor()

# 檢查不包含 GPP 事件檢測
assert not hasattr(processor, 'gpp_detector'), 'Stage 5 不應包含 GPP 事件檢測器'
assert hasattr(processor, 'signal_calculator'), 'Stage 5 應包含信號計算器'

# 檢查 3GPP 標準實現
calc = SignalQualityCalculator()
assert hasattr(calc, 'calculate_rsrp'), 'RSRP 計算缺失'
assert hasattr(calc, 'calculate_rsrq'), 'RSRQ 計算缺失'
assert hasattr(calc, 'calculate_sinr'), 'SINR 計算缺失'
print('✅ Stage 5 信號分析功能正確')
"
```

### 1.4 Stage 6 研究優化驗證
- [ ] **3GPP 事件檢測**: A4/A5/D2 事件完整實現
- [ ] **動態池規劃**: Starlink + OneWeb 分別規劃
- [ ] **ML 支援**: DQN/A3C/PPO/SAC 訓練數據生成
- [ ] **實時決策**: 毫秒級響應支援

```bash
# 驗證腳本
python -c "
from src.stages.stage6_research_optimization.stage6_research_optimization_processor import Stage6ResearchOptimizationProcessor
from src.stages.stage6_research_optimization.gpp_event_detector import GPPEventDetector
from src.stages.stage6_research_optimization.ml_training_data_generator import MLTrainingDataGenerator

processor = Stage6ResearchOptimizationProcessor()

# 檢查 3GPP 事件檢測
assert hasattr(processor, 'gpp_detector'), 'Stage 6 應包含 GPP 事件檢測器'

# 檢查 ML 支援
assert hasattr(processor, 'ml_data_generator'), 'Stage 6 應包含 ML 數據生成器'

# 檢查動態池規劃
assert hasattr(processor, 'pool_planner'), 'Stage 6 應包含動態池規劃器'

print('✅ Stage 6 研究優化功能完整')
"
```

---

## 📊 Level 2: 性能標準驗證

### 2.1 處理時間驗證
```bash
# 性能測試腳本
python -c "
import time
from datetime import datetime

# 模擬數據
test_data = {'test': True, 'satellites': list(range(100))}

# Stage 3 性能測試 (目標: < 2秒)
start = time.time()
# processor.process(test_data)  # 實際調用
stage3_time = time.time() - start

assert stage3_time < 2.0, f'Stage 3 處理時間過長: {stage3_time:.2f}s'
print(f'✅ Stage 3 處理時間: {stage3_time:.2f}s (< 2s)')

# Stage 4 性能測試 (目標: < 1秒)
# Stage 5 性能測試 (目標: < 0.5秒)
# Stage 6 決策性能測試 (目標: < 100ms)
"
```

### 2.2 記憶體使用驗證
- [ ] **Stage 3**: < 500MB (純座標轉換)
- [ ] **Stage 4**: < 300MB (可見性計算)
- [ ] **Stage 5**: < 400MB (信號分析)
- [ ] **Stage 6**: < 600MB (優化和 ML)

### 2.3 準確度驗證
- [ ] **座標轉換精度**: 亞米級 (< 1m 誤差)
- [ ] **仰角計算精度**: < 0.1° 誤差
- [ ] **信號計算精度**: 符合 3GPP 標準
- [ ] **事件檢測準確率**: > 95%

---

## 🎯 Level 3: final.md 需求驗證

### 3.1 衛星池規劃驗證
```bash
# final.md 需求檢查
python -c "
# 測試 Starlink 池規劃
# 目標: 任意時刻保持 10-15顆衛星可見 (5°仰角門檻)

from src.stages.stage6_research_optimization.dynamic_pool_planner import DynamicPoolPlanner

planner = DynamicPoolPlanner()
test_result = planner.plan_starlink_pool(test_data, target_satellites=(10, 15))

assert 'target_satellites' in test_result, 'Starlink 池規劃缺少目標設定'
target_min, target_max = test_result['target_satellites']
assert target_min == 10 and target_max == 15, f'Starlink 目標錯誤: {target_min}-{target_max} (應為 10-15)'
print('✅ Starlink 池規劃符合 final.md 需求')

# 測試 OneWeb 池規劃
# 目標: 任意時刻保持 3-6顆衛星可見 (10°仰角門檻)
oneweb_result = planner.plan_oneweb_pool(test_data, target_satellites=(3, 6))
target_min, target_max = oneweb_result['target_satellites']
assert target_min == 3 and target_max == 6, f'OneWeb 目標錯誤: {target_min}-{target_max} (應為 3-6)'
print('✅ OneWeb 池規劃符合 final.md 需求')
"
```

### 3.2 3GPP 事件檢測驗證
- [ ] **A4 事件**: "鄰近衛星變得優於門檻值" - 完整實現
- [ ] **A5 事件**: "服務衛星劣於門檻1且鄰近衛星優於門檻2" - 完整實現
- [ ] **D2 事件**: "基於距離的換手觸發" - 完整實現
- [ ] **事件頻率**: 能夠達到 1000+事件/小時

### 3.3 強化學習支援驗證
- [ ] **DQN 數據**: 狀態/動作/獎勵格式正確
- [ ] **A3C 數據**: 分散式訓練支援
- [ ] **PPO 數據**: 策略優化支援
- [ ] **SAC 數據**: 軟演員-評論家支援
- [ ] **訓練樣本**: 能夠達到 50,000+樣本/天

### 3.4 實時性能驗證
- [ ] **毫秒級響應**: < 100ms 換手決策
- [ ] **連續覆蓋**: 24小時不間斷服務
- [ ] **系統穩定性**: 72小時連續運行不崩潰

---

## 🔬 Level 4: 學術標準驗證

### 4.1 國際標準合規
- [ ] **3GPP TS 38.214**: 信號品質計算完全合規
- [ ] **3GPP TS 38.331**: 測量報告和事件檢測合規
- [ ] **ITU-R P.618**: 大氣傳播模型合規
- [ ] **ITU-R M.1732**: 衛星換手程序合規
- [ ] **IEEE 802.11**: 多目標優化框架合規

### 4.2 物理常數和精度
- [ ] **CODATA 2018**: 使用官方物理常數
- [ ] **無硬編碼**: 所有參數來自標準定義
- [ ] **數值穩定性**: 條件數和敏感性分析通過
- [ ] **收斂性證明**: 優化算法理論收斂保證

### 4.3 可重現性標準
- [ ] **固定隨機種子**: 所有隨機過程可重現
- [ ] **版本控制**: 算法和參數完整記錄
- [ ] **基準比較**: 與 SOTA 算法比較結果
- [ ] **統計顯著性**: 實驗結果統計可靠

---

## 🔄 Level 5: 整合穩定性驗證

### 5.1 六階段整合測試
```bash
# 完整流程測試
python scripts/run_six_stages_with_validation.py --test-mode

# 預期結果檢查:
# Stage 1: TLE 數據載入成功
# Stage 2: 軌道狀態傳播成功 (TEME 座標)
# Stage 3: 座標轉換成功 (WGS84 座標)
# Stage 4: 鏈路可行性評估成功 (可連線衛星池)
# Stage 5: 信號品質分析成功 (3GPP 標準)
# Stage 6: 研究數據生成成功 (事件+ML數據)
```

### 5.2 數據流驗證
- [ ] **Stage 1→2**: TLE 數據正確傳遞
- [ ] **Stage 2→3**: TEME 座標正確傳遞
- [ ] **Stage 3→4**: WGS84 座標正確傳遞
- [ ] **Stage 4→5**: 可連線衛星池正確傳遞
- [ ] **Stage 5→6**: 信號品質數據正確傳遞
- [ ] **各階段元數據**: 完整且一致

### 5.3 錯誤處理驗證
- [ ] **輸入驗證**: 各階段輸入格式檢查
- [ ] **異常恢復**: 處理失敗時的恢復機制
- [ ] **資源管理**: 記憶體和CPU使用監控
- [ ] **日誌記錄**: 完整的操作和錯誤日誌

### 5.4 長期穩定性測試
```bash
# 72小時連續運行測試
nohup python scripts/continuous_stability_test.py > stability_test.log 2>&1 &

# 監控指標:
# - 記憶體洩漏檢測
# - CPU 使用率穩定性
# - 處理時間一致性
# - 結果準確性維持
```

---

## 📝 驗證報告模板

### 驗證完成報告
```markdown
# 重構驗證報告

**日期**: $(date)
**重構版本**: v3.0 完整方案一
**測試環境**: [描述測試環境]

## 驗證結果摘要
- Level 1 基礎功能: ✅ 通過 / ❌ 失敗
- Level 2 性能標準: ✅ 通過 / ❌ 失敗
- Level 3 final.md 需求: ✅ 通過 / ❌ 失敗
- Level 4 學術標準: ✅ 通過 / ❌ 失敗
- Level 5 整合穩定性: ✅ 通過 / ❌ 失敗

## 詳細結果
[各階段詳細測試結果]

## 性能基準
- Stage 1: [時間] (基準: < 1s)
- Stage 2: [時間] (基準: < 5s)
- Stage 3: [時間] (基準: < 2s)
- Stage 4: [時間] (基準: < 1s)
- Stage 5: [時間] (基準: < 0.5s)
- Stage 6: [時間] (基準: < 0.2s, 決策 < 100ms)

## final.md 需求達成
- Starlink 池: [結果] (目標: 10-15顆)
- OneWeb 池: [結果] (目標: 3-6顆)
- 3GPP 事件: [結果] (目標: 1000+/小時)
- ML 樣本: [結果] (目標: 50,000+/天)

## 問題和解決方案
[發現的問題和對應解決方案]

## 建議
[進一步改進建議]
```

---

## 🚨 驗證失敗處理

### 如果驗證失敗
1. **記錄詳細錯誤資訊**
2. **分析失敗原因** (功能/性能/整合)
3. **執行對應修復方案**
4. **重新執行驗證**
5. **更新驗證檢查清單**

### 常見問題快速修復
- **導入錯誤**: 檢查模組路徑和 `__init__.py`
- **數據格式錯誤**: 檢查階段間接口定義
- **性能不達標**: 檢查算法實現和資源使用
- **功能缺失**: 檢查是否正確遷移所有必要功能

這個驗證檢查清單確保重構後的系統完全符合 final.md 需求，並維持高品質的學術標準。