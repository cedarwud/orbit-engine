# 🚀 Orbit Engine v3.0 完整重構計畫 - 方案一

**建立日期**: 2025-09-29
**重構目標**: 完全符合 final.md 研究需求的六階段架構重構
**預計時間**: 3-4 小時
**風險級別**: 中等 (有完整備份和恢復機制)

## 📋 重構概述

### 🎯 重構目標
將當前錯誤的六階段架構重新組織為符合 v3.0 規範和 final.md 研究需求的正確架構，實現：

1. **清晰的職責邊界** - 每個階段功能單一明確
2. **符合 final.md 需求** - 完全支援衛星池規劃和 3GPP 事件檢測
3. **學術標準合規** - 符合國際標準的實現方式
4. **可擴展架構** - 為後續研究提供穩固基礎

### 🚨 當前問題分析
- **Stage 3**: 包含應屬於 Stage 4 的可見性評估功能 (職責越界)
- **Stage 4**: 實現了錯誤的優化決策功能 (應為鏈路可行性評估)
- **Stage 5**: 實現了錯誤的數據整合功能 (應為信號品質分析)
- **Stage 6**: 實現了錯誤的持久化功能 (應為研究數據生成)

### ✅ 修正後架構
| 階段 | v3.0 正確職責 | final.md 對應需求 |
|------|---------------|------------------|
| Stage 1 | TLE 數據載入 | ✅ 已正確實現 |
| Stage 2 | 軌道狀態傳播 | ✅ 已正確實現 |
| Stage 3 | 座標系統轉換 | ⚠️ 需清理可見性功能 |
| **Stage 4** | **鏈路可行性評估** | **星座感知篩選 (Starlink 5°, OneWeb 10°)** |
| **Stage 5** | **信號品質分析** | **3GPP TS 38.214 標準 RSRP/RSRQ/SINR** |
| **Stage 6** | **研究數據生成** | **3GPP 事件檢測 + ML 訓練數據 + 動態池規劃** |

---

## 📂 重構計畫結構

```
refactor_plan_v3_complete/
├── README.md                           # 📄 本文件 - 統整說明
├── stage3_cleanup/                     # 🌍 Stage 3 清理計畫
│   └── STAGE3_CLEANUP_PLAN.md         #     移除職責越界功能
├── stage4_new_implementation/          # 🛰️ Stage 4 新實現計畫
│   └── STAGE4_IMPLEMENTATION_PLAN.md  #     鏈路可行性評估層
├── stage5_reorganization/              # 📡 Stage 5 重組計畫
│   └── STAGE5_REORGANIZATION_PLAN.md  #     信號品質分析層
├── stage6_reorganization/              # 🤖 Stage 6 重組計畫
│   └── STAGE6_REORGANIZATION_PLAN.md  #     研究數據生成層
├── execution_scripts/                  # ⚡ 執行腳本
│   └── EXECUTION_ORDER.md             #     詳細執行順序和檢查
└── validation_tests/                   # ✅ 驗證測試
    └── VALIDATION_CHECKLIST.md        #     5層級驗證檢查清單
```

---

## 🎯 與 final.md 需求的完美對應

### 核心研究需求實現

#### 1. **動態衛星池規劃** → Stage 6
- **Starlink**: 10-15顆衛星持續可見 (5°門檻, 90-95分鐘週期)
- **OneWeb**: 3-6顆衛星持續可見 (10°門檻, 109-115分鐘週期)
- **時空錯置策略**: 錯開時間和位置的衛星選擇

#### 2. **3GPP NTN 事件檢測** → Stage 6
- **A4 事件**: 鄰近衛星優於門檻 (3GPP TS 38.331 Section 5.5.4.5)
- **A5 事件**: 雙門檻換手條件 (Section 5.5.4.6)
- **D2 事件**: 距離基礎換手 (Section 5.5.4.15a)

#### 3. **強化學習支援** → Stage 6
- **多算法支援**: DQN/A3C/PPO/SAC 訓練數據生成
- **狀態空間**: 衛星位置、信號強度、仰角、距離等多維狀態
- **動作空間**: 換手決策 (保持/切換至候選衛星)
- **獎勵函數**: 基於 QoS、中斷時間、信號品質的複合獎勵

#### 4. **NTPU 特定需求** → Stage 4
- **精確座標**: 24°56'39"N, 121°22'17"E
- **星座感知**: Starlink 5° vs OneWeb 10° 差異化門檻
- **地面站特定**: NTPU 地理環境的可見性分析

---

## 🔧 重構執行流程

### Phase 1: 準備和備份 (15分鐘)
1. **完整系統備份** - 備份 `src/stages/`, `config/`, `scripts/`
2. **創建重構分支** - `git checkout -b refactor-v3-complete`
3. **基準測試** - 記錄重構前的性能基準

### Phase 2: Stage 3 清理 (30分鐘)
1. **分析和備份** - 提取可見性功能清單
2. **移除越界功能** - 移除仰角計算、可見性篩選、星座感知門檻
3. **功能驗證** - 確保純座標轉換功能正常

### Phase 3: Stage 4 新實現 (45分鐘)
1. **建立新架構** - 創建 `stage4_link_feasibility/` 目錄結構
2. **實現核心模組** - 星座感知篩選、NTPU 可見性、軌道週期分析
3. **整合測試** - 驗證鏈路可行性評估功能

### Phase 4: Stage 5 重組 (25分鐘)
1. **目錄重新命名** - `stage3_signal_analysis/` → `stage5_signal_analysis/`
2. **移除事件檢測** - 3GPP 事件檢測功能移至 Stage 6
3. **接口更新** - 更新為接收 Stage 4 的可連線衛星池

### Phase 5: Stage 6 重組 (40分鐘)
1. **整合優化功能** - 從原 `stage4_optimization/` 遷移
2. **整合事件檢測** - 從 Stage 5 遷移 3GPP 事件檢測
3. **實現 ML 支援** - 新增強化學習訓練數據生成

### Phase 6: 系統整合 (30分鐘)
1. **更新執行腳本** - 修正 `run_six_stages_with_validation.py` 導入路徑
2. **階段性測試** - 測試各階段獨立功能
3. **完整系統測試** - 六階段端到端測試

### Phase 7: 清理驗證 (20分鐘)
1. **移除舊實現** - 備份並移除不需要的舊目錄
2. **文檔同步更新** - 更新階段文檔和配置
3. **最終驗證** - 執行完整驗證檢查清單

---

## ⚡ 快速開始

### 1. 立即開始重構
```bash
cd /home/sat/orbit-engine

# 閱讀完整執行計畫
cat refactor_plan_v3_complete/execution_scripts/EXECUTION_ORDER.md

# 開始執行重構 (嚴格按順序)
# Phase 1: 備份和準備
echo "開始重構備份..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
cp -r src/stages archives/stages_backup_${BACKUP_DATE}
```

### 2. 關鍵驗證點
```bash
# 執行驗證檢查
cat refactor_plan_v3_complete/validation_tests/VALIDATION_CHECKLIST.md

# 快速功能測試
python -c "
# 測試 Stage 4 星座感知
from src.stages.stage4_link_feasibility.constellation_filter import ConstellationFilter
cf = ConstellationFilter()
print('Starlink 門檻:', cf.CONSTELLATION_THRESHOLDS['starlink']['min_elevation_deg'], '°')
print('OneWeb 門檻:', cf.CONSTELLATION_THRESHOLDS['oneweb']['min_elevation_deg'], '°')
"
```

### 3. 故障恢復
```bash
# 如果重構失敗，快速恢復
git checkout main
rm -rf src/stages/
cp -r archives/stages_backup_${BACKUP_DATE}/ src/stages/
echo "已恢復到重構前狀態"
```

---

## 📊 預期成果

### 功能成果
- ✅ **Stage 3**: 純座標轉換，性能提升 15-20%
- ✅ **Stage 4**: 星座感知篩選，符合 final.md 門檻要求
- ✅ **Stage 5**: 高效信號分析，僅處理可連線衛星
- ✅ **Stage 6**: 完整研究支援，3GPP 事件 + ML 訓練數據

### 研究目標達成
- ✅ **Starlink 池**: 10-15顆衛星持續可見
- ✅ **OneWeb 池**: 3-6顆衛星持續可見
- ✅ **3GPP 事件**: 1000+事件/小時檢測能力
- ✅ **ML 訓練**: 50,000+樣本/天生成能力
- ✅ **實時決策**: < 100ms 響應時間

### 學術標準
- ✅ **3GPP 合規**: TS 38.214, TS 38.331 完整實現
- ✅ **ITU-R 合規**: P.618 物理傳播模型
- ✅ **IEEE 合規**: 802.11 多目標優化框架
- ✅ **CODATA 2018**: 標準物理常數使用

---

## 🚨 重要注意事項

### 執行前必讀
1. **嚴格按順序執行** - 不可跳躍或並行執行階段
2. **完整備份確認** - 確保備份完整和可恢復
3. **測試環境優先** - 建議先在測試環境執行
4. **時間預算充足** - 預留足夠時間進行手動編輯和測試

### 風險控制
- **完整備份機制** - 所有重要文件都有時間戳備份
- **漸進式驗證** - 每個階段完成後立即驗證
- **快速回滾方案** - 任何時候都可以快速恢復
- **詳細執行日誌** - 記錄所有操作以便問題追蹤

### 成功標準
- **功能完整性** - 所有階段功能正常運作
- **性能達標** - 處理時間符合預期標準
- **final.md 符合** - 研究需求 100% 滿足
- **學術合規** - 國際標準完全符合

---

## 📞 支援和協助

### 文檔參考順序
1. **📖 開始**: 本 README.md (總體概覽)
2. **⚡ 執行**: `execution_scripts/EXECUTION_ORDER.md` (詳細步驟)
3. **🔧 實現**: 各階段具體實現計畫 (分階段詳細指導)
4. **✅ 驗證**: `validation_tests/VALIDATION_CHECKLIST.md` (完整驗證)

### 問題排除
- **導入錯誤** → 檢查模組路徑和 `__init__.py` 文件
- **功能缺失** → 確認功能遷移是否完整
- **性能問題** → 檢查算法實現和資源使用
- **測試失敗** → 參考驗證檢查清單逐項檢查

---

**開始重構**: 請從 `execution_scripts/EXECUTION_ORDER.md` 開始，嚴格按照執行順序進行

**預期結果**: 完全符合 final.md 需求的高品質六階段衛星研究系統

**重構完成標準**: 通過 5 層級驗證檢查清單的所有項目