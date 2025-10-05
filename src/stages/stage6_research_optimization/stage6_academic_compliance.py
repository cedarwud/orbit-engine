#!/usr/bin/env python3
"""
Stage 6: 學術標準合規檢查器

核心職責:
1. 檢查學術標準合規性
2. 防止統一時間基準違規
3. 驗證 constellation_configs 傳遞

依據:
- academic_standards_clarification.md Lines 174-205
- 禁止統一時間基準，每個 TLE 記錄必須保持獨立 epoch_datetime

Author: ORBIT Engine Team
Created: 2025-10-02 (重構自 stage6_research_optimization_processor.py)
"""

import logging
from typing import Dict, Any


class Stage6AcademicComplianceChecker:
    """Stage 6 學術標準合規檢查器

    負責驗證:
    - 無統一時間基準字段 (違反學術標準)
    - constellation_configs 正確傳遞
    - 其他學術標準要求
    """

    def __init__(self, logger: logging.Logger = None):
        """初始化學術合規檢查器

        Args:
            logger: 日誌記錄器，如未提供則創建新的
        """
        self.logger = logger or logging.getLogger(__name__)

    def check_academic_standards_compliance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """學術標準合規檢查

        依據: academic_standards_clarification.md Lines 174-205
        禁止統一時間基準，每個 TLE 記錄必須保持獨立 epoch_datetime

        Args:
            input_data: 輸入數據 (通常是 Stage 5 輸出)

        Returns:
            Dict: 合規檢查結果
                {
                    'compliant': bool,
                    'violations': List[str],
                    'warnings': List[str]
                }
        """
        compliance_result = {
            'compliant': True,
            'violations': [],
            'warnings': []
        }

        try:
            metadata = input_data.get('metadata', {})

            # 🚨 P1: 防御性檢查 - 確保不存在統一時間基準字段
            # 依據: academic_standards_clarification.md Lines 174-205
            forbidden_time_fields = ['calculation_base_time', 'primary_epoch_time', 'unified_time_base']
            for field in forbidden_time_fields:
                if field in metadata:
                    compliance_result['compliant'] = False
                    compliance_result['violations'].append(
                        f"❌ 檢測到禁止的統一時間基準字段: '{field}' "
                        f"(違反 academic_standards_clarification.md:174-205)"
                    )
                    self.logger.error(f"❌ 學術標準違規: 檢測到統一時間基準字段 '{field}'")

            # ✅ Fail-Fast: 檢查 constellation_configs 是否正確傳遞
            # constellation_configs 是信號計算的關鍵配置，不應使用默認值
            if 'constellation_configs' not in metadata:
                compliance_result['compliant'] = False
                compliance_result['violations'].append(
                    "❌ metadata 缺少 constellation_configs (信號計算必要配置)"
                )
                self.logger.error("❌ 學術標準違規: 缺少 constellation_configs")
            else:
                constellation_configs = metadata['constellation_configs']
                # 可以進行更深入的驗證
                if not constellation_configs:
                    compliance_result['warnings'].append(
                        "⚠️ constellation_configs 為空"
                    )

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            # 預期的數據結構錯誤
            self.logger.error(f"學術標準合規檢查數據錯誤: {e}")
            compliance_result['compliant'] = False
            compliance_result['violations'].append(f"數據結構錯誤: {str(e)}")

        except Exception as e:
            # 非預期錯誤，記錄並重新拋出
            self.logger.error(f"學術標準合規檢查內部錯誤: {e}", exc_info=True)
            raise  # ✅ Fail-Fast: 重新拋出非預期異常

        return compliance_result

    def validate_input_compliance(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據學術合規性

        包含學術標準合規檢查

        Args:
            input_data: 輸入數據

        Returns:
            Dict: 驗證結果
                {
                    'is_valid': bool,
                    'errors': List[str],
                    'warnings': List[str]
                }
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            if not isinstance(input_data, dict):
                validation_result['errors'].append("輸入數據必須是字典格式")
                return validation_result

            # 🚨 P1: 學術標準合規檢查
            compliance = self.check_academic_standards_compliance(input_data)
            if not compliance['compliant']:
                validation_result['errors'].extend(compliance['violations'])
                validation_result['is_valid'] = False
                return validation_result

            validation_result['warnings'].extend(compliance['warnings'])
            validation_result['is_valid'] = True

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            # 預期的數據結構錯誤
            validation_result['errors'].append(f"數據結構錯誤: {str(e)}")

        except Exception as e:
            # 非預期錯誤，記錄並重新拋出
            self.logger.error(f"輸入合規驗證內部錯誤: {e}", exc_info=True)
            raise  # ✅ Fail-Fast: 重新拋出非預期異常

        return validation_result
