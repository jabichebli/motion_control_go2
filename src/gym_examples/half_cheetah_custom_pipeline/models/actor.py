# models/actor.py
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


def mlp(input_dim, output_dim, hidden_sizes=(256, 256), activation=nn.Tanh):
    layers = []
    prev = input_dim
    for h in hidden_sizes:
        layers.append(nn.Linear(prev, h))
        layers.append(activation())
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


class Actor(nn.Module):
    """
    Gaussian policy with tanh squashing and log-prob correction.
    Usage:
        actor = Actor(obs_dim, action_dim, action_low, action_high)
        mean, log_std = actor.forward(obs)
        action, logp = actor.sample_action(obs)
        (During training use reparameterized sampling; for evaluation, use mean)
    """

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        action_low: np.ndarray = None,
        action_high: np.ndarray = None,
        hidden_sizes=(256, 256),
        activation=nn.Tanh,
        log_std_init=-0.5,
        device="cpu",
    ):
        super().__init__()
        self.device = torch.device(device)
        self.obs_dim = obs_dim
        self.action_dim = action_dim

        # feature extractor -> outputs mean
        self.net = mlp(obs_dim, action_dim, hidden_sizes, activation)

        # state-independent log_std (trainable parameter)
        log_std = torch.ones(action_dim, dtype=torch.float32) * log_std_init
        self.log_std_param = nn.Parameter(log_std)

        # action bounds
        if action_low is not None and action_high is not None:
            self.action_low = torch.tensor(action_low, dtype=torch.float32, device=self.device)
            self.action_high = torch.tensor(action_high, dtype=torch.float32, device=self.device)
        else:
            # default to [-1, 1] if not provided
            self.action_low = torch.tensor(-1.0, dtype=torch.float32, device=self.device)
            self.action_high = torch.tensor(1.0, dtype=torch.float32, device=self.device)

        # small epsilon for numerical stability
        self._eps = 1e-8

        self.to(self.device)

    def forward(self, obs: torch.Tensor):
        """
        Returns:
            mean: (batch, action_dim)
            log_std: (action_dim,) broadcastable to batch
        """
        mean = self.net(obs)
        log_std = self.log_std_param.clamp(-20, 2)  # clamp for numerical stability
        return mean, log_std

    @staticmethod
    def _gaussian_log_prob(noise, log_std):
        # noise = (action - mean) / std
        # log_prob (per-dim) = -0.5 * (noise^2 + 2*log_std + log(2*pi))
        return -0.5 * (noise.pow(2) + 2 * log_std + torch.log(torch.tensor(2 * np.pi)))

    def _apply_squash_correction(self, pre_squash_action, squashed_action):
        # For tanh correction: log_det_jacobian = sum(log(1 - tanh(x)^2))
        # pre_squash_action and squashed_action are tensors of same shape
        # correction per-dim: log(1 - tanh(pre)^2 + eps)
        # return: sum over action dims of -log(1 - tanh(pre)^2)
        # More stable: use 2*(log(2) - pre - softplus(-2*pre)) see some implementations,
        # but we'll use the direct formula with a small eps for clarity.
        # compute correction term: sum(log(1 - squashed^2) + eps)
        correction = torch.log(1.0 - squashed_action.pow(2) + self._eps)
        # sum across last dimension
        return correction.sum(dim=-1)

    def sample_action(self, obs: np.ndarray, deterministic=False):
        """
        High-level helper used during rollouts.
        Args:
            obs: np array (obs_dim,) or (batch, obs_dim)
            deterministic: if True return mean action (squashed and scaled)
        Returns:
            action_np: numpy array of action(s), scaled to action bounds
            logp: torch tensor of log-prob (batch,) (None if deterministic)
            mean_np: numpy array of mean action (before sampling, scaled)
        """
        single = False
        if not isinstance(obs, torch.Tensor):
            obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device)
        else:
            obs_t = obs.to(self.device)
        if obs_t.ndim == 1:
            obs_t = obs_t.unsqueeze(0)
            single = True

        mean, log_std = self.forward(obs_t)
        std = torch.exp(log_std)

        if deterministic:
            pre_squash_action = mean
            sampled = mean
        else:
            # reparameterization trick
            noise = torch.randn_like(mean)
            sampled = mean + noise * std
            pre_squash_action = sampled

        # apply tanh squash to keep in [-1,1]
        squashed = torch.tanh(pre_squash_action)
        # scale to action bounds
        # handle vector or scalar bounds
        low = self.action_low
        high = self.action_high
        # if low/high are scalars expand to action_dim
        if low.ndim == 0:
            low = low.expand(self.action_dim)
        if high.ndim == 0:
            high = high.expand(self.action_dim)
        action = low + (squashed + 1.0) * 0.5 * (high - low)

        if deterministic:
            action_np = action.detach().cpu().numpy()
            if single:
                action_np = action_np[0]
            return action_np, None, mean.detach().cpu().numpy()

        # compute log_prob with Gaussian log prob and tanh correction
        noise = (pre_squash_action - mean) / (std + self._eps)
        log_prob_per_dim = self._gaussian_log_prob(noise, log_std)
        log_prob = log_prob_per_dim.sum(dim=-1)  # sum over action dims

        # correction from tanh squashing
        correction = self._apply_squash_correction(pre_squash_action, squashed)  # sum over dims
        log_prob = log_prob - correction  # subtract because correction = sum(log(1 - tanh^2))
        # return numpy action and torch log_prob
        action_np = action.detach().cpu().numpy()
        if single:
            action_np = action_np[0]
            log_prob = log_prob.squeeze(0)
        return action_np, log_prob, mean.detach().cpu().numpy()

    def evaluate_actions(self, obs: torch.Tensor, actions: torch.Tensor):
        """
        Used during training to compute log_probs and entropy for provided actions.
        Inputs:
            obs: (batch, obs_dim)
            actions: in environment scale (i.e., between action_low and action_high)
        Returns:
            log_probs: (batch,)
            entropy: (batch,) (approx per-sample entropy)
            mean: (batch, action_dim)
        """

        # convert actions to pre-squash space: inverse of scaling + atanh
        # Step 1: map actions from [low, high] -> [-1, 1]
        low = self.action_low
        high = self.action_high
        if low.ndim == 0:
            low = low.expand(self.action_dim)
        if high.ndim == 0:
            high = high.expand(self.action_dim)

        # ensure tensors on device
        low = low.to(self.device)
        high = high.to(self.device)
        # actions input assumed to be on same device
        if not isinstance(actions, torch.Tensor):
            actions = torch.tensor(actions, dtype=torch.float32, device=self.device)

        y = 2.0 * (actions - low) / (high - low) - 1.0
        # clip to avoid numerical issues
        y = torch.clamp(y, -1 + 1e-6, 1 - 1e-6)
        # inverse tanh
        pre_squash = 0.5 * torch.log((1 + y) / (1 - y))

        mean, log_std = self.forward(obs)
        std = torch.exp(log_std)
        noise = (pre_squash - mean) / (std + self._eps)

        log_prob_per_dim = self._gaussian_log_prob(noise, log_std)
        base_log_prob = log_prob_per_dim.sum(dim=-1)
        correction = self._apply_squash_correction(pre_squash, torch.tanh(pre_squash))
        log_prob = base_log_prob - correction

        # entropy of diagonal Gaussian (before tanh)
        entropy = (0.5 * (1.0 + torch.log(2 * torch.tensor(np.pi))) + log_std).sum(dim=-1)

        return log_prob, entropy, mean.detach()
