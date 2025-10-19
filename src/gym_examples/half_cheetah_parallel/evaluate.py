# evaluate.py
from stable_baselines3 import PPO
import gymnasium as gym

# --- Load environment ---
env = gym.make("HalfCheetah-v5", render_mode="human")

# --- Load trained model ---
model = PPO.load("./models/ppo_HalfCheetah_final.zip")

# --- Run for a few episodes ---
for episode in range(5):
    obs, info = env.reset()
    done = False
    total_reward = 0

    while not done:
        action, _ = model.predict(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward

    print(f"Episode {episode+1} reward: {total_reward:.2f}")

env.close()
