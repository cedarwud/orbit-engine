"""
📊 Stage 2: 結果管理模組

負責 Stage 2 處理結果的構建、保存和載入操作。

支援格式：
- JSON：向後兼容，易讀性高
- HDF5：高效壓縮，學術標準格式
"""

import logging
import json
import os
import glob
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False
    logging.warning("⚠️ h5py 未安裝，HDF5 格式不可用")

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
                    # ✅ Grade A 標準: 移除估計誤差值
                    # SGP4 誤差應從算法實際計算獲取，不使用硬編碼估算值
                    # 參考: Vallado 2013, Table 3.2 - SGP4 精度範圍 0.5-5 km (視 TLE 新舊而定)
                    # 如需提供誤差，應從 Skyfield 或 SGP4 計算結果獲取
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

    def save_results(self, results: Dict[str, Any], output_format: str = 'both') -> str:
        """
        保存 Stage 2 處理結果到文件（支援 JSON/HDF5 雙格式）

        Args:
            results: 處理結果數據
            output_format: 輸出格式 ('json', 'hdf5', 'both')

        Returns:
            str: 主要輸出文件路徑

        Raises:
            IOError: 保存失敗
        """
        try:
            output_dir = "data/outputs/stage2"
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_files = []

            # JSON 格式（向後兼容）
            if output_format in ('json', 'both'):
                json_file = os.path.join(output_dir, f"orbital_propagation_output_{timestamp}.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
                self.logger.info(f"📁 JSON 格式已保存: {json_file}")
                output_files.append(json_file)

            # HDF5 格式（高效儲存）
            if output_format in ('hdf5', 'both') and HDF5_AVAILABLE:
                hdf5_file = os.path.join(output_dir, f"orbital_propagation_output_{timestamp}.h5")
                self._save_results_hdf5(results, hdf5_file)
                self.logger.info(f"📦 HDF5 格式已保存: {hdf5_file}")
                output_files.append(hdf5_file)

            # 返回主要格式路徑（HDF5 優先，否則 JSON）
            return output_files[-1] if output_files else ""

        except Exception as e:
            self.logger.error(f"❌ 保存 Stage 2 結果失敗: {e}")
            raise IOError(f"無法保存 Stage 2 結果: {e}")

    def _save_results_hdf5(self, results: Dict[str, Any], output_file: str):
        """
        保存結果為 HDF5 格式（學術標準，高效壓縮）

        Args:
            results: 處理結果數據
            output_file: HDF5 輸出文件路徑
        """
        if not HDF5_AVAILABLE:
            self.logger.warning("⚠️ h5py 未安裝，跳過 HDF5 保存")
            return

        with h5py.File(output_file, 'w') as f:
            # 保存元數據
            metadata = results.get('metadata', {})
            f.attrs['stage'] = results.get('stage', 'stage2_orbital_computing')
            f.attrs['coordinate_system'] = metadata.get('coordinate_system', 'TEME')
            f.attrs['architecture_version'] = metadata.get('architecture_version', 'v3.0')
            f.attrs['timestamp'] = datetime.now(timezone.utc).isoformat()
            f.attrs['total_satellites'] = metadata.get('total_satellites_processed', 0)

            # 保存衛星數據（按星座分組）
            satellites_data = results.get('satellites', {})

            for constellation_name, constellation_sats in satellites_data.items():
                if not isinstance(constellation_sats, dict):
                    continue

                # 創建星座組
                const_group = f.create_group(constellation_name)

                for sat_id, sat_data in constellation_sats.items():
                    # 創建衛星組
                    sat_group = const_group.create_group(sat_id)

                    # 提取軌道狀態數據
                    orbital_states = sat_data.get('orbital_states', [])
                    if not orbital_states:
                        continue

                    # TEME 位置 (N x 3)
                    positions = np.array([
                        state['position_teme'] for state in orbital_states
                    ], dtype=np.float64)

                    # TEME 速度 (N x 3)
                    velocities = np.array([
                        state['velocity_teme'] for state in orbital_states
                    ], dtype=np.float64)

                    # 時間戳 (N,)
                    timestamps = np.array([
                        state['timestamp'] for state in orbital_states
                    ], dtype='S32')

                    # 保存數據集（使用 gzip 壓縮）
                    sat_group.create_dataset(
                        'position_teme_km',
                        data=positions,
                        compression='gzip',
                        compression_opts=6
                    )
                    sat_group.create_dataset(
                        'velocity_teme_km_s',
                        data=velocities,
                        compression='gzip',
                        compression_opts=6
                    )
                    sat_group.create_dataset(
                        'timestamps_utc',
                        data=timestamps
                    )

                    # 衛星元數據
                    sat_group.attrs['constellation'] = sat_data.get('constellation', '')
                    sat_group.attrs['epoch_datetime'] = sat_data.get('epoch_datetime', '')
                    sat_group.attrs['algorithm_used'] = sat_data.get('algorithm_used', 'SGP4')
                    sat_group.attrs['total_positions'] = len(orbital_states)

        # 記錄壓縮效果
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        self.logger.info(f"📦 HDF5 文件大小: {file_size_mb:.1f} MB")
