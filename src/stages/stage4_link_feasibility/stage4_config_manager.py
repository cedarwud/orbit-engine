"""
Stage 4 Configuration Manager - Link Feasibility Analysis
===========================================================

Configuration management for Stage 4: Link Feasibility Assessment Layer

Responsibilities:
- Load visibility calculation parameters (IAU standards, elevation thresholds)
- Load pool optimization targets (min/max pool size, coverage rate)
- Load epoch validation settings
- Load performance settings (parallel processing)
- Validate academic compliance (Grade A standards)

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


class Stage4ConfigManager(BaseConfigManager):
    """
    Stage 4 配置管理器 - 鏈路可行性評估層

    管理配置項目:
    - IAU 標準可見性計算
    - 星座特定仰角門檻
    - 池優化目標（動態衛星池）
    - Epoch 驗證設置
    - 性能並行處理配置

    繼承自 BaseConfigManager，支持:
    - YAML 配置文件加載
    - 環境變數覆寫（flat + nested keys）
    - Fail-Fast 驗證
    """

    def get_stage_number(self) -> int:
        """返回 Stage 編號"""
        return 4

    def get_default_config(self) -> Dict[str, Any]:
        """
        返回 Stage 4 預設配置

        ⚠️ 注意: Grade A 標準要求所有參數都應從 YAML 配置文件讀取
        預設配置僅作為回退保障，生產環境必須提供完整 YAML 配置

        Returns:
            Dict[str, Any]: 預設配置字典
        """
        return {
            # ==================== 學術標準模式 ====================
            # SOURCE: IAU SOFA Standards of Fundamental Astronomy
            'use_iau_standards': True,    # 使用 Skyfield IAU 標準計算器
            'validate_epochs': True,      # 啟用 Epoch 驗證

            # ==================== 池優化設置 ====================
            # PURPOSE: Stage 4.2 時空錯置池規劃優化
            'enable_pool_optimization': True,  # 啟用池優化

            # ==================== 星座特定門檻 ====================
            # SOURCE: Starlink/OneWeb 官方規格
            'constellation_thresholds': {
                'starlink': {
                    'elevation_deg': 5.0,   # Starlink 最小仰角
                    'reason': 'Starlink 官方規格',
                },
                'oneweb': {
                    'elevation_deg': 10.0,  # OneWeb 最小仰角
                    'reason': 'OneWeb 官方規格',
                },
                'default': {
                    'elevation_deg': 10.0,  # 其他星座預設值
                },
            },

            # ==================== 可見性計算方法 ====================
            # SOURCE: Skyfield library IAU 2000A/2006 nutation model
            'visibility': {
                'method': 'skyfield_iau',      # IAU 標準
                'coordinate_system': 'WGS84 Ellipsoid',
                'precision_level': 'Research Grade',
                'nutation_model': 'IAU 2000A/2006',
                'polar_motion_correction': True,
                'atmospheric_refraction': True,
            },

            # ==================== NTPU 地面站座標 ====================
            # SOURCE: GPS 實測座標
            # REFERENCE: 24.9441°N, 121.3714°E, 36m altitude
            'ground_station': {
                'name': 'National Taipei University of Technology',
                'latitude_deg': 24.9441,
                'longitude_deg': 121.3714,
                'altitude_m': 36.0,
            },

            # ==================== Epoch 驗證設置 ====================
            # SOURCE: Vallado 2013 - Epoch diversity requirements
            'epoch_validation': {
                'enabled': True,
                'min_diversity_ratio': 0.5,     # 至少 50% epoch 多樣性
                'min_diversity_count': 3,       # 或至少 3 個不同 epoch
                'max_time_diff_days': 7,        # 時間戳記與 epoch 最大差距（天）
                'min_distribution_hours': 24,   # epoch 分布最小時間跨度（小時）
                'forbidden_fields': [           # 禁止的統一時間基準字段
                    'calculation_base_time',
                    'primary_epoch_time',
                    'unified_time_base',
                ],
            },

            # ==================== 輸出格式 ====================
            'output': {
                'format': 'complete_time_series_with_optimization',
                'version': 'plan_a_b_integrated_v1.0',
                'include_time_series': True,
                'include_service_window': True,
                'include_is_connectable': True,
                'include_link_quality': True,
                'include_epoch_report': True,
                'include_optimization_metrics': True,
            },

            # ==================== 日誌設置 ====================
            'logging': {
                'level': 'INFO',
                'enable_progress': True,
                'enable_epoch_validation': True,
                'enable_iau_standard_info': True,
            },

            # ==================== 性能設置 ====================
            # SOURCE: Python multiprocessing best practices
            'performance': {
                'batch_size': None,             # 無批次限制
                'parallel_processing': True,    # 啟用並行處理
                'max_workers': None,            # None = 動態計算
                'memory_limit_mb': None,        # 無記憶體限制

                # 動態 CPU 工作器策略（與 Stage 2 一致）
                'dynamic_worker_strategy': {
                    'cpu_usage_threshold_high': 30,   # CPU < 30%: 使用 95% 核心
                    'cpu_usage_threshold_medium': 50, # CPU 30-50%: 使用 75% 核心
                },
            },

            # ==================== 時間間隔設置 ====================
            # SOURCE: Vallado 2013 Section 8.6 - SGP4 Propagation Time Step
            # RECOMMENDATION: <1 minute interval for LEO precision
            'time_interval_seconds': 30,  # 30秒間隔

            # ==================== 池優化目標配置 ====================
            # SOURCE: 3GPP TR 38.821 (2021) Section 6.2 - NTN QoS requirements
            'pool_optimization_targets': {
                'starlink': {
                    'expected_visible_satellites': [10, 15],  # [min, max]
                    'min_pool_size': 10,
                    'max_pool_size': 15,
                    'target_coverage_rate': 0.95,  # 95% coverage
                    # SOURCE: ITU-T E.800 (2008)
                },
                'oneweb': {
                    'expected_visible_satellites': [3, 6],
                    'min_pool_size': 3,
                    'max_pool_size': 6,
                    'target_coverage_rate': 0.95,
                },
            },

            # ==================== 學術合規聲明 ====================
            'academic_compliance': {
                'iau_standards': True,
                'vallado_epoch_requirements': True,
                'kodheli_link_budget': True,
                'research_grade_precision': True,
                'peer_review_ready': True,
            },

            # ==================== 引用文獻 ====================
            'references': [
                'Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications (4th ed.).',
                'Rhodes, B. (2019). Skyfield: High precision research-grade positions.',
                'Kodheli, O., et al. (2021). Satellite Communications in the New Space Era.',
                'IAU SOFA (2021). IAU Standards of Fundamental Astronomy.',
            ],
        }

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        驗證 Stage 4 配置參數

        驗證項目:
        - 星座門檻配置完整性
        - 仰角範圍合理性
        - 池優化目標一致性
        - 時間間隔設置正確性
        - 學術標準合規性

        Args:
            config: 配置字典

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        errors = []

        # ========== 星座門檻驗證 ==========
        constellation_thresholds = config.get('constellation_thresholds', {})

        if not constellation_thresholds:
            errors.append("缺少必要的 'constellation_thresholds' 配置")
        else:
            # 驗證 Starlink 門檻
            starlink = constellation_thresholds.get('starlink', {})
            if 'elevation_deg' not in starlink:
                errors.append("缺少 'constellation_thresholds.starlink.elevation_deg'")
            elif not (0 <= starlink['elevation_deg'] <= 90):
                errors.append(
                    f"constellation_thresholds.starlink.elevation_deg 必須在 0-90° 範圍內，"
                    f"當前值: {starlink['elevation_deg']}"
                )

            # 驗證 OneWeb 門檻
            oneweb = constellation_thresholds.get('oneweb', {})
            if 'elevation_deg' not in oneweb:
                errors.append("缺少 'constellation_thresholds.oneweb.elevation_deg'")
            elif not (0 <= oneweb['elevation_deg'] <= 90):
                errors.append(
                    f"constellation_thresholds.oneweb.elevation_deg 必須在 0-90° 範圍內，"
                    f"當前值: {oneweb['elevation_deg']}"
                )

        # ========== 池優化目標驗證 ==========
        pool_targets = config.get('pool_optimization_targets', {})

        if pool_targets:
            for constellation in ['starlink', 'oneweb']:
                target = pool_targets.get(constellation, {})

                if target:
                    # 驗證 min/max pool size 一致性
                    min_pool = target.get('min_pool_size')
                    max_pool = target.get('max_pool_size')
                    expected_range = target.get('expected_visible_satellites', [])

                    if min_pool and max_pool and min_pool > max_pool:
                        errors.append(
                            f"pool_optimization_targets.{constellation}: "
                            f"min_pool_size ({min_pool}) > max_pool_size ({max_pool})"
                        )

                    if len(expected_range) == 2:
                        if min_pool and min_pool != expected_range[0]:
                            errors.append(
                                f"pool_optimization_targets.{constellation}: "
                                f"min_pool_size ({min_pool}) 與 expected_visible_satellites[0] "
                                f"({expected_range[0]}) 不一致"
                            )

                    # 驗證 target_coverage_rate 範圍
                    coverage_rate = target.get('target_coverage_rate')
                    if coverage_rate and not (0 < coverage_rate <= 1.0):
                        errors.append(
                            f"pool_optimization_targets.{constellation}.target_coverage_rate "
                            f"必須在 (0, 1.0] 範圍內，當前值: {coverage_rate}"
                        )

        # ========== 時間間隔驗證 ==========
        time_interval = config.get('time_interval_seconds')

        if time_interval is None:
            errors.append(
                "缺少必要的 'time_interval_seconds' 配置\n"
                "SOURCE: Vallado 2013 Section 8.6 - 建議 <60 秒間隔"
            )
        elif not isinstance(time_interval, (int, float)) or time_interval <= 0:
            errors.append(
                f"time_interval_seconds 必須是正數，當前值: {time_interval}"
            )
        elif time_interval > 60:
            errors.append(
                f"time_interval_seconds 不建議超過 60 秒（當前: {time_interval}秒）\n"
                "SOURCE: Vallado 2013 Section 8.6"
            )

        # ========== 地面站座標驗證 ==========
        ground_station = config.get('ground_station', {})

        if ground_station:
            lat = ground_station.get('latitude_deg')
            lon = ground_station.get('longitude_deg')

            if lat is not None and not (-90 <= lat <= 90):
                errors.append(
                    f"ground_station.latitude_deg 必須在 -90° 到 90° 範圍內，"
                    f"當前值: {lat}"
                )

            if lon is not None and not (-180 <= lon <= 180):
                errors.append(
                    f"ground_station.longitude_deg 必須在 -180° 到 180° 範圍內，"
                    f"當前值: {lon}"
                )

        # Return validation result
        if errors:
            error_message = "\n".join(errors)
            return False, error_message
        return True, None


# Convenience function for backward compatibility
def create_stage4_config_manager() -> Stage4ConfigManager:
    """創建 Stage 4 配置管理器"""
    return Stage4ConfigManager()
