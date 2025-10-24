import mujoco_py
print("mujoco-py version:", mujoco_py.__version__)

from mujoco_py import load_model_from_path, MjSim
import os

# Point to your hopper.xml (from gym or mujoco models)
model_path = os.path.join(os.environ['MUJOCO_PY_MUJOCO_PATH'], 'model/hopper.xml')
model = load_model_from_path(model_path)
sim = MjSim(model)
print("MuJoCo 3.2.7 simulation loaded successfully!")

