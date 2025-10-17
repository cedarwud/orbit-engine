#!/usr/bin/env python3
"""
Phase 1: 數據載入與處理

功能：
1. 從 orbit-engine 載入 Stage 6 (3GPP 事件) 和 Stage 5 (信號品質) 數據
2. 解析 A3/A4/A5/D2 事件
3. 建構換手決策樣本
4. 分割訓練集/驗證集/測試集
5. 保存處理後的數據

執行：
    python phase1_data_loader.py

輸出：
    data/handover_events.json        - 所有換手事件
    data/train_data.json             - 訓練集
    data/val_data.json               - 驗證集
    data/test_data.json              - 測試集
    data/data_statistics.json        - 數據統計
"""

import json
import glob
import yaml
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class OrbitEngineDataLoader:
    """從 orbit-engine 載入數據"""

    def __init__(self, config_path: str = "config/data_config.yaml"):
        """
        Args:
            config_path: 數據配置文件路徑
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.orbit_engine_root = Path(self.config['orbit_engine']['root'])
        self.stage6_data = None
        self.stage5_data = None

        print(f"✅ 配置載入完成")
        print(f"   orbit-engine 路徑: {self.orbit_engine_root}")

    def load_stage6(self) -> Dict:
        """載入 Stage 6 數據（3GPP 事件）"""
        stage6_config = self.config['orbit_engine']['stage6']
        stage6_path = Path(stage6_config['path'])
        pattern = stage6_config['pattern']

        # 尋找最新文件
        files = sorted(glob.glob(str(stage6_path / pattern)))
        if not files:
            raise FileNotFoundError(f"❌ 未找到 Stage 6 輸出: {stage6_path / pattern}")

        latest_file = files[-1]
        print(f"\n📥 載入 Stage 6: {latest_file}")

        with open(latest_file, 'r') as f:
            self.stage6_data = json.load(f)

        # 統計事件數量
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
        print(f"   總計: {total} 個事件")

        return self.stage6_data

    def load_stage5(self) -> Dict:
        """載入 Stage 5 數據（信號品質）"""
        stage5_config = self.config['orbit_engine']['stage5']
        stage5_path = Path(stage5_config['path'])
        pattern = stage5_config['pattern']

        # 尋找最新文件
        files = sorted(glob.glob(str(stage5_path / pattern)))
        if not files:
            raise FileNotFoundError(f"❌ 未找到 Stage 5 輸出: {stage5_path / pattern}")

        latest_file = files[-1]
        print(f"\n📥 載入 Stage 5: {latest_file}")

        with open(latest_file, 'r') as f:
            self.stage5_data = json.load(f)

        satellites = len(self.stage5_data['signal_analysis'])
        print(f"   衛星數量: {satellites}")

        return self.stage5_data

    def extract_handover_samples(self) -> List[Dict]:
        """
        從 3GPP 事件提取換手決策樣本

        Returns:
            samples: List of handover decision samples
            每個樣本包含：
            - timestamp: 時間戳
            - event_type: A3/A4/A5/D2
            - serving_satellite: 服務衛星 ID
            - neighbor_satellite: 鄰居衛星 ID
            - serving_rsrp: 服務衛星 RSRP
            - neighbor_rsrp: 鄰居衛星 RSRP
            - decision: 換手決策 (0=maintain, 1=handover)
            - metadata: 其他元數據
        """
        if self.stage6_data is None:
            raise ValueError("❌ 請先載入 Stage 6 數據")

        print("\n🔨 提取換手決策樣本...")

        samples = []
        events = self.stage6_data['gpp_events']
        event_filter = self.config['event_filter']

        # 處理 A3 事件
        if event_filter['use_a3']:
            for event in events.get('a3_events', []):
                sample = self._parse_a3_event(event)
                if sample:
                    samples.append(sample)

        # 處理 A4 事件
        if event_filter['use_a4']:
            for event in events.get('a4_events', []):
                sample = self._parse_a4_event(event)
                if sample:
                    samples.append(sample)

        # 處理 A5 事件
        if event_filter['use_a5']:
            for event in events.get('a5_events', []):
                sample = self._parse_a5_event(event)
                if sample:
                    samples.append(sample)

        # 處理 D2 事件
        if event_filter['use_d2']:
            for event in events.get('d2_events', []):
                sample = self._parse_d2_event(event)
                if sample:
                    samples.append(sample)

        print(f"   提取樣本數: {len(samples)}")

        # 按時間排序
        samples.sort(key=lambda x: x['timestamp'])

        return samples

    def _parse_a3_event(self, event: Dict) -> Dict:
        """解析 A3 事件"""
        measurements = event['measurements']

        # RSRP 過濾
        serving_rsrp = measurements['serving_rsrp_dbm']
        neighbor_rsrp = measurements['neighbor_rsrp_dbm']

        if not self._check_rsrp_valid(serving_rsrp) or not self._check_rsrp_valid(neighbor_rsrp):
            return None

        return {
            'timestamp': event['timestamp'],
            'event_type': 'A3',
            'serving_satellite': event['serving_satellite'],
            'neighbor_satellite': event['neighbor_satellite'],
            'serving_rsrp': serving_rsrp,
            'neighbor_rsrp': neighbor_rsrp,
            'rsrp_difference': measurements.get('trigger_margin_db', 0),
            'decision': 1,  # A3 建議換手
            'metadata': {
                'hysteresis_db': measurements.get('hysteresis_db', 0),
                'a3_offset_db': measurements.get('a3_offset_db', 0)
            }
        }

    def _parse_a4_event(self, event: Dict) -> Dict:
        """解析 A4 事件"""
        measurements = event['measurements']
        neighbor_rsrp = measurements['neighbor_rsrp_dbm']

        if not self._check_rsrp_valid(neighbor_rsrp):
            return None

        return {
            'timestamp': event['timestamp'],
            'event_type': 'A4',
            'serving_satellite': event.get('serving_satellite', 'unknown'),
            'neighbor_satellite': event['neighbor_satellite'],
            'serving_rsrp': -999,  # A4 不涉及服務衛星
            'neighbor_rsrp': neighbor_rsrp,
            'rsrp_difference': 0,
            'decision': 1,  # A4 建議換手
            'metadata': {
                'threshold': measurements.get('threshold', 0)
            }
        }

    def _parse_a5_event(self, event: Dict) -> Dict:
        """解析 A5 事件"""
        measurements = event['measurements']
        serving_rsrp = measurements['serving_rsrp_dbm']
        neighbor_rsrp = measurements['neighbor_rsrp_dbm']

        if not self._check_rsrp_valid(serving_rsrp) or not self._check_rsrp_valid(neighbor_rsrp):
            return None

        return {
            'timestamp': event['timestamp'],
            'event_type': 'A5',
            'serving_satellite': event['serving_satellite'],
            'neighbor_satellite': event['neighbor_satellite'],
            'serving_rsrp': serving_rsrp,
            'neighbor_rsrp': neighbor_rsrp,
            'rsrp_difference': neighbor_rsrp - serving_rsrp,
            'decision': 1,  # A5 建議換手（緊急）
            'metadata': {
                'threshold1': measurements.get('threshold1', 0),
                'threshold2': measurements.get('threshold2', 0)
            }
        }

    def _parse_d2_event(self, event: Dict) -> Dict:
        """解析 D2 事件"""
        measurements = event.get('measurements', {})

        return {
            'timestamp': event['timestamp'],
            'event_type': 'D2',
            'serving_satellite': event.get('serving_satellite', 'unknown'),
            'neighbor_satellite': event.get('target_satellite', 'unknown'),
            'serving_rsrp': measurements.get('serving_rsrp_dbm', -999),
            'neighbor_rsrp': measurements.get('target_rsrp_dbm', -999),
            'rsrp_difference': 0,
            'decision': 1,  # D2 建議換手（基於距離）
            'metadata': {
                'distance_based': True
            }
        }

    def _check_rsrp_valid(self, rsrp: float) -> bool:
        """檢查 RSRP 是否在有效範圍內"""
        min_rsrp = self.config['event_filter']['min_rsrp']
        max_rsrp = self.config['event_filter']['max_rsrp']
        return min_rsrp <= rsrp <= max_rsrp

    def split_data(self, samples: List[Dict]) -> Tuple[List, List, List]:
        """
        分割訓練/驗證/測試集

        Returns:
            (train_samples, val_samples, test_samples)
        """
        split_config = self.config['data_split']
        train_ratio = split_config['train_ratio']
        val_ratio = split_config['val_ratio']
        seed = split_config['random_seed']

        # 設置隨機種子
        np.random.seed(seed)

        # 隨機打亂
        indices = np.arange(len(samples))
        np.random.shuffle(indices)

        # 計算分割點
        n_samples = len(samples)
        n_train = int(n_samples * train_ratio)
        n_val = int(n_samples * val_ratio)

        # 分割
        train_idx = indices[:n_train]
        val_idx = indices[n_train:n_train + n_val]
        test_idx = indices[n_train + n_val:]

        train_samples = [samples[i] for i in train_idx]
        val_samples = [samples[i] for i in val_idx]
        test_samples = [samples[i] for i in test_idx]

        print(f"\n📊 數據分割:")
        print(f"   訓練集: {len(train_samples)} 樣本 ({train_ratio*100:.1f}%)")
        print(f"   驗證集: {len(val_samples)} 樣本 ({val_ratio*100:.1f}%)")
        print(f"   測試集: {len(test_samples)} 樣本 ({(1-train_ratio-val_ratio)*100:.1f}%)")

        return train_samples, val_samples, test_samples

    def save_data(self, all_samples: List[Dict],
                  train_samples: List[Dict],
                  val_samples: List[Dict],
                  test_samples: List[Dict]):
        """保存處理後的數據"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        print(f"\n💾 保存數據...")

        # 保存所有樣本
        with open(data_dir / "handover_events.json", 'w') as f:
            json.dump(all_samples, f, indent=2)
        print(f"   ✅ handover_events.json ({len(all_samples)} 樣本)")

        # 保存訓練集
        with open(data_dir / "train_data.json", 'w') as f:
            json.dump(train_samples, f, indent=2)
        print(f"   ✅ train_data.json ({len(train_samples)} 樣本)")

        # 保存驗證集
        with open(data_dir / "val_data.json", 'w') as f:
            json.dump(val_samples, f, indent=2)
        print(f"   ✅ val_data.json ({len(val_samples)} 樣本)")

        # 保存測試集
        with open(data_dir / "test_data.json", 'w') as f:
            json.dump(test_samples, f, indent=2)
        print(f"   ✅ test_data.json ({len(test_samples)} 樣本)")

        # 保存統計信息
        statistics = self._compute_statistics(all_samples)
        with open(data_dir / "data_statistics.json", 'w') as f:
            json.dump(statistics, f, indent=2)
        print(f"   ✅ data_statistics.json")

    def _compute_statistics(self, samples: List[Dict]) -> Dict:
        """計算數據統計"""
        # 事件類型統計
        event_types = {}
        rsrp_values = []

        for sample in samples:
            event_type = sample['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1

            if sample['serving_rsrp'] != -999:
                rsrp_values.append(sample['serving_rsrp'])
            if sample['neighbor_rsrp'] != -999:
                rsrp_values.append(sample['neighbor_rsrp'])

        rsrp_array = np.array(rsrp_values)

        return {
            'total_samples': len(samples),
            'event_types': event_types,
            'rsrp_statistics': {
                'mean': float(np.mean(rsrp_array)),
                'std': float(np.std(rsrp_array)),
                'min': float(np.min(rsrp_array)),
                'max': float(np.max(rsrp_array)),
                'median': float(np.median(rsrp_array))
            },
            'generated_at': datetime.now().isoformat()
        }


def main():
    """主函數"""
    print("=" * 70)
    print("Phase 1: 數據載入與處理")
    print("=" * 70)

    # 創建載入器
    loader = OrbitEngineDataLoader()

    # 載入數據
    loader.load_stage6()
    loader.load_stage5()

    # 提取樣本
    samples = loader.extract_handover_samples()

    # 分割數據
    train, val, test = loader.split_data(samples)

    # 保存數據
    loader.save_data(samples, train, val, test)

    print("\n" + "=" * 70)
    print("✅ Phase 1 完成！")
    print("=" * 70)
    print("\n下一步: 運行 Phase 2 (Baseline 方法)")
    print("  python phase2_baseline_methods.py")


if __name__ == "__main__":
    main()
