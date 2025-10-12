# Phase 1: 基類執行器實現

**文件**: `scripts/stage_executors/base_executor.py`
**預估行數**: ~180 行
**複雜度**: 🟡 中等

---

## 📋 完整實現代碼

```python
"""
階段執行器基類

提供統一的執行流程，減少重複代碼。
子類只需實現配置加載和處理器創建邏輯。

Author: Orbit Engine Refactoring Team
Date: 2025-10-12
Version: 1.0
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import json
import logging

# 導入工具函數
from .executor_utils import (
    clean_stage_outputs,
    find_latest_stage_output,
    project_root
)

# 導入處理結果類型
from src.shared.interfaces import ProcessingStatus


class StageExecutor(ABC):
    """
    階段執行器基類 - 統一執行流程

    使用 Template Method Pattern，定義標準執行流程：
    1. 顯示階段頭部
    2. 清理舊輸出
    3. 載入前階段數據（如需要）
    4. 載入配置（子類實現）
    5. 創建處理器（子類實現）
    6. 執行處理
    7. 保存驗證快照
    8. 錯誤處理

    子類只需實現:
    - load_config(): 載入階段配置
    - create_processor(): 創建處理器實例
    - requires_previous_stage(): 是否需要前階段數據（可選）
    """

    def __init__(self, stage_number: int, stage_name: str, emoji: str = "📦"):
        """
        初始化執行器

        Args:
            stage_number: 階段編號 (1-6)
            stage_name: 階段名稱（中文）
            emoji: 階段圖標（可選，默認 📦）
        """
        self.stage_number = stage_number
        self.stage_name = stage_name
        self.emoji = emoji
        self.logger = logging.getLogger(f"stage{stage_number}_executor")

    def execute(self, previous_results: Optional[Dict] = None) -> Tuple[bool, Any, Any]:
        """
        執行階段處理（模板方法）

        這是核心執行流程，子類不應覆蓋此方法。
        子類應實現 load_config() 和 create_processor()。

        Args:
            previous_results: 前序階段結果字典（可選）

        Returns:
            tuple: (success: bool, result: ProcessingResult, processor: Processor)
                - success: 是否執行成功
                - result: 處理結果對象（或 None）
                - processor: 處理器實例（或 None）
        """
        try:
            # Step 1: 顯示階段頭部
            self._print_stage_header()

            # Step 2: 清理舊輸出
            clean_stage_outputs(self.stage_number)

            # Step 3: 載入前階段數據（如需要）
            input_data = None
            if self.requires_previous_stage():
                input_data = self._load_previous_stage_data()
                if input_data is None:
                    # 前階段數據缺失，無法繼續
                    return False, None, None

            # Step 4: 載入配置（子類實現）
            config = self.load_config()

            # Step 5: 顯示配置摘要（可選）
            self._print_config_summary(config)

            # Step 6: 創建處理器（子類實現）
            processor = self.create_processor(config)

            # Step 7: 執行處理（統一接口）
            result = processor.execute(input_data)

            # Step 8: 檢查結果
            if not self._check_result(result):
                return False, result, processor

            # Step 9: 顯示處理結果摘要
            self._print_result_summary(result)

            # Step 10: 保存驗證快照（如果處理器支持）
            self._save_validation_snapshot(processor, result)

            return True, result, processor

        except Exception as e:
            # 統一錯誤處理
            error_msg = f'❌ Stage {self.stage_number} 執行異常: {e}'
            self.logger.error(error_msg, exc_info=True)
            print(error_msg)
            return False, None, None

    # ===== 子類必須實現的抽象方法 =====

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """
        載入階段配置

        子類必須實現此方法，從 YAML 文件或其他來源載入配置。

        Returns:
            Dict[str, Any]: 配置字典

        Example:
            ```python
            def load_config(self) -> Dict[str, Any]:
                config_path = project_root / "config/stage1_orbital_calculation.yaml"
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            ```
        """
        pass

    @abstractmethod
    def create_processor(self, config: Dict[str, Any]) -> Any:
        """
        創建處理器實例

        子類必須實現此方法，根據配置創建對應的處理器。

        Args:
            config: load_config() 返回的配置字典

        Returns:
            處理器實例（繼承自 BaseStageProcessor）

        Example:
            ```python
            def create_processor(self, config):
                from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor
                return create_stage1_processor(config)
            ```
        """
        pass

    # ===== 子類可覆蓋的可選方法 =====

    def requires_previous_stage(self) -> bool:
        """
        是否需要前階段數據

        默認行為：Stage 1 不需要，其他階段需要。
        子類可以覆蓋此方法自定義行為。

        Returns:
            bool: True 如果需要前階段數據
        """
        return self.stage_number > 1

    def get_previous_stage_number(self) -> int:
        """
        獲取前階段編號

        默認行為：當前階段 - 1
        子類可以覆蓋此方法（例如跳階段執行）。

        Returns:
            int: 前階段編號
        """
        return self.stage_number - 1

    # ===== 內部輔助方法（基類實現，子類不應覆蓋） =====

    def _print_stage_header(self):
        """顯示階段頭部信息"""
        print(f'\n{self.emoji} 階段{self.stage_number}：{self.stage_name}')
        print('-' * 60)

    def _load_previous_stage_data(self) -> Optional[Dict]:
        """
        載入前階段數據

        Returns:
            Optional[Dict]: 前階段數據，如果找不到則返回 None
        """
        previous_stage = self.get_previous_stage_number()
        output_file = find_latest_stage_output(previous_stage)

        if not output_file:
            error_msg = f'❌ 找不到 Stage {previous_stage} 輸出文件，請先執行 Stage {previous_stage}'
            self.logger.error(error_msg)
            print(error_msg)
            return None

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"✅ 已載入 Stage {previous_stage} 數據: {output_file}")
            return data
        except Exception as e:
            error_msg = f'❌ 載入 Stage {previous_stage} 數據失敗: {e}'
            self.logger.error(error_msg)
            print(error_msg)
            return None

    def _check_result(self, result) -> bool:
        """
        檢查處理結果

        Args:
            result: 處理器返回的結果

        Returns:
            bool: True 如果結果有效
        """
        if not result:
            error_msg = f'❌ Stage {self.stage_number} 無返回結果'
            self.logger.error(error_msg)
            print(error_msg)
            return False

        # 檢查狀態
        if hasattr(result, 'status'):
            if result.status != ProcessingStatus.SUCCESS:
                errors = '; '.join(result.errors) if hasattr(result, 'errors') and result.errors else "未知錯誤"
                error_msg = f'❌ Stage {self.stage_number} 執行失敗: {errors}'
                self.logger.error(error_msg)
                print(error_msg)
                return False

        # 檢查數據
        if hasattr(result, 'data') and not result.data:
            error_msg = f'❌ Stage {self.stage_number} 返回數據為空'
            self.logger.error(error_msg)
            print(error_msg)
            return False

        return True

    def _save_validation_snapshot(self, processor, result):
        """
        保存驗證快照

        Args:
            processor: 處理器實例
            result: 處理結果
        """
        if not hasattr(processor, 'save_validation_snapshot'):
            # 處理器不支持快照保存，跳過
            return

        try:
            # 提取數據（處理 ProcessingResult 對象）
            data = result.data if hasattr(result, 'data') else result

            # 調用處理器的快照保存方法
            snapshot_saved = processor.save_validation_snapshot(data)

            if snapshot_saved:
                self.logger.info(f'✅ Stage {self.stage_number} 驗證快照已保存')
                print(f'✅ Stage {self.stage_number} 驗證快照已保存')
            else:
                self.logger.warning(f'⚠️ Stage {self.stage_number} 驗證快照保存失敗')
                print(f'⚠️ Stage {self.stage_number} 驗證快照保存失敗')

        except Exception as e:
            # 快照保存失敗不應中斷主流程，只記錄警告
            warning_msg = f'⚠️ Stage {self.stage_number} 驗證快照保存失敗: {e}'
            self.logger.warning(warning_msg)
            print(warning_msg)

    def _print_config_summary(self, config: Dict[str, Any]):
        """
        顯示配置摘要（可選，由子類決定是否調用）

        Args:
            config: 配置字典
        """
        # 基類不顯示，子類可以覆蓋此方法添加自定義摘要
        pass

    def _print_result_summary(self, result):
        """
        顯示處理結果摘要

        Args:
            result: 處理結果
        """
        if not hasattr(result, 'data') or not hasattr(result, 'metrics'):
            return

        data = result.data
        metrics = result.metrics

        # 顯示通用統計信息
        print(f'📊 處理狀態: {result.status.value if hasattr(result, "status") else "未知"}')

        if hasattr(metrics, 'duration_seconds'):
            print(f'📊 處理時間: {metrics.duration_seconds:.3f}秒')

        # 顯示階段特定的統計（如果有）
        if isinstance(data, dict):
            # Stage 1: 衛星數量
            if 'satellites' in data:
                print(f'📊 處理衛星: {len(data["satellites"])}顆')

            # Stage 2: 時間序列長度
            if 'metadata' in data and 'time_series_length' in data['metadata']:
                print(f'📊 時間序列: {data["metadata"]["time_series_length"]}點')

            # Stage 4: 可見衛星數量
            if 'link_feasibility' in data:
                print(f'📊 可見衛星: {len(data["link_feasibility"])}顆')

            # Stage 5: 信號分析衛星數量
            if 'signal_analysis' in data:
                print(f'📊 分析衛星: {len(data["signal_analysis"])}顆')

            # Stage 6: 事件數量
            if 'handover_events' in data:
                print(f'📊 換手事件: {len(data["handover_events"])}個')


# ===== 便捷函數（向後兼容） =====

def create_stage_executor(stage_number: int, executor_class) -> StageExecutor:
    """
    創建階段執行器的工廠函數

    Args:
        stage_number: 階段編號
        executor_class: 執行器類

    Returns:
        StageExecutor: 執行器實例
    """
    return executor_class()
```

---

## 🧪 單元測試實現

創建 `tests/unit/refactoring/test_base_executor.py`:

```python
"""
base_executor.py 單元測試

測試基類執行器的核心功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from scripts.stage_executors.base_executor import StageExecutor
from src.shared.interfaces import ProcessingStatus, ProcessingResult


# ===== 測試用具體執行器 =====

class TestExecutor(StageExecutor):
    """測試用執行器"""

    def __init__(self, stage_number=1, stage_name="測試階段"):
        super().__init__(stage_number, stage_name)
        self.config_loaded = False
        self.processor_created = False

    def load_config(self):
        self.config_loaded = True
        return {'test_config': True}

    def create_processor(self, config):
        self.processor_created = True
        # 返回 Mock 處理器
        processor = Mock()
        processor.execute = Mock(return_value=self._create_success_result())
        processor.save_validation_snapshot = Mock(return_value=True)
        return processor

    def _create_success_result(self):
        result = Mock(spec=ProcessingResult)
        result.status = ProcessingStatus.SUCCESS
        result.data = {'satellites': [1, 2, 3]}
        result.errors = []
        result.metrics = Mock(duration_seconds=1.5)
        return result


# ===== 測試用例 =====

class TestStageExecutorBasic:
    """基本功能測試"""

    def test_executor_initialization(self):
        """測試執行器初始化"""
        executor = TestExecutor(stage_number=1, stage_name="測試階段")

        assert executor.stage_number == 1
        assert executor.stage_name == "測試階段"
        assert executor.emoji == "📦"

    def test_requires_previous_stage(self):
        """測試前階段依賴判斷"""
        # Stage 1 不需要前階段
        executor1 = TestExecutor(stage_number=1)
        assert executor1.requires_previous_stage() is False

        # Stage 2+ 需要前階段
        executor2 = TestExecutor(stage_number=2)
        assert executor2.requires_previous_stage() is True

    def test_get_previous_stage_number(self):
        """測試前階段編號獲取"""
        executor = TestExecutor(stage_number=3)
        assert executor.get_previous_stage_number() == 2


class TestStageExecutorExecution:
    """執行流程測試"""

    @patch('scripts.stage_executors.base_executor.clean_stage_outputs')
    def test_execute_stage1_no_previous_data(self, mock_clean):
        """測試 Stage 1 執行（無前階段數據）"""
        executor = TestExecutor(stage_number=1)

        success, result, processor = executor.execute()

        # 驗證執行成功
        assert success is True
        assert result is not None
        assert processor is not None

        # 驗證調用順序
        assert executor.config_loaded is True
        assert executor.processor_created is True
        mock_clean.assert_called_once_with(1)

    @patch('scripts.stage_executors.base_executor.clean_stage_outputs')
    @patch('scripts.stage_executors.base_executor.find_latest_stage_output')
    def test_execute_stage2_with_previous_data(self, mock_find, mock_clean):
        """測試 Stage 2 執行（有前階段數據）"""
        # Mock 前階段輸出文件
        mock_output_file = Path('/tmp/stage1_output.json')
        mock_find.return_value = mock_output_file

        # Mock 文件讀取
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = '{"satellites": []}'
            mock_open.return_value = mock_file

            with patch('json.load', return_value={'satellites': []}):
                executor = TestExecutor(stage_number=2)
                success, result, processor = executor.execute()

                # 驗證執行成功
                assert success is True
                assert result is not None

                # 驗證調用前階段數據載入
                mock_find.assert_called_once_with(1)

    @patch('scripts.stage_executors.base_executor.find_latest_stage_output')
    @patch('scripts.stage_executors.base_executor.clean_stage_outputs')
    def test_execute_fails_when_previous_data_missing(self, mock_clean, mock_find):
        """測試前階段數據缺失時執行失敗"""
        # Mock 找不到前階段輸出
        mock_find.return_value = None

        executor = TestExecutor(stage_number=2)
        success, result, processor = executor.execute()

        # 驗證執行失敗
        assert success is False
        assert result is None
        assert processor is None


class TestStageExecutorResultChecking:
    """結果檢查測試"""

    def test_check_result_success(self):
        """測試成功結果檢查"""
        executor = TestExecutor()

        result = Mock(spec=ProcessingResult)
        result.status = ProcessingStatus.SUCCESS
        result.data = {'satellites': []}

        assert executor._check_result(result) is True

    def test_check_result_fails_with_no_result(self):
        """測試無結果時檢查失敗"""
        executor = TestExecutor()
        assert executor._check_result(None) is False

    def test_check_result_fails_with_failed_status(self):
        """測試失敗狀態時檢查失敗"""
        executor = TestExecutor()

        result = Mock(spec=ProcessingResult)
        result.status = ProcessingStatus.FAILED
        result.errors = ["Error 1", "Error 2"]

        assert executor._check_result(result) is False

    def test_check_result_fails_with_empty_data(self):
        """測試空數據時檢查失敗"""
        executor = TestExecutor()

        result = Mock(spec=ProcessingResult)
        result.status = ProcessingStatus.SUCCESS
        result.data = None

        assert executor._check_result(result) is False


class TestStageExecutorErrorHandling:
    """錯誤處理測試"""

    @patch('scripts.stage_executors.base_executor.clean_stage_outputs')
    def test_execute_handles_exception(self, mock_clean):
        """測試異常處理"""
        executor = TestExecutor()

        # 讓 load_config 拋出異常
        def raise_exception():
            raise ValueError("配置載入失敗")

        executor.load_config = raise_exception

        success, result, processor = executor.execute()

        # 驗證執行失敗但不崩潰
        assert success is False
        assert result is None
        assert processor is None


class TestStageExecutorValidationSnapshot:
    """驗證快照測試"""

    @patch('scripts.stage_executors.base_executor.clean_stage_outputs')
    def test_save_validation_snapshot_success(self, mock_clean):
        """測試驗證快照保存成功"""
        executor = TestExecutor()

        success, result, processor = executor.execute()

        # 驗證快照保存被調用
        assert success is True
        processor.save_validation_snapshot.assert_called_once()

    @patch('scripts.stage_executors.base_executor.clean_stage_outputs')
    def test_save_validation_snapshot_not_supported(self, mock_clean):
        """測試處理器不支持快照保存"""
        executor = TestExecutor()

        # 創建不支持快照的處理器
        def create_processor_no_snapshot(config):
            processor = Mock()
            processor.execute = Mock(return_value=executor._create_success_result())
            # 不添加 save_validation_snapshot 方法
            return processor

        executor.create_processor = create_processor_no_snapshot

        success, result, processor = executor.execute()

        # 驗證執行成功（快照保存失敗不影響主流程）
        assert success is True
```

---

## 📝 使用範例

### 基本使用

```python
# 創建執行器實例
from scripts.stage_executors.stage1_executor import Stage1Executor

executor = Stage1Executor()
success, result, processor = executor.execute()

if success:
    print("執行成功")
else:
    print("執行失敗")
```

### 自定義執行器

```python
class CustomExecutor(StageExecutor):
    """自定義執行器範例"""

    def __init__(self):
        super().__init__(
            stage_number=7,
            stage_name="自定義階段",
            emoji="🎯"
        )

    def load_config(self):
        # 自定義配置加載邏輯
        return {
            'custom_param': True,
            'threshold': 0.5
        }

    def create_processor(self, config):
        # 自定義處理器創建邏輯
        from custom.processors import CustomProcessor
        return CustomProcessor(config)

    def requires_previous_stage(self):
        # 自定義依賴邏輯（例如可選前階段）
        return False  # 不依賴前階段
```

---

## ✅ 實施檢查清單

- [ ] 創建 `scripts/stage_executors/base_executor.py`
- [ ] 複製完整實現代碼
- [ ] 創建 `tests/unit/refactoring/test_base_executor.py`
- [ ] 複製完整測試代碼
- [ ] 運行單元測試
  ```bash
  pytest tests/unit/refactoring/test_base_executor.py -v
  ```
- [ ] 確認所有測試通過
- [ ] 檢查代碼覆蓋率 (≥ 85%)
  ```bash
  pytest tests/unit/refactoring/test_base_executor.py --cov=scripts.stage_executors.base_executor
  ```
- [ ] 提交 git commit
  ```bash
  git add scripts/stage_executors/base_executor.py
  git add tests/unit/refactoring/test_base_executor.py
  git commit -m "refactor(phase1): implement base executor with template method pattern"
  ```

---

**下一步**: [03_stage_executors_migration.md](03_stage_executors_migration.md) - 執行器遷移
