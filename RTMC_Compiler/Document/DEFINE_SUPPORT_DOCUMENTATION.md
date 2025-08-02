# #define Preprocessor Support Documentation

## Overview

The RT-Micro-C compiler now supports `#define` preprocessor directives, providing compile-time constant definition and substitution similar to the C preprocessor. This feature allows developers to define symbolic constants, configuration parameters, and reusable values that are expanded at compile time.

## Syntax

```c
#define IDENTIFIER value
```

Where:
- `IDENTIFIER` is the macro name (follows C identifier rules)
- `value` can be a number, string, character, or another identifier

## Supported Value Types

### Integer Constants
```c
#define MAX_SIZE 100
#define BUFFER_COUNT 8
#define PORT_NUMBER 8080
```

### Floating-Point Constants
```c
#define PI 3.14159265359
#define EULER 2.71828182846
#define GRAVITY 9.81
```

### String Literals
```c
#define VERSION "1.0.0"
#define ERROR_MSG "System error occurred"
#define DEBUG_PREFIX "[DEBUG] "
```

### Character Literals
```c
#define NEWLINE '\n'
#define TAB '\t'
#define NULL_CHAR '\0'
```

### Boolean Values
```c
#define TRUE true
#define FALSE false
#define ENABLED true
```

### Identifier References
```c
#define MAX_ITEMS 50
#define DEFAULT_COUNT MAX_ITEMS  // References another define
```

## Features

### Compile-Time Expansion
All `#define` macros are expanded during the preprocessing phase, before parsing. This means:
- No runtime overhead
- Values are directly substituted in the code
- Type checking occurs on the expanded values

### Word Boundary Matching
The preprocessor uses word boundary matching to ensure accurate substitution:
```c
#define MAX 100
int max_value = MAX;     // Correctly expands to: int max_value = 100;
int maximal = MAX + 1;   // MAX is NOT expanded in "maximal"
```

### Case Sensitivity
Macro names are case-sensitive:
```c
#define max 100
#define MAX 200
// These are different macros
```

## Example Usage

### Hardware Configuration
```c
#define LED_PIN 13
#define BUTTON_PIN 2
#define PWM_FREQUENCY 1000
#define ADC_RESOLUTION 12

void setup_hardware() {
    HW_GPIO_INIT(LED_PIN);
    HW_GPIO_INIT(BUTTON_PIN);
    HW_TIMER_SET_PWM_DUTY(PWM_FREQUENCY);
}
```

### RTOS Configuration
```c
#define TASK_STACK_SIZE 1024
#define MAX_TASKS 8
#define SCHEDULER_FREQUENCY 100
#define IDLE_TIMEOUT 5000

void create_tasks() {
    for (int i = 0; i < MAX_TASKS; i++) {
        RTOS_CREATE_TASK(worker_task);
    }
    delay_ms(IDLE_TIMEOUT);
}
```

### Mathematical Constants
```c
#define PI 3.14159265359
#define TWO_PI 6.28318530718
#define PI_OVER_2 1.57079632679

float calculate_circle_area(float radius) {
    return PI * radius * radius;
}

float calculate_circumference(float radius) {
    return TWO_PI * radius;
}
```

### Error Messages and Debugging
```c
#define DEBUG_ENABLED true
#define LOG_PREFIX "[RTMC] "
#define ERROR_INVALID_PARAM "Invalid parameter provided"
#define ERROR_MEMORY_FULL "Memory allocation failed"

void log_error(char* message) {
    if (DEBUG_ENABLED) {
        HW_UART_WRITE(LOG_PREFIX);
        HW_UART_WRITE(message);
    }
}
```

## Compilation Process

1. **Preprocessing Phase**: The preprocessor scans the source code for `#define` directives
2. **Definition Storage**: Macro definitions are stored in the preprocessor's symbol table
3. **Expansion**: All occurrences of defined identifiers are replaced with their values
4. **Parsing**: The expanded code is then parsed by the compiler

## Best Practices

### Naming Conventions
- Use ALL_CAPS for macro names to distinguish them from variables
- Use descriptive names that clearly indicate purpose
- Group related constants with common prefixes

```c
// Hardware pins
#define PIN_LED_STATUS 13
#define PIN_LED_ERROR 12
#define PIN_BUTTON_RESET 2

// Timing constants
#define TIMEOUT_SHORT_MS 100
#define TIMEOUT_MEDIUM_MS 500
#define TIMEOUT_LONG_MS 2000
```

### Organization
- Place `#define` statements at the top of files
- Group related definitions together
- Use comments to explain complex values

```c
// System configuration
#define SYSTEM_CLOCK_HZ 16000000  // 16 MHz system clock
#define BAUD_RATE 115200          // Serial communication rate

// Buffer sizes
#define RX_BUFFER_SIZE 256        // Receive buffer
#define TX_BUFFER_SIZE 128        // Transmit buffer
```

### Type Safety
While `#define` provides compile-time constants, consider using `const` variables for type safety when appropriate:

```c
// Using #define for compile-time constants
#define MAX_ITEMS 100

// Using const for type-safe constants
const int max_items = MAX_ITEMS;
```

## Limitations

1. **No Function-like Macros**: Currently only simple value substitution is supported
2. **No Conditional Compilation**: `#ifdef`, `#ifndef`, `#if` are not supported
3. **No Macro Arguments**: Parameterized macros are not supported
4. **Single Line Values**: Multi-line macro definitions are not supported

## Error Handling

The preprocessor will report errors for:
- Invalid `#define` syntax
- Missing macro names
- Circular references (future enhancement)

Example error:
```
Line 5: Invalid #define directive
```

## Integration with Existing Code

The `#define` feature integrates seamlessly with existing RT-Micro-C code:
- All existing syntax remains unchanged
- No performance impact on runtime execution
- Compatible with all language features (structs, unions, functions, etc.)

## Future Enhancements

Potential future additions to the preprocessor:
1. Function-like macros with parameters
2. Conditional compilation directives
3. Include guards
4. Macro expansion debugging tools
5. Built-in predefined macros (__FILE__, __LINE__, etc.)

## Conclusion

The `#define` preprocessor support in RT-Micro-C provides a powerful tool for creating maintainable, configurable embedded code. By following C-style preprocessor conventions, it enables familiar development patterns while maintaining the simplicity and efficiency of the RT-Micro-C language.
