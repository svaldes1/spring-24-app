cmake_minimum_required(VERSION 3.16)
project(mil-test)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include_directories("include")
file(GLOB_RECURSE mil-test CONFIGURE_DEPENDS "src/*.cpp")
add_executable(mil-test ${mil-test})
set_property(TARGET mil-test PROPERTY CXX_STANDARD 20)
