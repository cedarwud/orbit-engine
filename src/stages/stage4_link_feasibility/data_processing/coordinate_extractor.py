#!/usr/bin/env python3
"""WGS84座標提取器 - Stage 4"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CoordinateExtractor:
    """WGS84 座標數據提取器"""

    @staticmethod
    def extract(input_data: Dict[str, Any], constellation_filter) -> Dict[str, Any]:
        """
        提取 WGS84 座標數據

        Args:
            input_data: Stage 3 輸出數據
            constellation_filter: 星座過濾器實例（用於更新門檻）

        Returns:
            提取的 WGS84 座標數據
        """
        # ✅ 兼容 Stage 3 兩種輸出格式
        satellites_data = input_data.get('satellites') or input_data.get('geographic_coordinates', {})
        wgs84_data = {}

        # 從上游數據讀取 constellation_configs (Stage 1 傳遞)
        upstream_configs = None
        if 'metadata' in input_data and 'constellation_configs' in input_data['metadata']:
            upstream_configs = input_data['metadata']['constellation_configs']
            logger.info("✅ 從 Stage 1 讀取 constellation_configs")

            # 更新 ConstellationFilter 使用上游配置
            if upstream_configs and constellation_filter:
                for constellation_name, config in upstream_configs.items():
                    threshold = config.get('service_elevation_threshold_deg')
                    if threshold is not None:
                        constellation_key = constellation_name.lower()
                        if constellation_key in constellation_filter.CONSTELLATION_THRESHOLDS:
                            constellation_filter.CONSTELLATION_THRESHOLDS[constellation_key]['min_elevation_deg'] = threshold
                            logger.info(f"   {constellation_name}: {threshold}° (從上游配置)")

        for satellite_id, satellite_info in satellites_data.items():
            if isinstance(satellite_info, dict):
                # ✅ 兼容兩種格式
                wgs84_coordinates = satellite_info.get('wgs84_coordinates') or satellite_info.get('time_series', [])

                # ✅ 智能推斷星座
                constellation = satellite_info.get('constellation', 'unknown')
                if constellation == 'unknown':
                    sat_id_lower = str(satellite_id).lower()
                    if 'starlink' in sat_id_lower or (satellite_id.isdigit() and 40000 < int(satellite_id) < 60000):
                        constellation = 'starlink'
                    elif 'oneweb' in sat_id_lower or (satellite_id.isdigit() and int(satellite_id) >= 60000):
                        constellation = 'oneweb'

                if wgs84_coordinates:
                    wgs84_data[satellite_id] = {
                        'wgs84_coordinates': wgs84_coordinates,
                        'constellation': constellation,
                        'total_positions': len(wgs84_coordinates)
                    }

        logger.info(f"📊 提取了 {len(wgs84_data)} 顆衛星的 WGS84 座標數據")
        return wgs84_data, upstream_configs
