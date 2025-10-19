# models/ppo.py
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import numpy as np

# -----------------------
# Actor & Critic Networks
# -----------------------
class Actor(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        return self.net(x)

class Critic(nn.Module):
    def __init__(self, state_dim, hidden_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x):
        return self.net(x)


# -----------------------
# Rollout Buffer
# -----------------------
class RolloutBuffer:
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.dones = []

    def clear(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.dones = []

# -----------------------
# PPO Agent
# -----------------------
class PPO:
    def __init__(self, state_dim, action_dim, lr_actor=3e-4, lr_critic=1e-3, gamma=0.99, eps_clip=0.2):
        self.actor = Actor(state_dim, action_dim)
        self.critic = Critic(state_dim)
        self.optimizer_actor = optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.optimizer_critic = optim.Adam(self.critic.parameters(), lr=lr_critic)

        self.gamma = gamma
        self.eps_clip = eps_clip
        self.buffer = RolloutBuffer()

    def select_action(self, state):
        state = torch.tensor(state, dtype=torch.float32)
        probs = self.actor(state)
        dist = Categorical(probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)

        self.buffer.states.append(state)
        self.buffer.actions.append(action)
        self.buffer.log_probs.append(log_prob)
        return action.item()
    
    def compute_gae(self, rewards, dones, values, gamma=0.99, lam=0.95):
        advantages = []
        gae = 0
        values = values + [0]  # append V(s_{t+1}) = 0 for last step
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + gamma * lam * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        return advantages

    def update(self):
        # Convert buffer to tensors
        states = torch.stack(self.buffer.states)
        actions = torch.stack(self.buffer.actions)
        old_log_probs = torch.stack(self.buffer.log_probs)
        rewards = self.compute_returns(self.buffer.rewards, self.buffer.dones)

        # Normalize rewards
        rewards = torch.tensor(rewards, dtype=torch.float32)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)

        # PPO update loop
        for _ in range(4):  # PPO epochs
            # Compute current log probs & values
            probs = self.actor(states)
            dist = Categorical(probs)
            log_probs = dist.log_prob(actions)
            values = self.critic(states).squeeze()

            # Ratios for clipped surrogate
            ratios = torch.exp(log_probs - old_log_probs.detach())
            advantages = rewards - values.detach()

            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.eps_clip, 1 + self.eps_clip) * advantages

            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.MSELoss()(values, rewards)

            self.optimizer_actor.zero_grad()
            actor_loss.backward()
            self.optimizer_actor.step()

            self.optimizer_critic.zero_grad()
            critic_loss.backward()
            self.optimizer_critic.step()

        self.buffer.clear()

    def compute_returns(self, rewards, dones):
        returns = []
        R = 0
        for r, done in zip(reversed(rewards), reversed(dones)):
            if done:
                R = 0
            R = r + self.gamma * R
            returns.insert(0, R)
        return returns


# -----------------------
# Minimal training loop
# -----------------------
if __name__ == "__main__":
    import gym
    env = gym.make("CartPole-v1")
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n

    ppo = PPO(state_dim, action_dim)
    max_episodes = 1000
    max_timesteps = 200

    for ep in range(max_episodes):
        state = env.reset()
        ep_reward = 0
        for t in range(max_timesteps):
            action = ppo.select_action(state)
            next_state, reward, done, _ = env.step(action)
            ppo.buffer.rewards.append(reward)
            ppo.buffer.dones.append(done)

            state = next_state
            ep_reward += reward
            if done:
                break

        ppo.update()
        print(f"Episode {ep} reward: {ep_reward}")
