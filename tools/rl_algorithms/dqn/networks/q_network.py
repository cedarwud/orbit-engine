"""
Q-Network Implementation

Deep neural network for approximating Q-values in DQN.

SOURCE: Mnih et al. (2015) "Human-level control through deep reinforcement learning"
        Nature 518(7540):529-533
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List


class QNetwork(nn.Module):
    """
    Q-Network for Deep Q-Learning

    Architecture:
        Input(state_dim) → FC(256) → ReLU → FC(256) → ReLU → Output(action_dim)

    SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B
            "Deep Q-Network Architecture for Satellite Handover"

    Args:
        state_dim: State dimension (default: 53 for satellite handover)
        action_dim: Action dimension (default: 6 for stay + 5 candidates)
        hidden_dims: Hidden layer dimensions (default: [256, 256])
    """

    def __init__(
        self,
        state_dim: int = 53,
        action_dim: int = 6,
        hidden_dims: List[int] = None
    ):
        super().__init__()

        if hidden_dims is None:
            # Default architecture from Badini et al. (2024)
            hidden_dims = [256, 256]

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dims = hidden_dims

        # Build network layers
        layers = []
        in_dim = state_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.ReLU())
            in_dim = hidden_dim

        # Output layer
        layers.append(nn.Linear(in_dim, action_dim))

        self.network = nn.Sequential(*layers)

        # Initialize weights
        # SOURCE: He et al. (2015) "Delving Deep into Rectifiers"
        self._initialize_weights()

    def _initialize_weights(self):
        """Initialize network weights using He initialization

        SOURCE: He et al. (2015) "Delving Deep into Rectifiers:
                Surpassing Human-Level Performance on ImageNet Classification"
        """
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_uniform_(module.weight, nonlinearity='relu')
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through Q-Network

        Args:
            state: State tensor, shape (batch_size, state_dim) or (state_dim,)

        Returns:
            q_values: Q-values for each action, shape (batch_size, action_dim) or (action_dim,)
        """
        # Handle single state (no batch dimension)
        if state.dim() == 1:
            state = state.unsqueeze(0)
            q_values = self.network(state)
            return q_values.squeeze(0)

        return self.network(state)

    def get_action(self, state: torch.Tensor, epsilon: float = 0.0) -> int:
        """
        Get action using epsilon-greedy policy

        Args:
            state: State tensor, shape (state_dim,)
            epsilon: Exploration rate (0.0 = pure greedy)

        Returns:
            action: Selected action index

        SOURCE: Mnih et al. (2015) Nature - Epsilon-greedy exploration
        """
        if torch.rand(1).item() < epsilon:
            # Random exploration
            return torch.randint(0, self.action_dim, (1,)).item()
        else:
            # Greedy exploitation
            with torch.no_grad():
                q_values = self.forward(state)
                return q_values.argmax().item()

    def get_max_q_value(self, state: torch.Tensor) -> float:
        """
        Get maximum Q-value for a state

        Args:
            state: State tensor, shape (state_dim,)

        Returns:
            max_q: Maximum Q-value
        """
        with torch.no_grad():
            q_values = self.forward(state)
            return q_values.max().item()


def test_q_network():
    """測試 Q-Network"""
    print("Testing Q-Network...")

    # 創建 Q-Network
    state_dim = 53
    action_dim = 6
    q_net = QNetwork(state_dim=state_dim, action_dim=action_dim)

    print(f"\n✅ Q-Network created:")
    print(f"   State dim: {state_dim}")
    print(f"   Action dim: {action_dim}")
    print(f"   Hidden dims: {q_net.hidden_dims}")
    print(f"   Total parameters: {sum(p.numel() for p in q_net.parameters()):,}")

    # 測試單個狀態
    single_state = torch.randn(state_dim)
    q_values = q_net(single_state)
    print(f"\n✅ Single state forward pass:")
    print(f"   Input shape: {single_state.shape}")
    print(f"   Output shape: {q_values.shape}")
    print(f"   Q-values: {q_values}")

    # 測試批量狀態
    batch_size = 32
    batch_states = torch.randn(batch_size, state_dim)
    batch_q_values = q_net(batch_states)
    print(f"\n✅ Batch forward pass:")
    print(f"   Input shape: {batch_states.shape}")
    print(f"   Output shape: {batch_q_values.shape}")

    # 測試 epsilon-greedy 動作選擇
    print(f"\n✅ Epsilon-greedy action selection:")
    for epsilon in [0.0, 0.5, 1.0]:
        actions = [q_net.get_action(single_state, epsilon=epsilon) for _ in range(10)]
        print(f"   epsilon={epsilon}: actions={actions}")

    # 測試最大 Q 值
    max_q = q_net.get_max_q_value(single_state)
    print(f"\n✅ Maximum Q-value: {max_q:.4f}")

    # 測試網絡架構
    print(f"\n✅ Network architecture:")
    print(q_net)


if __name__ == "__main__":
    test_q_network()
