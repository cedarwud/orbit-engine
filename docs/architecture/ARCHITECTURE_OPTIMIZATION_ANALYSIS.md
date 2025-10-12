# Orbit Engine 架構優化分析報告

**日期**: 2025-10-12
**版本**: v1.0
**分析範圍**: 整體專案架構 (src/, scripts/, config/)

---

## 執行摘要

### 當前架構健康度: **B+ (85/100)**

**優點** ✅:
- 清晰的六階段管道架構
- 統一的 BaseStageProcessor 接口
- 良好的學術標準遵循
- 完整的驗證快照機制

**待優化空間** ⚠️:
1. **執行器重複代碼** (優先級: P0)
2. **驗證邏輯分散** (優先級: P1)
3. **配置管理不統一** (優先級: P1)
4. **接口使用不一致** (優先級: P2)
5. **模塊職責不清晰** (優先級: P2)

---

## 🔴 P0 級優化 - 執行器重複代碼

### 問題描述

6 個執行器文件 (stage1_executor.py ~ stage6_executor.py) 共計 568 行，存在**大量重複模式**：

```python
# ❌ 每個執行器都重複這些模式:

def execute_stageN(previous_results):
    try:
        print('\n📦 階段N：...')
        print('-' * 60)

        # 清理舊輸出 (重複 6 次)
        clean_stage_outputs(N)

        # 尋找前階段輸出 (重複 5 次)
        stageN_output = find_latest_stage_output(N-1)
        if not stageN_output:
            print(f'❌ 找不到 Stage {N-1} 輸出文件')
            return False, None, None

        # 載入配置 (部分一致，部分不一致)
        config = load_config(...)

        # 創建處理器 (重複模式)
        processor = StageNProcessor(config)

        # 載入前階段數據 (重複 5 次)
        with open(stageN_output, 'r') as f:
            data = json.load(f)

        # 執行處理 (不一致：有的用 execute(), 有的用 process())
        result = processor.execute(data)

        # 檢查結果 (邏輯相似但不完全一致)
        if not result or result.status != ProcessingStatus.SUCCESS:
            return False, result, processor

        # 保存快照 (部分重複)
        if hasattr(processor, 'save_validation_snapshot'):
            processor.save_validation_snapshot(result.data)

        return True, result, processor

    except Exception as e:
        print(f'❌ Stage {N} 執行異常: {e}')
        return False, None, None
```

**重複率分析**:
- 結構性重複: ~70%
- 錯誤處理: 100% 重複
- 數據載入: 85% 重複

### 推薦方案: 引入 StageExecutor 基類

```python
# ✅ 新架構: scripts/stage_executors/base_executor.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import json
import yaml
from .executor_utils import clean_stage_outputs, find_latest_stage_output, project_root

class StageExecutor(ABC):
    """
    階段執行器基類 - 統一執行流程

    子類只需實現:
    1. get_stage_info() - 階段基本信息
    2. load_config() - 配置載入邏輯
    3. create_processor() - 處理器創建
    """

    def __init__(self, stage_number: int, stage_name: str):
        self.stage_number = stage_number
        self.stage_name = stage_name

    def execute(self, previous_results: Optional[Dict] = None) -> Tuple[bool, Any, Any]:
        """
        統一執行流程 (Template Method Pattern)

        流程:
        1. 顯示階段信息
        2. 清理舊輸出
        3. 載入前階段數據（如需要）
        4. 載入配置
        5. 創建處理器
        6. 執行處理
        7. 保存驗證快照
        8. 錯誤處理
        """
        try:
            self._print_stage_header()
            clean_stage_outputs(self.stage_number)

            # 載入前階段數據
            input_data = None
            if self.stage_number > 1:
                input_data = self._load_previous_stage_data()
                if input_data is None and self.requires_previous_stage():
                    return False, None, None

            # 載入配置
            config = self.load_config()

            # 創建處理器
            processor = self.create_processor(config)

            # 執行處理 (統一使用 execute 方法)
            result = processor.execute(input_data)

            # 檢查結果
            if not self._check_result(result):
                return False, result, processor

            # 保存驗證快照（如果處理器支持）
            self._save_validation_snapshot(processor, result)

            return True, result, processor

        except Exception as e:
            print(f'❌ Stage {self.stage_number} 執行異常: {e}')
            return False, None, None

    def _print_stage_header(self):
        """顯示階段頭部信息"""
        print(f'\n📦 階段{self.stage_number}：{self.stage_name}')
        print('-' * 60)

    def _load_previous_stage_data(self) -> Optional[Dict]:
        """載入前階段數據"""
        previous_stage = self.stage_number - 1
        output_file = find_latest_stage_output(previous_stage)

        if not output_file:
            print(f'❌ 找不到 Stage {previous_stage} 輸出文件')
            return None

        with open(output_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _check_result(self, result) -> bool:
        """檢查處理結果"""
        from src.shared.interfaces import ProcessingStatus

        if not result:
            print(f'❌ Stage {self.stage_number} 無返回結果')
            return False

        if result.status != ProcessingStatus.SUCCESS:
            errors = '; '.join(result.errors) if result.errors else "未知錯誤"
            print(f'❌ Stage {self.stage_number} 執行失敗: {errors}')
            return False

        if not result.data:
            print(f'❌ Stage {self.stage_number} 返回數據為空')
            return False

        return True

    def _save_validation_snapshot(self, processor, result):
        """保存驗證快照"""
        if hasattr(processor, 'save_validation_snapshot'):
            try:
                processor.save_validation_snapshot(result.data)
                print(f'✅ Stage {self.stage_number} 驗證快照已保存')
            except Exception as e:
                print(f'⚠️ Stage {self.stage_number} 驗證快照保存失敗: {e}')

    # ===== 子類需實現的抽象方法 =====

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """
        載入階段配置

        Returns:
            配置字典
        """
        pass

    @abstractmethod
    def create_processor(self, config: Dict[str, Any]) -> Any:
        """
        創建處理器實例

        Args:
            config: 配置字典

        Returns:
            處理器實例
        """
        pass

    def requires_previous_stage(self) -> bool:
        """
        是否需要前階段數據（默認 Stage 1 不需要，其他需要）

        Returns:
            是否需要
        """
        return self.stage_number > 1


# ✅ 使用範例: scripts/stage_executors/stage1_executor.py (重構後)

from .base_executor import StageExecutor

class Stage1Executor(StageExecutor):
    """Stage 1 執行器 - TLE 數據載入層"""

    def __init__(self):
        super().__init__(stage_number=1, stage_name="TLE 數據載入層")

    def load_config(self) -> Dict[str, Any]:
        """載入 Stage 1 配置"""
        config_path = project_root / "config/stage1_orbital_calculation.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 1 配置: {config_path}")
        else:
            print(f"⚠️ 未找到配置文件，使用預設配置")
            config = self._get_default_config()

        # 處理取樣模式
        from .executor_utils import is_sampling_mode
        config['sample_mode'] = is_sampling_mode()

        return config

    def create_processor(self, config: Dict[str, Any]):
        """創建 Stage 1 處理器"""
        from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor
        return create_stage1_processor(config)

    def requires_previous_stage(self) -> bool:
        """Stage 1 不需要前階段數據"""
        return False

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            'sampling': {'mode': 'auto', 'sample_size': 50},
            'epoch_analysis': {'enabled': True},
            'epoch_filter': {
                'enabled': True,
                'mode': 'latest_date',
                'tolerance_hours': 24
            }
        }

# 新的入口函數 (向後兼容)
def execute_stage1(previous_results=None):
    executor = Stage1Executor()
    return executor.execute(previous_results)
```

**優勢**:
- ✅ 代碼減少: 568 行 → ~350 行 (-38%)
- ✅ 維護性提升: 統一錯誤處理、日誌格式
- ✅ 可測試性提升: 可單獨測試基類邏輯
- ✅ 向後兼容: 保留原有 `execute_stageN()` 函數
- ✅ 擴展性: 新增階段只需實現 3 個方法

---

## 🟠 P1 級優化 - 驗證邏輯分散與重複

### 問題描述

驗證邏輯分散在 3 個地方，職責不清晰：

1. **處理器內部驗證** (`processor.validate_input/validate_output`)
   - 位置: `src/stages/stageN_*/stageN_*_processor.py`
   - 職責: 數據結構驗證

2. **快照驗證器** (`scripts/stage_validators/stageN_validator.py`)
   - 位置: `scripts/stage_validators/`
   - 職責: 驗證快照合理性

3. **專用驗證模塊** (`src/stages/stageN_*/stageN_compliance_validator.py`)
   - 位置: 部分階段有（如 Stage 5）
   - 職責: 學術標準合規性

**問題**:
- ❌ 職責重疊，部分檢查重複（如 epoch 檢查）
- ❌ 命名不一致 (`validator` vs `compliance_validator`)
- ❌ 難以追蹤某個檢查應該在哪裡進行

### 推薦方案: 三層驗證架構

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: 處理器內部驗證 (BaseStageProcessor)                  │
│ 職責: 數據結構完整性 (字段存在性、類型正確性)                    │
│ 方法: validate_input(), validate_output()                    │
│ 時機: 處理前後立即執行                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: 學術合規驗證 (StageComplianceValidator)              │
│ 職責: 學術標準遵循 (ITU-R/3GPP 參數範圍、算法正確性)            │
│ 方法: validate_academic_compliance()                         │
│ 時機: 處理器內調用 (before save)                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: 快照驗證 (scripts/stage_validators)                 │
│ 職責: 回歸測試、管道完整性 (衛星數量一致性、格式正確性)           │
│ 方法: check_stageN_validation()                              │
│ 時機: 管道執行完成後批次檢查                                   │
└─────────────────────────────────────────────────────────────┘
```

**實現範例**:

```python
# src/shared/validation_framework/stage_compliance_validator.py (新增)

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class StageComplianceValidator(ABC):
    """
    階段學術合規驗證器基類

    職責: 驗證處理結果符合 ITU-R/3GPP/NASA JPL 學術標準
    """

    def __init__(self, stage_number: int):
        self.stage_number = stage_number
        self.violations = []

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行完整合規驗證

        Returns:
            {
                'valid': bool,
                'violations': List[str],  # 違規項目
                'warnings': List[str],    # 警告項目
                'checks_performed': List[str]
            }
        """
        self.violations = []
        warnings = []
        checks_performed = []

        # 執行各項檢查
        checks = [
            ('parameter_ranges', self.check_parameter_ranges),
            ('algorithm_compliance', self.check_algorithm_compliance),
            ('data_source_authenticity', self.check_data_source_authenticity)
        ]

        for check_name, check_func in checks:
            try:
                check_result = check_func(data)
                checks_performed.append(check_name)

                if not check_result['valid']:
                    self.violations.extend(check_result['violations'])
                if check_result.get('warnings'):
                    warnings.extend(check_result['warnings'])
            except Exception as e:
                warnings.append(f"{check_name} 檢查失敗: {e}")

        return {
            'valid': len(self.violations) == 0,
            'violations': self.violations,
            'warnings': warnings,
            'checks_performed': checks_performed
        }

    @abstractmethod
    def check_parameter_ranges(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查參數範圍（子類實現具體標準）"""
        pass

    @abstractmethod
    def check_algorithm_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查算法合規性（子類實現具體標準）"""
        pass

    @abstractmethod
    def check_data_source_authenticity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數據源真實性（子類實現具體標準）"""
        pass


# Stage 5 範例實現
class Stage5ComplianceValidator(StageComplianceValidator):
    """Stage 5 學術合規驗證器 - 信號品質分析"""

    def check_parameter_ranges(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        檢查 3GPP/ITU-R 參數範圍

        SOURCE: 3GPP TS 38.215 v18.1.0, ITU-R P.676-13
        """
        violations = []

        signal_analysis = data.get('signal_analysis', {})
        for sat_id, sat_data in signal_analysis.items():
            for ts in sat_data.get('time_series', []):
                rsrp = ts['signal_quality']['rsrp_dbm']

                # 3GPP TS 38.215: RSRP 測量範圍 -156 ~ -31 dBm
                # 注意：這是測量範圍，非截斷範圍
                if rsrp < -156 or rsrp > -31:
                    violations.append(
                        f"❌ 衛星 {sat_id} RSRP={rsrp} dBm 超出 3GPP TS 38.215 測量範圍 [-156, -31]"
                    )

        return {
            'valid': len(violations) == 0,
            'violations': violations
        }

    def check_algorithm_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查算法使用 ITU-R 官方實現"""
        violations = []

        metadata = data.get('metadata', {})
        atmospheric_model = metadata.get('atmospheric_model', '')

        if 'ITU-R P.676-13' not in atmospheric_model:
            violations.append(
                "❌ 未使用 ITU-R P.676-13 官方大氣模型 (要求使用 itur 官方套件)"
            )

        return {
            'valid': len(violations) == 0,
            'violations': violations
        }

    def check_data_source_authenticity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數據源追溯性"""
        warnings = []

        # 檢查是否有參數來源註釋 (透過 metadata 追蹤)
        config = data.get('metadata', {}).get('config', {})
        if not config.get('parameter_sources'):
            warnings.append(
                "⚠️ 缺少參數來源追溯信息 (建議在 config 中加入 parameter_sources)"
            )

        return {
            'valid': True,
            'violations': [],
            'warnings': warnings
        }
```

**職責劃分表**:

| 驗證層級 | 檢查內容 | 範例 | 失敗影響 |
|---------|---------|------|---------|
| Layer 1 (處理器) | 數據結構 | `satellites` 字段存在、RSRP 非 None | 立即返回錯誤 |
| Layer 2 (合規) | 學術標準 | RSRP 範圍 [-156, -31] dBm | 記錄違規但允許繼續 |
| Layer 3 (快照) | 回歸測試 | 衛星數量與 Stage 4 一致 | 管道執行失敗 |

---

## 🟠 P1 級優化 - 配置管理不統一

### 問題描述

6 個階段的配置管理方式不一致：

| 階段 | 配置文件 | 加載方式 | 問題 |
|-----|---------|---------|------|
| Stage 1 | `stage1_orbital_calculation.yaml` | ✅ YAML | 良好 |
| Stage 2 | `stage2_orbital_computing.yaml` | ✅ YAML | 良好 |
| Stage 3 | `stage3_coordinate_transformation.yaml` | ✅ YAML | 良好 |
| Stage 4 | `stage4_link_feasibility_config.yaml` | ✅ YAML | 良好 |
| Stage 5 | `stage5_signal_analysis_config.yaml` | ✅ YAML | 良好 |
| **Stage 6** | **❌ 無配置文件** | **硬編碼在執行器** | **不一致** |

**Stage 6 當前問題**:
```python
# ❌ 配置硬編碼在 stage6_executor.py (不存在)
# ❌ 處理器內部使用預設值
# ❌ 無法在不修改代碼的情況下調整參數
```

### 推薦方案: 統一配置管理

```yaml
# config/stage6_research_optimization_config.yaml (新增)

# Stage 6: 研究數據生成層配置
# 功能: 3GPP 換手事件檢測 + 強化學習訓練數據生成

event_detection:
  # A3: 鄰居信號優於服務衛星（相對偏移）
  # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4
  a3_offset_db: 3.0

  # A4: 鄰居信號超過絕對門檻
  # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.5
  a4_threshold_dbm: -110

  # A5: 服務信號劣化且鄰居良好
  # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.6
  a5_threshold1_dbm: -110  # 服務門檻
  a5_threshold2_dbm: -95   # 鄰居門檻

  # D2: 地面基站切換事件（未來實現）
  d2_enabled: false
  d2_rsrp_threshold_dbm: -100

  # 通用事件參數
  hysteresis_db: 2.0           # 遲滯（防止頻繁切換）
  time_to_trigger_ms: 640      # 觸發時間（L3 過濾）

handover_decision:
  # 評估模式: "batch" (批次評估) | "realtime" (實時評估)
  # 注意: 本系統為學術研究用途，推薦使用 batch 模式
  evaluation_mode: "batch"

  # 服務衛星選擇策略: "median" (中位數) | "max_rsrp" (最大RSRP)
  # SOURCE: 3GPP TS 36.300 Section 10.1.2.2 (Handover decision)
  serving_selection_strategy: "median"

  # 候選衛星排序: "rsrp" (按RSRP降序) | "elevation" (按仰角降序)
  candidate_ranking: "rsrp"

  # 性能監控（生產環境功能，學術研究建議禁用）
  enable_performance_metrics: false

  # 自適應門檻（生產環境功能，學術研究建議禁用）
  enable_adaptive_thresholds: false

research_data_generation:
  # 強化學習狀態空間特徵
  state_features:
    - "serving_rsrp"        # 服務衛星 RSRP
    - "neighbor_rsrp"       # 鄰居衛星 RSRP
    - "elevation_deg"       # 仰角
    - "slant_range_km"      # 斜距
    - "rsrp_delta_db"       # RSRP 差值

  # 動作空間
  action_space:
    - "stay"                # 保持當前服務衛星
    - "handover"            # 切換到鄰居衛星

  # 獎勵函數參數
  reward_config:
    rsrp_weight: 0.6        # RSRP 權重
    stability_weight: 0.3   # 穩定性權重 (減少換手次數)
    elevation_weight: 0.1   # 仰角權重

validation:
  # 驗證快照配置
  save_snapshot: true
  snapshot_sample_size: 100  # 保存前 100 個事件作為樣本

output:
  # 輸出格式配置
  include_event_details: true      # 包含事件詳細信息
  include_state_action_pairs: true # 包含 RL 訓練數據
  compress_output: false           # 是否壓縮輸出 (大數據集建議啟用)
```

**統一配置加載工具**:

```python
# src/shared/configs/config_loader.py (新增)

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class StageConfigLoader:
    """統一的階段配置加載器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / "config"

    def load_stage_config(self, stage_number: int,
                         required: bool = True) -> Dict[str, Any]:
        """
        載入階段配置文件

        Args:
            stage_number: 階段編號 (1-6)
            required: 是否必須存在配置文件

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 如果 required=True 且文件不存在
        """
        config_files = list(self.config_dir.glob(f"stage{stage_number}_*.yaml"))

        if not config_files:
            if required:
                raise FileNotFoundError(
                    f"Stage {stage_number} 配置文件不存在: {self.config_dir}/stage{stage_number}_*.yaml"
                )
            return {}

        config_file = config_files[0]
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 添加元數據
        config['_metadata'] = {
            'config_file': str(config_file),
            'stage_number': stage_number,
            'loaded_at': datetime.now(timezone.utc).isoformat()
        }

        return config

    def validate_config_structure(self, config: Dict[str, Any],
                                  schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證配置結構（簡化版，可擴展為 JSON Schema 驗證）

        Args:
            config: 配置字典
            schema: 模式定義

        Returns:
            驗證結果
        """
        errors = []

        for key, expected_type in schema.items():
            if key not in config:
                errors.append(f"缺少必要配置項: {key}")
            elif not isinstance(config[key], expected_type):
                errors.append(
                    f"配置項類型錯誤: {key} (期望 {expected_type.__name__}, "
                    f"實際 {type(config[key]).__name__})"
                )

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
```

---

## 🟡 P2 級優化 - 接口使用不一致

### 問題描述

不同階段的處理器接口使用不一致：

```python
# ❌ 不一致的接口使用

# Stage 1, 2, 3: 繼承 BaseStageProcessor，使用 process()
class Stage1MainProcessor(BaseStageProcessor):
    def process(self, input_data: Optional[Dict] = None) -> ProcessingResult:
        ...

# Stage 4: 繼承 BaseStageProcessor，但使用 process() (正確)
class Stage4LinkFeasibilityProcessor(BaseStageProcessor):
    def process(self, input_data: Any) -> ProcessingResult:
        ...

# Stage 5: 繼承 BaseStageProcessor，但重寫了 execute()
class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    def execute(self, input_data: Optional[Any] = None) -> ProcessingResult:
        # 完全重寫，沒有調用 super().execute()
        ...

# Stage 6: 繼承 BaseStageProcessor，也重寫了 execute()
class Stage6ResearchOptimizationProcessor(BaseStageProcessor):
    def execute(self, input_data: Optional[Dict] = None) -> ProcessingResult:
        ...
```

**BaseStageProcessor 設計原則** (Line 88-223):
```python
# ✅ 設計意圖: Template Method Pattern
# 子類應實現 process()，而非覆蓋 execute()

class BaseStageProcessor:
    def execute(self, input_data):
        """統一流程 - 子類不應覆蓋"""
        # 1. 輸入驗證
        # 2. 調用 process() (子類實現)
        # 3. 輸出驗證
        # 4. 保存快照
        ...

    @abstractmethod
    def process(self, input_data):
        """子類實現主邏輯"""
        pass
```

### 推薦方案: 統一使用 process()

```python
# ✅ Stage 5 重構範例

class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    """
    Stage 5: 信號品質分析處理器

    🔧 重構: 從 execute() 遷移到 process()
    好處: 自動獲得 BaseStageProcessor 的統一流程（驗證、快照、錯誤處理）
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            stage_number=5,
            stage_name="signal_analysis",
            config=config
        )
        # ... 初始化代碼保持不變

    def process(self, input_data: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        執行信號品質分析 (主邏輯)

        Args:
            input_data: Stage 4 輸出數據

        Returns:
            ProcessingResult: 包含信號分析結果
        """
        try:
            # 原 execute() 的主邏輯直接遷移到這裡
            self.logger.info("🔄 開始信號品質分析")

            # 提取輸入數據
            stage4_data = self.input_extractor.extract(input_data)

            # 執行信號分析
            signal_results = self._analyze_signals(stage4_data)

            # 構建輸出
            output_data = self.result_builder.build_result(signal_results)

            # 返回成功結果
            return create_success_result(output_data)

        except Exception as e:
            self.logger.error(f"信號分析失敗: {e}", exc_info=True)
            return create_error_result([str(e)])

    # validate_input/validate_output 保持不變
```

**遷移步驟**:

1. **Stage 5**:
   ```bash
   # 重命名當前 execute() 為 process()
   # 移除手動的驗證快照保存代碼（基類會處理）
   ```

2. **Stage 6**:
   ```bash
   # 同 Stage 5
   ```

3. **更新文檔**:
   ```bash
   # 更新 docs/architecture/02_STAGES_DETAIL.md
   # 明確標注所有處理器使用 process() 方法
   ```

---

## 🟡 P2 級優化 - 共享模塊組織

### 問題描述

`src/shared/` 模塊結構存在職責不清晰的問題：

```
src/shared/
├── base_processor.py                    # ✅ 清晰
├── constants/                           # ✅ 清晰
│   ├── academic_standards.py
│   ├── constellation_constants.py
│   └── ...
├── coordinate_systems/                  # ✅ 清晰
│   ├── iers_data_manager.py
│   ├── skyfield_coordinate_engine.py
│   └── wgs84_manager.py
├── interfaces/                          # ✅ 清晰
│   └── processor_interface.py
├── utils/                               # ⚠️ 太寬泛
│   ├── coordinate_converter.py          # 應屬於 coordinate_systems
│   ├── file_utils.py                    # ✅ 合適
│   ├── ground_distance_calculator.py    # 應屬於 coordinate_systems
│   ├── math_utils.py                    # ✅ 合適
│   └── time_utils.py                    # ✅ 合適
└── validation_framework/                # ❌ 職責不清
    ├── academic_validation_framework.py # 複雜，職責過多
    ├── real_time_snapshot_system.py     # 與項目定位不符（非實時系統）
    ├── stage4_validator.py              # 應在 stages/stage4_*/ 內
    ├── stage5_signal_validator.py       # 應在 stages/stage5_*/ 內
    └── validation_engine.py             # 重複於 processor_interface
```

### 推薦方案: 重組共享模塊

```
src/shared/
├── base/                                # 基礎類和接口
│   ├── __init__.py
│   ├── base_processor.py
│   └── processor_interface.py
│
├── constants/                           # 常量定義（保持不變）
│   ├── __init__.py
│   ├── academic_standards.py
│   ├── constellation_constants.py
│   └── ...
│
├── coordinate_systems/                  # 座標系統（整合）
│   ├── __init__.py
│   ├── converters/
│   │   ├── ecef_geodetic.py            # 從 utils 移入
│   │   └── teme_ecef.py
│   ├── iers_data_manager.py
│   ├── skyfield_coordinate_engine.py
│   └── wgs84_manager.py
│
├── validation/                          # 驗證框架（重構）
│   ├── __init__.py
│   ├── compliance_validator.py         # 學術合規驗證基類
│   ├── data_validator.py               # 數據結構驗證工具
│   └── snapshot_manager.py             # 快照管理（簡化版）
│
├── configs/                             # 配置管理（新增）
│   ├── __init__.py
│   └── config_loader.py                # 統一配置加載器
│
└── utils/                               # 通用工具（精簡）
    ├── __init__.py
    ├── file_utils.py
    ├── math_utils.py
    └── time_utils.py
```

**遷移原則**:

1. **coordinate_systems** 整合:
   ```python
   # 從 utils/coordinate_converter.py 移動到
   # coordinate_systems/converters/ecef_geodetic.py
   ```

2. **validation_framework** 簡化:
   ```python
   # 移除 real_time_snapshot_system.py (不符合項目定位)
   # 移除 stage4_validator.py, stage5_signal_validator.py
   #   → 移動到對應階段目錄 src/stages/stageN_*/
   ```

3. **新增 configs** 模塊:
   ```python
   # 統一配置加載邏輯
   ```

---

## 📊 優化效益評估

### 代碼減少預估

| 優化項目 | 當前行數 | 優化後行數 | 減少率 |
|---------|---------|-----------|-------|
| 執行器重複代碼 | 568 | 350 | -38% |
| 驗證邏輯整合 | ~1200 | ~800 | -33% |
| 共享模塊重組 | ~1500 | ~1300 | -13% |
| **總計** | **~3268** | **~2450** | **-25%** |

### 維護性提升

- ✅ **統一模式**: 新增階段只需實現 3 個方法
- ✅ **錯誤追蹤**: 統一錯誤處理和日誌格式
- ✅ **測試覆蓋**: 基類邏輯可單獨測試
- ✅ **文檔一致性**: 減少文檔維護工作量

### 風險評估

| 優化項目 | 風險等級 | 緩解措施 |
|---------|---------|---------|
| 執行器重構 | 🟢 低 | 保留向後兼容接口 |
| 驗證邏輯重組 | 🟡 中 | 分階段遷移，保留原邏輯 |
| 接口統一 | 🟡 中 | 完整測試覆蓋 |
| 模塊重組 | 🟠 中高 | 使用 deprecation 警告 |

---

## 🗺️ 實施路線圖

### Phase 1: 執行器重構 (1-2 天)

**目標**: 減少重複代碼，統一執行流程

1. **Day 1**: 實現 `StageExecutor` 基類
   - 創建 `scripts/stage_executors/base_executor.py`
   - 編寫單元測試

2. **Day 1-2**: 遷移所有執行器
   - Stage 1 → Stage 6 依次遷移
   - 每個階段遷移後執行完整測試

3. **Day 2**: 驗證與文檔
   - 運行完整管道測試
   - 更新 `docs/architecture/02_STAGES_DETAIL.md`

### Phase 2: 驗證邏輯重組 (2-3 天)

**目標**: 三層驗證架構清晰化

1. **Day 1**: 設計與實現基類
   - 創建 `StageComplianceValidator` 基類
   - 編寫驗證框架文檔

2. **Day 2**: 遷移現有驗證器
   - Stage 5 ComplianceValidator 遷移（已有）
   - Stage 4 新增 ComplianceValidator

3. **Day 3**: 整合與測試
   - 更新處理器調用驗證器的邏輯
   - 運行回歸測試

### Phase 3: 配置統一 (1 天)

**目標**: Stage 6 配置文件化

1. **創建配置文件**: `config/stage6_research_optimization_config.yaml`
2. **實現配置加載器**: `src/shared/configs/config_loader.py`
3. **更新 Stage 6 執行器**: 使用配置文件
4. **測試與驗證**: 確保參數可調整

### Phase 4: 接口統一 (1-2 天)

**目標**: 所有處理器使用 `process()` 方法

1. **Day 1**: Stage 5 遷移
   - 重命名 `execute()` → `process()`
   - 移除手動快照保存
   - 測試驗證

2. **Day 1-2**: Stage 6 遷移
   - 同 Stage 5

3. **Day 2**: 文檔更新
   - 更新架構文檔
   - 添加最佳實踐指南

### Phase 5: 模塊重組 (2-3 天)

**目標**: 共享模塊職責清晰化

1. **Day 1**: 規劃與設計
   - 確定最終目錄結構
   - 制定遷移策略

2. **Day 2**: 執行遷移
   - 移動文件
   - 更新 import 路徑
   - 添加 deprecation 警告

3. **Day 3**: 測試與驗證
   - 完整測試套件
   - 檢查所有 import

---

## 🎯 總結

### 優先行動建議

**立即執行** (P0):
1. ✅ 執行器重構 - 減少 38% 重複代碼

**近期執行** (P1):
2. ✅ 驗證邏輯重組 - 職責清晰化
3. ✅ 配置統一 - Stage 6 配置文件化

**長期改進** (P2):
4. ⚠️ 接口統一 - 需要充分測試
5. ⚠️ 模塊重組 - 影響範圍廣，謹慎執行

### 不建議優化的部分

❌ **處理器核心算法邏輯**: 已達 Grade A 學術標準，不應為了架構統一而修改
❌ **驗證標準**: 當前驗證邏輯嚴格且全面，不應簡化
❌ **數據流設計**: 六階段管道架構清晰，不需要大改

### 最終建議

當前架構整體**健康且成熟**，建議採用**漸進式優化**策略：
1. 先執行 P0 級優化（執行器重構）
2. 根據實際效果決定是否繼續 P1/P2 級優化
3. 避免為了架構完美而引入不必要的複雜性

---

**報告結束**
**作者**: Claude Code
**審閱建議**: 與團隊討論後再執行 Phase 1
