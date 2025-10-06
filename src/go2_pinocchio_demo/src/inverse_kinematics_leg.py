# inverse_kinematics_leg.py
import numpy as np
import pinocchio as pin

def inverse_kinematics_leg(model, data, q_init, frame_name, target_pos,
                           leg_joint_indices, eps=1e-4, max_iter=500, damping=1e-12):
    """
    Solve IK for a single leg of a quadruped relative to the floating base.
    
    Parameters
    ----------
    model : pin.Model
        Pinocchio robot model.
    data : pin.Data
        Pinocchio robot data.
    q_init : np.array
        Initial configuration (including floating base).
    frame_name : str
        Name of the foot frame to move.
    target_pos : np.array, shape (3,)
        Desired foot position in world coordinates.
    leg_joint_indices : slice or list
        Indices of the leg joints in q_init to update.
    eps : float
        Convergence threshold for foot position error.
    max_iter : int
        Maximum number of iterations.
    damping : float
        Damping factor for pseudo-inverse.
    
    Returns
    -------
    q_sol : np.array
        Solution configuration (same size as q_init).
    success : bool
        True if converged within max_iter iterations.
    """
    q = q_init.copy()
    
    for i in range(max_iter):
        # Forward kinematics
        pin.forwardKinematics(model, data, q)
        pin.updateFramePlacements(model, data)
        
        # Foot frame
        frame_id = model.getFrameId(frame_name)
        foot_pos = data.oMf[frame_id].translation
        
        # Error (position only)
        err = target_pos - foot_pos
        err_norm = np.linalg.norm(err)
        if err_norm < eps:
            return q, True
        
        # Full 6xN Jacobian
        J = pin.computeFrameJacobian(model, data, q, frame_id, pin.LOCAL_WORLD_ALIGNED)
        
        # Take only translation part (top 3 rows)
        J_trans = J[:3, leg_joint_indices] if isinstance(leg_joint_indices, slice) else J[:3, leg_joint_indices]
        
        # Compute delta q for leg joints only
        H = J_trans.T @ J_trans + damping*np.eye(J_trans.shape[1])
        dq = np.linalg.solve(H, J_trans.T @ err)
        
        # Apply update to leg joints
        if isinstance(leg_joint_indices, slice):
            q[leg_joint_indices] += dq
        else:
            q[leg_joint_indices] = q[leg_joint_indices] + dq

    # Did not converge
    return q, False
