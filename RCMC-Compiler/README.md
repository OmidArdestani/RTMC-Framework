# Mini-C RTOS Language Compiler

A lightweight C-like language compiler targeting real-time operating systems with hardware abstraction support.

## Features

- **Real-time Task Support**: Native RTOS task management with priorities and core affinity
- **Hardware Abstraction**: Built-in GPIO, Timer, ADC, UART, SPI, I2C support
- **Bit-field Structs**: Efficient memory layout for embedded systems
- **Optimized Bytecode**: Compact virtual machine instructions for resource-constrained environments
- **Class-based Tasks**: Object-oriented approach to task management

## Architecture

The compiler follows a traditional multi-stage pipeline:

1. **Lexical Analysis**: Tokenizes source code
2. **Parser**: Builds Abstract Syntax Tree (AST)
3. **Semantic Analysis**: Type checking and symbol resolution
4. **Optimizer**: Compile-time optimizations
5. **Bytecode Generator**: Produces .vmb executable files

## Usage

```bash
# Compile a Mini-C file
python main.py input.mc -o output.vmb

# Run with the virtual machine
python vm_runner.py output.vmb
```

## Mini-C Language Syntax

```c
// Hardware GPIO example
const int LED_PIN = 25;

void setup() {
    HW_GPIO_INIT(LED_PIN, 1);  // Initialize as output
}

void blink_task() {
    while (1) {
        HW_GPIO_SET(LED_PIN, 1);
        RTOS_DELAY_MS(500);
        HW_GPIO_SET(LED_PIN, 0);
        RTOS_DELAY_MS(500);
    }
}

void main() {
    setup();
    RTOS_CREATE_TASK(blink_task, "Blink", 1024, 5, 0);
}
```

## Virtual Machine Bytecode

The compiler generates compact bytecode with instructions for:
- Control flow (JUMP, CALL, RET)
- Data manipulation (LOAD, STORE, arithmetic)
- RTOS operations (task management, synchronization)
- Hardware access (GPIO, timers, communication)

## Building

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Build examples
python main.py examples/blink.mc -o examples/blink.vmb
```

## License

MIT License
