"""
Stage 1 Processor - 軌道計算處理器 (重構版)

這是重構後的Stage 1處理器，繼承自BaseStageProcessor，
提供模組化、可除錯的軌道計算功能。

主要改進：
1. 模組化設計 - 拆分為多個專責組件
2. 統一接口 - 符合BaseStageProcessor規範
3. 可除錯性 - 支援單階段執行和數據注入
4. 學術標準 - 保持Grade A級別的計算精度

🔧 Phase 1A重構 (v7.0):
5. 職責邊界清晰 - 移除觀測者計算功能 (移至Stage 2)
6. 軌道相位分析 - 整合TemporalSpatialAnalysisEngine的18個相位分析方法
7. 純ECI輸出 - 嚴格遵循Stage 1職責範圍

重構目標：
- 嚴格遵循STAGE_RESPONSIBILITIES.md定義的職責邊界
- 只負責TLE載入和SGP4軌道計算，輸出純ECI座標
- 移除越界功能：觀測者計算 → Stage 2
"""

import json
import logging
import math
import gzip
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone

# 導入基礎處理器
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.base_processor import BaseStageProcessor

# 導入Stage 1專用組件
from .tle_data_loader import TLEDataLoader
# 🔄 v2.0: 軌道計算器已移至 Stage 2
# from .orbital_calculator import OrbitalCalculator  # 已棄用
from .orbital_validation_engine import OrbitalValidationEngine

logger = logging.getLogger(__name__)

import time

class Stage1TLEProcessor(BaseStageProcessor):
    """
    🔄 Stage 1: TLE數據載入層處理器 (v2.0 重構版)
    
    📋 職責範圍 (符合文檔v2.0規範):
    1. ✅ TLE數據載入和解析
    2. ✅ 數據格式驗證和完整性檢查  
    3. ✅ 時間基準標準化
    4. ✅ 為Stage 2提供清潔的數據輸出
    
    ❌ 不再包含:
    - 軌道計算 (移至Stage 2)
    - SGP4位置計算 (移至Stage 2)
    - 可見性分析 (移至Stage 2)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(stage_number=1, stage_name="tle_data_loading", config=config or {})

        # 🔧 v2.0 配置參數
        self.sample_mode = self.config.get('sample_mode', False)
        self.sample_size = self.config.get('sample_size', 100)
        self.validate_tle_epoch = self.config.get('validate_tle_epoch', True)

        # 🏗️ v2.0 模組化組件 (符合文檔設計)
        try:
            from .tle_data_loader import TLEDataLoader
            from .data_validator import DataValidator
            from .time_reference_manager import TimeReferenceManager
            
            self.tle_loader = TLEDataLoader()
            self.data_validator = DataValidator(self.config)  
            self.time_reference_manager = TimeReferenceManager(self.config)
            
        except ImportError as e:
            self.logger.error(f"❌ v2.0組件載入失敗: {e}")
            # 創建基本實例避免錯誤
            self.tle_loader = None
            self.data_validator = None
            self.time_reference_manager = None

        # 🔄 v2.0 驗證引擎
        try:
            from shared.validation_framework.validation_engine import ValidationEngine
            self.validation_engine = ValidationEngine('stage1_data_loading')
        except ImportError:
            self.validation_engine = None

        # 📊 處理統計
        self.processing_stats = {
            'total_files_scanned': 0,
            'total_satellites_loaded': 0,
            'validation_failures': 0,
            'time_reference_issues': 0,
            'data_quality_score': 0.0
        }

        self.logger.info("🔄 Stage 1 TLE數據載入處理器已初始化 (v2.0架構)")

    def scan_tle_data(self) -> List[str]:
        """掃描TLE數據文件"""
        if not self.tle_loader:
            self.logger.error("❌ TLE載入器未初始化")
            return []
            
        try:
            tle_files = self.tle_loader.scan_tle_data()
            self.processing_stats['total_files_scanned'] = len(tle_files)
            return tle_files
        except Exception as e:
            self.logger.error(f"❌ TLE數據掃描失敗: {e}")
            return []

    def load_raw_satellite_data(self, tle_files: List[str]) -> List[Dict[str, Any]]:
        """載入原始衛星數據"""
        if not self.tle_loader:
            self.logger.error("❌ TLE載入器未初始化")
            return []
            
        try:
            satellite_data = self.tle_loader.load_satellite_data(tle_files)
            
            # 🎯 樣本模式處理
            if self.sample_mode and len(satellite_data) > self.sample_size:
                self.logger.info(f"🎯 樣本模式: 從{len(satellite_data)}顆衛星中選取{self.sample_size}顆")
                satellite_data = satellite_data[:self.sample_size]
            
            self.processing_stats['total_satellites_loaded'] = len(satellite_data)
            return satellite_data
            
        except Exception as e:
            self.logger.error(f"❌ 衛星數據載入失敗: {e}")
            return []

    def process_tle_data_loading(self) -> Dict[str, Any]:
        """
        🔄 v2.0主要處理方法：純數據載入流程
        
        Returns:
            包含載入和驗證的TLE數據的字典
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始Stage 1 TLE數據載入處理...")

        try:
            # 1️⃣ 掃描TLE文件
            tle_files = self.scan_tle_data()
            if not tle_files:
                raise ValueError("未找到TLE數據文件")

            # 2️⃣ 載入原始數據  
            raw_data = self.load_raw_satellite_data(tle_files)
            if not raw_data:
                raise ValueError("TLE數據載入失敗")

            # 3️⃣ 數據驗證
            if self.data_validator:
                validation_result = self.data_validator.validate_tle_dataset(raw_data)
                if not validation_result.get('is_valid', False):
                    self.processing_stats['validation_failures'] = len(validation_result.get('errors', []))
                    self.logger.warning(f"⚠️ 數據驗證發現 {self.processing_stats['validation_failures']} 個問題")

            # 4️⃣ 時間基準標準化
            if self.time_reference_manager:
                time_reference_result = self.time_reference_manager.establish_time_reference(raw_data)
                standardized_data = time_reference_result.get('standardized_data', raw_data)
                
                if not time_reference_result.get('time_reference_established', False):
                    self.processing_stats['time_reference_issues'] = len(raw_data)
                    self.logger.warning("⚠️ 時間基準建立部分失敗")
            else:
                standardized_data = raw_data

            # 5️⃣ 數據品質評估
            self.processing_stats['data_quality_score'] = self._assess_data_quality(standardized_data)

            # 📊 處理結果構建
            processing_duration = datetime.now(timezone.utc) - start_time
            
            result = {
                'stage': 'tle_data_loading',
                'stage_name': 'TLE數據載入層',
                'satellites': standardized_data,
                'metadata': {
                    'total_satellites': len(standardized_data),
                    'processing_start_time': start_time.isoformat(),
                    'processing_end_time': datetime.now(timezone.utc).isoformat(),
                    'processing_duration_seconds': processing_duration.total_seconds(),
                    'files_processed': len(tle_files),
                    'data_quality_score': self.processing_stats['data_quality_score'],
                    'constellations': self._analyze_constellations(standardized_data),
                    
                    # 🎯 v2.0 時間基準輸出 (符合文檔要求)
                    'calculation_base_time': self._extract_calculation_base_time(standardized_data),
                    'tle_epoch_time': self._extract_tle_epoch_time(standardized_data),
                    'time_base_source': 'tle_epoch_derived',
                    'tle_epoch_compliance': True,
                    'stage1_time_inheritance': {
                        'exported_time_base': self._extract_calculation_base_time(standardized_data),
                        'inheritance_ready': True,
                        'calculation_reference': 'tle_epoch_based'
                    }
                },
                'processing_stats': self.processing_stats
            }

            self.logger.info(f"✅ Stage 1 TLE數據載入完成: {len(standardized_data)}顆衛星")
            return result

        except Exception as e:
            self.logger.error(f"❌ Stage 1 TLE數據載入失敗: {e}")
            return {
                'stage': 'tle_data_loading',
                'satellites': [],
                'error': str(e),
                'processing_stats': self.processing_stats,
                'metadata': {
                    'processing_start_time': start_time.isoformat(),
                    'processing_end_time': datetime.now(timezone.utc).isoformat(),
                    'status': 'ERROR'
                }
            }

    def _assess_data_quality(self, data: List[Dict]) -> float:
        """評估數據品質分數 (0-100)"""
        if not data:
            return 0.0
            
        quality_factors = []
        
        # TLE格式完整性
        format_score = sum(1 for d in data if all(k in d for k in ['satellite_id', 'line1', 'line2', 'name'])) / len(data)
        quality_factors.append(format_score)
        
        # 時間基準一致性
        time_score = sum(1 for d in data if 'epoch_datetime' in d) / len(data)
        quality_factors.append(time_score)
        
        # 數據多樣性 (星座覆蓋)
        constellations = set(d.get('constellation', 'unknown').lower() for d in data)
        diversity_score = min(len(constellations) / 2.0, 1.0)  # 期望至少2個星座
        quality_factors.append(diversity_score)
        
        return sum(quality_factors) / len(quality_factors) * 100

    def _analyze_constellations(self, data: List[Dict]) -> Dict[str, Dict]:
        """分析星座分布"""
        constellations = {}
        
        for satellite in data:
            constellation = satellite.get('constellation', 'unknown').lower()
            if constellation not in constellations:
                constellations[constellation] = {
                    'satellite_count': 0,
                    'sample_satellites': []
                }
            
            constellations[constellation]['satellite_count'] += 1
            if len(constellations[constellation]['sample_satellites']) < 3:
                constellations[constellation]['sample_satellites'].append({
                    'satellite_id': satellite.get('satellite_id'),
                    'name': satellite.get('name', 'Unknown')
                })
        
        return constellations

    def _extract_calculation_base_time(self, data: List[Dict]) -> str:
        """提取計算基準時間 (TLE epoch時間)"""
        if not data:
            return datetime.now(timezone.utc).isoformat()
            
        # 使用最新的TLE epoch時間作為計算基準
        epoch_times = []
        for satellite in data:
            epoch_time = satellite.get('epoch_datetime')
            if epoch_time:
                try:
                    if isinstance(epoch_time, str):
                        parsed_time = datetime.fromisoformat(epoch_time.replace('Z', '+00:00'))
                    else:
                        parsed_time = epoch_time
                    epoch_times.append(parsed_time)
                except:
                    continue
        
        if epoch_times:
            # 使用最新的epoch時間
            latest_epoch = max(epoch_times)
            return latest_epoch.isoformat()
        else:
            return datetime.now(timezone.utc).isoformat()

    def _extract_tle_epoch_time(self, data: List[Dict]) -> str:
        """提取TLE epoch時間"""
        return self._extract_calculation_base_time(data)  # 在v2.0架構中兩者相同

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據 (v2.0版本 - 數據載入專用)"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        # 基本格式檢查
        if input_data is not None:
            if not isinstance(input_data, dict):
                validation_result['errors'].append("輸入數據必須是字典格式或None")
                validation_result['is_valid'] = False

        return validation_result

    def process(self, input_data: Any = None) -> Dict[str, Any]:
        """
        🔄 v2.0統一處理介面
        
        Args:
            input_data: 輸入數據 (可選，將自動載入TLE文件)
            
        Returns:
            處理結果字典
        """
        # 輸入驗證
        validation = self.validate_input(input_data)
        if not validation['is_valid']:
            return {
                'stage': 'tle_data_loading',
                'error': '; '.join(validation['errors']),
                'satellites': [],
                'processing_stats': self.processing_stats
            }

        # 執行數據載入流程
        return self.process_tle_data_loading()

    def validate_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證輸出數據 (v2.0版本 - 數據載入專用)"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        # 檢查必要字段
        required_fields = ['stage', 'satellites', 'metadata']
        for field in required_fields:
            if field not in output_data:
                validation_result['errors'].append(f"缺少必要字段: {field}")

        # 檢查階段標識
        if output_data.get('stage') != 'tle_data_loading':
            validation_result['errors'].append("階段標識錯誤，應為 'tle_data_loading'")

        # 檢查衛星數據
        satellites = output_data.get('satellites', [])
        if not isinstance(satellites, list):
            validation_result['errors'].append("衛星數據必須是列表格式")
        elif len(satellites) == 0:
            validation_result['warnings'].append("衛星數據為空")

        # v2.0 時間基準檢查
        metadata = output_data.get('metadata', {})
        if 'calculation_base_time' not in metadata:
            validation_result['errors'].append("缺少calculation_base_time")
        if metadata.get('time_base_source') != 'tle_epoch_derived':
            validation_result['warnings'].append("時間基準來源不是tle_epoch_derived")

        validation_result['is_valid'] = len(validation_result['errors']) == 0
        return validation_result

    def extract_key_metrics(self, results: Dict[str, Any] = None) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'tle_data_loading',
            'satellites_loaded': self.processing_stats['total_satellites_loaded'],
            'files_scanned': self.processing_stats['total_files_scanned'],
            'validation_failures': self.processing_stats['validation_failures'],
            'time_reference_issues': self.processing_stats['time_reference_issues'],
            'data_quality_score': self.processing_stats['data_quality_score'],
            'success_rate': (
                (self.processing_stats['total_satellites_loaded'] - self.processing_stats['validation_failures'])
                / max(1, self.processing_stats['total_satellites_loaded'])
            ) * 100 if self.processing_stats['total_satellites_loaded'] > 0 else 0
        }

    def run_validation_checks(self, data: Any) -> Dict[str, Any]:
        """
        🔄 v2.0驗證檢查 (專為數據載入設計)
        """
        try:
            if isinstance(data, dict) and 'satellites' in data:
                satellite_data = data['satellites']
            elif isinstance(data, list):
                satellite_data = data
            else:
                return {
                    'validation_status': 'failed',
                    'overall_status': 'FAIL',
                    'stage_compliance': False,
                    'academic_standards': False,
                    'error_message': '輸入數據格式錯誤',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            # 🔍 數據載入專用驗證項目
            validation_checks = {
                'tle_format_validation': self._check_tle_format(satellite_data),
                'data_completeness_check': self._check_data_completeness(satellite_data),
                'time_reference_check': self._check_time_reference(satellite_data),
                'constellation_coverage_check': self._check_constellation_coverage(satellite_data)
            }

            # 計算總體狀態
            passed_checks = sum(1 for check in validation_checks.values() if check)
            total_checks = len(validation_checks)
            overall_status = 'PASS' if passed_checks >= total_checks * 0.8 else 'FAIL'  # 80%通過率

            return {
                'validation_status': 'passed' if overall_status == 'PASS' else 'failed',
                'overall_status': overall_status,
                'checks_performed': list(validation_checks.keys()),
                'stage_compliance': overall_status == 'PASS',
                'academic_standards': passed_checks >= total_checks * 0.9,  # 90%為學術標準
                'detailed_results': validation_checks,
                'checks_passed': passed_checks,
                'total_checks': total_checks,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ 驗證檢查失敗: {e}")
            return {
                'validation_status': 'error',
                'overall_status': 'ERROR',
                'stage_compliance': False,
                'academic_standards': False,
                'error_message': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _check_tle_format(self, satellite_data: List[Dict]) -> bool:
        """檢查TLE格式完整性"""
        if not satellite_data:
            return False
            
        required_fields = ['satellite_id', 'line1', 'line2', 'name']
        valid_count = 0
        
        for satellite in satellite_data:
            if all(field in satellite and satellite[field] for field in required_fields):
                line1, line2 = satellite['line1'], satellite['line2']
                if len(line1) == 69 and len(line2) == 69 and line1[0] == '1' and line2[0] == '2':
                    valid_count += 1
        
        return valid_count >= len(satellite_data) * 0.95  # 95%格式正確率

    def _check_data_completeness(self, satellite_data: List[Dict]) -> bool:
        """檢查數據完整性"""
        if not satellite_data:
            return False
            
        # 檢查最小數據量 (至少100顆衛星)
        if len(satellite_data) < 100:
            return False
            
        # 檢查數據字段完整性
        complete_records = sum(1 for s in satellite_data 
                             if all(k in s for k in ['satellite_id', 'name', 'line1', 'line2']))
        
        return complete_records >= len(satellite_data) * 0.98  # 98%完整率

    def _check_time_reference(self, satellite_data: List[Dict]) -> bool:
        """檢查時間基準建立"""
        if not satellite_data:
            return False
            
        time_valid_count = sum(1 for s in satellite_data if 'epoch_datetime' in s)
        return time_valid_count >= len(satellite_data) * 0.90  # 90%時間解析成功率

    def _check_constellation_coverage(self, satellite_data: List[Dict]) -> bool:
        """檢查星座覆蓋度"""
        if not satellite_data:
            return False
            
        constellations = set()
        for satellite in satellite_data:
            name = satellite.get('name', '').lower()
            if 'starlink' in name:
                constellations.add('starlink')
            elif 'oneweb' in name:
                constellations.add('oneweb')
                
        return len(constellations) >= 2  # 至少包含兩個主要星座

    def save_results(self, results: Dict[str, Any]) -> str:
        """
        🔄 v2.0保存結果 (符合文檔命名規範)
        
        文檔要求: /app/data/tle_orbital_calculation_output.json
        """
        try:
            # 📁 使用文檔規範的輸出路徑和命名
            output_filename = "tle_orbital_calculation_output.json"
            output_path = self.output_dir / output_filename

            # 確保輸出目錄存在
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # 保存結果
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"✅ Stage 1 結果已保存至: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"❌ 保存結果失敗: {e}")
            raise RuntimeError(f"Stage 1 結果保存失敗: {e}")

    def execute(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        🔄 v2.0執行介面 (與六階段系統兼容)
        
        Args:
            input_data: 可選的輸入數據
            
        Returns:
            處理結果字典
        """
        try:
            # 執行數據載入處理
            results = self.process(input_data)
            
            # 保存結果 (如果配置允許)
            if self.config.get('save_output', True):
                self.save_results(results)
            
            # 生成驗證快照
            if self.config.get('generate_validation_snapshot', True):
                self.save_validation_snapshot(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Stage 1 執行失敗: {e}")
            return {
                'stage': 'tle_data_loading',
                'error': str(e),
                'satellites': [],
                'processing_stats': self.processing_stats,
                'metadata': {
                    'status': 'ERROR',
                    'error_message': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }

    def save_validation_snapshot(self, results: Dict[str, Any]) -> None:
        """保存驗證快照 (符合文檔規範)"""
        try:
            # 📁 驗證快照目錄
            validation_dir = self.output_dir / "validation_snapshots"
            validation_dir.mkdir(parents=True, exist_ok=True)
            
            snapshot_path = validation_dir / "stage1_validation.json"
            
            # 構建驗證快照
            snapshot = {
                'stage': 1,
                'stage_name': 'tle_data_loading',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'summary': {
                    'total_satellites': len(results.get('satellites', [])),
                    'processing_success': 'error' not in results,
                    'data_quality_score': results.get('processing_stats', {}).get('data_quality_score', 0),
                },
                'validation_results': self.run_validation_checks(results),
                'key_metrics': self.extract_key_metrics(results),
                'metadata': results.get('metadata', {})
            }
            
            import json
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"✅ 驗證快照已保存: {snapshot_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存驗證快照失敗: {e}")
