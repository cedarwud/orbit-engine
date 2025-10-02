#!/usr/bin/env python3
"""
Stage 3: 數據提取器 - TEME 座標提取與預處理模組

職責：
- 從 Stage 2 輸出中提取 TEME 座標數據
- 支援取樣模式（減少處理量）
- 解析軌道狀態數據
- 數據格式轉換與標準化

學術合規：Grade A 標準
"""

import logging
import random
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class Stage3DataExtractor:
    """Stage 3 TEME 數據提取器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化數據提取器

        Args:
            config: 提取配置，可包含：
                - sample_mode: bool - 是否啟用取樣模式
                - sample_size: int - 取樣數量
        """
        self.config = config or {}
        self.logger = logger
        self.sample_mode = self.config.get('sample_mode', False)
        self.sample_size = self.config.get('sample_size', 100)

    def extract_teme_coordinates(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取 TEME 座標數據

        Args:
            input_data: Stage 2 的輸出數據

        Returns:
            TEME 座標數據字典，格式：
            {
                'satellite_id': {
                    'satellite_id': str,
                    'constellation': str,
                    'time_series': [
                        {
                            'datetime_utc': str,
                            'position_teme_km': [x, y, z],
                            'velocity_teme_km_s': [vx, vy, vz]
                        },
                        ...
                    ]
                },
                ...
            }
        """
        satellites_data = input_data.get('satellites', {})
        teme_coordinates = {}

        for constellation_name, constellation_data in satellites_data.items():
            if isinstance(constellation_data, dict):
                for satellite_id, satellite_info in constellation_data.items():
                    # 提取 orbital_states 數據
                    orbital_states = satellite_info.get('orbital_states', [])

                    if orbital_states:
                        # 轉換所有時間點的 TEME 座標
                        time_series = self._parse_orbital_states(orbital_states)

                        if time_series:
                            teme_coordinates[satellite_id] = {
                                'satellite_id': satellite_id,
                                'constellation': constellation_name,
                                'time_series': time_series
                            }

        self.logger.info(f"提取了 {len(teme_coordinates)} 顆衛星的 TEME 座標數據")

        # 應用取樣模式（如啟用）
        if self.sample_mode:
            teme_coordinates = self._apply_sampling(teme_coordinates, satellites_data)

        return teme_coordinates

    def _parse_orbital_states(self, orbital_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析軌道狀態數據

        Args:
            orbital_states: 軌道狀態列表

        Returns:
            TEME 時間序列數據
        """
        time_series = []

        for state in orbital_states:
            # ✅ Stage 2 v3.0 使用 position_teme 和 velocity_teme（已是 km 和 km/s）
            position_teme = state.get('position_teme', [0, 0, 0])
            velocity_teme = state.get('velocity_teme', [0, 0, 0])
            timestamp_str = state.get('timestamp')

            if timestamp_str:
                teme_point = {
                    'datetime_utc': timestamp_str,  # ISO 格式時間字串
                    'position_teme_km': position_teme,  # km
                    'velocity_teme_km_s': velocity_teme  # km/s
                }
                time_series.append(teme_point)

        return time_series

    def _apply_sampling(
        self,
        teme_coordinates: Dict[str, Any],
        original_satellites_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        應用取樣模式

        Args:
            teme_coordinates: 完整的 TEME 座標數據
            original_satellites_data: 原始衛星數據（用於計數）

        Returns:
            取樣後的 TEME 座標數據
        """
        if len(teme_coordinates) > self.sample_size:
            # 取樣：隨機選擇指定數量的衛星
            sampled_sat_ids = random.sample(list(teme_coordinates.keys()), self.sample_size)
            sampled_coordinates = {
                sat_id: teme_coordinates[sat_id]
                for sat_id in sampled_sat_ids
            }

            self.logger.info(
                f"🧪 取樣模式：處理 {len(sampled_coordinates)} 顆衛星 "
                f"(共 {len(teme_coordinates)} 顆)"
            )

            return sampled_coordinates

        return teme_coordinates

    def get_extraction_summary(self, teme_coordinates: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取提取摘要

        Args:
            teme_coordinates: TEME 座標數據

        Returns:
            提取摘要字典
        """
        total_satellites = len(teme_coordinates)
        total_points = 0
        constellations = set()

        for satellite_id, sat_data in teme_coordinates.items():
            time_series = sat_data.get('time_series', [])
            total_points += len(time_series)
            constellation = sat_data.get('constellation')
            if constellation:
                constellations.add(constellation)

        return {
            'total_satellites': total_satellites,
            'total_coordinate_points': total_points,
            'constellations': list(constellations),
            'sample_mode': self.sample_mode,
            'sample_size': self.sample_size if self.sample_mode else None
        }


def create_data_extractor(config: Optional[Dict[str, Any]] = None) -> Stage3DataExtractor:
    """創建數據提取器實例"""
    return Stage3DataExtractor(config)
