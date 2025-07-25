# RT-Micro-C Language Compiler v1.0

A real-time, embedded domain-specific language (DSL) for microcontroller applications using RTOS. Designed for clarity, efficiency, and direct task-hardware mapping.

## 🚀 Language Features

### ✨ **Native Task System**
```c
// Define the task function
void BlinkTask() {
    static int ledPin = 13;
    
    HW_GPIO_INIT(ledPin, 1);
    while (1) {
        HW_GPIO_SET(ledPin, 1);
        RTOS_DELAY_MS(500);
        HW_GPIO_SET(ledPin, 0);
        RTOS_DELAY_MS(500);
    }
}

// In main(), start the task:
StartTask(1024, 0, 2, 1, BlinkTask);  // stack_size, core, priority, task_id, function
```

### 🔧 **Advanced Bit-Fields**
```c
struct ControlRegister {
    int enable : 1;      // 1-bit flag
    int mode : 2;        // 2-bit mode (0-3)
    int speed : 4;       // 4-bit speed (0-15)
    int reserved : 25;   // Remaining bits
};
```

### 🏗️ **Complete Struct Support**
- Regular struct declarations and member access
- Nested struct member assignments (`rect.point.x = 10`)
- Bit-field packing with 32-bit alignment
- Efficient memory layout for embedded systems

### ⚡ **Hardware Abstraction**
- **GPIO**: `HW_GPIO_INIT`, `HW_GPIO_SET`, `HW_GPIO_GET`
- **ADC**: `HW_ADC_INIT`, `HW_ADC_READ`
- **Timers**: `HW_TIMER_INIT`, `HW_TIMER_START`, PWM support
- **Communication**: UART, SPI, I2C interfaces

### 🔄 **RTOS Integration**
- Task creation with flexible configuration:
  - Stack size for memory management
  - Core assignment for multi-core systems
  - Priority levels for scheduling
  - Unique task IDs for control
- Semaphores, delays, task suspension/resumption
- Real-time scheduling and resource management

### 🎨 **Flexible Brace Styles**
RT-Micro-C supports both common brace styles for maximum developer comfort:

```c
// Style 1: Opening brace on same line
void function() {
    if (condition) {
        while (loop) {
            // code
        }
    }
}

void MyTask() {
    // task code
}

// Start task in main:
StartTask(1024, 0, 1, 1, MyTask);
```

```c
// Style 2: Opening brace on new line
void function()
{
    if (condition)
    {
        while (loop)
        {
            // code
        }
    }
}

void MyTask()
{
    // task code
}

// Start task in main:
StartTask(1024, 0, 1, 1, MyTask);
```

Both styles can be mixed within the same file, supporting team preferences and existing code styles.

## Architecture

The compiler follows a traditional multi-stage pipeline:

1. **Lexical Analysis**: Tokenizes source code
2. **Parser**: Builds Abstract Syntax Tree (AST)
3. **Semantic Analysis**: Type checking and symbol resolution
4. **Optimizer**: Compile-time optimizations
5. **Bytecode Generator**: Produces .vmb executable files

## Usage

```bash
# Compile a RT-Micro-C file
python main.py input.mc -o output.vmb

# Run with the virtual machine
python vm_runner.py output.vmb
```

## RT-Micro-C Language Syntax

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
    // Start task with stack size, core, priority, ID, and function
    StartTask(1024, 0, 5, 1, blink_task);
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
