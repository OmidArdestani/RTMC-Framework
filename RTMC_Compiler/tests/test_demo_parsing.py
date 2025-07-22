#!/usr/bin/env python3
"""
Test script to parse the comprehensive arrays_and_structs_demo.rtmc file
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.tokenizer import Tokenizer
from src.parser.parser import Parser
from src.parser.ast_nodes import ast_to_string

def test_demo_file():
    """Test parsing the complete demo file"""
    print("=== Testing arrays_and_structs_demo.rtmc ===")
    
    # Read the demo file
    try:
        with open("examples/arrays_and_structs_demo.rtmc", "r") as f:
            source_code = f.read()
    except FileNotFoundError:
        print("Demo file not found. Make sure arrays_and_structs_demo.rtmc exists in examples/")
        return
    
    print(f"Source code length: {len(source_code)} characters")
    print(f"Number of lines: {len(source_code.splitlines())}")
    print()
    
    try:
        # Tokenize
        print("Step 1: Tokenizing...")
        tokenizer = Tokenizer(source_code)
        tokens = tokenizer.tokenize()
        print(f"Generated {len(tokens)} tokens")
        
        # Parse
        print("Step 2: Parsing...")
        parser = Parser(tokens)
        ast = parser.parse()
        print("Parsing completed successfully!")
        
        # Analyze AST structure
        print("Step 3: Analyzing AST...")
        ast_string = ast_to_string(ast)
        
        # Count different node types
        array_decls = ast_string.count("ArrayDecl:")
        struct_decls = ast_string.count("StructDecl:")
        function_decls = ast_string.count("FunctionDecl:")
        array_accesses = ast_string.count("ArrayAccess:")
        member_exprs = ast_string.count("MemberExpr:")
        
        print(f"AST Analysis:")
        print(f"  - Array Declarations: {array_decls}")
        print(f"  - Struct Declarations: {struct_decls}")
        print(f"  - Function Declarations: {function_decls}")
        print(f"  - Array Accesses: {array_accesses}")
        print(f"  - Member Expressions: {member_exprs}")
        print()
        
        # Show first part of AST
        lines = ast_string.split('\n')
        print("First 50 lines of AST:")
        print("=" * 40)
        for i, line in enumerate(lines[:50]):
            print(f"{i+1:2d}: {line}")
        
        if len(lines) > 50:
            print(f"... ({len(lines) - 50} more lines)")
        
        print("=" * 40)
        print("✅ Demo file parsed successfully!")
        
    except Exception as e:
        print(f"❌ Error parsing demo file: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Show some context around the error
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

def test_specific_features():
    """Test specific language features from the demo"""
    print("\n=== Testing Specific Language Features ===")
    
    # Test 1: Simple array declaration
    test_cases = [
        ("Array with initializer", 'int numbers[5] = {1, 2, 3, 5, 8};'),
        ("Array without initializer", 'float coordinates[3];'),
        ("Struct array", 'Point vertices[4];'),
        ("Nested struct definition", '''
            struct Rectangle {
                Point topLeft;
                Point bottomRight;
                int color;
            };
        '''),
        ("Complex access", '''
            void test() {
                windows[0].bounds.topLeft.x = 10;
            }
        '''),
        ("Array access in loop", '''
            void test() {
                for (int i = 0; i < 4; i = i + 1) {
                    vertices[i].x = coordinates[i] * 10;
                }
            }
        ''')
    ]
    
    for name, code in test_cases:
        print(f"\nTesting: {name}")
        print("-" * 30)
        try:
            tokenizer = Tokenizer(code)
            tokens = tokenizer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            print("✅ Parsed successfully!")
            
            # Show a compact AST representation
            ast_str = ast_to_string(ast)
            lines = ast_str.split('\n')
            for line in lines[:10]:  # Show first 10 lines
                if line.strip():
                    print(f"  {line}")
            if len(lines) > 10:
                print(f"  ... ({len(lines) - 10} more lines)")
                
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    print("Testing RT-Micro-C Array and Struct Features")
    print("=" * 60)
    
    test_demo_file()
    test_specific_features()
    
    print("\n" + "=" * 60)
    print("Testing completed!")
