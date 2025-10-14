# envs/go2_env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import mujoco
import os
import logging

log = logging.getLogger(__name__)

class Go2Env(gym.Env):
    metadata = {"render_modes": ["none"], "render_fps": 60}

    def __init__(self):
        super().__init__()
        xml_path = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"XML not found: {xml_path}")

        # Load model/data
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        # Action space
        n_act = int(self.model.nu)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(n_act,), dtype=np.float32)

        # Observation space: qpos + qvel
        obs_dim = int(self.model.nq + self.model.nv)
        high = np.inf * np.ones(obs_dim, dtype=np.float32)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

        # Parameters
        self.torque_scale = 0.4
        self.max_steps = 1000
        self._step_count = 0
        self._prev_base_x = 0.0  # for computing forward progress

        mujoco.mj_resetData(self.model, self.data)
        self._set_initial_pose_safe()

    def _set_initial_pose_safe(self):
        qpos = np.array(self.data.qpos).copy()
        if len(qpos) >= 3:
            qpos[2] = max(qpos[2], 0.18)
        self.data.qpos[:] = qpos
        mujoco.mj_forward(self.model, self.data)

    def step(self, action):
        action = np.clip(action, self.action_space.low, self.action_space.high)
        self.data.ctrl[:] = (action * self.torque_scale).astype(np.float64)

        mujoco.mj_step(self.model, self.data)

        # --- Observations ---
        obs = np.concatenate([
            np.array(self.data.qpos).ravel(),
            np.array(self.data.qvel).ravel()
        ]).astype(np.float32)

        # --- Rewards ---
        base_x = float(self.data.qpos[0])
        base_z = float(self.data.qpos[2])
        vx = float(self.data.qvel[0])  # forward velocity

        # Components of reward
        forward_reward = 2.0 * vx              # move forward along +x
        height_reward = 2.0 * np.tanh(base_z - 0.18)  # stay near standing height
        smoothness_penalty = -0.05 * np.linalg.norm(self.data.qvel)
        energy_penalty = -0.02 * np.linalg.norm(self.data.ctrl)

        reward = forward_reward + height_reward + smoothness_penalty + energy_penalty

        # --- Termination ---
        self._step_count += 1
        terminated = base_z < 0.08
        truncated = self._step_count >= self.max_steps

        self._prev_base_x = base_x

        return obs, float(reward), terminated, truncated, {}

    def reset(self, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)
        mujoco.mj_resetData(self.model, self.data)
        self._set_initial_pose_safe()
        self._step_count = 0
        self._prev_base_x = 0.0
        obs = np.concatenate([
            np.array(self.data.qpos).ravel(),
            np.array(self.data.qvel).ravel()
        ]).astype(np.float32)
        return obs, {}

    def render(self):
        return  # headless

    def close(self):
        return



# # Code with no viewer 

# # envs/go2_env.py
# import gymnasium as gym
# from gymnasium import spaces
# import numpy as np
# import mujoco
# import os
# import logging

# log = logging.getLogger(__name__)

# class Go2Env(gym.Env):
#     metadata = {"render_modes": ["none"], "render_fps": 60}

#     def __init__(self):
#         super().__init__()
#         xml_path = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"
#         if not os.path.exists(xml_path):
#             raise FileNotFoundError(f"XML not found: {xml_path}")

#         # Load model/data
#         self.model = mujoco.MjModel.from_xml_path(xml_path)
#         self.data = mujoco.MjData(self.model)
#         # self.render_mode = render_mode   # <-- must be here


#         # Action space: continuous torque for all actuators
#         n_act = int(self.model.nu)
#         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(n_act,), dtype=np.float32)

#         # Observation: qpos + qvel flattened
#         n_qpos = int(self.model.nq)
#         n_qvel = int(self.model.nv)
#         obs_dim = n_qpos + n_qvel
#         high = np.inf * np.ones(obs_dim, dtype=np.float32)
#         self.observation_space = spaces.Box(-high, high, dtype=np.float32)

#         # Safety params
#         self.torque_scale = 0.2  # scale applied to actions
#         self.max_steps = 1000
#         self._step_count = 0

#         # Initial reset
#         mujoco.mj_resetData(self.model, self.data)
#         self._set_initial_pose_safe()

#     def _set_initial_pose_safe(self):
#         try:
#             qpos = np.array(self.data.qpos).copy()
#             if len(qpos) >= 3 and qpos[2] < 0.05:  # lift root z if too low
#                 qpos[2] = 0.18
#             self.data.qpos[:] = qpos
#             mujoco.mj_forward(self.model, self.data)
#         except Exception as e:
#             log.warning("Failed to set safe initial pose: %s", e)

#     def step(self, action):
#         action = np.asarray(action, dtype=np.float32).reshape(self.action_space.shape)
#         action = np.clip(action, self.action_space.low, self.action_space.high)
#         try:
#             self.data.ctrl[:] = (action * self.torque_scale).astype(np.float64)
#         except Exception:
#             n = min(len(self.data.ctrl), len(action))
#             self.data.ctrl[:n] = (action[:n] * self.torque_scale).astype(np.float64)

#         mujoco.mj_step(self.model, self.data)

#         obs = np.concatenate([np.array(self.data.qpos).ravel(), np.array(self.data.qvel).ravel()]).astype(np.float32)
#         base_z = float(self.data.qpos[2]) if self.model.nq >= 3 else 0.0
#         reward = -0.1 * np.linalg.norm(self.data.qvel) + 0.5 * np.tanh(base_z - 0.15)

#         self._step_count += 1
#         terminated = base_z < 0.05
#         truncated = self._step_count >= self.max_steps

#         return obs, float(reward), terminated, truncated, {}

#     def reset(self, seed=None, options=None):
#         if seed is not None:
#             np.random.seed(seed)
#         mujoco.mj_resetData(self.model, self.data)
#         self._set_initial_pose_safe()
#         self._step_count = 0
#         obs = np.concatenate([np.array(self.data.qpos).ravel(), np.array(self.data.qvel).ravel()]).astype(np.float32)
#         return obs, {}

#     def render(self):
#         # headless, do nothing
#         return

#     def close(self):
#         return



# Code with a viewer !!
#  # envs/go2_env.py
# import gymnasium as gym
# from gymnasium import spaces
# import numpy as np
# import mujoco
# import mujoco_viewer  # use legacy viewer
# import os
# import logging

# log = logging.getLogger(__name__)

# class Go2Env(gym.Env):
#     metadata = {"render_modes": ["human", "none"], "render_fps": 60}

#     def __init__(self, render_mode="none"):
#         super().__init__()
#         xml_path = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"
#         if not os.path.exists(xml_path):
#             raise FileNotFoundError(f"XML not found: {xml_path}")

#         # Load model/data
#         self.model = mujoco.MjModel.from_xml_path(xml_path)
#         self.data = mujoco.MjData(self.model)
#         self.render_mode = render_mode

#         # Action space: continuous torque for all actuators
#         n_act = int(self.model.nu)
#         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(n_act,), dtype=np.float32)

#         # Observation: qpos + qvel flattened
#         n_qpos = int(self.model.nq)
#         n_qvel = int(self.model.nv)
#         obs_dim = n_qpos + n_qvel
#         high = np.inf * np.ones(obs_dim, dtype=np.float32)
#         self.observation_space = spaces.Box(-high, high, dtype=np.float32)

#         # viewer handle (may be None if headless)
#         self.viewer = None

#         # Safety params
#         self.torque_scale = 0.2  # scale applied to actions
#         self.max_steps = 1000
#         self._step_count = 0

#         # Try initial reset to populate data
#         mujoco.mj_resetData(self.model, self.data)
#         self._set_initial_pose_safe()

#     def _set_initial_pose_safe(self):
#         try:
#             qpos = np.array(self.data.qpos).copy()
#             if len(qpos) >= 3 and qpos[2] < 0.05:  # lift root z if too low
#                 qpos[2] = 0.18
#             self.data.qpos[:] = qpos
#             mujoco.mj_forward(self.model, self.data)
#         except Exception as e:
#             log.warning("Failed to set safe initial pose: %s", e)
# envs/go2_env.py
# import gymnasium as gym
# from gymnasium import spaces
# import numpy as np
# import mujoco
# import mujoco_viewer  # use legacy viewer
# import os
# import logging

# log = logging.getLogger(__name__)

# class Go2Env(gym.Env):
#     metadata = {"render_modes": ["human", "none"], "render_fps": 60}

#     def __init__(self, render_mode="none"):
#         super().__init__()
#         xml_path = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"
#         if not os.path.exists(xml_path):
#             raise FileNotFoundError(f"XML not found: {xml_path}")

#         # Load model/data
#         self.model = mujoco.MjModel.from_xml_path(xml_path)
#         self.data = mujoco.MjData(self.model)
#         self.render_mode = render_mode

#         # Action space: continuous torque for all actuators
#         n_act = int(self.model.nu)
#         self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(n_act,), dtype=np.float32)

#         # Observation: qpos + qvel flattened
#         n_qpos = int(self.model.nq)
#         n_qvel = int(self.model.nv)
#         obs_dim = n_qpos + n_qvel
#         high = np.inf * np.ones(obs_dim, dtype=np.float32)
#         self.observation_space = spaces.Box(-high, high, dtype=np.float32)

#         # viewer handle (may be None if headless)
#         self.viewer = None

#         # Safety params
#         self.torque_scale = 0.2  # scale applied to actions
#         self.max_steps = 1000
#         self._step_count = 0

#         # Try initial reset to populate data
#         mujoco.mj_resetData(self.model, self.data)
#         self._set_initial_pose_safe()

#     def _set_initial_pose_safe(self):
#         try:
#             qpos = np.array(self.data.qpos).copy()
#             if len(qpos) >= 3 and qpos[2] < 0.05:  # lift root z if too low
#                 qpos[2] = 0.18
#             self.data.qpos[:] = qpos
#             mujoco.mj_forward(self.model, self.data)
#         except Exception as e:
#             log.warning("Failed to set safe initial pose: %s", e)


#     def step(self, action):
#         action = np.asarray(action, dtype=np.float32).reshape(self.action_space.shape)
#         action = np.clip(action, self.action_space.low, self.action_space.high)
#         try:
#             self.data.ctrl[:] = (action * self.torque_scale).astype(np.float64)
#         except Exception:
#             n = min(len(self.data.ctrl), len(action))
#             self.data.ctrl[:n] = (action[:n] * self.torque_scale).astype(np.float64)

#         mujoco.mj_step(self.model, self.data)

#         obs = np.concatenate([np.array(self.data.qpos).ravel(), np.array(self.data.qvel).ravel()]).astype(np.float32)
#         base_z = float(self.data.qpos[2]) if self.model.nq >= 3 else 0.0
#         reward = -0.1 * np.linalg.norm(self.data.qvel) + 0.5 * np.tanh(base_z - 0.15)

#         self._step_count += 1
#         terminated = base_z < 0.05
#         truncated = self._step_count >= self.max_steps

#         return obs, float(reward), terminated, truncated, {}

#     def reset(self, seed=None, options=None):
#         if seed is not None:
#             np.random.seed(seed)
#         mujoco.mj_resetData(self.model, self.data)
#         self._set_initial_pose_safe()
#         self._step_count = 0
#         obs = np.concatenate([np.array(self.data.qpos).ravel(), np.array(self.data.qvel).ravel()]).astype(np.float32)
#         return obs, {}

#     def render(self):
#         if self.render_mode != "human":
#             return

#         if self.viewer is None:
#             try:
#                 self.viewer = mujoco_viewer.MujocoViewer(self.model, self.data)
#             except Exception as e:
#                 log.exception("Failed launching mujoco_viewer (falling back to headless): %s", e)
#                 self.viewer = None
#                 return

#         try:
#             self.viewer.render()
#         except Exception as e:
#             log.exception("Viewer render error, closing viewer: %s", e)
#             try:
#                 self.viewer.close()
#             except Exception:
#                 pass
#             self.viewer = None

#     def close(self):
#         if self.viewer is not None:
#             try:
#                 self.viewer.close()
#             except Exception:
#                 pass
#             self.viewer = None
