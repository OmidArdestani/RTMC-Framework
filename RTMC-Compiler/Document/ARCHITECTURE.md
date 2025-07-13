# RT-Micro-C RTOS Language Compiler

## Overview

This is a complete implementation of the RT-Micro-C compiler specification for real-time operating systems. The compiler converts RT-Micro-C source code into optimized bytecode that runs on a lightweight virtual machine with built-in RTOS and hardware abstraction support.

## Architecture

### Compiler Pipeline

1. **Lexical Analysis** (`src/lexer/tokenizer.py`)
   - Tokenizes source code into language tokens
   - Recognizes keywords, identifiers, literals, operators
   - Handles RTOS and hardware function keywords

2. **Parser** (`src/parser/parser.py`)
   - Builds Abstract Syntax Tree (AST) from tokens
   - Recursive descent parser with precedence handling
   - Supports functions, structs, control flow, expressions

3. **Semantic Analysis** (`src/semantic/analyzer.py`)
   - Type checking and symbol resolution
   - Scope management and variable tracking
   - Built-in function validation

4. **Optimizer** (`src/optimizer/optimizer.py`)
   - Constant folding and propagation
   - Dead code elimination
   - Algebraic simplifications

5. **Bytecode Generator** (`src/bytecode/generator.py`)
   - Converts AST to bytecode instructions
   - Handles function calls, control flow, expressions
   - Optimizes instruction sequences

6. **Virtual Machine** (`src/vm/virtual_machine.py`)
   - Executes bytecode programs
   - Simulates RTOS tasks and synchronization
   - Hardware peripheral simulation

## Features

### Language Support
- **Data Types**: int, float, char, void, struct
- **Control Flow**: if/else, while, for, break, continue, return
- **Functions**: Declaration, calling, parameters, return values
- **Structs**: Field access, bit-fields for embedded systems
- **Arrays**: Static arrays with indexing
- **Constants**: Compile-time constant expressions

### RTOS Features
- **Task Management**: Create, delete, suspend, resume tasks
- **Synchronization**: Binary semaphores with timeout
- **Scheduling**: Cooperative multitasking with yielding
- **Timing**: Precise millisecond delays

### Hardware Abstraction
- **GPIO**: Pin initialization, digital I/O
- **Timers**: PWM generation, frequency control
- **ADC**: Analog input reading
- **Communication**: UART, SPI, I2C interfaces
- **Debug**: Print statements and breakpoints

## Usage

### Basic Compilation
```bash
python main.py input.mc -o output.vmb
```

### Compilation Options
```bash
python main.py input.mc -o output.vmb --verbose --ast --tokens
```

### Running Programs
```bash
python vm_runner.py output.vmb --debug --trace
```

### Example Programs

#### GPIO LED Blink
```c
const int LED_PIN = 25;

void main() {
    HW_GPIO_INIT(LED_PIN, 1);
    
    while (1) {
        HW_GPIO_SET(LED_PIN, 1);
        RTOS_DELAY_MS(500);
        HW_GPIO_SET(LED_PIN, 0);
        RTOS_DELAY_MS(500);
    }
}
```

#### Multi-Task with Semaphore
```c
int semaphore;
int shared_data = 0;

void task1() {
    while (1) {
        RTOS_SEMAPHORE_TAKE(semaphore, 1000);
        shared_data++;
        RTOS_SEMAPHORE_GIVE(semaphore);
        RTOS_DELAY_MS(100);
    }
}

void main() {
    semaphore = RTOS_SEMAPHORE_CREATE();
    RTOS_CREATE_TASK(task1, "Task1", 512, 5, 0);
    
    while (1) {
        RTOS_DELAY_MS(1000);
        DBG_PRINT("Main running");
    }
}
```

#### Debug Output with Variables
```c
void main() {
    int sensor_value = 1024;
    float temperature = 25.5;
    int *ptr = &sensor_value;
    
    // Simple debug output
    DBG_PRINT("System initialized");
    
    // Formatted debug output with variables
    DBG_PRINTF("Sensor reading: {0}", sensor_value);
    DBG_PRINTF("Temperature: {0}°C", temperature);
    DBG_PRINTF("Pointer address: {0}", ptr);
    DBG_PRINTF("Multiple values: sensor={0}, temp={1}", sensor_value, temperature);
    
    // Simple placeholder syntax
    DBG_PRINTF("Values: {}, {}", sensor_value, temperature);
}
```

## Bytecode Format

The compiler generates `.vmb` files with the following structure:

```
+--------------------------+
| Magic Header: "MINICRTOS"|
| Version: 1               |
| Constant Pool            |
| String Pool              |
| Symbol Table             |
| Function Table           |
| Struct Layout Table      |
| Bytecode Instructions    |
+--------------------------+
```

## Instruction Set

The RT-Micro-C Virtual Machine uses a stack-based instruction set with comprehensive support for embedded systems programming, real-time operations, and hardware abstraction.

### Control Flow Instructions
- **`JUMP`** - Unconditional jump to target address
- **`JUMPIF_TRUE`** - Conditional jump if top stack value is true
- **`JUMPIF_FALSE`** - Conditional jump if top stack value is false
- **`CALL`** - Call function by ID, pushes return address
- **`RET`** - Return from function, pops return address

### Data Manipulation Instructions

#### Load/Store Operations
- **`LOAD_CONST`** - Load constant value onto stack
- **`LOAD_VAR`** - Load variable value by address onto stack
- **`STORE_VAR`** - Store top stack value to variable address
- **`LOAD_STRUCT_MEMBER`** - Load struct member by base address and offset
- **`STORE_STRUCT_MEMBER`** - Store value to struct member
- **`LOAD_STRUCT_MEMBER_BIT`** - Load bit-field from struct (base, byte_offset, bit_offset, width)
- **`STORE_STRUCT_MEMBER_BIT`** - Store bit-field to struct

#### Pointer Operations
- **`LOAD_ADDR`** - Load address of variable (for pointer operations)
- **`LOAD_DEREF`** - Dereference pointer on stack
- **`STORE_DEREF`** - Store value at pointer address

#### Memory Management
- **`ALLOC_VAR`** - Allocate variable with specified size
- **`FREE_VAR`** - Free allocated variable at address
- **`ALLOC_STRUCT`** - Allocate struct with specified size

### Arithmetic and Logical Instructions
- **`ADD`** - Add two top stack values
- **`SUB`** - Subtract second stack value from top
- **`MUL`** - Multiply two top stack values
- **`DIV`** - Divide second stack value by top
- **`MOD`** - Modulo operation (second % top)
- **`AND`** - Logical AND of two top stack values
- **`OR`** - Logical OR of two top stack values
- **`NOT`** - Logical NOT of top stack value
- **`XOR`** - Logical XOR of two top stack values

### Comparison Instructions
- **`EQ`** - Equal comparison (==)
- **`NEQ`** - Not equal comparison (!=)
- **`LT`** - Less than comparison (<)
- **`LTE`** - Less than or equal comparison (<=)
- **`GT`** - Greater than comparison (>)
- **`GTE`** - Greater than or equal comparison (>=)

### RTOS Task Management Instructions
- **`RTOS_CREATE_TASK`** - Create new RTOS task (func_id, name_id, stack_size, priority, core)
- **`RTOS_DELETE_TASK`** - Delete RTOS task by handle
- **`RTOS_DELAY_MS`** - Delay current task for specified milliseconds
- **`RTOS_YIELD`** - Yield control to scheduler
- **`RTOS_SUSPEND_TASK`** - Suspend task by handle
- **`RTOS_RESUME_TASK`** - Resume suspended task by handle

### RTOS Synchronization Instructions
- **`RTOS_SEMAPHORE_CREATE`** - Create binary semaphore, returns handle
- **`RTOS_SEMAPHORE_TAKE`** - Take semaphore with timeout (handle, timeout_ms)
- **`RTOS_SEMAPHORE_GIVE`** - Give/release semaphore by handle

### Message Passing Instructions
- **`MSG_DECLARE`** - Declare message queue
- **`MSG_SEND`** - Send message to queue
- **`MSG_RECV`** - Receive message from queue

### Hardware Abstraction - GPIO Instructions
- **`HW_GPIO_INIT`** - Initialize GPIO pin (pin_number, mode: 0=input, 1=output)
- **`HW_GPIO_SET`** - Set GPIO pin value (pin_number, value: 0=low, 1=high)
- **`HW_GPIO_GET`** - Read GPIO pin value, pushes result to stack

### Hardware Abstraction - Timer Instructions
- **`HW_TIMER_INIT`** - Initialize timer (timer_id, mode, frequency)
- **`HW_TIMER_START`** - Start timer by ID
- **`HW_TIMER_STOP`** - Stop timer by ID
- **`HW_TIMER_SET_PWM_DUTY`** - Set PWM duty cycle (timer_id, duty_percent)

### Hardware Abstraction - ADC Instructions
- **`HW_ADC_INIT`** - Initialize ADC on specified pin
- **`HW_ADC_READ`** - Read ADC value from pin, pushes result to stack

### Hardware Abstraction - Communication Instructions
- **`HW_UART_WRITE`** - Write data to UART (buffer_address, length)
- **`HW_SPI_TRANSFER`** - SPI bidirectional transfer (tx_addr, rx_addr, length)
- **`HW_I2C_WRITE`** - Write data to I2C device (device_addr, data_value)
- **`HW_I2C_READ`** - Read data from I2C device (device_addr, register)

### Debug and System Instructions
- **`DBG_PRINT`** - Print debug string by string_id
- **`DBG_PRINTF`** - Print formatted debug string with variable substitution (format_string_id, arg_count)
- **`DBG_BREAKPOINT`** - Trigger debugger breakpoint
- **`SYSCALL`** - Generic system call (call_id, arguments...)
- **`HALT`** - Halt program execution
- **`NOP`** - No operation (for alignment/spacing)
- **`COMMENT`** - Debug comment instruction (ignored at runtime)

### Instruction Format

All instructions follow a consistent format:
```
OPCODE [OPERAND1] [OPERAND2] [OPERAND3] [...]
```

#### Operand Types
- **Immediate Values**: Constants embedded in instruction
- **Memory Addresses**: Variable and function locations
- **Stack Relative**: Offsets from stack pointer
- **Register IDs**: Hardware register identifiers

### Stack Operations

The virtual machine uses a stack-based execution model:

1. **Expression Evaluation**: Operands pushed to stack, operators consume and produce values
2. **Function Calls**: Parameters pushed before CALL, return value left on stack
3. **Local Variables**: Allocated on stack frame, accessed by offset
4. **Temporary Storage**: Intermediate calculation results

#### Stack Example
```c
int result = (a + b) * c;
```
Generates:
```
LOAD_VAR a_addr     // Push 'a'
LOAD_VAR b_addr     // Push 'b' 
ADD                 // Pop b,a; Push (a+b)
LOAD_VAR c_addr     // Push 'c'
MUL                 // Pop c,(a+b); Push result
STORE_VAR result_addr // Pop result; Store
```

### Error Handling

Runtime errors are detected and reported with context:
- **Division by Zero**: Arithmetic operations
- **Stack Overflow/Underflow**: Memory management
- **Invalid Memory Access**: Pointer operations
- **Timeout Violations**: RTOS operations
- **Hardware Errors**: Peripheral access failures
