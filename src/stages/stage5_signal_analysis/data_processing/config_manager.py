#!/usr/bin/env python3
"""配置管理器 - Stage 5"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """Stage 5 配置管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._load_signal_thresholds()
        self._load_system_params()

    def _load_signal_thresholds(self):
        """載入信號門檻配置"""
        from shared.constants.physics_constants import SignalConstants
        signal_consts = SignalConstants()

        self.signal_thresholds = self.config.get('signal_thresholds', {
            'rsrp_excellent': signal_consts.RSRP_EXCELLENT,
            'rsrp_good': signal_consts.RSRP_GOOD,
            'rsrp_fair': signal_consts.RSRP_FAIR,
            'rsrp_poor': signal_consts.RSRP_POOR,
            'rsrq_good': signal_consts.RSRQ_GOOD,
            'rsrq_fair': signal_consts.RSRQ_FAIR,
            'rsrq_poor': signal_consts.RSRQ_POOR,
            'sinr_good': signal_consts.SINR_EXCELLENT,
            'sinr_fair': signal_consts.SINR_GOOD,
            'sinr_poor': signal_consts.SINR_POOR
        })

    def _load_system_params(self):
        """載入系統參數"""
        if 'noise_figure_db' not in self.config:
            self.config['noise_figure_db'] = 7.0
        if 'temperature_k' not in self.config:
            self.config['temperature_k'] = 290.0

    def get_thresholds(self) -> Dict[str, float]:
        return self.signal_thresholds

    def get_config(self) -> Dict[str, Any]:
        return self.config
