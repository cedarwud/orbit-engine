# 重構計劃 01: 移除重複基類

**優先級**: 🔴 P0 (最高)
**風險等級**: 🟢 低風險
**預估時間**: 30 分鐘
**狀態**: ⏸️ 待執行

---

## 📋 目標

移除 `src/shared/base_stage_processor.py` (舊版 139行)，統一使用 `src/shared/base_processor.py` 中的 `BaseStageProcessor` 類別。

---

## 🔍 現狀分析

### 問題根源
```
src/shared/
├── base_stage_processor.py (139行) ❌ 舊版，功能簡單
└── base_processor.py (269行) ✅ 新版，功能完整
    └── interfaces/processor_interface.py (412行)
```

### 兩者差異

**舊版** (`base_stage_processor.py`):
```python
class BaseStageProcessor(BaseProcessor):
    def __init__(self, stage_name: str, config: Dict[str, Any] = None):
        super().__init__(processor_name=stage_name, config=config)
        self.stage_name = stage_name
        self.stats = {...}  # 簡單統計
```

**新版** (`base_processor.py`):
```python
class BaseStageProcessor(BaseProcessor):
    def __init__(self, stage_number: int, stage_name: str, config: Optional[Dict] = None):
        super().__init__(processor_name=f"stage{stage_number}_{stage_name}", config=config)
        self.stage_number = stage_number
        # 完整功能：
        # - 容器路徑管理
        # - 驗證快照保存
        # - 完整生命週期管理
        # - 輸入輸出驗證
```

### 當前使用情況
```bash
# 檢查結果：所有 stages 都使用新版
grep -r "from.*base_processor import BaseStageProcessor" src/stages/
# src/stages/stage1_orbital_calculation/stage1_main_processor.py
# src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py
# src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py
# src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py
# src/stages/stage5_signal_analysis/stage5_signal_analysis_processor.py
# src/stages/stage6_research_optimization/stage6_research_optimization_processor.py
```

### 影響範圍
- ✅ 無任何 stage 使用舊版
- ✅ 可以安全刪除
- ⚠️ 可能有測試或文檔引用舊路徑

---

## 🎯 執行步驟

### Step 1: 備份當前狀態
```bash
cd /home/sat/orbit-engine

# 檢查當前狀態
git status

# 創建備份點
git add .
git commit -m "Backup before refactoring: Remove duplicate base class"
```

### Step 2: 驗證無引用
```bash
# 檢查是否有檔案導入舊版基類
grep -r "from.*base_stage_processor import" . --include="*.py" --exclude-dir=venv

# 預期結果：無結果或僅在舊版檔案本身
```

### Step 3: 刪除舊版檔案
```bash
# 刪除舊版基類
rm src/shared/base_stage_processor.py

# 確認刪除
ls -la src/shared/base_stage_processor.py
# 應顯示: No such file or directory
```

### Step 4: 更新文檔引用 (如有)
```bash
# 檢查文檔是否提到舊版基類
grep -r "base_stage_processor" docs/ --include="*.md"

# 如有引用，更新為 base_processor
```

### Step 5: 驗證導入路徑
```bash
# 確認所有 stages 導入正確
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

# 驗證可以正常導入
from shared.base_processor import BaseStageProcessor
print("✅ BaseStageProcessor 導入成功")

# 驗證舊路徑不可用
try:
    from shared.base_stage_processor import BaseStageProcessor
    print("❌ 舊版基類仍然存在！")
except ImportError:
    print("✅ 舊版基類已成功移除")
EOF
```

### Step 6: 運行測試驗證
```bash
# 測試 Stage 1
./run.sh --stage 1

# 如果成功，測試完整流程
./run.sh --stages 1-3

# 如果有單元測試
make test
```

### Step 7: 提交變更
```bash
git add .
git commit -m "Refactor: Remove duplicate base_stage_processor.py

- 移除舊版 src/shared/base_stage_processor.py (139行)
- 統一使用 src/shared/base_processor.py 中的 BaseStageProcessor
- 所有 stages 已驗證使用新版基類
- 測試通過: Stage 1-3 執行正常

Ref: docs/refactoring/REFACTOR_PLAN_01
"
```

---

## ✅ 驗證檢查清單

完成以下檢查後，才能標記為完成：

- [ ] 舊版檔案已刪除: `src/shared/base_stage_processor.py`
- [ ] 無任何 `.py` 檔案導入舊版基類
- [ ] Python 導入測試通過 (新版可用，舊版不可用)
- [ ] Stage 1 執行成功: `./run.sh --stage 1`
- [ ] Stage 1-3 執行成功: `./run.sh --stages 1-3`
- [ ] Git 提交包含清晰的 commit message
- [ ] 文檔已更新 (如有引用舊版)

---

## 🔄 回滾方案

如果出現問題，立即回滾：

```bash
# 方案 1: 回滾到上一個 commit
git reset --hard HEAD~1

# 方案 2: 恢復單個檔案
git checkout HEAD~1 -- src/shared/base_stage_processor.py

# 方案 3: 查看差異後選擇性恢復
git diff HEAD~1
git checkout HEAD~1 -- [特定檔案]
```

---

## 📊 預期效益

- **代碼減少**: -139 行
- **技術債務**: -100% (完全移除重複代碼)
- **維護成本**: -5% (明確單一基類)
- **新人困惑**: -80% (不再有兩個基類選擇)

---

## 📝 注意事項

1. **不要修改新版基類**: 本次重構僅刪除舊版，不修改新版
2. **確認測試通過**: 刪除後必須運行測試
3. **文檔同步更新**: 如有引用舊版路徑的文檔，一併更新

---

## 🔗 相關資源

- [架構優化分析報告](../architecture/ARCHITECTURE_OPTIMIZATION_REPORT.md#1-基類架構混亂---雙重繼承體系)
- [BaseStageProcessor 新版實現](../../src/shared/base_processor.py#L13-L269)
- [處理器接口定義](../../src/shared/interfaces/processor_interface.py)

---

**創建日期**: 2025-10-11
**負責人**: Development Team
**審查者**: TBD
