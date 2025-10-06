
import pinocchio as pin
from os.path import join
import numpy as np

# Path to your GO2 URDF
urdf_path = "/home/jason/projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf"
model = pin.buildModelFromUrdf(urdf_path)
data = model.createData()

# Neutral configuration (all joints at "zero")
q = pin.neutral(model)

# Zero velocity
qd = np.zeros(model.nv)

# Inertia matrix (D)
D = pin.crba(model, data, q)       # Composite rigid body algorithm
D = (D + D.T) / 2.0                # Ensure symmetry

# Coriolis/Centrifugal (C)
C = pin.computeCoriolisMatrix(model, data, q, qd)

# Gravity (g)
g = pin.computeGeneralizedGravity(model, data, q)

# Actuation matrix (B)
B = np.zeros((model.nv, model.nv - 6))  # 6 floating base DOFs unactuated
B[6:, :] = np.eye(model.nv - 6)

print("Inertia D:\n", D)
print("Coriolis C:\n", C)
print("Gravity g:\n", g)
print("Actuation B:\n", B)