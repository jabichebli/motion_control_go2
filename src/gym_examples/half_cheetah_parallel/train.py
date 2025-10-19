# train.py
import os
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor
from stable_baselines3.common.callbacks import CheckpointCallback
import numpy as np
import torch
import random


def make_env(rank, log_dir):
    """Utility to create a monitored gym environment."""
    def _init():
        env = gym.make("HalfCheetah-v5")
        env = Monitor(env, os.path.join(log_dir, f"monitor_{rank}.csv"))
        return env
    return _init


def main():
    # --- Directories ---
    log_dir = "./logs"
    model_dir = "./models"
    tb_log_dir = "./tb_logs"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(tb_log_dir, exist_ok=True)

    # --- Reproducibility ---
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    # --- Create parallel environments ---
    num_envs = max(1, os.cpu_count() // 2)  # half of CPU cores
    env_fns = [make_env(i, log_dir) for i in range(num_envs)]
    env = SubprocVecEnv(env_fns)
    env = VecMonitor(env, log_dir)

    # --- Load or create PPO model ---
    final_model_path = f"{model_dir}/ppo_HalfCheetah_final.zip"
    if os.path.exists(final_model_path):
        model = PPO.load(final_model_path, env=env)
    else:
        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            tensorboard_log=tb_log_dir,
            n_steps=2048 // num_envs,  # rollout per env
            batch_size=64,
            n_epochs=10,
            learning_rate=3e-4,
            gamma=0.99,
            device="auto",
        )

    # --- Checkpoints ---
    checkpoint_callback = CheckpointCallback(
        save_freq=100_000 // num_envs,
        save_path=model_dir,
        name_prefix="ppo_HalfCheetah_checkpoint",
    )

    # --- Train ---
    model.learn(total_timesteps=3_000_000, callback=checkpoint_callback)

    # --- Save final ---
    model.save(final_model_path)
    print(f"Training complete. Model saved to {final_model_path}")

    env.close()


if __name__ == "__main__":
    # Needed for multiprocessing
    main()
