# models/critic.py
import torch
import torch.nn as nn
import numpy as np


def build_mlp(input_dim, hidden_sizes=(256, 256), activation=nn.Tanh, output_size=1):
    layers = []
    prev = input_dim
    for h in hidden_sizes:
        layers.append(nn.Linear(prev, h))
        layers.append(activation())
        prev = h
    layers.append(nn.Linear(prev, output_size))
    return nn.Sequential(*layers)


class Critic(nn.Module):
    """
    Value function approximator V(s). Returns a scalar value per state.
    """

    def __init__(self, obs_dim: int, hidden_sizes=(256, 256), activation=nn.Tanh, device="cpu"):
        super().__init__()
        self.device = torch.device(device)
        self.net = build_mlp(obs_dim, hidden_sizes, activation, output_size=1)
        self.to(self.device)

    def forward(self, obs: torch.Tensor):
        """
        Args:
            obs: (batch, obs_dim) or (obs_dim,)
        Returns:
            value: (batch,) or scalar
        """
        if not isinstance(obs, torch.Tensor):
            obs = torch.tensor(obs, dtype=torch.float32, device=self.device)
        if obs.ndim == 1:
            obs = obs.unsqueeze(0)
            squeezed = True
        else:
            squeezed = False

        value = self.net(obs)
        value = value.squeeze(-1)

        if squeezed:
            return value.squeeze(0)
        return value
