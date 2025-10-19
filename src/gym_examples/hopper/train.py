# train.py
from stable_baselines3 import PPO
import gymnasium as gym
import os
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback

# --- Setup directories ---
log_dir = "./logs"
model_dir = "./models"
os.makedirs(log_dir, exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

# --- Create Hopper environment ---
env = gym.make("Hopper-v5")
env = Monitor(env, log_dir)

# --- Initialize PPO model ---
model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    tensorboard_log="./tb_logs/"
)

# --- Save checkpoints every 100k steps ---
checkpoint_callback = CheckpointCallback(
    save_freq=100_000,
    save_path=model_dir,
    name_prefix="ppo_hopper_checkpoint",
)

# --- Train model ---
model.learn(total_timesteps=1_000_000, callback=checkpoint_callback)

# --- Save final model ---
model.save(f"{model_dir}/ppo_hopper_final.zip")

print("Training complete. Model saved to models/ppo_hopper_final.zip")

env.close()

