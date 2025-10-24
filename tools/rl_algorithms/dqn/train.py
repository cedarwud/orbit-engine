#!/usr/bin/env python3
"""
DQN Training Script

完整的 DQN 訓練管道，包括訓練循環、驗證、檢查點管理和 TensorBoard 日誌。

SOURCE: Proposal 003, Phase 3 - Training Pipeline
"""

import sys
from pathlib import Path
import logging
import yaml
import torch
import numpy as np
from datetime import datetime
from tqdm import tqdm

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.rl_algorithms.dqn.envs import SatelliteHandoverEnv
from tools.rl_algorithms.dqn.agents import DQNAgent
from tools.rl_algorithms.dqn.utils.checkpoint_manager import CheckpointManager

try:
    from torch.utils.tensorboard import SummaryWriter
    TENSORBOARD_AVAILABLE = True
except ImportError:
    TENSORBOARD_AVAILABLE = False

logger = logging.getLogger(__name__)


class DQNTrainer:
    """DQN 訓練管理器

    SOURCE: Mnih et al. (2015) Nature, Algorithm 1
    """

    def __init__(self, config_path: str):
        """初始化訓練器"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_device()
        self._setup_seeds()

        # 創建環境
        self.train_env = SatelliteHandoverEnv(
            self.config['data']['dataset_path'],
            split=self.config['data']['train_split']
        )
        self.val_env = SatelliteHandoverEnv(
            self.config['data']['dataset_path'],
            split=self.config['data']['val_split']
        )

        # 創建 Agent
        self.agent = DQNAgent(
            state_dim=self.config['environment']['state_dim'],
            action_dim=self.config['environment']['action_dim'],
            hidden_dims=self.config['network']['hidden_dims'],
            learning_rate=self.config['training']['learning_rate'],
            gamma=self.config['training']['gamma'],
            epsilon_start=self.config['training']['epsilon_start'],
            epsilon_end=self.config['training']['epsilon_end'],
            epsilon_decay=self.config['training']['epsilon_decay'],
            buffer_capacity=self.config['training']['replay_buffer_capacity'],
            batch_size=self.config['training']['batch_size'],
            target_update_freq=self.config['training']['target_update_freq'],
            device=str(self.device)
        )

        # Checkpoint Manager
        if self.config['checkpointing']['enabled']:
            self.checkpoint_manager = CheckpointManager(
                save_dir=self.config['checkpointing']['save_dir'],
                keep_last_n=self.config['checkpointing']['keep_last_n'],
                save_best=self.config['checkpointing']['save_best']
            )

        # TensorBoard
        if self.config['logging']['tensorboard_enabled'] and TENSORBOARD_AVAILABLE:
            log_dir = Path(self.config['logging']['tensorboard_dir'])
            log_dir.mkdir(parents=True, exist_ok=True)
            self.writer = SummaryWriter(log_dir)
        else:
            self.writer = None

        # 訓練狀態
        self.best_val_reward = float('-inf')
        self.patience_counter = 0

    def _load_config(self, config_path: str) -> dict:
        """加載配置"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """設置日誌"""
        level = getattr(logging, self.config['logging']['console_log_level'])
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    def _setup_device(self):
        """設置計算設備"""
        if self.config['device']['use_cuda'] and torch.cuda.is_available():
            self.device = torch.device(f"cuda:{self.config['device']['cuda_device']}")
        else:
            self.device = torch.device('cpu')
        logger.info(f"Using device: {self.device}")

    def _setup_seeds(self):
        """設置隨機種子"""
        seeds = self.config['seeds']
        torch.manual_seed(seeds['torch_seed'])
        np.random.seed(seeds['numpy_seed'])

    def train(self):
        """訓練主循環"""
        num_episodes = self.config['training']['episodes']
        log_freq = self.config['logging']['log_freq']

        logger.info(f"Starting training for {num_episodes} episodes...")

        for episode in tqdm(range(num_episodes), desc="Training"):
            episode_reward, episode_loss = self._train_episode()

            # 記錄
            if episode % log_freq == 0:
                self._log_metrics(episode, episode_reward, episode_loss)

            # 驗證
            if self.config['validation']['enabled'] and episode % self.config['validation']['val_freq'] == 0:
                val_reward = self._validate()
                self._check_early_stopping(val_reward)

            # 儲存檢查點
            if self.config['checkpointing']['enabled'] and episode % self.config['checkpointing']['save_freq'] == 0:
                self.checkpoint_manager.save(
                    self.agent, episode,
                    {'reward': episode_reward, 'loss': episode_loss}
                )

            # 衰減 epsilon
            self.agent.decay_epsilon()

        logger.info("Training completed!")

    def _train_episode(self):
        """訓練一個 episode"""
        obs, info = self.train_env.reset()
        episode_reward = 0
        episode_losses = []

        while True:
            action = self.agent.select_action(obs, training=True)
            next_obs, reward, terminated, truncated, info = self.train_env.step(action)

            self.agent.memory.push(obs, action, reward, next_obs, terminated or truncated)

            if self.agent.memory.is_ready(self.agent.batch_size):
                loss = self.agent.train_step()
                if loss is not None:
                    episode_losses.append(loss)

            episode_reward += reward
            obs = next_obs

            if terminated or truncated:
                break

        avg_loss = np.mean(episode_losses) if episode_losses else 0.0
        return episode_reward, avg_loss

    def _validate(self):
        """驗證"""
        val_episodes = self.config['validation']['val_episodes']
        val_rewards = []

        for _ in range(val_episodes):
            obs, info = self.val_env.reset()
            episode_reward = 0

            while True:
                action = self.agent.select_action(obs, training=False)
                obs, reward, terminated, truncated, info = self.val_env.step(action)
                episode_reward += reward

                if terminated or truncated:
                    break

            val_rewards.append(episode_reward)

        return np.mean(val_rewards)

    def _log_metrics(self, episode, reward, loss):
        """記錄指標"""
        logger.info(f"Episode {episode}: Reward={reward:.3f}, Loss={loss:.4f}, Epsilon={self.agent.epsilon:.4f}")

        if self.writer:
            self.writer.add_scalar('Train/Reward', reward, episode)
            self.writer.add_scalar('Train/Loss', loss, episode)
            self.writer.add_scalar('Train/Epsilon', self.agent.epsilon, episode)

    def _check_early_stopping(self, val_reward):
        """檢查早停"""
        if not self.config['early_stopping']['enabled']:
            return

        min_delta = self.config['early_stopping']['min_delta']
        patience = self.config['early_stopping']['patience']

        if val_reward > self.best_val_reward + min_delta:
            self.best_val_reward = val_reward
            self.patience_counter = 0
        else:
            self.patience_counter += 1

        if self.patience_counter >= patience:
            logger.info(f"Early stopping triggered at patience {self.patience_counter}")
            raise StopIteration


def main():
    """主函數"""
    config_path = "tools/rl_algorithms/dqn/config/training_config.yaml"

    trainer = DQNTrainer(config_path)
    trainer.train()


if __name__ == "__main__":
    main()
