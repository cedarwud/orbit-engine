#!/usr/bin/env python3
"""服務窗口計算器 - Stage 4"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ServiceWindowCalculator:
    """服務窗口計算器"""

    @staticmethod
    def calculate(time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算服務窗口

        Returns:
            服務窗口數據，字段名符合 stage4_validator.py 驗證要求:
            - start_time: 服務窗口開始時間
            - end_time: 服務窗口結束時間
            - duration_minutes: 持續時間（分鐘）
            - time_points_count: 時間點數量
            - continuity_score: 連續性分數
        """
        if not time_series:
            return {
                'duration_minutes': 0,
                'start_time': None,
                'end_time': None,
                'time_points_count': 0,
                'continuity_score': 0.0
            }

        # ✅ 修復: is_connectable 在 visibility_metrics 中，不是頂層字段
        connectable_points = [
            p for p in time_series
            if p.get('visibility_metrics', {}).get('is_connectable', False)
        ]

        if not connectable_points:
            return {
                'duration_minutes': 0,
                'start_time': None,
                'end_time': None,
                'time_points_count': 0,
                'continuity_score': 0.0
            }

        # 計算時間點數量
        time_points_count = len(connectable_points)

        # 取第一個和最後一個可連線點
        start_time = connectable_points[0].get('timestamp')
        end_time = connectable_points[-1].get('timestamp')

        # ✅ Fail-Fast #5: 根據實際時間戳計算持續時間（分鐘）
        # 移除 try-except，讓時間戳解析錯誤直接拋出
        # 依據: ACADEMIC_STANDARDS.md - 禁止假設值/估算值
        from datetime import datetime
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration_minutes = (end_dt - start_dt).total_seconds() / 60.0
        except Exception as e:
            raise ValueError(
                f"❌ Fail-Fast: 服務窗口時間戳解析失敗\n"
                f"start_time: {start_time}\n"
                f"end_time: {end_time}\n"
                f"時間點數量: {time_points_count}\n"
                f"原始錯誤: {e}\n"
                f"依據: ACADEMIC_STANDARDS.md - 禁止使用估算值（如假設1分鐘間隔）\n"
                f"時間戳記應由 Stage 2/3 提供標準 ISO 8601 格式"
            ) from e

        # 計算連續性分數
        continuity_score = len(connectable_points) / len(time_series) if time_series else 0.0

        return {
            'duration_minutes': round(duration_minutes, 1),
            'start_time': start_time,
            'end_time': end_time,
            'time_points_count': time_points_count,
            'continuity_score': round(continuity_score, 3)
        }
