#!/usr/bin/env python3
"""
Phase 2: Baseline 換手方法實作與評估

功能：
1. 實作 4 種 Baseline 換手決策方法
   - RSRP-based: 傳統 RSRP 門檻法
   - A3-triggered: 3GPP A3 事件觸發法
   - D2-distance: 距離/仰角換手法
   - Always-handover: 總是換手（對照組）

2. 評估 Baseline 方法性能
   - Handover Frequency（換手頻率）
   - Ping-Pong Rate（乒乓換手率）
   - Average QoS（平均 RSRP）

3. 保存評估結果

執行：
    python phase2_baseline_methods.py

輸出：
    results/baseline_results.json    - Baseline 評估結果
    results/baseline_comparison.txt  - 比較報告
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class BaselineMethod:
    """Baseline 換手方法基類"""

    def __init__(self, name: str):
        self.name = name

    def decide(self, sample: Dict) -> int:
        """
        換手決策

        Args:
            sample: 換手決策樣本

        Returns:
            decision: 0 = maintain (保持), 1 = handover (換手)
        """
        raise NotImplementedError


class RSRPBasedHandover(BaselineMethod):
    """
    RSRP 門檻換手法

    決策規則：
    - 當服務衛星 RSRP < threshold1 (較差)
    - 且鄰居衛星 RSRP > threshold2 (良好)
    - 且鄰居 RSRP 優於服務衛星至少 margin dB
    → 執行換手

    SOURCE: 3GPP TS 38.300 v18.0.0 傳統換手策略
    """

    def __init__(self,
                 serving_threshold: float = -100.0,  # SOURCE: 3GPP TS 38.133 v18.3.0 Table 10.1.19.2-1 (RSRP measurement accuracy)
                 neighbor_threshold: float = -90.0,   # SOURCE: 3GPP TS 38.133 v18.3.0 Table 10.1.19.2-1
                 margin: float = 3.0):                 # SOURCE: 3GPP TS 36.331 v18.1.0 Section 5.5.4 (Hysteresis typical value)
        """
        Args:
            serving_threshold: 服務衛星 RSRP 門檻 (dBm)
            neighbor_threshold: 鄰居衛星 RSRP 門檻 (dBm)
            margin: 換手裕度 (dB)
        """
        super().__init__("RSRP-based")
        self.serving_threshold = serving_threshold
        self.neighbor_threshold = neighbor_threshold
        self.margin = margin

    def decide(self, sample: Dict) -> int:
        """換手決策"""
        serving_rsrp = sample['serving_rsrp']
        neighbor_rsrp = sample['neighbor_rsrp']

        # 忽略無效值
        if serving_rsrp == -999 or neighbor_rsrp == -999:
            return 0  # maintain

        # 檢查門檻條件
        if serving_rsrp < self.serving_threshold:
            if neighbor_rsrp > self.neighbor_threshold:
                if neighbor_rsrp > serving_rsrp + self.margin:
                    return 1  # handover

        return 0  # maintain


class A3TriggeredHandover(BaselineMethod):
    """
    A3 事件觸發換手法

    決策規則：
    - 當 A3 事件發生時，直接換手
    - 其他事件根據 RSRP 差異決定

    SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4
    """

    def __init__(self, a3_offset: float = 3.0):  # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4 (a3-Offset typical value)
        """
        Args:
            a3_offset: A3 偏移量 (dB)
        """
        super().__init__("A3-triggered")
        self.a3_offset = a3_offset

    def decide(self, sample: Dict) -> int:
        """換手決策"""
        event_type = sample['event_type']

        # A3 事件直接換手
        if event_type == 'A3':
            return 1

        # A5 事件（緊急）直接換手
        if event_type == 'A5':
            return 1

        # 其他事件根據 RSRP 差異
        serving_rsrp = sample['serving_rsrp']
        neighbor_rsrp = sample['neighbor_rsrp']

        if serving_rsrp != -999 and neighbor_rsrp != -999:
            if neighbor_rsrp > serving_rsrp + self.a3_offset:
                return 1

        return 0


class D2DistanceBasedHandover(BaselineMethod):
    """
    D2 距離換手法

    決策規則：
    - 當服務衛星仰角 < min_elevation（低仰角信號差）
    - 或距離 > max_distance（距離過遠延遲高）
    → 換手到更優衛星

    SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a (Event D2: Distance-based handover)
    """

    def __init__(self,
                 min_elevation: float = 10.0,    # SOURCE: 3GPP TR 38.821 v17.0.0 Section 6.1.2 (Minimum elevation angle for NTN)
                 max_distance: float = 2000.0):   # SOURCE: ITU-R M.1184 Annex 1 (LEO satellite maximum service distance)
        """
        Args:
            min_elevation: 最小仰角門檻 (度)
            max_distance: 最大距離門檻 (km)
        """
        super().__init__("D2-distance")
        self.min_elevation = min_elevation
        self.max_distance = max_distance

    def decide(self, sample: Dict) -> int:
        """換手決策"""
        # 檢查是否有物理參數數據
        serving_elevation = sample.get('serving_elevation', None)
        serving_distance = sample.get('serving_distance', None)

        # 如果無數據，保持連接
        if serving_elevation is None or serving_distance is None:
            return 0  # maintain

        # 檢查 D2 條件
        if serving_elevation < self.min_elevation:
            return 1  # handover（仰角過低）

        if serving_distance > self.max_distance:
            return 1  # handover（距離過遠）

        return 0  # maintain


class AlwaysHandoverBaseline(BaselineMethod):
    """
    總是換手法（對照組）

    決策規則：
    - 只要有鄰居衛星，就換手

    用途：作為最差情況對照
    """

    def __init__(self):
        super().__init__("Always-handover")

    def decide(self, sample: Dict) -> int:
        """換手決策"""
        return 1  # 總是換手


class BaselineEvaluator:
    """Baseline 方法評估器"""

    def __init__(self):
        self.methods = []
        self.results = {}

    def add_method(self, method: BaselineMethod):
        """添加評估方法"""
        self.methods.append(method)

    def evaluate(self, samples: List[Dict]) -> Dict:
        """
        評估所有 Baseline 方法

        Args:
            samples: 測試樣本

        Returns:
            results: 評估結果
        """
        print(f"\n📊 評估 Baseline 方法...")
        print(f"   測試樣本數: {len(samples)}")

        for method in self.methods:
            print(f"\n   評估 {method.name}...")
            metrics = self._evaluate_method(method, samples)
            self.results[method.name] = metrics

            # 顯示結果
            print(f"      Handover Frequency: {metrics['handover_frequency']:.2f}")
            print(f"      Ping-Pong Rate: {metrics['ping_pong_rate']:.2%}")
            print(f"      Average QoS: {metrics['average_qos']:.2f} dBm")

        return self.results

    def _evaluate_method(self, method: BaselineMethod, samples: List[Dict]) -> Dict:
        """評估單個方法"""
        handover_count = 0
        ping_pong_count = 0
        qos_values = []
        decisions = []

        # 執行決策
        for sample in samples:
            decision = method.decide(sample)
            decisions.append(decision)

            if decision == 1:
                handover_count += 1

            # 收集 QoS 數據
            if sample['serving_rsrp'] != -999:
                qos_values.append(sample['serving_rsrp'])

        # 計算 Ping-Pong（連續換手）
        for i in range(len(decisions) - 1):
            if decisions[i] == 1 and decisions[i + 1] == 1:
                # 檢查是否在短時間內來回換手
                if self._is_ping_pong(samples[i], samples[i + 1]):
                    ping_pong_count += 1

        # 計算指標
        handover_frequency = handover_count / len(samples)
        ping_pong_rate = ping_pong_count / max(handover_count, 1)
        average_qos = np.mean(qos_values) if qos_values else -999

        return {
            'handover_count': handover_count,
            'handover_frequency': handover_frequency,
            'ping_pong_count': ping_pong_count,
            'ping_pong_rate': ping_pong_rate,
            'average_qos': average_qos,
            'total_samples': len(samples)
        }

    def _is_ping_pong(self, sample1: Dict, sample2: Dict) -> bool:
        """
        檢測 Ping-Pong 換手

        定義：在短時間內（< 10秒）來回換手到同一衛星
        """
        # 簡化版：檢查是否換回原服務衛星
        return (sample1['serving_satellite'] == sample2['neighbor_satellite'] and
                sample1['neighbor_satellite'] == sample2['serving_satellite'])

    def save_results(self):
        """保存評估結果"""
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)

        # 保存 JSON 結果
        results_file = results_dir / "baseline_results.json"
        output = {
            'evaluation_time': datetime.now().isoformat(),
            'methods': self.results
        }

        with open(results_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n💾 結果已保存: {results_file}")

        # 生成比較報告
        self._generate_comparison_report(results_dir)

    def _generate_comparison_report(self, results_dir: Path):
        """生成比較報告（文本格式）"""
        report_file = results_dir / "baseline_comparison.txt"

        with open(report_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("Baseline 方法比較報告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 表頭
            f.write(f"{'方法':<20} {'換手頻率':<15} {'Ping-Pong率':<15} {'平均QoS(dBm)':<15}\n")
            f.write("-" * 70 + "\n")

            # 各方法結果
            for method_name, metrics in self.results.items():
                f.write(f"{method_name:<20} "
                        f"{metrics['handover_frequency']:<15.2f} "
                        f"{metrics['ping_pong_rate']:<15.2%} "
                        f"{metrics['average_qos']:<15.2f}\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write("指標說明:\n")
            f.write("- 換手頻率: 換手次數 / 總樣本數（越低越好）\n")
            f.write("- Ping-Pong率: 乒乓換手次數 / 總換手次數（越低越好）\n")
            f.write("- 平均QoS: 平均 RSRP 值（越高越好）\n")
            f.write("=" * 70 + "\n")

        print(f"📄 比較報告已保存: {report_file}")


def convert_episodes_to_samples(episodes: List) -> List[Dict]:
    """
    將 Episode 格式轉換為 Baseline 評估所需的 samples 格式

    Args:
        episodes: Episode 對象列表（來自 phase1_data_loader_v2.py）

    Returns:
        samples: 換手決策樣本列表（舊格式，供 Baseline 評估使用）

    SOURCE: 相容性轉換函數，支援 Phase 1 v2 的新數據格式
    """
    samples = []

    for episode in episodes:
        # 處理字典格式的 Episode
        if isinstance(episode, dict):
            satellite_id = episode['satellite_id']
            time_series = episode.get('time_series', episode.get('time_points', []))
            gpp_events = episode.get('gpp_events', [])
        else:
            # 處理對象格式的 Episode
            satellite_id = episode.satellite_id
            time_series = getattr(episode, 'time_points', getattr(episode, 'time_series', []))
            gpp_events = episode.gpp_events

        # 從時間序列創建樣本（每個時間點一個樣本）
        for time_point in time_series:
            # 提取基本信號品質
            sample = {
                'satellite_id': satellite_id,
                'serving_satellite': satellite_id,
                'neighbor_satellite': 'unknown',  # Baseline 方法通常不需要明確鄰居
                'serving_rsrp': time_point.get('rsrp_dbm', -999),
                'neighbor_rsrp': -999,  # 簡化：假設無鄰居數據
                'event_type': 'NONE',
                'timestamp': time_point.get('timestamp', ''),
                # 物理參數（用於 D2 方法）
                'serving_elevation': time_point.get('elevation_deg', None),
                'serving_distance': time_point.get('distance_km', None),
            }
            samples.append(sample)

        # 從 3GPP 事件創建樣本（用於 A3-triggered 評估）
        for event in gpp_events:
            if event.get('role') == 'serving':
                measurements = event.get('measurements', {})
                sample = {
                    'satellite_id': satellite_id,
                    'serving_satellite': event.get('serving_satellite', satellite_id),
                    'neighbor_satellite': event.get('neighbor_satellite', 'unknown'),
                    'serving_rsrp': measurements.get('serving_rsrp_dbm', -999),
                    'neighbor_rsrp': measurements.get('neighbor_rsrp_dbm', -999),
                    'event_type': event.get('type', 'NONE'),
                    'timestamp': event.get('timestamp', ''),
                    'serving_elevation': None,
                    'serving_distance': None,
                }
                samples.append(sample)

    return samples


def main():
    """主函數"""
    print("=" * 70)
    print("Phase 2: Baseline 換手方法評估")
    print("=" * 70)

    # 載入測試數據（新格式：test_episodes.pkl）
    print("\n📥 載入測試數據...")
    data_path = Path("data")

    try:
        # 嘗試載入新格式（Phase 1 v2）
        with open(data_path / "test_episodes.pkl", 'rb') as f:
            test_episodes = pickle.load(f)
        print(f"   測試 Episodes: {len(test_episodes)}")

        # 轉換為 samples 格式
        print(f"   轉換 Episodes 為 Baseline 評估格式...")
        test_samples = convert_episodes_to_samples(test_episodes)
        print(f"   測試樣本數: {len(test_samples)}")

    except FileNotFoundError:
        # 降級：嘗試載入舊格式（向後相容）
        print(f"   ⚠️  找不到 test_episodes.pkl，嘗試載入舊格式...")
        try:
            with open(data_path / "test_data.json", 'r') as f:
                test_samples = json.load(f)
            print(f"   ✅ 使用舊格式 test_data.json")
            print(f"   測試樣本數: {len(test_samples)}")
        except FileNotFoundError:
            print(f"   ❌ 找不到測試數據！")
            print(f"   請先運行: python phase1_data_loader_v2.py")
            return

    # 創建評估器
    evaluator = BaselineEvaluator()

    # 添加 Baseline 方法
    evaluator.add_method(RSRPBasedHandover(
        serving_threshold=-100.0,
        neighbor_threshold=-90.0,
        margin=3.0
    ))

    evaluator.add_method(A3TriggeredHandover(
        a3_offset=3.0
    ))

    evaluator.add_method(D2DistanceBasedHandover(
        min_elevation=10.0,
        max_distance=2000.0
    ))

    evaluator.add_method(AlwaysHandoverBaseline())

    # 執行評估
    results = evaluator.evaluate(test_samples)

    # 保存結果
    evaluator.save_results()

    print("\n" + "=" * 70)
    print("✅ Phase 2 完成！")
    print("=" * 70)
    print("\n下一步: 運行 Phase 3 (RL 環境設計)")
    print("  python phase3_rl_environment.py")


if __name__ == "__main__":
    main()
