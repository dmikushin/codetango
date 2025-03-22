cmake_minimum_required(VERSION 3.10)
project(CodeTango VERSION 0.1.0 LANGUAGES CXX)

# Options
option(BUILD_EXAMPLES "Build example applications" ON)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
include_directories(include)

# Add the C++ library
add_subdirectory(src)

# Add examples if requested
if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

# Installation for headers
install(DIRECTORY include/ DESTINATION include)

# Package configuration
include(CMakePackageConfigHelpers)
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/CodeTangoConfigVersion.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

# Configure package config file
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/CodeTangoConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/CodeTangoConfig.cmake"
    @ONLY
)

# Install package config files
install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/CodeTangoConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/CodeTangoConfigVersion.cmake"
    DESTINATION lib/cmake/CodeTango
)

# Export targets
install(EXPORT CodeTangoTargets
    FILE CodeTangoTargets.cmake
    NAMESPACE CodeTango::
    DESTINATION lib/cmake/CodeTango
)
