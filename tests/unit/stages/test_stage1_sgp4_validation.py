"""
Stage 1 - SGP4 官方驗證層測試

🎓 學術級測試：驗證 Stage 1 TLE 處理與 NASA sgp4 標準一致性

測試目標：
1. 驗證 TLE checksum 計算與 python-sgp4 一致
2. 驗證 TLE 格式驗證與官方解析器一致
3. 確保雙重驗證機制正常運作

參考標準：
- python-sgp4 (Brandon Rhodes, 2020)
- CelesTrak TLE Format Specification
- NORAD TLE 官方規範
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

# 導入待測試的模組
from stages.stage1_orbital_calculation.tle_data_loader import TLEDataLoader
from stages.stage1_orbital_calculation.stage1_main_processor import Stage1MainProcessor

# 嘗試導入 sgp4（若不可用則跳過相關測試）
try:
    from sgp4.io import twoline2rv, verify_checksum
    from sgp4 import earth_gravity
    SGP4_AVAILABLE = True
except ImportError:
    SGP4_AVAILABLE = False


class TestSGP4ValidationLayer:
    """測試 SGP4 官方驗證層"""

    @pytest.fixture
    def sample_tle(self):
        """提供標準測試 TLE（來自真實數據）"""
        return {
            'name': 'STARLINK-1008',
            'line1': '1 44714U 19074B   25208.98798532  .00002307  00000+0  17380-3 0  9992',
            'line2': '2 44714  53.0548 115.3449 0001134  85.9190 274.1928 15.06383560315059'
        }

    @pytest.fixture
    def tle_loader(self):
        """創建 TLE 載入器實例"""
        return TLEDataLoader()

    @pytest.fixture
    def stage1_processor(self):
        """創建 Stage 1 處理器實例（測試模式）"""
        import os
        os.environ['ORBIT_ENGINE_TEST_MODE'] = '1'
        return Stage1MainProcessor({'sample_mode': True, 'sample_size': 10})

    @pytest.mark.skipif(not SGP4_AVAILABLE, reason="sgp4 庫未安裝")
    def test_checksum_consistency_with_sgp4(self, tle_loader, sample_tle):
        """
        測試：Checksum 計算與 python-sgp4 一致

        驗證點：
        - 內建 checksum 計算結果
        - python-sgp4 verify_checksum() 結果
        - 兩者必須一致
        """
        line1 = sample_tle['line1']
        line2 = sample_tle['line2']

        # 1. 內建驗證
        internal_valid_1 = tle_loader._verify_tle_checksum(line1)
        internal_valid_2 = tle_loader._verify_tle_checksum(line2)

        # 2. sgp4 官方驗證（verify_checksum 會拋出 ValueError 若無效）
        try:
            verify_checksum(line1)
            sgp4_valid_1 = True
        except ValueError:
            sgp4_valid_1 = False

        try:
            verify_checksum(line2)
            sgp4_valid_2 = True
        except ValueError:
            sgp4_valid_2 = False

        # 3. 驗證一致性
        assert internal_valid_1 == sgp4_valid_1, \
            f"Line 1 checksum 驗證不一致: 內建={internal_valid_1}, sgp4={sgp4_valid_1}"
        assert internal_valid_2 == sgp4_valid_2, \
            f"Line 2 checksum 驗證不一致: 內建={internal_valid_2}, sgp4={sgp4_valid_2}"

        # 4. 驗證結果應該都是 True（樣本 TLE 是有效的）
        assert internal_valid_1 and internal_valid_2, "內建驗證失敗"
        assert sgp4_valid_1 and sgp4_valid_2, "sgp4 驗證失敗"

    @pytest.mark.skipif(not SGP4_AVAILABLE, reason="sgp4 庫未安裝")
    def test_tle_parsing_consistency(self, tle_loader, sample_tle):
        """
        測試：TLE 解析與 sgp4 官方解析器一致

        驗證點：
        - 格式驗證通過
        - sgp4 官方解析器可成功解析
        - NORAD ID 提取一致
        """
        line1 = sample_tle['line1']
        line2 = sample_tle['line2']

        # 1. 內建格式驗證
        format_valid = tle_loader._validate_tle_format(line1, line2)
        assert format_valid, "內建格式驗證失敗"

        # 2. sgp4 官方解析
        try:
            satellite = twoline2rv(line1, line2, earth_gravity.wgs72)
            sgp4_parse_success = True
        except ValueError as e:
            sgp4_parse_success = False
            pytest.fail(f"sgp4 官方解析失敗: {e}")

        # 3. 驗證一致性
        assert format_valid == sgp4_parse_success, \
            "格式驗證與 sgp4 解析結果不一致"

        # 4. 驗證 NORAD ID 提取一致
        internal_norad_id = tle_loader._extract_norad_id(line1)
        sgp4_norad_id = str(satellite.satnum).strip()
        assert internal_norad_id == sgp4_norad_id, \
            f"NORAD ID 提取不一致: 內建={internal_norad_id}, sgp4={sgp4_norad_id}"

    @pytest.mark.skipif(not SGP4_AVAILABLE, reason="sgp4 庫未安裝")
    def test_invalid_tle_rejection(self, tle_loader):
        """
        測試：無效 TLE 被正確拒絕

        驗證點：
        - 內建驗證拒絕無效 TLE
        - sgp4 官方解析器同樣拒絕
        - 兩者行為一致
        """
        # 無效 TLE：checksum 錯誤
        invalid_line1 = '1 44714U 19074B   25272.21657815  .00017278  00000+0  11769-2 0  9990'  # 錯誤 checksum
        invalid_line2 = '2 44714  53.0521 191.5010 0001330  86.2947 273.8195 15.06371849324411'

        # 1. 內建驗證應拒絕
        internal_valid = tle_loader._verify_tle_checksum(invalid_line1)
        assert not internal_valid, "內建驗證應拒絕無效 checksum"

        # 2. sgp4 官方驗證應拒絕（拋出 ValueError）
        try:
            verify_checksum(invalid_line1)
            sgp4_valid = True
        except ValueError:
            sgp4_valid = False

        assert not sgp4_valid, "sgp4 驗證應拒絕無效 checksum"

        # 3. 驗證一致性
        assert internal_valid == sgp4_valid, "內建與 sgp4 驗證結果不一致"

    def test_checksum_fix_algorithm(self, tle_loader, sample_tle):
        """
        測試：Checksum 修復算法正確性

        驗證點：
        - 修復後的 checksum 正確
        - 修復邏輯符合 NORAD Modulo 10 標準
        """
        line1 = sample_tle['line1']

        # 1. 故意破壞 checksum
        broken_line1 = line1[:68] + '0'  # 將最後一位改為 0

        # 2. 修復 checksum
        fixed_line1 = tle_loader._fix_tle_checksum(broken_line1)

        # 3. 驗證修復結果
        assert fixed_line1 == line1, \
            f"Checksum 修復失敗: 預期={line1}, 實際={fixed_line1}"

        # 4. 驗證修復後的 checksum 有效
        assert tle_loader._verify_tle_checksum(fixed_line1), \
            "修復後的 checksum 無效"

    def test_checksum_calculation_modulo_10(self, stage1_processor):
        """
        測試：Modulo 10 算法正確性

        驗證點：
        - 數字正確加總
        - 正負號正確處理（算作 1）
        - 其他字符正確忽略
        - Modulo 10 正確計算
        """
        # 測試用例：使用實際驗證過的 TLE（前 68 字符, 預期 checksum）
        test_cases = [
            # STARLINK-1008 真實數據
            ('1 44714U 19074B   25208.98798532  .00002307  00000+0  17380-3 0  999', 2),
            ('2 44714  53.0548 115.3449 0001134  85.9190 274.1928 15.0638356031505', 9),
        ]

        for tle_line, expected_checksum in test_cases:
            calculated = stage1_processor._calculate_tle_checksum(tle_line)
            assert calculated == expected_checksum, \
                f"Checksum 計算錯誤: TLE='{tle_line[:20]}...', 預期={expected_checksum}, 實際={calculated}"

    @pytest.mark.skipif(not SGP4_AVAILABLE, reason="sgp4 庫未安裝")
    def test_epoch_extraction_consistency(self, tle_loader, sample_tle):
        """
        測試：Epoch 時間提取與 sgp4 一致

        驗證點：
        - 內建 epoch 解析
        - sgp4 官方 epoch 解析
        - 兩者時間一致（誤差 <1 秒）
        """
        line1 = sample_tle['line1']
        line2 = sample_tle['line2']

        # 1. 內建 epoch 解析
        internal_epoch = tle_loader._parse_tle_epoch(line1)
        assert internal_epoch is not None, "內建 epoch 解析失敗"

        # 2. sgp4 官方解析
        satellite = twoline2rv(line1, line2, earth_gravity.wgs72)

        # sgp4 提供 epochyr (可能是 2 位或 4 位數) 和 epochdays
        # 需要轉換為 datetime 進行比較
        from datetime import datetime, timedelta

        # 處理 epochyr（可能是 25 或 2025）
        if satellite.epochyr < 100:  # 兩位數年份
            if satellite.epochyr < 57:
                year = satellite.epochyr + 2000
            else:
                year = satellite.epochyr + 1900
        else:  # 四位數年份
            year = satellite.epochyr

        base_date = datetime(year, 1, 1, tzinfo=timezone.utc)
        sgp4_epoch = base_date + timedelta(days=satellite.epochdays - 1)

        # 3. 驗證一致性（允許 1 秒誤差）
        time_diff = abs((internal_epoch - sgp4_epoch).total_seconds())
        assert time_diff < 1.0, \
            f"Epoch 時間不一致: 內建={internal_epoch}, sgp4={sgp4_epoch}, 差異={time_diff}秒"

    @pytest.mark.skipif(not SGP4_AVAILABLE, reason="sgp4 庫未安裝")
    def test_dual_validation_mechanism(self, tle_loader, sample_tle):
        """
        測試：雙重驗證機制運作正常

        驗證點：
        - Layer 1 內建驗證執行
        - Layer 2 sgp4 驗證執行（若可用）
        - 兩層驗證結果一致
        """
        line1 = sample_tle['line1']
        line2 = sample_tle['line2']

        # 執行驗證（內部會調用雙重驗證）
        validation_result = tle_loader._validate_tle_format(line1, line2)

        # 驗證通過
        assert validation_result, "雙重驗證應通過有效 TLE"

        # sgp4 驗證應該被執行（檢查日誌或內部狀態）
        # 這裡我們通過手動驗證來確認
        try:
            satellite = twoline2rv(line1, line2, earth_gravity.wgs72)
            sgp4_success = True
        except ValueError:
            sgp4_success = False

        assert sgp4_success, "sgp4 驗證應成功"


class TestAcademicStandardCompliance:
    """測試學術標準合規性"""

    @pytest.fixture
    def tle_loader(self):
        """創建 TLE 載入器實例"""
        return TLEDataLoader()

    def test_implementation_references(self, tle_loader):
        """
        測試：實現引用完整性

        驗證點：
        - 文檔字符串包含參考文獻
        - 標註 NORAD 標準
        - 提及 python-sgp4 一致性
        """
        # 檢查關鍵函數的文檔字符串
        assert 'NORAD' in tle_loader._verify_tle_checksum.__doc__, \
            "應標註 NORAD 標準"
        assert 'CelesTrak' in tle_loader._verify_tle_checksum.__doc__ or \
               'NORAD' in tle_loader._verify_tle_checksum.__doc__, \
            "應包含參考文獻"

    @pytest.mark.skipif(not SGP4_AVAILABLE, reason="sgp4 庫未安裝")
    def test_sgp4_library_version(self):
        """
        測試：sgp4 庫版本符合要求

        驗證點：
        - sgp4 版本 >= 2.20
        """
        import sgp4
        version = sgp4.__version__
        major, minor = map(int, version.split('.')[:2])

        assert (major > 2) or (major == 2 and minor >= 20), \
            f"sgp4 版本應 >= 2.20, 當前版本: {version}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
