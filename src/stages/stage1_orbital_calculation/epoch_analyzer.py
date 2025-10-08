#!/usr/bin/env python3
"""
TLE Epoch 分析器與篩選器 - 動態分析 TLE 檔案的 epoch 分布

🎯 核心功能：
1. EpochAnalyzer: 動態分析 TLE epoch 分布（日期/時間/星座）
2. EpochFilter: 根據分析結果篩選衛星

⚠️ 重要原則：
- 完全動態分析，不硬編碼任何日期或時間
- 每個 TLE 檔案都可能不同，自動適應
- 星座感知（Starlink, OneWeb 分別統計）
- 向後兼容（可配置禁用）

🔬 符合學術標準：
- 基於真實 TLE epoch 數據分析
- 無估算值，無簡化算法
- 完整數據溯源

作者: Orbit Engine Team
版本: v1.0
日期: 2025-10-03
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class EpochAnalyzer:
    """TLE Epoch 動態分析器"""

    def analyze_epoch_distribution(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析 TLE epoch 分布

        Args:
            satellites: 衛星列表（必須包含 epoch_datetime, name）

        Returns:
            epoch_analysis: {
                'total_satellites': int,
                'epoch_time_range': {...},
                'date_distribution': {...},
                'time_distribution': {...},
                'constellation_distribution': {...},
                'recommended_reference_time': str,
                'recommendation_reason': str,
                'analysis_timestamp': str
            }
        """
        logger.info("📊 開始 TLE Epoch 分布分析...")

        if not satellites:
            raise ValueError("衛星列表為空，無法進行 epoch 分析")

        # 1. 日期分布統計
        date_distribution = self._analyze_date_distribution(satellites)

        # 2. 時間分布統計（最新日期）
        latest_date = max(date_distribution.keys())
        time_distribution = self._analyze_time_distribution(satellites, latest_date)

        # 3. 星座分布統計
        constellation_distribution = self._analyze_constellation_distribution(satellites)

        # 4. 計算推薦參考時刻
        recommended_time, reason = self._calculate_recommended_reference_time(
            date_distribution, time_distribution
        )

        # 5. 計算時間跨度
        epoch_time_range = self._calculate_time_range(satellites)

        analysis_result = {
            'total_satellites': len(satellites),
            'epoch_time_range': epoch_time_range,
            'date_distribution': date_distribution,
            'time_distribution': time_distribution,
            'constellation_distribution': constellation_distribution,
            'recommended_reference_time': recommended_time,
            'recommendation_reason': reason,
            'analysis_timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        self._log_analysis_summary(analysis_result)

        return analysis_result

    def _analyze_date_distribution(self, satellites: List[Dict]) -> Dict[str, Any]:
        """分析 epoch 日期分布"""
        date_counts = defaultdict(int)

        for satellite in satellites:
            epoch_dt = self._parse_datetime(satellite['epoch_datetime'])
            date_str = epoch_dt.strftime('%Y-%m-%d')
            date_counts[date_str] += 1

        # 按日期排序，計算百分比
        sorted_dates = sorted(date_counts.items(), key=lambda x: x[0], reverse=True)
        total = sum(date_counts.values())

        distribution = {}
        for date_str, count in sorted_dates:
            distribution[date_str] = {
                'count': count,
                'percentage': round(count / total * 100, 1)
            }

        return distribution

    def _analyze_time_distribution(self, satellites: List[Dict], target_date: str) -> Dict[str, Any]:
        """分析特定日期的時間分布（按小時統計）"""
        hour_counts = defaultdict(int)

        for satellite in satellites:
            epoch_dt = self._parse_datetime(satellite['epoch_datetime'])
            if epoch_dt.strftime('%Y-%m-%d') == target_date:
                hour_counts[epoch_dt.hour] += 1

        # ✅ Fail-Fast: 無數據時立即失敗
        if not hour_counts:
            raise ValueError(
                f"❌ 指定日期無衛星數據: {target_date}\n"
                f"Fail-Fast 原則: 無數據應立即失敗而非返回空結果"
            )

        most_dense_hour = max(hour_counts, key=hour_counts.get)
        total_on_date = sum(hour_counts.values())

        distribution = {
            'target_date': target_date,
            'hourly_distribution': dict(hour_counts),
            'most_dense_hour': most_dense_hour,
            'most_dense_count': hour_counts[most_dense_hour],
            'most_dense_percentage': round(hour_counts[most_dense_hour] / total_on_date * 100, 1)
        }

        return distribution

    def _analyze_constellation_distribution(self, satellites: List[Dict]) -> Dict[str, Any]:
        """分析星座分布（含轨道周期统计）"""
        constellation_counts = defaultdict(int)
        constellation_latest_epochs = {}
        constellation_orbital_periods = defaultdict(list)  # 新增：收集各星座的轨道周期

        for satellite in satellites:
            name_upper = satellite['name'].upper()
            epoch_dt = self._parse_datetime(satellite['epoch_datetime'])

            if 'STARLINK' in name_upper:
                constellation = 'STARLINK'
            elif 'ONEWEB' in name_upper:
                constellation = 'ONEWEB'
            else:
                constellation = 'OTHER'

            constellation_counts[constellation] += 1

            # 統一移除時區資訊進行比較
            epoch_dt_naive = epoch_dt.replace(tzinfo=None) if epoch_dt.tzinfo else epoch_dt

            if constellation not in constellation_latest_epochs:
                constellation_latest_epochs[constellation] = epoch_dt_naive
            elif epoch_dt_naive > constellation_latest_epochs[constellation]:
                constellation_latest_epochs[constellation] = epoch_dt_naive

            # 🔑 新增：从TLE mean_motion计算轨道周期
            # SOURCE: TLE Format Specification (NASA/NORAD)
            # mean_motion单位：每天绕地球圈数
            # orbital_period = 1440分钟 / mean_motion
            if 'mean_motion' in satellite:
                mean_motion = satellite['mean_motion']
                if mean_motion > 0:  # 避免除零
                    orbital_period_minutes = 1440.0 / mean_motion
                    constellation_orbital_periods[constellation].append(orbital_period_minutes)

        distribution = {}
        for constellation, count in constellation_counts.items():
            latest_epoch = constellation_latest_epochs.get(constellation)
            if latest_epoch is None:
                continue

            # 確保輸出格式包含時區標記
            latest_epoch_str = latest_epoch.isoformat() + 'Z'

            # 计算轨道周期统计
            periods = constellation_orbital_periods.get(constellation, [])
            orbital_period_stats = {}
            if periods:
                orbital_period_stats = {
                    'min_minutes': round(min(periods), 2),
                    'max_minutes': round(max(periods), 2),
                    'avg_minutes': round(sum(periods) / len(periods), 2),
                    'sample_count': len(periods)
                }

            distribution[constellation] = {
                'count': count,
                'latest_epoch': latest_epoch_str,
                'orbital_period_stats': orbital_period_stats  # 新增字段
            }

        return distribution

    def _calculate_recommended_reference_time(self, date_dist: Dict, time_dist: Dict) -> tuple:
        """計算推薦參考時刻"""
        # 使用最新日期 + 最密集時段的中點
        latest_date = max(date_dist.keys())
        most_dense_hour = time_dist.get('most_dense_hour', 2)

        # 使用該小時的中點（例: 02:30:00）
        recommended_time = f"{latest_date}T{most_dense_hour:02d}:30:00Z"

        reason = (
            f"最新日期 {latest_date} 的最密集時段 {most_dense_hour:02d}:00-{most_dense_hour:02d}:59 "
            f"({time_dist.get('most_dense_count', 0)} 顆衛星，"
            f"{time_dist.get('most_dense_percentage', 0):.1f}%)"
        )

        return recommended_time, reason

    def _calculate_time_range(self, satellites: List[Dict]) -> Dict[str, Any]:
        """計算 epoch 時間跨度"""
        epochs = []
        for sat in satellites:
            epoch_dt = self._parse_datetime(sat['epoch_datetime'])
            # 統一移除時區資訊
            epoch_dt_naive = epoch_dt.replace(tzinfo=None) if epoch_dt.tzinfo else epoch_dt
            epochs.append(epoch_dt_naive)

        earliest = min(epochs)
        latest = max(epochs)
        span = latest - earliest

        return {
            'earliest': earliest.isoformat() + 'Z',
            'latest': latest.isoformat() + 'Z',
            'span_days': round(span.total_seconds() / 86400, 2)
        }

    def _parse_datetime(self, dt_str: str) -> datetime:
        """解析日期時間字串"""
        if isinstance(dt_str, datetime):
            return dt_str

        # 處理帶時區的 ISO 格式
        dt_str = dt_str.replace('Z', '+00:00')
        return datetime.fromisoformat(dt_str)

    def _log_analysis_summary(self, analysis: Dict):
        """輸出分析摘要到日誌"""
        logger.info("=" * 60)
        logger.info("📊 Epoch 分布分析結果")
        logger.info("=" * 60)
        logger.info(f"總衛星數: {analysis['total_satellites']}")
        logger.info(f"Epoch 時間跨度: {analysis['epoch_time_range']['span_days']:.2f} 天")
        logger.info("")
        logger.info("日期分布（前 5 名）:")
        for i, (date, info) in enumerate(list(analysis['date_distribution'].items())[:5]):
            logger.info(f"  {i+1}. {date}: {info['count']} 顆 ({info['percentage']:.1f}%)")
        logger.info("")
        logger.info("✅ 推薦參考時刻:")
        logger.info(f"   {analysis['recommended_reference_time']}")
        logger.info(f"   依據: {analysis['recommendation_reason']}")
        logger.info("=" * 60)


class EpochFilter:
    """TLE Epoch 篩選器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Epoch 篩選器

        Args:
            config: epoch_filter 配置
                {
                    'enabled': bool,
                    'mode': str,  # 'latest_date' | 'recommended_date' | 'specific_date'
                    'tolerance_hours': int,  # 必須提供（enabled=True時）
                    'specific_date': str  # 可選
                }

        Raises:
            ValueError: 當enabled=True但缺少必要配置時
        """
        self.enabled = config.get('enabled', False)
        self.mode = config.get('mode', 'latest_date')

        # ✅ Grade A 標準: 啟用時禁止使用預設值
        if self.enabled and 'tolerance_hours' not in config:
            raise ValueError(
                "tolerance_hours 必須在配置中提供\n"
                "推薦值: 24小時（基於 SGP4 精度分析）\n"
                "SOURCE: SGP4 誤差增長率 1-3km/天，48h 窗口內精度優秀\n"
                "Grade A 標準禁止使用預設值"
            )
        self.tolerance_hours = config.get('tolerance_hours', 24)  # disabled時允許預設值，改為 24h

        self.specific_date = config.get('specific_date', None)

        logger.info(f"🔍 Epoch 篩選器初始化 (enabled={self.enabled}, mode={self.mode})")

    def filter_satellites(self, satellites: List[Dict], epoch_analysis: Dict) -> List[Dict]:
        """
        根據 epoch 篩選衛星

        Args:
            satellites: 衛星列表
            epoch_analysis: epoch 分析結果

        Returns:
            篩選後的衛星列表
        """
        if not self.enabled:
            logger.info("   Epoch 篩選未啟用，保留所有衛星")
            return satellites

        if self.mode == 'latest_date':
            return self._filter_by_latest_date(satellites, epoch_analysis)
        elif self.mode == 'recommended_date':
            return self._filter_by_recommended_date(satellites, epoch_analysis)
        elif self.mode == 'specific_date':
            return self._filter_by_specific_date(satellites)
        else:
            raise ValueError(
                f"❌ 無效的 Epoch 篩選模式: {self.mode}\n"
                f"支援的模式: latest_date, recommended_date, specific_date\n"
                f"Fail-Fast 原則: 無效配置應立即失敗"
            )

    def _filter_by_latest_date(self, satellites: List[Dict], epoch_analysis: Dict) -> List[Dict]:
        """保留最新日期的衛星（當天範圍，可含小容差）"""
        date_dist = epoch_analysis['date_distribution']
        latest_date = max(date_dist.keys())

        logger.info(f"📅 篩選模式: latest_date（{latest_date} 當天）")

        # 計算目標日期的開始和結束時間
        date_start = datetime.fromisoformat(latest_date + 'T00:00:00')
        date_end = datetime.fromisoformat(latest_date + 'T23:59:59.999999')

        # 允許小容差（向前向後延伸）
        tolerance_seconds = self.tolerance_hours * 3600
        date_start_with_tolerance = date_start - timedelta(seconds=tolerance_seconds)
        date_end_with_tolerance = date_end + timedelta(seconds=tolerance_seconds)

        filtered = []
        for satellite in satellites:
            epoch_dt = self._parse_datetime(satellite['epoch_datetime'])
            # 移除時區資訊進行比較
            epoch_dt_naive = epoch_dt.replace(tzinfo=None) if epoch_dt.tzinfo else epoch_dt

            # 檢查是否在 latest_date 當天範圍內（含容差）
            if date_start_with_tolerance <= epoch_dt_naive <= date_end_with_tolerance:
                filtered.append(satellite)

        logger.info(f"✅ 篩選結果: {len(filtered)}/{len(satellites)} 顆衛星保留 ({len(filtered)/len(satellites)*100:.1f}%)")
        return filtered

    def _filter_by_recommended_date(self, satellites: List[Dict], epoch_analysis: Dict) -> List[Dict]:
        """使用分析器推薦的參考時刻篩選"""
        recommended_time_str = epoch_analysis['recommended_reference_time']
        recommended_time = datetime.fromisoformat(recommended_time_str.replace('Z', '+00:00'))

        logger.info(f"📅 篩選模式: recommended_date（{recommended_time_str} ± {self.tolerance_hours}h）")

        tolerance_seconds = self.tolerance_hours * 3600

        filtered = []
        for satellite in satellites:
            epoch_dt = self._parse_datetime(satellite['epoch_datetime'])

            time_diff = abs((epoch_dt - recommended_time).total_seconds())
            if time_diff <= tolerance_seconds:
                filtered.append(satellite)

        logger.info(f"✅ 篩選結果: {len(filtered)}/{len(satellites)} 顆衛星保留 ({len(filtered)/len(satellites)*100:.1f}%)")
        return filtered

    def _filter_by_specific_date(self, satellites: List[Dict]) -> List[Dict]:
        """使用指定日期篩選"""
        if not self.specific_date:
            logger.error("❌ specific_date 模式需要提供 specific_date 配置")
            return satellites

        logger.info(f"📅 篩選模式: specific_date（{self.specific_date} ± {self.tolerance_hours}h）")

        target_datetime = datetime.fromisoformat(self.specific_date + 'T00:00:00+00:00')
        tolerance_seconds = self.tolerance_hours * 3600

        filtered = []
        for satellite in satellites:
            epoch_dt = self._parse_datetime(satellite['epoch_datetime'])

            time_diff = abs((epoch_dt - target_datetime).total_seconds())
            if time_diff <= 86400 + tolerance_seconds:
                filtered.append(satellite)

        logger.info(f"✅ 篩選結果: {len(filtered)}/{len(satellites)} 顆衛星保留 ({len(filtered)/len(satellites)*100:.1f}%)")
        return filtered

    def _parse_datetime(self, dt_str: str) -> datetime:
        """解析日期時間字串"""
        if isinstance(dt_str, datetime):
            return dt_str

        dt_str = dt_str.replace('Z', '+00:00')
        return datetime.fromisoformat(dt_str)


# 便利函數
def create_epoch_analyzer() -> EpochAnalyzer:
    """創建 Epoch 分析器實例"""
    return EpochAnalyzer()


def create_epoch_filter(config: Dict[str, Any]) -> EpochFilter:
    """創建 Epoch 篩選器實例"""
    return EpochFilter(config)
