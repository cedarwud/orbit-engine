#!/usr/bin/env python3
"""
Stage 3: 數據驗證器 - 輸入/輸出驗證模組

職責：
- 驗證 Stage 2 輸出數據格式與內容
- 驗證 Stage 3 輸出數據合規性
- 檢查真實算法合規性標記
- 座標範圍合理性檢查

學術合規：Grade A 標準
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Stage3DataValidator:
    """Stage 3 數據驗證器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化數據驗證器

        Args:
            config: 驗證配置（可選）
        """
        self.config = config or {}
        self.logger = logger

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """
        驗證輸入數據

        Args:
            input_data: Stage 2 的輸出數據

        Returns:
            驗證結果字典，包含：
            - valid: bool - 是否通過驗證
            - errors: List[str] - 錯誤列表
            - warnings: List[str] - 警告列表
        """
        errors = []
        warnings = []

        if not isinstance(input_data, dict):
            errors.append("輸入數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'satellites']
        for field in required_fields:
            if field not in input_data:
                errors.append(f"缺少必需字段: {field}")

        if input_data.get('stage') != 'stage2_orbital_computing':
            errors.append("輸入階段標識錯誤，需要 Stage 2 軌道狀態傳播輸出")

        satellites = input_data.get('satellites', {})
        if not isinstance(satellites, dict):
            errors.append("衛星數據格式錯誤")
        elif len(satellites) == 0:
            warnings.append("衛星數據為空")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """
        驗證輸出數據

        Args:
            output_data: Stage 3 的輸出數據

        Returns:
            驗證結果字典
        """
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'stage_name', 'geographic_coordinates', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        if output_data.get('stage') != 3:
            errors.append("階段標識錯誤")

        if output_data.get('stage_name') != 'coordinate_system_transformation':
            errors.append("階段名稱錯誤")

        # 檢查真實算法合規性
        metadata = output_data.get('metadata', {})
        real_algo_compliance = metadata.get('real_algorithm_compliance', {})

        if real_algo_compliance.get('hardcoded_constants_used', True):
            errors.append("檢測到硬編碼常數使用，違反真實算法原則")

        if real_algo_compliance.get('simplified_algorithms_used', True):
            errors.append("檢測到簡化算法使用，違反真實算法原則")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_stage2_output(self, input_data: Any) -> bool:
        """
        驗證 Stage 2 的輸出數據

        Args:
            input_data: Stage 2 輸出數據

        Returns:
            bool: 是否為有效的 Stage 2 輸出
        """
        if not isinstance(input_data, dict):
            return False

        required_fields = ['stage', 'satellites']
        for field in required_fields:
            if field not in input_data:
                return False

        # 檢查是否為 Stage 2 軌道狀態傳播輸出
        return input_data.get('stage') == 'stage2_orbital_computing'

    def validate_coordinate_ranges(
        self,
        latitude_deg: float,
        longitude_deg: float,
        altitude_m: float
    ) -> bool:
        """
        驗證座標範圍合理性

        Args:
            latitude_deg: 緯度（度）
            longitude_deg: 經度（度）
            altitude_m: 高度（米）

        Returns:
            bool: 座標是否在合理範圍內
        """
        # WGS84 地理座標範圍（精確定義）
        MIN_LATITUDE_DEG = -90.0
        MAX_LATITUDE_DEG = 90.0
        # SOURCE: WGS84 標準定義
        # NIMA TR8350.2 Section 3.2 - Geographic Coordinates

        MIN_LONGITUDE_DEG = -180.0
        MAX_LONGITUDE_DEG = 180.0
        # SOURCE: WGS84 標準定義
        # 經度範圍: -180° to +180° (Prime Meridian convention)

        # LEO 衛星高度範圍
        MIN_LEO_ALTITUDE_M = 200000.0  # 200 km
        # SOURCE: ITU-R Recommendation S.1503-3 (01/2021)
        # LEO satellite minimum operational altitude
        # Below this, atmospheric drag becomes excessive

        MAX_LEO_ALTITUDE_M = 2000000.0  # 2000 km
        # SOURCE: ITU definition of LEO orbit upper boundary
        # LEO: 200-2000 km, MEO starts at ~2000km
        # Reference: ITU-R S.1503-3 Section 2.1

        # 檢查緯度範圍
        if latitude_deg < MIN_LATITUDE_DEG or latitude_deg > MAX_LATITUDE_DEG:
            return False

        # 檢查經度範圍
        if longitude_deg < MIN_LONGITUDE_DEG or longitude_deg > MAX_LONGITUDE_DEG:
            return False

        # 檢查高度範圍
        if altitude_m < MIN_LEO_ALTITUDE_M or altitude_m > MAX_LEO_ALTITUDE_M:
            return False

        return True

    def validate_teme_data(self, teme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證提取的 TEME 數據

        Args:
            teme_data: TEME 座標數據

        Returns:
            驗證結果字典
        """
        errors = []
        warnings = []

        if not isinstance(teme_data, dict):
            errors.append("TEME 數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        if len(teme_data) == 0:
            warnings.append("TEME 數據為空")

        # 檢查每個衛星的數據結構
        for satellite_id, satellite_data in teme_data.items():
            if not isinstance(satellite_data, dict):
                errors.append(f"衛星 {satellite_id} 數據格式錯誤")
                continue

            if 'time_series' not in satellite_data:
                errors.append(f"衛星 {satellite_id} 缺少 time_series 字段")
                continue

            time_series = satellite_data.get('time_series', [])
            if not isinstance(time_series, list):
                errors.append(f"衛星 {satellite_id} 的 time_series 必須是列表")
                continue

            if len(time_series) == 0:
                warnings.append(f"衛星 {satellite_id} 的 time_series 為空")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


def create_data_validator(config: Optional[Dict[str, Any]] = None) -> Stage3DataValidator:
    """創建數據驗證器實例"""
    return Stage3DataValidator(config)
