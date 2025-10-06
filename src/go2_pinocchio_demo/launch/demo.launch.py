from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
import os

def generate_launch_description():
    urdf_file = os.path.join(
        os.getenv('HOME'),
        'projects/motion_control_go2/src/unitree_ros/robots/go2_description/urdf/go2_description.urdf'
    )

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': Command(['xacro ', urdf_file])}],
            output='screen'
        ),

        Node(
            package='go2_pinocchio_demo',
            executable='fk_ik_id_example',
            name='fk_ik_id_example',
            output='screen'
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen'
        )
    ])
