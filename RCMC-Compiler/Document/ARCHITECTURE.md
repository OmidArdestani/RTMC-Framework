# Mini-C RTOS Language Compiler

## Overview

This is a complete implementation of the Mini-C compiler specification for real-time operating systems. The compiler converts Mini-C source code into optimized bytecode that runs on a lightweight virtual machine with built-in RTOS and hardware abstraction support.

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

### Control Flow
- `JUMP`, `JUMPIF_TRUE`, `JUMPIF_FALSE`
- `CALL`, `RET`

### Data Operations
- `LOAD_CONST`, `LOAD_VAR`, `STORE_VAR`
- `LOAD_STRUCT_MEMBER`, `STORE_STRUCT_MEMBER`
- `ADD`, `SUB`, `MUL`, `DIV`, `MOD`
- `EQ`, `NEQ`, `LT`, `LTE`, `GT`, `GTE`
- `AND`, `OR`, `NOT`, `XOR`

### RTOS Operations
- `RTOS_CREATE_TASK`, `RTOS_DELETE_TASK`
- `RTOS_DELAY_MS`, `RTOS_YIELD`
- `RTOS_SEMAPHORE_CREATE`, `RTOS_SEMAPHORE_TAKE`, `RTOS_SEMAPHORE_GIVE`

### Hardware Operations
- `HW_GPIO_INIT`, `HW_GPIO_SET`, `HW_GPIO_GET`
- `HW_TIMER_INIT`, `HW_TIMER_START`, `HW_TIMER_STOP`
- `HW_ADC_INIT`, `HW_ADC_READ`
- `HW_UART_WRITE`, `HW_SPI_TRANSFER`
- `HW_I2C_WRITE`, `HW_I2C_READ`

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Or run individual test files:
```bash
python tests/test_compiler.py
```

## Implementation Details

### Memory Management
- Stack-based virtual machine
- Automatic memory allocation for variables
- Simplified garbage collection

### Type System
- Static typing with implicit conversions
- Numeric type promotion (char -> int -> float)
- Struct type checking with field validation

### Error Handling
- Comprehensive error reporting with line numbers
- Graceful error recovery in parser
- Runtime error detection in VM

### Optimization
- Constant folding at compile time
- Dead code elimination
- Algebraic simplification
- Jump optimization

## Future Enhancements

- **Pointers**: Add pointer support for dynamic memory
- **Arrays**: Dynamic array allocation
- **Interrupts**: Hardware interrupt handling
- **Modules**: Support for separate compilation units
- **Debugging**: Advanced debugging features
- **Optimization**: Loop unrolling, function inlining
- **Target**: Code generation for real microcontrollers

## License

MIT License - see LICENSE file for details.
