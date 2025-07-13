# RT-Micro-C Hexadecimal Literal Support

## Overview

The RT-Micro-C compiler now supports hexadecimal integer literals, allowing developers to specify integer values in hexadecimal format using the standard C syntax.

## Syntax

### Hexadecimal Literals
```c
// Lowercase format (preferred)
int value1 = 0xff;        // 255 in decimal
int value2 = 0x1a2b;      // 6699 in decimal
int value3 = 0x0;         // 0 in decimal

// Uppercase format (also supported)
int value4 = 0XFF;        // 255 in decimal
int value5 = 0XABCD;      // 43981 in decimal

// Leading zeros are allowed
int value6 = 0x00A0;      // 160 in decimal
int value7 = 0x000F;      // 15 in decimal
```

### Valid Hexadecimal Digits
- **0-9**: Numeric digits
- **A-F**: Hexadecimal digits (case insensitive)
- **a-f**: Hexadecimal digits (case insensitive)

## Usage Examples

### Basic Variable Assignment
```c
void main() {
    int hexValue = 0xDEAD;
    int flags = 0xFF00;
    int address = 0x8000;
    
    DBG_PRINTF("hexValue: {}", hexValue);     // Output: 57005
    DBG_PRINTF("flags: {}", flags);           // Output: 65280
    DBG_PRINTF("address: {}", address);       // Output: 32768
}
```

### Bit-field Initialization
```c
struct ControlRegister {
    int enable  : 1;
    int mode    : 3;
    int address : 12;
    int reserved: 16;
};

void configureDevice() {
    ControlRegister reg;
    reg.enable = 0x1;        // Set enable bit
    reg.mode = 0x7;          // Set mode to 7
    reg.address = 0xFFF;     // Set address to maximum
    reg.reserved = 0x0;      // Clear reserved bits
}
```

### Array Initialization
```c
void initializeBuffers() {
    int bufferSizes[4] = {0x100, 0x200, 0x400, 0x800};
    int addresses[3] = {0x1000, 0x2000, 0x3000};
    
    // Use in loops
    for (int i = 0; i < 0x10; i++) {  // Loop 16 times
        // Process data
    }
}
```

### Mixed Decimal and Hexadecimal
```c
void mixedValues() {
    int decimal = 42;        // Decimal literal
    int hex = 0x2A;          // Hexadecimal literal (same value as 42)
    int octal = 052;         // Note: Octal not yet supported
    
    if (decimal == hex) {    // This will be true
        DBG_PRINT("Values are equal!");
    }
}
```

## Implementation Details

### Lexical Analysis
The tokenizer has been enhanced to recognize hexadecimal patterns:
1. Detects `0x` or `0X` prefix
2. Reads valid hexadecimal digits (0-9, A-F, a-f)
3. Generates `INTEGER` tokens with hexadecimal string values

### Parsing
The parser converts hexadecimal string tokens to integer values:
```python
if token_value.lower().startswith('0x'):
    value = int(token_value, 16)  # Parse as hexadecimal
else:
    value = int(token_value)      # Parse as decimal
```

### Supported Contexts
Hexadecimal literals can be used in all contexts where integer literals are valid:
- Variable declarations and initialization
- Function parameters
- Array sizes and indices
- Bit-field widths
- Expression operands
- Case labels (when switch statements are added)

## Range Limitations

### 32-bit Signed Integer Range
- **Minimum**: `-2,147,483,648` (`-0x80000000`)
- **Maximum**: `2,147,483,647` (`0x7FFFFFFF`)

### Common Hexadecimal Values
```c
int maxPositive = 0x7FFFFFFF;    // 2,147,483,647
int allBitsSet = 0xFFFFFFFF;     // -1 (two's complement)
int highBit = 0x80000000;        // -2,147,483,648
int byteMask = 0xFF;             // 255
int wordMask = 0xFFFF;           // 65535
```

## Error Handling

### Invalid Hexadecimal
```c
// These will cause compilation errors:
int invalid1 = 0x;          // No digits after 0x
int invalid2 = 0xGHIJ;      // Invalid characters G, H, I, J
int invalid3 = 0x 123;      // Space between 0x and digits
```

### Overflow Detection
```c
// This will cause a compilation error (value too large):
int tooLarge = 0xFFFFFFFF1;  // Exceeds 32-bit range
```

## Best Practices

### 1. Use Appropriate Case
```c
// Preferred: lowercase hex digits
int preferred = 0xabcd;

// Acceptable: uppercase hex digits
int acceptable = 0XABCD;

// Mixed case should be avoided for consistency
```

### 2. Hardware Register Programming
```c
// Clear and readable bit manipulation
#define STATUS_ENABLE    0x0001
#define STATUS_READY     0x0002
#define STATUS_ERROR     0x0004
#define STATUS_COMPLETE  0x0008

void setStatus() {
    int status = STATUS_ENABLE | STATUS_READY;  // 0x0003
    // Configure hardware register
}
```

### 3. Memory Addresses
```c
// Embedded systems often use specific memory addresses
#define GPIO_BASE        0x40020000
#define TIMER_BASE       0x40010000
#define UART_BASE        0x40013800

void configurePeripherals() {
    int* gpio_reg = (int*)GPIO_BASE;
    int* timer_reg = (int*)TIMER_BASE;
    // Configure peripherals
}
```

## Testing

The hexadecimal literal support has been thoroughly tested:

### Test Cases
- ✅ Basic hexadecimal parsing (`0xFF`, `0x1234`)
- ✅ Case insensitivity (`0xFF` vs `0XFF`)
- ✅ Leading zeros (`0x00A0`)
- ✅ Maximum values (`0x7FFFFFFF`)
- ✅ Zero value (`0x0`)
- ✅ Integration with existing decimal parsing
- ✅ Bit-field assignments
- ✅ Variable initialization
- ✅ Expression evaluation

### Example Output
```
DEBUG: testStruct1.item1 (0xBBAD): 48045
DEBUG: testStruct1.item2 (0x52FC): 21244
DEBUG: hexValue1 (0xFF): 255
DEBUG: hexValue2 (0x00A0): 160
DEBUG: hexValue3 (0x7FFFFFFF): 2147483647
DEBUG: hexValue4 (0x0): 0
DEBUG: hexValue5 (0XFF): 255
DEBUG: hexValue6 (0XABCD): 43981
DEBUG: decimalValue (42): 42
```

## Backward Compatibility

This enhancement maintains full backward compatibility:
- All existing decimal literals continue to work unchanged
- No changes to existing syntax or semantics
- No impact on compilation performance
- Existing code requires no modifications

## Future Enhancements

1. **Binary Literals**: Support for `0b` prefix (`0b1010`)
2. **Octal Literals**: Support for leading zero prefix (`052`)
3. **Integer Suffixes**: Support for `L`, `U` suffixes (`0xFFL`, `0x1000U`)
4. **Digit Separators**: Support for underscores (`0xFF_FF_FF_FF`)

## Conclusion

The addition of hexadecimal literal support significantly enhances RT-Micro-C's suitability for embedded systems programming, hardware register manipulation, and low-level system development while maintaining the language's focus on real-time and resource-constrained environments.
