import gymnasium as gym
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
import imageio
import matplotlib.pyplot as plt
import mujoco
# =====================
# Hyperparameters
# =====================
ENV_NAME = "Hopper-v5"
SEED = 42
MAX_EPISODES = 2500
MAX_STEPS = 1000
BATCH_SIZE = 256
GAMMA = 0.99
TAU = 0.005
ACTOR_LR = 1e-3
CRITIC_LR = 1e-3
POLICY_NOISE = 0.2
NOISE_CLIP = 0.5
POLICY_FREQ = 2
BUFFER_SIZE = int(1e6)

# =====================
# Utilities
# =====================
def set_seed(env, seed=SEED):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    env.action_space.seed(seed)
    env.observation_space.seed(seed)

# =====================
# Replay Buffer
# =====================
class ReplayBuffer:
    def __init__(self, max_size=BUFFER_SIZE):
        self.buffer = deque(maxlen=max_size)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size=BATCH_SIZE):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(np.array(states)),
            torch.FloatTensor(np.array(actions)),
            torch.FloatTensor(np.array(rewards)).unsqueeze(1),
            torch.FloatTensor(np.array(next_states)),
            torch.FloatTensor(np.array(dones)).unsqueeze(1)
        )

    def size(self):
        return len(self.buffer)

# =====================
# Actor Network
# =====================
class Actor(nn.Module):
    def __init__(self, state_dim, action_dim, max_action):
        super().__init__()
        self.max_action = max_action
        self.net = nn.Sequential(
            nn.Linear(state_dim, 400),
            nn.ReLU(),
            nn.Linear(400, 300),
            nn.ReLU(),
            nn.Linear(300, action_dim),
            nn.Tanh()
        )

    def forward(self, state):
        return self.max_action * self.net(state)

# =====================
# Critic Network (Twin Q)
# =====================
class Critic(nn.Module):
    def __init__(self, state_dim, action_dim):
        super().__init__()
        # Q1
        self.q1 = nn.Sequential(
            nn.Linear(state_dim + action_dim, 400),
            nn.ReLU(),
            nn.Linear(400, 300),
            nn.ReLU(),
            nn.Linear(300, 1)
        )
        # Q2
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

    def q1_value(self, state, action):
        sa = torch.cat([state, action], dim=-1)
        return self.q1(sa)

# =====================
# TD3 Agent
# =====================
class TD3Agent:
    def __init__(self, state_dim, action_dim, max_action):
        self.actor = Actor(state_dim, action_dim, max_action)
        self.actor_target = Actor(state_dim, action_dim, max_action)
        self.actor_target.load_state_dict(self.actor.state_dict())
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=ACTOR_LR)

        self.critic = Critic(state_dim, action_dim)
        self.critic_target = Critic(state_dim, action_dim)
        self.critic_target.load_state_dict(self.critic.state_dict())
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=CRITIC_LR)

        self.max_action = max_action
        self.total_it = 0

    def select_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0)
        return self.actor(state).detach().cpu().numpy()[0]

    def train(self, replay_buffer):
        if replay_buffer.size() < BATCH_SIZE:
            return

        self.total_it += 1

        # Sample batch
        states, actions, rewards, next_states, dones = replay_buffer.sample(BATCH_SIZE)

        with torch.no_grad():
            # Add noise to actions
            noise = (torch.randn_like(actions) * POLICY_NOISE).clamp(-NOISE_CLIP, NOISE_CLIP)
            next_actions = (self.actor_target(next_states) + noise).clamp(-self.max_action, self.max_action)

            # Target Q-values
            target_q1, target_q2 = self.critic_target(next_states, next_actions)
            target_q = rewards + GAMMA * (1 - dones) * torch.min(target_q1, target_q2)

        # Critic loss
        current_q1, current_q2 = self.critic(states, actions)
        critic_loss = nn.MSELoss()(current_q1, target_q) + nn.MSELoss()(current_q2, target_q)
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        # Delayed policy updates
        if self.total_it % POLICY_FREQ == 0:
            # Actor loss
            actor_loss = -self.critic.q1_value(states, self.actor(states)).mean()
            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            self.actor_optimizer.step()

            # Soft update
            for param, target_param in zip(self.critic.parameters(), self.critic_target.parameters()):
                target_param.data.copy_(TAU * param.data + (1 - TAU) * target_param.data)
            for param, target_param in zip(self.actor.parameters(), self.actor_target.parameters()):
                target_param.data.copy_(TAU * param.data + (1 - TAU) * target_param.data)

# =====================
# Training loop
# =====================
def train_td3(env_name=ENV_NAME, episodes=MAX_EPISODES, max_steps=MAX_STEPS):
    env = gym.make(env_name, render_mode=None)  # headless training
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    max_action = env.action_space.high[0]

    agent = TD3Agent(state_dim, action_dim, max_action)
    replay_buffer = ReplayBuffer()

    episode_rewards = []

    for ep in range(episodes):
        state, _ = env.reset()
        ep_reward = 0

        for step in range(max_steps):
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            replay_buffer.push(state, action, reward, next_state, float(done))
            agent.train(replay_buffer)

            state = next_state
            ep_reward += reward
            if done:
                break

        episode_rewards.append(ep_reward)
        print(f"Episode {ep} Reward: {ep_reward:.2f}")

    env.close()
    print("Training complete!")
    # --- Plot rewards ---
    plt.figure(figsize=(10,5))
    plt.plot(episode_rewards, label='Episode Reward')
    window = 10
    moving_avg = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
    plt.plot(np.arange(window-1, len(episode_rewards)), moving_avg, color='red', linewidth=2, label=f'{window}-Episode Moving Avg')
    plt.title("TD3 Training Rewards")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.grid(True)
    plt.legend()
    plt.show()

    return episode_rewards

# =====================
# Run training
# =====================
if __name__ == "__main__":
    rewards = train_td3()
    print("Training complete!")
