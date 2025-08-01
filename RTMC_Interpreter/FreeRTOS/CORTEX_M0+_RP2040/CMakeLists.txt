set(FREERTOS_KERNEL_PATH "C:/Users/oarde/Downloads/FreeRTOSv202406.01-LTS/FreeRTOS-LTS/FreeRTOS/FreeRTOS-Kernel")

# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.1.1)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.1.1)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
set(PICO_BOARD pico CACHE STRING "Board type")

# Note that this file can be used as a top level CMakeLists.txt to build all the Demos (it includes
# them all, but they are usable in their own right, which is why no common work is done here)

cmake_minimum_required(VERSION 3.13)

# Pull in SDK (must be before project)
include(pico_sdk_import.cmake)

PROJECT(examples)

add_subdirectory(OnEitherCore)
add_subdirectory(Standard)
add_subdirectory(RTMCInterpreter)
