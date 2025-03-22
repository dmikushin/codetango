# Add example executable
add_executable(example_cpp
    example.cpp
)

# Link with codetango library
target_link_libraries(example_cpp
    PRIVATE
        codetango
)

# Install examples
install(TARGETS example_cpp
    RUNTIME DESTINATION bin/examples
)

# Install Python example
install(FILES
    example.py
    DESTINATION bin/examples
    PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)
