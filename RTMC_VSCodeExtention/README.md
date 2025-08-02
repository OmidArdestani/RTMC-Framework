# RTMC Language Support for VS Code

A comprehensive Visual Studio Code extension for RT-Micro-C (RTMC) language support. RTMC is a real-time, embedded domain-specific language designed for microcontroller applications using RTOS.

## Features

### 🎨 **Syntax Highlighting**
- Complete syntax highlighting for RTMC language constructs
- Special highlighting for:
  - Task definitions with core and priority parameters
  - RTOS functions (purple/magenta)
  - Hardware functions (green variants)
  - Debug functions (red)
  - Bitfield definitions
  - Struct declarations

### 📝 **Code Snippets**
- **Task Templates**: Quick task creation with `task` snippet
- **GPIO Operations**: `gpio-init`, `gpio-set`, `gpio-get`
- **ADC Operations**: `adc-init`, `adc-read`
- **Timer Operations**: `timer-init`, `timer-pwm`
- **RTOS Operations**: `delay`, `sem-create`, `sem-take`, `sem-give`
- **Complete Program**: `rtmc-program` for full program template

### 🔧 **IntelliSense Support**
- Auto-completion for RTMC keywords and functions
- Hover information for functions and keywords
- Parameter hints for hardware and RTOS functions

### 🛠️ **Build & Run Integration**
- **Compile**: `Ctrl+Shift+B` to compile .rtmc files
- **Run**: `Ctrl+F5` to run compiled programs
- **Debug**: Enhanced debugging with trace support

### 🎯 **Language Features**
- Bracket matching and auto-closing
- Comment toggling (// and /* */)
- Code folding support
- Indentation rules

## Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "RTMC Language Support"
4. Install the extension

## Configuration

Configure the extension in VS Code settings:

```json
{
  "rtmc.compilerPath": "python",
  "rtmc.compilerScript": "path/to/your/rtmc/compiler/main.py",
  "rtmc.vmRunnerScript": "path/to/your/rtmc/vm_runner.py",
  "rtmc.enableDebugMode": false
}
```

## Usage

### Creating a New RTMC File

1. Create a new file with `.rtmc` extension
2. Start typing - IntelliSense will provide suggestions
3. Use snippets for quick code generation

### Example RTMC Code

```c
// RT-Micro-C Task Example
int ledPin = 13;
int blinkDelay = 500;

void BlinkTaskRun() {
    HW_GPIO_INIT(ledPin, 1);  // Initialize as output
    
    while (1) {
        HW_GPIO_SET(ledPin, 1);
        delay_ms(blinkDelay);
        HW_GPIO_SET(ledPin, 0);
        delay_ms(blinkDelay);
    }
}

void main() {
    StartTask(1024, 0, 2, 1, BlinkTaskRun);

    print("RTMC System Starting");
    
    while (1) {
        delay_ms(5000);
        print("Main loop heartbeat");
    }
}
```

### Building and Running

1. **Compile**: Press `Ctrl+Shift+B` or use Command Palette `RTMC: Compile RTMC File`
2. **Run**: Press `Ctrl+F5` or use Command Palette `RTMC: Run RTMC Program`
3. **Debug**: Use Command Palette `RTMC: Debug RTMC Program`

## Language Features

### Task System
```c
void run() {
    // Task implementation
}
StartTask(stack_size, core, priority, task_id, run);
```

### Hardware Abstraction
- **GPIO**: `HW_GPIO_INIT`, `HW_GPIO_SET`, `HW_GPIO_GET`
- **ADC**: `HW_ADC_INIT`, `HW_ADC_READ`
- **Timers**: `HW_TIMER_INIT`, `HW_TIMER_START`, PWM support
- **Communication**: UART, SPI, I2C interfaces

### RTOS Integration
- **Delays**: `delay_ms`
- **Semaphores**: `RTOS_SEMAPHORE_CREATE`, `RTOS_SEMAPHORE_TAKE`, `RTOS_SEMAPHORE_GIVE`
- **Task Management**: `RTOS_SUSPEND_TASK`, `RTOS_RESUME_TASK`

### Bitfield Support
```c
struct ControlRegister {
    int enable : 1;      // 1-bit flag
    int mode : 2;        // 2-bit mode (0-3)
    int speed : 4;       // 4-bit speed (0-15)
    int reserved : 25;   // Remaining bits
};
```

## Commands

- `RTMC: Compile RTMC File` - Compile the current RTMC file
- `RTMC: Run RTMC Program` - Run the compiled program
- `RTMC: Debug RTMC Program` - Debug with trace information

## Snippets Reference

| Snippet | Description |
|---------|-------------|
| `task` | Complete task template |
| `gpio-blink` | GPIO LED blink task |
| `adc-sensor` | ADC sensor reading task |
| `struct` | Struct definition |
| `bitfield` | Bitfield struct |
| `main` | Main function |
| `func` | Function definition |
| `gpio-init` | GPIO initialization |
| `adc-read` | ADC reading |
| `delay` | RTOS delay |
| `dbg` | Debug print |
| `rtmc-program` | Complete program template |

## Theme

The extension includes a custom "RTMC Dark" theme optimized for RTMC syntax highlighting with:
- Distinctive colors for RTOS functions (purple/magenta)
- Hardware function highlighting (green variants)
- Debug function emphasis (red)
- Clear task and struct definition highlighting

## Requirements

- Python 3.7 or later
- RTMC Compiler (main.py)
- RTMC VM Runner (vm_runner.py)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This extension is licensed under the MIT License.
