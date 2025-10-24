# 執行流程與控制邏輯

本文檔詳細說明 `scripts/run_six_stages_with_validation.py` 的執行流程和控制邏輯。

## 文件結構

```
scripts/run_six_stages_with_validation.py (332 行)
├── 環境初始化 (Line 19-58)
├── 執行器與驗證器映射表 (Line 72-101)
├── 驗證函數 (Line 104-184)
├── 主要執行函數 (Line 187-258)
└── 主函數與命令行解析 (Line 260-332)
```

## 啟動流程

### 1. 環境初始化 (Line 29-44)

```python
# 自動加載 .env 文件
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
    logger.info(f"✅ 已自動加載環境配置: {env_file}")
    test_mode = os.getenv('ORBIT_ENGINE_TEST_MODE', '未設置')
    logger.info(f"   ORBIT_ENGINE_TEST_MODE = {test_mode}")
```

**重要**: 無需手動 `export` 環境變量，系統自動讀取 `.env` 文件。

### 2. Python 路徑設置 (Line 46-53)

```python
# 確保能找到模組
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 如果在容器中，也添加容器路徑
if os.path.exists('/orbit-engine'):
    sys.path.insert(0, '/orbit-engine')
    sys.path.insert(0, '/orbit-engine/src')
```

### 3. 導入執行器與驗證器 (Line 62-70)

```python
from stage_executors import (
    execute_stage1, execute_stage2, execute_stage3,
    execute_stage4, execute_stage5, execute_stage6
)
from stage_validators import (
    check_stage1_validation, check_stage2_validation, check_stage3_validation,
    check_stage4_validation, check_stage5_validation, check_stage6_validation
)
```

## 核心數據結構

### 執行器映射表 (Line 76-83)

```python
STAGE_EXECUTORS = {
    1: execute_stage1,
    2: execute_stage2,
    3: execute_stage3,
    4: execute_stage4,
    5: execute_stage5,
    6: execute_stage6,
}
```

### 驗證器映射表 (Line 85-92)

```python
STAGE_VALIDATORS = {
    1: check_stage1_validation,
    2: check_stage2_validation,
    3: check_stage3_validation,
    4: check_stage4_validation,
    5: check_stage5_validation,
    6: check_stage6_validation,
}
```

### 階段名稱映射表 (Line 94-101)

```python
STAGE_NAMES = {
    1: "數據載入層",
    2: "軌道狀態傳播層",
    3: "座標系統轉換層",
    4: "鏈路可行性評估層",
    5: "信號品質分析層",
    6: "研究數據生成層",
}
```

## 執行模式

### 模式 1: 完整管道順序執行 (預設)

**觸發條件**: 無參數執行

```bash
./run.sh
python scripts/run_six_stages_with_validation.py
```

**執行函數**: `run_all_stages_sequential()` (Line 191-227)

**執行流程**:

```python
def run_all_stages_sequential(validation_level='STANDARD'):
    print('🚀 開始六階段數據處理 (重構版本)')

    stage_results = {}  # 存儲各階段結果

    for stage_num in range(1, 7):
        print(f'📦 階段{stage_num}：{STAGE_NAMES[stage_num]}')

        # 1. 執行階段
        executor = STAGE_EXECUTORS[stage_num]
        success, result, processor = executor(stage_results)

        # 2. 檢查執行結果
        if not success or not result:
            return False, stage_num, f"階段{stage_num}處理失敗"

        # 3. 保存結果到字典 (供下一階段使用)
        stage_results[f'stage{stage_num}'] = result

        # 4. 立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            processor, result, stage_num, STAGE_NAMES[stage_num]
        )

        # 5. 驗證失敗則停止 (Fail-Fast)
        if not validation_success:
            return False, stage_num, validation_msg

        print(f'✅ 階段{stage_num}完成並驗證通過')

    return True, 6, "所有階段成功完成"
```

**數據流動**:

```
stage_results = {}
  ↓
Stage 1 執行 → stage_results['stage1'] = result1
  ↓ (傳遞 stage_results)
Stage 2 執行 (讀取 stage_results['stage1']) → stage_results['stage2'] = result2
  ↓ (傳遞 stage_results)
Stage 3 執行 (讀取 stage_results['stage2']) → stage_results['stage3'] = result3
  ↓
... (以此類推)
```

### 模式 2: 單一階段執行

**觸發條件**: `--stage N` 參數

```bash
./run.sh --stage 4
python scripts/run_six_stages_with_validation.py --stage 4
```

**執行函數**: `run_stage_specific(target_stage)` (Line 230-257)

**執行流程**:

```python
def run_stage_specific(target_stage, validation_level='STANDARD'):
    if target_stage not in range(1, 7):
        return False, target_stage, f"無效階段: {target_stage}"

    print(f'🎯 執行階段 {target_stage}: {STAGE_NAMES[target_stage]}')

    # 1. 執行階段 (空字典，強制從文件讀取)
    executor = STAGE_EXECUTORS[target_stage]
    success, result, processor = executor({})  # ⚠️ 傳遞空字典

    # 2. 檢查執行結果
    if not success or not result:
        return False, target_stage, f"Stage {target_stage} 執行失敗"

    # 3. 立即驗證
    validation_success, validation_msg = validate_stage_immediately(
        processor, result, target_stage, STAGE_NAMES[target_stage]
    )

    if validation_success:
        return True, target_stage, f"Stage {target_stage} 成功完成並驗證通過"
    else:
        return False, target_stage, f"Stage {target_stage} 驗證失敗"
```

**關鍵設計**: 傳遞空字典 `{}`，強制執行器從磁碟讀取前序輸出文件。

### 模式 3: 階段範圍執行

**觸發條件**: `--stages 1-3` 或 `--stages 1,3,5` 參數

```bash
./run.sh --stages 4-6
./run.sh --stages 1,3,5
python scripts/run_six_stages_with_validation.py --stages 2-4
```

**執行函數**: `main()` 中的範圍處理邏輯 (Line 273-306)

**執行流程**:

```python
if args.stages:
    stages_to_run = []

    # 解析範圍字符串
    if '-' in args.stages:
        # 範圍模式: "1-3" → [1, 2, 3]
        start, end = map(int, args.stages.split('-'))
        stages_to_run = list(range(start, end + 1))
    else:
        # 列舉模式: "1,3,5" → [1, 3, 5]
        stages_to_run = [int(s.strip()) for s in args.stages.split(',')]

    print(f'🎯 運行階段範圍: {stages_to_run}')

    overall_success = True
    stage_results = {}  # 保持階段間數據流動

    for stage in stages_to_run:
        # 執行階段 (傳遞 stage_results)
        executor = STAGE_EXECUTORS[stage]
        success, result, processor = executor(stage_results)

        if not success:
            overall_success = False
            break
        else:
            stage_results[f'stage{stage}'] = result  # 保存結果

    return overall_success
```

**數據流動**: 保持階段間內存傳遞，但起始階段需從文件讀取。

## 驗證流程

### 雙層驗證架構 (Line 108-184)

#### Layer 1: 內建驗證 (Processor 內部)

```python
def validate_stage_immediately(stage_processor, processing_results, stage_num, stage_name):
    # 檢查 ProcessingResult 狀態
    if hasattr(processing_results, "data") and hasattr(processing_results, "status"):
        if processing_results.status.value != 'success':
            return False, f"階段{stage_num}執行失敗"

        # 保存驗證快照
        if hasattr(stage_processor, 'save_validation_snapshot'):
            stage_processor.save_validation_snapshot(processing_results.data)

        # 執行內建驗證
        if hasattr(stage_processor, 'run_validation_checks'):
            validation_result = stage_processor.run_validation_checks(processing_results.data)
            validation_status = validation_result.get('validation_status')

            if validation_status == 'passed':
                # 通過 Layer 1，進入 Layer 2
                return check_validation_snapshot_quality(stage_num)
```

#### Layer 2: 快照品質檢查 (Validator 外部)

```python
def check_validation_snapshot_quality(stage_num):
    """Layer 2 驗證: 使用重構後的模塊化驗證器"""

    # 讀取驗證快照
    snapshot_path = f"data/validation_snapshots/stage{stage_num}_validation.json"
    with open(snapshot_path, 'r', encoding='utf-8') as f:
        snapshot_data = json.load(f)

    # 調用對應的驗證器
    validator = STAGE_VALIDATORS.get(stage_num)
    if validator:
        return validator(snapshot_data)
    else:
        return False, f"❌ Stage {stage_num} 驗證器不存在"
```

### 驗證策略: Fail-Fast

```python
# 在 run_all_stages_sequential() 中
if not validation_success:
    print(f'❌ 階段{stage_num}驗證失敗: {validation_msg}')
    return False, stage_num, validation_msg  # 立即返回，停止後續階段
```

**優勢**:
- 節省計算資源 (不執行無意義的後續階段)
- 快速定位問題階段
- 保持數據一致性 (避免錯誤數據流向下游)

## 命令行參數解析

### 參數定義 (Line 262-265)

```python
parser = argparse.ArgumentParser(description='六階段數據處理系統 (重構版本)')
parser.add_argument('--stage', type=int, choices=[1,2,3,4,5,6], help='運行特定階段')
parser.add_argument('--stages', type=str, help='運行階段範圍，如 "1-2" 或 "1,3,5"')
args = parser.parse_args()
```

### 執行模式選擇邏輯 (Line 273-311)

```python
if args.stages:
    # 模式 3: 階段範圍執行
    success, completed_stage, message = handle_stage_range(args.stages)
elif args.stage:
    # 模式 2: 單一階段執行
    success, completed_stage, message = run_stage_specific(args.stage)
else:
    # 模式 1: 完整管道執行
    success, completed_stage, message = run_all_stages_sequential()
```

## 執行結果輸出

### 統計信息 (Line 316-320)

```python
print(f'📊 執行統計:')
print(f'   執行時間: {execution_time:.2f} 秒')
print(f'   完成階段: {completed_stage}/6')
print(f'   最終狀態: {"✅ 成功" if success else "❌ 失敗"}')
print(f'   訊息: {message}')
```

### 重構版本標識 (Line 322-326)

```python
print('🎯 重構版本優勢:')
print('   📦 模塊化架構 (14個獨立模塊)')
print('   📦 代碼量減少 -75% (1919行 → 332行)')
print('   📦 平均函數長度 -64% (192行 → 69行)')
print('   📦 Git 友好 (減少衝突風險)')
```

## 錯誤處理

### 階段執行失敗

```python
if not success or not result:
    print(f'❌ 階段{stage_num}處理失敗')
    return False, stage_num, f"階段{stage_num}處理失敗"
```

### 驗證失敗

```python
if not validation_success:
    print(f'❌ 階段{stage_num}驗證失敗: {validation_msg}')
    return False, stage_num, validation_msg
```

### 異常處理

```python
try:
    # 執行邏輯
except Exception as e:
    logger.error(f"執行異常: {e}")
    return False, 0, f"執行異常: {e}"
```

## 數據流模式總結

### 管道模式 (完整執行 / 階段範圍執行)

```
┌─────────────┐
│ stage_results│ = {}
└──────┬──────┘
       │
       ├─→ Stage 1 執行 → stage_results['stage1'] = result1
       │
       ├─→ Stage 2 執行 (讀取 stage_results['stage1'])
       │            → stage_results['stage2'] = result2
       │
       ├─→ Stage 3 執行 (讀取 stage_results['stage2'])
       │            → stage_results['stage3'] = result3
       │
       └─→ ... (以此類推)
```

**優勢**: 內存數據傳遞，無需 I/O，性能最佳。

### 文件模式 (單一階段執行)

```
┌──────────────────────────────┐
│ data/outputs/stage3/*.json   │ (前序輸出)
└──────────────┬───────────────┘
               │
               ├─→ Stage 4 執行 (從文件讀取 Stage 3 輸出)
               │
               └─→ data/outputs/stage4/*.json (保存輸出)
```

**優勢**: 可重入性，支持部分管道重跑。

## 執行範例

### 範例 1: 完整管道執行

```bash
$ ./run.sh

🚀 開始六階段數據處理 (重構版本)
============================================================
📦 階段1：數據載入層
------------------------------------------------------------
✅ 階段1完成並驗證通過
============================================================
📦 階段2：軌道狀態傳播層
------------------------------------------------------------
✅ 階段2完成並驗證通過
...
📊 執行統計:
   執行時間: 2314.52 秒
   完成階段: 6/6
   最終狀態: ✅ 成功
```

### 範例 2: 單一階段執行

```bash
$ ./run.sh --stage 5

🎯 執行階段 5: 信號品質分析層
------------------------------------------------------------
📊 階段五：信號品質分析層 (Grade A+ 模式)
✅ 已加載配置文件: stage5_signal_analysis_config.yaml
✅ Stage 5 成功完成並驗證通過

📊 執行統計:
   執行時間: 387.21 秒
   完成階段: 5/6
   最終狀態: ✅ 成功
```

### 範例 3: 階段範圍執行

```bash
$ ./run.sh --stages 4-6

🎯 運行階段範圍: [4, 5, 6]
============================================================
📦 階段4：鏈路可行性評估層
✅ 階段4完成
============================================================
📦 階段5：信號品質分析層
✅ 階段5完成
============================================================
📦 階段6：研究數據生成層
✅ 階段6完成

📊 執行統計:
   執行時間: 612.34 秒
   完成階段: 6/6
   最終狀態: ✅ 成功
```

## 退出碼

```python
return 0 if success else 1
```

- **0**: 所有階段成功完成
- **1**: 至少一個階段執行失敗或驗證失敗

## 日誌輸出

系統使用標準 Python logging 模組：

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

輸出到標準輸出 (stdout)，可重定向到文件：

```bash
./run.sh 2>&1 | tee pipeline_execution.log
```

---

**文檔版本**: v1.0
**創建日期**: 2025-10-10
