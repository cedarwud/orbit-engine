# ⚡ 執行順序與檢查清單

**目標**: 提供完整的重構執行步驟，確保安全、有序地完成方案一的重構

## 🚨 重構前的安全檢查

### 必須完成的準備工作
- [ ] 完整備份現有 `src/stages/` 目錄
- [ ] 確認 git 工作區乾淨 (無未提交變更)
- [ ] 創建專用重構分支 `git checkout -b refactor-v3-complete`
- [ ] 測試當前系統運行狀況，記錄基準性能

### 依賴關係檢查
- [ ] 確認 `scripts/run_six_stages_with_validation.py` 當前可正常運行
- [ ] 檢查 `config/` 目錄中的配置文件完整性
- [ ] 驗證 `shared/` 模組的穩定性
- [ ] 確認測試數據 `data/tle_data/` 可用

## 📋 執行順序 (嚴格按順序執行)

### Phase 1: 安全備份與準備 (預計 15 分鐘)

#### Step 1.1: 完整系統備份
```bash
# 執行時間: ~5 分鐘
echo "🔒 開始系統備份..."

# 創建時間戳
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# 備份整個 stages 目錄
cp -r src/stages archives/stages_backup_${BACKUP_DATE}

# 備份配置文件
cp -r config archives/config_backup_${BACKUP_DATE}

# 備份主執行腳本
cp scripts/run_six_stages_with_validation.py \
   archives/run_six_stages_backup_${BACKUP_DATE}.py

echo "✅ 系統備份完成: archives/*_${BACKUP_DATE}"
```

#### Step 1.2: 創建重構工作分支
```bash
# 執行時間: ~2 分鐘
echo "🌿 創建重構分支..."

# 確保工作區乾淨
git status
git add .
git commit -m "Pre-refactor backup: $(date)"

# 創建並切換到重構分支
git checkout -b refactor-v3-complete

echo "✅ 重構分支已創建: refactor-v3-complete"
```

#### Step 1.3: 基準測試
```bash
# 執行時間: ~8 分鐘
echo "📊 執行基準測試..."

# 記錄當前系統性能
python scripts/run_six_stages_with_validation.py > \
       archives/baseline_performance_${BACKUP_DATE}.log 2>&1

echo "✅ 基準測試完成: archives/baseline_performance_${BACKUP_DATE}.log"
```

### Phase 2: Stage 3 清理 (預計 30 分鐘)

#### Step 2.1: Stage 3 功能分析和備份
```bash
# 執行時間: ~10 分鐘
echo "🌍 開始 Stage 3 清理..."

# 詳細備份 Stage 3 的可見性功能
mkdir -p refactor_plan_v3_complete/stage3_cleanup/extracted_functions

# 提取可見性相關功能
grep -n "visibility\|elevation" \
    src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py \
    > refactor_plan_v3_complete/stage3_cleanup/visibility_functions_inventory.txt

# 備份完整的 Stage 3 實現
cp src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py \
   refactor_plan_v3_complete/stage3_cleanup/stage3_original_backup.py

echo "✅ Stage 3 功能分析完成"
```

#### Step 2.2: 移除可見性功能
```bash
# 執行時間: ~15 分鐘
echo "✂️ 移除 Stage 3 可見性功能..."

# 這一步需要手動編輯，提供編輯指導
echo "📝 請按照 stage3_cleanup/STAGE3_CLEANUP_PLAN.md 手動移除以下功能:"
echo "   - _first_layer_visibility_filter()"
echo "   - _geometric_elevation_calculation()"
echo "   - _real_elevation_calculation()"
echo "   - 星座感知門檻邏輯"

echo "⏳ 手動編輯後按 Enter 繼續..."
read -p "Stage 3 清理完成? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ Stage 3 清理未完成，請完成後重新執行"
    exit 1
fi
```

#### Step 2.3: Stage 3 功能驗證
```bash
# 執行時間: ~5 分鐘
echo "✅ 驗證 Stage 3 清理結果..."

# 檢查 Stage 3 是否仍可運行 (僅前3階段)
python -c "
from src.stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
processor = Stage3CoordinateTransformProcessor()
print('✅ Stage 3 清理後仍可正常導入')
"

echo "✅ Stage 3 清理驗證完成"
```

### Phase 3: Stage 4 新實現 (預計 45 分鐘)

#### Step 3.1: 建立 Stage 4 新架構
```bash
# 執行時間: ~10 分鐘
echo "🛰️ 建立 Stage 4 新實現..."

# 建立新的 Stage 4 目錄結構
mkdir -p src/stages/stage4_link_feasibility/{utils,config}

# 從重構計畫複製模板
cp refactor_plan_v3_complete/stage4_new_implementation/templates/* \
   src/stages/stage4_link_feasibility/ 2>/dev/null || echo "模板文件將手動創建"

echo "✅ Stage 4 目錄結構已建立"
```

#### Step 3.2: 實現核心模組
```bash
# 執行時間: ~25 分鐘
echo "🔧 實現 Stage 4 核心模組..."

echo "📝 請按照 stage4_new_implementation/STAGE4_IMPLEMENTATION_PLAN.md 實現以下模組:"
echo "   1. constellation_filter.py"
echo "   2. ntpu_visibility_calculator.py"
echo "   3. orbital_period_analyzer.py"
echo "   4. service_window_calculator.py"
echo "   5. stage4_link_feasibility_processor.py"

echo "⏳ 核心模組實現後按 Enter 繼續..."
read -p "Stage 4 核心模組完成? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ Stage 4 實現未完成，請完成後重新執行"
    exit 1
fi
```

#### Step 3.3: Stage 4 功能驗證
```bash
# 執行時間: ~10 分鐘
echo "✅ 驗證 Stage 4 新實現..."

# 測試 Stage 4 基本功能
python -c "
from src.stages.stage4_link_feasibility.stage4_link_feasibility_processor import Stage4LinkFeasibilityProcessor
processor = Stage4LinkFeasibilityProcessor()
print('✅ Stage 4 新實現可正常導入')
"

# 測試星座感知功能
python -c "
from src.stages.stage4_link_feasibility.constellation_filter import ConstellationFilter
filter = ConstellationFilter()
print('✅ 星座感知篩選器正常')
print(f'   Starlink 門檻: {filter.CONSTELLATION_THRESHOLDS[\"starlink\"][\"min_elevation_deg\"]}°')
print(f'   OneWeb 門檻: {filter.CONSTELLATION_THRESHOLDS[\"oneweb\"][\"min_elevation_deg\"]}°')
"

echo "✅ Stage 4 新實現驗證完成"
```

### Phase 4: Stage 5 重組 (預計 25 分鐘)

#### Step 4.1: Stage 5 重新命名和遷移
```bash
# 執行時間: ~10 分鐘
echo "📡 開始 Stage 5 重組..."

# 複製現有 stage3_signal_analysis 到新的 stage5
cp -r src/stages/stage3_signal_analysis/ src/stages/stage5_signal_analysis/

# 備份原 stage3_signal_analysis
mv src/stages/stage3_signal_analysis/ \
   archives/stage3_signal_analysis_moved_to_stage5_${BACKUP_DATE}/

echo "✅ Stage 5 目錄遷移完成"
```

#### Step 4.2: 移除 3GPP 事件檢測 (移至 Stage 6)
```bash
# 執行時間: ~10 分鐘
echo "✂️ 從 Stage 5 移除 3GPP 事件檢測..."

# 備份 GPP 事件檢測器到 Stage 6
cp src/stages/stage5_signal_analysis/gpp_event_detector.py \
   refactor_plan_v3_complete/stage6_reorganization/gpp_event_detector_from_stage5.py

# 標記需要手動移除的功能
echo "📝 請從 Stage 5 手動移除以下功能 (保存至 Stage 6):"
echo "   - GPPEventDetector 類別和相關方法"
echo "   - 3GPP A4/A5/D2 事件檢測邏輯"
echo "   - 換手候選管理功能"

echo "⏳ Stage 5 清理後按 Enter 繼續..."
read -p "Stage 5 3GPP 功能移除完成? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ Stage 5 清理未完成，請完成後重新執行"
    exit 1
fi
```

#### Step 4.3: 更新 Stage 5 接口
```bash
# 執行時間: ~5 分鐘
echo "🔌 更新 Stage 5 接口..."

# 驗證 Stage 5 重組結果
python -c "
from src.stages.stage5_signal_analysis.stage3_signal_analysis_processor import Stage3SignalAnalysisProcessor as Stage5Processor
processor = Stage5Processor()
print('✅ Stage 5 重組後可正常導入')
"

echo "✅ Stage 5 重組驗證完成"
```

### Phase 5: Stage 6 重組 (預計 40 分鐘)

#### Step 5.1: 備份現有 Stage 6 並建立新架構
```bash
# 執行時間: ~10 分鐘
echo "🤖 開始 Stage 6 重組..."

# 備份現有 stage6_persistence_api
mv src/stages/stage6_persistence_api/ \
   archives/stage6_persistence_api_backup_${BACKUP_DATE}/

# 建立新的 Stage 6 目錄
mkdir -p src/stages/stage6_research_optimization/{ml_support,utils}

echo "✅ Stage 6 新架構目錄已建立"
```

#### Step 5.2: 遷移優化功能從原 Stage 4
```bash
# 執行時間: ~15 分鐘
echo "📦 遷移優化功能到 Stage 6..."

# 從原 stage4_optimization 遷移核心模組
cp src/stages/stage4_optimization/pool_planner.py \
   src/stages/stage6_research_optimization/dynamic_pool_planner.py

cp src/stages/stage4_optimization/handover_optimizer.py \
   src/stages/stage6_research_optimization/

cp src/stages/stage4_optimization/multi_obj_optimizer.py \
   src/stages/stage6_research_optimization/

cp src/stages/stage4_optimization/research_performance_analyzer.py \
   src/stages/stage6_research_optimization/

cp src/stages/stage4_optimization/config_manager.py \
   src/stages/stage6_research_optimization/

echo "✅ 優化功能遷移完成"
```

#### Step 5.3: 整合 3GPP 事件檢測
```bash
# 執行時間: ~10 分鐘
echo "📡 整合 3GPP 事件檢測到 Stage 6..."

# 從 Stage 5 移入 GPP 事件檢測
cp refactor_plan_v3_complete/stage6_reorganization/gpp_event_detector_from_stage5.py \
   src/stages/stage6_research_optimization/gpp_event_detector.py

echo "✅ 3GPP 事件檢測整合完成"
```

#### Step 5.4: 實現 ML 支援模組
```bash
# 執行時間: ~5 分鐘
echo "🧠 實現 ML 支援模組..."

echo "📝 請實現以下 ML 支援模組:"
echo "   - ml_training_data_generator.py"
echo "   - real_time_decision_engine.py"
echo "   - ml_support/ 子模組"

echo "⏳ ML 模組實現後按 Enter 繼續..."
read -p "Stage 6 ML 模組完成? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ Stage 6 ML 模組未完成，請完成後重新執行"
    exit 1
fi
```

### Phase 6: 系統整合與測試 (預計 30 分鐘)

#### Step 6.1: 更新主執行腳本
```bash
# 執行時間: ~10 分鐘
echo "🔄 更新主執行腳本..."

# 備份原執行腳本
cp scripts/run_six_stages_with_validation.py \
   archives/run_six_stages_original_${BACKUP_DATE}.py

echo "📝 請更新 scripts/run_six_stages_with_validation.py 中的導入路徑:"
echo "   Stage 4: stage4_optimization → stage4_link_feasibility"
echo "   Stage 5: stage3_signal_analysis → stage5_signal_analysis"
echo "   Stage 6: stage6_persistence_api → stage6_research_optimization"

echo "⏳ 腳本更新後按 Enter 繼續..."
read -p "執行腳本更新完成? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 執行腳本更新未完成，請完成後重新執行"
    exit 1
fi
```

#### Step 6.2: 階段性測試
```bash
# 執行時間: ~15 分鐘
echo "🧪 執行階段性測試..."

# 測試前3階段 (應該正常運行)
echo "測試 Stage 1-3..."
python -c "
import sys
sys.path.append('.')
from scripts.run_six_stages_with_validation import run_specific_stages
result = run_specific_stages([1, 2, 3])
print('✅ Stage 1-3 測試:', '通過' if result else '失敗')
"

echo "⏳ 如果前3階段測試失敗，請檢查並修復後繼續..."
read -p "繼續進行完整測試? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "⚠️ 請修復問題後重新執行測試"
    exit 1
fi
```

#### Step 6.3: 完整系統測試
```bash
# 執行時間: ~5 分鐘
echo "🎯 執行完整系統測試..."

# 完整六階段測試
python scripts/run_six_stages_with_validation.py > \
       archives/refactored_system_test_${BACKUP_DATE}.log 2>&1

echo "📊 測試完成，檢查結果:"
echo "   日誌文件: archives/refactored_system_test_${BACKUP_DATE}.log"
tail -20 archives/refactored_system_test_${BACKUP_DATE}.log

echo "✅ 完整系統測試完成"
```

### Phase 7: 清理與驗證 (預計 20 分鐘)

#### Step 7.1: 移除舊實現
```bash
# 執行時間: ~5 分鐘
echo "🧹 清理舊實現..."

# 移除原 stage4_optimization (已遷移到 stage6)
mv src/stages/stage4_optimization/ \
   archives/stage4_optimization_moved_to_stage6_${BACKUP_DATE}/

echo "✅ 舊實現清理完成"
```

#### Step 7.2: 文檔同步更新
```bash
# 執行時間: ~10 分鐘
echo "📚 同步更新文檔..."

# 重新命名文檔文件
mv docs/stages/stage3-signal-analysis.md \
   archives/stage3-signal-analysis_old_${BACKUP_DATE}.md

echo "📝 請更新以下文檔:"
echo "   - 創建新的 docs/stages/stage3-coordinate-transformation.md"
echo "   - 更新 docs/stages/stage4-link-feasibility.md"
echo "   - 更新 docs/stages/stage5-signal-analysis.md"
echo "   - 更新 docs/stages/stage6-research-optimization.md"

echo "⏳ 文檔更新後按 Enter 繼續..."
read -p "文檔更新完成? (y/n): " confirm
```

#### Step 7.3: 最終驗證
```bash
# 執行時間: ~5 分鐘
echo "✅ 執行最終驗證..."

# 檢查重構目標達成
echo "🎯 重構目標驗證:"

# 檢查 Stage 4 星座感知功能
python -c "
from src.stages.stage4_link_feasibility.constellation_filter import ConstellationFilter
cf = ConstellationFilter()
starlink_threshold = cf.CONSTELLATION_THRESHOLDS['starlink']['min_elevation_deg']
oneweb_threshold = cf.CONSTELLATION_THRESHOLDS['oneweb']['min_elevation_deg']
print(f'✅ Starlink 門檻: {starlink_threshold}° (final.md 要求: 5°)')
print(f'✅ OneWeb 門檻: {oneweb_threshold}° (final.md 要求: 10°)')
print(f'   符合 final.md 要求: {starlink_threshold == 5.0 and oneweb_threshold == 10.0}')
"

# 檢查 Stage 6 ML 支援
echo "檢查 ML 算法支援..."
if [ -f "src/stages/stage6_research_optimization/ml_training_data_generator.py" ]; then
    echo "✅ ML 訓練數據生成器存在"
else
    echo "❌ ML 訓練數據生成器缺失"
fi

echo "✅ 最終驗證完成"
```

## 🎯 成功標準

### 必須達成的目標
- [ ] Stage 3 只保留純座標轉換功能
- [ ] Stage 4 實現星座感知篩選 (Starlink 5°, OneWeb 10°)
- [ ] Stage 5 專注信號品質分析 (3GPP TS 38.214)
- [ ] Stage 6 整合優化功能和 3GPP 事件檢測
- [ ] 完整系統可正常運行六個階段
- [ ] 符合 final.md 的研究需求

### 性能標準
- [ ] Stage 1-2: 性能保持不變
- [ ] Stage 3: 性能提升 (移除不必要計算)
- [ ] Stage 4: 處理時間 < 1秒
- [ ] Stage 5: 處理時間 < 0.5秒
- [ ] Stage 6: 實時決策 < 100ms

### 功能標準
- [ ] Starlink 目標 10-15顆衛星可達成
- [ ] OneWeb 目標 3-6顆衛星可達成
- [ ] 3GPP A4/A5/D2 事件正確檢測
- [ ] ML 訓練數據正確生成

## 🚨 故障恢復

### 如果重構失敗
```bash
# 快速恢復到重構前狀態
echo "🔄 恢復到重構前狀態..."

# 切換回主分支
git checkout main

# 從備份恢復
rm -rf src/stages/
cp -r archives/stages_backup_${BACKUP_DATE}/ src/stages/

cp archives/run_six_stages_backup_${BACKUP_DATE}.py \
   scripts/run_six_stages_with_validation.py

echo "✅ 系統已恢復到重構前狀態"
```

### 部分失敗處理
- **Stage 3 清理失敗**: 恢復 `stage3_original_backup.py`
- **Stage 4 實現失敗**: 暫時保留原 `stage4_optimization`
- **Stage 5-6 重組失敗**: 恢復對應的備份目錄

## 📊 完成檢查清單

### 重構完成後必須驗證
- [ ] 所有6個階段都可正常運行
- [ ] 輸出格式符合文檔規範
- [ ] 性能達到預期標準
- [ ] final.md 需求全部滿足
- [ ] 所有測試用例通過
- [ ] 文檔同步更新完成

**估計總時間**: 3-4 小時 (包含手動編輯和測試時間)
**風險級別**: 中等 (有完整備份和恢復方案)
**建議執行**: 在測試環境先執行一次，確認無誤後在正式環境執行