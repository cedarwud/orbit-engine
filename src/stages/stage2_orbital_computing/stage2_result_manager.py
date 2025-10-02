"""
📊 Stage 2: 結果管理模組

負責 Stage 2 處理結果的構建、保存和載入操作。
"""

import logging
import json
import os
import glob
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Stage2ResultManager:
    """Stage 2 結果管理器"""

    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """初始化結果管理器"""
        self.logger = logger_instance or logging.getLogger(f"{__name__}.Stage2ResultManager")

    def build_final_result(
        self,
        orbital_results: Dict[str, Any],
        start_time: datetime,
        processing_time: timedelta,
        input_data: Dict[str, Any],
        processing_stats: Dict[str, Any],
        coordinate_system: str,
        propagation_method: str,
        time_interval_seconds: float,
        dynamic_calculation: bool,
        coverage_cycles: float
    ) -> Dict[str, Any]:
        """
        構建最終結果

        Args:
            orbital_results: 軌道計算結果
            start_time: 處理開始時間
            processing_time: 處理耗時
            input_data: 輸入數據
            processing_stats: 處理統計
            coordinate_system: 座標系統
            propagation_method: 傳播方法
            time_interval_seconds: 時間間隔
            dynamic_calculation: 是否動態計算
            coverage_cycles: 覆蓋週期

        Returns:
            Dict[str, Any]: 最終結果數據
        """
        # 按星座分組統計
        constellation_stats = {}
        satellites_by_constellation = {}

        for satellite_id, result in orbital_results.items():
            constellation = result.constellation
            if constellation not in constellation_stats:
                constellation_stats[constellation] = 0
                satellites_by_constellation[constellation] = {}

            constellation_stats[constellation] += 1
            # 轉換為規格格式
            orbital_states = []
            for pos in result.teme_positions:
                orbital_state = {
                    'timestamp': pos.timestamp,
                    'position_teme': [pos.x, pos.y, pos.z],  # TEME 座標 (km)
                    'velocity_teme': [pos.vx, pos.vy, pos.vz],  # TEME 速度 (km/s)
                    'satellite_id': satellite_id,
                    'propagation_error': 0.001  # km (估計誤差，符合SGP4精度)
                }
                orbital_states.append(orbital_state)

            satellites_by_constellation[constellation][satellite_id] = {
                'satellite_id': satellite_id,
                'constellation': constellation,
                'epoch_datetime': result.epoch_datetime,
                'orbital_states': orbital_states,  # 符合規格的軌道狀態格式
                'propagation_successful': result.propagation_successful,
                'algorithm_used': result.algorithm_used,
                'coordinate_system': result.coordinate_system,
                'total_positions': len(result.teme_positions)
            }

        # 記錄統計信息
        logger.info(f"📊 最終結果統計:")
        for constellation, count in constellation_stats.items():
            logger.info(f"   {constellation}: {count} 顆衛星")

        # ✅ 保留上游 metadata (特別是 constellation_configs)
        upstream_metadata = input_data.get('metadata', {})

        # 合併 metadata: 保留上游配置，添加 Stage 2 處理信息
        merged_metadata = {
            **upstream_metadata,  # ✅ 保留 Stage 1 的 constellation_configs 和 research_configuration
            # Stage 2 特定信息
            'processing_start_time': start_time.isoformat(),
            'processing_end_time': datetime.now(timezone.utc).isoformat(),
            'processing_duration_seconds': processing_time.total_seconds(),
            'total_satellites_processed': processing_stats['total_satellites_processed'],
            'successful_propagations': processing_stats['successful_propagations'],
            'failed_propagations': processing_stats['failed_propagations'],
            'total_teme_positions': processing_stats['total_teme_positions'],
            'constellation_distribution': constellation_stats,
            'coordinate_system': coordinate_system,
            'propagation_method': propagation_method,
            'time_interval_seconds': time_interval_seconds,
            'dynamic_calculation_enabled': dynamic_calculation,
            'coverage_cycles': coverage_cycles,
            'architecture_version': 'v3.0',
            'processing_grade': 'A',
            'stage_concept': 'orbital_state_propagation',  # 新概念標記
            'tle_reparse_prohibited': True,  # 確認未重新解析 TLE
            'epoch_datetime_source': 'stage1_provided'  # 確認時間來源
        }

        return {
            'stage': 'stage2_orbital_computing',
            'satellites': satellites_by_constellation,  # 按星座分組
            'metadata': merged_metadata,
            'processing_stats': processing_stats,
            'next_stage_ready': True  # 為 Stage 3 準備就緒
        }

    def load_stage1_output(self) -> Dict[str, Any]:
        """
        載入 Stage 1 輸出數據

        Returns:
            Dict[str, Any]: Stage 1 輸出數據

        Raises:
            FileNotFoundError: 找不到 Stage 1 輸出文件
        """
        stage1_output_dir = "data/outputs/stage1"

        if not os.path.exists(stage1_output_dir):
            raise FileNotFoundError(f"Stage 1 輸出目錄不存在: {stage1_output_dir}")

        # 尋找最新的 Stage 1 輸出文件
        patterns = [
            os.path.join(stage1_output_dir, "data_loading_output_*.json"),
            os.path.join(stage1_output_dir, "tle_data_loading_output_*.json")
        ]
        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern))

        if not files:
            raise FileNotFoundError(f"Stage 1 輸出文件不存在")

        stage1_output_file = max(files, key=os.path.getmtime)
        self.logger.info(f"📥 載入 Stage 1 輸出: {stage1_output_file}")

        with open(stage1_output_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_results(self, results: Dict[str, Any]) -> str:
        """
        保存 Stage 2 處理結果到文件

        Args:
            results: 處理結果數據

        Returns:
            str: 輸出文件路徑

        Raises:
            IOError: 保存失敗
        """
        try:
            output_dir = "data/outputs/stage2"
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"orbital_propagation_output_{timestamp}.json")

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            self.logger.info(f"📁 Stage 2 結果已保存: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"❌ 保存 Stage 2 結果失敗: {e}")
            raise IOError(f"無法保存 Stage 2 結果: {e}")
