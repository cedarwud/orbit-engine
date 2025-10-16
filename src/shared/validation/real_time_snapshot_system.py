#!/usr/bin/env python3
"""
🔍 實時驗證快照系統
Real-Time Validation Snapshot System

監控整個六階段系統的學術合規性狀態，提供即時快照和連續驗證
Monitors academic compliance status across all six stages with real-time snapshots
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import hashlib
import logging

# 學術合規性常數
ACADEMIC_GRADE_A_REQUIREMENTS = [
    "real_tle_data_source",
    "complete_sgp4_implementation",
    "physics_based_calculations",
    "itu_r_compliant_formulas",
    "3gpp_standard_parameters"
]

FORBIDDEN_ACADEMIC_VIOLATIONS = [
    "simplified_algorithms",
    "mock_data_usage",
    "hardcoded_assumptions",
    "simulation_mode_fallbacks",
    "random_generated_parameters"
]

@dataclass
class ValidationSnapshot:
    """驗證快照數據結構"""
    timestamp: str
    stage: str
    compliance_score: float
    grade_level: str
    violations: List[Dict[str, Any]]
    academic_requirements: List[Dict[str, Any]]
    file_checksums: Dict[str, str]
    performance_metrics: Dict[str, float]

class RealTimeValidationMonitor:
    """實時驗證監控器"""

    def __init__(self, project_root: str = "/home/sat/orbit-engine"):
        self.project_root = Path(project_root)
        self.snapshots_dir = self.project_root / "tests" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # 設置日誌
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_snapshots: Dict[str, ValidationSnapshot] = {}

    def start_monitoring(self, interval_seconds: int = 300):
        """開始實時監控"""
        if self.monitoring_active:
            self.logger.warning("監控已經在運行中")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info(f"實時驗證監控已啟動，間隔: {interval_seconds}秒")

    def stop_monitoring(self):
        """停止實時監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        self.logger.info("實時驗證監控已停止")

    def _monitoring_loop(self, interval_seconds: int):
        """監控循環"""
        while self.monitoring_active:
            try:
                self._create_all_stage_snapshots()
                time.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"監控循環異常: {e}")
                time.sleep(10)  # 異常時短暫等待

    def _create_all_stage_snapshots(self):
        """為所有階段創建驗證快照"""
        stages = [
            "stage1_orbital_calculation",
            "stage2_orbital_computing",
            "stage3_signal_analysis",
            "stage4_optimization",
            "stage5_data_integration",
            "stage6_persistence_api"
        ]

        for stage in stages:
            try:
                snapshot = self._create_stage_snapshot(stage)
                self._save_snapshot(snapshot)
                self.last_snapshots[stage] = snapshot

                # 檢查是否有新的違規
                self._check_for_new_violations(stage, snapshot)

            except Exception as e:
                self.logger.error(f"創建{stage}快照失敗: {e}")

    def _create_stage_snapshot(self, stage: str) -> ValidationSnapshot:
        """為指定階段創建驗證快照"""
        stage_path = self.project_root / "src" / "stages" / stage

        if not stage_path.exists():
            raise FileNotFoundError(f"階段路徑不存在: {stage_path}")

        # 計算文件校驗和
        file_checksums = self._calculate_file_checksums(stage_path)

        # 執行合規性檢查
        violations = self._check_academic_violations(stage_path)
        academic_requirements = self._check_academic_requirements(stage_path)

        # 計算合規性分數
        compliance_score = self._calculate_compliance_score(violations, academic_requirements)
        grade_level = self._determine_grade_level(compliance_score, violations)

        # 性能指標
        performance_metrics = self._calculate_performance_metrics(stage_path)

        return ValidationSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            stage=stage,
            compliance_score=compliance_score,
            grade_level=grade_level,
            violations=violations,
            academic_requirements=academic_requirements,
            file_checksums=file_checksums,
            performance_metrics=performance_metrics
        )

    def _calculate_file_checksums(self, stage_path: Path) -> Dict[str, str]:
        """計算階段文件的校驗和"""
        checksums = {}

        for py_file in stage_path.rglob("*.py"):
            try:
                content = py_file.read_bytes()
                checksum = hashlib.md5(content).hexdigest()
                relative_path = str(py_file.relative_to(self.project_root))
                checksums[relative_path] = checksum
            except Exception as e:
                self.logger.warning(f"計算校驗和失敗 {py_file}: {e}")

        return checksums

    def _check_academic_violations(self, stage_path: Path) -> List[Dict[str, Any]]:
        """檢查學術合規性違規"""
        violations = []

        for py_file in stage_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                file_violations = self._scan_file_violations(content, str(py_file))
                violations.extend(file_violations)
            except Exception as e:
                self.logger.warning(f"掃描違規失敗 {py_file}: {e}")

        return violations

    def _scan_file_violations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """掃描單個文件的違規"""
        violations = []

        # 檢查簡化算法
        if any(keyword in content.lower() for keyword in ['simplified', '簡化', 'basic model']):
            violations.append({
                'type': 'simplified_algorithm',
                'severity': 'critical',
                'file': file_path,
                'description': '發現簡化算法實現'
            })

        # 檢查模擬數據
        if any(keyword in content.lower() for keyword in ['mock', 'random.normal', 'np.random']):
            violations.append({
                'type': 'mock_data_usage',
                'severity': 'critical',
                'file': file_path,
                'description': '發現模擬數據使用'
            })

        # 檢查硬編碼假設
        if any(keyword in content for keyword in ['假設', 'assumed', 'hardcoded']):
            violations.append({
                'type': 'hardcoded_assumption',
                'severity': 'major',
                'file': file_path,
                'description': '發現硬編碼假設'
            })

        return violations

    def _check_academic_requirements(self, stage_path: Path) -> List[Dict[str, Any]]:
        """檢查學術要求滿足情況"""
        requirements = []

        for requirement in ACADEMIC_GRADE_A_REQUIREMENTS:
            status = self._check_specific_requirement(stage_path, requirement)
            requirements.append({
                'requirement': requirement,
                'status': 'satisfied' if status else 'not_satisfied',
                'critical': True
            })

        return requirements

    def _check_specific_requirement(self, stage_path: Path, requirement: str) -> bool:
        """檢查特定學術要求"""
        if requirement == "real_tle_data_source":
            return self._check_real_tle_usage(stage_path)
        elif requirement == "complete_sgp4_implementation":
            return self._check_sgp4_implementation(stage_path)
        elif requirement == "physics_based_calculations":
            return self._check_physics_calculations(stage_path)
        elif requirement == "itu_r_compliant_formulas":
            return self._check_itu_r_compliance(stage_path)
        elif requirement == "3gpp_standard_parameters":
            return self._check_3gpp_compliance(stage_path)
        return False

    def _check_real_tle_usage(self, stage_path: Path) -> bool:
        """檢查真實TLE數據使用"""
        for py_file in stage_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                if any(keyword in content for keyword in ['tle_data', 'space-track', 'orbital_elements']):
                    return True
            except:
                continue
        return False

    def _check_sgp4_implementation(self, stage_path: Path) -> bool:
        """檢查SGP4實現"""
        for py_file in stage_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                if 'sgp4' in content.lower() and 'orbital' in content.lower():
                    return True
            except:
                continue
        return False

    def _check_physics_calculations(self, stage_path: Path) -> bool:
        """檢查物理計算"""
        for py_file in stage_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                if any(keyword in content.lower() for keyword in ['friis', 'physics', 'calculation']):
                    return True
            except:
                continue
        return False

    def _check_itu_r_compliance(self, stage_path: Path) -> bool:
        """檢查ITU-R合規性"""
        for py_file in stage_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                if 'itu' in content.lower() or 'itu_r' in content:
                    return True
            except:
                continue
        return False

    def _check_3gpp_compliance(self, stage_path: Path) -> bool:
        """檢查3GPP合規性"""
        for py_file in stage_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                if '3gpp' in content.lower() or 'ntn' in content.lower():
                    return True
            except:
                continue
        return False

    def _calculate_compliance_score(self, violations: List[Dict], requirements: List[Dict]) -> float:
        """計算合規性分數 (0-100)"""
        # 基礎分數
        base_score = 100.0

        # 違規扣分
        for violation in violations:
            if violation['severity'] == 'critical':
                base_score -= 25.0
            elif violation['severity'] == 'major':
                base_score -= 10.0
            elif violation['severity'] == 'minor':
                base_score -= 5.0

        # 要求未滿足扣分
        unsatisfied_requirements = [r for r in requirements if r['status'] == 'not_satisfied']
        for req in unsatisfied_requirements:
            if req['critical']:
                base_score -= 15.0
            else:
                base_score -= 5.0

        return max(0.0, base_score)

    def _determine_grade_level(self, compliance_score: float, violations: List[Dict]) -> str:
        """確定評級等級"""
        critical_violations = [v for v in violations if v['severity'] == 'critical']

        if critical_violations:
            return "Grade F - 嚴重違規"
        elif compliance_score >= 95.0:
            return "Grade A - 學術級合規"
        elif compliance_score >= 85.0:
            return "Grade B - 標準合規"
        elif compliance_score >= 70.0:
            return "Grade C - 基本合規"
        else:
            return "Grade D - 需要改進"

    def _calculate_performance_metrics(self, stage_path: Path) -> Dict[str, float]:
        """計算性能指標"""
        metrics = {
            'total_files': 0,
            'total_lines': 0,
            'avg_file_size_kb': 0.0,
            'complexity_score': 0.0
        }

        total_size = 0
        for py_file in stage_path.rglob("*.py"):
            try:
                metrics['total_files'] += 1
                content = py_file.read_text(encoding='utf-8')
                lines = len(content.splitlines())
                metrics['total_lines'] += lines

                file_size = py_file.stat().st_size
                total_size += file_size

                # 簡單的複雜度評估（基於函數和類的數量）
                functions = content.count('def ')
                classes = content.count('class ')
                metrics['complexity_score'] += (functions * 2 + classes * 5)

            except Exception:
                continue

        if metrics['total_files'] > 0:
            metrics['avg_file_size_kb'] = total_size / metrics['total_files'] / 1024
            metrics['complexity_score'] = metrics['complexity_score'] / metrics['total_files']

        return metrics

    def _check_for_new_violations(self, stage: str, snapshot: ValidationSnapshot):
        """檢查新的違規"""
        if stage in self.last_snapshots:
            old_violations = {v['type'] + v['file'] for v in self.last_snapshots[stage].violations}
            new_violations = {v['type'] + v['file'] for v in snapshot.violations}

            added_violations = new_violations - old_violations
            if added_violations:
                self.logger.warning(f"{stage} 發現新違規: {len(added_violations)}項")

            removed_violations = old_violations - new_violations
            if removed_violations:
                self.logger.info(f"{stage} 修復違規: {len(removed_violations)}項")

    def _save_snapshot(self, snapshot: ValidationSnapshot):
        """保存快照到文件"""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{snapshot.stage}_validation_snapshot_{timestamp_str}.json"
        file_path = self.snapshots_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, ensure_ascii=False, indent=2)

        # 保持最新的快照
        latest_filename = f"{snapshot.stage}_validation_snapshot_latest.json"
        latest_path = self.snapshots_dir / latest_filename

        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, ensure_ascii=False, indent=2)

    def generate_compliance_dashboard(self) -> Dict[str, Any]:
        """生成合規性儀表板"""
        dashboard = {
            'system_overview': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_stages': len(self.last_snapshots),
                'overall_compliance_score': 0.0,
                'system_grade': 'Unknown'
            },
            'stage_summaries': [],
            'critical_violations': [],
            'improvement_recommendations': []
        }

        if self.last_snapshots:
            total_score = sum(s.compliance_score for s in self.last_snapshots.values())
            dashboard['system_overview']['overall_compliance_score'] = total_score / len(self.last_snapshots)

            # 收集所有嚴重違規
            for stage, snapshot in self.last_snapshots.items():
                stage_summary = {
                    'stage': stage,
                    'compliance_score': snapshot.compliance_score,
                    'grade_level': snapshot.grade_level,
                    'violations_count': len(snapshot.violations),
                    'last_updated': snapshot.timestamp
                }
                dashboard['stage_summaries'].append(stage_summary)

                # 收集嚴重違規
                critical_violations = [v for v in snapshot.violations if v['severity'] == 'critical']
                dashboard['critical_violations'].extend(critical_violations)

        # 確定系統整體評級
        overall_score = dashboard['system_overview']['overall_compliance_score']
        if dashboard['critical_violations']:
            dashboard['system_overview']['system_grade'] = "Grade F - 系統級違規"
        elif overall_score >= 95.0:
            dashboard['system_overview']['system_grade'] = "Grade A - 學術級系統"
        elif overall_score >= 85.0:
            dashboard['system_overview']['system_grade'] = "Grade B - 標準系統"
        else:
            dashboard['system_overview']['system_grade'] = "Grade C - 需要改進"

        return dashboard

    def create_immediate_snapshot(self, stage: Optional[str] = None) -> Dict[str, ValidationSnapshot]:
        """立即創建快照（用於按需驗證）"""
        if stage:
            snapshot = self._create_stage_snapshot(stage)
            self._save_snapshot(snapshot)
            return {stage: snapshot}
        else:
            snapshots = {}
            stages = [
                "stage1_orbital_calculation",
                "stage2_orbital_computing",
                "stage3_signal_analysis",
                "stage4_optimization",
                "stage5_data_integration",
                "stage6_persistence_api"
            ]

            for stage_name in stages:
                try:
                    snapshot = self._create_stage_snapshot(stage_name)
                    self._save_snapshot(snapshot)
                    snapshots[stage_name] = snapshot
                except Exception as e:
                    self.logger.error(f"創建{stage_name}快照失敗: {e}")

            return snapshots

def main():
    """測試實時驗證系統"""
    monitor = RealTimeValidationMonitor()

    # 創建立即快照
    print("🔍 創建即時驗證快照...")
    snapshots = monitor.create_immediate_snapshot()

    # 生成儀表板
    dashboard = monitor.generate_compliance_dashboard()

    print(f"\n📊 系統合規性儀表板:")
    print(f"   整體評級: {dashboard['system_overview']['system_grade']}")
    print(f"   合規性分數: {dashboard['system_overview']['overall_compliance_score']:.1f}")
    print(f"   嚴重違規: {len(dashboard['critical_violations'])}項")

    for stage_summary in dashboard['stage_summaries']:
        print(f"   {stage_summary['stage']}: {stage_summary['grade_level']} ({stage_summary['compliance_score']:.1f})")

    return dashboard

if __name__ == "__main__":
    main()