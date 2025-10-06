# visualize_IK_baseframe.py
import time
import threading
import numpy as np
import mujoco
import mujoco.viewer
import pinocchio as pin
from inverse_kinematics_leg import inverse_kinematics_leg

# -----------------------------
# Paths
# -----------------------------
URDF_PATH = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
MJ_SCENE_XML = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"

# -----------------------------
# Load MuJoCo scene
# -----------------------------
mj_model = mujoco.MjModel.from_xml_path(MJ_SCENE_XML)
mj_data = mujoco.MjData(mj_model)

# -----------------------------
# Define standing pose
# -----------------------------
q_stand = np.zeros(mj_model.nq)
q_stand[0:3] = [0, 0, 0.35]        # base x,y,z
q_stand[3:7] = [1, 0, 0, 0]        # base quaternion
# Leg joint angles (replace with realistic standing pose)
q_stand[7:] = np.array([
    0.0, 0.8, -1.6,  # FR leg
    0.0, 0.8, -1.6,  # FL leg
    0.0, 0.8, -1.6,  # RR leg
    0.0, 0.8, -1.6   # RL leg
])
mj_data.qpos[:] = q_stand

# -----------------------------
# Load Pinocchio model
# -----------------------------
pin_model = pin.buildModelFromUrdf(URDF_PATH, pin.JointModelFreeFlyer())
pin_data = pin_model.createData()

# -----------------------------
# Foot target and leg indices
# -----------------------------
frame_name = "FR_foot"
foot_lift = -0.03
target_rel = np.array([0.23, -0.10, foot_lift]) # relative to base

# Compute base pose in world
pin.forwardKinematics(pin_model, pin_data, q_stand)
pin.updateFramePlacements(pin_model, pin_data)
base_pose = pin_data.oMi[0]
target_pos = base_pose * pin.SE3(np.eye(3), target_rel)

# FR leg joint indices in q_stand
fr_leg_idx = slice(7, 10)  # replace with correct indices if needed

# -----------------------------
# Run IK for single leg
# -----------------------------
q_sol, success = inverse_kinematics_leg(
    model=pin_model,
    data=pin_data,
    q_init=q_stand,
    frame_name=frame_name,
    target_pos=target_pos.translation,
    leg_joint_indices=fr_leg_idx
)
print(f"IK converged for {frame_name}: {success}")

# -----------------------------
# Setup MuJoCo viewer
# -----------------------------
viewer = mujoco.viewer.launch_passive(mj_model, mj_data)
locker = threading.Lock()

# -----------------------------
# Animate leg lift
# -----------------------------
def animate_IK():
    steps = 100
    for i in range(steps):
        alpha = (i + 1)/steps
        q_interp = q_stand.copy()
        # interpolate only FR leg joints
        q_interp[fr_leg_idx] = (1-alpha)*q_stand[fr_leg_idx] + alpha*q_sol[fr_leg_idx]
        locker.acquire()
        mj_data.qpos[:] = q_interp
        mujoco.mj_step(mj_model, mj_data)
        locker.release()
        time.sleep(mj_model.opt.timestep)

# -----------------------------
# Viewer thread
# -----------------------------
def viewer_thread():
    while viewer.is_running():
        locker.acquire()
        viewer.sync()
        locker.release()
        time.sleep(0.01)

# -----------------------------
# Run threads
# -----------------------------
t1 = threading.Thread(target=viewer_thread)
t2 = threading.Thread(target=animate_IK)

t1.start()
t2.start()
t1.join()
t2.join()


# import time
# import threading
# import numpy as np
# import mujoco
# import mujoco.viewer
# import pinocchio as pin
# from inverse_kinematics_leg import inverse_kinematics_leg

# # -----------------------------
# # Paths
# # -----------------------------
# URDF_PATH = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# MJ_SCENE_XML = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"

# # -----------------------------
# # Load MuJoCo scene
# # -----------------------------
# mj_model = mujoco.MjModel.from_xml_path(MJ_SCENE_XML)
# mj_data = mujoco.MjData(mj_model)

# # -----------------------------
# # Standing base pose
# # -----------------------------
# q_stand = np.zeros(mj_model.nq)
# q_stand[0:3] = [0, 0, 0.35]        # base x,y,z
# q_stand[3:7] = [1, 0, 0, 0]        # base quaternion
# # Leg joint angles (realistic standing pose)
# q_stand[7:] = np.array([
#     0.0, 0.8, -1.6,  # FR leg
#     0.0, 0.8, -1.6,  # FL leg
#     0.0, 0.8, -1.6,  # RR leg
#     0.0, 0.8, -1.6   # RL leg
# ])
# mj_data.qpos[:] = q_stand

# # -----------------------------
# # Pinocchio model
# # -----------------------------
# pin_model = pin.buildModelFromUrdf(URDF_PATH, pin.JointModelFreeFlyer())
# pin_data = pin_model.createData()

# # -----------------------------
# # Lock base in IK
# # -----------------------------
# q0 = q_stand.copy()  # initial configuration
# q0_base = q0[:7].copy()  # floating base: x,y,z + quaternion
# q0_legs = q0[7:].copy()  # only leg joints

# # -----------------------------
# # Define foot target (relative to base)
# # -----------------------------
# frame_name = "FR_foot"
# foot_lift = 0.08  # lift foot 8 cm
# target_rel = np.array([0.23, -0.10, foot_lift])

# # Compute base pose in world
# pin.forwardKinematics(pin_model, pin_data, q0)
# pin.updateFramePlacements(pin_model, pin_data)
# base_pose = pin_data.oMi[0]  # floating base
# target_world = base_pose * pin.SE3(np.eye(3), target_rel)

# # -----------------------------
# # Run IK on leg joints only
# # -----------------------------
# # Here, we freeze the base by passing q0_base as fixed and only optimizing q0_legs
# q_sol_legs, success = inverse_kinematics_leg(
#     pin_model, pin_data,
#     q0,  # full configuration
#     frame_name,
#     target_world,
#     eps=1e-4, max_iter=1000, dt=0.1, damping=1e-12
# )


# # Merge base + leg solution
# q_sol = q0.copy()
# q_sol[7:] = q_sol_legs[7:]

# print(f"IK {'converged' if success else 'did NOT converge'} for {frame_name}")

# # -----------------------------
# # Viewer setup
# # -----------------------------
# viewer = mujoco.viewer.launch_passive(mj_model, mj_data)
# locker = threading.Lock()

# # -----------------------------
# # Animate foot lift
# # -----------------------------
# def animate_IK():
#     steps = 100
#     for i in range(steps):
#         alpha = (i+1)/steps
#         q_interp = q_stand * (1 - alpha) + q_sol * alpha
#         locker.acquire()
#         mj_data.qpos[:] = q_interp
#         mujoco.mj_step(mj_model, mj_data)
#         locker.release()
#         time.sleep(mj_model.opt.timestep)

# # -----------------------------
# # Viewer thread
# # -----------------------------
# def viewer_thread():
#     while viewer.is_running():
#         locker.acquire()
#         viewer.sync()
#         locker.release()
#         time.sleep(0.01)

# # -----------------------------
# # Run threads
# # -----------------------------
# t1 = threading.Thread(target=viewer_thread)
# t2 = threading.Thread(target=animate_IK)
# t1.start()
# t2.start()
# t1.join()
# t2.join()



# # import time
# # import threading
# # import numpy as np
# # import mujoco
# # import mujoco.viewer
# # import pinocchio as pin
# # from inverse_kinematics import inverse_kinematics  # your IK function

# # # -----------------------------
# # # Paths
# # # -----------------------------
# # URDF_PATH = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# # MJ_SCENE_XML = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"

# # # -----------------------------
# # # Load MuJoCo scene
# # # -----------------------------
# # mj_model = mujoco.MjModel.from_xml_path(MJ_SCENE_XML)
# # mj_data = mujoco.MjData(mj_model)

# # # -----------------------------
# # # Standing base pose
# # # -----------------------------
# # q_stand = np.zeros(mj_model.nq)
# # q_stand[0:3] = [0, 0, 0.35]        # base x,y,z
# # q_stand[3:7] = [1, 0, 0, 0]        # base quaternion
# # # Leg joint angles (replace with realistic standing pose)
# # q_stand[7:] = np.array([
# #     0.0, 0.8, -1.6,  # FR leg
# #     0.0, 0.8, -1.6,  # FL leg
# #     0.0, 0.8, -1.6,  # RR leg
# #     0.0, 0.8, -1.6   # RL leg
# # ])
# # mj_data.qpos[:] = q_stand

# # # -----------------------------
# # # Pinocchio model
# # # -----------------------------
# # pin_model = pin.buildModelFromUrdf(URDF_PATH, pin.JointModelFreeFlyer())
# # pin_data = pin_model.createData()

# # # -----------------------------
# # # Define base-relative foot target
# # # -----------------------------
# # frame_name = "FR_foot"
# # foot_lift = -0.28  # lift foot by 8cm
# # target_rel = np.array([0.23, -0.10, foot_lift])  # relative to base

# # # Compute base pose in world (floating base)
# # pin.forwardKinematics(pin_model, pin_data, q_stand)
# # pin.updateFramePlacements(pin_model, pin_data)
# # base_pose = pin_data.oMi[0]  # floating base

# # # Convert base-relative target to world coordinates for Pinocchio IK
# # target_pose = base_pose * pin.SE3(np.eye(3), target_rel)

# # # -----------------------------
# # # Run IK
# # # -----------------------------
# # q_sol, success = inverse_kinematics(
# #     pin_model, pin_data, q_stand, frame_name, target_pose,
# #     eps=1e-4, max_iter=1000, dt=0.1, damping=1e-12
# # )
# # print(f"IK {'converged' if success else 'did NOT converge'} for {frame_name}")

# # # -----------------------------
# # # Viewer setup
# # # -----------------------------
# # viewer = mujoco.viewer.launch_passive(mj_model, mj_data)
# # locker = threading.Lock()

# # # -----------------------------
# # # Animate foot lift
# # # -----------------------------
# # def animate_IK():
# #     steps = 100
# #     for i in range(steps):
# #         alpha = (i+1)/steps
# #         q_interp = q_stand * (1 - alpha) + q_sol * alpha
# #         locker.acquire()
# #         mj_data.qpos[:] = q_interp
# #         mujoco.mj_step(mj_model, mj_data)
# #         locker.release()
# #         time.sleep(mj_model.opt.timestep)

# # # -----------------------------
# # # Viewer thread
# # # -----------------------------
# # def viewer_thread():
# #     while viewer.is_running():
# #         locker.acquire()
# #         viewer.sync()
# #         locker.release()
# #         time.sleep(0.01)

# # # -----------------------------
# # # Run threads
# # # -----------------------------
# # t1 = threading.Thread(target=viewer_thread)
# # t2 = threading.Thread(target=animate_IK)
# # t1.start()
# # t2.start()
# # t1.join()
# # t2.join()
