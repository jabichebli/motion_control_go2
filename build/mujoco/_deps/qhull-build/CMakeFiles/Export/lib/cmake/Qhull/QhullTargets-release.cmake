#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Qhull::qhullcpp" for configuration "Release"
set_property(TARGET Qhull::qhullcpp APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Qhull::qhullcpp PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libqhullcpp.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS Qhull::qhullcpp )
list(APPEND _IMPORT_CHECK_FILES_FOR_Qhull::qhullcpp "${_IMPORT_PREFIX}/lib/libqhullcpp.a" )

# Import target "Qhull::qhullstatic" for configuration "Release"
set_property(TARGET Qhull::qhullstatic APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Qhull::qhullstatic PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libqhullstatic.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS Qhull::qhullstatic )
list(APPEND _IMPORT_CHECK_FILES_FOR_Qhull::qhullstatic "${_IMPORT_PREFIX}/lib/libqhullstatic.a" )

# Import target "Qhull::qhullstatic_r" for configuration "Release"
set_property(TARGET Qhull::qhullstatic_r APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Qhull::qhullstatic_r PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libqhullstatic_r.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS Qhull::qhullstatic_r )
list(APPEND _IMPORT_CHECK_FILES_FOR_Qhull::qhullstatic_r "${_IMPORT_PREFIX}/lib/libqhullstatic_r.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
