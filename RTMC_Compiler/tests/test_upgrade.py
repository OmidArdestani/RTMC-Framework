#!/usr/bin/env python3
"""
Test script for the upgraded RT-Micro-C compiler
Tests the new struct layout and pointer features
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.semantic.struct_layout import StructLayoutTable, FieldLayout, StructLayout
from src.parser.ast_nodes import *
from src.bytecode.generator import BytecodeGenerator, CompileMode

def test_struct_layout():
    """Test the struct layout calculation"""
    print("Testing struct layout calculation...")
    
    # Create a simple struct
    # struct TestStruct {
    #     char a;
    #     int b;
    #     float c;
    # };
    
    fields = [
        FieldNode("a", PrimitiveTypeNode("char"), line=1),
        FieldNode("b", PrimitiveTypeNode("int"), line=2),
        FieldNode("c", PrimitiveTypeNode("float"), line=3)
    ]
    
    struct_decl = StructDeclNode("TestStruct", fields, line=1)
    
    # Create layout table and register struct
    layout_table = StructLayoutTable()
    layout_table.register_struct(struct_decl)
    
    # Calculate layout
    layout = layout_table.calculate_layout("TestStruct")
    
    print(f"Struct TestStruct:")
    print(f"  Total size: {layout.total_size} bytes")
    print(f"  Alignment: {layout.alignment} bytes")
    print(f"  Fields:")
    for name, field in layout.fields.items():
        print(f"    {name}: offset {field.offset}, size {field.size}")
    
    # Test nested struct
    print("\nTesting nested struct...")
    
    # struct NestedStruct {
    #     TestStruct base;
    #     int extra;
    # };
    
    nested_fields = [
        FieldNode("base", StructTypeNode("TestStruct"), line=1),
        FieldNode("extra", PrimitiveTypeNode("int"), line=2)
    ]
    
    nested_struct = StructDeclNode("NestedStruct", nested_fields, line=1)
    layout_table.register_struct(nested_struct)
    
    nested_layout = layout_table.calculate_layout("NestedStruct")
    
    print(f"Struct NestedStruct:")
    print(f"  Total size: {nested_layout.total_size} bytes")
    print(f"  Base struct: {nested_layout.base_struct}")
    print(f"  Fields:")
    for name, field in nested_layout.fields.items():
        print(f"    {name}: offset {field.offset}, size {field.size}")
    
    # Test inheritance check
    print(f"\nInheritance test:")
    print(f"  Is NestedStruct a substruct of TestStruct? {layout_table.is_substruct('NestedStruct', 'TestStruct')}")
    
    return True

def test_pointer_ast():
    """Test pointer AST nodes"""
    print("\nTesting pointer AST nodes...")
    
    # Create pointer type: int*
    base_type = PrimitiveTypeNode("int")
    pointer_type = PointerTypeNode(base_type, 1)
    
    # Create pointer declaration: int *ptr;
    pointer_decl = PointerDeclNode("ptr", base_type, 1, line=1)
    
    # Create address-of expression: &variable
    var_expr = IdentifierExprNode("variable")
    addr_expr = AddressOfNode(var_expr)
    
    # Create dereference expression: *ptr
    ptr_expr = IdentifierExprNode("ptr")
    deref_expr = DereferenceNode(ptr_expr)
    
    print(f"Pointer type: {pointer_type}")
    print(f"Pointer declaration: {pointer_decl}")
    print(f"Address-of expression: {addr_expr}")
    print(f"Dereference expression: {deref_expr}")
    
    return True

def test_compile_modes():
    """Test compilation modes"""
    print("\nTesting compilation modes...")
    
    # Test debug mode
    debug_generator = BytecodeGenerator(CompileMode.DEBUG)
    print(f"Debug mode: {debug_generator.mode}")
    
    # Test release mode
    release_generator = BytecodeGenerator(CompileMode.RELEASE)
    print(f"Release mode: {release_generator.mode}")
    
    return True

def test_bit_fields():
    """Test bit-field support"""
    print("\nTesting bit-field support...")
    
    # Create a struct with bit-fields
    # struct BitFieldStruct {
    #     int a : 4;
    #     int b : 8;
    #     int c : 20;
    # };
    
    fields = [
        FieldNode("a", PrimitiveTypeNode("int"), bit_width=4, line=1),
        FieldNode("b", PrimitiveTypeNode("int"), bit_width=8, line=2),
        FieldNode("c", PrimitiveTypeNode("int"), bit_width=20, line=3)
    ]
    
    struct_decl = StructDeclNode("BitFieldStruct", fields, line=1)
    
    # Create layout table and register struct
    layout_table = StructLayoutTable()
    layout_table.register_struct(struct_decl)
    
    # Calculate layout
    layout = layout_table.calculate_layout("BitFieldStruct")
    
    print(f"Bit-field struct BitFieldStruct:")
    print(f"  Total size: {layout.total_size} bytes")
    print(f"  Fields:")
    for name, field in layout.fields.items():
        if field.bit_width > 0:
            print(f"    {name}: offset {field.offset}, bit_offset {field.bit_offset}, bit_width {field.bit_width}")
        else:
            print(f"    {name}: offset {field.offset}, size {field.size}")
    
    # Test bit-field info retrieval
    bit_info = layout_table.get_bit_field_info("BitFieldStruct", "a")
    if bit_info:
        print(f"  Bit-field 'a' info: byte_offset={bit_info[0]}, bit_offset={bit_info[1]}, bit_width={bit_info[2]}")
    
    return True

def main():
    print("RT-Micro-C Compiler Upgrade Test")
    print("=" * 40)
    
    try:
        # Run tests
        test_struct_layout()
        test_pointer_ast()
        test_compile_modes()
        test_bit_fields()
        
        print("\n" + "=" * 40)
        print("All tests passed!")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
