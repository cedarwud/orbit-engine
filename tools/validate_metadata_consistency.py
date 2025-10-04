#!/usr/bin/env python3
"""
Metadata 一致性驗證腳本

目的：
- 防止 metadata 聲明與實際數據不一致
- 檢測修復過程創造的新矛盾
- 作為 CI/CD 流程的一部分

使用：
    python scripts/validate_metadata_consistency.py
    python scripts/validate_metadata_consistency.py --snapshot data/validation_snapshots/stage1_validation.json

退出碼：
    0 - 所有檢查通過
    1 - 發現一致性問題
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


class MetadataConsistencyValidator:
    """Metadata 一致性驗證器"""

    def __init__(self, snapshot_path: str):
        self.snapshot_path = snapshot_path
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_snapshot(self) -> Dict:
        """載入驗證快照"""
        try:
            with open(self.snapshot_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 無法載入快照: {e}")
            sys.exit(1)

    def check_academic_compliance_structure(self, snapshot: Dict) -> bool:
        """檢查 academic_compliance 結構完整性"""
        print("\n🔍 檢查 academic_compliance 結構...")

        metadata = snapshot.get('metadata', {})
        academic_compliance = metadata.get('academic_compliance', {})

        # 檢查新版結構（v2.0）
        required_keys = ['tle_data', 'algorithms', 'system_parameters']

        if all(key in academic_compliance for key in required_keys):
            print("   ✅ 使用 v2.0 結構（三層分離）")
            return self._validate_v2_structure(academic_compliance)
        else:
            # 舊版結構檢查
            if 'no_estimated_values' in academic_compliance:
                print("   ⚠️ 使用舊版結構（單層）")
                return self._validate_v1_structure(academic_compliance, metadata)
            else:
                self.errors.append("academic_compliance 結構無法識別")
                return False

    def _validate_v2_structure(self, compliance: Dict) -> bool:
        """驗證 v2.0 三層結構"""
        all_valid = True

        # TLE 數據層檢查
        tle_data = compliance.get('tle_data', {})
        if not tle_data.get('real_data'):
            self.errors.append("tle_data.real_data 應為 True")
            all_valid = False

        if tle_data.get('source') != 'Space-Track.org':
            self.errors.append(f"tle_data.source 應為 'Space-Track.org'，當前: {tle_data.get('source')}")
            all_valid = False

        # 算法層檢查
        algorithms = compliance.get('algorithms', {})
        if not algorithms.get('no_simplified_algorithms'):
            self.errors.append("algorithms.no_simplified_algorithms 應為 True")
            all_valid = False

        # 系統參數層檢查
        sys_params = compliance.get('system_parameters', {})
        if sys_params.get('rf_parameters_status') != 'documented_research_estimates':
            self.warnings.append("system_parameters.rf_parameters_status 建議為 'documented_research_estimates'")

        if not sys_params.get('provenance_tracked'):
            self.errors.append("system_parameters.provenance_tracked 應為 True")
            all_valid = False

        return all_valid

    def _validate_v1_structure(self, compliance: Dict, metadata: Dict) -> bool:
        """驗證舊版結構（檢測矛盾）"""
        all_valid = True

        # 檢查是否有 constellation_configs
        constellation_configs = metadata.get('constellation_configs', {})

        if constellation_configs:
            # 檢查是否包含 RF 參數
            has_rf_params = False
            for constellation, config in constellation_configs.items():
                if 'tx_power_dbw' in config or 'tx_antenna_gain_db' in config:
                    has_rf_params = True
                    break

            # 如果有 RF 參數但聲稱 no_estimated_values=True，這是矛盾
            if has_rf_params and compliance.get('no_estimated_values'):
                self.errors.append(
                    "矛盾：constellation_configs 包含 RF 參數（研究估計值），"
                    "但 academic_compliance.no_estimated_values=True"
                )
                self.errors.append(
                    "建議：升級到 v2.0 結構，區分 TLE 數據層 vs 系統參數層"
                )
                all_valid = False

        return all_valid

    def check_rf_parameters_documentation(self, snapshot: Dict) -> bool:
        """檢查 RF 參數是否有完整文檔"""
        print("\n🔍 檢查 RF 參數文檔...")

        metadata = snapshot.get('metadata', {})
        constellation_configs = metadata.get('constellation_configs', {})

        if not constellation_configs:
            print("   ⚠️ 未發現 constellation_configs")
            return True

        # 檢查 RF 參數存在性
        rf_params = ['tx_power_dbw', 'tx_antenna_gain_db', 'frequency_ghz']
        all_valid = True

        for constellation, config in constellation_configs.items():
            has_rf = any(param in config for param in rf_params)

            if has_rf:
                print(f"   📡 {constellation} 包含 RF 參數")

                # 檢查文檔是否存在
                rf_doc_path = Path('docs/data_sources/RF_PARAMETERS.md')
                if not rf_doc_path.exists():
                    self.errors.append(
                        f"RF 參數缺少文檔: docs/data_sources/RF_PARAMETERS.md 不存在"
                    )
                    all_valid = False
                else:
                    # 檢查文檔內容
                    with open(rf_doc_path, 'r', encoding='utf-8') as f:
                        doc_content = f.read()

                        # 檢查是否包含必要的引用
                        if constellation.lower() not in doc_content.lower():
                            self.warnings.append(
                                f"RF_PARAMETERS.md 未提及 {constellation}"
                            )

                        # 檢查是否標註不確定性
                        if '不確定性' not in doc_content and 'uncertainty' not in doc_content.lower():
                            self.warnings.append(
                                "RF_PARAMETERS.md 缺少不確定性評估"
                            )

        return all_valid

    def check_constellation_constants_consistency(self, snapshot: Dict) -> bool:
        """檢查 constellation_constants.py 與快照的一致性"""
        print("\n🔍 檢查 constellation_constants 一致性...")

        try:
            sys.path.insert(0, 'src')
            from shared.constants.constellation_constants import ConstellationRegistry

            metadata = snapshot.get('metadata', {})
            constellation_configs = metadata.get('constellation_configs', {})

            all_valid = True

            for constellation in ConstellationRegistry.SUPPORTED_CONSTELLATIONS:
                const_name = constellation.name

                if const_name not in constellation_configs:
                    self.errors.append(
                        f"constellation_configs 缺少 {const_name}"
                    )
                    all_valid = False
                    continue

                snapshot_config = constellation_configs[const_name]

                # 檢查關鍵參數一致性
                if hasattr(constellation, 'tx_power_dbw'):
                    if snapshot_config.get('tx_power_dbw') != constellation.tx_power_dbw:
                        self.errors.append(
                            f"{const_name}.tx_power_dbw 不一致: "
                            f"常數={constellation.tx_power_dbw}, "
                            f"快照={snapshot_config.get('tx_power_dbw')}"
                        )
                        all_valid = False

            return all_valid

        except Exception as e:
            self.errors.append(f"無法導入 ConstellationRegistry: {e}")
            return False

    def check_validation_snapshot_integrity(self, snapshot: Dict) -> bool:
        """檢查驗證快照完整性"""
        print("\n🔍 檢查驗證快照完整性...")

        all_valid = True

        # 基本字段檢查
        required_fields = ['stage', 'status', 'metadata', 'validation_passed']
        for field in required_fields:
            if field not in snapshot:
                self.errors.append(f"驗證快照缺少必要字段: {field}")
                all_valid = False

        # Metadata 字段檢查
        metadata = snapshot.get('metadata', {})
        required_metadata = ['academic_compliance', 'constellation_configs']

        for field in required_metadata:
            if field not in metadata:
                self.errors.append(f"metadata 缺少必要字段: {field}")
                all_valid = False

        return all_valid

    def run_all_checks(self) -> bool:
        """運行所有檢查"""
        print(f"\n{'='*60}")
        print(f"📋 Metadata 一致性驗證")
        print(f"{'='*60}")
        print(f"快照路徑: {self.snapshot_path}")

        snapshot = self.load_snapshot()

        checks = [
            self.check_validation_snapshot_integrity(snapshot),
            self.check_academic_compliance_structure(snapshot),
            self.check_rf_parameters_documentation(snapshot),
            self.check_constellation_constants_consistency(snapshot),
        ]

        all_passed = all(checks)

        # 報告結果
        print(f"\n{'='*60}")
        print(f"📊 驗證結果")
        print(f"{'='*60}")

        if self.errors:
            print(f"\n❌ 發現 {len(self.errors)} 個錯誤:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if self.warnings:
            print(f"\n⚠️ 發現 {len(self.warnings)} 個警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if all_passed and not self.errors:
            print("\n✅ 所有檢查通過！Metadata 一致性良好。")
            return True
        else:
            print("\n❌ 驗證失敗！請修正上述問題。")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='驗證 Metadata 一致性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--snapshot',
        default='data/validation_snapshots/stage1_validation.json',
        help='驗證快照路徑 (默認: stage1_validation.json)'
    )

    args = parser.parse_args()

    validator = MetadataConsistencyValidator(args.snapshot)
    success = validator.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
