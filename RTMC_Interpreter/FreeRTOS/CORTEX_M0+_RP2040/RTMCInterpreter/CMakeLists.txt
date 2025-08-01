cmake_minimum_required(VERSION 3.13)

# Pull in SDK (must be before project)
include(pico_sdk_import.cmake)

# Pull in FreeRTOS
include(FreeRTOS_Kernel_import.cmake)

project(rtmc_interpreter_example C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# Create the RTMC Interpreter library
add_library(rtmc_interpreter_example
    rtmc_interpreter.c
    rtmc_interpreter.h
    rtmc_binary_loader.c
    rtmc_binary_loader.h
)

target_include_directories(rtmc_interpreter_example PUBLIC
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(rtmc_interpreter_example
    pico_stdlib
    FreeRTOS-Kernel
    FreeRTOS-Kernel-Heap4
    hardware_gpio
    hardware_timer
    hardware_adc
    hardware_uart
    hardware_spi
    hardware_i2c
    hardware_pwm
)

# Create example executable that uses the interpreter
add_executable(rtmc_interpreter_example
    rtmc_interpreter.c
    rtmc_binary_loader.c
)

target_compile_definitions(rtmc_interpreter_example PRIVATE
    PICO_STDIO_STACK_BUFFER_SIZE=64
)

pico_add_extra_outputs(rtmc_interpreter_example)
