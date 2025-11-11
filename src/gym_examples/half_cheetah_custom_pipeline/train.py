# train.py
import os
import gymnasium as gym
from models.ppo import PPOAgent
from utils.logger import RunLogger  # Optional, replace with simple print if you don't have logger
from utils.memory import RolloutBuffer

# ---------------------
# Hyperparameters
# ---------------------
ENV_ID = "HalfCheetah-v5"
TOTAL_TIMESTEPS = 1_000_000
ROLLOUT_STEPS = 2048  # steps per rollout buffer fill
EVAL_INTERVAL = 10_000  # evaluate every X timesteps
MODEL_DIR = "./models"
LOG_DIR = "./logs"
TB_LOG_DIR = "./tb_logs"

# ---------------------
# Setup directories
# ---------------------
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TB_LOG_DIR, exist_ok=True)

# ---------------------
# Create environment
# ---------------------
env = gym.make(ENV_ID)
eval_env = gym.make(ENV_ID)  # for evaluation

# ---------------------
# Load or initialize PPO
# ---------------------
model_path = f"{MODEL_DIR}/ppo_{ENV_ID}_final.pth"
if os.path.exists(model_path):
    print(f"Loading existing model from {model_path}")
    agent = PPOAgent.load(model_path, env)
else:
    agent = PPOAgent(
        env=env,
        state_dim=env.observation_space.shape[0],
        action_dim=env.action_space.shape[0],
        max_action=float(env.action_space.high[0])
    )

# ---------------------
# Optional logger setup
# ---------------------
logger = RunLogger(log_dir=LOG_DIR)

# ---------------------
# Training Loop
# ---------------------
timesteps = 0
episode_rewards = []

obs, _ = env.reset()
episode_reward = 0

print("Starting training...")

while timesteps < TOTAL_TIMESTEPS:
    # Collect rollout for PPO buffer
    for _ in range(ROLLOUT_STEPS):
        action, log_prob, value = agent.select_action(obs)
        next_obs, reward, terminated, truncated, info = env.step(action)

        agent.buffer.store(obs, action, reward, value, log_prob)
        episode_reward += reward
        obs = next_obs
        timesteps += 1

        if terminated or truncated:
            agent.buffer.finish_path(last_value=0)
            episode_rewards.append(episode_reward)
            logger.log_scalar("episode_reward", episode_reward, timestep=timesteps)
            print(f"Episode finished | Reward: {episode_reward:.2f} | Timesteps: {timesteps}")
            obs, _ = env.reset()
            episode_reward = 0

        if timesteps >= TOTAL_TIMESTEPS:
            break

    # PPO policy update
    agent.update()

    # Optional: evaluation
    if timesteps % EVAL_INTERVAL == 0:
        eval_reward = 0
        eval_obs, _ = eval_env.reset()
        done = False
        while not done:
            action, _, _ = agent.select_action(eval_obs, deterministic=True)
            eval_obs, reward, terminated, truncated, _ = eval_env.step(action)
            eval_reward += reward
            done = terminated or truncated
        logger.log_scalar("eval_reward", eval_reward, timestep=timesteps)
        print(f"[Eval] Timesteps: {timesteps} | Eval Reward: {eval_reward:.2f}")

# ---------------------
# Save final model
# ---------------------
agent.save(model_path)
print(f"Training complete. Model saved to {model_path}")

env.close()
eval_env.close()
