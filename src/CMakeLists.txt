# Add library
add_library(codetango SHARED
    codetango.cpp
)

# Set include directories for the library
target_include_directories(codetango
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# Set library properties
set_target_properties(codetango PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    OUTPUT_NAME "codetango"
    PUBLIC_HEADER "${CMAKE_SOURCE_DIR}/include/codetango.h"
)

# Install the library
install(TARGETS codetango
    EXPORT CodeTangoTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    PUBLIC_HEADER DESTINATION include
)
