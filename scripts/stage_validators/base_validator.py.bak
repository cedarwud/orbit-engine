"""
驗證器基類 - Template Method Pattern

提供統一的驗證流程和工具方法，消除驗證器之間的重複代碼。

設計模式: Template Method Pattern
- 定義標準驗證流程框架
- 子類只需實現專用驗證邏輯
- 提供 Fail-Fast 工具方法

Author: Orbit Engine Refactoring Team
Date: 2025-10-12
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import os


class StageValidator(ABC):
    """
    驗證器基類 - 使用 Template Method Pattern 統一驗證流程

    標準驗證流程:
    1. 基礎結構驗證 (stage 標識, metadata, data_summary)
    2. 驗證結果框架檢查 (5 項驗證框架，如果適用)
    3. 專用驗證 (子類實現)

    使用範例:
    ```python
    class Stage1Validator(StageValidator):
        def __init__(self):
            super().__init__(
                stage_number=1,
                stage_identifier='stage1_orbital_calculation'
            )

        def perform_stage_specific_validation(self, snapshot_data: dict) -> tuple:
            # 只需實現專用驗證邏輯
            data_summary = snapshot_data['data_summary']
            satellites_loaded = data_summary.get('satellites_loaded', 0)

            if satellites_loaded == 0:
                return False, "❌ Stage 1 未載入任何衛星"

            return True, f"✅ Stage 1 驗證通過: 載入 {satellites_loaded} 顆衛星"

    # 使用
    validator = Stage1Validator()
    passed, message = validator.validate(snapshot_data)
    ```
    """

    def __init__(self, stage_number: int, stage_identifier: str):
        """
        初始化驗證器

        Args:
            stage_number: 階段編號 (1-6)
            stage_identifier: 階段標識符 (如 'stage1_orbital_calculation')
        """
        self.stage_number = stage_number
        self.stage_identifier = stage_identifier

    # ============================================================
    # Template Method (主流程)
    # ============================================================

    def validate(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        模板方法: 定義標準驗證流程

        驗證步驟:
        1. 基礎結構驗證 (所有驗證器共同)
        2. 驗證結果框架檢查 (大部分驗證器)
        3. 專用驗證 (子類實現)

        Args:
            snapshot_data: 驗證快照數據

        Returns:
            tuple: (validation_passed: bool, message: str)
        """
        try:
            # Step 1: 基礎結構驗證
            is_valid, error_msg = self._validate_basic_structure(snapshot_data)
            if not is_valid:
                return False, error_msg

            # Step 2: 驗證結果框架檢查 (如果適用)
            if self.uses_validation_framework():
                framework_result = self._validate_validation_framework(snapshot_data)
                if framework_result is not None:
                    # 框架驗證完成 (成功或失敗)
                    return framework_result

            # Step 3: 專用驗證 (子類實現)
            return self.perform_stage_specific_validation(snapshot_data)

        except KeyError as e:
            # 捕獲字段訪問錯誤
            return False, f"❌ Stage {self.stage_number} 驗證數據結構錯誤: 缺少必需字段 {e}"
        except Exception as e:
            # 捕獲其他未預期的錯誤
            return False, f"❌ Stage {self.stage_number} 驗證異常: {type(e).__name__}: {e}"

    # ============================================================
    # 基礎驗證方法 (所有驗證器共同)
    # ============================================================

    def _validate_basic_structure(self, snapshot_data: dict) -> Tuple[bool, Optional[str]]:
        """
        驗證基礎結構

        檢查項目:
        - snapshot_data 類型
        - stage 標識
        - metadata 字段
        - data_summary 字段 (可選)

        Args:
            snapshot_data: 驗證快照數據

        Returns:
            tuple: (is_valid: bool, error_message: str | None)
        """
        # 檢查類型
        if not isinstance(snapshot_data, dict):
            return False, f"❌ 快照數據類型錯誤: {type(snapshot_data).__name__} (期望: dict)"

        # 檢查 stage 標識
        if 'stage' not in snapshot_data:
            return False, f"❌ 快照數據缺少 'stage' 字段"

        if snapshot_data['stage'] != self.stage_identifier:
            return False, f"❌ Stage {self.stage_number} 快照標識不正確: {snapshot_data['stage']} (期望: {self.stage_identifier})"

        # 檢查 metadata (大部分驗證器需要)
        if 'metadata' not in snapshot_data:
            # 某些驗證器可能不需要 metadata，子類可覆蓋此方法
            if self.requires_metadata():
                return False, f"❌ 快照數據缺少 'metadata' 字段"

        # 檢查 data_summary (大部分驗證器需要)
        if 'data_summary' not in snapshot_data:
            if self.requires_data_summary():
                return False, f"❌ 快照數據缺少 'data_summary' 字段"

        return True, None

    def _validate_validation_framework(self, snapshot_data: dict) -> Optional[Tuple[bool, str]]:
        """
        驗證 5 項驗證框架 (如果存在)

        檢查項目:
        - validation_results 存在性
        - overall_status
        - checks_passed / checks_performed
        - 通過率檢查 (基於取樣模式)

        Args:
            snapshot_data: 驗證快照數據

        Returns:
            tuple | None:
                - (True, message) 如果驗證通過
                - (False, message) 如果驗證失敗
                - None 如果需要進一步檢查 (舊格式或未完成)
        """
        # 檢查 validation_results 存在性
        if 'validation_results' not in snapshot_data:
            # 舊格式快照，跳過框架檢查
            return None

        validation_results = snapshot_data['validation_results']

        # 獲取 checks_passed / checks_performed (支持新舊格式)
        validation_details = validation_results.get('validation_details', {})

        # 新格式: 在 validation_details 中
        checks_passed = validation_details.get('checks_passed',
                                              # 舊格式: 直接在 validation_results 中
                                              validation_results.get('checks_passed', 0))
        checks_performed = validation_details.get('checks_performed',
                                                 validation_results.get('checks_performed', 0))

        # 檢查執行完整性
        expected_checks = self.get_expected_validation_checks()
        if checks_performed < expected_checks:
            return False, f"❌ Stage {self.stage_number} 驗證不完整: 只執行了{checks_performed}/{expected_checks}項檢查"

        # 檢查通過率 (基於取樣模式)
        min_required = self._get_min_required_checks(snapshot_data)
        if checks_passed < min_required:
            return False, f"❌ Stage {self.stage_number} 驗證未達標: 只通過了{checks_passed}/{expected_checks}項檢查 (需要至少{min_required}項)"

        # 檢查 overall_status
        overall_status = validation_results.get('overall_status', 'UNKNOWN')

        # 取樣模式: 放寬標準
        is_sampling = self._is_sampling_mode(snapshot_data)
        if is_sampling and checks_passed >= min_required:
            # 取樣模式下，達到最低要求即可通過
            return self._build_success_message(snapshot_data, validation_results)

        if overall_status == 'PASS':
            return self._build_success_message(snapshot_data, validation_results)

        # 需要進一步檢查
        return None

    # ============================================================
    # 取樣模式處理
    # ============================================================

    def _is_sampling_mode(self, snapshot_data: dict) -> bool:
        """
        檢測是否為取樣模式

        默認實現: 檢查環境變數 ORBIT_ENGINE_TEST_MODE
        子類可覆蓋此方法添加特定邏輯 (如基於衛星數量判斷)

        Args:
            snapshot_data: 驗證快照數據

        Returns:
            bool: True 如果為取樣模式
        """
        return os.getenv('ORBIT_ENGINE_TEST_MODE') == '1'

    def _get_min_required_checks(self, snapshot_data: dict) -> int:
        """
        獲取最低通過檢查數

        根據取樣模式調整標準:
        - 正常模式: 4/5 項通過
        - 取樣模式: 1/5 項通過

        Args:
            snapshot_data: 驗證快照數據

        Returns:
            int: 最低通過檢查數
        """
        if self._is_sampling_mode(snapshot_data):
            return 1  # 取樣模式: 1/5
        else:
            return 4  # 正常模式: 4/5

    # ============================================================
    # Fail-Fast 工具方法
    # ============================================================

    def check_field_exists(self, data: dict, field: str, parent: str = '') -> Tuple[bool, Optional[str]]:
        """
        檢查字段是否存在 (Fail-Fast 模式)

        Args:
            data: 數據字典
            field: 字段名稱
            parent: 父字段路徑 (用於錯誤訊息)

        Returns:
            tuple: (exists: bool, error_message: str | None)

        Example:
            ```python
            exists, msg = self.check_field_exists(metadata, 'total_satellites', 'metadata')
            if not exists:
                return False, msg
            ```
        """
        if field not in data:
            parent_str = f"{parent}." if parent else ""
            return False, f"❌ {parent_str}{field} 字段不存在"
        return True, None

    def check_field_type(self, value: Any, expected_type: type, field_name: str) -> Tuple[bool, Optional[str]]:
        """
        檢查字段類型 (Fail-Fast 模式)

        Args:
            value: 字段值
            expected_type: 期望類型 (或類型元組)
            field_name: 字段名稱

        Returns:
            tuple: (is_valid: bool, error_message: str | None)

        Example:
            ```python
            valid, msg = self.check_field_type(satellites_count, int, 'satellites_count')
            if not valid:
                return False, msg
            ```
        """
        if not isinstance(value, expected_type):
            if isinstance(expected_type, tuple):
                expected_str = ' | '.join(t.__name__ for t in expected_type)
            else:
                expected_str = expected_type.__name__

            return False, f"❌ {field_name} 類型錯誤: {type(value).__name__} (期望: {expected_str})"
        return True, None

    def check_field_range(self, value: float, min_val: float, max_val: float,
                         field_name: str, unit: str = '') -> Tuple[bool, Optional[str]]:
        """
        檢查字段範圍 (Fail-Fast 模式)

        Args:
            value: 字段值
            min_val: 最小值
            max_val: 最大值
            field_name: 字段名稱
            unit: 單位 (用於錯誤訊息)

        Returns:
            tuple: (is_valid: bool, error_message: str | None)

        Example:
            ```python
            valid, msg = self.check_field_range(rsrp, -140, -20, 'RSRP', 'dBm')
            if not valid:
                return False, msg
            ```
        """
        if value < min_val or value > max_val:
            unit_str = f" {unit}" if unit else ""
            return False, (
                f"❌ {field_name} 值超出範圍: {value}{unit_str} "
                f"(範圍: {min_val}-{max_val}{unit_str})"
            )
        return True, None

    # ============================================================
    # 抽象方法 (子類必須實現)
    # ============================================================

    @abstractmethod
    def perform_stage_specific_validation(self, snapshot_data: dict) -> Tuple[bool, str]:
        """
        執行階段特定的驗證邏輯

        這是唯一需要子類實現的方法！
        基礎檢查（stage 標識、metadata、data_summary）已由基類完成。

        Args:
            snapshot_data: 驗證快照數據

        Returns:
            tuple: (validation_passed: bool, message: str)

        Example:
            ```python
            def perform_stage_specific_validation(self, snapshot_data: dict) -> tuple:
                data_summary = snapshot_data['data_summary']
                satellites_loaded = data_summary.get('satellites_loaded', 0)

                if satellites_loaded == 0:
                    return False, "❌ Stage 1 未載入任何衛星"

                return True, f"✅ Stage 1 驗證通過: 載入 {satellites_loaded} 顆衛星"
            ```
        """
        pass

    # ============================================================
    # 可覆蓋的配置方法 (子類可選擇性覆蓋)
    # ============================================================

    def uses_validation_framework(self) -> bool:
        """
        是否使用 5 項驗證框架

        默認: True (大部分驗證器使用)

        子類可覆蓋此方法返回 False (如 Stage 4, 5 使用 Fail-Fast 驗證)

        Returns:
            bool: True 如果使用驗證框架
        """
        return True

    def get_expected_validation_checks(self) -> int:
        """
        期望的驗證檢查數量

        默認: 5 項

        Returns:
            int: 期望的驗證檢查數量
        """
        return 5

    def requires_metadata(self) -> bool:
        """
        是否需要 metadata 字段

        默認: True (大部分驗證器需要)

        Returns:
            bool: True 如果需要 metadata
        """
        return True

    def requires_data_summary(self) -> bool:
        """
        是否需要 data_summary 字段

        默認: True (所有驗證器需要)

        Returns:
            bool: True 如果需要 data_summary
        """
        return True

    def _build_success_message(self, snapshot_data: dict, validation_results: dict) -> Tuple[bool, str]:
        """
        構建成功訊息

        默認實現: 基本訊息
        子類可覆蓋此方法自定義訊息格式

        Args:
            snapshot_data: 驗證快照數據
            validation_results: 驗證結果數據

        Returns:
            tuple: (True, success_message)
        """
        # 獲取 checks_passed / checks_performed (支持新舊格式)
        validation_details = validation_results.get('validation_details', {})
        checks_passed = validation_details.get('checks_passed',
                                              validation_results.get('checks_passed', 0))
        checks_performed = validation_details.get('checks_performed',
                                                 validation_results.get('checks_performed', 0))

        # 取樣模式標記
        mode_indicator = "🧪 取樣模式" if self._is_sampling_mode(snapshot_data) else ""

        message = (
            f"✅ Stage {self.stage_number} 驗證通過 {mode_indicator}: "
            f"驗證框架 {checks_passed}/{checks_performed} 項通過"
        )

        return True, message
