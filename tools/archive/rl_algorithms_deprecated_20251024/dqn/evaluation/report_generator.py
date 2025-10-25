"""
Report Generator

生成評估報告，包括表格、圖表和 Markdown 文檔。

SOURCE: Proposal 003, Phase 4 - Evaluation Framework
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """評估報告生成器

    生成完整的策略比較報告，包括:
    - CSV 表格
    - 可視化圖表（換手、QoS、獎勵）
    - Markdown 報告

    SOURCE: Henderson et al. (2018) AAAI
            "Deep Reinforcement Learning that Matters"
            - 報告最佳實踐
    """

    def __init__(self, output_dir: str = "data/evaluation_reports"):
        """初始化報告生成器

        Args:
            output_dir: 報告輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_comparison_report(
        self,
        comparison_df: pd.DataFrame,
        detailed_results: Dict,
        report_name: Optional[str] = None
    ) -> str:
        """生成完整比較報告

        Args:
            comparison_df: 策略比較表格
            detailed_results: 詳細評估結果字典 {policy_name: metrics}
            report_name: 報告名稱（可選，默認使用時間戳）

        Returns:
            report_path: 報告目錄路徑

        包含:
        - 表格比較 (CSV)
        - 換手次數柱狀圖
        - RSRP/SNR 分布圖
        - 獎勵比較圖
        - Markdown 報告
        """
        # 創建報告目錄
        if report_name is None:
            report_name = datetime.now().strftime("evaluation_report_%Y%m%d_%H%M%S")

        report_dir = self.output_dir / report_name
        report_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating comparison report in: {report_dir}")

        # 1. 保存比較表格
        table_path = report_dir / "comparison_table.csv"
        comparison_df.to_csv(table_path, index=False)
        logger.info(f"✅ Saved comparison table: {table_path}")

        # 2. 生成圖表
        self._plot_handover_comparison(comparison_df, detailed_results, report_dir)
        self._plot_qos_comparison(comparison_df, detailed_results, report_dir)
        self._plot_reward_comparison(comparison_df, detailed_results, report_dir)

        # 3. 生成 Markdown 報告
        self._generate_markdown_report(comparison_df, detailed_results, report_dir)

        logger.info(f"✅ Report generation complete: {report_dir}")
        return str(report_dir)

    def _plot_handover_comparison(self, df: pd.DataFrame, results: Dict, output_dir: Path):
        """生成換手指標比較圖

        SOURCE: Matplotlib best practices for bar charts
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Extract policy names and metrics
        policies = df['Policy'].tolist()
        total_handovers = [results[p]['handover']['total_handovers'] for p in policies]
        unnecessary_ho = [results[p]['handover']['unnecessary_handovers'] for p in policies]

        # Plot 1: Total Handovers
        ax1 = axes[0]
        ax1.bar(policies, total_handovers, color='steelblue', alpha=0.8)
        ax1.set_title('Total Handover Count', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Total Handovers', fontsize=12)
        ax1.set_xlabel('Policy', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for i, v in enumerate(total_handovers):
            ax1.text(i, v + max(total_handovers) * 0.02, str(v), ha='center', va='bottom', fontsize=10)

        # Plot 2: Unnecessary Handovers
        ax2 = axes[1]
        ax2.bar(policies, unnecessary_ho, color='coral', alpha=0.8)
        ax2.set_title('Unnecessary Handovers (Ping-Pong)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Unnecessary Handovers', fontsize=12)
        ax2.set_xlabel('Policy', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)

        for i, v in enumerate(unnecessary_ho):
            ax2.text(i, v + max(unnecessary_ho + [1]) * 0.02, str(v), ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        plot_path = output_dir / "handover_comparison.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"✅ Saved handover comparison plot: {plot_path}")

    def _plot_qos_comparison(self, df: pd.DataFrame, results: Dict, output_dir: Path):
        """生成 QoS 指標比較圖"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        policies = df['Policy'].tolist()
        avg_rsrp = [results[p]['qos']['avg_rsrp'] for p in policies]
        avg_snr = [results[p]['qos']['avg_snr'] for p in policies]

        # Plot 1: Average RSRP
        ax1 = axes[0]
        ax1.bar(policies, avg_rsrp, color='mediumseagreen', alpha=0.8)
        ax1.set_title('Average RSRP', fontsize=14, fontweight='bold')
        ax1.set_ylabel('RSRP (dBm)', fontsize=12)
        ax1.set_xlabel('Policy', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)
        ax1.axhline(y=-110, color='red', linestyle='--', linewidth=1, label='Coverage Threshold (-110 dBm)')
        ax1.legend()

        for i, v in enumerate(avg_rsrp):
            ax1.text(i, v + abs(min(avg_rsrp)) * 0.02, f'{v:.1f}', ha='center', va='bottom', fontsize=10)

        # Plot 2: Average SNR
        ax2 = axes[1]
        ax2.bar(policies, avg_snr, color='mediumpurple', alpha=0.8)
        ax2.set_title('Average SNR', fontsize=14, fontweight='bold')
        ax2.set_ylabel('SNR (dB)', fontsize=12)
        ax2.set_xlabel('Policy', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        ax2.axhline(y=0, color='red', linestyle='--', linewidth=1, label='QoS Threshold (0 dB)')
        ax2.legend()

        for i, v in enumerate(avg_snr):
            ax2.text(i, v + abs(min(avg_snr + [0])) * 0.05, f'{v:.1f}', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        plot_path = output_dir / "qos_comparison.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"✅ Saved QoS comparison plot: {plot_path}")

    def _plot_reward_comparison(self, df: pd.DataFrame, results: Dict, output_dir: Path):
        """生成獎勵比較圖"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        policies = df['Policy'].tolist()
        total_rewards = [results[p]['reward']['total_reward'] for p in policies]
        avg_rewards = [results[p]['reward']['avg_reward'] for p in policies]
        reward_stds = [results[p]['reward']['reward_std'] for p in policies]

        # Plot 1: Total Reward
        ax1 = axes[0]
        ax1.bar(policies, total_rewards, color='darkorange', alpha=0.8)
        ax1.set_title('Total Reward', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Total Reward', fontsize=12)
        ax1.set_xlabel('Policy', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)

        for i, v in enumerate(total_rewards):
            ax1.text(i, v + max(total_rewards) * 0.02, f'{v:.1f}', ha='center', va='bottom', fontsize=10)

        # Plot 2: Average Reward with Std
        ax2 = axes[1]
        ax2.bar(policies, avg_rewards, yerr=reward_stds, color='teal', alpha=0.8, capsize=5)
        ax2.set_title('Average Reward (± Std)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Average Reward', fontsize=12)
        ax2.set_xlabel('Policy', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)

        for i, (v, std) in enumerate(zip(avg_rewards, reward_stds)):
            ax2.text(i, v + max(avg_rewards) * 0.02, f'{v:.2f}±{std:.2f}', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plot_path = output_dir / "reward_comparison.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"✅ Saved reward comparison plot: {plot_path}")

    def _generate_markdown_report(self, df: pd.DataFrame, results: Dict, output_dir: Path):
        """生成 Markdown 報告"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 計算關鍵比較（假設第一個是 DQN，第二個是 Baseline）
        policies = df['Policy'].tolist()
        if len(policies) >= 2:
            policy1, policy2 = policies[0], policies[1]
            r1, r2 = results[policy1], results[policy2]

            # 換手減少百分比
            ho_reduction = ((r2['handover']['total_handovers'] - r1['handover']['total_handovers']) /
                           r2['handover']['total_handovers'] * 100) if r2['handover']['total_handovers'] > 0 else 0

            # 不必要換手減少百分比
            unho_reduction = ((r2['handover']['unnecessary_handovers'] - r1['handover']['unnecessary_handovers']) /
                             max(r2['handover']['unnecessary_handovers'], 1) * 100)

            # RSRP 差異
            rsrp_diff = r1['qos']['avg_rsrp'] - r2['qos']['avg_rsrp']

            # 獎勵提升百分比
            reward_improvement = ((r1['reward']['total_reward'] - r2['reward']['total_reward']) /
                                 abs(r2['reward']['total_reward']) * 100) if r2['reward']['total_reward'] != 0 else 0

            key_findings = f"""## 🎯 關鍵發現

1. **換手優化**: {policy1} {'減少' if ho_reduction > 0 else '增加'} {abs(ho_reduction):.1f}% 換手次數
2. **不必要換手**: {policy1} {'降低' if unho_reduction > 0 else '增加'} {abs(unho_reduction):.1f}% 乒乓效應
3. **信號品質權衡**: {policy2 if rsrp_diff < 0 else policy1} 平均 RSRP 優 {abs(rsrp_diff):.2f} dB
4. **總體性能**: {policy1} 總獎勵{'高出' if reward_improvement > 0 else '低於'} {abs(reward_improvement):.1f}%
"""
        else:
            key_findings = "## 🎯 關鍵發現\n\n僅有單一策略，無比較數據。\n"

        # 生成 Markdown
        markdown_content = f"""# DQN Baseline Evaluation Report

**生成時間**: {timestamp}
**測試回合**: {results[policies[0]]['num_episodes']} episodes per policy
**策略數量**: {len(policies)}

---

## 📊 性能比較表格

{df.to_markdown(index=False)}

---

{key_findings}

---

## 📈 視覺化圖表

### 換手指標比較
![Handover Comparison](handover_comparison.png)

### QoS 指標比較
![QoS Comparison](qos_comparison.png)

### 獎勵指標比較
![Reward Comparison](reward_comparison.png)

---

## 📝 詳細指標

"""

        # 添加每個策略的詳細指標
        for policy_name in policies:
            r = results[policy_name]
            markdown_content += f"""### {policy_name}

**換手指標**:
- 總換手次數: {r['handover']['total_handovers']}
- 換手率: {r['handover']['handover_rate']:.3f} per minute
- 不必要換手: {r['handover']['unnecessary_handovers']} ({r['handover']['unnecessary_handover_rate']:.2%})

**QoS 指標**:
- 平均 RSRP: {r['qos']['avg_rsrp']:.2f} dBm
- 平均 SNR: {r['qos']['avg_snr']:.2f} dB
- RSRP 範圍: [{r['qos']['min_rsrp']:.2f}, {r['qos']['max_rsrp']:.2f}] dBm
- 覆蓋率: {r['qos']['coverage_rate']:.2%} (RSRP > -110 dBm)
- QoS 滿足率: {r['qos']['qos_satisfaction_rate']:.2%}

**獎勵指標**:
- 總獎勵: {r['reward']['total_reward']:.2f}
- 平均獎勵: {r['reward']['avg_reward']:.3f} ± {r['reward']['reward_std']:.3f}
- 獎勵範圍: [{r['reward']['min_reward']:.2f}, {r['reward']['max_reward']:.2f}]

---

"""

        markdown_content += f"""## 🔬 評估方法

**環境**: Satellite Handover Environment (Gymnasium)
**數據集**: HDF5 test split
**策略評估**: Greedy policy (無探索)
**評估指標**:
- 換手指標（Badini et al. 2024 IEEE TAES）
- QoS 指標（3GPP TS 38.133）
- 獎勵指標（Henderson et al. 2018 AAAI）

---

**報告生成器**: Proposal 003, Phase 4 - Evaluation Framework
**SOURCE**: Academic standards for RL evaluation

---

*此報告由 Orbit Engine DQN Evaluation Framework 自動生成*
"""

        # 保存 Markdown 報告
        report_path = output_dir / "evaluation_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"✅ Saved Markdown report: {report_path}")


def test_report_generator():
    """測試報告生成器"""
    print("Testing ReportGenerator...\n")

    # 創建模擬數據
    comparison_df = pd.DataFrame([
        {
            'Policy': 'DQN Baseline',
            'Total Handovers': 245,
            'Handover Rate (per min)': '0.123',
            'Unnecessary HO': 21,
            'Unnecessary HO Rate': '8.5%',
            'Avg RSRP (dBm)': '-35.2',
            'Avg SNR (dB)': '5.3',
            'Coverage Rate': '100.0%',
            'QoS Satisfaction': '92.3%',
            'Total Reward': '4523.5',
            'Avg Reward': '22.617',
            'Reward Std': '5.234'
        },
        {
            'Policy': 'RSRP Baseline',
            'Total Handovers': 312,
            'Handover Rate (per min)': '0.156',
            'Unnecessary HO': 47,
            'Unnecessary HO Rate': '15.1%',
            'Avg RSRP (dBm)': '-33.8',
            'Avg SNR (dB)': '6.1',
            'Coverage Rate': '100.0%',
            'QoS Satisfaction': '94.1%',
            'Total Reward': '4102.3',
            'Avg Reward': '20.512',
            'Reward Std': '6.123'
        }
    ])

    detailed_results = {
        'DQN Baseline': {
            'handover': {'total_handovers': 245, 'handover_rate': 0.123, 'unnecessary_handovers': 21, 'unnecessary_handover_rate': 0.085},
            'qos': {'avg_rsrp': -35.2, 'avg_snr': 5.3, 'min_rsrp': -42.0, 'max_rsrp': -28.0, 'coverage_rate': 1.0, 'qos_satisfaction_rate': 0.923},
            'reward': {'total_reward': 4523.5, 'avg_reward': 22.617, 'reward_std': 5.234, 'min_reward': 10.0, 'max_reward': 35.0},
            'num_episodes': 100
        },
        'RSRP Baseline': {
            'handover': {'total_handovers': 312, 'handover_rate': 0.156, 'unnecessary_handovers': 47, 'unnecessary_handover_rate': 0.151},
            'qos': {'avg_rsrp': -33.8, 'avg_snr': 6.1, 'min_rsrp': -40.0, 'max_rsrp': -26.0, 'coverage_rate': 1.0, 'qos_satisfaction_rate': 0.941},
            'reward': {'total_reward': 4102.3, 'avg_reward': 20.512, 'reward_std': 6.123, 'min_reward': 8.0, 'max_reward': 33.0},
            'num_episodes': 100
        }
    }

    # 生成報告
    generator = ReportGenerator(output_dir="data/test_reports")
    report_path = generator.generate_comparison_report(comparison_df, detailed_results, report_name="test_report")

    print(f"✅ Test report generated at: {report_path}")
    print(f"   - comparison_table.csv")
    print(f"   - handover_comparison.png")
    print(f"   - qos_comparison.png")
    print(f"   - reward_comparison.png")
    print(f"   - evaluation_report.md")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    test_report_generator()
