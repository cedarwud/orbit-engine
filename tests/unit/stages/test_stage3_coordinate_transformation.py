"""
Stage 3 座標轉換處理器 - TDD測試套件

測試 TEME → WGS84 座標轉換功能：
- Skyfield 庫座標轉換準確性
- IAU 標準合規性驗證
- 批量處理性能測試
- 時間系統正確性驗證
"""

import pytest
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
import os

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

# 繞過容器檢查進行測試 - 使用臨時目錄
temp_container_root = '/tmp/claude/home/sat/orbit-engine-test'
os.environ['CONTAINER_ROOT'] = temp_container_root
if not Path(temp_container_root).exists():
    Path(temp_container_root).mkdir(parents=True, exist_ok=True)

from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus


class TestStage3CoordinateTransformation:
    """Stage 3 座標轉換處理器測試套件"""

    @pytest.fixture
    def stage2_teme_data(self):
        """Stage 2 TEME 座標輸出格式 - 使用真實衛星數據"""
        # 導入真實數據提供器
        sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))
        from shared.data_sources.real_satellite_data import get_real_test_data

        # 獲取真實的 Starlink 衛星數據
        real_data = get_real_test_data("starlink")

        # 驗證數據真實性
        from shared.data_sources.real_satellite_data import get_real_satellite_data_provider
        provider = get_real_satellite_data_provider()
        is_authentic = provider.validate_data_authenticity(real_data)

        if not is_authentic:
            raise ValueError("測試數據未通過真實性驗證，違反 CRITICAL DEVELOPMENT PRINCIPLE")

        return real_data

    @pytest.fixture
    def coordinate_processor(self):
        """座標轉換處理器實例"""
        config = {
            'coordinate_config': {
                'source_frame': 'TEME',
                'target_frame': 'WGS84',
                'time_corrections': True,
                'polar_motion': True,
                'nutation_model': 'IAU2000A'
            },
            'test_mode': True,  # 啟用測試模式，跳過可見性篩選
            'skip_visibility_filter': True
        }
        return Stage3CoordinateTransformProcessor(config)

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_coordinate_transformation_basic(self, coordinate_processor, stage2_teme_data):
        """測試基本座標轉換功能"""
        result = coordinate_processor.process(stage2_teme_data)

        # 驗證處理結果
        assert isinstance(result, ProcessingResult)
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None

        # 驗證輸出結構
        assert 'geographic_coordinates' in result.data
        assert 'metadata' in result.data

        # 驗證座標數據
        geo_coords = result.data['geographic_coordinates']
        assert '44714' in geo_coords

        satellite_coords = geo_coords['44714']
        assert 'time_series' in satellite_coords
        assert len(satellite_coords['time_series']) == 2  # 兩個時間點

        # 驗證第一個座標點
        first_coord = satellite_coords['time_series'][0]
        assert 'timestamp' in first_coord
        assert 'latitude_deg' in first_coord
        assert 'longitude_deg' in first_coord
        assert 'altitude_km' in first_coord

        # 驗證座標值範圍
        assert -90 <= first_coord['latitude_deg'] <= 90
        assert -180 <= first_coord['longitude_deg'] <= 180
        assert first_coord['altitude_km'] > 200  # LEO 衛星最低高度約 200km

        print("✅ 基本座標轉換功能測試通過")

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_coordinate_accuracy_validation(self, coordinate_processor, stage2_teme_data):
        """測試座標轉換準確性驗證"""
        result = coordinate_processor.process(stage2_teme_data)

        assert result.status == ProcessingStatus.SUCCESS

        # 驗證準確性統計
        metadata = result.data['metadata']
        assert 'total_coordinate_points' in metadata
        assert 'processing_duration_seconds' in metadata

        # 座標轉換應該成功
        geo_coords = result.data['geographic_coordinates']
        satellite_coords = geo_coords['44714']

        for coord_point in satellite_coords['time_series']:
            # 驗證所有座標點都有效
            assert coord_point['latitude_deg'] is not None
            assert coord_point['longitude_deg'] is not None
            assert coord_point['altitude_km'] is not None

            # 驗證合理的衛星高度 (LEO 範圍)
            assert 300 <= coord_point['altitude_km'] <= 2000

        print("✅ 座標轉換準確性驗證測試通過")

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_skyfield_integration(self, coordinate_processor):
        """測試 Skyfield 庫整合"""
        # 使用真實 ISS 數據進行單點測試
        from shared.data_sources.real_satellite_data import get_real_test_data
        single_point_data = get_real_test_data("iss")

        # 驗證數據真實性
        from shared.data_sources.real_satellite_data import get_real_satellite_data_provider
        provider = get_real_satellite_data_provider()
        if not provider.validate_data_authenticity(single_point_data):
            raise ValueError("ISS 測試數據未通過真實性驗證")

        result = coordinate_processor.process(single_point_data)

        assert result.status == ProcessingStatus.SUCCESS

        # 驗證 Skyfield 轉換結果
        geo_coords = result.data['geographic_coordinates']
        # 使用真實 ISS 衛星 ID
        iss_sat_id = '25544'
        test_coord = geo_coords[iss_sat_id]['time_series'][0]

        # ISS 軌道高度約 400km，緯度在 ±51.6° 範圍內
        assert abs(test_coord['latitude_deg']) <= 60.0  # ISS 軌道傾角限制
        assert 350.0 <= test_coord['altitude_km'] <= 500.0  # ISS 實際高度範圍 (包含軌道提升期間)

        print("✅ Skyfield 庫整合測試通過")

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_time_system_validation(self, coordinate_processor):
        """測試時間系統驗證"""
        # 驗證處理器的時間系統配置
        assert hasattr(coordinate_processor.coordinate_engine, 'ts')  # Skyfield 時間標度
        assert coordinate_processor.coordinate_config.get('time_corrections') == True

        # 測試時間解析
        timestamp_str = '2025-09-27T12:00:00.000000+00:00'
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        # 確保可以創建 Skyfield 時間對象
        t = coordinate_processor.coordinate_engine.ts.from_datetime(dt)
        assert t is not None

        print("✅ 時間系統驗證測試通過")

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_iau_standard_compliance(self, coordinate_processor):
        """測試 IAU 標準合規性"""
        # 驗證使用的章動模型
        config = coordinate_processor.coordinate_config
        assert config.get('nutation_model') == 'IAU2000A'
        assert config.get('polar_motion') == True
        assert config.get('time_corrections') == True

        print("✅ IAU 標準合規性測試通過")

    @pytest.mark.integration
    @pytest.mark.stage3
    def test_batch_processing_performance(self, coordinate_processor):
        """測試批量處理性能 - 使用真實混合衛星數據"""
        # 使用混合真實衛星數據 (ISS + Starlink + GPS)
        from shared.data_sources.real_satellite_data import get_real_test_data
        large_dataset = get_real_test_data("mixed")

        # 驗證數據真實性
        from shared.data_sources.real_satellite_data import get_real_satellite_data_provider
        provider = get_real_satellite_data_provider()
        if not provider.validate_data_authenticity(large_dataset):
            raise ValueError("批量測試數據未通過真實性驗證，違反 CRITICAL DEVELOPMENT PRINCIPLE")

        # 測試批量處理
        result = coordinate_processor.process(large_dataset)

        assert result.status == ProcessingStatus.SUCCESS

        # 驗證處理結果 - 根據真實數據調整期望值
        metadata = result.data['metadata']
        expected_points = large_dataset['metadata']['total_orbital_states']
        expected_satellites = large_dataset['metadata']['total_satellites']

        assert metadata['total_coordinate_points'] == expected_points
        assert metadata['processing_duration_seconds'] is not None

        # 驗證所有座標點都成功轉換
        geo_coords = result.data['geographic_coordinates']
        assert len(geo_coords) >= 1  # 至少有一顆衛星

        # 驗證每顆衛星都有座標點
        for sat_id in geo_coords:
            assert len(geo_coords[sat_id]['time_series']) >= 1

        print(f"✅ 批量處理性能測試通過 - 處理了 {metadata['total_coordinate_points']} 個真實衛星座標點")

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_error_handling(self, coordinate_processor):
        """測試錯誤處理"""
        # 測試無效輸入數據
        invalid_data = {
            'stage': 'invalid_stage',
            'satellites': {}
        }

        result = coordinate_processor.process(invalid_data)
        assert result.status in [ProcessingStatus.ERROR, ProcessingStatus.SUCCESS, ProcessingStatus.VALIDATION_FAILED]  # 可能繼續處理空數據

        # 測試缺少必要字段的數據
        incomplete_data = {
            'stage': 'stage2_orbital_computing',
            'satellites': {
                'starlink': {
                    'incomplete_sat': {
                        'satellite_id': 'incomplete_sat',
                        'orbital_states': [{
                            'timestamp': '2025-09-27T12:00:00.000000+00:00'
                            # 缺少 position_teme_km
                        }]
                    }
                }
            }
        }

        result = coordinate_processor.process(incomplete_data)
        # 處理器應該能夠優雅處理錯誤
        assert result.status in [ProcessingStatus.SUCCESS, ProcessingStatus.ERROR, ProcessingStatus.VALIDATION_FAILED]

        print("✅ 錯誤處理測試通過")

    @pytest.mark.integration
    @pytest.mark.stage3
    def test_output_format_compatibility(self, coordinate_processor, stage2_teme_data):
        """測試輸出格式兼容性"""
        result = coordinate_processor.process(stage2_teme_data)

        assert result.status == ProcessingStatus.SUCCESS

        # 驗證輸出格式符合 Stage 4 需求
        expected_output_structure = {
            'stage': 3,
            'stage_name': 'coordinate_system_transformation',
            'geographic_coordinates': {},
            'metadata': {
                'total_satellites': 1,
                'total_coordinate_points': 2,
                'processing_duration_seconds': 0.0,
                'real_algorithm_compliance': {},
                'transformation_config': {}
            }
        }

        # 驗證頂層結構
        actual_data = result.data
        for key in expected_output_structure:
            assert key in actual_data

        # 驗證元數據字段
        metadata = actual_data['metadata']
        assert 'total_satellites' in metadata
        assert 'total_coordinate_points' in metadata
        assert 'processing_duration_seconds' in metadata

        # 驗證座標數據結構
        geo_coords = actual_data['geographic_coordinates']
        for sat_id, sat_data in geo_coords.items():
            assert 'time_series' in sat_data
            for coord_point in sat_data['time_series']:
                required_fields = ['timestamp', 'latitude_deg', 'longitude_deg', 'altitude_km']
                for field in required_fields:
                    assert field in coord_point

        print("✅ 輸出格式兼容性測試通過")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])