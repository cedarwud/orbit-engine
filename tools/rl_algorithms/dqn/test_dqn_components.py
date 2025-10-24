#!/usr/bin/env python3
"""
測試 DQN 所有組件

驗證 Gymnasium 環境、Q-Network、Replay Buffer 和 DQN Agent 是否正常工作
"""

import sys
from pathlib import Path
import torch
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.rl_algorithms.dqn.envs import SatelliteHandoverEnv
from tools.rl_algorithms.dqn.networks import QNetwork
from tools.rl_algorithms.dqn.utils import ReplayBuffer
from tools.rl_algorithms.dqn.agents import DQNAgent


def test_all_components():
    """測試所有 DQN 組件"""
    print("=" * 70)
    print("Testing DQN Components")
    print("=" * 70)

    dataset_path = "data/ml_training/rl_training_dataset_20251023_120619.h5"

    # 1. 測試 Gymnasium 環境
    print("\n1️⃣ Testing Gymnasium Environment...")
    try:
        env = SatelliteHandoverEnv(dataset_path, split='train')
        obs, info = env.reset(seed=42)
        print(f"   ✅ Environment created")
        print(f"      Observation space: {env.observation_space}")
        print(f"      Action space: {env.action_space}")
        print(f"      Initial obs shape: {obs.shape}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # 2. 測試 Q-Network
    print("\n2️⃣ Testing Q-Network...")
    try:
        q_net = QNetwork(state_dim=53, action_dim=6)
        state_tensor = torch.FloatTensor(obs)
        q_values = q_net(state_tensor)
        print(f"   ✅ Q-Network created")
        print(f"      Parameters: {sum(p.numel() for p in q_net.parameters()):,}")
        print(f"      Q-values shape: {q_values.shape}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # 3. 測試 Replay Buffer
    print("\n3️⃣ Testing Replay Buffer...")
    try:
        buffer = ReplayBuffer(capacity=1000)
        for i in range(64):
            buffer.push(obs, 0, 0.5, obs, False)
        states, actions, rewards, next_states, dones = buffer.sample(32)
        print(f"   ✅ Replay Buffer created")
        print(f"      Buffer size: {len(buffer)}")
        print(f"      Sample batch shapes: states={states.shape}, actions={actions.shape}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # 4. 測試 DQN Agent
    print("\n4️⃣ Testing DQN Agent...")
    try:
        agent = DQNAgent(state_dim=53, action_dim=6, batch_size=32)
        action = agent.select_action(obs, training=True)
        print(f"   ✅ DQN Agent created")
        print(f"      Epsilon: {agent.epsilon}")
        print(f"      Selected action: {action}")

        # 測試訓練步驟（需要足夠的樣本）
        for i in range(100):
            agent.memory.push(obs, 0, 0.5, obs, False)

        loss = agent.train_step()
        print(f"      Training loss: {loss:.4f}" if loss else "      (Not enough samples yet)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # 5. 測試完整訓練循環（簡短版本）
    print("\n5️⃣ Testing Training Loop...")
    try:
        env = SatelliteHandoverEnv(dataset_path, split='train')
        agent = DQNAgent(state_dim=53, action_dim=6, batch_size=16)

        obs, info = env.reset()
        total_reward = 0
        steps = 0

        for _ in range(10):  # 只運行 10 步
            action = agent.select_action(obs, training=True)
            next_obs, reward, terminated, truncated, info = env.step(action)

            agent.memory.push(obs, action, reward, next_obs, terminated or truncated)

            if agent.memory.is_ready(agent.batch_size):
                loss = agent.train_step()

            total_reward += reward
            steps += 1
            obs = next_obs

            if terminated or truncated:
                obs, info = env.reset()
                break

        print(f"   ✅ Training loop successful")
        print(f"      Steps: {steps}")
        print(f"      Total reward: {total_reward:.3f}")
        print(f"      Buffer size: {len(agent.memory)}")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    print("\n" + "=" * 70)
    print("✅ All DQN components tested successfully!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_all_components()
    sys.exit(0 if success else 1)
