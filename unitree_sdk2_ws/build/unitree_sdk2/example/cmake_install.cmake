# Install script for directory: /home/jason/projects/unitree_sdk2_ws/unitree_sdk2/example

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/jason/projects/unitree_sdk2_ws/install/unitree_sdk2")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/helloworld/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/wireless_controller/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/jsonize/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/state_machine/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/go2/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/b2/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/h1/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/g1/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/go2w/cmake_install.cmake")
  include("/home/jason/projects/unitree_sdk2_ws/build/unitree_sdk2/example/b2w/cmake_install.cmake")

endif()

