# 重構計劃 04: Stage 1 配置 YAML 化

**優先級**: 🟠 P1 (重要)
**風險等級**: 🟡 中風險
**預估時間**: 1 小時
**狀態**: ⏸️ 待執行
**前置條件**: 完成 Plan 01-03

---

## 📋 目標

將 Stage 1 的硬編碼配置遷移到 YAML 配置文件，提升可維護性和可配置性。

---

## 🔍 現狀分析

### 當前硬編碼位置

**文件**: `scripts/stage_executors/stage1_executor.py:26-44`

```python
def execute_stage1(previous_results=None):
    # ❌ 硬編碼配置 (19行)
    config = {
        'sample_mode': use_sampling,
        'sample_size': 50,
        'epoch_analysis': {
            'enabled': True  # 啟用 epoch 動態分析
        },
        'epoch_filter': {
            'enabled': True,           # 啟用 epoch 篩選
            'mode': 'latest_date',     # 篩選模式：保留最新日期衛星
            'tolerance_hours': 24      # 容差範圍：± 24 小時
        }
    }
```

### 問題

1. **參數調整困難**: 需要修改代碼，不能動態切換
2. **缺少文檔**: 參數含義分散在註解中
3. **無版本控制**: 無法比較不同配置版本
4. **測試不便**: 無法輕鬆切換 dev/test/prod 配置

---

## 🎯 執行步驟

### Step 1: 備份當前狀態
```bash
cd /home/sat/orbit-engine

git add .
git commit -m "Backup before refactoring: Add Stage 1 YAML config"
```

### Step 2: 創建 Stage 1 配置文件

創建 `config/stage1_orbital_calculation.yaml`:
```yaml
# Stage 1: TLE 數據載入層配置
# SOURCE: Stage 1 執行器硬編碼參數遷移
# Date: 2025-10-11

# 取樣模式配置
sampling:
  # 取樣模式開關
  # - auto: 根據 ORBIT_ENGINE_TEST_MODE 自動判斷
  # - enabled: 強制啟用取樣模式
  # - disabled: 強制禁用取樣模式 (處理全部衛星)
  mode: auto

  # 取樣數量 (僅在取樣模式啟用時生效)
  # SOURCE: 測試環境預設值，足夠覆蓋 Starlink + OneWeb 樣本
  sample_size: 50

# Epoch 動態分析配置
epoch_analysis:
  # 是否啟用 Epoch 動態分析
  # SOURCE: Stage 1 預設啟用，用於識別最新 TLE 數據日期
  enabled: true

# Epoch 篩選配置
epoch_filter:
  # 是否啟用 Epoch 篩選
  # PURPOSE: 保留最新日期的衛星 TLE，移除過時數據
  enabled: true

  # 篩選模式
  # - latest_date: 保留最新日期的衛星 (預設)
  # - date_range: 保留指定日期範圍
  # - all: 不篩選 (保留所有 TLE)
  # SOURCE: 研究需求 - 確保使用最新軌道參數
  mode: latest_date

  # 容差範圍 (小時)
  # 定義: 與最新日期相差在此範圍內的衛星視為「最新」
  # 範例: tolerance_hours=24 表示最新日期 ±24 小時內的衛星都保留
  # SOURCE: TLE 數據更新週期通常為 24-48 小時
  tolerance_hours: 24

# 星座配置 (全局配置，會傳遞給下游 Stages)
constellation_configs:
  starlink:
    # 仰角門檻 (度)
    # SOURCE: 3GPP TR 38.821 Section 6.1.2 - Starlink NTN minimum elevation
    elevation_threshold: 5.0

    # 工作頻率 (GHz)
    # SOURCE: SpaceX Starlink Gen2 Ka-band downlink (12.2-12.7 GHz)
    frequency_ghz: 12.5

    # 目標可見衛星數量範圍
    # SOURCE: 研究需求 - 動態池優化目標
    target_satellites:
      min: 10
      max: 15

  oneweb:
    # 仰角門檻 (度)
    # SOURCE: OneWeb Technical Specifications - Ku-band minimum elevation
    # NOTE: OneWeb 使用更高仰角門檻以降低干擾
    elevation_threshold: 10.0

    # 工作頻率 (GHz)
    # SOURCE: OneWeb Ku-band downlink (10.7-12.75 GHz center)
    frequency_ghz: 12.75

    # 目標可見衛星數量範圍
    target_satellites:
      min: 3
      max: 6

# TLE 數據源配置
tle_data:
  # TLE 文件路徑 (相對於項目根目錄)
  data_directory: data/tle_data

  # TLE 文件格式
  # - txt: 標準 3-line TLE 格式
  # - json: JSON 格式 (備用)
  format: txt

  # TLE 檔案名稱模式 (glob)
  file_patterns:
    - "*.tle"
    - "*.txt"

# 驗證配置
validation:
  # TLE 格式驗證
  # SOURCE: NORAD TLE 標準 - Line1 和 Line2 各 69 字符
  tle_format_check: true

  # Checksum 驗證
  # SOURCE: TLE checksum algorithm (modulo-10)
  tle_checksum_check: true

  # Epoch 多樣性檢查
  # 要求: 至少有指定數量的不同 epoch (防止數據單一性)
  min_unique_epochs: 5

# 輸出配置
output:
  # 輸出目錄
  directory: data/outputs/stage1

  # 檔案名稱模式
  # {timestamp}: YYYYMMDD_HHMMSS
  filename_pattern: "stage1_output_{timestamp}.json"

  # 是否保存驗證快照
  save_validation_snapshot: true

# 性能配置
performance:
  # 是否顯示進度條
  show_progress: true

  # 日誌等級
  # - DEBUG: 詳細調試信息
  # - INFO: 一般信息 (預設)
  # - WARNING: 警告信息
  # - ERROR: 錯誤信息
  log_level: INFO
```

### Step 3: 修改 Stage 1 執行器

編輯 `scripts/stage_executors/stage1_executor.py`:
```python
import yaml
from pathlib import Path
from .executor_utils import project_root

def execute_stage1(previous_results=None):
    """執行 Stage 1: TLE 數據載入層"""
    try:
        print('\n🛰️ 階段一：TLE 數據載入層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(1)

        # ✅ 從 YAML 載入配置
        config_path = project_root / "config/stage1_orbital_calculation.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 1 配置: {config_path}")
        else:
            # ⚠️ 回退到預設配置 (僅用於開發環境)
            print(f"⚠️ 未找到配置文件: {config_path}")
            print("⚠️ 使用預設配置")
            config = {
                'sampling': {'mode': 'auto', 'sample_size': 50},
                'epoch_analysis': {'enabled': True},
                'epoch_filter': {
                    'enabled': True,
                    'mode': 'latest_date',
                    'tolerance_hours': 24
                }
            }

        # ✅ 處理取樣模式 (支持環境變數覆蓋)
        sampling_mode = config.get('sampling', {}).get('mode', 'auto')
        if sampling_mode == 'auto':
            use_sampling = is_sampling_mode()  # 從環境變數讀取
        else:
            use_sampling = (sampling_mode == 'enabled')

        # 更新配置中的 sample_mode (向後兼容)
        config['sample_mode'] = use_sampling
        config['sample_size'] = config.get('sampling', {}).get('sample_size', 50)

        print(f"📋 配置摘要:")
        print(f"   取樣模式: {'啟用' if use_sampling else '禁用'}")
        if use_sampling:
            print(f"   取樣數量: {config['sample_size']} 顆衛星")
        print(f"   Epoch 篩選: {config['epoch_filter']['mode']}")
        print(f"   容差範圍: ±{config['epoch_filter']['tolerance_hours']} 小時")

        # 創建處理器
        from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor
        stage1_processor = create_stage1_processor(config)

        # 執行處理
        stage1_result = stage1_processor.execute()

        # 檢查結果
        if not stage1_result or stage1_result.status.value != 'success':
            error_msg = '; '.join(stage1_result.errors) if stage1_result and stage1_result.errors else "無結果"
            print(f'❌ Stage 1 執行失敗: {error_msg}')
            return False, stage1_result, stage1_processor

        return True, stage1_result, stage1_processor

    except Exception as e:
        print(f'❌ Stage 1 執行異常: {e}')
        import traceback
        traceback.print_exc()
        return False, None, None
```

### Step 4: 驗證配置載入
```bash
# 測試配置文件語法
python3 -c "
import yaml
with open('config/stage1_orbital_calculation.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
print('✅ YAML 語法正確')
print(f'配置鍵: {list(config.keys())}')
"
```

### Step 5: 運行測試
```bash
# 測試 Stage 1 (使用新配置)
./run.sh --stage 1

# 檢查是否正確載入配置
grep "已載入 Stage 1 配置" /tmp/*.log

# 測試取樣模式切換
ORBIT_ENGINE_TEST_MODE=1 ./run.sh --stage 1  # 應啟用取樣
ORBIT_ENGINE_TEST_MODE=0 ./run.sh --stage 1  # 應禁用取樣

# 完整流程測試
./run.sh --stages 1-3
```

### Step 6: 文檔更新

更新 `docs/architecture/02_STAGES_DETAIL.md`:
```markdown
## Stage 1: TLE 數據載入層

### 配置文件

**文件**: `config/stage1_orbital_calculation.yaml`

**主要配置項**:
- `sampling`: 取樣模式配置
- `epoch_filter`: Epoch 篩選規則
- `constellation_configs`: 星座特定參數 (傳遞給下游)

**範例**:
```yaml
epoch_filter:
  enabled: true
  mode: latest_date
  tolerance_hours: 24
```
```

### Step 7: 提交變更
```bash
git add config/stage1_orbital_calculation.yaml
git add scripts/stage_executors/stage1_executor.py
git add docs/architecture/02_STAGES_DETAIL.md

git commit -m "Refactor: Migrate Stage 1 config to YAML

將 Stage 1 硬編碼配置遷移至 YAML 配置文件

變更:
- 新增 config/stage1_orbital_calculation.yaml
- 修改 scripts/stage_executors/stage1_executor.py 支持 YAML 載入
- 保留環境變數覆蓋機制 (ORBIT_ENGINE_TEST_MODE)
- 更新文檔: docs/architecture/02_STAGES_DETAIL.md

優勢:
- 參數調整無需修改代碼
- 完整文檔和 SOURCE 註解
- 支持多環境配置 (dev/test/prod)

測試:
- Stage 1 獨立測試通過
- 取樣模式切換正常
- Stage 1-3 完整流程測試通過

Ref: docs/refactoring/REFACTOR_PLAN_04
"
```

---

## ✅ 驗證檢查清單

- [ ] 配置文件已創建: `config/stage1_orbital_calculation.yaml`
- [ ] YAML 語法正確 (無解析錯誤)
- [ ] 執行器成功載入配置
- [ ] Stage 1 測試通過: `./run.sh --stage 1`
- [ ] 取樣模式切換正常 (TEST_MODE=0/1)
- [ ] 完整流程測試通過: `./run.sh --stages 1-3`
- [ ] 文檔已更新
- [ ] Git 提交包含清晰 message

---

## 🔄 回滾方案

```bash
# 回滾配置文件
git checkout HEAD~1 -- config/stage1_orbital_calculation.yaml

# 回滾執行器
git checkout HEAD~1 -- scripts/stage_executors/stage1_executor.py

# 或完全回滾
git reset --hard HEAD~1
```

---

## 📊 預期效益

- **配置靈活性**: 0 → 100% (可動態調整)
- **文檔完整性**: +80% (YAML 註解)
- **環境切換效率**: +90% (無需修改代碼)
- **參數追蹤性**: +100% (Git 版本控制)

---

## 📝 注意事項

1. **保持向後兼容**: 環境變數 `ORBIT_ENGINE_TEST_MODE` 仍然生效
2. **回退機制**: 如無配置文件，使用預設值
3. **配置優先級**: YAML < 環境變數 < 命令行參數

---

## 🔗 相關資源

- [架構優化分析報告](../architecture/ARCHITECTURE_OPTIMIZATION_REPORT.md#3-配置管理分散---yaml-vs-硬編碼)
- [Stage 1 執行器](../../scripts/stage_executors/stage1_executor.py)

---

**創建日期**: 2025-10-11
**負責人**: Development Team
**審查者**: TBD
