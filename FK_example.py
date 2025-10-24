import os
import time
import numpy as np
import mujoco
import mujoco.viewer
import pinocchio as pin
from pinocchio.utils import zero

# === PATH SETUP ===
URDF_PATH = URDF_PATH = os.path.expanduser("~/go2_ws/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf")

MJ_XML_PATH = os.path.expanduser("~/unitree_mujoco/unitree_robots/go2/scene.xml") # adjust if named differently
PKG_DIR = os.path.dirname(URDF_PATH)

assert os.path.exists(URDF_PATH), f"URDF not found at {URDF_PATH}"
assert os.path.exists(MJ_XML_PATH), f"MuJoCo XML not found at {MJ_XML_PATH}"

# === LOAD PINOCCHIO MODEL ===
model, _, _ = pin.buildModelsFromUrdf(URDF_PATH, PKG_DIR)
data = model.createData()

q0 = pin.neutral(model)
joint_names = list(model.names)
print("Loaded Pinocchio model with joints:", joint_names)

# Identify front-left leg joints (based on naming)
FL_indices = [i for i, n in enumerate(joint_names) if "FL" in n or "lf" in n.lower()]
print("Front-left leg joints:", FL_indices)

# Create modified configuration: lift front-left leg
q = q0.copy()
if len(FL_indices) >= 3:
    q[FL_indices[1]] += 0.3  # hip pitch
    q[FL_indices[2]] -= 0.4  # knee

# Compute FK
pin.forwardKinematics(model, data, q)
pin.updateFramePlacements(model, data)
FL_foot = [fid for fid, f in enumerate(model.frames) if "FL_foot" in f.name or "lf_foot" in f.name.lower()]
if FL_foot:
    pos = data.oMf[FL_foot[0]].translation
    print(f"Front-left foot position (world): {pos}")

# === LOAD MUJOCO MODEL ===
mj_model = mujoco.MjModel.from_xml_path(MJ_XML_PATH)
mj_data = mujoco.MjData(mj_model)

# === SYNC JOINT STATES ===
# Build a name map: MuJoCo joint name -> index
mj_joint_names = [mj_model.joint(i).name for i in range(mj_model.njnt)]
mj_name_to_id = {name: i for i, name in enumerate(mj_joint_names)}

print("MuJoCo joints:", mj_joint_names)
print("\n=== Joint name alignment ===")
for i, pname in enumerate(joint_names):
    for mj in mj_joint_names:
        if pname.split(':')[-1] == mj:
            jid = mj_name_to_id[mj]
            if jid < mj_model.nq and i < len(q):
                mj_data.qpos[jid] = q[i]


# Apply Pinocchio q to matching MuJoCo joints (if names match)
for i, name in enumerate(joint_names):
    if name in mj_name_to_id and i < len(q):
        jid = mj_name_to_id[name]
        mj_data.qpos[jid] = q[i]

# Forward the MuJoCo model to apply new qpos
mujoco.mj_forward(mj_model, mj_data)

# === VISUALISE ===
with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
    print("Viewer launched — showing Pinocchio FK pose.")
    for i in range(1000):
        viewer.sync()
        time.sleep(0.01)