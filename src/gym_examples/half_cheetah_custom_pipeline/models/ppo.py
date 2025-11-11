"""
PPO.py
Full PPO trainer (Gymnasium-compatible) using your Actor, Critic and RolloutBuffer.

Usage:
    python PPO.py

Adjust hyperparameters in the main() function or pass arguments by editing.
"""

import os
import time
import argparse
from collections import deque

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Import your modules (assumes project layout has models/ and utils/ on PYTHONPATH)
from models.actor import Actor
from models.critic import Critic
from utils.memory import RolloutBuffer


class PPOAgent:
    def __init__(
        self,
        obs_dim,
        action_dim,
        action_low,
        action_high,
        device="cpu",
        actor_hidden=(256, 256),
        critic_hidden=(256, 256),
        actor_lr=3e-4,
        critic_lr=1e-3,
        clip_ratio=0.2,
        vf_coef=0.5,
        ent_coef=0.0,
        max_grad_norm=0.5,
        train_epochs=10,
        minibatch_size=64,
    ):
        self.device = device
        self.actor = Actor(obs_dim, action_dim, action_low, action_high, hidden_sizes=actor_hidden, device=device)
        self.critic = Critic(obs_dim, hidden_sizes=critic_hidden, device=device)

        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=actor_lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=critic_lr)

        self.clip_ratio = clip_ratio
        self.vf_coef = vf_coef
        self.ent_coef = ent_coef
        self.max_grad_norm = max_grad_norm
        self.train_epochs = train_epochs
        self.minibatch_size = minibatch_size

    def select_action(self, obs, deterministic=False):
        """
        Returns:
            action_np: numpy action (env scale)
            logp: torch scalar (on device)
            value: float
            mean_np: numpy mean action (pre-sampling, scaled)
        """
        # Actor.sample_action expects numpy obs
        action_np, logp, mean = self.actor.sample_action(obs, deterministic=deterministic)
        # value estimate from critic
        if isinstance(obs, np.ndarray):
            obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device)
        else:
            obs_t = obs.to(self.device)
        value_t = self.critic(obs_t)
        # value_t might be a tensor (batch or scalar). convert to float (single)
        if torch.is_tensor(value_t):
            value = value_t.detach().cpu().numpy()
            # if batch of size 1 reduce
            if np.ndim(value) > 0 and value.shape[0] == 1:
                value = float(value[0])
            else:
                # if user passed batch we take first
                value = float(value[0]) if np.ndim(value) > 0 else float(value)
        else:
            value = float(value_t)

        # logp could be tensor, convert to float
        if isinstance(logp, torch.Tensor):
            logp_val = float(logp.detach().cpu().numpy()) if logp.ndim == 0 else float(logp.detach().cpu().numpy()[0])
        else:
            logp_val = float(logp) if logp is not None else None

        return action_np, logp_val, value, mean

    def update(self, rollout_data):
        """
        rollout_data: dict with tensors (states, actions, returns, advantages, log_probs)
        All tensors are already on the agent device (RolloutBuffer.get() did that).
        """
        states = rollout_data["states"]
        actions = rollout_data["actions"]
        returns = rollout_data["returns"]
        advantages = rollout_data["advantages"]
        old_log_probs = rollout_data["log_probs"]

        dataset = TensorDataset(states, actions, returns, advantages, old_log_probs)
        dataloader = DataLoader(dataset, batch_size=self.minibatch_size, shuffle=True)

        actor_losses = []
        critic_losses = []
        approx_kls = []
        entropies = []

        for epoch in range(self.train_epochs):
            for batch in dataloader:
                b_states, b_actions, b_returns, b_advs, b_old_logp = batch

                # Ensure device
                b_states = b_states.to(self.device)
                b_actions = b_actions.to(self.device)
                b_returns = b_returns.to(self.device)
                b_advs = b_advs.to(self.device)
                b_old_logp = b_old_logp.to(self.device)

                # Evaluate current policy for the batch actions
                # Actor.evaluate_actions expects actions in env scale
                new_logp, entropy, _ = self.actor.evaluate_actions(b_states, b_actions)
                # new_logp: (batch,)
                # entropy: (batch,)
                # Convert as needed
                ratio = torch.exp(new_logp - b_old_logp)  # (batch,)

                # Policy loss (clipped surrogate)
                surrogate1 = ratio * b_advs
                surrogate2 = torch.clamp(ratio, 1.0 - self.clip_ratio, 1.0 + self.clip_ratio) * b_advs
                policy_loss = -torch.min(surrogate1, surrogate2).mean()

                # Entropy (we'll minimize -entropy)
                entropy_loss = -entropy.mean() if entropy is not None else 0.0

                # Value function loss
                values = self.critic(b_states).squeeze(-1)  # (batch,)
                value_loss = nn.functional.mse_loss(values, b_returns)

                # Combined losses: actor update
                self.actor_optimizer.zero_grad()
                total_actor_loss = policy_loss + self.ent_coef * entropy_loss
                total_actor_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm)
                self.actor_optimizer.step()

                # Critic update
                self.critic_optimizer.zero_grad()
                total_critic_loss = self.vf_coef * value_loss
                total_critic_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.critic.parameters(), self.max_grad_norm)
                self.critic_optimizer.step()

                actor_losses.append(policy_loss.item())
                critic_losses.append(value_loss.item())
                entropies.append(-entropy_loss if isinstance(entropy_loss, torch.Tensor) else 0.0)

                # approx KL for monitoring
                with torch.no_grad():
                    approx_kl = (b_old_logp - new_logp).mean().item()
                    approx_kls.append(approx_kl)

        stats = {
            "actor_loss": float(np.mean(actor_losses)) if actor_losses else 0.0,
            "critic_loss": float(np.mean(critic_losses)) if critic_losses else 0.0,
            "entropy": float(np.mean(entropies)) if entropies else 0.0,
            "approx_kl": float(np.mean(approx_kls)) if approx_kls else 0.0,
        }
        return stats

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(
            {
                "actor_state_dict": self.actor.state_dict(),
                "critic_state_dict": self.critic.state_dict(),
                "actor_optimizer": self.actor_optimizer.state_dict(),
                "critic_optimizer": self.critic_optimizer.state_dict(),
            },
            path,
        )

    def load(self, path, map_location=None):
        checkpoint = torch.load(path, map_location=map_location)
        self.actor.load_state_dict(checkpoint["actor_state_dict"])
        self.critic.load_state_dict(checkpoint["critic_state_dict"])
        if "actor_optimizer" in checkpoint:
            self.actor_optimizer.load_state_dict(checkpoint["actor_optimizer"])
        if "critic_optimizer" in checkpoint:
            self.critic_optimizer.load_state_dict(checkpoint["critic_optimizer"])


def evaluate_policy(env, agent, n_episodes=5, max_steps=1000, render=False):
    """
    Runs deterministic episodes to evaluate current policy.
    """
    returns = []
    for ep in range(n_episodes):
        obs, _ = env.reset()
        done = False
        total_r = 0.0
        steps = 0
        while True:
            action, _, _, _ = agent.select_action(obs, deterministic=True)
            obs, r, terminated, truncated, info = env.step(action)
            total_r += float(r)
            steps += 1
            if terminated or truncated or steps >= max_steps:
                break
        returns.append(total_r)
    return np.mean(returns), np.std(returns)


def make_env(env_name, seed=None):
    env = gym.make(env_name)
    if seed is not None:
        env.reset(seed=seed)
        try:
            env.action_space.seed(seed)
            env.observation_space.seed(seed)
        except Exception:
            pass
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=str, default="Pendulum-v1", help="Gymnasium env id (continuous example)")
    parser.add_argument("--total_timesteps", type=int, default=200_000)
    parser.add_argument("--steps_per_epoch", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--save_path", type=str, default="./checkpoints/ppo_checkpoint.pt")
    parser.add_argument("--eval_every_epochs", type=int, default=5)
    parser.add_argument("--eval_episodes", type=int, default=5)
    args = parser.parse_args()

    # reproducibility
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    env = make_env(args.env, seed=args.seed)
    obs_space = env.observation_space
    act_space = env.action_space

    assert isinstance(act_space, gym.spaces.Box), "This trainer expects continuous Box action spaces."
    obs_dim = int(np.prod(obs_space.shape))
    action_dim = int(np.prod(act_space.shape))
    action_low = act_space.low
    action_high = act_space.high

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    # hyperparams
    steps_per_epoch = args.steps_per_epoch
    total_timesteps = args.total_timesteps
    epochs = int(np.ceil(total_timesteps / steps_per_epoch))
    buffer_size = steps_per_epoch

    agent = PPOAgent(
        obs_dim=obs_dim,
        action_dim=action_dim,
        action_low=action_low,
        action_high=action_high,
        device=device,
        actor_hidden=(256, 256),
        critic_hidden=(256, 256),
        actor_lr=3e-4,
        critic_lr=1e-3,
        clip_ratio=0.2,
        vf_coef=0.5,
        ent_coef=0.0,
        max_grad_norm=0.5,
        train_epochs=10,
        minibatch_size=64,
    )

    # Buffer
    buffer = RolloutBuffer(buffer_size=buffer_size, state_dim=obs_dim, action_dim=action_dim, gamma=0.99, gae_lambda=0.95, device=device)

    # Logging
    ep_returns = deque(maxlen=100)
    start_time = time.time()

    obs, _ = env.reset(seed=args.seed)
    ep_ret = 0.0
    ep_len = 0

    for epoch in range(1, epochs + 1):
        for step in range(steps_per_epoch):
            # select action
            action, logp, value, _ = agent.select_action(obs, deterministic=False)

            # step env
            next_obs, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)

            # store. Actor.sample_action returned action in numpy scale
            # Ensure action has correct shape when storing (action_dim,)
            action_to_store = np.array(action, dtype=np.float32)
            # some envs return scalar action for 1-D action spaces; ensure shape
            if action_dim == 1:
                action_to_store = np.reshape(action_to_store, (1,))

            # store into buffer
            buffer.store(state=np.ascontiguousarray(np.array(obs, dtype=np.float32).reshape(-1)),
                         action=action_to_store,
                         reward=float(reward),
                         done=done,
                         log_prob=float(logp),
                         value=float(value))

            obs = next_obs
            ep_ret += float(reward)
            ep_len += 1

            if done:
                # if episode ended because of truncation/termination we compute last_value accordingly
                # if terminated -> last_value = 0, if truncated -> estimate V(s') for bootstrap
                if truncated:
                    # bootstrap from value of last state
                    last_value = float(agent.critic(torch.tensor(obs, dtype=torch.float32, device=device)).detach().cpu().numpy().squeeze())
                else:
                    last_value = 0.0
                buffer.finish_path(last_value=last_value)

                ep_returns.append(ep_ret)
                obs, _ = env.reset()
                ep_ret = 0.0
                ep_len = 0

        # At epoch end, if buffer not closed by episode end, finish path with bootstrap from current obs
        # If buffer.ptr != buffer_size then some trajectories finished earlier; but RolloutBuffer.get asserts full buffer.
        # We compute last_value for the current observation to bootstrap.
        last_value = float(agent.critic(torch.tensor(obs, dtype=torch.float32, device=device)).detach().cpu().numpy().squeeze())
        buffer.finish_path(last_value=last_value)

        # get data and update
        rollout_data = buffer.get()
        stats = agent.update(rollout_data)

        # Logging
        if len(ep_returns) > 0:
            mean_return_100 = np.mean(ep_returns)
        else:
            mean_return_100 = float('nan')

        elapsed = time.time() - start_time
        print(f"Epoch {epoch}/{epochs} | Timesteps {epoch * steps_per_epoch}/{total_timesteps} | "
              f"ActorLoss {stats['actor_loss']:.4f} CriticLoss {stats['critic_loss']:.4f} KL {stats['approx_kl']:.5f} Ent {stats['entropy']:.4f} | "
              f"AvgReturn(100) {mean_return_100:.3f} | Time {elapsed:.1f}s")

        # periodic evaluation + checkpoint
        if epoch % args.eval_every_epochs == 0:
            mean_eval, std_eval = evaluate_policy(env, agent, n_episodes=args.eval_episodes)
            print(f"--- Eval at epoch {epoch}: mean_return {mean_eval:.3f} std {std_eval:.3f}")
            agent.save(args.save_path)
            print(f"Saved checkpoint to {args.save_path}")

    env.close()
    print("Training complete.")

if __name__ == "__main__":
    main()