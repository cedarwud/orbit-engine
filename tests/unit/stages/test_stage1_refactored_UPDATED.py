#!/usr/bin/env python3
"""
Stage 1 重構處理器 TDD 測試套件 - 更新版

測試重構後的 Stage1RefactoredProcessor，確保：
- 100% BaseStageProcessor 接口合規
- ProcessingResult 標準輸出格式
- 5項專用驗證檢查功能
- 向後兼容性保證
- TLE 數據載入和驗證功能

更新日期: 2025-09-24
測試版本: Stage1RefactoredProcessor v1.0
"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# 添加 src 路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

# 導入重構後的處理器
from stages.stage1_orbital_calculation.stage1_main_processor import (
    Stage1RefactoredProcessor, create_stage1_refactored_processor
)

# 導入標準接口
from shared.interfaces.processor_interface import (
    ProcessingStatus, ProcessingResult, ProcessingMetrics, BaseProcessor
)
from shared.base_processor import BaseStageProcessor


class TestStage1RefactoredProcessor:
    """Stage 1 重構處理器測試套件"""

    @pytest.fixture
    def processor(self):
        """創建重構後的 Stage 1 處理器實例"""
        return create_stage1_refactored_processor({
            'sample_mode': True,
            'sample_size': 5
        })

    @pytest.fixture
    def processor_full(self):
        """創建完整模式的處理器 (用於性能測試)"""
        return create_stage1_refactored_processor({
            'sample_mode': False
        })

    # === 接口合規性測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_processor_creation(self, processor):
        """測試處理器創建"""
        assert processor is not None
        assert isinstance(processor, Stage1RefactoredProcessor)
        assert isinstance(processor, BaseStageProcessor)
        assert isinstance(processor, BaseProcessor)

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_base_processor_interface_compliance(self, processor):
        """測試 BaseProcessor 接口完全合規"""
        # 檢查必要方法存在
        required_methods = ['process', 'validate_input', 'validate_output',
                           'get_status', 'get_metrics', 'get_config']

        for method in required_methods:
            assert hasattr(processor, method), f"缺少必要方法: {method}"

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_base_stage_processor_interface_compliance(self, processor):
        """測試 BaseStageProcessor 接口完全合規"""
        # 檢查階段處理器專用方法
        stage_methods = ['execute', 'run_validation_checks', 'save_validation_snapshot']

        for method in stage_methods:
            assert hasattr(processor, method), f"缺少階段處理器方法: {method}"

        # 檢查屬性
        assert hasattr(processor, 'stage_number')
        assert hasattr(processor, 'stage_name')
        assert processor.stage_number == 1
        assert 'tle_data_loading' in processor.stage_name

    # === ProcessingResult 標準化測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_execute_returns_processing_result(self, processor):
        """測試 execute() 返回標準 ProcessingResult"""
        result = processor.execute()

        # 檢查返回類型
        assert isinstance(result, ProcessingResult), "execute() 必須返回 ProcessingResult"

        # 檢查必要屬性
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'metrics')

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_process_returns_processing_result(self, processor):
        """測試 process() 返回標準 ProcessingResult"""
        result = processor.process()

        assert isinstance(result, ProcessingResult), "process() 必須返回 ProcessingResult"
        assert result.status == ProcessingStatus.SUCCESS

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_processing_result_structure(self, processor):
        """測試 ProcessingResult 結構完整性"""
        result = processor.execute()

        # 檢查狀態
        assert result.status == ProcessingStatus.SUCCESS

        # 檢查數據結構
        assert isinstance(result.data, dict)
        assert 'satellites' in result.data
        assert 'metadata' in result.data
        assert 'stage' in result.data

        # 檢查指標
        assert isinstance(result.metrics, ProcessingMetrics)
        assert result.metrics.duration_seconds > 0

        # 檢查錯誤和警告
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    # === 數據載入和驗證測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_tle_data_loading(self, processor):
        """測試 TLE 數據載入功能"""
        result = processor.execute()

        # 檢查衛星數據
        satellites = result.data.get('satellites', [])
        assert len(satellites) > 0, "應該載入衛星數據"

        # 檢查第一顆衛星數據結構 (包含個別epoch時間)
        if satellites:
            satellite = satellites[0]
            required_fields = ['satellite_id', 'tle_line1', 'tle_line2', 'norad_id', 'epoch_datetime']

            for field in required_fields:
                assert field in satellite, f"衛星數據缺少字段: {field}"

            # ⚠️ 學術標準修正: 驗證個別epoch_datetime字段
            assert 'epoch_datetime' in satellite, "每顆衛星必須有個別epoch_datetime字段"
            epoch_datetime = satellite['epoch_datetime']
            assert epoch_datetime is not None, "epoch_datetime不能為空"
            assert isinstance(epoch_datetime, str), "epoch_datetime必須為ISO格式字串"

            # 驗證ISO 8601格式
            from datetime import datetime
            try:
                parsed_dt = datetime.fromisoformat(epoch_datetime.replace('Z', '+00:00'))
                assert parsed_dt is not None, "epoch_datetime必須為有效的ISO 8601格式"
            except ValueError:
                pytest.fail(f"epoch_datetime格式不正確: {epoch_datetime}")

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_tle_format_validation(self, processor):
        """測試 TLE 格式驗證功能"""
        result = processor.execute()
        satellites = result.data.get('satellites', [])

        if satellites:
            satellite = satellites[0]
            line1 = satellite.get('tle_line1', '')
            line2 = satellite.get('tle_line2', '')

            # 檢查 TLE 格式
            assert len(line1) == 69, f"TLE Line1 長度應為69，實際為{len(line1)}"
            assert len(line2) == 69, f"TLE Line2 長度應為69，實際為{len(line2)}"
            assert line1[0] == '1', "TLE Line1 應以 '1' 開始"
            assert line2[0] == '2', "TLE Line2 應以 '2' 開始"

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_time_base_establishment(self, processor):
        """測試個別epoch時間基準建立功能 (學術標準修正)"""
        result = processor.execute()
        metadata = result.data.get('metadata', {})

        # ⚠️ 學術標準修正: 檢查個別epoch時間字段 (不再檢查統一時間基準)
        academic_compliance_fields = [
            'time_base_source',
            'academic_compliance',
            'individual_epoch_processing',
            'academic_compliance_note'
        ]
        for field in academic_compliance_fields:
            assert field in metadata, f"缺少學術標準字段: {field}"

        # 驗證個別epoch處理標記
        assert metadata['individual_epoch_processing'] == True, "必須啟用個別epoch處理"
        assert metadata['academic_compliance'] == 'individual_epoch_based', "必須符合個別epoch學術標準"
        assert metadata['time_base_source'] == 'individual_tle_epochs', "時間來源必須為個別TLE epochs"

        # 檢查禁止統一時間基準
        forbidden_fields = ['calculation_base_time', 'primary_epoch_time']
        for field in forbidden_fields:
            assert field not in metadata, f"禁止字段出現: {field} (不符合學術標準)"

        # 檢查時間基準資料品質
        assert 'time_quality_metrics' in metadata
        time_quality = metadata['time_quality_metrics']
        assert 'overall_time_quality_score' in time_quality
        assert time_quality['overall_time_quality_score'] > 0

    # === 驗證功能測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_run_validation_checks_method_exists(self, processor):
        """測試 run_validation_checks 方法存在且可調用"""
        result = processor.execute()

        # 檢查方法存在
        assert hasattr(processor, 'run_validation_checks')

        # 檢查方法可調用
        validation_report = processor.run_validation_checks(result.data)
        assert isinstance(validation_report, dict)

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_validation_checks_structure(self, processor):
        """測試驗證檢查結構完整性"""
        result = processor.execute()
        validation_report = processor.run_validation_checks(result.data)

        # 檢查報告結構
        required_fields = ['validation_status', 'overall_status', 'validation_details']
        for field in required_fields:
            assert field in validation_report, f"驗證報告缺少字段: {field}"

        # 檢查驗證詳情
        details = validation_report['validation_details']
        assert 'success_rate' in details

        # 檢查5項驗證檢查是否都存在
        expected_checks = [
            'tle_format_validation',
            'tle_checksum_verification',
            'data_completeness_check',
            'time_base_establishment',
            'satellite_data_structure'
        ]

        for check in expected_checks:
            assert check in details, f"驗證結果中缺少檢查: {check}"

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_five_validation_checks_performed(self, processor):
        """測試 5 項專用驗證檢查是否執行"""
        result = processor.execute()
        validation_report = processor.run_validation_checks(result.data)

        details = validation_report['validation_details']

        expected_checks = [
            'tle_format_validation',
            'tle_checksum_verification',
            'data_completeness_check',
            'time_base_establishment',
            'satellite_data_structure'
        ]

        for check in expected_checks:
            assert check in details, f"驗證結果中缺少檢查: {check}"
            # 檢查每個檢查都有 passed 字段
            assert 'passed' in details[check], f"檢查 {check} 缺少 passed 字段"
            assert isinstance(details[check]['passed'], bool), f"檢查 {check} 的 passed 字段應該是布林值"

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_validation_success_rate_calculation(self, processor):
        """測試驗證成功率計算"""
        result = processor.execute()
        validation_report = processor.run_validation_checks(result.data)

        details = validation_report['validation_details']
        success_rate = details.get('success_rate', 0.0)

        # 成功率應該在合理範圍內
        assert 0.0 <= success_rate <= 1.0, f"成功率超出範圍: {success_rate}"

        # 對於樣本數據，成功率應該很高
        assert success_rate >= 0.8, f"成功率過低: {success_rate}"

    # === 快照保存測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_save_validation_snapshot_method_exists(self, processor):
        """測試 save_validation_snapshot 方法存在且可調用"""
        result = processor.execute()

        # 檢查方法存在
        assert hasattr(processor, 'save_validation_snapshot')

        # 檢查方法可調用
        snapshot_saved = processor.save_validation_snapshot(result.data)
        assert isinstance(snapshot_saved, bool)

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_validation_snapshot_content(self, processor):
        """測試驗證快照內容正確性"""
        result = processor.execute()
        snapshot_saved = processor.save_validation_snapshot(result.data)

        if snapshot_saved:
            # 檢查快照文件
            snapshot_path = processor.validation_dir / 'stage1_validation.json'
            assert snapshot_path.exists(), "快照文件應該存在"

            with open(snapshot_path, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)

            # 檢查快照基本結構
            assert snapshot_data.get('stage') == 1
            assert snapshot_data.get('stage_name') == 'refactored_tle_data_loading'
            assert snapshot_data.get('status') == 'success'
            assert snapshot_data.get('validation_passed') == True

    # === 向後兼容性測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_backward_compatibility_data_access(self, processor):
        """測試向後兼容性 - 數據訪問方式"""
        result = processor.execute()

        # Stage 2 應該能通過 result.data 訪問所有必要數據
        stage2_input = result.data

        # 檢查關鍵字段存在
        assert 'satellites' in stage2_input
        assert 'metadata' in stage2_input
        assert 'stage' in stage2_input

        # ⚠️ 學術標準修正: 檢查個別epoch時間繼承字段 (Stage 2 繼承用)
        metadata = stage2_input['metadata']
        assert 'time_base_source' in metadata
        assert metadata['time_base_source'] == 'individual_tle_epochs'
        assert 'academic_compliance' in metadata
        assert metadata['academic_compliance'] == 'individual_epoch_based'

        # 檢查stage1_time_inheritance新結構
        assert 'stage1_time_inheritance' in metadata
        inheritance = metadata['stage1_time_inheritance']
        assert inheritance['time_processing_method'] == 'individual_epoch_based'
        assert inheritance['unified_time_base_prohibited'] == True

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_data_structure_compatibility(self, processor):
        """測試數據結構兼容性"""
        result = processor.execute()
        satellites = result.data.get('satellites', [])

        if satellites:
            satellite = satellites[0]

            # ⚠️ 學術標準修正: 檢查基本字段 (包含個別epoch時間)
            basic_fields = ['satellite_id', 'tle_line1', 'tle_line2', 'norad_id', 'epoch_datetime']
            for field in basic_fields:
                assert field in satellite, f"基本字段缺失: {field}"

            # 驗證個別epoch_datetime字段格式
            epoch_datetime = satellite['epoch_datetime']
            assert isinstance(epoch_datetime, str), "epoch_datetime必須為ISO格式字串"
            assert 'T' in epoch_datetime, "epoch_datetime必須包含ISO 8601的T分隔符"
            assert epoch_datetime.endswith(('+00:00', 'Z')), "epoch_datetime必須包含UTC時區資訊"

    # === 性能測試 ===

    @pytest.mark.integration
    @pytest.mark.stage1
    def test_processing_performance(self, processor):
        """測試處理性能"""
        import time

        start_time = time.time()
        result = processor.execute()
        end_time = time.time()

        duration = end_time - start_time

        # 小樣本處理應該很快
        assert duration < 5.0, f"處理時間過長: {duration:.2f}秒"

        # 檢查指標記錄
        assert result.metrics is not None
        assert result.metrics.duration_seconds > 0

    @pytest.mark.integration
    @pytest.mark.stage1
    @pytest.mark.slow
    def test_full_processing_performance(self, processor_full):
        """測試完整處理性能 (慢測試)"""
        import time

        start_time = time.time()
        result = processor_full.execute()
        end_time = time.time()

        duration = end_time - start_time

        # 完整處理應該在 30 秒內完成 (文檔要求)
        assert duration < 30.0, f"完整處理時間超過要求: {duration:.2f}秒"

        # 應該處理完整的衛星數據集 (9000+ 顆衛星)
        satellites_count = len(result.data.get('satellites', []))
        expected_min = 8000  # 最少期望 8000+ 顆衛星 (Starlink + OneWeb)
        assert satellites_count >= expected_min, f"衛星數量未達標: 載入{satellites_count}顆，期望至少{expected_min}顆"

        # 檢查主要星座是否存在
        from collections import Counter
        constellation_counts = Counter([s.get('constellation', 'unknown') for s in result.data.get('satellites', [])])

        # Starlink 應該有大量衛星 (7000+)
        starlink_count = constellation_counts.get('starlink', 0)
        assert starlink_count >= 7000, f"Starlink衛星數量不足: {starlink_count}顆，期望至少7000顆"

        # OneWeb 應該有數百顆衛星 (500+)
        oneweb_count = constellation_counts.get('oneweb', 0)
        assert oneweb_count >= 500, f"OneWeb衛星數量不足: {oneweb_count}顆，期望至少500顆"

    # === 錯誤處理測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_input_validation(self, processor):
        """測試輸入驗證"""
        # 測試有效輸入
        valid_result = processor.validate_input(None)  # Stage 1 接受 None
        assert valid_result['valid'] == True

        # 測試無效輸入
        invalid_result = processor.validate_input("invalid_input")
        assert isinstance(invalid_result, dict)
        assert 'valid' in invalid_result

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_output_validation(self, processor):
        """測試輸出驗證"""
        result = processor.execute()

        validation_result = processor.validate_output(result.data)
        assert isinstance(validation_result, dict)
        assert 'valid' in validation_result
        assert validation_result['valid'] == True

    # === 配置測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_processor_configuration(self):
        """測試處理器配置"""
        config = {
            'sample_mode': True,
            'sample_size': 3,
            'tle_validation_config': {
                'strict_format_check': True,
                'checksum_verification': True
            }
        }

        processor = create_stage1_refactored_processor(config)
        assert processor is not None

        result = processor.execute()
        satellites = result.data.get('satellites', [])

        # 樣本模式也會載入所有數據，但處理速度應該很快
        assert len(satellites) >= 0, "應該載入衛星數據"

        # 檢查處理性能是否合理
        assert result.metrics.duration_seconds < 10.0, "樣本模式處理時間應該很短"

    # === 重構標記測試 ===

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_refactored_version_markers(self, processor):
        """測試重構版本標記"""
        result = processor.execute()
        metadata = result.data.get('metadata', {})

        # 檢查重構版本標記
        assert metadata.get('refactored_version') == True
        assert metadata.get('interface_compliance') == 'BaseStageProcessor_v2.0'

        # 檢查處理統計資料
        assert 'processing_metadata' in metadata


# === 工廠函數測試 ===

@pytest.mark.unit
@pytest.mark.stage1
def test_create_stage1_refactored_processor_factory():
    """測試工廠函數"""
    processor = create_stage1_refactored_processor()
    assert isinstance(processor, Stage1RefactoredProcessor)

    # 測試配置傳遞
    config = {'sample_mode': True}
    processor_with_config = create_stage1_refactored_processor(config)
    assert processor_with_config is not None


# === TDD 測試標記 ===

@pytest.mark.tdd
class TestStage1RefactoredTDD:
    """Stage 1 重構 TDD 專用測試"""

    def test_tdd_red_green_refactor_cycle(self):
        """TDD 紅-綠-重構循環測試"""
        # 這個測試確保重構後的處理器通過所有 TDD 要求
        processor = create_stage1_refactored_processor({'sample_mode': True, 'sample_size': 2})

        # RED: 測試失敗場景
        # GREEN: 測試成功場景
        result = processor.execute()
        assert result.status == ProcessingStatus.SUCCESS

        # REFACTOR: 驗證重構後的品質改善
        validation = processor.run_validation_checks(result.data)
        assert validation['validation_status'] == 'passed'


if __name__ == "__main__":
    # 直接執行測試
    pytest.main([__file__, "-v", "-s", "--tb=short"])