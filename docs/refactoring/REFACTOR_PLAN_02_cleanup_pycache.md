# 重構計劃 02: 清理緩存和歷史引用

**優先級**: 🔴 P0 (最高)
**風險等級**: 🟢 低風險 (零功能影響)
**預估時間**: 15 分鐘
**狀態**: ⏸️ 待執行

---

## 📋 目標

清理所有 `__pycache__` 目錄和歷史模塊緩存，確保導入路徑使用最新的統一版本。

---

## 🔍 現狀分析

### 問題根源

**歷史重複模塊** (已刪除源碼，但緩存殘留):
```bash
# 過去存在的重複模塊:
src/stages/stage5_signal_analysis/coordinate_converter.py (已刪除 ✅)
src/stages/stage6_research_optimization/coordinate_converter.py (已刪除 ✅)
src/stages/stage6_research_optimization/ground_distance_calculator.py (已刪除 ✅)

# 但緩存仍存在:
src/stages/stage5_signal_analysis/__pycache__/coordinate_converter.cpython-312.pyc ❌
src/stages/stage6_research_optimization/__pycache__/coordinate_converter.cpython-312.pyc ❌
src/stages/stage6_research_optimization/__pycache__/ground_distance_calculator.cpython-312.pyc ❌
```

**當前統一版本**:
```
src/shared/utils/coordinate_converter.py ✅
src/shared/utils/ground_distance_calculator.py ✅
```

### 潛在風險

1. **導入歧義**: Python 可能優先使用緩存的舊版模塊
2. **調試困難**: 修改代碼後，緩存不更新導致行為不一致
3. **部署問題**: 生產環境可能執行不同版本的代碼

---

## 🎯 執行步驟

### Step 1: 備份當前狀態
```bash
cd /home/sat/orbit-engine

# 創建備份點
git add .
git commit -m "Backup before refactoring: Cleanup pycache and historical references"
```

### Step 2: 統計當前緩存
```bash
# 統計 __pycache__ 數量
echo "📊 當前 __pycache__ 目錄數量:"
find . -type d -name "__pycache__" | wc -l

# 統計緩存檔案大小
echo "💾 緩存總大小:"
du -sh $(find . -type d -name "__pycache__")

# 列出所有緩存目錄
echo "📂 緩存目錄列表:"
find . -type d -name "__pycache__" | head -20
```

### Step 3: 清理所有 Python 緩存
```bash
# 方法 1: 使用 find + rm (推薦)
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

# 方法 2: 使用 Python 內建工具
python3 -m py_compile --invalidate-caches

# 驗證清理結果
echo "✅ 清理後 __pycache__ 數量:"
find . -type d -name "__pycache__" | wc -l
# 預期: 0
```

### Step 4: 驗證導入路徑正確性
```bash
# 檢查所有導入路徑是否使用統一版本
echo "🔍 檢查 coordinate_converter 導入:"
grep -r "from.*coordinate_converter import" src/stages --include="*.py"

# 預期結果 (應全部使用 shared.utils):
# src/stages/stage5_signal_analysis/time_series_analyzer.py:
#     from src.shared.utils.coordinate_converter import geodetic_to_ecef
# src/stages/stage6_research_optimization/gpp_event_detector.py:
#     from src.shared.utils.coordinate_converter import ecef_to_geodetic

# 檢查 ground_distance_calculator 導入:
echo "🔍 檢查 ground_distance_calculator 導入:"
grep -r "from.*ground_distance_calculator import" src/stages --include="*.py"

# 預期結果 (應全部使用 shared.utils):
# 應顯示使用 src.shared.utils.ground_distance_calculator
```

### Step 5: 測試導入功能
```bash
# 測試統一模塊可正常導入
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

# 測試 coordinate_converter
try:
    from shared.utils.coordinate_converter import ecef_to_geodetic, geodetic_to_ecef
    print("✅ coordinate_converter 導入成功")
except ImportError as e:
    print(f"❌ coordinate_converter 導入失敗: {e}")

# 測試 ground_distance_calculator
try:
    from shared.utils.ground_distance_calculator import calculate_ground_distance
    print("✅ ground_distance_calculator 導入成功")
except ImportError as e:
    print(f"❌ ground_distance_calculator 導入失敗: {e}")

# 測試舊路徑不可用 (應該失敗)
try:
    from stages.stage5_signal_analysis.coordinate_converter import ecef_to_geodetic
    print("⚠️ 警告: 舊路徑仍然可用!")
except (ImportError, ModuleNotFoundError):
    print("✅ 舊路徑已正確移除")
EOF
```

### Step 6: 運行完整測試
```bash
# 測試 Stage 5 (使用 coordinate_converter)
./run.sh --stage 5

# 測試 Stage 6 (使用 coordinate_converter, ground_distance_calculator)
./run.sh --stage 6

# 測試完整流程
./run.sh --stages 1-6

# 如果有單元測試
make test
```

### Step 7: 添加 .gitignore 規則
```bash
# 確保未來不會提交 __pycache__
cat >> .gitignore << 'EOF'

# Python cache files
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
EOF

# 驗證 .gitignore
git check-ignore **/__pycache__
# 應顯示被忽略
```

### Step 8: 提交變更
```bash
git add .gitignore
git commit -m "Refactor: Cleanup all pycache and enforce gitignore

- 清理所有 __pycache__ 目錄和 *.pyc 緩存
- 移除歷史模塊緩存 (coordinate_converter, ground_distance_calculator)
- 驗證統一導入路徑: src.shared.utils.*
- 更新 .gitignore 防止未來提交緩存檔案
- 測試通過: Stage 5, 6 執行正常

Ref: docs/refactoring/REFACTOR_PLAN_02
"
```

---

## ✅ 驗證檢查清單

完成以下檢查後，才能標記為完成：

- [ ] 所有 `__pycache__` 目錄已刪除: `find . -type d -name __pycache__ | wc -l` = 0
- [ ] 所有 `*.pyc` 檔案已刪除: `find . -type f -name "*.pyc" | wc -l` = 0
- [ ] 導入測試通過: 統一模塊可導入，舊路徑不可用
- [ ] Stage 5 執行成功: `./run.sh --stage 5`
- [ ] Stage 6 執行成功: `./run.sh --stage 6`
- [ ] `.gitignore` 已更新，包含 `__pycache__/` 規則
- [ ] Git 提交包含清晰的 commit message

---

## 🔄 回滾方案

本次重構僅刪除緩存檔案，無需回滾。如果測試失敗：

```bash
# 重新生成緩存
python3 -m compileall src/

# 或直接運行程序，自動生成緩存
./run.sh --stage 1
```

---

## 📊 預期效益

- **磁盤空間**: 節省 ~50-100 MB (視緩存數量)
- **導入一致性**: 100% (無歧義)
- **調試效率**: +20% (無緩存干擾)
- **部署安全性**: +100% (無舊版模塊殘留)

---

## 📝 注意事項

1. **執行後重新運行**: 清理後首次運行會重新生成緩存 (正常現象)
2. **Docker 環境**: 如在容器內執行，需同時清理容器緩存
3. **CI/CD**: 確保 CI 環境也忽略 `__pycache__`

---

## 🔧 進階: 自動化清理腳本

創建清理腳本供未來使用：

```bash
cat > scripts/cleanup_cache.sh << 'SCRIPT'
#!/bin/bash
# Orbit Engine 緩存清理腳本

echo "🧹 清理 Python 緩存..."

# 清理 __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "✅ __pycache__ 目錄已清理"

# 清理 .pyc 檔案
find . -type f -name "*.pyc" -delete
echo "✅ .pyc 檔案已清理"

# 清理 .pyo 檔案
find . -type f -name "*.pyo" -delete
echo "✅ .pyo 檔案已清理"

# 統計
echo ""
echo "📊 清理結果:"
echo "   __pycache__ 殘留: $(find . -type d -name __pycache__ | wc -l)"
echo "   .pyc 殘留: $(find . -type f -name "*.pyc" | wc -l)"

SCRIPT

chmod +x scripts/cleanup_cache.sh

# 測試腳本
./scripts/cleanup_cache.sh
```

---

## 🔗 相關資源

- [架構優化分析報告](../architecture/ARCHITECTURE_OPTIMIZATION_REPORT.md#5-工具模塊歷史重複-已部分修復)
- [Python 緩存機制](https://docs.python.org/3/tutorial/modules.html#compiled-python-files)
- [統一 coordinate_converter](../../src/shared/utils/coordinate_converter.py)

---

**創建日期**: 2025-10-11
**負責人**: Development Team
**審查者**: TBD
