#!/usr/bin/env python3
"""
RL Data Generator

從 Stage 5/6 JSON 輸出生成 HDF5 訓練數據集。

使用方法:
    python tools/ml_data_generator/rl_data_generator.py \
        --stage5 data/outputs/stage5/stage5_signal_quality.json \
        --stage6 data/outputs/stage6/stage6_research.json \
        --output data/ml_training/rl_training_dataset.h5

SOURCE: Proposal 003, Phase 1 - ML Data Generator
"""

import argparse
import json
import h5py
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_stage5_data(stage5_path):
    """加載 Stage 5 數據

    SOURCE: Stage 5 輸出格式
    """
    logger.info(f"Loading Stage 5 data from: {stage5_path}")
    with open(stage5_path, 'r') as f:
        data = json.load(f)

    logger.info(f"✅ Loaded Stage 5 data")
    return data


def load_stage6_data(stage6_path):
    """加載 Stage 6 數據

    SOURCE: Stage 6 輸出格式
    """
    logger.info(f"Loading Stage 6 data from: {stage6_path}")
    with open(stage6_path, 'r') as f:
        data = json.load(f)

    # 檢查是否有 ML 訓練數據
    if 'ml_training_data' not in data:
        raise KeyError("Stage 6 data does not contain 'ml_training_data' field")

    rl_data = data['ml_training_data']
    logger.info(f"✅ Loaded Stage 6 RL training data: {len(rl_data)} transitions")
    return rl_data


def extract_transitions(rl_data):
    """從 RL 訓練數據提取 transitions

    Returns:
        states, actions, rewards, next_states, dones

    SOURCE: Sutton & Barto (2018) - MDP Transition
    """
    states = []
    actions = []
    rewards = []
    next_states = []
    dones = []

    for transition in rl_data:
        # State (53 維)
        state = np.array(transition['state'], dtype=np.float32)
        states.append(state)

        # Action
        action = int(transition['action'])
        actions.append(action)

        # Reward
        reward = float(transition['reward'])
        rewards.append(reward)

        # Next State (53 維)
        next_state = np.array(transition['next_state'], dtype=np.float32)
        next_states.append(next_state)

        # Done
        done = bool(transition.get('done', False))
        dones.append(done)

    return (
        np.array(states, dtype=np.float32),
        np.array(actions, dtype=np.int32),
        np.array(rewards, dtype=np.float32),
        np.array(next_states, dtype=np.float32),
        np.array(dones, dtype=bool)
    )


def split_dataset(states, actions, rewards, next_states, dones, train_ratio=0.7, val_ratio=0.15):
    """分割數據集

    Args:
        train_ratio: 訓練集比例 (default: 0.7)
        val_ratio: 驗證集比例 (default: 0.15)
        test_ratio: 測試集比例 (default: 0.15, auto-calculated)

    Returns:
        train, val, test splits

    SOURCE: Standard ML practice
    """
    n = len(states)
    indices = np.random.permutation(n)

    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]

    def split_data(data, idx):
        return data[idx]

    train = {
        'states': split_data(states, train_idx),
        'actions': split_data(actions, train_idx),
        'rewards': split_data(rewards, train_idx),
        'next_states': split_data(next_states, train_idx),
        'dones': split_data(dones, train_idx)
    }

    val = {
        'states': split_data(states, val_idx),
        'actions': split_data(actions, val_idx),
        'rewards': split_data(rewards, val_idx),
        'next_states': split_data(next_states, val_idx),
        'dones': split_data(dones, val_idx)
    }

    test = {
        'states': split_data(states, test_idx),
        'actions': split_data(actions, test_idx),
        'rewards': split_data(rewards, test_idx),
        'next_states': split_data(next_states, test_idx),
        'dones': split_data(dones, test_idx)
    }

    logger.info(f"Dataset split: train={len(train_idx)}, val={len(val_idx)}, test={len(test_idx)}")

    return train, val, test


def save_to_hdf5(output_path, train, val, test):
    """保存到 HDF5 文件

    SOURCE: HDF5 best practices
    """
    logger.info(f"Saving to HDF5: {output_path}")

    with h5py.File(output_path, 'w') as f:
        # 保存訓練集
        train_group = f.create_group('train')
        train_group.create_dataset('states', data=train['states'], compression='gzip')
        train_group.create_dataset('actions', data=train['actions'], compression='gzip')
        train_group.create_dataset('rewards', data=train['rewards'], compression='gzip')
        train_group.create_dataset('next_states', data=train['next_states'], compression='gzip')
        train_group.create_dataset('dones', data=train['dones'], compression='gzip')
        train_group.attrs['num_samples'] = len(train['states'])
        train_group.attrs['state_dim'] = train['states'].shape[1]
        train_group.attrs['action_dim'] = int(train['actions'].max() + 1)

        # 保存驗證集
        val_group = f.create_group('val')
        val_group.create_dataset('states', data=val['states'], compression='gzip')
        val_group.create_dataset('actions', data=val['actions'], compression='gzip')
        val_group.create_dataset('rewards', data=val['rewards'], compression='gzip')
        val_group.create_dataset('next_states', data=val['next_states'], compression='gzip')
        val_group.create_dataset('dones', data=val['dones'], compression='gzip')
        val_group.attrs['num_samples'] = len(val['states'])
        val_group.attrs['state_dim'] = val['states'].shape[1]
        val_group.attrs['action_dim'] = int(val['actions'].max() + 1)

        # 保存測試集
        test_group = f.create_group('test')
        test_group.create_dataset('states', data=test['states'], compression='gzip')
        test_group.create_dataset('actions', data=test['actions'], compression='gzip')
        test_group.create_dataset('rewards', data=test['rewards'], compression='gzip')
        test_group.create_dataset('next_states', data=test['next_states'], compression='gzip')
        test_group.create_dataset('dones', data=test['dones'], compression='gzip')
        test_group.attrs['num_samples'] = len(test['states'])
        test_group.attrs['state_dim'] = test['states'].shape[1]
        test_group.attrs['action_dim'] = int(test['actions'].max() + 1)

        # 保存元數據
        f.attrs['creation_time'] = datetime.now().isoformat()
        f.attrs['total_samples'] = len(train['states']) + len(val['states']) + len(test['states'])
        f.attrs['source'] = 'Proposal 003, Phase 1 - ML Data Generator'

    logger.info(f"✅ HDF5 file saved successfully")


def print_statistics(output_path):
    """打印數據集統計信息"""
    with h5py.File(output_path, 'r') as f:
        logger.info("=" * 60)
        logger.info("Dataset Statistics:")
        logger.info("=" * 60)

        for split in ['train', 'val', 'test']:
            group = f[split]
            logger.info(f"\n{split.upper()}:")
            logger.info(f"  Samples: {group.attrs['num_samples']}")
            logger.info(f"  State dim: {group.attrs['state_dim']}")
            logger.info(f"  Action dim: {group.attrs['action_dim']}")
            logger.info(f"  Reward range: [{group['rewards'][:].min():.2f}, {group['rewards'][:].max():.2f}]")
            logger.info(f"  Done count: {group['dones'][:].sum()}")

        logger.info(f"\nTotal samples: {f.attrs['total_samples']}")
        logger.info(f"Creation time: {f.attrs['creation_time']}")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Generate HDF5 training dataset from Stage 5/6 JSON')
    parser.add_argument('--stage5', type=str, required=True, help='Path to Stage 5 JSON file')
    parser.add_argument('--stage6', type=str, required=True, help='Path to Stage 6 JSON file')
    parser.add_argument('--output', type=str, required=True, help='Output HDF5 file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed (default: 42)')
    args = parser.parse_args()

    # 設置隨機種子
    np.random.seed(args.seed)

    # 檢查輸入文件
    if not Path(args.stage5).exists():
        raise FileNotFoundError(f"Stage 5 file not found: {args.stage5}")
    if not Path(args.stage6).exists():
        raise FileNotFoundError(f"Stage 6 file not found: {args.stage6}")

    # 創建輸出目錄
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("RL Data Generator - Proposal 003, Phase 1")
    logger.info("=" * 60)

    # 加載數據
    stage5_data = load_stage5_data(args.stage5)
    rl_data = load_stage6_data(args.stage6)

    # 提取 transitions
    logger.info("Extracting transitions...")
    states, actions, rewards, next_states, dones = extract_transitions(rl_data)
    logger.info(f"✅ Extracted {len(states)} transitions")
    logger.info(f"   State shape: {states.shape}")
    logger.info(f"   Action shape: {actions.shape}")
    logger.info(f"   Unique actions: {np.unique(actions)}")

    # 分割數據集
    logger.info("Splitting dataset...")
    train, val, test = split_dataset(states, actions, rewards, next_states, dones)

    # 保存到 HDF5
    save_to_hdf5(output_path, train, val, test)

    # 打印統計信息
    print_statistics(output_path)

    logger.info("=" * 60)
    logger.info("✅ RL Data Generator completed successfully")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
