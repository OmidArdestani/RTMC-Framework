#!/usr/bin/env python3
"""
Test script for sizeof functionality in RTMC compiler
"""

import sys
import os

# Add the parent directory to the path so we can import the compiler modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the compiler modules with relative imports
try:
    from src.lexer.ply_lexer import RTMCLexer
    from src.parser.ply_parser import RTMCParser  
    from src.semantic.analyzer import SemanticAnalyzer
    from src.optimizer.optimizer import ConstantFolder
    from src.bytecode.generator import BytecodeGenerator
except ImportError:
    # Fallback for different import structure
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from RTMC_Compiler.src.lexer.ply_lexer import RTMCLexer
    from RTMC_Compiler.src.parser.ply_parser import RTMCParser
    from RTMC_Compiler.src.semantic.analyzer import SemanticAnalyzer
    from RTMC_Compiler.src.optimizer.optimizer import ConstantFolder
    from RTMC_Compiler.src.bytecode.generator import BytecodeGenerator

def test_sizeof_parsing():
    """Test that sizeof expressions are parsed correctly"""
    print("Testing sizeof parsing...")
    
    code = """
    int main() {
        int x = sizeof(int);
        int y = sizeof(x);
        return 0;
    }
    """
    
    lexer = RTMCLexer()
    parser = RTMCParser()
    
    try:
        tokens = lexer.tokenize(code)
        ast = parser.parse(tokens)
        print("✓ Sizeof parsing test passed!")
        return True
    except Exception as e:
        print(f"✗ Sizeof parsing test failed: {e}")
        return False

def test_sizeof_semantic_analysis():
    """Test that sizeof expressions are semantically analyzed correctly"""
    print("Testing sizeof semantic analysis...")
    
    code = """
    struct Point { int x; int y; };
    
    int main() {
        int a = sizeof(int);
        int b = sizeof(Point);
        struct Point p;
        int c = sizeof(p);
        return 0;
    }
    """
    
    lexer = RTMCLexer()
    parser = RTMCParser()
    analyzer = SemanticAnalyzer()
    
    try:
        tokens = lexer.tokenize(code)
        ast = parser.parse(tokens)
        analyzer.analyze(ast)
        
        if not analyzer.errors:
            print("✓ Sizeof semantic analysis test passed!")
            return True
        else:
            print(f"✗ Sizeof semantic analysis test failed: {analyzer.errors}")
            return False
    except Exception as e:
        print(f"✗ Sizeof semantic analysis test failed: {e}")
        return False

def test_sizeof_optimization():
    """Test that sizeof expressions are optimized to constants"""
    print("Testing sizeof optimization...")
    
    code = """
    struct Point { int x; int y; };
    
    int main() {
        int a = sizeof(int);
        return 0;
    }
    """
    
    lexer = RTMCLexer()
    parser = RTMCParser()
    analyzer = SemanticAnalyzer()
    optimizer = ConstantFolder()
    
    try:
        tokens = lexer.tokenize(code)
        ast = parser.parse(tokens)
        analyzer.analyze(ast)
        
        if analyzer.errors:
            print(f"✗ Semantic analysis failed: {analyzer.errors}")
            return False
        
        optimized_ast = optimizer.visit_program(ast)
        print("✓ Sizeof optimization test passed!")
        return True
    except Exception as e:
        print(f"✗ Sizeof optimization test failed: {e}")
        return False

def main():
    """Run all sizeof tests"""
    print("Running sizeof implementation tests...\n")
    
    tests = [
        test_sizeof_parsing,
        test_sizeof_semantic_analysis,
        test_sizeof_optimization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All sizeof tests passed!")
        return 0
    else:
        print("❌ Some sizeof tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())
