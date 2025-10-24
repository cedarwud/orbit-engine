"""
Dataset Builder - 構建 RL 訓練數據集（HDF5 格式）
"""

import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from collections import defaultdict, Counter
import numpy as np
import h5py

from .types import Stage6Output, Transition, DatasetStatistics, RLState
from .state_extractor import StateExtractor
from .reward_calculator import RewardCalculator

logger = logging.getLogger(__name__)


class RLDatasetBuilder:
    """構建 RL 訓練數據集

    從 Stage 6 輸出生成 (state, action, reward, next_state, done) transitions
    並保存為 HDF5 格式，分為 train/val/test 三個集合

    SOURCE: Sutton & Barto (2018) "Reinforcement Learning: An Introduction"
    """

    def __init__(
        self,
        state_extractor: Optional[StateExtractor] = None,
        reward_calculator: Optional[RewardCalculator] = None,
        action_selection_strategy: str = "weighted_combination",
        rsrp_weight: float = 0.6,
        distance_weight: float = 0.4,
        min_score_threshold: float = 0.5
    ):
        """初始化 Dataset Builder

        Args:
            state_extractor: State Extractor 實例（默認創建）
            reward_calculator: Reward Calculator 實例（默認創建）
            action_selection_strategy: 動作選擇策略 ("weighted_combination" 或 "sequential_priority")
            rsrp_weight: RSRP 權重（默認 0.6）
            distance_weight: 距離權重（默認 0.4）
            min_score_threshold: 最低換手分數閾值（默認 0.5，適用於 [0,1] 歸一化範圍）

        NORMALIZATION:
            使用 Min-Max 歸一化將 RSRP 和 Distance 都映射到 [0, 1]
            SOURCE: Multi-Attribute Decision Making (MADM) standard practice
            REFERENCE: MDPI Electronics 2022 "Two-Step Handover Strategy"
        """
        self.state_extractor = state_extractor or StateExtractor(max_candidates=5)
        self.reward_calculator = reward_calculator or RewardCalculator()

        # Action selection configuration
        self.action_selection_strategy = action_selection_strategy
        self.rsrp_weight = rsrp_weight
        self.distance_weight = distance_weight
        self.min_score_threshold = min_score_threshold

        # Action selection statistics (for D2 usage tracking)
        self.action_stats = {
            'd2_changed_decision': 0,    # D2 changed the final decision (真正影響)
            'd2_participated': 0,        # D2 participated in scoring (僅參與計算)
            'd2_only_decision': 0,       # D2 was the only event (D2 單獨決定)
            'total_handovers': 0,        # Total handover actions (non-stay)
            'a4_only_decisions': 0,      # A4 was the only event
            'rsrp_estimated': 0          # RSRP estimated from distance (FSPL)
        }

        logger.info(f"RLDatasetBuilder initialized with strategy: {action_selection_strategy}")
        if action_selection_strategy == "weighted_combination":
            logger.info(f"  Normalization: Min-Max to [0, 1] (MADM standard)")
            logger.info(f"  RSRP weight: {rsrp_weight}, Distance weight: {distance_weight}")
            logger.info(f"  Min score threshold: {min_score_threshold}")

    @staticmethod
    def _estimate_rsrp_margin_from_distance(distance_km: float) -> float:
        """基於 Free Space Path Loss (FSPL) 估算 RSRP margin

        用於沒有 A4 事件的候選衛星，根據距離估算其相對 RSRP 表現。

        FSPL Formula:
            FSPL(dB) = 20*log10(d_km) + 20*log10(f_MHz) + 32.44

        For LEO satellites:
            - Frequency: Ku-band ~12 GHz (Starlink), S-band ~2 GHz (3GPP)
            - Distance: 550-2000 km slant range
            - RSRP margin ∝ -FSPL ∝ -20*log10(distance)

        SOURCE:
            - ITU-R P.525-4 "Calculation of free-space attenuation"
            - Friis transmission equation
            - 3GPP TR 38.821 Section 6.1.1 "Path loss models"

        Args:
            distance_km: Ground distance to satellite (km)

        Returns:
            Estimated RSRP margin (dB, relative value for ranking)

        Note:
            This is a relative estimate for multi-attribute ranking, not absolute RSRP.
            Actual RSRP depends on EIRP, antenna gains, atmospheric effects, etc.
        """
        import math

        # FSPL component: 20*log10(distance)
        # Negate to get margin (shorter distance → higher RSRP)
        if distance_km <= 0:
            return 0.0

        # Simplified FSPL-based margin (relative)
        # Using base distance of 1000 km for normalization
        base_distance_km = 1000.0
        fspl_margin = -20 * math.log10(distance_km / base_distance_km)

        return fspl_margin

    def build_dataset(
        self,
        stage6_outputs: List[Stage6Output],
        output_path: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> DatasetStatistics:
        """構建完整數據集並保存為 HDF5

        Args:
            stage6_outputs: Stage 6 輸出列表
            output_path: HDF5 文件輸出路徑
            train_ratio: 訓練集比例（默認 70%）
            val_ratio: 驗證集比例（默認 15%）
            test_ratio: 測試集比例（默認 15%）

        Returns:
            數據集統計信息
        """
        logger.info(f"Building dataset from {len(stage6_outputs)} Stage 6 outputs...")

        # 0. 重置統計計數器
        self.action_stats = {
            'd2_changed_decision': 0,
            'd2_participated': 0,
            'd2_only_decision': 0,
            'total_handovers': 0,
            'a4_only_decisions': 0,
            'rsrp_estimated': 0
        }

        # 1. 生成所有 transitions
        all_transitions = []
        for idx, stage6_output in enumerate(stage6_outputs):
            logger.info(f"Processing file {idx+1}/{len(stage6_outputs)}: {Path(stage6_output.file_path).name}")
            transitions = self.generate_transitions(stage6_output)
            all_transitions.extend(transitions)

        if not all_transitions:
            logger.error("No transitions generated!")
            raise ValueError("Failed to generate any transitions")

        logger.info(f"✅ Generated {len(all_transitions)} total transitions")

        # 2. 分割數據集
        train_trans, val_trans, test_trans = self.split_dataset(
            all_transitions, train_ratio, val_ratio, test_ratio
        )

        # 3. 保存為 HDF5
        self.save_to_hdf5(
            {
                'train': train_trans,
                'val': val_trans,
                'test': test_trans
            },
            output_path
        )

        # 4. 計算統計信息
        statistics = self._compute_statistics(all_transitions)
        logger.info(f"📊 Dataset Statistics: {statistics.total_transitions} transitions, "
                   f"{statistics.num_episodes} episodes")

        # 5. 記錄 A4/D2 使用統計（僅在 weighted_combination 策略下）
        if self.action_selection_strategy == "weighted_combination":
            total_handovers = self.action_stats['total_handovers']
            d2_changed = self.action_stats['d2_changed_decision']
            d2_participated = self.action_stats['d2_participated']
            d2_only = self.action_stats['d2_only_decision']
            a4_only = self.action_stats['a4_only_decisions']
            rsrp_estimated = self.action_stats['rsrp_estimated']

            # D2 真實影響率 = (d2_changed + d2_only) / total_handovers
            d2_real_impact = d2_changed + d2_only
            d2_impact_rate = (d2_real_impact / total_handovers * 100) if total_handovers > 0 else 0.0

            # D2 參與率（包括未改變決策的情況）
            d2_participation_rate = ((d2_participated + d2_only) / total_handovers * 100) if total_handovers > 0 else 0.0

            # RSRP 估算使用率
            rsrp_estimation_rate = (rsrp_estimated / total_handovers * 100) if total_handovers > 0 else 0.0

            logger.info(f"")
            logger.info(f"📊 A4/D2 Decision Impact Analysis (Weights: RSRP={self.rsrp_weight}, Distance={self.distance_weight}):")
            logger.info(f"   Total handovers: {total_handovers}")
            logger.info(f"   ")
            logger.info(f"   A4-only decisions: {a4_only} ({a4_only/total_handovers*100:.1f}%)")
            logger.info(f"   D2-only decisions: {d2_only} ({d2_only/total_handovers*100:.1f}%)")
            logger.info(f"   ")
            logger.info(f"   D2 participated in scoring: {d2_participated} ({d2_participation_rate:.1f}%)")
            logger.info(f"   └─ D2 changed final decision: {d2_changed} ({d2_changed/total_handovers*100:.1f}%)")
            logger.info(f"   └─ D2 didn't change decision: {d2_participated - d2_changed} ({(d2_participated-d2_changed)/total_handovers*100:.1f}%)")
            logger.info(f"   ")
            logger.info(f"   🔬 RSRP Estimation (FSPL-based): {rsrp_estimated} ({rsrp_estimation_rate:.1f}%)")
            logger.info(f"      Candidates without A4 events had RSRP estimated from distance")
            logger.info(f"   ")
            logger.info(f"   📈 D2 Real Impact Rate: {d2_impact_rate:.1f}% (changed + d2-only)")
            logger.info(f"      (target: >15% for meaningful contribution)")

            if d2_impact_rate >= 15.0:
                logger.info(f"   ✅ D2 impact target achieved!")
            elif d2_impact_rate >= 10.0:
                logger.info(f"   ⚠️  D2 impact moderate (need +{15.0 - d2_impact_rate:.1f}% for target)")
            else:
                logger.info(f"   ❌ D2 impact below threshold (need +{15.0 - d2_impact_rate:.1f}%)")

        return statistics

    def generate_transitions(self, stage6_output: Stage6Output) -> List[Transition]:
        """從單個 Stage 6 輸出生成 transitions

        NEW策略 (修復數據生成瓶頸):
        1. 為每顆衛星生成獨立的 episode (而非整個文件一個 episode)
        2. 每個 episode 內，該衛星作為服務衛星，其他衛星作為候選
        3. 使用 greedy RSRP 策略作為動作標籤
        4. 計算獎勵函數

        SOURCE: 修復 Proposal 003 數據生成瓶頸
                舊邏輯: 2 files → 2 episodes → 40 transitions
                新邏輯: 246 satellites → 246 episodes → ~4920 transitions

        Args:
            stage6_output: Stage 6 輸出

        Returns:
            Transition 列表
        """
        transitions = []

        available_satellites = stage6_output.get_available_satellites()
        if not available_satellites:
            logger.warning("No available satellites in this output")
            return []

        # 為每顆衛星生成獨立的 episode
        for satellite_id in available_satellites:
            time_series_length = stage6_output.get_time_series_length(satellite_id)
            if time_series_length < 2:  # 至少需要2個時間點
                continue

            # 獲取該衛星的時間序列（用於提取timestamp）
            sat_id_str = str(satellite_id)
            time_series = stage6_output.signal_analysis[sat_id_str].get('time_series', [])

            # 為這顆衛星生成 episode 的 transitions
            for t in range(time_series_length - 1):  # -1 因為需要 next_state
                try:
                    # 提取當前狀態（以該衛星為服務衛星）
                    state = self.state_extractor.extract_state_for_satellite(
                        stage6_output, satellite_id, t
                    )
                    if not state:
                        continue

                    # 提取下一狀態
                    next_state = self.state_extractor.extract_state_for_satellite(
                        stage6_output, satellite_id, t + 1
                    )
                    if not next_state:
                        continue

                    # 提取當前時間戳
                    entry = time_series[t]
                    timestamp = entry.get('timestamp')
                    if not timestamp:
                        logger.warning(f"Missing timestamp for satellite {satellite_id} at t={t}")
                        continue

                    # FIXED: 使用 3GPP 事件選擇動作（A4 為主、D2 為輔）
                    # SOURCE: Proposal 003 - Extract action labels from Stage 6 gpp_events
                    action = self._select_action_from_gpp_events(
                        stage6_output,
                        satellite_id,  # serving_satellite_id
                        timestamp,
                        next_state.candidate_satellites
                    )

                    # 計算獎勵
                    reward = self.reward_calculator.compute_reward(state, action, next_state)

                    # 判斷是否結束（該衛星的最後一個時間步）
                    done = (t == time_series_length - 2)

                    # 創建 transition (每顆衛星有獨立的 episode_id)
                    transition = Transition(
                        state=state,
                        action=action,
                        reward=reward,
                        next_state=next_state,
                        done=done,
                        timestamp=state.time_features.timestamp if state.time_features else None,
                        scenario_variant_id=self._get_scenario_variant_id(stage6_output),
                        episode_id=hash(f"{stage6_output.file_path}_{satellite_id}") % 1000000
                    )

                    transitions.append(transition)

                except Exception as e:
                    logger.error(f"Error generating transition for sat {satellite_id} at t={t}: {e}")
                    continue

        logger.info(f"Generated {len(transitions)} transitions from {len(available_satellites)} satellites in {Path(stage6_output.file_path).name}")
        return transitions

    def _select_action_from_gpp_events(
        self,
        stage6_output: 'Stage6Output',
        serving_satellite_id: int,
        timestamp: str,
        candidate_satellites: List['SatelliteState']
    ) -> int:
        """使用 3GPP 事件選擇動作（路由器方法）

        根據配置的策略調用不同的實現：
        - weighted_combination: 加權組合 A4 + D2
        - sequential_priority: 順序優先（A4 → D2）

        Args:
            stage6_output: Stage 6 輸出（包含 gpp_events）
            serving_satellite_id: 當前服務衛星 ID
            timestamp: 當前時間戳
            candidate_satellites: 候選衛星列表

        Returns:
            動作 (0=stay, 1-5=handover to candidate)
        """
        if self.action_selection_strategy == "weighted_combination":
            return self._select_action_from_combined_events(
                stage6_output, serving_satellite_id, timestamp, candidate_satellites
            )
        else:  # sequential_priority (legacy)
            return self._select_action_from_gpp_events_legacy(
                stage6_output, serving_satellite_id, timestamp, candidate_satellites
            )

    def _select_action_from_combined_events(
        self,
        stage6_output: 'Stage6Output',
        serving_satellite_id: int,
        timestamp: str,
        candidate_satellites: List['SatelliteState']
    ) -> int:
        """使用加權組合策略選擇動作（Phase 1: Weighted Combination）

        同時考慮 A4 (RSRP) 和 D2 (距離) 事件，為每個候選計算組合分數：
        combined_score = rsrp_margin * w_rsrp + (distance_improvement / norm) * w_distance

        SOURCE:
        - 3GPP TS 38.331 v18.5.1 Section 5.5.4.5 (A4 event)
        - 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a (D2 event)
        - 3GPP TR 38.821 Section 6.4.2 (LEO mobility management)
        - Badini et al. (2024) IEEE TAES - Multi-objective handover criteria

        Args:
            stage6_output: Stage 6 輸出（包含 gpp_events）
            serving_satellite_id: 當前服務衛星 ID
            timestamp: 當前時間戳
            candidate_satellites: 候選衛星列表

        Returns:
            動作 (0=stay, 1-5=handover to candidate)
        """
        # 收集 A4 和 D2 事件
        a4_events = stage6_output.get_a4_events_at_time(timestamp, serving_satellite_id)
        d2_events = stage6_output.get_d2_events_at_time(timestamp, serving_satellite_id)

        # 如果沒有任何事件，保持
        if not a4_events and not d2_events:
            return 0

        # Step 1: 收集所有候選的原始指標值（未歸一化）
        # SOURCE: Min-Max Normalization for Multi-Attribute Decision Making (MADM)
        # REFERENCE: MDPI Electronics 2022 "Two-Step Handover Strategy for GEO/LEO Networks"
        a4_raw_values: Dict[int, float] = {}  # RSRP margin (dB)
        d2_raw_values: Dict[int, float] = {}  # Distance improvement (km)
        a4_estimated: set = set()  # Track which A4 values are estimated (not from real events)

        for candidate in candidate_satellites:
            candidate_id = candidate.satellite_id

            # 收集 A4 原始值（實測或估算）
            a4_event = self._find_event_for_neighbor(a4_events, candidate_id)
            if a4_event:
                # 有實際 A4 事件
                a4_raw_values[candidate_id] = a4_event['measurements'].get('trigger_margin_db', 0.0)
            else:
                # 沒有 A4 事件，但有 D2 事件 → 基於距離估算 RSRP
                d2_event = self._find_event_for_neighbor(d2_events, candidate_id)
                if d2_event and d2_event.get('distance_analysis', {}).get('handover_recommended', False):
                    # 使用 D2 的 neighbor_ground_distance 估算 RSRP margin
                    neighbor_distance = d2_event['measurements'].get('neighbor_ground_distance_km', 0.0)
                    estimated_rsrp = self._estimate_rsrp_margin_from_distance(neighbor_distance)
                    a4_raw_values[candidate_id] = estimated_rsrp
                    a4_estimated.add(candidate_id)
                    logger.debug(f"Estimated RSRP for candidate {candidate_id}: {estimated_rsrp:.2f} dB (distance={neighbor_distance:.1f} km)")

            # 收集 D2 原始值
            d2_event = self._find_event_for_neighbor(d2_events, candidate_id)
            if d2_event:
                if d2_event.get('distance_analysis', {}).get('handover_recommended', False):
                    d2_raw_values[candidate_id] = d2_event['measurements'].get('ground_distance_improvement_km', 0.0)

        # Step 2: Min-Max 歸一化到 [0, 1]
        # Formula: normalized = (value - min) / (max - min)
        a4_normalized: Dict[int, float] = {}
        d2_normalized: Dict[int, float] = {}
        has_any_d2 = bool(d2_raw_values)

        # A4 歸一化
        if len(a4_raw_values) > 1:
            a4_min = min(a4_raw_values.values())
            a4_max = max(a4_raw_values.values())
            if a4_max > a4_min:
                for cid, value in a4_raw_values.items():
                    a4_normalized[cid] = (value - a4_min) / (a4_max - a4_min)
            else:
                # 所有候選 RSRP 相同，歸一化為中性值
                for cid in a4_raw_values:
                    a4_normalized[cid] = 0.5
        elif len(a4_raw_values) == 1:
            # 只有一個候選有 A4 事件
            for cid in a4_raw_values:
                a4_normalized[cid] = 1.0

        # D2 歸一化
        if len(d2_raw_values) > 1:
            d2_min = min(d2_raw_values.values())
            d2_max = max(d2_raw_values.values())
            if d2_max > d2_min:
                for cid, value in d2_raw_values.items():
                    d2_normalized[cid] = (value - d2_min) / (d2_max - d2_min)
            else:
                # 所有候選距離改善相同
                for cid in d2_raw_values:
                    d2_normalized[cid] = 0.5
        elif len(d2_raw_values) == 1:
            # 只有一個候選有 D2 事件
            for cid in d2_raw_values:
                d2_normalized[cid] = 1.0

        # Step 3: 加權組合（現在兩個分數都在 [0, 1] 範圍）
        candidate_scores: Dict[int, float] = {}
        candidate_a4_only_scores: Dict[int, float] = {}

        all_candidate_ids = set(a4_normalized.keys()) | set(d2_normalized.keys())

        for candidate_id in all_candidate_ids:
            a4_score = a4_normalized.get(candidate_id, 0.0) * self.rsrp_weight
            d2_score = d2_normalized.get(candidate_id, 0.0) * self.distance_weight

            total_score = a4_score + d2_score

            if total_score > 0:
                candidate_scores[candidate_id] = total_score
                # 僅 A4 分數（用於對比 D2 是否改變決策）
                candidate_a4_only_scores[candidate_id] = a4_score

        # 如果沒有候選有正分數，保持
        if not candidate_scores:
            return 0

        # 選擇最高分的候選（使用完整分數 A4+D2）
        best_candidate_id = max(candidate_scores, key=candidate_scores.get)
        best_score = candidate_scores[best_candidate_id]

        # 檢查分數是否達到閾值
        if best_score < self.min_score_threshold:
            logger.debug(f"Best score {best_score:.2f} below threshold {self.min_score_threshold}, staying")
            return 0

        # 記錄統計數據：檢查 D2 是否真正改變了決策
        self.action_stats['total_handovers'] += 1

        # 檢查是否選擇了使用估算 RSRP 的候選
        if best_candidate_id in a4_estimated:
            self.action_stats['rsrp_estimated'] += 1
            logger.debug(f"Selected candidate {best_candidate_id} with estimated RSRP (FSPL-based)")

        if has_any_d2 and candidate_a4_only_scores:
            # 如果有 D2 參與，計算「僅使用 A4」會選擇哪個候選
            best_a4_only_id = max(candidate_a4_only_scores, key=candidate_a4_only_scores.get)

            # 記錄 D2 參與次數
            self.action_stats['d2_participated'] += 1

            # 檢查 D2 是否改變了決策
            if best_candidate_id != best_a4_only_id:
                self.action_stats['d2_changed_decision'] += 1
                logger.debug(f"D2 changed decision: A4-only would choose {best_a4_only_id}, but A4+D2 chose {best_candidate_id}")
            else:
                logger.debug(f"D2 participated but didn't change decision (still chose {best_candidate_id})")
        elif not a4_events and d2_events:
            # 純 D2 決策（沒有 A4 事件）
            self.action_stats['d2_only_decision'] += 1
            logger.debug(f"D2-only decision: {best_candidate_id}")
        else:
            # 純 A4 決策
            self.action_stats['a4_only_decisions'] += 1
            logger.debug(f"A4-only decision: {best_candidate_id}")

        # 找到候選索引並返回動作
        for idx, candidate in enumerate(candidate_satellites):
            if candidate.satellite_id == best_candidate_id:
                return idx + 1  # action 1-5

        # Fallback: 候選不在列表中
        return 0

    def _select_action_from_gpp_events_legacy(
        self,
        stage6_output: 'Stage6Output',
        serving_satellite_id: int,
        timestamp: str,
        candidate_satellites: List['SatelliteState']
    ) -> int:
        """使用順序優先策略選擇動作（Legacy: Sequential Priority）

        FIXED策略 (使用 Stage 6 gpp_events):
        - 優先使用 A4 事件（主要）- Neighbour > threshold
        - 輔助使用 D2 事件（補充）- 距離換手決策
        - 如果都沒有 → action = 0 (stay)

        SOURCE:
        - 3GPP TS 38.331 v18.5.1 Section 5.5.4.5 (A4 event)
        - 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a (D2 event)
        - Proposal 003 Architecture: 從 gpp_events 提取動作標籤

        Args:
            stage6_output: Stage 6 輸出（包含 gpp_events）
            serving_satellite_id: 當前服務衛星 ID
            timestamp: 當前時間戳
            candidate_satellites: 候選衛星列表

        Returns:
            動作 (0=stay, 1-5=handover to candidate)
        """
        # 1. 優先檢查 A4 事件（主要）
        a4_events = stage6_output.get_a4_events_at_time(timestamp, serving_satellite_id)
        if a4_events:
            # 有 A4 事件，選擇第一個觸發的鄰居
            neighbor_id = int(a4_events[0]['neighbor_satellite'])

            # 找到該鄰居在候選列表中的索引
            for idx, candidate in enumerate(candidate_satellites):
                if candidate.satellite_id == neighbor_id:
                    return idx + 1  # action 1-5

            # 如果鄰居不在候選列表中（可能被過濾），保持
            logger.debug(f"A4 event neighbor {neighbor_id} not in candidates, staying")
            return 0

        # 2. 輔助檢查 D2 事件（補充）
        d2_events = stage6_output.get_d2_events_at_time(timestamp, serving_satellite_id)
        if d2_events:
            # 檢查是否建議換手
            event = d2_events[0]
            if event.get('distance_analysis', {}).get('handover_recommended', False):
                neighbor_id = int(event['neighbor_satellite'])

                # 找到該鄰居在候選列表中的索引
                for idx, candidate in enumerate(candidate_satellites):
                    if candidate.satellite_id == neighbor_id:
                        return idx + 1  # action 1-5

                logger.debug(f"D2 event neighbor {neighbor_id} not in candidates, staying")
                return 0

        # 3. 沒有任何事件，保持當前衛星
        return 0

    def _find_event_for_neighbor(
        self,
        events: List[Dict[str, Any]],
        neighbor_id: int
    ) -> Optional[Dict[str, Any]]:
        """查找特定鄰居的事件

        Args:
            events: 事件列表
            neighbor_id: 鄰居衛星 ID

        Returns:
            找到的事件，如果沒有則返回 None
        """
        if not events:
            return None

        for event in events:
            if int(event.get('neighbor_satellite', -1)) == neighbor_id:
                return event

        return None

    def _get_scenario_variant_id(self, stage6_output: Stage6Output) -> str:
        """獲取場景變體 ID

        SOURCE: Proposal 002 - Scenario Diversity
                格式: "{traffic_type}_{load_pattern}"

        Args:
            stage6_output: Stage 6 輸出

        Returns:
            場景變體 ID（如 "voip_uniform"）
        """
        if not stage6_output.scenario_variants:
            return "default"

        traffic_profile = stage6_output.scenario_variants.get('traffic_profile', {})
        satellite_load = stage6_output.scenario_variants.get('satellite_load', {})

        traffic_type = traffic_profile.get('type', 'best_effort')
        load_pattern = satellite_load.get('pattern', 'uniform')

        return f"{traffic_type}_{load_pattern}"

    def split_dataset(
        self,
        transitions: List[Transition],
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[List[Transition], List[Transition], List[Transition]]:
        """分割數據集為 train/val/test

        確保 12 種場景變體均勻分佈到各個集合

        SOURCE: Standard ML practice for dataset splitting

        Args:
            transitions: 所有 transitions
            train_ratio: 訓練集比例
            val_ratio: 驗證集比例
            test_ratio: 測試集比例

        Returns:
            (train_transitions, val_transitions, test_transitions)
        """
        # 驗證比例
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.01:
            raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")

        # 按場景變體分組
        scenario_groups = defaultdict(list)
        for transition in transitions:
            scenario_id = transition.scenario_variant_id or 'default'
            scenario_groups[scenario_id].append(transition)

        train_trans = []
        val_trans = []
        test_trans = []

        # 對每個場景變體分別分割
        for scenario_id, group_transitions in scenario_groups.items():
            n_total = len(group_transitions)
            n_train = int(n_total * train_ratio)
            n_val = int(n_total * val_ratio)

            # 隨機打亂（使用固定 seed 保證可重現）
            np.random.seed(42)
            indices = np.random.permutation(n_total)

            train_indices = indices[:n_train]
            val_indices = indices[n_train:n_train + n_val]
            test_indices = indices[n_train + n_val:]

            train_trans.extend([group_transitions[i] for i in train_indices])
            val_trans.extend([group_transitions[i] for i in val_indices])
            test_trans.extend([group_transitions[i] for i in test_indices])

            logger.debug(f"Scenario {scenario_id}: {len(train_indices)} train, "
                        f"{len(val_indices)} val, {len(test_indices)} test")

        logger.info(f"✅ Dataset split: {len(train_trans)} train, "
                   f"{len(val_trans)} val, {len(test_trans)} test")

        return train_trans, val_trans, test_trans

    def save_to_hdf5(self, dataset: Dict[str, List[Transition]], output_path: str):
        """保存數據集為 HDF5 格式

        HDF5 結構:
        ├─ train/
        │  ├─ states (N, state_dim)
        │  ├─ actions (N,)
        │  ├─ rewards (N,)
        │  ├─ next_states (N, state_dim)
        │  └─ dones (N,)
        ├─ val/
        │  └─ ...
        └─ test/
           └─ ...

        Args:
            dataset: {'train': [...], 'val': [...], 'test': [...]}
            output_path: HDF5 文件輸出路徑
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving dataset to {output_path}...")

        with h5py.File(output_path, 'w') as f:
            for split_name, transitions in dataset.items():
                if not transitions:
                    logger.warning(f"Split '{split_name}' is empty, skipping")
                    continue

                logger.info(f"  Saving {split_name} split ({len(transitions)} transitions)...")

                # 轉換為 numpy arrays
                states = np.array([t.state.to_numpy() for t in transitions], dtype=np.float32)
                actions = np.array([t.action for t in transitions], dtype=np.int32)
                rewards = np.array([t.reward for t in transitions], dtype=np.float32)
                next_states = np.array([t.next_state.to_numpy() for t in transitions], dtype=np.float32)
                dones = np.array([t.done for t in transitions], dtype=np.bool_)

                # 創建 group
                group = f.create_group(split_name)

                # 保存 datasets（使用 gzip 壓縮節省空間）
                group.create_dataset('states', data=states, compression='gzip', compression_opts=4)
                group.create_dataset('actions', data=actions)
                group.create_dataset('rewards', data=rewards)
                group.create_dataset('next_states', data=next_states, compression='gzip', compression_opts=4)
                group.create_dataset('dones', data=dones)

                # 保存 metadata
                group.attrs['num_samples'] = len(transitions)
                group.attrs['state_dim'] = states.shape[1]
                group.attrs['action_dim'] = int(np.max(actions)) + 1

                logger.info(f"  ✅ {split_name}: {len(transitions)} samples, "
                           f"state_dim={states.shape[1]}, action_dim={group.attrs['action_dim']}")

        logger.info(f"✅ Dataset saved to {output_path} ({output_file.stat().st_size / 1024 / 1024:.2f} MB)")

    def _compute_statistics(self, transitions: List[Transition]) -> DatasetStatistics:
        """計算數據集統計信息

        Args:
            transitions: Transition 列表

        Returns:
            DatasetStatistics
        """
        # 計算 episode 數量
        episode_ids = set(t.episode_id for t in transitions if t.episode_id is not None)
        num_episodes = len(episode_ids) if episode_ids else 1

        # 計算平均 episode 長度
        avg_episode_length = len(transitions) / num_episodes if num_episodes > 0 else 0

        # 場景變體分布
        scenario_counts = Counter(
            t.scenario_variant_id for t in transitions if t.scenario_variant_id
        )

        # 動作分布
        action_counts = Counter(t.action for t in transitions)

        # 獎勵統計
        rewards = [t.reward for t in transitions]
        reward_stats = {
            'mean': float(np.mean(rewards)),
            'std': float(np.std(rewards)),
            'min': float(np.min(rewards)),
            'max': float(np.max(rewards))
        }

        return DatasetStatistics(
            total_transitions=len(transitions),
            num_episodes=num_episodes,
            avg_episode_length=avg_episode_length,
            scenario_variant_distribution=dict(scenario_counts),
            action_distribution=dict(action_counts),
            reward_stats=reward_stats
        )

    def validate_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """驗證數據集完整性和質量

        Args:
            dataset_path: HDF5 數據集路徑

        Returns:
            驗證報告
        """
        logger.info(f"Validating dataset: {dataset_path}")

        report = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }

        try:
            with h5py.File(dataset_path, 'r') as f:
                # 檢查 splits 存在
                expected_splits = ['train', 'val', 'test']
                for split in expected_splits:
                    if split not in f:
                        report['errors'].append(f"Missing split: {split}")
                        report['valid'] = False

                # 檢查每個 split 的數據
                for split in expected_splits:
                    if split not in f:
                        continue

                    group = f[split]

                    # 檢查必需 datasets
                    required_datasets = ['states', 'actions', 'rewards', 'next_states', 'dones']
                    for dataset_name in required_datasets:
                        if dataset_name not in group:
                            report['errors'].append(f"{split}/{dataset_name} missing")
                            report['valid'] = False

                    # 檢查 shapes 一致性
                    if all(ds in group for ds in required_datasets):
                        n_samples = len(group['states'])
                        for dataset_name in required_datasets:
                            if len(group[dataset_name]) != n_samples:
                                report['errors'].append(
                                    f"{split}/{dataset_name} length mismatch: "
                                    f"{len(group[dataset_name])} vs {n_samples}"
                                )
                                report['valid'] = False

                        report['info'][f'{split}_samples'] = n_samples

                logger.info(f"✅ Validation {'passed' if report['valid'] else 'FAILED'}")

        except Exception as e:
            report['valid'] = False
            report['errors'].append(f"Exception during validation: {e}")

        return report


def main():
    """測試 Dataset Builder"""
    logging.basicConfig(level=logging.INFO)

    from .json_parser import Stage6OutputParser

    # 解析測試文件
    parser = Stage6OutputParser()
    test_dir = "data/outputs/stage6"

    outputs = parser.parse_batch(test_dir)
    if not outputs:
        print("❌ No Stage 6 outputs found")
        return

    # 構建數據集
    builder = RLDatasetBuilder()
    output_path = "data/ml_training/rl_training_dataset.h5"

    try:
        statistics = builder.build_dataset(outputs, output_path)
        print(f"\n✅ Dataset built successfully!")
        print(f"   Total transitions: {statistics.total_transitions}")
        print(f"   Episodes: {statistics.num_episodes}")
        print(f"   Avg episode length: {statistics.avg_episode_length:.1f}")
        print(f"   Reward stats: mean={statistics.reward_stats['mean']:.3f}, "
              f"std={statistics.reward_stats['std']:.3f}")

        # 驗證數據集
        validation_report = builder.validate_dataset(output_path)
        if validation_report['valid']:
            print(f"\n✅ Dataset validation passed")
        else:
            print(f"\n❌ Dataset validation failed:")
            for error in validation_report['errors']:
                print(f"   - {error}")

    except Exception as e:
        print(f"❌ Failed to build dataset: {e}")


if __name__ == "__main__":
    main()
