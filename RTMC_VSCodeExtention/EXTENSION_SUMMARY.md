# RTMC VS Code Extension - Complete Package

## Overview

This VS Code extension provides comprehensive language support for RT-Micro-C (RTMC), a real-time embedded domain-specific language designed for microcontroller applications using RTOS.

## 🚀 Features

### 1. **Advanced Syntax Highlighting**
- **Task Definitions**: Special highlighting for `StartTask(stack_size, core, priority, task_id, read_adc_task_run);` syntax
- **RTOS Functions**: Purple/magenta highlighting for RTOS operations
- **Hardware Functions**: Green variants for different hardware peripherals
  - GPIO functions (bright green)
  - Timer functions (medium green)
  - ADC functions (darker green)
  - Communication functions (UART, SPI, I2C)
- **Debug Functions**: Red highlighting for debug operations
- **Bitfield Syntax**: Special highlighting for struct bitfields with colon syntax
- **Struct Definitions**: Distinctive colors for struct declarations

### 2. **Rich Code Snippets**
- **Complete Program**: `rtmc-program` - Full program template
- **Task Templates**: 
  - `task` - Basic task template
  - `gpio-blink` - GPIO LED blink task
  - `adc-sensor` - ADC sensor reading task
- **Data Structures**:
  - `struct` - Basic struct definition
  - `bitfield` - Bitfield struct for hardware registers
- **Hardware Operations**:
  - `gpio-init`, `gpio-set`, `gpio-get` - GPIO operations
  - `adc-init`, `adc-read` - ADC operations
  - `timer-init`, `timer-pwm` - Timer operations
  - `uart-write` - UART communication
- **RTOS Operations**:
  - `delay` - RTOS delay
  - `sem-create`, `sem-take`, `sem-give` - Semaphore operations
- **Control Flow**:
  - `if`, `ifelse` - Conditional statements
  - `while`, `for` - Loop constructs
- **Utilities**:
  - `main` - Main function template
  - `func` - Function definition
  - `import` - Import statement
  - `dbg` - Debug print

### 3. **IntelliSense Support**
- **Auto-completion** for all RTMC keywords and functions
- **Parameter hints** for hardware and RTOS functions
- **Hover information** with detailed function descriptions
- **Smart suggestions** based on context

### 4. **Build & Run Integration**
- **Compile**: `Ctrl+Shift+B` - Compile .rtmc files to bytecode
- **Run**: `Ctrl+F5` - Execute compiled programs
- **Debug**: Enhanced debugging with trace support
- **Terminal Integration**: Commands run in VS Code terminal
- **Error Reporting**: Compilation errors displayed in VS Code

### 5. **Custom Theme**
- **RTMC Dark Theme**: Specially designed for RTMC syntax
- **Color-coded Functions**: Different colors for different function types
- **High Contrast**: Optimized for embedded development workflow

## 📁 File Structure

```
RTMC-VSCode-Extention/
├── package.json                 # Extension manifest
├── README.md                    # Documentation
├── BUILD.md                     # Build instructions
├── CHANGELOG.md                 # Version history
├── language-configuration.json  # Language settings
├── icon.svg                     # Extension icon
├── sample.rtmc                  # Sample RTMC file
├── .gitignore                   # Git ignore rules
├── .eslintrc.js                 # ESLint configuration
├── tsconfig.json                # TypeScript configuration
├── syntaxes/
│   └── rtmc.tmLanguage.json     # Syntax highlighting grammar
├── themes/
│   └── rtmc-dark-theme.json     # Custom dark theme
├── snippets/
│   └── rtmc.json                # Code snippets
├── src/
│   ├── extension.ts             # Main extension code
│   └── test/                    # Test files
├── .vscode/
│   ├── extensions.json          # Recommended extensions
│   ├── launch.json              # Debug configuration
│   └── tasks.json               # Build tasks
```

## 🔧 Configuration

The extension provides several configuration options:

```json
{
  "rtmc.compilerPath": "python",
  "rtmc.compilerScript": "path/to/RTMC-Compiler/main.py",
  "rtmc.vmRunnerScript": "path/to/RTMC-Compiler/vm_runner.py",
  "rtmc.enableDebugMode": false
}
```

## 🎨 Language Features

### Task System
```c
int ledPin = 13;

void run() {
    HW_GPIO_INIT(ledPin, 1);
    while (1) {
        HW_GPIO_SET(ledPin, 1);
        delay_ms(500);
        HW_GPIO_SET(ledPin, 0);
        delay_ms(500);
    }
}

void main()
{
  StartTask(stack_size, core, priority, task_id, run);
}
```

### Bitfield Structs
```c
struct ControlRegister {
    int enable : 1;      // 1-bit flag
    int mode : 2;        // 2-bit mode
    int speed : 4;       // 4-bit speed
    int reserved : 25;   // Remaining bits
};
```

### Hardware Abstraction
```c
// GPIO Operations
HW_GPIO_INIT(pin, direction);
HW_GPIO_SET(pin, value);
int value = HW_GPIO_GET(pin);

// ADC Operations
HW_ADC_INIT(pin);
int reading = HW_ADC_READ(pin);

// Timer Operations
HW_TIMER_INIT(timer_id, frequency);
HW_TIMER_SET_PWM_DUTY(timer_id, duty_cycle);
```

### RTOS Features
```c
// Delays
delay_ms(milliseconds);

// Semaphores
int sem = RTOS_SEMAPHORE_CREATE();
RTOS_SEMAPHORE_TAKE(sem, timeout);
RTOS_SEMAPHORE_GIVE(sem);
```

## 🚀 Installation & Usage

1. **Prerequisites**:
   - Node.js (16+)
   - VS Code
   - Python (for RTMC compiler)

2. **Build Extension**:
   ```bash
   cd RTMC-VSCode-Extention
   npm install
   npm run compile
   ```

3. **Install Extension**:
   - Package: `vsce package`
   - Install: VS Code → Extensions → Install from VSIX

4. **Configure**:
   - Set compiler and VM runner paths in VS Code settings

5. **Start Coding**:
   - Create `.rtmc` files
   - Use snippets and IntelliSense
   - Compile with `Ctrl+Shift+B`
   - Run with `Ctrl+F5`

## 🎯 Benefits

- **Rapid Development**: Snippets and templates accelerate coding
- **Error Prevention**: Syntax highlighting catches errors early
- **Embedded Focus**: Tailored for microcontroller development
- **RTOS Integration**: First-class support for real-time concepts
- **Hardware Abstraction**: Clear visualization of hardware operations
- **Debug Support**: Enhanced debugging capabilities

## 🔍 Sample Code

The extension includes a comprehensive `sample.rtmc` file demonstrating:
- Task definitions with different priorities
- Hardware peripheral usage
- RTOS synchronization
- Bitfield structures
- Control flow constructs
- Debug operations

## 📊 Language Coverage

The extension provides complete support for:
- ✅ Task definitions
- ✅ Struct and bitfield declarations
- ✅ All RTOS functions
- ✅ Hardware abstraction functions
- ✅ Control flow statements
- ✅ Debug operations
- ✅ Import statements
- ✅ Data types and operators
- ✅ Comments and documentation

## 🎨 Visual Design

The extension features:
- **Consistent Color Scheme**: Related functions use similar colors
- **High Contrast**: Important keywords stand out
- **Functional Grouping**: Hardware vs RTOS vs debug functions
- **Readability**: Optimized for long coding sessions

This extension transforms VS Code into a powerful IDE for RTMC development, providing all the tools needed for efficient embedded systems programming with real-time capabilities.
