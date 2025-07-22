#!/usr/bin/env python3
"""
Simple test for arrays_and_structs_demo.rtmc
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.tokenizer import Tokenizer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.bytecode.generator import BytecodeGenerator

def test_demo_file():
    """Test the arrays_and_structs_demo.rtmc file"""
    
    file_path = "examples/arrays_and_structs_demo.rtmc"
    print(f"Testing {file_path}...")
    
    try:
        # Read source
        with open(file_path, 'r') as f:
            source = f.read()
        
        print(f"Source: {len(source)} characters, {len(source.splitlines())} lines")
        
        # Tokenize
        print("Tokenizing...")
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        print(f"Generated {len(tokens)} tokens")
        
        # Parse
        print("Parsing...")
        parser = Parser(tokens)
        ast = parser.parse()
        print(f"Generated AST with {len(ast.declarations)} declarations")
        
        # Show declarations
        for i, decl in enumerate(ast.declarations):
            print(f"  {i}: {type(decl).__name__}")
            if hasattr(decl, 'name'):
                print(f"      Name: {decl.name}")
        
        # Semantic Analysis
        print("Semantic analysis...")
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("Semantic analysis passed!")
        
        # Bytecode Generation
        print("Bytecode generation...")
        generator = BytecodeGenerator()
        program = generator.generate(ast)
        print(f"Generated {len(program.instructions)} instructions")
        
        print("SUCCESS: All stages completed!")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_demo_file()
    sys.exit(0 if success else 1)
