# RTMC Interpreter for FreeRTOS on Raspberry Pi Pico

This directory contains a complete C-based implementation of the RT-Micro-C bytecode interpreter for FreeRTOS running on the Raspberry Pi Pico (RP2040).

## Overview

The RTMC Interpreter translates the Python-based virtual machine into a native C implementation that can execute RT-Micro-C bytecode programs directly on the Raspberry Pi Pico hardware using FreeRTOS for task management.

## Architecture

### Core Components

1. **Virtual Machine Core** (`rtmc_interpreter.h/c`)
   - Bytecode instruction execution engine
   - Memory management
   - Task scheduling interface with FreeRTOS

2. **RTOS Integration**
   - FreeRTOS task creation and management
   - Semaphore and queue operations
   - Message passing between tasks

3. **Hardware Abstraction Layer**
   - GPIO control (input/output, PWM)
   - Timer management
   - ADC operations
   - UART, SPI, I2C communication

### Supported Instructions

The interpreter supports all RT-Micro-C bytecode instructions:

#### Control Flow
- `JUMP`, `JUMPIF_TRUE`, `JUMPIF_FALSE`
- `CALL`, `RET`

#### Data Manipulation
- `LOAD_CONST`, `LOAD_VAR`, `STORE_VAR`
- `LOAD_STRUCT_MEMBER`, `STORE_STRUCT_MEMBER`
- `LOAD_STRUCT_MEMBER_BIT`, `STORE_STRUCT_MEMBER_BIT`
- Pointer operations: `LOAD_ADDR`, `LOAD_DEREF`, `STORE_DEREF`

#### Arithmetic & Logic
- `ADD`, `SUB`, `MUL`, `DIV`, `MOD`
- `AND`, `OR`, `NOT`, `XOR`
- Comparisons: `EQ`, `NEQ`, `LT`, `LTE`, `GT`, `GTE`

#### Memory Management
- `ALLOC_VAR`, `FREE_VAR`, `ALLOC_STRUCT`
- `ALLOC_FRAME`, `FREE_FRAME`
- Array operations: `ALLOC_ARRAY`, `LOAD_ARRAY_ELEM`, `STORE_ARRAY_ELEM`

#### RTOS Operations
- `RTOS_CREATE_TASK`, `RTOS_DELETE_TASK`
- `delay_ms`, `RTOS_YIELD`
- `RTOS_SEMAPHORE_CREATE`, `RTOS_SEMAPHORE_TAKE`, `RTOS_SEMAPHORE_GIVE`
- `RTOS_SUSPEND_TASK`, `RTOS_RESUME_TASK`

#### Message Passing
- `MSG_DECLARE`, `MSG_SEND`, `MSG_RECV`

#### Hardware Access
- GPIO: `HW_GPIO_INIT`, `HW_GPIO_SET`, `HW_GPIO_GET`
- Timers: `HW_TIMER_INIT`, `HW_TIMER_START`, `HW_TIMER_STOP`, `HW_TIMER_SET_PWM_DUTY`
- ADC: `HW_ADC_INIT`, `HW_ADC_READ`
- Communication: `HW_UART_WRITE`, `HW_SPI_TRANSFER`, `HW_I2C_WRITE`, `HW_I2C_READ`

#### Debug Support
- `PRINT`, `PRINTF`, `DBG_BREAKPOINT`

## Building

### Prerequisites

1. **Pico SDK**: Download and install the Raspberry Pi Pico SDK
2. **FreeRTOS Kernel**: Download FreeRTOS LTS release
3. **CMake**: Version 3.13 or higher
4. **ARM GCC Toolchain**: For cross-compilation

### Build Steps

1. Update the `FREERTOS_KERNEL_PATH` in the main `CMakeLists.txt` to point to your FreeRTOS installation.

2. Create a build directory:
   ```bash
   mkdir build
   cd build
   ```

3. Configure the build:
   ```bash
   cmake .. -DPICO_BOARD=pico
   ```

4. Build the project:
   ```bash
   make rtmc_interpreter_example
   ```

5. The resulting UF2 file can be copied to the Pico when it's in bootloader mode.

## Usage

### UART-Based Program Loading (Recommended)

The interpreter now supports dynamic program loading through UART commands:

```c
#include "rtmc_interpreter.h"

int main() {
    // The main application handles UART commands automatically
    // See rtmc_interpreter_example_main.c for complete implementation
    
    stdio_init_all();
    uart_init_custom();        // Initialize UART interface
    app_init();               // Initialize application state
    
    // Create command processing and monitoring tasks
    xTaskCreate(command_task, "CommandTask", 2048, NULL, 2, NULL);
    xTaskCreate(monitor_task, "MonitorTask", 1024, NULL, 1, NULL);
    
    // Start FreeRTOS scheduler
    vTaskStartScheduler();
    return 0;
}
```

#### UART Commands

- `LOAD <size>` - Load bytecode program of specified size
- `RUN` - Start executing the loaded program  
- `STOP` - Stop the currently running program
- `STATUS` - Get current VM status and information
- `RESET` - Reset the VM and clear loaded program
- `HELP` - Show available commands

#### Python Control Utility

Use the included `rtmc_sender.py` script for easy program uploading:

```bash
# Interactive mode
python rtmc_sender.py COM3 interactive

# Direct commands
python rtmc_sender.py COM3 load blink.vmb
python rtmc_sender.py COM3 run
python rtmc_sender.py COM3 status
python rtmc_sender.py COM3 stop
```

### Basic Usage (Legacy)

```c
#include "rtmc_interpreter.h"

int main() {
    // Initialize stdio
    stdio_init_all();
    
    // Create VM
    rtmc_vm_t* vm = rtmc_vm_create(true, false); // debug=true, trace=false
    
    // Create and load program
    rtmc_program_t* program = rtmc_program_create();
    // ... populate program with bytecode ...
    
    // Load program into VM
    rtmc_vm_load_program(vm, program);
    
    // Run VM (creates FreeRTOS tasks)
    rtmc_vm_run(vm);
    
    // Start FreeRTOS scheduler
    vTaskStartScheduler();
    
    return 0;
}
```

### Example Program

The `example_main.c` file demonstrates a simple LED blinking program:

```c
// Example bytecode for blinking LED on GPIO 25
static rtmc_instruction_t example_instructions[] = {
    {RTMC_OP_LOAD_CONST, 1, {{.i32 = 25}}, 1},      // Load GPIO pin 25
    {RTMC_OP_LOAD_CONST, 1, {{.i32 = 1}}, 2},       // Load OUTPUT mode
    {RTMC_OP_HW_GPIO_INIT, 0, {}, 3},               // Initialize GPIO
    // ... more instructions for blinking loop
};
```

## Configuration

### Memory Limits

The interpreter has configurable memory limits defined in `rtmc_interpreter.h`:

```c
#define RTMC_MAX_INSTRUCTIONS       10000
#define RTMC_MAX_CONSTANTS         1000
#define RTMC_MAX_STRINGS           500
#define RTMC_MAX_FUNCTIONS         100
#define RTMC_MAX_SYMBOLS           1000
#define RTMC_MAX_TASKS             16
#define RTMC_MAX_SEMAPHORES        32
#define RTMC_MAX_MESSAGE_QUEUES    16
#define RTMC_MAX_STACK_SIZE        256
#define RTMC_MAX_CALL_STACK        32
#define RTMC_MAX_MEMORY_SIZE       4096
```

### FreeRTOS Configuration

The `FreeRTOSConfig.h` file contains FreeRTOS-specific settings optimized for the interpreter:

- Heap size: 128KB
- Maximum tasks: 32 priority levels
- Dual-core support enabled
- Task notifications enabled for message passing

## Hardware Support

### GPIO
- All 30 GPIO pins supported
- Input/output modes
- Digital read/write operations

### Timers
- 8 timer channels
- PWM support using Pico's PWM slices
- Configurable frequency and duty cycle

### ADC
- 4 ADC channels (ADC0-ADC3)
- 12-bit resolution
- Temperature sensor support

### Communication
- UART: Serial communication
- SPI: High-speed serial interface
- I2C: Two-wire interface for sensors

## Debugging

### Debug Output

Enable debug mode when creating the VM:

```c
rtmc_vm_t* vm = rtmc_vm_create(true, false); // debug=true, trace=false
```

Debug output includes:
- Instruction execution traces
- Memory allocation/deallocation
- Hardware operation status
- Task creation/deletion events

### Error Handling

The interpreter provides comprehensive error codes:

```c
typedef enum {
    RTMC_OK = 0,
    RTMC_ERROR_NULL_POINTER,
    RTMC_ERROR_INVALID_OPCODE,
    RTMC_ERROR_STACK_OVERFLOW,
    RTMC_ERROR_STACK_UNDERFLOW,
    RTMC_ERROR_DIVISION_BY_ZERO,
    // ... more error codes
} rtmc_error_t;
```

## Integration with Python VM

This C implementation maintains compatibility with the Python virtual machine:

1. **Identical Instruction Set**: All opcodes and operand formats match exactly
2. **Memory Layout**: Compatible memory addressing scheme
3. **RTOS Semantics**: Same task scheduling and synchronization behavior
4. **Hardware Interface**: Equivalent hardware abstraction layer

## Performance Characteristics

### Memory Usage
- Code size: ~50KB (depending on configuration)
- RAM usage: ~10KB + program memory + task stacks
- Heap usage: Configurable, default 128KB

### Execution Speed
- Native ARM Cortex-M0+ execution
- No interpretation overhead for hardware operations
- FreeRTOS provides real-time task scheduling

### Real-time Characteristics
- Deterministic instruction execution
- Bounded interrupt latency
- Priority-based preemptive scheduling

## Limitations

1. **Binary Format**: Currently requires manual bytecode creation (no binary loader yet)
2. **Floating Point**: Limited floating-point support (RP2040 has no FPU)
3. **Memory Size**: Limited by available RAM (264KB total on RP2040)
4. **Debug Features**: Limited compared to Python implementation

## Future Enhancements

1. **Binary Loader**: Support for loading compiled .vmb files
2. **Flash Storage**: Store programs in flash memory
3. **Network Support**: WiFi/Bluetooth communication
4. **Advanced Debugging**: GDB integration, breakpoints
5. **Optimization**: JIT compilation for frequently executed code

## Files

- `rtmc_interpreter.h` - Main header with all type definitions and function prototypes
- `rtmc_interpreter.c` - Complete implementation of the interpreter
- `rtmc_binary_loader.h/c` - Binary program loader with CRC32 verification
- `rtmc_interpreter_example_main.c` - UART-based control system with dynamic program loading
- `rtmc_sender.py` - Python utility for sending programs and controlling execution
- `FreeRTOSConfig.h` - FreeRTOS configuration optimized for the interpreter
- `CMakeLists.txt` - Build configuration for CMake
- `README.md` - This documentation file
- `USAGE_GUIDE.md` - Comprehensive guide for UART control system

## Workflow

1. **Develop RT-Micro-C Program:**
   ```c
   // blink.rtmc
   void blink_task() {
       gpio_init(25, OUTPUT);
       while(1) {
           gpio_set(25, 1);
           delay_ms(500);
           gpio_set(25, 0);
           delay_ms(500);
       }
   }
   
   int main() {
       create_task(blink_task, 1024, 5, 0);
       return 0;
   }
   ```

2. **Compile to Bytecode:**
   ```bash
   cd RTMC_Compiler
   python main.py blink.rtmc -o blink.vmb
   ```

3. **Upload and Execute:**
   ```bash
   python rtmc_sender.py COM3 load blink.vmb
   python rtmc_sender.py COM3 run
   ```

4. **Monitor and Control:**
   - Watch LED blink on GPIO 25
   - Use STATUS commands to monitor execution
   - Use STOP/START for execution control

## License

This implementation follows the same license as the parent RTMC project.
