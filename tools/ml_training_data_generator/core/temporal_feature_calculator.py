"""
Temporal Feature Calculator - 計算時間特徵（velocity, predicted RSRP）

PURPOSE: 添加時間維度特徵以支持 D2 預測性換手學習

Created: 2025-10-24
"""

import logging
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TemporalFeatureCalculator:
    """計算衛星的時間特徵

    Features:
    1. RSRP velocity (dRSRP/dt)
    2. Distance velocity (dDistance/dt)
    3. Predicted RSRP (t+30s, t+60s)

    SOURCE: Badini et al. (2024) IEEE TAES - Velocity features
    SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a - D2 predictive intent
    """

    def __init__(self, time_interval_sec: float = 30.0):
        """初始化時間特徵計算器

        Args:
            time_interval_sec: 時間序列間隔（秒）
                SOURCE: Stage 4 configuration - 30 秒間隔
        """
        self.time_interval_sec = time_interval_sec
        logger.info(f"TemporalFeatureCalculator initialized (interval={time_interval_sec}s)")

    def calculate_velocity_features(
        self,
        current_entry: Dict,
        previous_entry: Optional[Dict],
        time_interval_sec: Optional[float] = None
    ) -> Tuple[float, float]:
        """計算 velocity 特徵

        Args:
            current_entry: 當前時間點的數據
            previous_entry: 前一時間點的數據（None 時 velocity=0）
            time_interval_sec: 時間間隔（None 時使用 self.time_interval_sec）

        Returns:
            (rsrp_velocity, distance_velocity)

        SOURCE:
        - Badini et al. (2024) IEEE TAES, Section III.B
        - Velocity = (value_t - value_t-1) / delta_t
        """
        if previous_entry is None:
            # 邊界情況：第一個時間點，velocity=0
            return 0.0, 0.0

        delta_t = time_interval_sec or self.time_interval_sec

        # Extract current values
        current_signal = current_entry.get('signal_quality', {})
        current_physical = current_entry.get('physical_parameters', {})
        current_rsrp = current_signal.get('rsrp_dbm', 0.0)
        current_distance = current_physical.get('distance_km', 0.0)

        # Extract previous values
        prev_signal = previous_entry.get('signal_quality', {})
        prev_physical = previous_entry.get('physical_parameters', {})
        prev_rsrp = prev_signal.get('rsrp_dbm', 0.0)
        prev_distance = prev_physical.get('distance_km', 0.0)

        # Calculate velocities
        rsrp_velocity = (current_rsrp - prev_rsrp) / delta_t  # dB/s
        distance_velocity = (current_distance - prev_distance) / delta_t  # km/s

        return rsrp_velocity, distance_velocity

    def predict_future_rsrp(
        self,
        current_entry: Dict,
        rsrp_velocity: float,
        distance_velocity: float,
        future_seconds: List[float]
    ) -> List[float]:
        """預測未來 RSRP（使用 FSPL 線性近似）

        Simplified prediction method:
        1. Use current distance + distance_velocity to estimate future distance
        2. Apply FSPL relationship: delta_rsrp_db = -20*log10(d_new/d_current)
        3. predicted_rsrp = current_rsrp + delta_rsrp_db

        Args:
            current_entry: 當前時間點數據
            rsrp_velocity: RSRP velocity (dB/s)
            distance_velocity: Distance velocity (km/s)
            future_seconds: 預測時間點列表（如 [30, 60]）

        Returns:
            List of predicted RSRP values

        SOURCE:
        - ITU-R P.525-4: Free Space Path Loss
        - FSPL(dB) = 20*log10(distance) + 20*log10(frequency) + 32.44
        - Simplified: delta_RSRP ≈ -20*log10(d_new/d_old)
        """
        # Extract current values
        current_signal = current_entry.get('signal_quality', {})
        current_physical = current_entry.get('physical_parameters', {})
        current_rsrp = current_signal.get('rsrp_dbm', 0.0)
        current_distance = current_physical.get('distance_km', 0.0)

        predicted_rsrps = []

        for delta_t in future_seconds:
            # Method 1: Linear extrapolation (simple)
            # predicted_rsrp = current_rsrp + rsrp_velocity * delta_t

            # Method 2: FSPL-based (more accurate)
            future_distance = current_distance + distance_velocity * delta_t

            # Safety check: distance must be positive
            if future_distance <= 0 or current_distance <= 0:
                # Fallback to linear extrapolation
                predicted_rsrp = current_rsrp + rsrp_velocity * delta_t
            else:
                # FSPL relationship: RSRP change is proportional to distance ratio
                # delta_rsrp_db = -20 * log10(d_new / d_old)
                delta_rsrp_db = -20 * math.log10(future_distance / current_distance)
                predicted_rsrp = current_rsrp + delta_rsrp_db

            # Clamp to reasonable range [-140, -20] dBm
            # SOURCE: 3GPP TS 38.215 v18.1.0 Section 5.1.1 (measurement range)
            predicted_rsrp = max(-140.0, min(-20.0, predicted_rsrp))

            predicted_rsrps.append(predicted_rsrp)

        return predicted_rsrps

    def calculate_all_temporal_features(
        self,
        time_series: List[Dict],
        timestamp_idx: int
    ) -> Dict[str, float]:
        """計算指定時間點的所有時間特徵

        Args:
            time_series: 完整時間序列數據
            timestamp_idx: 當前時間點索引

        Returns:
            Dict with keys:
            - rsrp_velocity: float
            - distance_velocity: float
            - predicted_rsrp_30s: float
            - predicted_rsrp_60s: float
        """
        current_entry = time_series[timestamp_idx]
        previous_entry = time_series[timestamp_idx - 1] if timestamp_idx > 0 else None

        # Calculate velocities
        rsrp_velocity, distance_velocity = self.calculate_velocity_features(
            current_entry, previous_entry
        )

        # Predict future RSRP (t+30s, t+60s)
        predicted_rsrps = self.predict_future_rsrp(
            current_entry,
            rsrp_velocity,
            distance_velocity,
            future_seconds=[30.0, 60.0]
        )

        return {
            'rsrp_velocity': rsrp_velocity,
            'distance_velocity': distance_velocity,
            'predicted_rsrp_30s': predicted_rsrps[0],
            'predicted_rsrp_60s': predicted_rsrps[1]
        }


def create_temporal_feature_calculator(time_interval_sec: float = 30.0) -> TemporalFeatureCalculator:
    """Factory function to create temporal feature calculator

    Args:
        time_interval_sec: Time series interval in seconds

    Returns:
        TemporalFeatureCalculator instance
    """
    return TemporalFeatureCalculator(time_interval_sec=time_interval_sec)
