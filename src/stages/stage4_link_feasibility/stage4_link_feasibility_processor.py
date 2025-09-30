#!/usr/bin/env python3
"""
Stage 4: 鏈路可行性評估處理器 - 六階段架構 v3.0

核心職責:
1. 星座感知篩選 (Starlink 5° vs OneWeb 10°)
2. NTPU 地面站可見性分析
3. 軌道週期感知處理
4. 服務窗口計算
5. 為後續階段提供可連線衛星池

符合 final.md 研究需求和學術標準
"""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# 導入共享模組
from src.shared.base_processor import BaseStageProcessor
from src.shared.interfaces import ProcessingStatus, ProcessingResult, create_processing_result

# 導入 Stage 4 核心模組
from .constellation_filter import ConstellationFilter
from .ntpu_visibility_calculator import NTPUVisibilityCalculator

logger = logging.getLogger(__name__)


class Stage4LinkFeasibilityProcessor(BaseStageProcessor):
    """Stage 4 鏈路可行性評估處理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 Stage 4 處理器"""
        super().__init__(stage_number=4, stage_name="link_feasibility", config=config)

        # 初始化核心組件
        self.constellation_filter = ConstellationFilter(config)
        self.visibility_calculator = NTPUVisibilityCalculator(config)

        self.logger.info("🛰️ Stage 4 鏈路可行性評估處理器初始化完成")
        self.logger.info("   職責: 星座感知篩選、NTPU可見性分析、服務窗口計算")

    def execute(self, input_data: Any) -> Dict[str, Any]:
        """執行鏈路可行性評估 (BaseStageProcessor 接口)"""
        try:
            self.logger.info("🚀 Stage 4: 開始鏈路可行性評估")

            # 驗證輸入數據
            if not self._validate_stage3_output(input_data):
                raise ValueError("Stage 3 輸出格式驗證失敗")

            # 提取 WGS84 座標數據
            wgs84_data = self._extract_wgs84_coordinates(input_data)

            # 執行主要處理流程
            result = self._process_link_feasibility(wgs84_data)

            self.logger.info("✅ Stage 4: 鏈路可行性評估完成")
            return result

        except Exception as e:
            self.logger.error(f"❌ Stage 4 執行異常: {e}")
            raise

    def process(self, input_data: Any) -> ProcessingResult:
        """處理接口 (符合 ProcessingResult 標準)"""
        start_time = time.time()

        try:
            result_data = self.execute(input_data)

            processing_time = time.time() - start_time

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message="Stage 4 鏈路可行性評估成功",
                processing_time=processing_time,
                metadata={
                    'stage': 4,
                    'stage_name': 'link_feasibility',
                    'total_feasible_satellites': result_data.get('metadata', {}).get('feasible_satellites_count', 0)
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Stage 4 處理失敗: {e}")

            return create_processing_result(
                status=ProcessingStatus.FAILED,
                data=None,
                message=f"Stage 4 處理失敗: {str(e)}",
                processing_time=processing_time,
                metadata={'stage': 4, 'stage_name': 'link_feasibility'}
            )

    def _validate_stage3_output(self, input_data: Any) -> bool:
        """驗證 Stage 3 輸出格式"""
        if not isinstance(input_data, dict):
            self.logger.error("輸入數據必須是字典格式")
            return False

        if 'stage' not in input_data or input_data['stage'] != 'stage3_coordinate_transformation':
            self.logger.error("輸入數據必須來自 Stage 3")
            return False

        if 'satellites' not in input_data:
            self.logger.error("缺少 satellites 數據")
            return False

        self.logger.info(f"✅ Stage 3 輸出驗證通過: {len(input_data['satellites'])} 顆衛星")
        return True

    def _extract_wgs84_coordinates(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取 WGS84 座標數據"""
        satellites_data = input_data.get('satellites', {})
        wgs84_data = {}

        for satellite_id, satellite_info in satellites_data.items():
            if isinstance(satellite_info, dict):
                wgs84_coordinates = satellite_info.get('wgs84_coordinates', [])
                constellation = satellite_info.get('constellation', 'unknown')

                if wgs84_coordinates:
                    wgs84_data[satellite_id] = {
                        'wgs84_coordinates': wgs84_coordinates,
                        'constellation': constellation,
                        'total_positions': len(wgs84_coordinates)
                    }

        self.logger.info(f"📊 提取了 {len(wgs84_data)} 顆衛星的 WGS84 座標數據")
        return wgs84_data

    def _process_link_feasibility(self, wgs84_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行主要的鏈路可行性評估流程"""
        self.logger.info("🔍 開始鏈路可行性評估流程...")

        # Step 1: 為每顆衛星計算仰角數據
        elevation_data = self._calculate_all_elevations(wgs84_data)

        # Step 2: 應用星座感知篩選
        constellation_result = self.constellation_filter.apply_constellation_filtering(
            wgs84_data, elevation_data
        )

        # Step 3: 詳細的 NTPU 可見性分析
        ntpu_coverage = self.visibility_calculator.analyze_ntpu_coverage(
            constellation_result['filtered_satellites']
        )

        # Step 4: 構建標準化輸出
        return self._build_stage4_output(
            wgs84_data,
            constellation_result,
            ntpu_coverage,
            elevation_data
        )

    def _calculate_all_elevations(self, wgs84_data: Dict[str, Any]) -> Dict[str, float]:
        """為所有衛星計算最大仰角"""
        elevation_data = {}
        processed = 0
        total = len(wgs84_data)

        self.logger.info(f"📐 開始計算 {total} 顆衛星的仰角...")

        for sat_id, sat_data in wgs84_data.items():
            processed += 1
            if processed % 1000 == 0:
                self.logger.info(f"仰角計算進度: {processed}/{total} ({processed/total:.1%})")

            wgs84_coordinates = sat_data.get('wgs84_coordinates', [])
            max_elevation = -90.0

            # 計算軌道軌跡中的最大仰角
            for point in wgs84_coordinates:
                try:
                    lat = point.get('latitude_deg')
                    lon = point.get('longitude_deg')
                    alt_m = point.get('altitude_m', 0)
                    alt_km = alt_m / 1000.0 if alt_m > 1000 else alt_m  # 處理單位

                    if lat is not None and lon is not None:
                        elevation = self.visibility_calculator.calculate_satellite_elevation(
                            lat, lon, alt_km
                        )
                        max_elevation = max(max_elevation, elevation)

                except Exception as e:
                    continue

            elevation_data[sat_id] = max_elevation

        self.logger.info(f"✅ 仰角計算完成: {len(elevation_data)} 顆衛星")
        return elevation_data

    def _build_stage4_output(self, original_data: Dict[str, Any],
                           constellation_result: Dict[str, Any],
                           ntpu_coverage: Dict[str, Any],
                           elevation_data: Dict[str, float]) -> Dict[str, Any]:
        """構建 Stage 4 標準化輸出"""

        filtered_satellites = constellation_result['filtered_satellites']
        coverage_analysis = constellation_result['coverage_analysis']

        # 構建星座分類結果
        feasible_satellites = {}
        for constellation, analysis in coverage_analysis.items():
            feasible_satellites[constellation] = {
                'satellites': analysis['satellites'],
                'satellite_count': analysis['current_count'],
                'target_range': analysis['target_range'],
                'elevation_threshold': analysis['elevation_threshold'],
                'meets_minimum': analysis['meets_minimum'],
                'within_target': analysis['within_target'],
                'coverage_ratio': analysis['coverage_ratio']
            }

        # 構建輸出結果
        stage4_output = {
            'stage': 'stage4_link_feasibility',
            'feasible_satellites': feasible_satellites,
            'ntpu_analysis': {
                'ground_station': ntpu_coverage['ground_station'],
                'satellites_analysis': ntpu_coverage['satellites_analysis'],
                'coverage_summary': ntpu_coverage['coverage_summary']
            },
            'elevation_analysis': {
                'satellite_elevations': elevation_data,
                'max_elevation': max(elevation_data.values()) if elevation_data else 0,
                'avg_elevation': sum(elevation_data.values()) / len(elevation_data) if elevation_data else 0
            },
            'metadata': {
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_input_satellites': len(original_data),
                'feasible_satellites_count': len(filtered_satellites),
                'constellation_distribution': {
                    constellation: len(data['satellites'])
                    for constellation, data in feasible_satellites.items()
                },
                'link_feasibility_criteria': self.constellation_filter.CONSTELLATION_THRESHOLDS,
                'processing_stage': 4
            }
        }

        # 記錄處理結果
        self.logger.info(f"📊 Stage 4 處理統計:")
        self.logger.info(f"   輸入衛星: {len(original_data)} 顆")
        self.logger.info(f"   可行衛星: {len(filtered_satellites)} 顆")

        for constellation, data in feasible_satellites.items():
            self.logger.info(f"   {constellation}: {data['satellite_count']}/{data['target_range'][1]} 顆 "
                           f"({'✅達標' if data['within_target'] else '⚠️未達標'})")

        return stage4_output

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            if not isinstance(input_data, dict):
                validation_result['errors'].append("輸入數據必須是字典格式")
                return validation_result

            if 'stage' not in input_data:
                validation_result['errors'].append("缺少 stage 標識")
            elif input_data['stage'] != 'stage3_coordinate_transformation':
                validation_result['errors'].append("輸入數據必須來自 Stage 3")

            if 'satellites' not in input_data:
                validation_result['errors'].append("缺少 satellites 數據")
            else:
                satellites_count = len(input_data['satellites'])
                if satellites_count == 0:
                    validation_result['errors'].append("satellites 數據為空")
                else:
                    validation_result['warnings'].append(f"將處理 {satellites_count} 顆衛星")

            validation_result['is_valid'] = len(validation_result['errors']) == 0

        except Exception as e:
            validation_result['errors'].append(f"驗證過程異常: {str(e)}")

        return validation_result

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            if not isinstance(output_data, dict):
                validation_result['errors'].append("輸出數據必須是字典格式")
                return validation_result

            required_keys = ['stage', 'feasible_satellites', 'ntpu_analysis', 'metadata']
            for key in required_keys:
                if key not in output_data:
                    validation_result['errors'].append(f"缺少必要字段: {key}")

            if output_data.get('stage') != 'stage4_link_feasibility':
                validation_result['errors'].append("stage 標識不正確")

            # 檢查可行衛星數據
            feasible_satellites = output_data.get('feasible_satellites', {})
            for constellation, data in feasible_satellites.items():
                sat_count = data.get('satellite_count', 0)
                target_range = data.get('target_range', (0, 0))

                if sat_count < target_range[0]:
                    validation_result['warnings'].append(
                        f"{constellation} 衛星數量 ({sat_count}) 低於目標最小值 ({target_range[0]})"
                    )

            validation_result['is_valid'] = len(validation_result['errors']) == 0

        except Exception as e:
            validation_result['errors'].append(f"驗證過程異常: {str(e)}")

        return validation_result


def create_stage4_processor(config: Optional[Dict[str, Any]] = None) -> Stage4LinkFeasibilityProcessor:
    """創建 Stage 4 處理器實例"""
    return Stage4LinkFeasibilityProcessor(config)


if __name__ == "__main__":
    # 測試 Stage 4 處理器
    processor = create_stage4_processor()

    print("🧪 Stage 4 處理器測試:")
    print(f"階段號: {processor.stage_number}")
    print(f"階段名: {processor.stage_name}")
    print("組件:")
    print(f"  - 星座篩選器: {type(processor.constellation_filter).__name__}")
    print(f"  - 可見性計算器: {type(processor.visibility_calculator).__name__}")

    print("✅ Stage 4 處理器測試完成")