import gymnasium as gym
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random

# ------------------------------
# Replay Buffer
# ------------------------------
class ReplayBuffer:
    def __init__(self, max_size=100000):
        self.buffer = deque(maxlen=max_size)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(states),
            torch.FloatTensor(actions),
            torch.FloatTensor(rewards).unsqueeze(1),
            torch.FloatTensor(next_states),
            torch.FloatTensor(dones).unsqueeze(1)
        )

    def __len__(self):
        return len(self.buffer)


# ------------------------------
# Actor & Critic Networks
# ------------------------------
class Actor(nn.Module):
    def __init__(self, state_dim, action_dim, max_action):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 400),
            nn.ReLU(),
            nn.Linear(400, 300),
            nn.ReLU(),
            nn.Linear(300, action_dim),
            nn.Tanh()
        )
        self.max_action = max_action

    def forward(self, x):
        return self.max_action * self.net(x)


class Critic(nn.Module):
    def __init__(self, state_dim, action_dim):
        super().__init__()
        # Q1 network
        self.q1 = nn.Sequential(
            nn.Linear(state_dim + action_dim, 400),
            nn.ReLU(),
            nn.Linear(400, 300),
            nn.ReLU(),
            nn.Linear(300, 1)
        )
        # Q2 network
        self.q2 = nn.Sequential(
            nn.Linear(state_dim + action_dim, 400),
            nn.ReLU(),
            nn.Linear(400, 300),
            nn.ReLU(),
            nn.Linear(300, 1)
        )

    def forward(self, state, action):
        sa = torch.cat([state, action], dim=-1)
        return self.q1(sa), self.q2(sa)


# ------------------------------
# TD3 Agent
# ------------------------------
class TD3Agent:
    def __init__(self, state_dim, action_dim, max_action,
                 lr=3e-4, gamma=0.99, tau=0.005, policy_noise=0.2, noise_clip=0.5, policy_freq=2):
        self.actor = Actor(state_dim, action_dim, max_action)
        self.actor_target = Actor(state_dim, action_dim, max_action)
        self.actor_target.load_state_dict(self.actor.state_dict())
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr)

        self.critic = Critic(state_dim, action_dim)
        self.critic_target = Critic(state_dim, action_dim)
        self.critic_target.load_state_dict(self.critic.state_dict())
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr)

        self.max_action = max_action
        self.gamma = gamma
        self.tau = tau
        self.policy_noise = policy_noise
        self.noise_clip = noise_clip
        self.policy_freq = policy_freq
        self.total_it = 0

    def select_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0)
        return self.actor(state).detach().cpu().numpy()[0]

    def train(self, replay_buffer, batch_size=100):
        self.total_it += 1
        states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size)

        # ------------------------------
        # Critic Update
        # ------------------------------
        with torch.no_grad():
            # Add clipped noise to next action
            noise = (torch.randn_like(actions) * self.policy_noise).clamp(-self.noise_clip, self.noise_clip)
            next_actions = (self.actor_target(next_states) + noise).clamp(-self.max_action, self.max_action)

            # Compute target Q
            target_q1, target_q2 = self.critic_target(next_states, next_actions)
            target_q = torch.min(target_q1, target_q2)
            target_q = rewards + (1 - dones) * self.gamma * target_q

        current_q1, current_q2 = self.critic(states, actions)
        critic_loss = nn.MSELoss()(current_q1, target_q) + nn.MSELoss()(current_q2, target_q)
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        # ------------------------------
        # Delayed Policy Update
        # ------------------------------
        if self.total_it % self.policy_freq == 0:
            actor_loss = -self.critic.q1(torch.cat([states, self.actor(states)], dim=-1), self.actor(states)).mean()
            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            self.actor_optimizer.step()

            # Soft update target networks
            for param, target_param in zip(self.critic.parameters(), self.critic_target.parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
            for param, target_param in zip(self.actor.parameters(), self.actor_target.parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)


# ------------------------------
# Main Training Loop
# ------------------------------
def train_td3(env_name="Hopper-v5", max_episodes=500, max_steps=1000):
    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    max_action = float(env.action_space.high[0])

    agent = TD3Agent(state_dim, action_dim, max_action)
    replay_buffer = ReplayBuffer()

    for ep in range(max_episodes):
        obs, info = env.reset()
        episode_reward = 0

        for step in range(max_steps):
            # Select action + exploration noise
            action = agent.select_action(obs)
            action = (action + np.random.normal(0, 0.1, size=action_dim)).clip(-max_action, max_action)

            # Step through environment
            next_obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            # Store in replay buffer
            replay_buffer.push(obs, action, reward, next_obs, done)
            obs = next_obs
            episode_reward += reward

            # Train agent
            if len(replay_buffer) > 1000:
                agent.train(replay_buffer)

            if done:
                break

        print(f"Episode {ep}: Reward={episode_reward:.2f}")

    env.close()


if __name__ == "__main__":
    train_td3()
