import pinocchio as pin
import numpy as np
from inverse_kinematics import inverse_kinematics

# -----------------------------
# Load URDF model
# -----------------------------
urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"

# Use free-flyer for floating base
model = pin.buildModelFromUrdf(urdf_path, pin.JointModelFreeFlyer())
data = model.createData()

# Initial configuration
q0 = pin.neutral(model)

# -----------------------------
# Define leg and target pose
# -----------------------------
frame_name = "FR_foot"  # front right foot
target_position = np.array([0.23, -0.10, -0.03])  # relative to world/base
target_pose = pin.SE3(np.eye(3), target_position)

# -----------------------------
# Run IK
# -----------------------------
q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_pose,
                                    eps=1e-4, max_iter=1000, dt=0.1, damping=1e-12)

if success:
    print(f"IK converged for {frame_name}!")
else:
    print(f"IK did NOT converge for {frame_name}.")

# -----------------------------
# Show resulting pose
# -----------------------------
pin.forwardKinematics(model, data, q_sol)
pin.updateFramePlacements(model, data)
foot_pose = data.oMf[model.getFrameId(frame_name)]

print("Target foot position:", target_pose.translation.T)
print("Resulting foot position:", foot_pose.translation.T)
print("Final error:", (foot_pose.translation - target_pose.translation).T)




# # import pinocchio as pin
# # import numpy as np
# # from inverse_kinematics import inverse_kinematics

# # import pinocchio as pin
# # import numpy as np
# # from inverse_kinematics import inverse_kinematics

# # # Load model
# # urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# # model = pin.buildModelFromUrdf(urdf_path)
# # data = model.createData()
# # q0 = pin.neutral(model)

# # # Choose leg frame and target relative to base
# # frame_name = "FR_foot"
# # target_rel = np.array([0.25, -0.1, -0.03])

# # # Compute base pose in world
# # pin.forwardKinematics(model, data, q0)
# # pin.updateFramePlacements(model, data)
# # base_pose = data.oMf[model.getFrameId("root_link")]
# # target_world = base_pose * pin.SE3(np.eye(3), target_rel)

# # # Run IK
# # q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_world)

# # print(f"IK {'converged' if success else 'failed'} for {frame_name}")
# # pin.forwardKinematics(model, data, q_sol)
# # pin.updateFramePlacements(model, data)
# # foot_pose = data.oMf[model.getFrameId(frame_name)]
# # print("Resulting foot position:", foot_pose.translation.T)

# import pinocchio as pin
# import numpy as np
# from inverse_kinematics import inverse_kinematics

# # -----------------------------
# # Load URDF model
# # -----------------------------
# urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# model = pin.buildModelFromUrdf(urdf_path)
# data = model.createData()

# # Neutral configuration
# q0 = pin.neutral(model)

# # -----------------------------
# # Define leg and base-relative target
# # -----------------------------
# frame_name = "FR_foot"  # change to any foot frame
# target_rel = np.array([0.23, -0.10, -0.03]) # X, Y, Z relative to base (forward, lateral, downward)

# # -----------------------------
# # Compute base pose in world
# # -----------------------------
# pin.forwardKinematics(model, data, q0)
# pin.updateFramePlacements(model, data)

# # Access the floating base pose using the first joint
# base_pose = data.oMi[0]  # floating base joint

# # Convert base-relative target to world coordinates
# target_world = base_pose * pin.SE3(np.eye(3), target_rel)

# # -----------------------------
# # Run inverse kinematics
# # -----------------------------
# q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_world, eps=1e-3, max_iter=2000, dt=0.01)

# if success:
#     print(f"IK converged for {frame_name}!")
# else:
#     print(f"IK did NOT converge for {frame_name}.")

# # -----------------------------
# # Print resulting foot position
# # -----------------------------
# pin.forwardKinematics(model, data, q_sol)
# pin.updateFramePlacements(model, data)
# foot_pose = data.oMf[model.getFrameId(frame_name)]
# print("Resulting foot position (world frame):", foot_pose.translation.T)

# import pinocchio as pin
# # import numpy as np
# # from inverse_kinematics import inverse_kinematics

# # # Load model
# # urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# # model = pin.buildModelFromUrdf(urdf_path)
# # data = model.createData()
# # q0 = pin.neutral(model)

# # # Choose leg frame and target relative to base
# # frame_name = "FR_foot"
# # target_rel = np.array([0.25, -0.1, -0.03])

# # # Compute base pose in world
# # pin.forwardKinematics(model, data, q0)
# # pin.updateFramePlacements(model, data)
# # base_pose = data.oMf[model.getFrameId("root_link")]
# # target_world = base_pose * pin.SE3(np.eye(3), target_rel)

# # # Run IK
# # q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_world)

# # print(f"IK {'converged' if success else 'failed'} for {frame_name}")
# # pin.forwardKinematics(model, data, q_sol)
# # pin.updateFramePlacements(model, data)
# # foot_pose = data.oMf[model.getFrameId(frame_name)]
# # print("Resulting foot position:", foot_pose.translation.T)

# import pinocchio as pin
# import numpy as np
# from inverse_kinematics import inverse_kinematics

# # -----------------------------
# # Load URDF model
# # -----------------------------
# urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# model = pin.buildModelFromUrdf(urdf_path)
# data = model.createData()

# # Neutral configuration
# q0 = pin.neutral(model)

# # -----------------------------
# # Define leg and base-relative target
# # -----------------------------
# frame_name = "FR_foot"  # change to any foot frame
# target_rel = np.array([0.23, -0.10, -0.03]) # X, Y, Z relative to base (forward, lateral, downward)

# # -----------------------------
# # Compute base pose in world
# # -----------------------------
# pin.forwardKinematics(model, data, q0)
# pin.updateFramePlacements(model, data)

# # Access the floating base pose using the first joint
# base_pose = data.oMi[0]  # floating base joint

# # Convert base-relative target to world coordinates
# target_world = base_pose * pin.SE3(np.eye(3), target_rel)

# # -----------------------------
# # Run inverse kinematics
# # -----------------------------
# q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_world, eps=1e-3, max_iter=2000, dt=0.01)

# if success:
#     print(f"IK converged for {frame_name}!")
# else:
#     print(f"IK did NOT converge for {frame_name}.")

# # -----------------------------
# # Print resulting foot position
# # -----------------------------
# pin.forwardKinematics(model, data, q_sol)
# pin.updateFramePlacements(model, data)
# foot_pose = data.oMf[model.getFrameId(frame_name)]
# print("Resulting foot position (world frame):", foot_pose.translation.T)

# # Load model
# # urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# # model = pin.buildModelFromUrdf(urdf_path)
# # data = model.createData()
# # q0 = pin.neutral(model)

# # # Choose leg frame and target relative to base
# # frame_name = "FR_foot"
# # target_rel = np.array([0.25, -0.1, -0.03])

# # # Compute base pose in world
# # pin.forwardKinematics(model, data, q0)
# # pin.updateFramePlacements(model, data)
# # base_pose = data.oMf[model.getFrameId("root_link")]
# # target_world = base_pose * pin.SE3(np.eye(3), target_rel)

# # # Run IK
# # q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_world)

# # print(f"IK {'converged' if success else 'failed'} for {frame_name}")
# # pin.forwardKinematics(model, data, q_sol)
# # pin.updateFramePlacements(model, data)
# # foot_pose = data.oMf[model.getFrameId(frame_name)]
# # print("Resulting foot position:", foot_pose.translation.T)

# import pinocchio as pin
# import numpy as np
# from inverse_kinematics import inverse_kinematics

# # -----------------------------
# # Load URDF model
# # -----------------------------
# urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
# model = pin.buildModelFromUrdf(urdf_path)
# data = model.createData()

# # Neutral configuration
# q0 = pin.neutral(model)

# # -----------------------------
# # Define leg and base-relative target
# # -----------------------------
# frame_name = "FR_foot"  # change to any foot frame
# target_rel = np.array([0.23, -0.10, -0.03]) # X, Y, Z relative to base (forward, lateral, downward)

# # -----------------------------
# # Compute base pose in world
# # -----------------------------
# pin.forwardKinematics(model, data, q0)
# pin.updateFramePlacements(model, data)

# # Access the floating base pose using the first joint
# base_pose = data.oMi[0]  # floating base joint

# # Convert base-relative target to world coordinates
# target_world = base_pose * pin.SE3(np.eye(3), target_rel)

# # -----------------------------
# # Run inverse kinematics
# # -----------------------------
# q_sol, success = inverse_kinematics(model, data, q0, frame_name, target_world, eps=1e-3, max_iter=2000, dt=0.01)

# if success:
#     print(f"IK converged for {frame_name}!")
# else:
#     print(f"IK did NOT converge for {frame_name}.")

# # -----------------------------
# # Print resulting foot position
# # -----------------------------
# pin.forwardKinematics(model, data, q_sol)
# pin.updateFramePlacements(model, data)
# foot_pose = data.oMf[model.getFrameId(frame_name)]
# print("Resulting foot position (world frame):", foot_pose.translation.T)

