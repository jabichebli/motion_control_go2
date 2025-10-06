cmake_minimum_required(VERSION 3.8)
project(go2_pinocchio_demo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(pinocchio REQUIRED)
find_package(Eigen3 REQUIRED)


include_directories(
  ${pinocchio_INCLUDE_DIRS}
  ${EIGEN3_INCLUDE_DIRS}
  )

# Executable
add_executable(fk_ik_id_example src/fk_ik_id_example.cpp)
ament_target_dependencies(fk_ik_id_example rclcpp std_msgs sensor_msgs)
target_link_libraries(fk_ik_id_example ${pinocchio_LIBRARIES})

install(TARGETS
  fk_ik_id_example
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch
        DESTINATION share/${PROJECT_NAME})

  
ament_package()
