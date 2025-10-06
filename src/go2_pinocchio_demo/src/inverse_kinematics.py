import pinocchio as pin
import numpy as np
from numpy.linalg import norm, solve

def inverse_kinematics(model, data, q_init, frame_name, target_pose,
                       eps=1e-4, max_iter=1000, dt=1e-1, damping=1e-12):
    """
    Closed-Loop Inverse Kinematics (CLIK) for a frame.

    Parameters
    ----------
    model : pinocchio.Model
        Robot model.
    data : pinocchio.Data
        Robot data.
    q_init : np.ndarray
        Initial joint configuration.
    frame_name : str
        Name of the frame to reach.
    target_pose : pinocchio.SE3
        Desired SE3 pose in world frame.
    eps : float
        Convergence threshold.
    max_iter : int
        Maximum number of iterations.
    dt : float
        Step size.
    damping : float
        Regularization for pseudo-inverse.

    Returns
    -------
    q : np.ndarray
        Joint configuration after IK.
    success : bool
        True if converged, False otherwise.
    """
    q = q_init.copy()
    frame_id = model.getFrameId(frame_name)

    for i in range(max_iter):
        # Forward kinematics
        pin.forwardKinematics(model, data, q)
        pin.updateFramePlacements(model, data)

        # Current -> desired error in local frame
        iMd = data.oMf[frame_id].actInv(target_pose)
        err = pin.log(iMd).vector

        if norm(err) < eps:
            return q, True

        # Frame Jacobian in LOCAL frame
        J = pin.computeFrameJacobian(model, data, q, frame_id, pin.LOCAL)
        J = -pin.Jlog6(iMd.inverse()) @ J

        # Damped pseudo-inverse update
        v = -J.T @ solve(J @ J.T + damping * np.eye(6), err)

        # Integrate configuration
        q = pin.integrate(model, q, v * dt)

        if not i % 50:
            print(f"Iter {i}, |err|={norm(err):.6f}")

    return q, False

# import pinocchio as pin
# import numpy as np
# from numpy.linalg import norm, solve

# def inverse_kinematics(model, data, q_init, frame_name, target_pose,
#                        eps=1e-4, max_iter=1000, dt=0.1, damping=1e-12):
#     """
#     Compute iterative inverse kinematics for a single frame.

#     Parameters
#     ----------
#     model : pinocchio.Model
#         Pinocchio model of the robot.
#     data : pinocchio.Data
#         Pinocchio data object.
#     q_init : np.ndarray
#         Initial joint configuration (size nv).
#     frame_name : str
#         Name of the frame to reach.
#     target_pose : pin.SE3
#         Desired SE3 pose in world frame.
#     eps : float, optional
#         Convergence threshold, by default 1e-4.
#     max_iter : int, optional
#         Maximum iterations, by default 1000.
#     dt : float, optional
#         Step size, by default 0.1.
#     damping : float, optional
#         Regularization for pseudo-inverse, by default 1e-12.

#     Returns
#     -------
#     q : np.ndarray
#         Joint configuration after IK.
#     success : bool
#         True if converged, False otherwise.
#     """

#     q = q_init.copy()
#     frame_id = model.getFrameId(frame_name)

#     for i in range(max_iter):
#         # Forward kinematics
#         pin.forwardKinematics(model, data, q)
#         pin.updateFramePlacements(model, data)

#         # Compute error in joint frame
#         iMf = data.oMf[frame_id].actInv(target_pose)
#         err = pin.log(iMf).vector

#         if norm(err) < eps:
#             return q, True

#         # Compute frame Jacobian in joint frame
#         J = pin.computeFrameJacobian(model, data, q, frame_id, pin.LOCAL)
#         J = -pin.Jlog6(iMf.inverse()) @ J

#         # Velocity update using damped pseudo-inverse
#         v = -J.T @ solve(J @ J.T + damping * np.eye(6), err)

#         # Integrate configuration
#         q = pin.integrate(model, q, v * dt)

#         if i % 50 == 0:
#             print(f"Iteration {i}: error norm = {norm(err):.6f}")

#     return q, False
