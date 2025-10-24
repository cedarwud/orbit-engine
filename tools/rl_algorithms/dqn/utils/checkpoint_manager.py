"""
Checkpoint Manager

管理模型檢查點的儲存、加載和清理。

SOURCE: PyTorch Lightning - Checkpoint management patterns
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import torch
from datetime import datetime

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    訓練檢查點管理器

    功能:
    - 定期儲存模型檢查點
    - 保留最近 N 個檢查點
    - 儲存最佳模型
    - 恢復訓練

    Args:
        save_dir: 檢查點儲存目錄
        keep_last_n: 保留最近 N 個檢查點（None = 保留全部）
        save_best: 是否儲存最佳模型
    """

    def __init__(
        self,
        save_dir: str,
        keep_last_n: Optional[int] = 5,
        save_best: bool = True
    ):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.keep_last_n = keep_last_n
        self.save_best = save_best

        self.best_metric = float('-inf')
        self.checkpoints = []

        logger.info(f"CheckpointManager initialized: save_dir={self.save_dir}, "
                   f"keep_last_n={self.keep_last_n}, save_best={self.save_best}")

    def save(
        self,
        agent,
        episode: int,
        metrics: Dict[str, float],
        optimizer_state: Optional[Dict] = None
    ) -> str:
        """儲存檢查點

        Args:
            agent: DQN Agent 實例
            episode: 當前 episode 數
            metrics: 訓練指標（如 reward, loss）
            optimizer_state: Optimizer 狀態（可選）

        Returns:
            checkpoint_path: 儲存的檢查點路徑
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        reward = metrics.get('reward', 0.0)

        # 構建檢查點文件名
        filename = f"checkpoint_ep{episode}_r{reward:.2f}_{timestamp}.pt"
        checkpoint_path = self.save_dir / filename

        # 構建檢查點字典
        checkpoint = {
            'episode': episode,
            'metrics': metrics,
            'agent_state': {
                'q_network': agent.q_network.state_dict(),
                'target_network': agent.target_network.state_dict(),
                'epsilon': agent.epsilon
            },
            'timestamp': timestamp
        }

        if optimizer_state:
            checkpoint['optimizer_state'] = optimizer_state

        # 儲存檢查點
        torch.save(checkpoint, checkpoint_path)
        self.checkpoints.append(checkpoint_path)

        logger.info(f"✅ Saved checkpoint: {filename}")

        # 清理舊檢查點
        self._cleanup_old_checkpoints()

        # 儲存最佳模型
        if self.save_best and reward > self.best_metric:
            self.best_metric = reward
            self._save_best_model(checkpoint_path)

        return str(checkpoint_path)

    def _save_best_model(self, checkpoint_path: Path):
        """儲存最佳模型副本

        Args:
            checkpoint_path: 當前最佳檢查點路徑
        """
        best_model_path = self.save_dir / "best_model.pt"

        # 複製檢查點
        import shutil
        shutil.copy(checkpoint_path, best_model_path)

        logger.info(f"🏆 Saved best model: reward={self.best_metric:.2f}")

    def _cleanup_old_checkpoints(self):
        """清理舊檢查點，保留最近 N 個"""
        if self.keep_last_n is None:
            return

        if len(self.checkpoints) > self.keep_last_n:
            # 移除最舊的檢查點
            old_checkpoints = self.checkpoints[:-self.keep_last_n]

            for old_checkpoint in old_checkpoints:
                if old_checkpoint.exists():
                    # 不要刪除 best_model.pt
                    if old_checkpoint.name != "best_model.pt":
                        old_checkpoint.unlink()
                        logger.debug(f"🗑️ Removed old checkpoint: {old_checkpoint.name}")

            # 更新檢查點列表
            self.checkpoints = self.checkpoints[-self.keep_last_n:]

    def load_latest(self, agent, optimizer=None) -> Optional[Dict[str, Any]]:
        """加載最新檢查點

        Args:
            agent: DQN Agent 實例
            optimizer: Optimizer 實例（可選）

        Returns:
            checkpoint: 檢查點字典，如果沒有檢查點則返回 None
        """
        checkpoints = sorted(self.save_dir.glob("checkpoint_*.pt"))

        if not checkpoints:
            logger.warning("⚠️ No checkpoints found")
            return None

        latest_checkpoint = checkpoints[-1]
        return self.load(str(latest_checkpoint), agent, optimizer)

    def load_best(self, agent, optimizer=None) -> Optional[Dict[str, Any]]:
        """加載最佳模型

        Args:
            agent: DQN Agent 實例
            optimizer: Optimizer 實例（可選）

        Returns:
            checkpoint: 檢查點字典，如果沒有最佳模型則返回 None
        """
        best_model_path = self.save_dir / "best_model.pt"

        if not best_model_path.exists():
            logger.warning("⚠️ Best model not found")
            return None

        return self.load(str(best_model_path), agent, optimizer)

    def load(
        self,
        checkpoint_path: str,
        agent,
        optimizer=None
    ) -> Dict[str, Any]:
        """加載檢查點

        Args:
            checkpoint_path: 檢查點路徑
            agent: DQN Agent 實例
            optimizer: Optimizer 實例（可選）

        Returns:
            checkpoint: 檢查點字典

        Raises:
            FileNotFoundError: 檢查點文件不存在
        """
        checkpoint_file = Path(checkpoint_path)

        if not checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        logger.info(f"Loading checkpoint: {checkpoint_file.name}")

        checkpoint = torch.load(checkpoint_file, weights_only=False)

        # 恢復 agent 狀態
        agent.q_network.load_state_dict(checkpoint['agent_state']['q_network'])
        agent.target_network.load_state_dict(checkpoint['agent_state']['target_network'])
        agent.epsilon = checkpoint['agent_state']['epsilon']

        # 恢復 optimizer 狀態
        if optimizer and 'optimizer_state' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state'])

        logger.info(f"✅ Loaded checkpoint from episode {checkpoint['episode']}")

        return checkpoint

    def get_latest_episode(self) -> int:
        """獲取最新檢查點的 episode 數

        Returns:
            episode: Episode 數，如果沒有檢查點則返回 0
        """
        checkpoints = sorted(self.save_dir.glob("checkpoint_*.pt"))

        if not checkpoints:
            return 0

        latest_checkpoint = checkpoints[-1]
        checkpoint = torch.load(latest_checkpoint, weights_only=False)
        return checkpoint['episode']


def test_checkpoint_manager():
    """測試 Checkpoint Manager"""
    import tempfile
    import shutil
    from ..agents.dqn_agent import DQNAgent

    print("Testing Checkpoint Manager...\n")

    # 創建臨時目錄
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")

    try:
        # 創建 Checkpoint Manager
        manager = CheckpointManager(
            save_dir=temp_dir,
            keep_last_n=3,
            save_best=True
        )

        # 創建測試 agent
        agent = DQNAgent(state_dim=53, action_dim=6)

        # 測試儲存多個檢查點
        print("\n1️⃣ Testing save checkpoints...")
        for episode in [10, 20, 30, 40, 50]:
            reward = episode * 0.1  # 模擬遞增的 reward
            metrics = {'reward': reward, 'loss': 0.1}
            manager.save(agent, episode, metrics)

        print(f"   Checkpoints saved: {len(manager.checkpoints)}")
        print(f"   Best metric: {manager.best_metric:.2f}")

        # 測試加載最新檢查點
        print("\n2️⃣ Testing load latest checkpoint...")
        checkpoint = manager.load_latest(agent)
        if checkpoint:
            print(f"   ✅ Loaded episode: {checkpoint['episode']}")
            print(f"   Metrics: {checkpoint['metrics']}")

        # 測試加載最佳模型
        print("\n3️⃣ Testing load best model...")
        best_checkpoint = manager.load_best(agent)
        if best_checkpoint:
            print(f"   ✅ Best episode: {best_checkpoint['episode']}")
            print(f"   Best metrics: {best_checkpoint['metrics']}")

        # 測試獲取最新 episode
        print("\n4️⃣ Testing get latest episode...")
        latest_episode = manager.get_latest_episode()
        print(f"   ✅ Latest episode: {latest_episode}")

        print("\n✅ All tests passed!")

    finally:
        # 清理臨時目錄
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

    test_checkpoint_manager()
