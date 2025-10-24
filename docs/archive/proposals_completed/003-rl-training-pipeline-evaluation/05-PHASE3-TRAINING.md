# Proposal 003: Phase 3 - Training Pipeline

**文檔版本**: v2.0
**最後更新**: 2025-10-23
**預計時間**: 2 天

---

## 📋 概述

Phase 3 實現完整的 DQN 訓練管道，包括超參數配置、日誌記錄、模型儲存和訓練監控。

**關鍵設計**:
- ✅ **端到端訓練** - 自動化訓練流程
- ✅ **TensorBoard 整合** - 視覺化訓練過程
- ✅ **檢查點管理** - 定期儲存模型
- ✅ **配置化設計** - YAML 超參數配置

---

## 🎯 目標

1. 建立訓練配置系統（超參數、訓練策略）
2. 整合 TensorBoard 日誌記錄
3. 實現模型檢查點儲存/加載
4. 建立訓練監控和早停機制
5. 支持訓練恢復（從檢查點繼續）

---

## 📦 模組設計

詳見 [02-ARCHITECTURE.md](02-ARCHITECTURE.md) Module 3

### 核心組件

1. **Training Manager** - 訓練流程管理
2. **Config Manager** - 超參數配置
3. **Checkpoint Manager** - 模型儲存/加載
4. **Logger** - TensorBoard 日誌記錄

---

## 🔧 訓練配置

### YAML 配置文件

```yaml
# config/training/dqn_training_config.yaml

training:
  episodes: 500                # 訓練回合數
  max_steps_per_episode: 200   # 每回合最大步數
  batch_size: 64               # 批次大小
  learning_rate: 0.0001        # 學習率
  gamma: 0.99                  # 折扣因子
  epsilon_start: 1.0           # 初始探索率
  epsilon_end: 0.01            # 最終探索率
  epsilon_decay: 0.995         # 探索率衰減
  target_update_freq: 10       # Target Network 更新頻率
  replay_buffer_size: 100000   # Experience Replay 容量

checkpointing:
  save_freq: 50                # 每 N 回合儲存一次
  save_dir: "data/models/dqn"  # 模型儲存目錄
  keep_last_n: 5               # 保留最近 N 個檢查點

logging:
  tensorboard_dir: "logs/tensorboard"
  log_freq: 10                 # 每 N 回合記錄一次

early_stopping:
  enabled: true
  patience: 50                 # 無改善容忍回合數
  min_delta: 0.1               # 最小改善閾值
```

**SOURCE**:
- Mnih et al. (2015) Nature - DQN 超參數
- OpenAI Baselines documentation - 標準訓練配置

---

## 🏃 Training Manager

### 訓練管道實現

```python
import yaml
from pathlib import Path
import torch
from torch.utils.tensorboard import SummaryWriter

class DQNTrainingManager:
    """DQN 訓練管道管理器

    SOURCE: Mnih et al. (2015) Nature, Algorithm 1: Deep Q-learning
            with experience replay
    """

    def __init__(self, config_path: str):
        """初始化訓練管理器

        Args:
            config_path: YAML 配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.writer = SummaryWriter(self.config['logging']['tensorboard_dir'])
        self.checkpoint_manager = CheckpointManager(
            self.config['checkpointing']['save_dir']
        )
        self.best_reward = float('-inf')
        self.patience_counter = 0

    def train(self, env, agent):
        """執行訓練

        Args:
            env: Gymnasium 環境
            agent: DQN Agent

        Returns:
            training_history (dict): 訓練歷史記錄
        """
        training_history = {
            'episode_rewards': [],
            'episode_lengths': [],
            'losses': [],
            'epsilon_values': []
        }

        for episode in range(self.config['training']['episodes']):
            episode_reward, episode_length = self._run_episode(env, agent)

            # 記錄訓練指標
            training_history['episode_rewards'].append(episode_reward)
            training_history['episode_lengths'].append(episode_length)
            training_history['epsilon_values'].append(agent.epsilon)

            # TensorBoard 日誌
            if episode % self.config['logging']['log_freq'] == 0:
                self._log_metrics(episode, episode_reward, agent)

            # 儲存檢查點
            if episode % self.config['checkpointing']['save_freq'] == 0:
                self._save_checkpoint(episode, agent, episode_reward)

            # 早停檢查
            if self._check_early_stopping(episode_reward):
                print(f"Early stopping at episode {episode}")
                break

            # 更新探索率
            agent.decay_epsilon()

        self.writer.close()
        return training_history

    def _run_episode(self, env, agent):
        """執行單個訓練回合

        Returns:
            episode_reward (float): 回合總獎勵
            episode_length (int): 回合步數
        """
        state, info = env.reset()
        episode_reward = 0
        episode_length = 0
        max_steps = self.config['training']['max_steps_per_episode']

        while episode_length < max_steps:
            # 選擇動作
            action = agent.select_action(state)

            # 執行動作
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            # 存入 Replay Buffer
            agent.memory.push(state, action, reward, next_state, done)

            # 訓練 Q-Network
            if len(agent.memory) > self.config['training']['batch_size']:
                loss = agent.train_step()
                if loss is not None:
                    self.writer.add_scalar('Loss/train', loss, episode_length)

            state = next_state
            episode_reward += reward
            episode_length += 1

            if done:
                break

        return episode_reward, episode_length

    def _log_metrics(self, episode, reward, agent):
        """記錄訓練指標到 TensorBoard"""
        self.writer.add_scalar('Reward/episode', reward, episode)
        self.writer.add_scalar('Epsilon/value', agent.epsilon, episode)
        self.writer.add_scalar('Memory/size', len(agent.memory), episode)

    def _save_checkpoint(self, episode, agent, reward):
        """儲存訓練檢查點"""
        checkpoint = {
            'episode': episode,
            'model_state_dict': agent.q_network.state_dict(),
            'target_state_dict': agent.target_network.state_dict(),
            'optimizer_state_dict': agent.optimizer.state_dict(),
            'epsilon': agent.epsilon,
            'reward': reward
        }
        self.checkpoint_manager.save(checkpoint, episode, reward)

    def _check_early_stopping(self, current_reward):
        """檢查是否應該早停

        SOURCE: Prechelt (1998) "Early Stopping - But When?",
                Neural Networks: Tricks of the Trade
        """
        if not self.config['early_stopping']['enabled']:
            return False

        min_delta = self.config['early_stopping']['min_delta']
        patience = self.config['early_stopping']['patience']

        if current_reward > self.best_reward + min_delta:
            self.best_reward = current_reward
            self.patience_counter = 0
        else:
            self.patience_counter += 1

        return self.patience_counter >= patience
```

---

## 💾 Checkpoint Manager

### 模型儲存和加載

```python
class CheckpointManager:
    """訓練檢查點管理器"""

    def __init__(self, save_dir: str):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: dict, episode: int, reward: float):
        """儲存檢查點

        Args:
            checkpoint: 包含模型狀態的字典
            episode: 當前回合數
            reward: 當前獎勵
        """
        filename = f"checkpoint_ep{episode}_r{reward:.2f}.pth"
        filepath = self.save_dir / filename
        torch.save(checkpoint, filepath)
        print(f"✅ Checkpoint saved: {filename}")

        # 清理舊檢查點（保留最近 N 個）
        self._cleanup_old_checkpoints()

    def load_latest(self, agent):
        """加載最新檢查點

        Args:
            agent: DQN Agent 實例

        Returns:
            start_episode (int): 恢復的回合數
        """
        checkpoints = sorted(self.save_dir.glob("checkpoint_*.pth"))
        if not checkpoints:
            print("⚠️ No checkpoint found, starting from scratch")
            return 0

        latest_checkpoint = checkpoints[-1]
        checkpoint = torch.load(latest_checkpoint)

        agent.q_network.load_state_dict(checkpoint['model_state_dict'])
        agent.target_network.load_state_dict(checkpoint['target_state_dict'])
        agent.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        agent.epsilon = checkpoint['epsilon']

        print(f"✅ Checkpoint loaded: {latest_checkpoint.name}")
        return checkpoint['episode']

    def _cleanup_old_checkpoints(self):
        """清理舊檢查點，保留最近 N 個"""
        checkpoints = sorted(self.save_dir.glob("checkpoint_*.pth"))
        keep_last_n = 5  # 從配置讀取

        if len(checkpoints) > keep_last_n:
            for old_checkpoint in checkpoints[:-keep_last_n]:
                old_checkpoint.unlink()
                print(f"🗑️ Removed old checkpoint: {old_checkpoint.name}")
```

---

## 📊 訓練監控

### TensorBoard 視覺化

```bash
# 啟動 TensorBoard
tensorboard --logdir logs/tensorboard

# 監控訓練指標:
# - Reward/episode: 回合總獎勵
# - Loss/train: 訓練損失
# - Epsilon/value: 探索率衰減
# - Memory/size: Replay Buffer 大小
```

### 訓練曲線範例

```
Episode 0-100:   Reward = -50 ~ 0   (隨機探索)
Episode 100-200: Reward = 0 ~ 50    (開始學習)
Episode 200-300: Reward = 50 ~ 100  (性能提升)
Episode 300-500: Reward = 100 ~ 150 (收斂)
```

---

## ⏱️ 實施計畫

詳見 [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) Phase 3

### Day 6: 訓練配置系統
- YAML 配置文件設計
- Config Manager 實現
- 超參數加載和驗證

### Day 7: 訓練管道整合
- Training Manager 實現
- Checkpoint Manager 實現
- TensorBoard 日誌整合
- 早停機制
- 單元測試

---

## ✅ 驗收標準

- [ ] YAML 配置文件正確加載
- [ ] 訓練管道可以完整執行 500 回合
- [ ] TensorBoard 正確記錄所有指標
- [ ] 檢查點儲存/加載正常運作
- [ ] 早停機制正確觸發
- [ ] 訓練可以從檢查點恢復
- [ ] 探索率 ε 正確衰減（1.0 → 0.01）
- [ ] 單元測試覆蓋率 > 80%
- [ ] 所有函數有 SOURCE 標註

---

## 🔬 測試策略

### 單元測試

```python
def test_training_manager_initialization():
    """測試訓練管理器初始化"""
    config_path = "config/training/dqn_training_config.yaml"
    manager = DQNTrainingManager(config_path)
    assert manager.config['training']['episodes'] == 500

def test_checkpoint_save_load():
    """測試檢查點儲存和加載"""
    checkpoint_manager = CheckpointManager("data/models/test")
    agent = create_test_agent()

    # 儲存檢查點
    checkpoint = {
        'episode': 100,
        'model_state_dict': agent.q_network.state_dict(),
        'epsilon': 0.5
    }
    checkpoint_manager.save(checkpoint, 100, 50.0)

    # 加載檢查點
    episode = checkpoint_manager.load_latest(agent)
    assert episode == 100
    assert abs(agent.epsilon - 0.5) < 1e-6

def test_early_stopping():
    """測試早停機制"""
    manager = create_test_manager()
    manager.best_reward = 100.0

    # 無改善 50 回合應該觸發早停
    for _ in range(50):
        should_stop = manager._check_early_stopping(95.0)
    assert should_stop == True

def test_epsilon_decay():
    """測試探索率衰減"""
    agent = create_test_agent()
    agent.epsilon = 1.0
    agent.epsilon_decay = 0.995

    for _ in range(100):
        agent.decay_epsilon()

    # 100 回合後 ε 應該約為 0.606
    assert 0.6 < agent.epsilon < 0.62
```

---

## 📚 參考文獻

1. **Mnih et al. (2015)** - "Human-level control through deep reinforcement learning", Nature
   - DQN 訓練超參數
   - Experience Replay 配置

2. **Prechelt (1998)** - "Early Stopping - But When?", Neural Networks: Tricks of the Trade
   - 早停策略

3. **OpenAI Baselines** - https://github.com/openai/baselines
   - 標準 RL 訓練配置
   - 日誌記錄最佳實踐

4. **PyTorch Lightning** - https://pytorch-lightning.readthedocs.io/
   - Checkpoint 管理模式
   - 訓練管道架構

---

**文檔狀態**: ✅ 完成
**下一階段**: [06-PHASE4-EVALUATION.md](06-PHASE4-EVALUATION.md)
