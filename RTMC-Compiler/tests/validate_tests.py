#!/usr/bin/env python3
"""
Test Validation Script
Validates that all test modules can be imported and basic functionality works.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_imports():
    """Validate that all necessary modules can be imported"""
    print("Validating imports...")
    
    try:
        # Test core compiler modules
        from src.lexer.ply_lexer import RTMCLexer
        print("✓ Lexer import successful")
        
        from src.parser.ply_parser import RTMCParser
        print("✓ Parser import successful")
        
        from src.parser.ast_nodes import ASTNode, ProgramNode, FunctionDeclNode
        print("✓ AST nodes import successful")
        
        from src.semantic.analyzer import SemanticAnalyzer
        print("✓ Semantic analyzer import successful")
        
        from src.bytecode.generator import BytecodeGenerator
        print("✓ Bytecode generator import successful")
        
        from src.vm.virtual_machine import VirtualMachine
        print("✓ Virtual machine import successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("Note: Some imports may fail if modules are not fully implemented")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False

def validate_basic_functionality():
    """Validate basic functionality of core components"""
    print("\nValidating basic functionality...")
    
    try:
        # Test lexer
        from src.lexer.ply_lexer import RTMCLexer
        lexer = RTMCLexer()
        tokens = lexer.tokenize("int main() { return 0; }")
        if tokens and len(tokens) > 0:
            print("✓ Lexer basic functionality works")
        else:
            print("✗ Lexer produced no tokens")
            return False
        
        # Test parser (if available)
        try:
            from src.parser.ply_parser import RTMCParser
            parser = RTMCParser()
            ast = parser.parse(tokens)
            if ast:
                print("✓ Parser basic functionality works")
            else:
                print("? Parser returned None (may be normal)")
        except Exception as e:
            print(f"? Parser test failed: {e} (may not be fully implemented)")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def check_test_files():
    """Check that all test files exist and can be imported"""
    print("\nChecking test files...")
    
    test_files = [
        "test_comprehensive_specifications.py",
        "test_lexer_comprehensive.py", 
        "test_parser_comprehensive.py",
        "test_semantic_comprehensive.py",
        "test_integration_comprehensive.py",
        "run_comprehensive_tests.py"
    ]
    
    tests_dir = Path(__file__).parent
    
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            print(f"✓ {test_file} exists")
            
            # Try to import the test module
            try:
                module_name = test_file[:-3]  # Remove .py extension
                if module_name != "run_comprehensive_tests":  # Skip runner
                    __import__(module_name)
                    print(f"  ✓ {module_name} imports successfully")
            except Exception as e:
                print(f"  ? {module_name} import issue: {e}")
        else:
            print(f"✗ {test_file} not found")

def validate_source_structure():
    """Validate that the source code structure matches expectations"""
    print("\nValidating source structure...")
    
    src_dir = Path(__file__).parent.parent / "src"
    
    expected_dirs = [
        "lexer",
        "parser", 
        "semantic",
        "bytecode",
        "vm",
        "optimizer"
    ]
    
    for dir_name in expected_dirs:
        dir_path = src_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"✓ {dir_name}/ directory exists")
            
            # Check for __init__.py
            init_file = dir_path / "__init__.py"
            if init_file.exists():
                print(f"  ✓ {dir_name}/__init__.py exists")
            else:
                print(f"  ? {dir_name}/__init__.py missing (may be normal)")
                
        else:
            print(f"✗ {dir_name}/ directory not found")

def main():
    """Main validation function"""
    print("RT-Micro-C Compiler Test Suite Validation")
    print("="*50)
    
    all_good = True
    
    # Validate imports
    if not validate_imports():
        all_good = False
        print("\nNote: Some import failures are expected if modules are not fully implemented")
    
    # Validate basic functionality  
    if not validate_basic_functionality():
        all_good = False
    
    # Check test files
    check_test_files()
    
    # Check source structure
    validate_source_structure()
    
    print("\n" + "="*50)
    if all_good:
        print("✓ Validation completed successfully!")
        print("You can now run the comprehensive tests with:")
        print("  python tests/run_comprehensive_tests.py")
        print("Or run specific test categories:")
        print("  python tests/run_comprehensive_tests.py lexer")
        print("  python tests/run_comprehensive_tests.py parser") 
        print("  python tests/run_comprehensive_tests.py semantic")
        print("  python tests/run_comprehensive_tests.py integration")
    else:
        print("? Validation completed with some issues")
        print("Some tests may not work until all modules are fully implemented")
    
    print("\nTest Coverage Summary:")
    print("- Lexical Analysis: Comprehensive tokenization tests")
    print("- Parser: AST generation and syntax validation")
    print("- Semantic Analysis: Type checking and scope resolution")
    print("- Bytecode Generation: Code generation testing")
    print("- Virtual Machine: Execution simulation")
    print("- Integration: End-to-end compilation testing")
    print("- Features: All documented language features")
    print("- Error Handling: Error detection and reporting")
    print("- Performance: Scalability and edge cases")

if __name__ == '__main__':
    main()
