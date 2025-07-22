# RT-Micro-C Compiler Upgrade Documentation

## Overview

The RT-Micro-C compiler has been upgraded with 5 major new features to improve struct handling, add pointer support, enable C-style inheritance, fix debug information, and add compilation modes.

## 1. Fixed Struct Offset Resolution and Size Calculation

### Problem Solved
Previously, the compiler used hardcoded field offsets and returned a fixed 16-byte size for all structs. This has been completely rewritten.

### New Features
- **Accurate struct size calculation**: Structs now have their actual size computed based on field sizes and alignment requirements
- **Proper field offset calculation**: Field offsets are calculated considering data alignment and nested structs
- **Bit-field support**: Bit-fields are properly packed and aligned with correct bit offset tracking
- **Nested struct support**: Structs containing other structs are handled correctly

### Implementation Details
- New `StructLayoutTable` class manages all struct layout information
- Field offsets are computed with proper alignment (1-byte for char, 4-byte for int/float, 8-byte for pointers)
- Bit-fields are packed into bytes with proper bit offset tracking
- Struct inheritance is detected automatically when the first field is another struct type

### Example
```c
struct InnerStruct {
    char a;      // offset 0, size 1
    int b;       // offset 4, size 4 (aligned to 4-byte boundary)
};               // total size: 8 bytes

struct OuterStruct {
    InnerStruct inner;  // offset 0, size 8
    float value;        // offset 8, size 4
};                      // total size: 12 bytes
```

## 2. Pointer and Pointer-to-Pointer Support

### New Syntax Supported
```c
int a = 10;
int *b = &a;          // Single pointer
int **c = &b;         // Double pointer
int d = **c;          // Dereference double pointer
```

### AST Nodes Added
- `PointerTypeNode`: Represents pointer types with level support (*, **, etc.)
- `PointerDeclNode`: Extends VariableDeclNode for pointer declarations
- `AddressOfNode`: Represents address-of operator (&)
- `DereferenceNode`: Represents dereference operator (*)

### Bytecode Instructions Added
- `LOAD_ADDR <var>`: Load address of a variable onto stack
- `LOAD_DEREF`: Dereference pointer on stack
- `STORE_DEREF`: Store value at address pointed to by stack value

### Type System
- Pointers are 8 bytes (64-bit)
- Pointer arithmetic is supported
- Type checking ensures & and * operations are balanced

## 3. Structure Inheritance (C-style)

### Feature Description
Allows struct A to be included as the first field in struct B to simulate inheritance.

### Example
```c
struct Base {
    int id;
    char status;
};

struct Derived {
    Base base;           // First field creates inheritance
    float extra_data;
};
```

### Implementation
- When the first field of a struct is another struct type, inheritance is automatically detected
- The base struct field is placed at offset 0
- `get_base_struct()` and `is_substruct()` functions provide inheritance queries
- Enables casting from Derived* to Base* at runtime

### Benefits
- Enables object-oriented programming patterns in C
- Supports polymorphism through base pointer casting
- Maintains C compatibility

## 4. Fixed Line Numbers in Bytecode Debug Info

### Problem Solved
Previously, all bytecode instructions had line = 0, making debugging impossible.

### New Features
- Every AST node now carries accurate line and column information
- Bytecode instructions embed source line numbers
- Debug info table maps instruction addresses to source lines
- Enhanced error reporting with precise source locations

### Implementation
- `ASTNode` base class now accepts line and column parameters
- `BytecodeGenerator.emit()` propagates line numbers to instructions
- `Instruction` class enhanced with column support
- Debug info table: `Dict[int, int]` mapping instruction_index → source_line

### Example Debug Output
```
Instruction 0x0010: LOAD_VAR 2    // Line 15, Column 8
Instruction 0x0011: LOAD_CONST 0  // Line 15, Column 12
Instruction 0x0012: ADD           // Line 15, Column 11
```

## 5. Debug and Release Modes for Bytecode Generation

### Compilation Modes
- **Debug Mode** (default): Includes all debug information
- **Release Mode**: Strips debug information for smaller, faster code

### Debug Mode Features
- Full symbol names preserved
- Line numbers embedded in instructions
- Struct field metadata included
- Comment instructions for documentation
- Complete debug info table

### Release Mode Features
- Debug information stripped
- Smaller bytecode files
- Faster execution (no debug overhead)
- Compressed constant pool (planned)

### Usage
```bash
# Debug mode (default)
python main.py source.rtmc

# Release mode
python main.py --release source.rtmc
```

### Implementation
- `CompileMode` enum: DEBUG, RELEASE
- `BytecodeGenerator` accepts mode parameter
- Debug info generation wrapped in `if mode == CompileMode.DEBUG`
- `.vmb` header includes compilation mode

## API Reference

### New Classes

#### StructLayoutTable
```python
class StructLayoutTable:
    def register_struct(self, struct_decl: StructDeclNode)
    def calculate_layout(self, struct_name: str) -> StructLayout
    def get_field_offset(self, struct_name: str, field_path: str) -> int
    def get_bit_field_info(self, struct_name: str, field_path: str) -> Optional[Tuple[int, int, int]]
    def get_struct_size(self, struct_name: str) -> int
    def get_base_struct(self, struct_name: str) -> Optional[str]
    def is_substruct(self, child_struct: str, base_struct: str) -> bool
```

#### Enhanced BytecodeGenerator
```python
class BytecodeGenerator:
    def __init__(self, mode: CompileMode = CompileMode.DEBUG)
    def set_current_position(self, line: int, column: int = 0)
    def emit(self, instruction: Instruction)  # Now includes line tracking
```

### New AST Nodes

#### PointerTypeNode
```python
class PointerTypeNode(TypeNode):
    def __init__(self, base_type: TypeNode, pointer_level: int = 1, line: int = 0, column: int = 0)
```

#### AddressOfNode
```python
class AddressOfNode(ExpressionNode):
    def __init__(self, operand: ExpressionNode, line: int = 0, column: int = 0)
```

#### DereferenceNode
```python
class DereferenceNode(ExpressionNode):
    def __init__(self, operand: ExpressionNode, line: int = 0, column: int = 0)
```

## Migration Guide

### For Existing Code
1. Existing struct declarations will automatically benefit from accurate size calculation
2. No changes needed for basic struct usage
3. Bit-fields will be properly packed instead of using fixed offsets

### For New Code
1. Use pointer syntax: `int *ptr = &variable;`
2. Use struct inheritance: Place base struct as first field
3. Use `--release` flag for production builds
4. Enhanced debugging information available in debug mode

## Performance Impact

### Debug Mode
- Slightly larger bytecode due to debug information
- Minimal runtime overhead for debug info
- Better debugging experience

### Release Mode
- Smaller bytecode files
- Faster execution (no debug overhead)
- Optimized for production use

### Struct Operations
- More accurate but potentially slower size calculations
- Better memory utilization due to proper alignment
- Improved performance for nested struct operations

## Testing

Run the comprehensive test suite:
```bash
python test_upgrade.py
```

This tests:
- Struct layout calculation
- Pointer AST nodes
- Compilation modes
- Bit-field support
- Inheritance detection

## Future Enhancements

### Planned Features
1. Constant pool compression in release mode
2. Advanced pointer arithmetic optimizations
3. Multiple inheritance support
4. Enhanced debug symbols with variable names
5. Source map generation for debugging

### Extension Points
- `StructLayoutTable` can be extended for custom alignment strategies
- `CompileMode` enum can be extended with additional modes
- Instruction set can be extended with more pointer operations

## Examples

See `examples/new_features_demo.rtmc` for a comprehensive example demonstrating all new features.

## Conclusion

These upgrades significantly enhance the RT-Micro-C compiler's capabilities:
- Accurate struct handling enables complex data structures
- Pointer support enables advanced memory management
- C-style inheritance enables object-oriented patterns
- Debug information improves development experience
- Compilation modes optimize for different use cases

The upgrades maintain backward compatibility while adding powerful new features for embedded systems development.
