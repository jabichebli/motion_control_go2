# rl_go2/envs/test_ppo.py
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from go2_env import Go2Env

# --- Load trained model ---
model_path = "./models/ppo_go2_final.zip"
model = PPO.load(model_path)

# --- Environment ---
def make_env():
    return Go2Env(render_mode="none")  # headless

env = DummyVecEnv([make_env])

# --- Run one episode ---
obs = env.reset()
done = False
total_reward = 0.0
step = 0

while step < 1000:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    step += 1
    if terminated or truncated:
        obs = env.reset()

env.close()
print(f"Total reward from episode: {total_reward:.2f}")
