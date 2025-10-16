"""
Stage 5 Configuration Manager - Signal Quality Analysis
========================================================

Configuration management for Stage 5: Signal Quality Analysis Layer

Responsibilities:
- Load 3GPP TS 38.214 signal calculator parameters
- Load ITU-R P.676 atmospheric model parameters
- Load signal quality thresholds (RSRP, RSRQ, SINR)
- Load parallel processing settings
- Validate academic compliance (Grade A+ standards)

Author: Orbit Engine Refactoring Team
Date: 2025-10-15
Version: 1.0 (Phase 4 P1 Day 1-2)
"""

import logging
from typing import Dict, Any, Tuple, Optional
import multiprocessing as mp

try:
    from shared.configs import BaseConfigManager
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from shared.configs import BaseConfigManager


class Stage5ConfigManager(BaseConfigManager):
    """
    Stage 5 配置管理器 - 信號品質分析層 (Grade A+)

    管理配置項目:
    - 3GPP TS 38.214 信號計算器參數
    - ITU-R P.676 大氣衰減模型參數
    - 信號品質門檻值 (RSRP, RSRQ, SINR)
    - 並行處理配置
    - 觀測者位置（都卜勒計算）

    繼承自 BaseConfigManager，支持:
    - YAML 配置文件加載
    - 環境變數覆寫（flat + nested keys）
    - Fail-Fast 驗證
    """

    def get_stage_number(self) -> int:
        """返回 Stage 編號"""
        return 5

    def get_default_config(self) -> Dict[str, Any]:
        """
        返回 Stage 5 預設配置

        ⚠️ 注意: Grade A+ 標準要求所有參數都應從 YAML 配置文件讀取
        預設配置僅作為回退保障，生產環境必須提供完整 YAML 配置

        Returns:
            Dict[str, Any]: 預設配置字典
        """
        return {
            # ==================== 3GPP TS 38.214 信號計算器配置 ====================
            # SOURCE: 3GPP TS 38.104/211/214 specifications
            'signal_calculator': {
                # 帶寬配置
                # SOURCE: 3GPP TS 38.104 V18.4.0 Table 5.3.2-1
                # NR Band n258: 24.25-27.5 GHz, Channel BW: 50/100/200 MHz
                'bandwidth_mhz': 100.0,

                # 子載波間隔
                # SOURCE: 3GPP TS 38.211 V18.5.0 Table 4.2-1
                # Ku-band (12.5 GHz) recommended: 30 kHz
                'subcarrier_spacing_khz': 30.0,

                # 接收器噪聲係數
                # SOURCE: Receiver equipment specifications or ITU-R recommendations
                # Typical range: 5-10 dB (standard receiver: 5-7 dB)
                'noise_figure_db': 7.0,

                # 接收器溫度
                # SOURCE: ITU-R P.372 standard noise temperature
                # Standard environment: 290 K (17°C)
                'temperature_k': 290.0,
            },

            # ==================== ITU-R P.676 大氣衰減模型配置 ====================
            # SOURCE: ITU-R P.835-6 - Reference Standard Atmospheres
            'atmospheric_model': {
                # 溫度
                # SOURCE: ITU-R P.835-6 Mid-latitude annual mean
                # Reference range: 200-350 K
                'temperature_k': 283.0,  # Mid-latitude annual mean

                # 氣壓
                # SOURCE: ICAO Standard Atmosphere (1993)
                # Sea level standard: 1013.25 hPa
                'pressure_hpa': 1013.25,

                # 水蒸氣密度
                # SOURCE: ITU-R P.835-6 Mid-latitude annual mean
                # Reference range: 0-30 g/m³
                'water_vapor_density_g_m3': 7.5,
            },

            # ==================== 信號品質門檻值配置 ====================
            # SOURCE: 3GPP TS 38.133 V18.6.0 Section 9.2.3
            'signal_thresholds': {
                # RSRP 門檻值 (dBm)
                # SOURCE: 3GPP TS 38.133 Table 9.2.3.1-1
                'rsrp_excellent': -80.0,  # 優秀信號
                'rsrp_good': -90.0,       # 良好信號
                'rsrp_fair': -100.0,      # 可用信號
                'rsrp_poor': -110.0,      # 較差信號
                'rsrp_minimum': -120.0,   # 最低可連接門檻

                # RSRQ 門檻值 (dB)
                # SOURCE: 3GPP TS 38.133 Section 9.2.3
                'rsrq_excellent': -10.0,  # 優秀品質
                'rsrq_good': -15.0,       # 良好品質
                'rsrq_fair': -20.0,       # 可用品質
                'rsrq_poor': -25.0,       # 較差品質

                # SINR 門檻值 (dB)
                # SOURCE: 3GPP TS 38.214 Typical operating points
                'sinr_excellent': 20.0,   # 256QAM 可用
                'sinr_good': 13.0,        # 64QAM 可用
                'sinr_fair': 0.0,         # QPSK 可用
                'sinr_poor': -5.0,        # 邊緣連接
            },

            # ==================== 並行處理配置 ====================
            # SOURCE: Python multiprocessing best practices
            'parallel_processing': {
                'max_workers': None,      # None = auto-detect (min(cpu_count, 30))
                'enable_parallel': True,  # 啟用並行處理
            },

            # ==================== 觀測者位置配置 ====================
            # SOURCE: From Stage 1 or GPS measurements (TEME coordinate system)
            'observer': {
                'position_km': None,  # [x, y, z] - Usually provided by upstream stages
            },
        }

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        驗證 Stage 5 配置參數

        驗證項目:
        - signal_calculator 必要參數完整性
        - atmospheric_model 必要參數完整性
        - 參數範圍合理性
        - 學術標準合規性

        Args:
            config: 配置字典

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        errors = []

        # ========== signal_calculator 驗證 ==========
        # ✅ Fail-Fast: 必需的配置區塊不使用 .get() 回退
        if 'signal_calculator' not in config:
            errors.append(
                "缺少必要的 'signal_calculator' 配置\n"
                "Grade A 標準禁止使用預設值\n"
                "必須在配置文件中明確提供:\n"
                "  signal_calculator:\n"
                "    bandwidth_mhz: <value>  # SOURCE: 3GPP TS 38.104\n"
                "    subcarrier_spacing_khz: <value>  # SOURCE: 3GPP TS 38.211\n"
                "    noise_figure_db: <value>  # SOURCE: Hardware specs\n"
                "    temperature_k: <value>  # SOURCE: ITU-R P.372"
            )
            signal_calc = {}  # 避免後續檢查時 KeyError
        else:
            signal_calc = config['signal_calculator']

        if signal_calc:
            # 驗證必要參數
            required_params = {
                'bandwidth_mhz': (1.0, 400.0),          # 1-400 MHz
                'subcarrier_spacing_khz': (15.0, 240.0), # 15-240 kHz
                'noise_figure_db': (0.0, 20.0),         # 0-20 dB
                'temperature_k': (200.0, 350.0),        # 200-350 K
            }

            for param, (min_val, max_val) in required_params.items():
                if param not in signal_calc:
                    errors.append(
                        f"signal_calculator 缺少必要參數: {param}\n"
                        f"SOURCE: 3GPP TS 38.104/211/214"
                    )
                else:
                    value = signal_calc[param]
                    if not isinstance(value, (int, float)):
                        errors.append(
                            f"signal_calculator.{param} 必須是數值類型，"
                            f"當前類型: {type(value).__name__}"
                        )
                    elif not (min_val <= value <= max_val):
                        errors.append(
                            f"signal_calculator.{param} 超出有效範圍 "
                            f"[{min_val}, {max_val}]，當前值: {value}"
                        )

        # ========== atmospheric_model 驗證 ==========
        # ✅ Fail-Fast: 必需的配置區塊不使用 .get() 回退
        if 'atmospheric_model' not in config:
            errors.append(
                "缺少必要的 'atmospheric_model' 配置\n"
                "Grade A 標準禁止使用預設值\n"
                "必須在配置文件中明確提供:\n"
                "  atmospheric_model:\n"
                "    temperature_k: <value>  # SOURCE: ITU-R P.835-6\n"
                "    pressure_hpa: <value>  # SOURCE: ICAO Standard Atmosphere\n"
                "    water_vapor_density_g_m3: <value>  # SOURCE: ITU-R P.835-6"
            )
            atmos_model = {}  # 避免後續檢查時 KeyError
        else:
            atmos_model = config['atmospheric_model']

        if atmos_model:
            # 驗證必要參數
            required_params = {
                'temperature_k': (200.0, 350.0),            # 200-350 K
                'pressure_hpa': (500.0, 1100.0),            # 500-1100 hPa
                'water_vapor_density_g_m3': (0.0, 30.0),   # 0-30 g/m³
            }

            for param, (min_val, max_val) in required_params.items():
                if param not in atmos_model:
                    errors.append(
                        f"atmospheric_model 缺少必要參數: {param}\n"
                        f"SOURCE: ITU-R P.676-13, P.835-6"
                    )
                else:
                    value = atmos_model[param]
                    if not isinstance(value, (int, float)):
                        errors.append(
                            f"atmospheric_model.{param} 必須是數值類型，"
                            f"當前類型: {type(value).__name__}"
                        )
                    elif not (min_val <= value <= max_val):
                        errors.append(
                            f"atmospheric_model.{param} 超出有效範圍 "
                            f"[{min_val}, {max_val}]，當前值: {value}"
                        )

        # ========== signal_thresholds 驗證 (optional but recommended) ==========
        # ✅ Fail-Fast: 即使是可選配置也要明確檢查，而非靜默回退
        if 'signal_thresholds' not in config:
            # 可選配置，但應該記錄警告
            self.logger.warning(
                "未配置 signal_thresholds，將使用預設值\n"
                "建議在配置中明確提供以符合 Grade A 標準"
            )
            signal_thresholds = {}
        else:
            signal_thresholds = config['signal_thresholds']

        if signal_thresholds:
            # 驗證 RSRP 門檻合理性 (遞減順序)
            rsrp_keys = ['rsrp_excellent', 'rsrp_good', 'rsrp_fair', 'rsrp_poor', 'rsrp_minimum']
            rsrp_values = [signal_thresholds.get(key) for key in rsrp_keys if key in signal_thresholds]

            if len(rsrp_values) >= 2:
                for i in range(len(rsrp_values) - 1):
                    if rsrp_values[i] <= rsrp_values[i + 1]:
                        errors.append(
                            f"signal_thresholds: RSRP 門檻必須遞減順序 "
                            f"(excellent > good > fair > poor > minimum)"
                        )
                        break

        # ========== parallel_processing 驗證 (optional) ==========
        # ✅ Fail-Fast: 即使是可選配置也要明確檢查，而非靜默回退
        if 'parallel_processing' not in config:
            # 可選配置，將使用自動檢測
            self.logger.info(
                "未配置 parallel_processing，將使用自動檢測\n"
                "max_workers 將自動設置為 min(cpu_count, 30)"
            )
            parallel_config = {}
        else:
            parallel_config = config['parallel_processing']

        if parallel_config:
            # ✅ Fail-Fast: 明確檢查是否存在，而非使用 .get()
            if 'max_workers' in parallel_config:
                max_workers = parallel_config['max_workers']
            else:
                max_workers = None  # 明確設置為 None 表示使用自動檢測

            if max_workers is not None:
                if not isinstance(max_workers, int) or max_workers < 1:
                    errors.append(
                        f"parallel_processing.max_workers 必須是正整數或 null，"
                        f"當前值: {max_workers}"
                    )
                elif max_workers > mp.cpu_count() * 2:
                    errors.append(
                        f"parallel_processing.max_workers 不建議超過 CPU 核心數的 2 倍，"
                        f"當前值: {max_workers}, CPU 核心: {mp.cpu_count()}"
                    )

        # Return validation result
        if errors:
            error_message = "\n".join(errors)
            return False, error_message
        return True, None


# Convenience function for backward compatibility
def create_stage5_config_manager() -> Stage5ConfigManager:
    """創建 Stage 5 配置管理器"""
    return Stage5ConfigManager()
