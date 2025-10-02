from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone
import logging
import json
import asyncio
import os

# 導入BaseProcessor接口
from .interfaces.processor_interface import BaseProcessor, ProcessingResult, ProcessingStatus, create_processing_result

class BaseStageProcessor(BaseProcessor):
    """所有階段處理器的基礎抽象類"""
    
    def __init__(self, stage_number: int, stage_name: str, config: Optional[Dict] = None):
        """
        初始化基礎處理器
        
        Args:
            stage_number: 階段編號 (1-6)
            stage_name: 階段名稱
            config: 配置參數
        """
        # 首先調用BaseProcessor的初始化
        super().__init__(processor_name=f"stage{stage_number}_{stage_name}", config=config or {})
        
        self.stage_number = stage_number
        self.stage_name = stage_name
        
        # 處理時間追蹤
        self.processing_start_time: Optional[datetime] = None
        self.processing_end_time: Optional[datetime] = None
        self.processing_duration: float = 0.0
        
        # 統一日誌
        self.logger = logging.getLogger(f"stage{stage_number}_{stage_name}")
        
        # 🚨 重要：強制 Orbit Engine 容器內執行 - 統一執行環境
        # 架構決策：只支援容器執行，避免路徑和環境不一致問題
        # 🧪 測試模式：允許跳過容器檢查
        if not os.environ.get('ORBIT_ENGINE_TEST_MODE'):
            from .constants.system_constants import OrbitEngineSystemPaths

            if not Path(OrbitEngineSystemPaths.CONTAINER_ROOT).exists():
                raise RuntimeError(
                    "🚫 Orbit Engine 必須在容器內執行！\n"
                    "正確執行方式：\n"
                    "  docker exec orbit-engine-dev bash\n"
                    f"  cd {OrbitEngineSystemPaths.CONTAINER_ROOT} && python scripts/run_six_stages_with_validation.py\n"
                    "\n"
                    "測試模式：\n"
                    "  export ORBIT_ENGINE_TEST_MODE=1\n"
                    "\n"
                    "原因：\n"
                "- 確保執行環境一致性\n"
                "- 避免路徑混亂和數據分散\n"
                "- 簡化維護和除錯複雜度\n"
                f"- 統一 Orbit Engine 路徑規範: {OrbitEngineSystemPaths.CONTAINER_ROOT}"
            )

        # 容器環境 - 使用統一的 Orbit Engine 路徑配置
        from .constants.system_constants import get_current_paths
        current_paths = get_current_paths()

        self.output_dir = Path(current_paths[f'stage{stage_number}_output'])
        self.validation_dir = Path(current_paths['validation_snapshots'])

        self.logger.info(f"🚀 Orbit Engine 容器執行確認 - 輸出路徑: {self.output_dir}")
        self.logger.info(f"📂 Volume映射: 容器{self.output_dir} → 主機./data/outputs/stage{stage_number}")
        self.logger.info(f"📋 驗證快照路徑: {self.validation_dir}")
        self.logger.info(f"🌍 執行環境: {current_paths['environment']}")
        
        self._initialize_directories()
        self._load_configuration()

    def execute(self, input_data: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        執行階段處理流程
        
        Args:
            input_data: 輸入數據
            
        Returns:
            ProcessingResult: 處理結果
        """
        try:
            self.logger.info(f"開始執行 Stage {self.stage_number}: {self.stage_name}")
            
            # 記錄開始時間
            self.processing_start_time = datetime.now(timezone.utc)
            self._start_processing()
            
            # 輸入驗證
            if input_data is not None:
                validation_result = self.validate_input(input_data)
                if not validation_result.get('valid', False):
                    error_msg = f"輸入驗證失敗: {validation_result.get('errors', [])}"
                    self.logger.error(error_msg)
                    self._end_processing(ProcessingStatus.VALIDATION_FAILED)
                    return create_processing_result(
                        status=ProcessingStatus.VALIDATION_FAILED,
                        data={},
                        metadata={'stage': self.stage_number, 'validation_errors': validation_result.get('errors', [])},
                        message=error_msg
                    )
            
            # 執行主處理邏輯
            result = self.process(input_data)
            
            # 輸出驗證 - 使用完整的result.data和metadata合併進行驗證
            if result.status == ProcessingStatus.SUCCESS and result.data:
                # 為輸出驗證創建完整的數據結構，包含metadata
                validation_data = result.data.copy()
                if 'metadata' not in validation_data and result.metadata:
                    validation_data['metadata'] = result.metadata
                
                output_validation = self.validate_output(validation_data)
                if not output_validation.get('valid', False):
                    error_msg = f"輸出驗證失敗: {output_validation.get('errors', [])}"
                    self.logger.error(error_msg)
                    result.status = ProcessingStatus.VALIDATION_FAILED
                    result.metadata.update({'output_validation_errors': output_validation.get('errors', [])})
                    result.message = error_msg
            
            # 記錄結束時間
            self.processing_end_time = datetime.now(timezone.utc)
            if self.processing_start_time:
                self.processing_duration = (self.processing_end_time - self.processing_start_time).total_seconds()
            
            self._end_processing(result.status)
            
            self.logger.info(f"Stage {self.stage_number} 執行完成，耗時: {self.processing_duration:.2f}秒")
            
            # 更新結果metadata
            result.metadata.update({
                'stage': self.stage_number,
                'stage_name': self.stage_name,
                'processing_duration': self.processing_duration,
                'start_time': self.processing_start_time.isoformat() if self.processing_start_time else None,
                'end_time': self.processing_end_time.isoformat() if self.processing_end_time else None
            })
            
            # 保存輸出文件和驗證快照（無論成功或失敗都生成快照）
            try:
                # 如果處理成功，保存輸出文件
                if result.status == ProcessingStatus.SUCCESS:
                    # 調用子類的save_results方法（如果存在）
                    if hasattr(self, 'save_results'):
                        # 為保存創建完整的數據結構
                        save_data = result.data.copy()
                        save_data['metadata'] = result.metadata
                        output_path = self.save_results(save_data)
                        result.metadata['output_file'] = output_path
                        self.logger.info(f"✅ 輸出已保存至: {output_path}")

                # 🔧 重要修改：無論成功或失敗都創建驗證快照
                # ✅ P0-1 修復: 優先調用子類的 save_validation_snapshot (如果存在)
                if hasattr(self, 'save_validation_snapshot') and callable(getattr(self, 'save_validation_snapshot')):
                    # 子類實現了專用的 save_validation_snapshot 方法
                    try:
                        self.save_validation_snapshot(result.data)
                        self.logger.info(f"✅ 使用子類專用驗證快照方法")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 子類驗證快照失敗，回退到基礎方法: {e}")
                        self._save_validation_snapshot(result)
                else:
                    # 使用基礎快照方法
                    self._save_validation_snapshot(result)

            except Exception as save_error:
                self.logger.warning(f"⚠️ 保存輸出時出現警告: {save_error}")
                # 不影響主處理結果，只記錄警告
            
            return result
            
        except Exception as e:
            error_msg = f"Stage {self.stage_number} 執行異常: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            self.processing_end_time = datetime.now(timezone.utc)
            if self.processing_start_time:
                self.processing_duration = (self.processing_end_time - self.processing_start_time).total_seconds()
            
            self._end_processing(ProcessingStatus.FAILED)
            
            return create_processing_result(
                status=ProcessingStatus.FAILED,
                data={},
                metadata={
                    'stage': self.stage_number,
                    'stage_name': self.stage_name,
                    'error': str(e),
                    'processing_duration': self.processing_duration
                },
                message=error_msg
            )

    def _save_validation_snapshot(self, result: ProcessingResult) -> None:
        """
        保存驗證快照
        
        Args:
            result: 處理結果
        """
        try:
            validation_snapshot = {
                'stage': self.stage_number,
                'stage_name': self.stage_name,
                'status': result.status.value,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'processing_duration': self.processing_duration,
                'data_summary': {
                    'has_data': bool(result.data),
                    'data_keys': list(result.data.keys()) if result.data else [],
                    'metadata_keys': list(result.metadata.keys()) if result.metadata else []
                },
                'validation_passed': result.status == ProcessingStatus.SUCCESS,
                'errors': result.errors,
                'warnings': result.warnings
            }
            
            # 添加階段特定的數據摘要
            if result.data and isinstance(result.data, dict):
                # Stage 1 特殊處理
                if self.stage_number == 1:
                    satellite_count = len(result.data.get('satellites', []))
                    validation_snapshot['data_summary']['satellite_count'] = satellite_count
                    validation_snapshot['next_stage_ready'] = satellite_count > 0 and result.status == ProcessingStatus.SUCCESS
                    validation_snapshot['refactored_version'] = True
                    validation_snapshot['interface_compliance'] = True

                    # ✅ 添加完整 metadata 用於驗證腳本檢查
                    validation_snapshot['metadata'] = result.data.get('metadata', {})

                    # ✅ 添加衛星樣本用於 epoch_datetime 獨立性驗證
                    satellites = result.data.get('satellites', [])
                    satellites_sample = satellites[:10] if len(satellites) > 10 else satellites
                    validation_snapshot['satellites_sample'] = satellites_sample

                elif 'tle_data' in result.data:
                    validation_snapshot['data_summary']['satellite_count'] = len(result.data['tle_data'])

                if 'next_stage_ready' in result.data:
                    validation_snapshot['next_stage_ready'] = result.data['next_stage_ready']
            
            # 保存驗證快照
            snapshot_filename = f"stage{self.stage_number}_validation.json"
            snapshot_path = self.validation_dir / snapshot_filename
            
            import json
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(validation_snapshot, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📋 驗證快照已保存至: {snapshot_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存驗證快照失敗: {e}")

    def _initialize_directories(self) -> None:
        """初始化輸出目錄"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_configuration(self) -> None:
        """載入配置參數"""
        # 從配置文件或環境變量載入參數
        pass
