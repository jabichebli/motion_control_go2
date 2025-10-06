import time
import threading
import numpy as np
import mujoco
import mujoco.viewer
import pinocchio as pin
from inverse_kinematics import inverse_kinematics  # your IK function

# -----------------------------
# Paths
# -----------------------------
URDF_PATH = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
MJ_SCENE_XML = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"  # nice terrain/scene

# -----------------------------
# Load MuJoCo scene
# -----------------------------
mj_model = mujoco.MjModel.from_xml_path(MJ_SCENE_XML)
mj_data = mujoco.MjData(mj_model)

# -----------------------------
# Define a standing pose for the robot
# -----------------------------
q_stand = np.zeros(mj_model.nq)
# Floating base position and orientation
q_stand[0:3] = [0, 0, 0.35]        # x, y, z of base
q_stand[3:7] = [1, 0, 0, 0]        # quaternion w,x,y,z

# Leg joints (replace these with correct angles for Go2)
q_stand[7:] = np.array([
    0.0, 0.8, -1.6,  # FR leg
    0.0, 0.8, -1.6,  # FL leg
    0.0, 0.8, -1.6,  # RR leg
    0.0, 0.8, -1.6   # RL leg
])
mj_data.qpos[:] = q_stand

# -----------------------------
# Load Pinocchio model for IK
# -----------------------------
pin_model = pin.buildModelFromUrdf(URDF_PATH, pin.JointModelFreeFlyer())
pin_data = pin_model.createData()

# -----------------------------
# Define foot target (world coordinates)
# -----------------------------
frame_name = "FR_foot"
target_pos = np.array([0.23, -0.10, -0.03])
pin.forwardKinematics(pin_model, pin_data, q_stand)
pin.updateFramePlacements(pin_model, pin_data)
base_pose = pin_data.oMi[0]  # floating base
target_pose = base_pose * pin.SE3(np.eye(3), target_pos)

# -----------------------------
# Compute IK
# -----------------------------
q_sol, success = inverse_kinematics(
    pin_model, pin_data, q_stand, frame_name, target_pose,
    eps=1e-4, max_iter=1000, dt=0.1, damping=1e-12
)
if success:
    print(f"IK converged for {frame_name}")
else:
    print(f"IK did NOT converge for {frame_name}")

# -----------------------------
# Setup viewer
# -----------------------------
viewer = mujoco.viewer.launch_passive(mj_model, mj_data)

# Lock for safe threading
locker = threading.Lock()

# -----------------------------
# Simulation / Animation Thread
# -----------------------------
def animate_IK():
    # simple interpolation from stand to IK solution
    steps = 100
    for i in range(steps):
        alpha = (i+1)/steps
        q_interp = q_stand * (1 - alpha) + q_sol * alpha
        locker.acquire()
        mj_data.qpos[:] = q_interp
        mujoco.mj_step(mj_model, mj_data)
        locker.release()
        time.sleep(mj_model.opt.timestep)

# -----------------------------
# Viewer Thread
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



# import pinocchio as pin
# import numpy as np
# import mujoco
# import mujoco.viewer

# from inverse_kinematics import inverse_kinematics  # your IK function

# # -----------------------------
# # Paths
# # -----------------------------
# urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# mjxml_scene = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"

# # -----------------------------
# # Load Pinocchio model
# # -----------------------------
# model = pin.buildModelFromUrdf(urdf_path, pin.JointModelFreeFlyer())
# data = model.createData()
# q0 = pin.neutral(model)

# # -----------------------------
# # Define leg and target (lift foot)
# # -----------------------------
# frame_name = "FR_foot"           # front-right foot
# target_position = np.array([0.23, -0.10, 0.08])  # lift foot up

# # Convert base-relative target to world coordinates
# pin.forwardKinematics(model, data, q0)
# pin.updateFramePlacements(model, data)
# base_pose = data.oMi[0]  # floating base
# target_world = base_pose * pin.SE3(np.eye(3), target_position)

# # -----------------------------
# # Run IK
# # -----------------------------
# q_sol, success = inverse_kinematics(
#     model, data, q0, frame_name, target_world,
#     eps=1e-4, max_iter=1000, dt=0.1, damping=1e-12
# )

# if success:
#     print(f"IK converged for {frame_name}!")
# else:
#     print(f"IK did NOT converge for {frame_name}.")

# pin.forwardKinematics(model, data, q_sol)
# pin.updateFramePlacements(model, data)
# foot_pose = data.oMf[model.getFrameId(frame_name)]
# print("Target foot position:", target_position)
# print("Resulting foot position:", foot_pose.translation.T)

# # -----------------------------
# # Load MuJoCo scene and robot
# # -----------------------------
# mj_model = mujoco.MjModel.from_xml_path(mjxml_scene)
# mj_data = mujoco.MjData(mj_model)

# # -----------------------------
# # Set base to standing pose
# # -----------------------------
# mj_data.qpos[:3] = [0, 0, 0.35]  # base height
# mj_data.qpos[3:7] = [1, 0, 0, 0] # upright quaternion

# # -----------------------------
# # Copy joint angles from IK (skip free-flyer)
# # -----------------------------
# mj_data.qpos[7:7+len(q_sol)-7] = q_sol[7:]
# mujoco.mj_forward(mj_model, mj_data)

# # -----------------------------
# # Launch viewer
# # -----------------------------
# with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
#     print("MuJoCo viewer running. Press Q to quit.")
#     while viewer.is_running():
#         mujoco.mj_step(mj_model, mj_data)
#         viewer.sync()


# # import pinocchio as pin
# # import numpy as np
# # from inverse_kinematics import inverse_kinematics
# # import mujoco
# # import mujoco.viewer
# # import time

# # # -----------------------------
# # # 1. Pinocchio IK
# # # -----------------------------
# # urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# # model = pin.buildModelFromUrdf(urdf_path, pin.JointModelFreeFlyer())
# # data = model.createData()
# # q0 = pin.neutral(model)

# # frame_name = "FR_foot"
# # target_position = np.array([0.23, -0.10, -0.03])
# # target_pose = pin.SE3(np.eye(3), target_position)

# # q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_pose,
# #                                     eps=1e-4, max_iter=1000, dt=0.1, damping=1e-12)

# # pin.forwardKinematics(model, data, q_sol)
# # pin.updateFramePlacements(model, data)
# # foot_pose = data.oMf[model.getFrameId(frame_name)]

# # print(f"IK {'converged' if success else 'did not converge'} for {frame_name}")
# # print("Target:", target_position)
# # print("Result:", foot_pose.translation.T)
# # print("Final error:", (foot_pose.translation - target_pose.translation).T)

# # # -----------------------------
# # # 2. Load full MuJoCo scene
# # # -----------------------------
# # SCENE_XML = "/home/jason/projects/motion_control_go2/src/unitree_mujoco/unitree_robots/go2/scene.xml"
# # mj_model = mujoco.MjModel.from_xml_path(SCENE_XML)
# # mj_data = mujoco.MjData(mj_model)

# # # -----------------------------
# # # 3. Apply IK solution to robot in scene
# # # -----------------------------
# # # This assumes robot is the first body/joint in the scene
# # mj_data.qpos[:len(q_sol)] = q_sol
# # mujoco.mj_forward(mj_model, mj_data)

# # # -----------------------------
# # # 4. Launch viewer
# # # -----------------------------
# # with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
# #     print("MuJoCo viewer running... Press Q to quit.")
# #     while viewer.is_running():
# #         mujoco.mj_step(mj_model, mj_data)
# #         viewer.sync()
# #         time.sleep(0.01)
