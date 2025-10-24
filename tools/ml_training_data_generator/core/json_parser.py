"""
JSON Parser - 解析 Stage 6 輸出

這個模組只讀取 Stage 6 JSON 文件，不修改原始輸出。
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .types import Stage6Output

logger = logging.getLogger(__name__)


class Stage6OutputParser:
    """解析 Stage 6 JSON 輸出

    獨立工具設計：只讀取 JSON，不修改 Stage 6 輸出。
    Stage 6 輸出仍用於前端渲染。

    SOURCE: Proposal 003, Architecture Document
            "ML Data Generator 是獨立工具"
    """

    def __init__(self):
        """初始化解析器"""
        self.required_fields = ['signal_analysis']  # Minimal requirement
        logger.info("Stage6OutputParser initialized")

    def parse_file(self, json_path: str) -> Optional[Stage6Output]:
        """解析單個 Stage 6 JSON 文件

        Args:
            json_path: JSON 文件路徑

        Returns:
            Stage6Output 或 None（解析失敗時）
        """
        json_file = Path(json_path)

        if not json_file.exists():
            logger.error(f"JSON file not found: {json_path}")
            return None

        if not json_file.suffix == '.json':
            logger.warning(f"File is not JSON: {json_path}")
            return None

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 驗證 schema
            if not self.validate_schema(data):
                logger.error(f"Schema validation failed: {json_path}")
                return None

            # 提取 signal_analysis
            signal_analysis = data.get('signal_analysis', {})

            # 推斷 constellation（從第一個衛星）
            constellation = 'mixed'  # Default
            if signal_analysis:
                first_sat = next(iter(signal_analysis.values()))
                constellation = first_sat.get('constellation', 'unknown')

            # 推斷 start_time 和 end_time（從第一個衛星的 time_series）
            start_time = ''
            end_time = ''
            if signal_analysis:
                first_sat = next(iter(signal_analysis.values()))
                time_series = first_sat.get('time_series', [])
                if time_series:
                    start_time = time_series[0].get('timestamp', '')
                    end_time = time_series[-1].get('timestamp', '')

            # 構建 Stage6Output 對象
            stage6_output = Stage6Output(
                file_path=str(json_file),
                constellation=constellation,
                start_time=start_time,
                end_time=end_time,
                signal_analysis=signal_analysis,
                scenario_variants=data.get('scenario_variants'),
                gpp_events=data.get('gpp_events'),
                pool_verification=data.get('pool_verification')
            )

            num_satellites = len(stage6_output.get_available_satellites())
            logger.info(f"✅ Parsed {json_file.name}: {num_satellites} satellites")

            return stage6_output

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {json_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing {json_path}: {e}")
            return None

    def parse_batch(self, json_dir: str, pattern: str = "stage6_research*.json") -> List[Stage6Output]:
        """批量解析目錄中的 JSON 文件

        Args:
            json_dir: JSON 文件目錄
            pattern: 文件名模式（glob pattern）

        Returns:
            Stage6Output 列表
        """
        json_directory = Path(json_dir)

        if not json_directory.exists():
            logger.error(f"Directory not found: {json_dir}")
            return []

        if not json_directory.is_dir():
            logger.error(f"Path is not a directory: {json_dir}")
            return []

        # 查找匹配的 JSON 文件
        json_files = sorted(json_directory.glob(pattern))
        logger.info(f"Found {len(json_files)} JSON files in {json_dir}")

        if not json_files:
            logger.warning(f"No files matching pattern '{pattern}' in {json_dir}")
            return []

        # 解析所有文件
        outputs = []
        for json_file in json_files:
            output = self.parse_file(str(json_file))
            if output:
                outputs.append(output)

        success_rate = len(outputs) / len(json_files) * 100 if json_files else 0
        logger.info(f"✅ Parsed {len(outputs)}/{len(json_files)} files ({success_rate:.1f}% success)")

        return outputs

    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """驗證 JSON schema 完整性

        Args:
            data: JSON 數據（字典）

        Returns:
            True if valid, False otherwise
        """
        # 檢查必需字段
        for field in self.required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False

        # 檢查 signal_analysis 結構
        signal_analysis = data.get('signal_analysis', {})
        if not isinstance(signal_analysis, dict):
            logger.error("signal_analysis must be a dictionary")
            return False

        if not signal_analysis:
            logger.warning("signal_analysis is empty")
            return False

        # 檢查至少一個衛星的數據結構
        first_satellite = next(iter(signal_analysis.values()), None)
        if first_satellite:
            if 'time_series' not in first_satellite:
                logger.error("Missing 'time_series' in satellite data")
                return False

            time_series = first_satellite.get('time_series', [])
            if not time_series:
                logger.warning("time_series is empty for first satellite")
                return False

            # 檢查 time_series 的第一個條目
            first_entry = time_series[0]
            required_signal_fields = ['timestamp', 'signal_quality']
            for field in required_signal_fields:
                if field not in first_entry:
                    logger.error(f"Missing field in time_series entry: {field}")
                    return False

            # 檢查 signal_quality 結構
            signal_quality = first_entry.get('signal_quality', {})
            # Note: actual field is 'rs_sinr_db', not 'snr_db'
            required_signal_quality_fields = ['rsrp_dbm', 'rsrq_db']
            for field in required_signal_quality_fields:
                if field not in signal_quality:
                    logger.error(f"Missing field in signal_quality: {field}")
                    return False

            # Check for SNR field (either rs_sinr_db or snr_db)
            if 'rs_sinr_db' not in signal_quality and 'snr_db' not in signal_quality:
                logger.error("Missing SNR field (expected 'rs_sinr_db' or 'snr_db')")
                return False

        logger.debug("Schema validation passed")
        return True

    def get_dataset_info(self, outputs: List[Stage6Output]) -> Dict[str, Any]:
        """獲取數據集信息統計

        Args:
            outputs: Stage6Output 列表

        Returns:
            統計信息字典
        """
        if not outputs:
            return {}

        total_satellites = sum(len(output.get_available_satellites()) for output in outputs)
        constellations = set(output.constellation for output in outputs)

        # 統計時間序列長度
        total_time_steps = 0
        for output in outputs:
            for sat_id in output.get_available_satellites():
                total_time_steps += output.get_time_series_length(sat_id)

        info = {
            'num_files': len(outputs),
            'constellations': list(constellations),
            'total_satellites': total_satellites,
            'avg_satellites_per_file': total_satellites / len(outputs),
            'total_time_steps': total_time_steps,
            'avg_time_steps': total_time_steps / total_satellites if total_satellites > 0 else 0
        }

        logger.info(f"📊 Dataset Info: {info['num_files']} files, "
                   f"{info['total_satellites']} satellites, "
                   f"{info['total_time_steps']} time steps")

        return info


def main():
    """測試 JSON Parser"""
    logging.basicConfig(level=logging.INFO)

    parser = Stage6OutputParser()

    # 測試單個文件解析
    test_file = "data/outputs/stage6/stage6_research_optimization_20251020_122405.json"
    if Path(test_file).exists():
        output = parser.parse_file(test_file)
        if output:
            print(f"✅ Parsed: {output.constellation}")
            print(f"   Satellites: {len(output.get_available_satellites())}")

    # 測試批量解析
    test_dir = "data/outputs/stage6"
    if Path(test_dir).exists():
        outputs = parser.parse_batch(test_dir)
        if outputs:
            info = parser.get_dataset_info(outputs)
            print(f"\n📊 Dataset Info:")
            for key, value in info.items():
                print(f"   {key}: {value}")


if __name__ == "__main__":
    main()
