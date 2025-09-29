
if(NOT "/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-subbuild/trianglemeshdistance-populate-prefix/src/trianglemeshdistance-populate-stamp/trianglemeshdistance-populate-gitinfo.txt" IS_NEWER_THAN "/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-subbuild/trianglemeshdistance-populate-prefix/src/trianglemeshdistance-populate-stamp/trianglemeshdistance-populate-gitclone-lastrun.txt")
  message(STATUS "Avoiding repeated git clone, stamp file is up to date: '/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-subbuild/trianglemeshdistance-populate-prefix/src/trianglemeshdistance-populate-stamp/trianglemeshdistance-populate-gitclone-lastrun.txt'")
  return()
endif()

execute_process(
  COMMAND ${CMAKE_COMMAND} -E rm -rf "/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-src"
  RESULT_VARIABLE error_code
  )
if(error_code)
  message(FATAL_ERROR "Failed to remove directory: '/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-src'")
endif()

# try the clone 3 times in case there is an odd git clone issue
set(error_code 1)
set(number_of_tries 0)
while(error_code AND number_of_tries LESS 3)
  execute_process(
    COMMAND "/usr/bin/git"  clone --no-checkout --config "advice.detachedHead=false" "https://github.com/InteractiveComputerGraphics/TriangleMeshDistance.git" "trianglemeshdistance-src"
    WORKING_DIRECTORY "/home/jason/projects/motion_control_go2/build/mujoco/_deps"
    RESULT_VARIABLE error_code
    )
  math(EXPR number_of_tries "${number_of_tries} + 1")
endwhile()
if(number_of_tries GREATER 1)
  message(STATUS "Had to git clone more than once:
          ${number_of_tries} times.")
endif()
if(error_code)
  message(FATAL_ERROR "Failed to clone repository: 'https://github.com/InteractiveComputerGraphics/TriangleMeshDistance.git'")
endif()

execute_process(
  COMMAND "/usr/bin/git"  checkout 2cb643de1436e1ba8e2be49b07ec5491ac604457 --
  WORKING_DIRECTORY "/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-src"
  RESULT_VARIABLE error_code
  )
if(error_code)
  message(FATAL_ERROR "Failed to checkout tag: '2cb643de1436e1ba8e2be49b07ec5491ac604457'")
endif()

set(init_submodules TRUE)
if(init_submodules)
  execute_process(
    COMMAND "/usr/bin/git"  submodule update --recursive --init 
    WORKING_DIRECTORY "/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-src"
    RESULT_VARIABLE error_code
    )
endif()
if(error_code)
  message(FATAL_ERROR "Failed to update submodules in: '/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-src'")
endif()

# Complete success, update the script-last-run stamp file:
#
execute_process(
  COMMAND ${CMAKE_COMMAND} -E copy
    "/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-subbuild/trianglemeshdistance-populate-prefix/src/trianglemeshdistance-populate-stamp/trianglemeshdistance-populate-gitinfo.txt"
    "/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-subbuild/trianglemeshdistance-populate-prefix/src/trianglemeshdistance-populate-stamp/trianglemeshdistance-populate-gitclone-lastrun.txt"
  RESULT_VARIABLE error_code
  )
if(error_code)
  message(FATAL_ERROR "Failed to copy script-last-run stamp file: '/home/jason/projects/motion_control_go2/build/mujoco/_deps/trianglemeshdistance-subbuild/trianglemeshdistance-populate-prefix/src/trianglemeshdistance-populate-stamp/trianglemeshdistance-populate-gitclone-lastrun.txt'")
endif()

