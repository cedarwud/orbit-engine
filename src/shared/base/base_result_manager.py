"""
📊 Base Result Manager - Template Method Pattern for Result/Snapshot Management

Universal base class for all stage result and validation snapshot managers.
Eliminates code duplication across 6 stages using Template Method Pattern.

Author: Orbit Engine Refactoring Team
Date: 2025-10-12 (Phase 3 Refactoring)

Design Philosophy:
-----------------
1. **Template Methods**: Common workflow implemented in base class
2. **Abstract Methods**: Stage-specific logic implemented in subclasses
3. **Fail-Fast Helpers**: Grade A+ validation helpers
4. **Backward Compatibility**: All existing manager interfaces preserved
5. **Extension Points**: Subclasses can extend with stage-specific features (e.g., HDF5 caching)

Usage Example:
--------------
```python
class Stage5ResultManager(BaseResultManager):
    def get_stage_number(self) -> int:
        return 5

    def get_stage_identifier(self) -> str:
        return 'stage5_signal_analysis'

    def build_stage_results(self, **kwargs) -> Dict[str, Any]:
        # Stage 5 specific result building
        return {...}

    def build_snapshot_data(self, processing_results, processing_stats) -> Dict[str, Any]:
        # Stage 5 specific snapshot data
        return {...}
```
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


class BaseResultManager(ABC):
    """
    Base class for stage result and validation snapshot managers.

    Uses Template Method Pattern to standardize result/snapshot management
    while allowing stage-specific customization through abstract methods.

    Template Methods (implemented here):
    ------------------------------------
    - save_results(): Standard result saving workflow
    - save_validation_snapshot(): Standard snapshot creation workflow

    Helper Methods (common utilities):
    -----------------------------------
    - _merge_upstream_metadata(): Merge upstream + current stage metadata
    - _create_output_directory(): Create and return output directory
    - _create_validation_directory(): Create and return validation directory
    - _generate_timestamp(): Generate UTC timestamp string
    - _save_json(): Save data as JSON file
    - _check_required_field(): Fail-Fast field validation
    - _check_required_fields(): Batch Fail-Fast validation

    Abstract Methods (subclass must implement):
    -------------------------------------------
    - get_stage_number(): Return stage number (1-6)
    - get_stage_identifier(): Return stage identifier (e.g., 'stage2_orbital_computing')
    - build_stage_results(**kwargs): Build stage-specific result structure
    - build_snapshot_data(processing_results, processing_stats): Build snapshot data
    """

    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """
        Initialize base result manager

        Args:
            logger_instance: Optional logger instance (defaults to module logger)
        """
        self.logger = logger_instance or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    # ==================== Abstract Methods (Subclass Implementation Required) ====================

    @abstractmethod
    def get_stage_number(self) -> int:
        """
        Return stage number (1-6)

        Returns:
            Stage number

        Example:
            return 5
        """
        pass

    @abstractmethod
    def get_stage_identifier(self) -> str:
        """
        Return stage identifier string

        Returns:
            Stage identifier (e.g., 'stage2_orbital_computing', 'stage5_signal_analysis')

        Example:
            return 'stage5_signal_analysis'
        """
        pass

    @abstractmethod
    def build_stage_results(self, **kwargs) -> Dict[str, Any]:
        """
        Build stage-specific result structure

        This method should construct the complete output data structure
        for the current stage, including all required fields.

        Args:
            **kwargs: Stage-specific arguments

        Returns:
            Complete result dictionary

        Example (Stage 5):
            return {
                'stage': 5,
                'stage_name': 'signal_quality_analysis',
                'signal_analysis': analyzed_satellites,
                'metadata': metadata
            }
        """
        pass

    @abstractmethod
    def build_snapshot_data(
        self,
        processing_results: Dict[str, Any],
        processing_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build stage-specific validation snapshot data

        This method should construct the validation snapshot structure
        for the current stage. The base class will add common fields
        (stage, timestamp, validation_passed, etc.).

        Args:
            processing_results: Full processing results from stage
            processing_stats: Processing statistics dictionary

        Returns:
            Stage-specific snapshot data (will be merged with common fields)

        Example (Stage 5):
            return {
                'metadata': {...},
                'data_summary': {
                    'total_satellites_analyzed': 50,
                    'usable_satellites': 45
                },
                'validation_status': 'passed'
            }
        """
        pass

    # ==================== Template Methods (Common Workflow) ====================

    def save_results(
        self,
        results: Dict[str, Any],
        output_format: str = 'json',
        custom_filename: Optional[str] = None
    ) -> str:
        """
        Template method: Save stage results to file

        Standard workflow:
        1. Create output directory
        2. Generate timestamp (unless custom filename provided)
        3. Build output file path
        4. Save results as JSON
        5. Log success message

        Args:
            results: Complete result dictionary (from build_stage_results())
            output_format: Output format ('json' or 'both') - HDF5 handled by subclasses
            custom_filename: Optional custom filename (without extension)

        Returns:
            Output file path

        Raises:
            IOError: If saving fails

        Note:
            Subclasses can override this method to add HDF5 support or other formats.
            See Stage2ResultManager and Stage3ResultsManager for examples.
        """
        try:
            # Step 1: Create output directory
            output_dir = self._create_output_directory(self.get_stage_number())

            # Step 2: Generate filename
            if custom_filename:
                filename = f"{custom_filename}.json"
            else:
                timestamp = self._generate_timestamp()
                stage_id = self.get_stage_identifier()
                filename = f"{stage_id}_output_{timestamp}.json"

            # Step 3: Build output file path
            output_file = output_dir / filename

            # Step 4: Save as JSON
            self._save_json(results, output_file)

            # Step 5: Log success
            stage_num = self.get_stage_number()
            self.logger.info(f"📁 Stage {stage_num} 結果已保存: {output_file}")

            return str(output_file)

        except Exception as e:
            stage_num = self.get_stage_number()
            self.logger.error(f"❌ 保存 Stage {stage_num} 結果失敗: {e}")
            raise IOError(f"無法保存 Stage {stage_num} 結果: {e}")

    def save_validation_snapshot(
        self,
        processing_results: Dict[str, Any],
        processing_stats: Dict[str, Any]
    ) -> bool:
        """
        Template method: Save validation snapshot

        Standard workflow:
        1. Create validation directory
        2. Build stage-specific snapshot data (abstract method)
        3. Add common snapshot fields (stage, timestamp, validation_passed)
        4. Save snapshot as JSON
        5. Log result

        Args:
            processing_results: Full processing results from stage
            processing_stats: Processing statistics dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Create validation directory
            validation_dir = self._create_validation_directory()

            # Step 2: Build stage-specific snapshot data
            stage_snapshot_data = self.build_snapshot_data(
                processing_results,
                processing_stats
            )

            # Step 3: Add common snapshot fields
            stage_num = self.get_stage_number()
            stage_id = self.get_stage_identifier()

            snapshot_data = {
                'stage': stage_id,
                'stage_number': stage_num,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                **stage_snapshot_data  # Merge stage-specific fields
            }

            # Ensure validation_passed field exists (required by validators)
            if 'validation_passed' not in snapshot_data:
                # Default: Check if validation_status is 'passed'
                validation_status = snapshot_data.get('validation_status', 'unknown')
                snapshot_data['validation_passed'] = (validation_status == 'passed')

            # Step 4: Save snapshot
            snapshot_path = validation_dir / f"stage{stage_num}_validation.json"
            self._save_json(snapshot_data, snapshot_path)

            # Step 5: Log result
            validation_passed = snapshot_data['validation_passed']
            status_emoji = '✅' if validation_passed else '⚠️'
            self.logger.info(
                f"📋 Stage {stage_num} 驗證快照已保存: {snapshot_path} "
                f"{status_emoji}"
            )

            return True

        except Exception as e:
            stage_num = self.get_stage_number()
            self.logger.error(f"❌ Stage {stage_num} 驗證快照保存失敗: {e}")
            return False

    # ==================== Helper Methods (Common Utilities) ====================

    def _merge_upstream_metadata(
        self,
        upstream_metadata: Dict[str, Any],
        stage_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge upstream metadata with current stage metadata

        Grade A+ requirement: Preserve upstream metadata through pipeline
        to maintain data lineage and configuration traceability.

        Args:
            upstream_metadata: Metadata from previous stages
            stage_metadata: Current stage metadata

        Returns:
            Merged metadata dictionary (stage_metadata takes priority)

        Example:
            upstream = {'constellation_configs': {...}, 'processing_start_time': '...'}
            current = {'signal_calculations': 12345, 'processing_duration': 30.5}
            result = {
                'constellation_configs': {...},  # from upstream
                'processing_start_time': '...',  # from upstream
                'signal_calculations': 12345,    # from current
                'processing_duration': 30.5      # from current
            }
        """
        return {**upstream_metadata, **stage_metadata}

    def _create_output_directory(self, stage_number: int) -> Path:
        """
        Create and return output directory path

        Args:
            stage_number: Stage number (1-6)

        Returns:
            Output directory path

        Example:
            stage_number=5 → Path("data/outputs/stage5")
        """
        output_dir = Path(f"data/outputs/stage{stage_number}")
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _create_validation_directory(self) -> Path:
        """
        Create and return validation snapshot directory path

        Returns:
            Validation directory path (data/validation_snapshots)
        """
        validation_dir = Path("data/validation_snapshots")
        validation_dir.mkdir(parents=True, exist_ok=True)
        return validation_dir

    def _generate_timestamp(self) -> str:
        """
        Generate UTC timestamp string

        Returns:
            Timestamp string in format YYYYMMDD_HHMMSS

        Example:
            "20251012_143052"
        """
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def _save_json(self, data: Dict[str, Any], file_path: Path) -> None:
        """
        Save data as JSON file

        Standard JSON saving with:
        - UTF-8 encoding
        - 2-space indentation
        - Non-ASCII characters preserved
        - Datetime objects auto-converted to strings

        Args:
            data: Dictionary to save
            file_path: Target file path

        Raises:
            IOError: If file writing fails
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    # ==================== Fail-Fast Helper Methods ====================

    def _check_required_field(
        self,
        data: Dict[str, Any],
        field: str,
        context: str = ''
    ) -> bool:
        """
        Check if required field exists in data (Fail-Fast)

        Grade A+ requirement: No default values for missing fields.
        Fail immediately if required field is missing.

        Args:
            data: Dictionary to check
            field: Required field name
            context: Context description for error message

        Returns:
            True if field exists, False otherwise (with error log)

        Example:
            if not self._check_required_field(metadata, 'constellation_configs', 'metadata'):
                return False, "Missing required field"
        """
        if field not in data:
            context_str = f"{context} " if context else ""
            self.logger.error(f"❌ {context_str}缺少必需字段 '{field}'")
            return False
        return True

    def _check_required_fields(
        self,
        data: Dict[str, Any],
        fields: List[str],
        context: str = ''
    ) -> Tuple[bool, Optional[str]]:
        """
        Check multiple required fields exist in data (Fail-Fast batch check)

        Args:
            data: Dictionary to check
            fields: List of required field names
            context: Context description for error message

        Returns:
            (success: bool, error_message: Optional[str])
            - (True, None) if all fields exist
            - (False, error_message) if any field missing

        Example:
            success, error = self._check_required_fields(
                metadata,
                ['constellation_configs', 'processing_duration_seconds'],
                'metadata'
            )
            if not success:
                return False, error
        """
        missing_fields = [field for field in fields if field not in data]

        if missing_fields:
            context_str = f"{context} " if context else ""
            error_msg = (
                f"❌ {context_str}缺少必需字段: {', '.join(missing_fields)}"
            )
            self.logger.error(error_msg)
            return False, error_msg

        return True, None

    def _check_field_type(
        self,
        data: Dict[str, Any],
        field: str,
        expected_type: type,
        context: str = ''
    ) -> bool:
        """
        Check if field exists and has expected type (Fail-Fast)

        Args:
            data: Dictionary to check
            field: Field name
            expected_type: Expected Python type
            context: Context description for error message

        Returns:
            True if field exists and has correct type, False otherwise

        Example:
            if not self._check_field_type(stats, 'total_satellites', int, 'processing_stats'):
                return False
        """
        if not self._check_required_field(data, field, context):
            return False

        value = data[field]
        if not isinstance(value, expected_type):
            context_str = f"{context} " if context else ""
            self.logger.error(
                f"❌ {context_str}字段 '{field}' 類型錯誤: "
                f"期望 {expected_type.__name__}, 實際 {type(value).__name__}"
            )
            return False

        return True

    # ==================== Extension Points ====================

    def get_output_filename_pattern(self) -> str:
        """
        Get output filename pattern (can be overridden by subclasses)

        Default pattern: {stage_identifier}_output_{timestamp}.json

        Returns:
            Filename pattern string

        Example:
            Override in Stage3ResultsManager:
            return f"stage3_coordinate_transformation_real_{timestamp}.json"
        """
        stage_id = self.get_stage_identifier()
        return f"{stage_id}_output_{{timestamp}}.json"


# ==================== Backward Compatibility Helper ====================

def create_result_manager(
    stage_number: int,
    logger_instance: Optional[logging.Logger] = None
) -> BaseResultManager:
    """
    Factory function to create stage-specific result manager

    ⚠️ This function will be populated as stages are migrated.
    Currently returns None for unmigrated stages.

    Args:
        stage_number: Stage number (1-6)
        logger_instance: Optional logger instance

    Returns:
        Stage-specific result manager instance

    Raises:
        NotImplementedError: If stage not yet migrated

    Example:
        manager = create_result_manager(5, logger)
        results = manager.build_stage_results(...)
        manager.save_results(results)
    """
    # This will be populated as we migrate each stage
    stage_managers = {
        # 2: Stage2ResultManager,
        # 3: Stage3ResultsManager,
        # 4: Stage4ResultManager,
        # 5: Stage5ResultManager,
        # 6: Stage6ResultManager,
    }

    if stage_number in stage_managers:
        manager_class = stage_managers[stage_number]
        return manager_class(logger_instance)
    else:
        raise NotImplementedError(
            f"Stage {stage_number} result manager not yet migrated to base class. "
            f"Migrated stages: {list(stage_managers.keys())}"
        )
