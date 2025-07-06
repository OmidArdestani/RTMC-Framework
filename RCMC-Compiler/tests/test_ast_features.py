#!/usr/bin/env python3
"""
Test script to demonstrate the new AST features:
1. Fixed-length array declarations
2. Nested struct support

This shows how the AST nodes would be constructed for:
- int numbers[5] = {1, 2, 3, 4, 5};
- struct Point { int x; int y; };
- struct Rectangle { Point topLeft; Point bottomRight; };
"""

from src.parser.ast_nodes import *

def test_array_declaration():
    """Test array declaration with initializer"""
    print("=== Array Declaration Test ===")
    
    # Create array literal: {1, 2, 3, 4, 5}
    elements = [
        LiteralExprNode(1, "int"),
        LiteralExprNode(2, "int"),
        LiteralExprNode(3, "int"),
        LiteralExprNode(4, "int"),
        LiteralExprNode(5, "int")
    ]
    array_literal = ArrayLiteralNode(elements)
    
    # Create array declaration: int numbers[5] = {1, 2, 3, 4, 5};
    element_type = PrimitiveTypeNode("int")
    array_decl = ArrayDeclNode("numbers", element_type, 5, array_literal)
    
    print("Array Declaration AST:")
    print(ast_to_string(array_decl))
    print()

def test_array_access():
    """Test array access expression"""
    print("=== Array Access Test ===")
    
    # Create array access: numbers[2]
    array_var = IdentifierExprNode("numbers")
    index_expr = LiteralExprNode(2, "int")
    array_access = ArrayAccessNode(array_var, index_expr)
    
    print("Array Access AST:")
    print(ast_to_string(array_access))
    print()

def test_nested_struct():
    """Test nested struct declarations"""
    print("=== Nested Struct Test ===")
    
    # Create Point struct: struct Point { int x; int y; };
    point_fields = [
        FieldNode("x", PrimitiveTypeNode("int")),
        FieldNode("y", PrimitiveTypeNode("int"))
    ]
    point_struct = StructDeclNode("Point", point_fields)
    
    # Create Rectangle struct with nested Point fields
    rectangle_fields = [
        FieldNode("topLeft", StructTypeNode("Point")),
        FieldNode("bottomRight", StructTypeNode("Point"))
    ]
    rectangle_struct = StructDeclNode("Rectangle", rectangle_fields)
    
    print("Point Struct AST:")
    print(ast_to_string(point_struct))
    
    print("Rectangle Struct AST:")
    print(ast_to_string(rectangle_struct))
    print()

def test_nested_member_access():
    """Test nested member access: rect.topLeft.x"""
    print("=== Nested Member Access Test ===")
    
    # Create nested member access: rect.topLeft.x
    rect_var = IdentifierExprNode("rect")
    top_left_access = MemberExprNode(rect_var, "topLeft", computed=False)
    x_access = MemberExprNode(top_left_access, "x", computed=False)
    
    print("Nested Member Access AST:")
    print(ast_to_string(x_access))
    print()

def test_complex_example():
    """Test a complex example combining arrays and nested structs"""
    print("=== Complex Example Test ===")
    
    # Array of Points: Point points[3] = {{0, 0}, {1, 1}, {2, 2}};
    point_literals = []
    for i in range(3):
        elements = [
            LiteralExprNode(i, "int"),  # x coordinate
            LiteralExprNode(i, "int")   # y coordinate
        ]
        point_literals.append(ArrayLiteralNode(elements))
    
    points_array_literal = ArrayLiteralNode(point_literals)
    point_type = StructTypeNode("Point")
    points_array_decl = ArrayDeclNode("points", point_type, 3, points_array_literal)
    
    print("Array of Points Declaration AST:")
    print(ast_to_string(points_array_decl))
    
    # Access: points[1].y
    points_var = IdentifierExprNode("points")
    index_1 = LiteralExprNode(1, "int")
    array_element = ArrayAccessNode(points_var, index_1)
    y_member = MemberExprNode(array_element, "y", computed=False)
    
    print("Complex Access (points[1].y) AST:")
    print(ast_to_string(y_member))
    print()

if __name__ == "__main__":
    print("Testing New AST Features for RT-Micro-C Compiler")
    print("=" * 50)
    print()
    
    test_array_declaration()
    test_array_access()
    test_nested_struct()
    test_nested_member_access()
    test_complex_example()
    
    print("All tests completed successfully!")
