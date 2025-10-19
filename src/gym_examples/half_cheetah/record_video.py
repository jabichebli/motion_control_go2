# record_video.py
import gymnasium as gym
from stable_baselines3 import PPO
from gymnasium.wrappers import RecordVideo
import os

# --- Config ---
env_id = "HalfCheetah-v5"
model_path = "./models/ppo_HalfCheetah_final.zip"
video_folder = "./videos"
episodes_to_record = 3

# --- Create output directory ---
os.makedirs(video_folder, exist_ok=True)

# --- Make environment with video recorder ---
env = gym.make(env_id, render_mode="rgb_array")
env = RecordVideo(
    env,
    video_folder=video_folder,
    name_prefix="ppo_HalfCheetah_run",
    episode_trigger=lambda ep: True  # record every episode
)

# --- Load trained model ---
model = PPO.load(model_path)
print(f"Recording {episodes_to_record} episodes...")

# --- Run episodes and record ---
for ep in range(episodes_to_record):
    obs, info = env.reset()
    done = False
    total_reward = 0

    while not done:
        action, _ = model.predict(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward

    print(f"Episode {ep+1} reward: {total_reward:.2f}")

env.close()
print(f"Videos saved to: {os.path.abspath(video_folder)}")
