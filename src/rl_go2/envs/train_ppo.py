# rl_go2/envs/train_ppo.py
import os
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor  # for episode stats
from go2_env import Go2Env


# --- Logging callback ------------------------------------------------------
class RewardLoggerCallback(BaseCallback):
    def __init__(self, verbose=1):
        super().__init__(verbose)
        self.episode_rewards = []

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        for info in infos:
            if "episode" in info:
                self.episode_rewards.append(info["episode"]["r"])
        return True


# --- Environment creation ---------------------------------------------------
def make_env():
    env = Go2Env()
    env = Monitor(env)  # record episode stats for callback
    return env


# --- Paths -----------------------------------------------------------------
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "ppo_go2_headless")
VECNORM_PATH = os.path.join(MODEL_DIR, "vecnormalize.pkl")
os.makedirs(MODEL_DIR, exist_ok=True)

# --- Create or load VecNormalize -------------------------------------------
if os.path.exists(VECNORM_PATH):
    print(f"🔁 Loading VecNormalize from {VECNORM_PATH}")
    env = DummyVecEnv([make_env])
    env = VecNormalize.load(VECNORM_PATH, env)
    env.training = True
    env.norm_reward = True
else:
    print("🆕 Creating new VecNormalize environment")
    env = DummyVecEnv([make_env])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)


# --- Load or create PPO model ----------------------------------------------
if os.path.exists(MODEL_PATH + ".zip"):
    print(f"🔁 Resuming PPO training from {MODEL_PATH}")
    model = PPO.load(MODEL_PATH, env=env)
else:
    print("🆕 Creating new PPO model")
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=512,
        gamma=0.995,
        ent_coef=0.001,
        clip_range=0.2,
    )


# --- Train -----------------------------------------------------------------
timesteps = 1_000_000  # can increase later (e.g., 10_000_000)
log_callback = RewardLoggerCallback()

print("🚀 Starting PPO training...")
model.learn(total_timesteps=timesteps, callback=log_callback)
print("✅ Training complete.")


# --- Save everything -------------------------------------------------------
model.save(MODEL_PATH)
env.save(VECNORM_PATH)
print(f"💾 Model and VecNormalize saved to '{MODEL_DIR}'")


# --- Plot reward curve -----------------------------------------------------
if len(log_callback.episode_rewards) > 0:
    plt.figure(figsize=(8, 5))
    plt.plot(np.arange(len(log_callback.episode_rewards)),
             log_callback.episode_rewards, label="Episode Reward")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.title("PPO Training Reward (Go2 headless)")
    plt.grid(True)
    plt.legend()
    os.makedirs("logs", exist_ok=True)
    plt.savefig("logs/reward_curve.png")
    plt.show()
else:
    print("⚠️ No episode rewards recorded — check that Monitor is wrapping the env.")



# # rl_go2/envs/train_ppo.py
# import os
# import numpy as np
# import matplotlib.pyplot as plt
# from stable_baselines3 import PPO
# from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
# from stable_baselines3.common.callbacks import BaseCallback
# from gymnasium.wrappers import RecordEpisodeStatistics
# from go2_env import Go2Env
# from stable_baselines3.common.monitor import Monitor


# # --- Logging callback ---
# class RewardLoggerCallback(BaseCallback):
#     def __init__(self, verbose=1):
#         super().__init__(verbose)
#         self.episode_rewards = []

#     def _on_step(self) -> bool:
#         infos = self.locals.get("infos", [])
#         for info in infos:
#             if "episode" in info:
#                 self.episode_rewards.append(info["episode"]["r"])
#         return True

# # --- Environment ---
# # def make_env():
# #     env = Go2Env()  # headless
# #     env = RecordEpisodeStatistics(env)  # automatically add episode reward info
# #     return env

# # env = DummyVecEnv([make_env])
# def make_env():
#     env = Go2Env()
#     env = Monitor(env)
#     return env

# env = DummyVecEnv([make_env])
# env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

# # --- Create PPO model ---
# model = PPO(
#     "MlpPolicy",
#     env,
#     verbose=1,
#     learning_rate=3e-4,
#     n_steps=2048,
#     batch_size=512,
#     gamma=0.995,
#     ent_coef=0.001,
#     clip_range=0.2,
# )

# # --- Train ---
# log_callback = RewardLoggerCallback()
# timesteps = 1_000_000  # start small, increase later
# model.learn(total_timesteps=timesteps, callback=log_callback)

# # --- Save model ---
# os.makedirs("models", exist_ok=True)
# model.save("models/ppo_go2_headless")

# # --- Plot reward curve ---
# if len(log_callback.episode_rewards) > 0:
#     plt.figure(figsize=(8, 5))
#     plt.plot(np.arange(len(log_callback.episode_rewards)), log_callback.episode_rewards, label="Episode Reward")
#     plt.xlabel("Episode")
#     plt.ylabel("Reward")
#     plt.title("PPO Training Reward (Go2 headless)")
#     plt.grid(True)
#     plt.legend()
#     os.makedirs("logs", exist_ok=True)
#     plt.savefig("logs/reward_curve.png")
#     plt.show()
# else:
#     print("No episode rewards recorded. Make sure the environment returns 'episode' info.")


# # train_ppo.py
# import os
# import numpy as np
# import matplotlib.pyplot as plt
# from stable_baselines3 import PPO
# from stable_baselines3.common.vec_env import DummyVecEnv
# from stable_baselines3.common.callbacks import BaseCallback
# from go2_env import Go2Env

# # -----------------------------
# # Reward logger callback
# # -----------------------------
# class RewardLoggerCallback(BaseCallback):
#     def __init__(self, verbose=1):
#         super().__init__(verbose)
#         self.episode_rewards = []

#     def _on_step(self) -> bool:
#         # "infos" comes from env.step()
#         infos = self.locals.get("infos", [])
#         for info in infos:
#             if "episode" in info:
#                 self.episode_rewards.append(info["episode"]["r"])
#         return True

# # -----------------------------
# # Environment
# # -----------------------------
# def make_env():
#     return Go2Env()  # headless

# env = DummyVecEnv([make_env])

# # -----------------------------
# # PPO Model
# # -----------------------------
# model = PPO(
#     "MlpPolicy",
#     env,
#     verbose=1,
#     learning_rate=3e-4,
#     n_steps=2048,
#     batch_size=64,  # old code hyperparameter
#     n_epochs=10,
#     gamma=0.99,
#     gae_lambda=0.95,
#     clip_range=0.2,
#     ent_coef=0.0,
# )

# # -----------------------------
# # Train
# # -----------------------------
# reward_logger = RewardLoggerCallback()
# timesteps = 50_000  # start small, increase later
# model.learn(total_timesteps=timesteps, callback=reward_logger)

# # -----------------------------
# # Save model
# # -----------------------------
# os.makedirs("models", exist_ok=True)
# model.save("models/ppo_go2_headless")

# # -----------------------------
# # Plot reward curve
# # -----------------------------
# plt.figure(figsize=(8, 5))
# plt.plot(reward_logger.episode_rewards, label="Episode Reward")
# plt.xlabel("Episode")
# plt.ylabel("Total Reward")
# plt.title("PPO Training Reward (Go2 headless)")
# plt.grid(True)
# plt.legend()
# os.makedirs("logs", exist_ok=True)
# plt.savefig("logs/reward_curve.png")
# plt.show()

# print("Training finished!")


# # rl_go2/train_ppo.py
# import gymnasium as gym
# import numpy as np
# from stable_baselines3 import PPO
# from stable_baselines3.common.vec_env import DummyVecEnv
# from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
# from go2_env import Go2Env
# import os

# # --- Create environment ---
# def make_env():
#     return Go2Env()

# env = DummyVecEnv([make_env])  # SB3 expects a vectorized environment

# # --- Directories for logs and models ---
# log_dir = "./logs/"
# os.makedirs(log_dir, exist_ok=True)
# models_dir = "./models/"
# os.makedirs(models_dir, exist_ok=True)

# # --- Callbacks ---
# checkpoint_callback = CheckpointCallback(save_freq=5000, save_path=models_dir,
#                                          name_prefix="ppo_go2")
# eval_env = DummyVecEnv([make_env])
# eval_callback = EvalCallback(eval_env, best_model_save_path=models_dir,
#                              log_path=log_dir, eval_freq=5000,
#                              deterministic=True, render=False)

# # --- Create PPO model ---
# model = PPO(
#     "MlpPolicy",
#     env,
#     verbose=1,
#     learning_rate=3e-4,
#     n_steps=2048,
#     batch_size=64,
#     n_epochs=10,
#     gamma=0.99,
#     gae_lambda=0.95,
#     clip_range=0.2,
#     ent_coef=0.0,
#     tensorboard_log=log_dir,
# )

# # --- Train the model ---
# model.learn(
#     total_timesteps=50000,  # start small
#     callback=[checkpoint_callback, eval_callback]
# )

# # --- Save the final model ---
# model.save(os.path.join(models_dir, "ppo_go2_final"))

# print("Training finished!")
# rl_go2/train_ppo.py
# import gymnasium as gym
# import numpy as np
# from stable_baselines3 import PPO
# from stable_baselines3.common.vec_env import DummyVecEnv
# from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
# from go2_env import Go2Env
# import os

# # --- Create environment ---
# def make_env():
#     return Go2Env()

# env = DummyVecEnv([make_env])  # SB3 expects a vectorized environment

# # --- Directories for logs and models ---
# log_dir = "./logs/"
# os.makedirs(log_dir, exist_ok=True)
# models_dir = "./models/"
# os.makedirs(models_dir, exist_ok=True)

# # --- Callbacks ---
# checkpoint_callback = CheckpointCallback(save_freq=5000, save_path=models_dir,
#                                          name_prefix="ppo_go2")
# eval_env = DummyVecEnv([make_env])
# eval_callback = EvalCallback(eval_env, best_model_save_path=models_dir,
#                              log_path=log_dir, eval_freq=5000,
#                              deterministic=True, render=False)

# # --- Create PPO model ---
# model = PPO(
#     "MlpPolicy",
#     env,
#     verbose=1,
#     learning_rate=3e-4,
#     n_steps=2048,
#     batch_size=64,
#     n_epochs=10,
#     gamma=0.99,
#     gae_lambda=0.95,
#     clip_range=0.2,
#     ent_coef=0.0,
#     tensorboard_log=log_dir,
# )

# # --- Train the model ---
# model.learn(
#     total_timesteps=50000,  # start small
#     callback=[checkpoint_callback, eval_callback]
# )

# # --- Save the final model ---
# model.save(os.path.join(models_dir, "ppo_go2_final"))

# print("Training finished!")
