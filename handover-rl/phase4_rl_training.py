#!/usr/bin/env python3
"""
Phase 4: RL 智能體訓練

功能：
1. 實作 DQN 智能體
2. 訓練 DQN 模型
3. 保存訓練好的模型
4. 記錄訓練曲線

執行：
    python phase4_rl_training.py

輸出：
    results/models/dqn_final.pth          - 最終模型
    results/models/dqn_best.pth           - 最佳模型
    results/training_log.json             - 訓練日誌
    results/plots/training_curve.png      - 訓練曲線
"""

import json
import yaml
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
from pathlib import Path
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt

from phase3_rl_environment import HandoverEnvironment


class DQNNetwork(nn.Module):
    """
    DQN 神經網路

    架構:
        Input (state_dim=12) → FC(128) → ReLU → FC(128) → ReLU → Output (action_dim=2)

    SOURCE: Mnih et al. (2015) Human-level control through deep reinforcement learning
    NOTE: 12-dim state = [RSRP, RSRQ, SINR, distance, elevation, doppler, velocity,
                           atmospheric_loss, path_loss, propagation_delay, offset_mo, cell_offset]
          2 actions = [maintain, handover]
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DQNNetwork, self).__init__()

        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

        self.relu = nn.ReLU()

    def forward(self, x):
        """前向傳播"""
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class ReplayBuffer:
    """
    經驗回放緩衝區

    儲存 (state, action, reward, next_state, done) 轉移
    """

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """添加經驗"""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        """隨機採樣批次"""
        batch = random.sample(self.buffer, batch_size)

        states, actions, rewards, next_states, dones = zip(*batch)

        return (
            torch.FloatTensor(np.array(states)),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(np.array(next_states)),
            torch.FloatTensor(dones)
        )

    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    """DQN 智能體"""

    def __init__(self, state_dim: int, action_dim: int, config: Dict):
        """
        Args:
            state_dim: 狀態維度
            action_dim: 動作維度
            config: DQN 配置
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config

        # Q 網路
        hidden_dim = config['hidden_dim']
        self.q_network = DQNNetwork(state_dim, action_dim, hidden_dim)
        self.target_network = DQNNetwork(state_dim, action_dim, hidden_dim)
        self.target_network.load_state_dict(self.q_network.state_dict())

        # 優化器
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=config['learning_rate'])
        self.loss_fn = nn.MSELoss()

        # 經驗回放
        self.replay_buffer = ReplayBuffer(capacity=config['memory_size'])

        # 超參數 (SOURCE: Mnih et al. 2015 DQN paper)
        self.gamma = config['gamma']                    # SOURCE: Discount factor (typical 0.99)
        self.epsilon = config['epsilon_start']          # SOURCE: Epsilon-greedy exploration (typical 1.0)
        self.epsilon_end = config['epsilon_end']        # SOURCE: Minimum epsilon (typical 0.01)
        self.epsilon_decay = config['epsilon_decay']    # SOURCE: Decay rate per episode
        self.batch_size = config['batch_size']          # SOURCE: Mini-batch size (typical 32-64)
        self.target_update = config['target_update']    # SOURCE: Target network update frequency

        # 訓練計數
        self.update_count = 0

    def select_action(self, state: np.ndarray, eval_mode: bool = False) -> int:
        """
        選擇動作（ε-greedy 策略）

        Args:
            state: 當前狀態
            eval_mode: 評估模式（不探索）

        Returns:
            action: 選擇的動作
        """
        if not eval_mode and random.random() < self.epsilon:
            # 探索：隨機動作
            return random.randint(0, self.action_dim - 1)
        else:
            # 利用：最佳動作
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.q_network(state_tensor)
                action = q_values.argmax(dim=1).item()
            return action

    def update(self):
        """更新 Q 網路"""
        if len(self.replay_buffer) < self.batch_size:
            return None

        # 採樣批次
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        # 計算當前 Q 值
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # 計算目標 Q 值
        with torch.no_grad():
            next_q = self.target_network(next_states).max(dim=1)[0]
            target_q = rewards + self.gamma * next_q * (1 - dones)

        # 計算損失
        loss = self.loss_fn(current_q, target_q)

        # 反向傳播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 更新目標網路
        self.update_count += 1
        if self.update_count % self.target_update == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # 衰減 epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return loss.item()

    def save(self, path: str):
        """保存模型"""
        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)

    def load(self, path: str):
        """載入模型"""
        checkpoint = torch.load(path)
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']


class Trainer:
    """訓練器"""

    def __init__(self, config: Dict):
        import pickle

        self.config = config

        # 載入數據（Episode 格式 from phase1_data_loader_v2.py）
        print("📥 載入 Episode 數據...")
        data_path = Path("data")

        with open(data_path / "train_episodes.pkl", 'rb') as f:
            self.train_episodes = pickle.load(f)
        with open(data_path / "val_episodes.pkl", 'rb') as f:
            self.val_episodes = pickle.load(f)

        print(f"   訓練集: {len(self.train_episodes)} Episodes")
        print(f"   驗證集: {len(self.val_episodes)} Episodes")

        # 創建環境
        self.train_env = HandoverEnvironment(self.train_episodes, config, mode='train')
        self.val_env = HandoverEnvironment(self.val_episodes, config, mode='eval')

        # 創建智能體
        state_dim = config['environment']['state_dim']
        action_dim = config['environment']['action_dim']
        self.agent = DQNAgent(state_dim, action_dim, config['dqn'])

        # 訓練配置
        self.episodes = config['training']['episodes']
        self.save_interval = config['training']['save_interval']
        self.log_interval = config['training']['log_interval']
        self.eval_interval = config['training']['eval_interval']

        # 記錄
        self.training_log = []
        self.best_reward = -float('inf')

    def train(self):
        """訓練循環"""
        print(f"\n🚀 開始訓練 DQN (共 {self.episodes} episodes)...")

        for episode in range(1, self.episodes + 1):
            # 訓練一個 episode
            episode_reward, episode_loss = self._train_episode()

            # 記錄
            log_entry = {
                'episode': episode,
                'reward': episode_reward,
                'loss': episode_loss,
                'epsilon': self.agent.epsilon
            }

            # 評估
            if episode % self.eval_interval == 0:
                val_reward = self._evaluate()
                log_entry['val_reward'] = val_reward

                # 保存最佳模型
                if val_reward > self.best_reward:
                    self.best_reward = val_reward
                    self.agent.save("results/models/dqn_best.pth")

            self.training_log.append(log_entry)

            # 日誌
            if episode % self.log_interval == 0:
                print(f"Episode {episode}/{self.episodes}: "
                      f"Reward={episode_reward:.2f}, "
                      f"Loss={episode_loss:.4f}, "
                      f"ε={self.agent.epsilon:.3f}")

            # 保存檢查點
            if episode % self.save_interval == 0:
                self.agent.save(f"results/checkpoints/dqn_episode_{episode}.pth")

        # 保存最終模型
        self.agent.save("results/models/dqn_final.pth")
        print(f"\n✅ 訓練完成！最佳驗證獎勵: {self.best_reward:.2f}")

    def _train_episode(self) -> Tuple[float, float]:
        """訓練一個 episode"""
        state, _ = self.train_env.reset()
        episode_reward = 0
        episode_losses = []

        while True:
            # 選擇動作
            action = self.agent.select_action(state)

            # 執行動作
            next_state, reward, terminated, truncated, info = self.train_env.step(action)

            # 儲存經驗
            done = float(terminated or truncated)
            self.agent.replay_buffer.push(state, action, reward, next_state, done)

            # 更新網路
            loss = self.agent.update()
            if loss is not None:
                episode_losses.append(loss)

            # 累積獎勵
            episode_reward += reward

            # 更新狀態
            state = next_state

            if terminated or truncated:
                break

        avg_loss = np.mean(episode_losses) if episode_losses else 0
        return episode_reward, avg_loss

    def _evaluate(self) -> float:
        """評估當前策略"""
        state, _ = self.val_env.reset()
        total_reward = 0

        while True:
            action = self.agent.select_action(state, eval_mode=True)
            next_state, reward, terminated, truncated, info = self.val_env.step(action)

            total_reward += reward
            state = next_state

            if terminated or truncated:
                break

        return total_reward

    def save_training_log(self):
        """保存訓練日誌"""
        log_file = Path("results/training_log.json")
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'w') as f:
            json.dump(self.training_log, f, indent=2)

        print(f"💾 訓練日誌已保存: {log_file}")

    def plot_training_curve(self):
        """繪製訓練曲線"""
        episodes = [entry['episode'] for entry in self.training_log]
        rewards = [entry['reward'] for entry in self.training_log]
        losses = [entry['loss'] for entry in self.training_log]

        # 提取驗證獎勵
        val_episodes = [entry['episode'] for entry in self.training_log if 'val_reward' in entry]
        val_rewards = [entry['val_reward'] for entry in self.training_log if 'val_reward' in entry]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # 獎勵曲線
        ax1.plot(episodes, rewards, label='Training Reward', alpha=0.6)
        if val_episodes:
            ax1.plot(val_episodes, val_rewards, 'o-', label='Validation Reward', linewidth=2)
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Reward')
        ax1.set_title('DQN Training Curve - Reward')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 損失曲線
        ax2.plot(episodes, losses, label='Loss', color='orange', alpha=0.6)
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Loss')
        ax2.set_title('DQN Training Curve - Loss')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        plot_file = Path("results/plots/training_curve.png")
        plot_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_file, dpi=150)
        print(f"📊 訓練曲線已保存: {plot_file}")

        plt.close()


def main():
    """主函數"""
    print("=" * 70)
    print("Phase 4: DQN 訓練")
    print("=" * 70)

    # 載入配置
    with open("config/rl_config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    # 創建必要目錄
    Path("results/models").mkdir(parents=True, exist_ok=True)
    Path("results/checkpoints").mkdir(parents=True, exist_ok=True)
    Path("results/plots").mkdir(parents=True, exist_ok=True)

    # 創建訓練器
    trainer = Trainer(config)

    # 開始訓練
    trainer.train()

    # 保存日誌
    trainer.save_training_log()

    # 繪製曲線
    trainer.plot_training_curve()

    print("\n" + "=" * 70)
    print("✅ Phase 4 完成！")
    print("=" * 70)
    print("\n下一步: 運行 Phase 5 (評估與比較)")
    print("  python phase5_evaluation.py")


if __name__ == "__main__":
    main()
