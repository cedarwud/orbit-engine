#!/usr/bin/env python3
"""
Phase 5: 評估與比較

功能：
1. 評估訓練好的 DQN 模型
2. 與 Baseline 方法比較
3. 生成完整評估報告
4. 繪製性能比較圖表

執行：
    python phase5_evaluation.py

輸出：
    results/final_evaluation.json        - 完整評估結果
    results/comparison_report.txt        - 比較報告
    results/plots/performance_comparison.png - 性能比較圖
"""

import json
import pickle
import yaml
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
from datetime import datetime

from phase3_rl_environment import HandoverEnvironment
from phase4_rl_training import DQNAgent
from phase2_baseline_methods import RSRPBasedHandover, A3TriggeredHandover, AlwaysHandoverBaseline


class Evaluator:
    """評估器"""

    def __init__(self, config: Dict):
        self.config = config

        # 載入測試數據（新格式：test_episodes.pkl）
        print("📥 載入測試數據...")
        data_path = Path("data")

        try:
            # 嘗試載入新格式（Phase 1 v2）
            with open(data_path / "test_episodes.pkl", 'rb') as f:
                test_episodes = pickle.load(f)
            print(f"   測試 Episodes: {len(test_episodes)}")

            # ✅ 載入時間戳索引（用於真實鄰居查找 - 關鍵修復！）
            try:
                with open(data_path / "timestamp_index.pkl", 'rb') as f:
                    self.timestamp_index = pickle.load(f)
                print(f"   ✅ 時間戳索引: {len(self.timestamp_index)} 個時間戳")
            except FileNotFoundError:
                print("   ❌ 找不到 timestamp_index.pkl - 這將導致獎勵函數失效！")
                print("   請重新運行: python phase1_data_loader_v2.py")
                raise

            # 轉換為 samples 格式（用於 Baseline 評估）
            print(f"   轉換 Episodes 為 Baseline 評估格式...")
            self.test_samples = self._convert_episodes_to_samples(test_episodes)
            print(f"   測試樣本數: {len(self.test_samples)}")

            # ✅ 保存 episodes 用於 DQN 評估
            self.test_episodes = test_episodes

        except FileNotFoundError:
            # 降級：嘗試載入舊格式（向後相容）
            print(f"   ⚠️  找不到 test_episodes.pkl，嘗試載入舊格式...")
            try:
                with open(data_path / "test_data.json", 'r') as f:
                    self.test_samples = json.load(f)
                print(f"   ✅ 使用舊格式 test_data.json")
                print(f"   測試樣本數: {len(self.test_samples)}")
                self.test_episodes = []
                self.timestamp_index = {}
            except FileNotFoundError:
                raise FileNotFoundError(
                    "找不到測試數據！請先運行: python phase1_data_loader_v2.py"
                )

        # ✅ 創建測試環境（傳入 episodes 和 timestamp_index）
        self.test_env = HandoverEnvironment(self.test_episodes, config, timestamp_index=self.timestamp_index, mode='eval')

        # 評估結果
        self.results = {}

    def _convert_episodes_to_samples(self, episodes: List) -> List[Dict]:
        """
        將 Episode 格式轉換為評估所需的 samples 格式

        ✅ 使用真實鄰居數據（無簡化假設）

        Args:
            episodes: Episode 對象列表（來自 phase1_data_loader_v2.py）

        Returns:
            samples: 換手決策樣本列表（舊格式，供評估使用）

        SOURCE: 相容性轉換函數，支援 Phase 1 v2 的新數據格式
        """
        samples = []

        # ✅ 載入時間戳索引（用於真實鄰居查找）
        timestamp_index = None
        try:
            data_path = Path("data")
            with open(data_path / "timestamp_index.pkl", 'rb') as f:
                timestamp_index = pickle.load(f)
            print(f"   ✅ 時間戳索引已載入（用於真實鄰居 RSRP）")
        except FileNotFoundError:
            print(f"   ⚠️  找不到 timestamp_index.pkl，將使用簡化版本")

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
                timestamp = time_point.get('timestamp', '')
                serving_rsrp = time_point.get('rsrp_dbm', -999)

                # ✅ 從時間戳索引找到真實鄰居
                best_neighbor_id = 'unknown'
                best_neighbor_rsrp = -999

                if timestamp_index and timestamp in timestamp_index:
                    neighbors = timestamp_index[timestamp]

                    # 找到最佳鄰居（RSRP 最高且優於當前衛星）
                    for neighbor_id, neighbor_data in neighbors.items():
                        # 排除當前服務衛星自己
                        if neighbor_id == satellite_id:
                            continue

                        neighbor_rsrp = neighbor_data.get('rsrp_dbm', -999)
                        if neighbor_rsrp > best_neighbor_rsrp:
                            best_neighbor_rsrp = neighbor_rsrp
                            best_neighbor_id = neighbor_id

                # 提取基本信號品質
                sample = {
                    'satellite_id': satellite_id,
                    'serving_satellite': satellite_id,
                    'neighbor_satellite': best_neighbor_id,  # ✅ 真實鄰居衛星
                    'serving_rsrp': serving_rsrp,
                    'neighbor_rsrp': best_neighbor_rsrp,  # ✅ 真實鄰居 RSRP（從時間戳索引獲取）
                    'event_type': 'NONE',
                    'timestamp': timestamp,
                    # 物理參數
                    'serving_elevation': time_point.get('elevation_deg', None),
                    'serving_distance': time_point.get('distance_km', None),
                }
                samples.append(sample)

            # 從 3GPP 事件創建樣本
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

    def evaluate_dqn(self, model_path: str) -> Dict:
        """評估 DQN 模型"""
        print(f"\n🤖 評估 DQN 模型: {model_path}")

        # 載入模型
        state_dim = self.config['environment']['state_dim']
        action_dim = self.config['environment']['action_dim']
        agent = DQNAgent(state_dim, action_dim, self.config['dqn'])

        if Path(model_path).exists():
            agent.load(model_path)
            print(f"   ✅ 模型載入成功")
        else:
            print(f"   ❌ 模型不存在: {model_path}")
            return {}

        # 執行評估
        state, _ = self.test_env.reset()
        total_reward = 0
        handover_count = 0
        ping_pong_count = 0
        qos_values = []
        decisions = []

        step = 0
        while True:
            # 選擇動作（不探索）
            action = agent.select_action(state, eval_mode=True)
            decisions.append(action)

            # 執行動作
            next_state, reward, terminated, truncated, info = self.test_env.step(action)

            total_reward += reward

            if action == 1:
                handover_count += 1

            # 收集 QoS 數據
            if step < len(self.test_samples):
                sample = self.test_samples[step]
                if sample['serving_rsrp'] != -999:
                    qos_values.append(sample['serving_rsrp'])

            state = next_state
            step += 1

            if terminated or truncated:
                break

        # 計算 Ping-Pong
        for i in range(len(decisions) - 1):
            if decisions[i] == 1 and decisions[i + 1] == 1:
                if self._is_ping_pong(i):
                    ping_pong_count += 1

        # 計算指標
        metrics = {
            'total_reward': total_reward,
            'average_reward': total_reward / len(self.test_samples),
            'handover_count': handover_count,
            'handover_frequency': handover_count / len(self.test_samples),
            'ping_pong_count': ping_pong_count,
            'ping_pong_rate': ping_pong_count / max(handover_count, 1),
            'average_qos': np.mean(qos_values) if qos_values else -999,
            'total_samples': len(self.test_samples)
        }

        print(f"   總獎勵: {metrics['total_reward']:.2f}")
        print(f"   換手頻率: {metrics['handover_frequency']:.3f}")
        print(f"   Ping-Pong 率: {metrics['ping_pong_rate']:.2%}")
        print(f"   平均 QoS: {metrics['average_qos']:.2f} dBm")

        return metrics

    def evaluate_baseline(self, method_name: str, method) -> Dict:
        """評估 Baseline 方法"""
        print(f"\n📊 評估 Baseline: {method_name}")

        handover_count = 0
        ping_pong_count = 0
        qos_values = []
        decisions = []

        for sample in self.test_samples:
            decision = method.decide(sample)
            decisions.append(decision)

            if decision == 1:
                handover_count += 1

            if sample['serving_rsrp'] != -999:
                qos_values.append(sample['serving_rsrp'])

        # 計算 Ping-Pong
        for i in range(len(decisions) - 1):
            if decisions[i] == 1 and decisions[i + 1] == 1:
                if self._is_ping_pong(i):
                    ping_pong_count += 1

        metrics = {
            'handover_count': handover_count,
            'handover_frequency': handover_count / len(self.test_samples),
            'ping_pong_count': ping_pong_count,
            'ping_pong_rate': ping_pong_count / max(handover_count, 1),
            'average_qos': np.mean(qos_values) if qos_values else -999,
            'total_samples': len(self.test_samples)
        }

        print(f"   換手頻率: {metrics['handover_frequency']:.3f}")
        print(f"   Ping-Pong 率: {metrics['ping_pong_rate']:.2%}")
        print(f"   平均 QoS: {metrics['average_qos']:.2f} dBm")

        return metrics

    def _is_ping_pong(self, index: int) -> bool:
        """檢測 Ping-Pong"""
        if index + 1 >= len(self.test_samples):
            return False

        sample1 = self.test_samples[index]
        sample2 = self.test_samples[index + 1]

        return (sample1['serving_satellite'] == sample2['neighbor_satellite'] and
                sample1['neighbor_satellite'] == sample2['serving_satellite'])

    def compare_all_methods(self):
        """比較所有方法"""
        print("\n" + "=" * 70)
        print("評估所有方法")
        print("=" * 70)

        # 評估 DQN
        dqn_best = self.evaluate_dqn("results/models/dqn_best.pth")
        if dqn_best:
            self.results['DQN (Best)'] = dqn_best

        # 評估 Baseline
        self.results['RSRP-based'] = self.evaluate_baseline(
            "RSRP-based",
            RSRPBasedHandover(serving_threshold=-100.0, neighbor_threshold=-90.0, margin=3.0)
        )

        self.results['A3-triggered'] = self.evaluate_baseline(
            "A3-triggered",
            A3TriggeredHandover(a3_offset=3.0)
        )

        self.results['Always-handover'] = self.evaluate_baseline(
            "Always-handover",
            AlwaysHandoverBaseline()
        )

    def save_results(self):
        """保存評估結果"""
        results_file = Path("results/final_evaluation.json")

        output = {
            'evaluation_time': datetime.now().isoformat(),
            'test_samples': len(self.test_samples),
            'methods': self.results
        }

        with open(results_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n💾 評估結果已保存: {results_file}")

    def generate_report(self):
        """生成比較報告"""
        report_file = Path("results/comparison_report.txt")

        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("Handover-RL 最終評估報告\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"測試樣本數: {len(self.test_samples)}\n\n")

            # 表頭
            f.write(f"{'方法':<20} {'換手頻率':<15} {'Ping-Pong率':<15} {'平均QoS(dBm)':<15}\n")
            f.write("-" * 80 + "\n")

            # 各方法結果
            for method_name, metrics in self.results.items():
                f.write(f"{method_name:<20} "
                        f"{metrics['handover_frequency']:<15.3f} "
                        f"{metrics['ping_pong_rate']:<15.2%} "
                        f"{metrics['average_qos']:<15.2f}\n")

            # 最佳方法
            f.write("\n" + "=" * 80 + "\n")
            f.write("性能排名:\n\n")

            # 按換手頻率排序（越低越好）
            sorted_by_frequency = sorted(self.results.items(),
                                        key=lambda x: x[1]['handover_frequency'])
            f.write("換手頻率（越低越好）:\n")
            for i, (name, metrics) in enumerate(sorted_by_frequency, 1):
                f.write(f"  {i}. {name}: {metrics['handover_frequency']:.3f}\n")

            # 按 Ping-Pong 率排序（越低越好）
            sorted_by_pingpong = sorted(self.results.items(),
                                       key=lambda x: x[1]['ping_pong_rate'])
            f.write("\nPing-Pong 率（越低越好）:\n")
            for i, (name, metrics) in enumerate(sorted_by_pingpong, 1):
                f.write(f"  {i}. {name}: {metrics['ping_pong_rate']:.2%}\n")

            # 按平均 QoS 排序（越高越好）
            sorted_by_qos = sorted(self.results.items(),
                                  key=lambda x: x[1]['average_qos'],
                                  reverse=True)
            f.write("\n平均 QoS（越高越好）:\n")
            for i, (name, metrics) in enumerate(sorted_by_qos, 1):
                f.write(f"  {i}. {name}: {metrics['average_qos']:.2f} dBm\n")

            f.write("\n" + "=" * 80 + "\n")

        print(f"📄 比較報告已保存: {report_file}")

    def plot_comparison(self):
        """繪製性能比較圖"""
        methods = list(self.results.keys())
        handover_freq = [self.results[m]['handover_frequency'] for m in methods]
        ping_pong_rate = [self.results[m]['ping_pong_rate'] for m in methods]
        avg_qos = [self.results[m]['average_qos'] for m in methods]

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

        # 換手頻率
        colors = ['#2ecc71' if 'DQN' in m else '#3498db' for m in methods]
        ax1.bar(range(len(methods)), handover_freq, color=colors)
        ax1.set_xticks(range(len(methods)))
        ax1.set_xticklabels(methods, rotation=45, ha='right')
        ax1.set_ylabel('Handover Frequency')
        ax1.set_title('換手頻率（越低越好）')
        ax1.grid(True, alpha=0.3)

        # Ping-Pong 率
        ax2.bar(range(len(methods)), ping_pong_rate, color=colors)
        ax2.set_xticks(range(len(methods)))
        ax2.set_xticklabels(methods, rotation=45, ha='right')
        ax2.set_ylabel('Ping-Pong Rate')
        ax2.set_title('Ping-Pong 率（越低越好）')
        ax2.grid(True, alpha=0.3)

        # 平均 QoS
        ax3.bar(range(len(methods)), avg_qos, color=colors)
        ax3.set_xticks(range(len(methods)))
        ax3.set_xticklabels(methods, rotation=45, ha='right')
        ax3.set_ylabel('Average RSRP (dBm)')
        ax3.set_title('平均 QoS（越高越好）')
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        plot_file = Path("results/plots/performance_comparison.png")
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"📊 性能比較圖已保存: {plot_file}")

        plt.close()


def main():
    """主函數"""
    print("=" * 70)
    print("Phase 5: 最終評估與比較")
    print("=" * 70)

    # 載入配置
    with open("config/rl_config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    # 創建評估器
    evaluator = Evaluator(config)

    # 比較所有方法
    evaluator.compare_all_methods()

    # 保存結果
    evaluator.save_results()

    # 生成報告
    evaluator.generate_report()

    # 繪製圖表
    evaluator.plot_comparison()

    print("\n" + "=" * 70)
    print("✅ 所有階段完成！")
    print("=" * 70)
    print("\n📁 輸出文件:")
    print("   results/final_evaluation.json      - 完整評估結果")
    print("   results/comparison_report.txt      - 比較報告")
    print("   results/plots/                     - 所有圖表")
    print("\n🎓 下一步: 撰寫論文，使用這些結果作為實驗數據")


if __name__ == "__main__":
    main()
