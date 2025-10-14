# COde to test the environment with no viewer
# test_env.py
from envs.go2_env import Go2Env
import numpy as np

env = Go2Env()
obs, _ = env.reset()

for i in range(1000):
    action = np.random.uniform(-1, 1, env.action_space.shape)
    obs, reward, done, trunc, info = env.step(action)
    if done or trunc:
        obs, _ = env.reset()

env.close()
print("Headless simulation finished OK.")



# Code to test the environment with a viewer
#  from envs.go2_env import Go2Env
# import numpy as np

# def main():
#     env = Go2Env(render_mode="human")
#     obs, _ = env.reset()

#     for i in range(1000):
#         action = np.random.uniform(-1, 1, env.action_space.shape)
#         obs, reward, done, trunc, info = env.step(action)
#         env.render()
#         if done or trunc:
#             obs, _ = env.reset()

#     env.close()

# if __name__ == "__main__":
#     main()