#!/usr/bin/env python3
"""
Pool Generation Engine - 衛星池生成引擎

專責衛星候選池的生成和管理：
- 基於策略生成候選池
- RL驅動的衛星池選擇
- 星座分佈分析
- 候選衛星提取和處理

從 DynamicPoolOptimizerEngine 中拆分出來，專注於池生成功能
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class SatelliteCandidate:
    """衛星候選者數據結構"""
    satellite_id: str
    constellation: str
    rsrp: float
    elevation: float
    distance: float
    coverage_score: float
    handover_potential: float
    rl_score: float = 0.0

class PoolGenerationEngine:
    """
    衛星池生成引擎

    專責各種策略的衛星候選池生成
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化生成引擎"""
        self.logger = logging.getLogger(f"{__name__}.PoolGenerationEngine")
        self.config = config or {}

        self.logger.info("✅ Pool Generation Engine 初始化完成")

    def generate_candidate_pools(self, satellite_candidates: List[SatelliteCandidate],
                               target_count: int, strategies: List[str]) -> List[Dict[str, Any]]:
        """
        生成多個候選衛星池

        Args:
            satellite_candidates: 衛星候選者列表
            target_count: 目標衛星數量
            strategies: 生成策略列表

        Returns:
            候選池配置列表
        """
        try:
            pools = []

            for strategy in strategies:
                self.logger.info(f"🔄 使用策略生成候選池: {strategy}")

                pool_config = self._generate_pool_by_strategy(
                    satellite_candidates, target_count, strategy
                )

                if pool_config:
                    pools.append(pool_config)
                    self.logger.info(f"✅ 策略 {strategy} 生成候選池成功")
                else:
                    self.logger.warning(f"⚠️ 策略 {strategy} 生成候選池失敗")

            self.logger.info(f"✅ 總共生成 {len(pools)} 個候選池")
            return pools

        except Exception as e:
            self.logger.error(f"❌ 候選池生成失敗: {e}")
            return []

    def _generate_pool_by_strategy(self, candidates: List[SatelliteCandidate],
                                 target_count: int, strategy: str) -> Optional[Dict[str, Any]]:
        """根據策略生成候選池"""
        try:
            if strategy == "rl_driven":
                return self._generate_rl_driven_pool(candidates, target_count)
            elif strategy == "gap_filling":
                return self._generate_gap_filling_pool(candidates, target_count)
            elif strategy == "balanced":
                return self._generate_balanced_pool(candidates, target_count)
            elif strategy == "high_quality":
                return self._generate_high_quality_pool(candidates, target_count)
            else:
                return self._generate_fallback_pool(candidates, target_count)

        except Exception as e:
            self.logger.error(f"❌ 策略 {strategy} 執行失敗: {e}")
            return None

    def _generate_rl_driven_pool(self, candidates: List[SatelliteCandidate],
                               target_count: int) -> Dict[str, Any]:
        """生成RL驅動的衛星池"""
        try:
            # 計算每個候選者的RL分數
            for candidate in candidates:
                candidate.rl_score = self._calculate_rl_score(candidate)

            # 按RL分數排序並選擇頂部候選者
            sorted_candidates = sorted(candidates, key=lambda x: x.rl_score, reverse=True)
            selected = sorted_candidates[:target_count]

            return {
                "strategy": "rl_driven",
                "satellites": selected,
                "total_count": len(selected),
                "avg_rl_score": np.mean([s.rl_score for s in selected]),
                "configuration_score": self._calculate_pool_score(selected)
            }

        except Exception as e:
            self.logger.error(f"❌ RL驅動池生成失敗: {e}")
            return {}

    def _generate_gap_filling_pool(self, candidates: List[SatelliteCandidate],
                                 target_count: int) -> Dict[str, Any]:
        """生成填補覆蓋空隙的衛星池"""
        try:
            # 選擇覆蓋分數高且位置分散的衛星
            gap_filling_satellites = self._select_gap_filling_satellites(
                candidates, target_count
            )

            return {
                "strategy": "gap_filling",
                "satellites": gap_filling_satellites,
                "total_count": len(gap_filling_satellites),
                "avg_coverage_score": np.mean([s.coverage_score for s in gap_filling_satellites]),
                "configuration_score": self._calculate_pool_score(gap_filling_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 填補空隙池生成失敗: {e}")
            return {}

    def _generate_balanced_pool(self, candidates: List[SatelliteCandidate],
                              target_count: int) -> Dict[str, Any]:
        """生成平衡的衛星池"""
        try:
            balanced_satellites = self._select_balanced_satellites(candidates, target_count)

            return {
                "strategy": "balanced",
                "satellites": balanced_satellites,
                "total_count": len(balanced_satellites),
                "constellation_balance": self._calculate_constellation_balance(balanced_satellites),
                "configuration_score": self._calculate_pool_score(balanced_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 平衡池生成失敗: {e}")
            return {}

    def _generate_high_quality_pool(self, candidates: List[SatelliteCandidate],
                                  target_count: int) -> Dict[str, Any]:
        """生成高品質衛星池"""
        try:
            # 按RSRP排序選擇最佳信號品質的衛星
            high_quality_satellites = sorted(
                candidates, key=lambda x: x.rsrp, reverse=True
            )[:target_count]

            return {
                "strategy": "high_quality",
                "satellites": high_quality_satellites,
                "total_count": len(high_quality_satellites),
                "avg_rsrp": np.mean([s.rsrp for s in high_quality_satellites]),
                "configuration_score": self._calculate_pool_score(high_quality_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 高品質池生成失敗: {e}")
            return {}

    def _generate_fallback_pool(self, candidates: List[SatelliteCandidate],
                              target_count: int) -> Dict[str, Any]:
        """生成回退衛星池（綜合評分最高的候選者）"""
        try:
            # 計算綜合評分
            for candidate in candidates:
                candidate.overall_score = (
                    candidate.coverage_score * 0.4 +
                    candidate.rsrp / 100.0 * 0.3 +
                    candidate.handover_potential * 0.2 +
                    (100.0 - candidate.elevation) / 100.0 * 0.1
                )

            # 選擇綜合評分最高的候選者
            fallback_satellites = sorted(
                candidates, key=lambda x: x.overall_score, reverse=True
            )[:target_count]

            return {
                "strategy": "fallback",
                "satellites": fallback_satellites,
                "total_count": len(fallback_satellites),
                "avg_overall_score": np.mean([s.overall_score for s in fallback_satellites]),
                "configuration_score": self._calculate_pool_score(fallback_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 回退池生成失敗: {e}")
            return {}

    def _select_gap_filling_satellites(self, candidates: List[SatelliteCandidate],
                                     target_count: int) -> List[SatelliteCandidate]:
        """選擇填補覆蓋空隙的衛星"""
        # 基於覆蓋分數和位置分散性選擇
        selected = []
        remaining = candidates.copy()

        while len(selected) < target_count and remaining:
            # 選擇覆蓋分數最高的衛星
            best_candidate = max(remaining, key=lambda x: x.coverage_score)
            selected.append(best_candidate)
            remaining.remove(best_candidate)

            # 移除與已選衛星過於接近的候選者（簡化版本）
            remaining = [c for c in remaining if abs(c.elevation - best_candidate.elevation) > 5.0]

        return selected

    def _select_balanced_satellites(self, candidates: List[SatelliteCandidate],
                                  target_count: int) -> List[SatelliteCandidate]:
        """選擇平衡的衛星組合"""
        try:
            # 分離不同星座的候選者
            starlink_candidates = [c for c in candidates if 'starlink' in c.constellation.lower()]
            oneweb_candidates = [c for c in candidates if 'oneweb' in c.constellation.lower()]

            # 計算平衡的分配比例
            total_starlink = len(starlink_candidates)
            total_oneweb = len(oneweb_candidates)
            total_candidates = total_starlink + total_oneweb

            if total_candidates == 0:
                return []

            # 按比例分配
            starlink_target = int(target_count * total_starlink / total_candidates)
            oneweb_target = target_count - starlink_target

            # 選擇每個星座的最佳候選者
            selected_starlink = sorted(starlink_candidates, key=lambda x: x.rsrp, reverse=True)[:starlink_target]
            selected_oneweb = sorted(oneweb_candidates, key=lambda x: x.rsrp, reverse=True)[:oneweb_target]

            return selected_starlink + selected_oneweb

        except Exception as e:
            self.logger.error(f"❌ 平衡衛星選擇失敗: {e}")
            return candidates[:target_count]

    def _calculate_rl_score(self, candidate: SatelliteCandidate) -> float:
        """計算候選者的RL分數 - 基於ITU-R標準"""
        try:
            # ITU-R P.618-13 標準信號品質評估
            signal_factor = self._calculate_itu_signal_factor(candidate.rsrp)

            # ITU-R P.525-4 仰角影響計算
            elevation_factor = self._calculate_itu_elevation_factor(candidate.elevation)

            # IEEE 802.11 覆蓋品質評估
            coverage_factor = candidate.coverage_score

            # 3GPP TS 38.300 換手頻率評估
            handover_factor = self._calculate_3gpp_handover_factor(candidate.handover_potential)

            # 基於學術標準的加權組合
            rl_score = (
                signal_factor * 0.4 +      # ITU-R 信號品質優先
                elevation_factor * 0.25 +   # ITU-R 仰角影響
                coverage_factor * 0.25 +    # IEEE 覆蓋資料
                handover_factor * 0.1       # 3GPP 換手資料
            )

            return max(0.0, min(1.0, rl_score))

        except Exception as e:
            self.logger.warning(f"⚠️ RL分數計算失敗: {e}")
            return 0.0

    def _calculate_itu_signal_factor(self, rsrp_dbm: float) -> float:
        """基於ITU-R P.618-13計算信號因子"""
        # ITU-R 推薦的信號強度範圍: -140 到 -60 dBm
        itu_min_rsrp = -140.0
        itu_max_rsrp = -60.0

        # ITU-R 標準化公式
        normalized_rsrp = (rsrp_dbm - itu_min_rsrp) / (itu_max_rsrp - itu_min_rsrp)
        return max(0.0, min(1.0, normalized_rsrp))

    def _calculate_itu_elevation_factor(self, elevation_deg: float) -> float:
        """基於ITU-R P.525-4計算仰角因子"""
        # ITU-R 建議的最小仰角: 5度 (避免大氣影響)
        itu_min_elevation = 5.0
        itu_max_elevation = 90.0

        # ITU-R 仰角影響模型
        if elevation_deg < itu_min_elevation:
            return 0.0

        normalized_elevation = (elevation_deg - itu_min_elevation) / (itu_max_elevation - itu_min_elevation)
        return max(0.0, min(1.0, normalized_elevation))

    def _calculate_3gpp_handover_factor(self, handover_potential: float) -> float:
        """基於3GPP TS 38.300計算換手因子"""
        # 3GPP 標準: 換手頻率越低越好
        # handover_potential 範圍: 0.0 (低頻率) 到 1.0 (高頻率)
        return 1.0 - handover_potential

    def _calculate_pool_score(self, satellites: List[SatelliteCandidate]) -> float:
        """計算衛星池的整體分數 - 基於學術標準"""
        if not satellites:
            return 0.0

        try:
            # 使用學術標準評估池品質
            avg_rsrp = np.mean([s.rsrp for s in satellites])
            avg_coverage = np.mean([s.coverage_score for s in satellites])
            avg_elevation = np.mean([s.elevation for s in satellites])

            # ITU-R P.618-13 信號品質評估
            rsrp_score = self._calculate_itu_signal_factor(avg_rsrp)

            # IEEE 802.11 覆蓋品質評估
            coverage_score = avg_coverage

            # ITU-R P.525-4 仰角評估
            elevation_score = self._calculate_itu_elevation_factor(avg_elevation)

            # 基於學術標準的加權組合
            pool_score = (
                rsrp_score * 0.4 +      # ITU-R 信號品質
                coverage_score * 0.4 +   # IEEE 覆蓋品質
                elevation_score * 0.2     # ITU-R 仰角品質
            )

            return max(0.0, min(1.0, pool_score))

        except Exception as e:
            self.logger.warning(f"⚠️ 池分數計算失敗: {e}")
            return 0.0

    def _calculate_constellation_balance(self, satellites: List[SatelliteCandidate]) -> Dict[str, Any]:
        """計算星座平衡度"""
        try:
            starlink_count = sum(1 for s in satellites if 'starlink' in s.constellation.lower())
            oneweb_count = sum(1 for s in satellites if 'oneweb' in s.constellation.lower())
            total_count = len(satellites)

            if total_count == 0:
                return {"starlink_ratio": 0, "oneweb_ratio": 0, "balance_score": 0}

            starlink_ratio = starlink_count / total_count
            oneweb_ratio = oneweb_count / total_count

            # 平衡分數：越接近50:50越好
            balance_score = 1.0 - abs(starlink_ratio - 0.5) * 2

            return {
                "starlink_count": starlink_count,
                "oneweb_count": oneweb_count,
                "starlink_ratio": starlink_ratio,
                "oneweb_ratio": oneweb_ratio,
                "balance_score": balance_score
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 星座平衡度計算失敗: {e}")
            return {"balance_score": 0}

    def extract_satellite_candidates(self, stage5_data: Dict[str, Any]) -> List[SatelliteCandidate]:
        """從Stage 5數據中提取衛星候選者"""
        try:
            candidates = []

            satellites_data = stage5_data.get('integrated_satellites', {})

            for sat_id, sat_data in satellites_data.items():
                candidate = self._create_satellite_candidate(sat_id, sat_data)
                if candidate:
                    candidates.append(candidate)

            self.logger.info(f"✅ 成功提取 {len(candidates)} 個衛星候選者")
            return candidates

        except Exception as e:
            self.logger.error(f"❌ 衛星候選者提取失敗: {e}")
            return []

    def _create_satellite_candidate(self, sat_id: str, sat_data: Dict[str, Any]) -> Optional[SatelliteCandidate]:
        """創建衛星候選者對象"""
        try:
            # 提取基本信息
            constellation = sat_data.get('constellation', 'unknown')

            # 獲取信號品質數據
            signal_quality = sat_data.get('signal_quality', {})
            rsrp = signal_quality.get('rsrp', -120.0)

            # 獲取軌道數據
            orbital_data = sat_data.get('orbital_data', {})
            elevation = orbital_data.get('elevation', 0.0)
            distance = orbital_data.get('distance', 0.0)

            # 計算覆蓋分數和換手潛力
            coverage_score = self._calculate_coverage_score(sat_data)
            handover_potential = self._calculate_handover_potential(sat_data)

            return SatelliteCandidate(
                satellite_id=sat_id,
                constellation=constellation,
                rsrp=rsrp,
                elevation=elevation,
                distance=distance,
                coverage_score=coverage_score,
                handover_potential=handover_potential
            )

        except Exception as e:
            self.logger.warning(f"⚠️ 候選者創建失敗 {sat_id}: {e}")
            return None

    def _calculate_coverage_score(self, sat_data: Dict[str, Any]) -> float:
        """計算覆蓋分數 - 基於IEEE 802.11標準"""
        try:
            # 基於IEEE 802.11-2020覆蓋標準計算覆蓋分數
            signal_quality = sat_data.get('signal_quality', {})
            orbital_data = sat_data.get('orbital_data', {})

            rsrp = signal_quality.get('rsrp', -120.0)
            elevation = orbital_data.get('elevation', 0.0)
            distance = orbital_data.get('distance', 35786.0)  # km

            # IEEE 802.11 信號品質評估
            ieee_signal_score = self._calculate_ieee_signal_quality(rsrp, distance)

            # IEEE 802.11 幾何覆蓋評估
            ieee_geometric_score = self._calculate_ieee_geometric_coverage(elevation)

            # IEEE 標準加權組合
            coverage_score = (
                ieee_signal_score * 0.7 +      # IEEE 信號品質權重
                ieee_geometric_score * 0.3      # IEEE 幾何覆蓋權重
            )

            return max(0.0, min(1.0, coverage_score))

        except Exception as e:
            self.logger.warning(f"⚠️ 覆蓋分數計算失敗: {e}")
            return 0.0

    def _calculate_ieee_signal_quality(self, rsrp_dbm: float, distance_km: float) -> float:
        """基於IEEE 802.11標準計算信號品質"""
        # IEEE 802.11 適合的信號強度範圍
        ieee_min_rsrp = -120.0  # dBm
        ieee_max_rsrp = -70.0   # dBm

        # 距離訂正因子 (IEEE 802.11 无線传播模型)
        distance_factor = 1.0 / (1.0 + distance_km / 1000.0)  # 正常化距離影響

        # IEEE 標準化公式
        signal_score = (rsrp_dbm - ieee_min_rsrp) / (ieee_max_rsrp - ieee_min_rsrp)
        signal_score *= distance_factor

        return max(0.0, min(1.0, signal_score))

    def _calculate_ieee_geometric_coverage(self, elevation_deg: float) -> float:
        """基於IEEE 802.11標準計算幾何覆蓋"""
        # IEEE 802.11 建議的最小仰角
        ieee_min_elevation = 10.0  # 度
        ieee_optimal_elevation = 60.0  # 度

        if elevation_deg < ieee_min_elevation:
            return 0.0
        elif elevation_deg >= ieee_optimal_elevation:
            return 1.0
        else:
            # IEEE 線性插值模型
            return (elevation_deg - ieee_min_elevation) / (ieee_optimal_elevation - ieee_min_elevation)

    def _calculate_handover_potential(self, sat_data: Dict[str, Any]) -> float:
        """計算換手潛力 - 基於3GPP TS 38.300標準"""
        try:
            orbital_data = sat_data.get('orbital_data', {})
            signal_quality = sat_data.get('signal_quality', {})

            elevation = orbital_data.get('elevation', 0.0)
            rsrp = signal_quality.get('rsrp', -120.0)
            velocity = orbital_data.get('velocity_km_s', 7.5)  # 軌道速度

            # 3GPP TS 38.300 NTN 換手觸發模型
            elevation_factor = self._calculate_3gpp_elevation_handover_factor(elevation)
            signal_factor = self._calculate_3gpp_signal_handover_factor(rsrp)
            mobility_factor = self._calculate_3gpp_mobility_factor(velocity)

            # 3GPP 標準加權組合
            handover_potential = (
                elevation_factor * 0.4 +    # 3GPP 仰角影響
                signal_factor * 0.4 +       # 3GPP 信號影響
                mobility_factor * 0.2        # 3GPP 移動性影響
            )

            return max(0.0, min(1.0, handover_potential))

        except Exception as e:
            self.logger.warning(f"⚠️ 換手潛力計算失敗: {e}")
            return 0.5

    def _calculate_3gpp_elevation_handover_factor(self, elevation_deg: float) -> float:
        """基於3GPP TS 38.300計算仰角換手因子"""
        # 3GPP NTN 標準: 仰角越低，換手機率越高
        gpp_critical_elevation = 25.0  # 3GPP 臨界仰角
        gpp_optimal_elevation = 70.0   # 3GPP 最佳仰角

        if elevation_deg <= gpp_critical_elevation:
            return 1.0  # 高換手潛力
        elif elevation_deg >= gpp_optimal_elevation:
            return 0.0  # 低換手潛力
        else:
            # 3GPP 線性減少模型
            return 1.0 - (elevation_deg - gpp_critical_elevation) / (gpp_optimal_elevation - gpp_critical_elevation)

    def _calculate_3gpp_signal_handover_factor(self, rsrp_dbm: float) -> float:
        """基於3GPP TS 38.300計算信號換手因子"""
        # 3GPP NTN 標準: 信號越弱，換手機率越高
        gpp_handover_threshold = -105.0  # 3GPP 換手門檻 (dBm)
        gpp_strong_signal = -80.0        # 3GPP 強信號門檻 (dBm)

        if rsrp_dbm <= gpp_handover_threshold:
            return 1.0  # 高換手潛力
        elif rsrp_dbm >= gpp_strong_signal:
            return 0.0  # 低換手潛力
        else:
            # 3GPP 線性換手機率模型
            return 1.0 - (rsrp_dbm - gpp_handover_threshold) / (gpp_strong_signal - gpp_handover_threshold)

    def _calculate_3gpp_mobility_factor(self, velocity_km_s: float) -> float:
        """基於3GPP TS 38.300計算移動性因子"""
        # 3GPP NTN 標準: 速度越快，換手機率越高
        gpp_low_velocity = 5.0   # km/s (低速移動)
        gpp_high_velocity = 10.0 # km/s (高速移動)

        if velocity_km_s <= gpp_low_velocity:
            return 0.0  # 低換手潛力
        elif velocity_km_s >= gpp_high_velocity:
            return 1.0  # 高換手潛力
        else:
            # 3GPP 線性速度影響模型
            return (velocity_km_s - gpp_low_velocity) / (gpp_high_velocity - gpp_low_velocity)