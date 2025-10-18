#!/usr/bin/env python3
"""
Phase 1: 數據載入與處理（學術標準版 - 無簡化假設）

✨ 關鍵改進（相較於舊版）：
1. 提取 Stage 5 完整 12 維特徵（RSRP/RSRQ/SINR/distance/elevation/doppler/velocity/atmospheric_loss...）
2. 基於軌道週期創建 Episodes（保持時間連續性）
3. 充分利用 Stage 5 的時間序列結構（~220 時間點/軌道週期）
4. ✅ 構建時間戳索引 - 用於真實鄰居衛星查找（消除 Phase 2/3/5 的簡化假設）

功能：
1. 從 orbit-engine 載入 Stage 5 (信號品質) 和 Stage 6 (3GPP 事件) 完整數據
2. 提取 12 維狀態特徵
3. 基於軌道週期創建 Episodes
4. ✅ 構建時間戳索引（每個時刻 10-15 顆同時可見衛星）
5. 分割訓練集/驗證集/測試集
6. 保存處理後的數據

執行：
    python phase1_data_loader_v2.py

輸出：
    data/train_episodes.pkl          - 訓練集 Episodes
    data/val_episodes.pkl            - 驗證集 Episodes
    data/test_episodes.pkl           - 測試集 Episodes
    data/timestamp_index.pkl         - ✅ 時間戳索引（真實鄰居查找）
    data/data_statistics.json        - 數據統計
"""

import json
import glob
import yaml
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict


class Episode:
    """
    單顆衛星的完整軌道週期 Episode

    每個 Episode 包含：
    - satellite_id: 衛星 ID
    - constellation: 星座名稱（Starlink/OneWeb）
    - time_series: 完整時間序列數據（~220 個時間點，12 維特徵）
    - gpp_events: 該衛星觸發的 3GPP 事件列表
    - episode_length: Episode 長度（時間點數）
    """

    def __init__(self, satellite_id: str, constellation: str):
        self.satellite_id = satellite_id
        self.constellation = constellation
        self.time_series = []
        self.gpp_events = []
        self.episode_length = 0

    def add_time_point(self, time_point: Dict):
        """添加時間點數據（包含完整 12 維特徵）"""
        self.time_series.append(time_point)
        self.episode_length += 1

    def add_gpp_event(self, event: Dict):
        """添加 3GPP 事件"""
        self.gpp_events.append(event)

    def to_dict(self) -> Dict:
        """轉換為字典（用於保存）"""
        return {
            'satellite_id': self.satellite_id,
            'constellation': self.constellation,
            'time_series': self.time_series,
            'gpp_events': self.gpp_events,
            'episode_length': self.episode_length
        }


class OrbitEngineDataLoader:
    """
    從 orbit-engine 載入完整數據（學術標準版）

    設計原則（SOURCE: rl.md 評估報告）：
    - 充分利用 Stage 5 的所有物理/信號特徵（12 維）
    - 保持時間序列結構（基於軌道週期）
    - 與 3GPP 事件自然對應
    """

    def __init__(self, config_path: str = "config/data_config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.orbit_engine_root = Path(self.config['orbit_engine']['root'])
        self.stage5_data = None
        self.stage6_data = None

        print(f"✅ 配置載入完成")
        print(f"   orbit-engine 路徑: {self.orbit_engine_root}")

    def load_stage5(self) -> Dict:
        """
        載入 Stage 5 數據（完整時間序列）

        SOURCE: orbit-engine Stage 5 信號品質分析輸出
        包含：signal_analysis (每顆衛星的完整軌道週期時間序列)
        """
        stage5_config = self.config['orbit_engine']['stage5']
        stage5_path = Path(stage5_config['path'])
        pattern = stage5_config['pattern']

        files = sorted(glob.glob(str(stage5_path / pattern)))
        if not files:
            raise FileNotFoundError(f"❌ 未找到 Stage 5 輸出: {stage5_path / pattern}")

        latest_file = files[-1]
        print(f"\n📥 載入 Stage 5: {latest_file}")

        with open(latest_file, 'r') as f:
            self.stage5_data = json.load(f)

        satellites = len(self.stage5_data['signal_analysis'])

        # 統計總時間點數
        total_time_points = 0
        for sat_data in self.stage5_data['signal_analysis'].values():
            total_time_points += len(sat_data['time_series'])

        print(f"   衛星數量: {satellites}")
        print(f"   總時間點數: {total_time_points:,}")
        print(f"   平均時間點/衛星: {total_time_points / satellites:.1f}")

        return self.stage5_data

    def load_stage6(self) -> Dict:
        """
        載入 Stage 6 數據（3GPP 事件）

        SOURCE: orbit-engine Stage 6 研究優化輸出
        包含：gpp_events (A3/A4/A5/D2 換手事件)
        """
        stage6_config = self.config['orbit_engine']['stage6']
        stage6_path = Path(stage6_config['path'])
        pattern = stage6_config['pattern']

        files = sorted(glob.glob(str(stage6_path / pattern)))
        if not files:
            raise FileNotFoundError(f"❌ 未找到 Stage 6 輸出: {stage6_path / pattern}")

        latest_file = files[-1]
        print(f"\n📥 載入 Stage 6: {latest_file}")

        with open(latest_file, 'r') as f:
            self.stage6_data = json.load(f)

        events = self.stage6_data['gpp_events']
        total = sum([
            len(events.get('a3_events', [])),
            len(events.get('a4_events', [])),
            len(events.get('a5_events', [])),
            len(events.get('d2_events', []))
        ])

        print(f"   A3 事件: {len(events.get('a3_events', []))}")
        print(f"   A4 事件: {len(events.get('a4_events', []))}")
        print(f"   A5 事件: {len(events.get('a5_events', []))}")
        print(f"   D2 事件: {len(events.get('d2_events', []))}")
        print(f"   總計: {total:,} 個事件")

        return self.stage6_data

    def extract_full_features(self, time_point: Dict) -> Dict:
        """
        從時間點提取完整的 12 維特徵

        ✨ 這是相較於舊版的關鍵改進！

        特徵列表（學術標準）:
        1-3. 信號品質 (3 維): RSRP, RSRQ, RS-SINR
        4-10. 物理參數 (7 維): Distance, Elevation, Doppler, Velocity, Atmospheric Loss, Path Loss, Delay
        11-12. 3GPP 偏移 (2 維): Offset MO, Cell Offset

        SOURCE:
        - orbit-engine Stage 5 信號品質分析
        - ITU-R P.676-13 (大氣衰減模型)
        - 3GPP TS 38.214 (信號品質計算)
        - rl.md Line 68-77 (學術文獻證據)

        Args:
            time_point: Stage 5 的單個時間點數據

        Returns:
            features: 完整的 12 維特徵字典
        """
        signal_quality = time_point.get('signal_quality', {})
        physical_params = time_point.get('physical_parameters', {})

        features = {
            # 信號品質 (3 維)
            'rsrp_dbm': signal_quality.get('rsrp_dbm', -999),
            'rsrq_db': signal_quality.get('rsrq_db', -999),
            'rs_sinr_db': signal_quality.get('rs_sinr_db', -999),

            # 物理參數 (7 維)
            'distance_km': physical_params.get('distance_km', -999),
            'elevation_deg': physical_params.get('elevation_deg', -999),
            'doppler_shift_hz': physical_params.get('doppler_shift_hz', -999),
            'radial_velocity_ms': physical_params.get('radial_velocity_ms', -999),
            'atmospheric_loss_db': physical_params.get('atmospheric_loss_db', -999),
            'path_loss_db': physical_params.get('path_loss_db', -999),
            'propagation_delay_ms': physical_params.get('propagation_delay_ms', -999),

            # 3GPP 偏移 (2 維)
            'offset_mo_db': signal_quality.get('offset_mo_db', 0),
            'cell_offset_db': signal_quality.get('cell_offset_db', 0),

            # 元數據
            'timestamp': time_point.get('timestamp', ''),
            'is_connectable': time_point.get('is_connectable', False)
        }

        return features

    def create_episodes(self) -> List[Episode]:
        """
        創建基於軌道週期的 Episodes

        ✨ 這是相較於舊版的關鍵改進！

        設計原則：
        - 每個 Episode = 一顆衛星的完整軌道週期（~220 時間點）
        - 保持時間連續性（5 秒間隔）
        - 關聯對應的 3GPP 事件

        SOURCE:
        - docs/final.md Line 74-84 (軌道週期分析)
        - Starlink: ~90-95 分鐘軌道週期
        - OneWeb: ~109-115 分鐘軌道週期
        - rl.md Line 108-165 (Episode 設計問題分析)

        Returns:
            episodes: Episode 對象列表
        """
        if self.stage5_data is None or self.stage6_data is None:
            raise ValueError("❌ 請先載入 Stage 5 和 Stage 6 數據")

        print("\n🔨 創建基於軌道週期的 Episodes...")

        episodes = []
        signal_analysis = self.stage5_data['signal_analysis']
        gpp_events = self.stage6_data['gpp_events']

        # 按衛星組織 3GPP 事件
        events_by_satellite = self._organize_events_by_satellite(gpp_events)

        for sat_id, sat_data in signal_analysis.items():
            # 判斷星座
            constellation = self._get_constellation(sat_id)

            # 創建 Episode
            episode = Episode(sat_id, constellation)

            # 添加時間序列數據（提取完整 12 維特徵）
            for time_point in sat_data['time_series']:
                features = self.extract_full_features(time_point)
                episode.add_time_point(features)

            # 添加對應的 3GPP 事件
            if sat_id in events_by_satellite:
                for event in events_by_satellite[sat_id]:
                    episode.add_gpp_event(event)

            episodes.append(episode)

        print(f"   創建 Episodes: {len(episodes)}")

        # 統計 Episodes 長度
        episode_lengths = [ep.episode_length for ep in episodes]
        print(f"   平均 Episode 長度: {np.mean(episode_lengths):.1f} 時間點")
        print(f"   最短 Episode: {np.min(episode_lengths)} 時間點")
        print(f"   最長 Episode: {np.max(episode_lengths)} 時間點")

        return episodes

    def _organize_events_by_satellite(self, gpp_events: Dict) -> Dict[str, List]:
        """按衛星組織 3GPP 事件"""
        events_by_sat = defaultdict(list)

        for event_type in ['a3_events', 'a4_events', 'a5_events', 'd2_events']:
            for event in gpp_events.get(event_type, []):
                # 服務衛星
                serving_sat = event.get('serving_satellite')
                if serving_sat:
                    events_by_sat[serving_sat].append({
                        'type': event_type.replace('_events', '').upper(),
                        'role': 'serving',
                        **event
                    })

                # 鄰居衛星
                neighbor_sat = event.get('neighbor_satellite') or event.get('target_satellite')
                if neighbor_sat:
                    events_by_sat[neighbor_sat].append({
                        'type': event_type.replace('_events', '').upper(),
                        'role': 'neighbor',
                        **event
                    })

        return dict(events_by_sat)

    def _get_constellation(self, satellite_id: str) -> str:
        """
        判斷衛星所屬星座

        SOURCE: orbit-engine Stage 1 星座配置
        - Starlink: NORAD ID 40000-60000 範圍
        - OneWeb: NORAD ID 44000-49000 範圍
        """
        try:
            sat_id_int = int(satellite_id)
            if 40000 <= sat_id_int < 60000:
                return 'starlink'
            elif 44000 <= sat_id_int < 50000:
                return 'oneweb'
            else:
                return 'unknown'
        except:
            return 'unknown'

    def split_episodes(self, episodes: List[Episode]) -> Tuple[List, List, List]:
        """
        分割訓練/驗證/測試集

        SOURCE: 標準 ML 數據分割比例
        - 訓練集: 75%
        - 驗證集: 12.5%
        - 測試集: 12.5%
        """
        split_config = self.config['data_split']
        train_ratio = split_config['train_ratio']
        val_ratio = split_config['val_ratio']
        seed = split_config['random_seed']

        np.random.seed(seed)

        indices = np.arange(len(episodes))
        np.random.shuffle(indices)

        n_episodes = len(episodes)
        n_train = int(n_episodes * train_ratio)
        n_val = int(n_episodes * val_ratio)

        train_idx = indices[:n_train]
        val_idx = indices[n_train:n_train + n_val]
        test_idx = indices[n_train + n_val:]

        train_episodes = [episodes[i] for i in train_idx]
        val_episodes = [episodes[i] for i in val_idx]
        test_episodes = [episodes[i] for i in test_idx]

        print(f"\n📊 數據分割:")
        print(f"   訓練集: {len(train_episodes)} Episodes ({train_ratio*100:.1f}%)")
        print(f"   驗證集: {len(val_episodes)} Episodes ({val_ratio*100:.1f}%)")
        print(f"   測試集: {len(test_episodes)} Episodes ({(1-train_ratio-val_ratio)*100:.1f}%)")

        return train_episodes, val_episodes, test_episodes

    def build_timestamp_index(self, episodes: List[Episode]) -> Dict:
        """
        構建時間戳索引 - 用於真實鄰居衛星查找

        ✅ 消除簡化假設的關鍵功能！

        原理：
        - 在同一時刻，可能有 10-15 顆衛星同時可見
        - 通過時間戳索引，可以快速找到真實鄰居衛星及其 RSRP
        - 完全基於 Stage 5 真實觀測數據，無估算或假設

        SOURCE:
        - Stage 5 signal_analysis 真實時間序列數據
        - 時間戳重疊分析顯示每個時刻有 10-15 顆衛星

        Returns:
            timestamp_index: {
                "2025-10-16T03:08:30+00:00": {
                    "55487": {12維特徵},
                    "55490": {12維特徵},
                    ...  # 同一時刻所有可見衛星
                }
            }
        """
        print(f"\n🔍 構建時間戳索引（用於真實鄰居查找）...")

        timestamp_index = defaultdict(dict)

        for episode in episodes:
            sat_id = episode.satellite_id
            for time_point in episode.time_series:
                timestamp = time_point['timestamp']
                # 將該衛星在該時刻的完整特徵加入索引
                timestamp_index[timestamp][sat_id] = time_point

        # 統計索引質量
        unique_timestamps = len(timestamp_index)
        satellites_per_timestamp = [len(sats) for sats in timestamp_index.values()]
        avg_neighbors = np.mean(satellites_per_timestamp)
        min_neighbors = np.min(satellites_per_timestamp)
        max_neighbors = np.max(satellites_per_timestamp)

        print(f"   唯一時間戳數: {unique_timestamps}")
        print(f"   平均同時可見衛星數: {avg_neighbors:.1f}")
        print(f"   最少同時可見: {min_neighbors} 顆")
        print(f"   最多同時可見: {max_neighbors} 顆")
        print(f"   ✅ 時間戳索引構建完成（用於真實鄰居 RSRP 比較）")

        return dict(timestamp_index)

    def save_episodes(self, train_episodes: List[Episode],
                     val_episodes: List[Episode],
                     test_episodes: List[Episode]):
        """保存 Episodes（使用 pickle 保留對象結構）"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        print(f"\n💾 保存 Episodes...")

        # 保存訓練集
        with open(data_dir / "train_episodes.pkl", 'wb') as f:
            pickle.dump([ep.to_dict() for ep in train_episodes], f)
        print(f"   ✅ train_episodes.pkl ({len(train_episodes)} Episodes)")

        # 保存驗證集
        with open(data_dir / "val_episodes.pkl", 'wb') as f:
            pickle.dump([ep.to_dict() for ep in val_episodes], f)
        print(f"   ✅ val_episodes.pkl ({len(val_episodes)} Episodes)")

        # 保存測試集
        with open(data_dir / "test_episodes.pkl", 'wb') as f:
            pickle.dump([ep.to_dict() for ep in test_episodes], f)
        print(f"   ✅ test_episodes.pkl ({len(test_episodes)} Episodes)")

        # 構建並保存時間戳索引（用於真實鄰居查找）
        all_episodes = train_episodes + val_episodes + test_episodes
        timestamp_index = self.build_timestamp_index(all_episodes)

        with open(data_dir / "timestamp_index.pkl", 'wb') as f:
            pickle.dump(timestamp_index, f)
        print(f"   ✅ timestamp_index.pkl (用於真實鄰居查找)")

        # 保存統計信息
        statistics = self._compute_statistics(train_episodes, val_episodes, test_episodes)
        with open(data_dir / "data_statistics.json", 'w') as f:
            json.dump(statistics, f, indent=2)
        print(f"   ✅ data_statistics.json")

    def _compute_statistics(self, train_eps: List, val_eps: List, test_eps: List) -> Dict:
        """計算數據統計"""
        all_episodes = train_eps + val_eps + test_eps

        # 統計特徵值範圍
        feature_stats = defaultdict(lambda: {'values': []})

        for episode in all_episodes:
            for time_point in episode.time_series:
                for key, value in time_point.items():
                    if isinstance(value, (int, float)) and value != -999:
                        feature_stats[key]['values'].append(value)

        # 計算統計量
        stats = {}
        for feature, data in feature_stats.items():
            if data['values']:
                values = np.array(data['values'])
                stats[feature] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'median': float(np.median(values))
                }

        # 星座統計
        constellation_counts = defaultdict(int)
        for episode in all_episodes:
            constellation_counts[episode.constellation] += 1

        return {
            'total_episodes': len(all_episodes),
            'train_episodes': len(train_eps),
            'val_episodes': len(val_eps),
            'test_episodes': len(test_eps),
            'constellation_distribution': dict(constellation_counts),
            'feature_statistics': stats,
            'generated_at': datetime.now().isoformat()
        }


def main():
    """主函數"""
    print("=" * 70)
    print("Phase 1: 數據載入與處理（學術標準版 v2）")
    print("=" * 70)

    loader = OrbitEngineDataLoader()

    # 載入數據
    loader.load_stage5()
    loader.load_stage6()

    # 創建 Episodes
    episodes = loader.create_episodes()

    # 分割數據
    train, val, test = loader.split_episodes(episodes)

    # 保存數據
    loader.save_episodes(train, val, test)

    print("\n" + "=" * 70)
    print("✅ Phase 1 完成！")
    print("=" * 70)
    print("\n✨ 關鍵改進:")
    print("   - ✅ 提取完整 12 維特徵（RSRP/RSRQ/SINR/distance/elevation/doppler...）")
    print("   - ✅ 基於軌道週期創建 Episodes（保持時間連續性）")
    print("   - ✅ 充分利用 Stage 5 的時間序列結構")
    print("\n下一步: 運行 Phase 2 (Baseline 方法)")
    print("  python phase2_baseline_methods.py")


if __name__ == "__main__":
    main()
