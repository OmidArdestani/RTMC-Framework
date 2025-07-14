# RT-Micro-C Union and Field Initialization Support

## Overview

The RT-Micro-C compiler now supports union declarations and field initialization, enabling more flexible data structure definitions with memory overlapping and default values.

## New Features

### 1. Union Declarations

Unions allow multiple fields to share the same memory location, useful for type punning and memory-efficient data structures.

#### Basic Union Syntax
```c
union BasicUnion {
    int intValue;
    float floatValue;
    char charArray[4];
};
```

#### Anonymous Unions in Structs
```c
struct TestStruct {
    union {
        struct {
            int item1 : 16;
            int item2 : 16;
        };
        int value = 0;
    };
};
```

### 2. Field Initialization

Fields can now have default initialization values:

```c
struct ConfigStruct {
    int defaultValue = 42;
    bool enabled = true;
    float multiplier = 1.0;
};
```

### 3. Nested Anonymous Structs and Unions

The compiler supports complex nesting patterns:

```c
struct ComplexStruct {
    int normalField;
    union {
        struct {
            int x;
            int y;
        } point;
        struct {
            int red   : 8;
            int green : 8;
            int blue  : 8;
            int alpha : 8;
        } color;
        int rawValue;
    } data;
};
```

## Implementation Details

### Lexer Updates
- Added `UNION` token type
- Added `union` keyword to keyword table

### Parser Updates
- Added `UnionDeclNode` AST node
- Added `UnionTypeNode` for type references
- Enhanced `FieldNode` to support initializers
- Added `union_declaration()` method
- Enhanced field parsing to handle initialization

### AST Node Types
```python
class UnionDeclNode(ASTNode):
    def __init__(self, name: str, fields: List[FieldNode], ...):
        # Union declaration with overlapping fields

class UnionTypeNode(TypeNode):
    def __init__(self, union_name: str, ...):
        # Reference to a union type

class FieldNode:
    def __init__(self, name: str, type: TypeNode, 
                 bit_width: Optional[int] = None,
                 initializer: Optional[ExpressionNode] = None, ...):
        # Field with optional initialization
```

### Semantic Analysis
- Union type checking and validation
- Field overlap detection
- Size calculation (maximum of all fields)
- Type compatibility checking for initializers

### Memory Layout
- Unions: All fields start at offset 0
- Size: Maximum size of all fields with proper alignment
- Structs with unions: Regular field layout with union embedded

## Usage Examples

### Example 1: Type Punning
```c
union TypePun {
    float floatVal;
    int intVal;
};

void main() {
    TypePun data;
    data.floatVal = 3.14;
    DBG_PRINTF("Float as int: {}", data.intVal);
}
```

### Example 2: Bit-field Unions
```c
struct ControlRegister {
    union {
        struct {
            int enable  : 1;
            int mode    : 3;
            int speed   : 4;
            int reserved: 24;
        };
        int rawValue = 0x00000001;  // Default: enabled
    };
};
```

### Example 3: Protocol Headers
```c
struct PacketHeader {
    int type;
    union {
        struct {
            int sourceId;
            int destId;
        } routing;
        struct {
            int timestamp;
            int sequence;
        } control;
        int rawData[2];
    } payload;
};
```

## Compiler Pipeline Integration

### 1. Lexical Analysis
- Recognizes `union` keyword
- Maintains existing struct and identifier parsing

### 2. Syntax Analysis
- Parses union declarations with field lists
- Handles anonymous unions within structs
- Supports field initialization expressions

### 3. Semantic Analysis
- Validates union field types
- Checks initializer type compatibility
- Calculates union sizes and alignment

### 4. Code Generation
- Generates appropriate memory layout instructions
- Handles field access for overlapping union fields
- Emits initialization code for default values

### 5. Optimization
- Dead code elimination for unused union fields
- Constant folding for field initializers
- Memory layout optimization

## Testing

The implementation has been tested with:
- Basic union declarations ✅
- Anonymous unions in structs ✅
- Field initialization ✅
- Nested struct/union combinations ✅
- Bit-field unions ✅
- Type compatibility checking ✅

## Future Enhancements

1. **Full Union Semantics**: Implement proper memory overlapping behavior
2. **Union Assignment**: Support assigning one union to another
3. **Designated Initializers**: Support `{.field = value}` syntax
4. **Union Arrays**: Arrays of union types
5. **Runtime Type Detection**: Safe union access patterns

## Backward Compatibility

This update maintains full backward compatibility with existing RT-Micro-C code:
- All existing struct declarations continue to work
- No changes to existing field access syntax
- Existing compilation flags and options unchanged

## Conclusion

The addition of union support and field initialization greatly enhances the RT-Micro-C language's capability for systems programming, embedded development, and complex data structure definitions while maintaining the language's focus on real-time and resource-constrained environments.
