#!/usr/bin/env python3
"""
ML Training Data Generator - Main Entry Point

從 Stage 6 JSON 輸出生成 RL 訓練數據集（HDF5 格式）

Usage:
    python generate_dataset.py [--config CONFIG_PATH]

SOURCE: Proposal 003, Phase 1 - ML Data Generator
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ml_training_data_generator.core.json_parser import Stage6OutputParser
from tools.ml_training_data_generator.core.state_extractor import StateExtractor
from tools.ml_training_data_generator.core.reward_calculator import RewardCalculator
from tools.ml_training_data_generator.core.dataset_builder import RLDatasetBuilder


def setup_logging(config: dict):
    """設置日誌系統

    Args:
        config: 配置字典
    """
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 基本配置
    handlers = [logging.StreamHandler(sys.stdout)]

    # 如果配置要求，同時保存到文件
    if log_config.get('save_to_file', False):
        log_dir = Path(log_config.get('log_dir', 'logs/ml_data_generator'))
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"data_generator_{timestamp}.log"

        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )

    logger = logging.getLogger(__name__)
    if log_config.get('save_to_file', False):
        logger.info(f"Logging to file: {log_file}")

    return logger


def load_config(config_path: str) -> dict:
    """加載配置文件

    Args:
        config_path: YAML 配置文件路徑

    Returns:
        配置字典
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def validate_config(config: dict) -> bool:
    """驗證配置完整性

    Args:
        config: 配置字典

    Returns:
        True if valid
    """
    required_sections = ['paths', 'state_extraction', 'reward_function', 'dataset_split']

    for section in required_sections:
        if section not in config:
            print(f"❌ Missing config section: {section}")
            return False

    # 驗證權重總和
    reward_config = config.get('reward_function', {})
    weights_sum = (
        reward_config.get('weight_qos', 0) +
        reward_config.get('weight_signal', 0) +
        reward_config.get('weight_handover', 0)
    )
    if abs(weights_sum - 1.0) > 0.01:
        print(f"❌ Reward weights must sum to 1.0, got {weights_sum}")
        return False

    # 驗證數據集分割比例
    split_config = config.get('dataset_split', {})
    split_sum = (
        split_config.get('train_ratio', 0) +
        split_config.get('val_ratio', 0) +
        split_config.get('test_ratio', 0)
    )
    if abs(split_sum - 1.0) > 0.01:
        print(f"❌ Dataset split ratios must sum to 1.0, got {split_sum}")
        return False

    return True


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description='ML Training Data Generator - Convert Stage 6 outputs to RL training data'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='tools/ml_training_data_generator/config/data_generator_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Override Stage 6 input directory'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        help='Override HDF5 output path'
    )

    args = parser.parse_args()

    # 1. 加載配置
    print(f"📖 Loading configuration from: {args.config}")
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return 1

    # 驗證配置
    if not validate_config(config):
        print(f"❌ Config validation failed")
        return 1

    print(f"✅ Configuration loaded and validated")

    # 2. 設置日誌
    logger = setup_logging(config)
    logger.info("=" * 70)
    logger.info("ML Training Data Generator")
    logger.info("SOURCE: Proposal 003, Phase 1")
    logger.info("=" * 70)

    # 3. 準備路徑
    paths_config = config['paths']
    input_dir = args.input_dir or paths_config['stage6_input_dir']
    output_dir = Path(paths_config['output_dir'])
    output_filename = paths_config['output_filename']

    if args.output_path:
        output_path = Path(args.output_path)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename_with_timestamp = output_filename.replace('.h5', f'_{timestamp}.h5')
        output_path = output_dir / output_filename_with_timestamp

    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output path: {output_path}")

    # 4. 解析 Stage 6 JSON 輸出
    logger.info("-" * 70)
    logger.info("Step 1: Parsing Stage 6 JSON outputs")
    logger.info("-" * 70)

    parser_obj = Stage6OutputParser()
    stage6_outputs = parser_obj.parse_batch(
        input_dir,
        pattern=paths_config.get('stage6_pattern', 'stage6_research*.json')
    )

    if not stage6_outputs:
        logger.error("❌ No Stage 6 outputs found or parsed successfully")
        return 1

    logger.info(f"✅ Parsed {len(stage6_outputs)} Stage 6 outputs")

    # 獲取數據集信息
    dataset_info = parser_obj.get_dataset_info(stage6_outputs)
    logger.info(f"📊 Dataset Info:")
    for key, value in dataset_info.items():
        logger.info(f"   {key}: {value}")

    # 5. 初始化組件
    logger.info("-" * 70)
    logger.info("Step 2: Initializing components")
    logger.info("-" * 70)

    state_config = config['state_extraction']
    reward_config = config['reward_function']
    action_config = config.get('action_selection', {})

    state_extractor = StateExtractor(
        max_candidates=state_config['max_candidates']
    )

    reward_calculator = RewardCalculator(
        weight_qos=reward_config['weight_qos'],
        weight_signal=reward_config['weight_signal'],
        weight_handover=reward_config['weight_handover']
    )

    # Action selection parameters (Phase 1: Weighted Combination with Min-Max Normalization)
    # SOURCE: Min-Max Normalization - MADM standard practice
    strategy = action_config.get('strategy', 'weighted_combination')
    weights = action_config.get('weights', {})
    thresholds = action_config.get('thresholds', {})

    dataset_builder = RLDatasetBuilder(
        state_extractor=state_extractor,
        reward_calculator=reward_calculator,
        action_selection_strategy=strategy,
        rsrp_weight=weights.get('rsrp', 0.6),
        distance_weight=weights.get('distance', 0.4),
        min_score_threshold=thresholds.get('min_score', 0.5)  # Updated for [0,1] normalized range
    )

    logger.info("✅ Components initialized")

    # 6. 構建數據集
    logger.info("-" * 70)
    logger.info("Step 3: Building RL training dataset")
    logger.info("-" * 70)

    split_config = config['dataset_split']

    try:
        statistics = dataset_builder.build_dataset(
            stage6_outputs=stage6_outputs,
            output_path=str(output_path),
            train_ratio=split_config['train_ratio'],
            val_ratio=split_config['val_ratio'],
            test_ratio=split_config['test_ratio']
        )

        logger.info("✅ Dataset built successfully")

        # 7. 顯示統計信息
        logger.info("-" * 70)
        logger.info("Step 4: Dataset Statistics")
        logger.info("-" * 70)

        logger.info(f"📊 Total transitions: {statistics.total_transitions}")
        logger.info(f"📊 Number of episodes: {statistics.num_episodes}")
        logger.info(f"📊 Avg episode length: {statistics.avg_episode_length:.1f}")

        logger.info(f"\n📊 Scenario Variant Distribution:")
        for variant, count in statistics.scenario_variant_distribution.items():
            percentage = count / statistics.total_transitions * 100
            logger.info(f"   {variant}: {count} ({percentage:.1f}%)")

        logger.info(f"\n📊 Action Distribution:")
        for action, count in statistics.action_distribution.items():
            percentage = count / statistics.total_transitions * 100
            action_name = "stay" if action == 0 else f"handover_{action}"
            logger.info(f"   {action_name}: {count} ({percentage:.1f}%)")

        logger.info(f"\n📊 Reward Statistics:")
        for key, value in statistics.reward_stats.items():
            logger.info(f"   {key}: {value:.3f}")

        # 8. 驗證數據集
        logger.info("-" * 70)
        logger.info("Step 5: Validating dataset")
        logger.info("-" * 70)

        validation_report = dataset_builder.validate_dataset(str(output_path))

        if validation_report['valid']:
            logger.info("✅ Dataset validation passed")
            for split, samples in validation_report['info'].items():
                logger.info(f"   {split}: {samples} samples")
        else:
            logger.error("❌ Dataset validation failed:")
            for error in validation_report['errors']:
                logger.error(f"   - {error}")
            return 1

        # 9. 完成
        logger.info("=" * 70)
        logger.info("✅ ML Training Data Generator completed successfully")
        logger.info(f"📁 Output: {output_path}")
        logger.info(f"💾 File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"❌ Failed to build dataset: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
