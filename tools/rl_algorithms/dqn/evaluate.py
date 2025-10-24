#!/usr/bin/env python3
"""
DQN Evaluation Script

評估訓練完成的 DQN 模型，並與 RSRP Baseline 比較。

使用方法:
    # 評估最佳模型
    python tools/rl_algorithms/dqn/evaluate.py

    # 評估指定檢查點
    python tools/rl_algorithms/dqn/evaluate.py --checkpoint data/models/dqn/checkpoint_ep500.pt

    # 指定測試回合數
    python tools/rl_algorithms/dqn/evaluate.py --episodes 200

SOURCE: Proposal 003, Phase 4 - Evaluation Framework
"""

import sys
from pathlib import Path
import argparse
import logging
import yaml

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.rl_algorithms.dqn.envs import SatelliteHandoverEnv
from tools.rl_algorithms.dqn.agents import DQNAgent
from tools.rl_algorithms.dqn.utils.checkpoint_manager import CheckpointManager
from tools.rl_algorithms.dqn.evaluation import (
    EvaluationMetrics,
    RSRPBaselinePolicy,
    EvaluationPipeline,
    ReportGenerator
)

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """加載訓練配置

    Args:
        config_path: 配置文件路徑

    Returns:
        config: 配置字典
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """主函數"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='DQN Evaluation Script')
    parser.add_argument('--config', type=str,
                       default='tools/rl_algorithms/dqn/config/training_config.yaml',
                       help='Training config path')
    parser.add_argument('--checkpoint', type=str, default=None,
                       help='Checkpoint path (default: load best model)')
    parser.add_argument('--episodes', type=int, default=100,
                       help='Number of test episodes')
    parser.add_argument('--output', type=str, default='data/evaluation_reports',
                       help='Output directory for reports')
    parser.add_argument('--hysteresis', type=float, default=3.0,
                       help='Hysteresis for RSRP baseline (dB)')
    args = parser.parse_args()

    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 80)
    logger.info("DQN Evaluation Pipeline")
    logger.info("=" * 80)

    # 加載配置
    logger.info(f"Loading config from: {args.config}")
    config = load_config(args.config)

    # 創建測試環境
    logger.info(f"Creating test environment...")
    test_env = SatelliteHandoverEnv(
        config['data']['dataset_path'],
        split=config['data']['test_split']
    )
    logger.info(f"✅ Test environment created (split: {config['data']['test_split']})")

    # 加載 DQN Agent
    logger.info("Loading DQN Agent...")
    dqn_agent = DQNAgent(
        state_dim=config['environment']['state_dim'],
        action_dim=config['environment']['action_dim'],
        hidden_dims=config['network']['hidden_dims'],
        learning_rate=config['training']['learning_rate'],
        gamma=config['training']['gamma'],
        device='cpu'  # 評估時使用 CPU
    )

    # 加載檢查點
    checkpoint_manager = CheckpointManager(
        save_dir=config['checkpointing']['save_dir']
    )

    if args.checkpoint:
        # 加載指定檢查點
        logger.info(f"Loading checkpoint: {args.checkpoint}")
        checkpoint = checkpoint_manager.load(args.checkpoint, dqn_agent)
    else:
        # 加載最佳模型
        logger.info("Loading best model...")
        checkpoint = checkpoint_manager.load_best(dqn_agent)

    if checkpoint:
        logger.info(f"✅ Loaded checkpoint from episode {checkpoint['episode']}")
        logger.info(f"   Metrics: {checkpoint['metrics']}")
    else:
        logger.warning("⚠️  No checkpoint loaded, using untrained model")

    # 創建 RSRP Baseline
    logger.info(f"Creating RSRP Baseline (hysteresis={args.hysteresis} dB)...")
    rsrp_baseline = RSRPBaselinePolicy(hysteresis_db=args.hysteresis)
    logger.info("✅ RSRP Baseline created")

    # 創建評估組件
    logger.info("Creating evaluation components...")
    metrics_calculator = EvaluationMetrics()
    evaluation_pipeline = EvaluationPipeline(test_env, metrics_calculator)
    report_generator = ReportGenerator(output_dir=args.output)
    logger.info("✅ Evaluation components ready")

    # 評估策略
    logger.info("=" * 80)
    logger.info(f"Starting evaluation ({args.episodes} episodes)...")
    logger.info("=" * 80)

    policies = {
        'DQN Baseline': dqn_agent,
        'RSRP Baseline': rsrp_baseline
    }

    comparison_df, detailed_results = evaluation_pipeline.compare_policies(
        policies,
        num_episodes=args.episodes,
        verbose=True
    )

    # 顯示比較表格
    logger.info("=" * 80)
    logger.info("Evaluation Results")
    logger.info("=" * 80)
    print("\n" + comparison_df.to_string(index=False) + "\n")

    # 生成報告
    logger.info("=" * 80)
    logger.info("Generating evaluation report...")
    logger.info("=" * 80)

    report_path = report_generator.generate_comparison_report(
        comparison_df,
        detailed_results,
        report_name=f"dqn_evaluation_{checkpoint['episode'] if checkpoint else 'untrained'}"
    )

    logger.info("=" * 80)
    logger.info("Evaluation Complete!")
    logger.info("=" * 80)
    logger.info(f"📊 Report saved to: {report_path}")
    logger.info(f"   - comparison_table.csv")
    logger.info(f"   - handover_comparison.png")
    logger.info(f"   - qos_comparison.png")
    logger.info(f"   - reward_comparison.png")
    logger.info(f"   - evaluation_report.md")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
