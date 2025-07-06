# RT-Micro-C Compiler: Array and Nested Struct Features

## Overview

This document describes the implementation of two major new features for the RT-Micro-C compiler:

1. **Fixed-Length Arrays** - Support for declaring and manipulating arrays with compile-time known sizes
2. **Nested Struct Definitions** - Support for defining structs that contain other struct types as fields

## Feature 1: Fixed-Length Arrays

### Language Syntax

Arrays in RT-Micro-C follow C-style syntax:

```c
// Basic array declarations
int numbers[5];
float values[10];
char buffer[256];

// Array declarations with initializers
int fibonacci[6] = {1, 1, 2, 3, 5, 8};
float coords[3] = {1.0, 2.5, 3.7};

// Struct arrays
struct Point points[4];
struct Sensor sensors[8] = {{0, 0}, {1, 1}, {2, 2}};
```

### AST Implementation

#### New Node Types

1. **ArrayDeclNode** - Represents array variable declarations
   ```python
   class ArrayDeclNode(ASTNode):
       name: str                    # Variable name
       element_type: TypeNode       # Type of array elements  
       size: int                    # Fixed array size
       initializer: Optional[ExpressionNode]  # Optional initializer
   ```

2. **ArrayLiteralNode** - Represents array initializer lists
   ```python
   class ArrayLiteralNode(ExpressionNode):
       elements: List[ExpressionNode]  # Array element expressions
   ```

3. **ArrayAccessNode** - Represents indexed array access
   ```python
   class ArrayAccessNode(ExpressionNode):
       array: ExpressionNode    # Array being accessed
       index: ExpressionNode    # Index expression
   ```

#### Usage Examples

```python
# int numbers[5] = {1, 2, 3, 4, 5};
elements = [LiteralExprNode(i, "int") for i in range(1, 6)]
array_literal = ArrayLiteralNode(elements)
array_decl = ArrayDeclNode("numbers", PrimitiveTypeNode("int"), 5, array_literal)

# numbers[2]
array_var = IdentifierExprNode("numbers")
index = LiteralExprNode(2, "int")
access = ArrayAccessNode(array_var, index)
```

### Semantic Analysis Requirements

1. **Size Validation**: Array size must be a positive integer constant
2. **Type Checking**: All initializer elements must match the declared element type
3. **Bounds Checking**: Initializer list length must not exceed declared size
4. **Memory Layout**: Calculate total memory requirements for arrays

### Bytecode Generation

#### New Instructions
- `ALLOC_ARRAY <type> <size>` - Allocate array memory
- `LOAD_ARRAY_ELEM <base> <index>` - Load array element
- `STORE_ARRAY_ELEM <base> <index>` - Store array element
- `INIT_ARRAY <count>` - Initialize array with stack values

#### Example Bytecode
```asm
; int numbers[5] = {1, 2, 3, 4, 5};
ALLOC_ARRAY int 5
LOAD_CONST 1
LOAD_CONST 2
LOAD_CONST 3
LOAD_CONST 4
LOAD_CONST 5
INIT_ARRAY 5

; numbers[2]
LOAD_VAR numbers
LOAD_CONST 2
LOAD_ARRAY_ELEM
```

## Feature 2: Nested Struct Definitions

### Language Syntax

Structs can contain other struct types as fields:

```c
// Basic struct
struct Point {
    int x;
    int y;
};

// Nested struct
struct Rectangle {
    Point topLeft;
    Point bottomRight;
    int color;
};

// Deeply nested
struct Window {
    Rectangle bounds;
    Point center;
    int zOrder;
};
```

### AST Implementation

#### Enhanced FieldNode

```python
class FieldNode:
    name: str               # Field name
    type: TypeNode          # Field type (can be StructTypeNode)
    bit_width: Optional[int]  # For bitfields
    offset: Optional[int]   # Calculated during semantic analysis
```

#### Nested Access Support

The existing `MemberExprNode` already supports chaining for nested access:

```python
# rect.topLeft.x
rect_var = IdentifierExprNode("rect")
top_left = MemberExprNode(rect_var, "topLeft", computed=False)
x_access = MemberExprNode(top_left, "x", computed=False)
```

### Semantic Analysis Requirements

1. **Type Resolution**: Ensure nested struct types exist before use
2. **Circular Reference Detection**: Prevent struct A containing struct A
3. **Offset Calculation**: Calculate field offsets accounting for nested structs
4. **Size Calculation**: Total struct size including nested structs

#### Offset Calculation Algorithm

```python
def calculate_struct_layout(struct_decl, type_registry):
    offset = 0
    for field in struct_decl.fields:
        field.offset = offset
        if isinstance(field.type, StructTypeNode):
            nested_struct = type_registry[field.type.struct_name]
            field_size = calculate_struct_size(nested_struct, type_registry)
        else:
            field_size = get_primitive_size(field.type.type_name)
        offset += field_size
    return offset
```

### Bytecode Generation

#### Nested Member Access
For `rect.topLeft.x`:

**Option 1: Chained Access**
```asm
LOAD_VAR rect
LOAD_STRUCT_MEMBER topLeft_offset
LOAD_STRUCT_MEMBER x_offset
```

**Option 2: Flattened Access** (Preferred)
```asm
LOAD_VAR rect
LOAD_STRUCT_MEMBER_NESTED topLeft.x_total_offset
```

#### New Instructions
- `LOAD_STRUCT_MEMBER_NESTED <total_offset>` - Direct nested field access
- `STORE_STRUCT_MEMBER_NESTED <total_offset>` - Direct nested field store

## Integration with Existing Compiler

### Parser Changes Required

1. **Grammar Updates**:
   ```
   declaration: variable_decl | array_decl | struct_decl | function_decl
   array_decl: type IDENTIFIER '[' INT_LITERAL ']' ('=' array_literal)? ';'
   array_literal: '{' expression_list '}'
   primary_expr: IDENTIFIER | literal | array_access | '(' expression ')'
   array_access: postfix_expr '[' expression ']'
   ```

2. **Lexer Token Support**:
   - Already supports `[`, `]`, `{`, `}` tokens
   - No new tokens required

### Semantic Analyzer Updates

1. **Symbol Table Enhancements**:
   ```python
   class SymbolInfo:
       name: str
       type: TypeNode
       is_array: bool = False
       array_size: Optional[int] = None
       offset: int = 0
   ```

2. **Type Checking**:
   - Validate array bounds and initializer compatibility
   - Resolve nested struct types and calculate layouts
   - Detect circular dependencies in struct definitions

### Bytecode Generator Updates

1. **Memory Management**:
   - Stack-based array allocation
   - Efficient nested struct field access
   - Bounds checking for array operations

2. **Optimization Opportunities**:
   - Constant propagation for array indices
   - Flattened offset calculation for nested structs
   - Dead code elimination for unused array elements

### Virtual Machine Updates

1. **Memory Model**:
   ```python
   class VMStack:
       def alloc_array(self, element_type, size):
           total_size = get_type_size(element_type) * size
           array_base = self.allocate(total_size)
           return array_base
       
       def get_array_element(self, base, index, element_size):
           return base + (index * element_size)
   ```

2. **Runtime Checks**:
   - Array bounds checking
   - Null pointer validation for nested structs

## Example Usage

### Complete Example: 2D Point Array

```c
// RT-Micro-C source code
struct Point {
    int x;
    int y;
};

struct Polygon {
    Point vertices[4];
    int numVertices;
};

task DrawingTask(core: 0, priority: 10) {
    Polygon square;
    
    void run() {
        // Initialize square vertices
        square.vertices[0] = {0, 0};
        square.vertices[1] = {10, 0};
        square.vertices[2] = {10, 10};
        square.vertices[3] = {0, 10};
        square.numVertices = 4;
        
        // Access vertex coordinates
        int firstX = square.vertices[0].x;
        int lastY = square.vertices[3].y;
    }
}
```

### Generated AST Structure

```python
# Point struct
point_fields = [
    FieldNode("x", PrimitiveTypeNode("int"), offset=0),
    FieldNode("y", PrimitiveTypeNode("int"), offset=4)
]
point_struct = StructDeclNode("Point", point_fields)

# Polygon struct with array field
polygon_fields = [
    FieldNode("vertices", ArrayTypeNode(StructTypeNode("Point"), 4), offset=0),
    FieldNode("numVertices", PrimitiveTypeNode("int"), offset=32)
]
polygon_struct = StructDeclNode("Polygon", polygon_fields)

# Array access: square.vertices[0].x
square_var = IdentifierExprNode("square")
vertices_access = MemberExprNode(square_var, "vertices")
index_0 = LiteralExprNode(0, "int")
vertex_access = ArrayAccessNode(vertices_access, index_0)
x_access = MemberExprNode(vertex_access, "x")
```

## Testing Strategy

1. **Unit Tests**: Test individual AST node creation and manipulation
2. **Integration Tests**: Test parsing, semantic analysis, and code generation
3. **End-to-End Tests**: Compile and execute RT-Micro-C programs using new features
4. **Error Handling**: Test invalid array sizes, undefined struct types, circular references

## Performance Considerations

1. **Compile Time**:
   - Efficient struct layout calculation algorithms
   - Memoization of type size calculations
   - Early detection of circular dependencies

2. **Runtime Performance**:
   - Direct offset calculation for nested access
   - Bounds checking optimization
   - Memory layout optimization for cache efficiency

## Future Enhancements

1. **Dynamic Arrays**: Support for runtime-sized arrays
2. **Array Operations**: Built-in functions for array manipulation
3. **Struct Inheritance**: Support for struct inheritance relationships
4. **Memory Alignment**: Automatic field alignment for optimal performance

This implementation provides a solid foundation for array and nested struct support in the RT-Micro-C compiler while maintaining compatibility with the existing codebase.
