#!/usr/bin/env python3
"""輸入提取器 - Stage 5"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InputExtractor:
    """輸入數據提取器"""

    @staticmethod
    def extract(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取衛星數據"""
        connectable_satellites = input_data.get('connectable_satellites', {})

        if not connectable_satellites:
            logger.warning("⚠️ 未找到 connectable_satellites，嘗試舊格式")
            satellites = input_data.get('satellites', {})
            if satellites:
                connectable_satellites = {'other': list(satellites.values())}
            else:
                raise ValueError("Stage 5 輸入數據驗證失敗：未找到衛星數據")

        metadata = input_data.get('metadata', {})
        constellation_configs = metadata.get('constellation_configs', {})

        total_connectable = sum(len(sats) for sats in connectable_satellites.values())
        logger.info(f"📊 提取可連線衛星池: {total_connectable} 顆衛星")

        return {
            'connectable_satellites': connectable_satellites,
            'metadata': {'constellation_configs': constellation_configs}
        }
