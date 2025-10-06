import pinocchio as pin
import numpy as np

urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"

model = pin.buildModelFromUrdf(urdf_path)
data = model.createData()

print(f"Model loaded: {model.nq} dofs, {model.njoints} joints")

# Neutral configuration (all joints at zero)
q = pin.neutral(model)

# Optional: zero joint velocities
qd = np.zeros(model.nv)

# Forward kinematics
pin.forwardKinematics(model, data, q, qd)
pin.updateFramePlacements(model, data)  # update frame poses

# Suppose the right-front foot frame is called "RF_FOOT"
frame_id = model.getFrameId("FR_foot")
foot_pose = data.oMf[frame_id]  # SE3 transform
print("RF foot position (XYZ):", foot_pose.translation.T)
print("RF foot rotation matrix:\n", foot_pose.rotation)

for i, frame in enumerate(model.frames):
    pose = data.oMf[i]
    print(f"Frame {frame.name} position: {pose.translation.T}")


