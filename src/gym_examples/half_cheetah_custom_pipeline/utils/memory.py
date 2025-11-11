# utils/memory.py
import torch
import numpy as np


class RolloutBuffer:
    """
    Stores trajectories collected by the agent for PPO.
    Computes advantages and returns after rollout is complete.
    """

    def __init__(self, buffer_size, state_dim, action_dim, gamma=0.99, gae_lambda=0.95, device="cpu"):
        self.buffer_size = buffer_size
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.device = device

        # Allocate storage
        self.states = np.zeros((buffer_size, state_dim), dtype=np.float32)
        self.actions = np.zeros((buffer_size, action_dim), dtype=np.float32)
        self.rewards = np.zeros(buffer_size, dtype=np.float32)
        self.dones = np.zeros(buffer_size, dtype=np.float32)
        self.log_probs = np.zeros(buffer_size, dtype=np.float32)
        self.values = np.zeros(buffer_size, dtype=np.float32)

        self.ptr = 0
        self.path_start_idx = 0

    def store(self, state, action, reward, done, log_prob, value):
        """Store one transition in the buffer."""
        if self.ptr >= self.buffer_size:
            raise RuntimeError("RolloutBuffer overflow.")
        self.states[self.ptr] = state
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.dones[self.ptr] = done
        self.log_probs[self.ptr] = log_prob
        self.values[self.ptr] = value
        self.ptr += 1

    def finish_path(self, last_value=0):
        """
        Compute advantages and returns for the trajectory using GAE (Generalized Advantage Estimation).
        """
        path_slice = slice(self.path_start_idx, self.ptr)
        rewards = np.append(self.rewards[path_slice], last_value)
        values = np.append(self.values[path_slice], last_value)

        advantages = np.zeros_like(rewards[:-1])
        gae = 0
        for t in reversed(range(len(rewards) - 1)):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - self.dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - self.dones[t]) * gae
            advantages[t] = gae

        self.advantages = advantages
        self.returns = advantages + self.values[path_slice]
        self.path_start_idx = self.ptr

    def get(self):
        """Return all data as torch tensors (and normalize advantages)."""
        assert self.ptr == self.buffer_size, "Buffer not full yet!"

        adv_mean = np.mean(self.advantages)
        adv_std = np.std(self.advantages) + 1e-8
        normalized_adv = (self.advantages - adv_mean) / adv_std

        data = dict(
            states=torch.tensor(self.states, dtype=torch.float32, device=self.device),
            actions=torch.tensor(self.actions, dtype=torch.float32, device=self.device),
            returns=torch.tensor(self.returns, dtype=torch.float32, device=self.device),
            advantages=torch.tensor(normalized_adv, dtype=torch.float32, device=self.device),
            log_probs=torch.tensor(self.log_probs, dtype=torch.float32, device=self.device),
        )

        # Reset pointer
        self.ptr, self.path_start_idx = 0, 0
        return data
