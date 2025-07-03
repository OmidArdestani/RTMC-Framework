#!/usr/bin/env python3
"""
Simple test script for Mini-C compiler
Tests basic functionality without external dependencies.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_tokenizer():
    """Test basic tokenizer functionality"""
    print("Testing tokenizer...")
    
    from lexer.tokenizer import Tokenizer, TokenType
    
    source = "int main() { HW_GPIO_SET(25, 1); return 0; }"
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    
    print(f"  Tokenized {len(tokens)} tokens")
    
    # Check for expected tokens
    expected_types = [TokenType.INT, TokenType.IDENTIFIER, TokenType.LEFT_PAREN, TokenType.RIGHT_PAREN, TokenType.LEFT_BRACE, TokenType.HW_GPIO_SET]
    for i, expected in enumerate(expected_types):
        if i < len(tokens) and tokens[i].type == expected:
            print(f"  ✓ Token {i}: {expected.name}")
        else:
            print(f"  ✗ Token {i}: Expected {expected.name}")
            return False
    
    return True

def test_parser():
    """Test basic parser functionality"""
    print("Testing parser...")
    
    from lexer.tokenizer import Tokenizer
    from parser.parser import Parser
    from parser.ast_nodes import FunctionDeclNode
    
    source = """
    void main() {
        int x = 42;
        return;
    }
    """
    
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    print(f"  Parsed {len(ast.declarations)} declarations")
    
    if len(ast.declarations) > 0 and isinstance(ast.declarations[0], FunctionDeclNode):
        func = ast.declarations[0]
        print(f"  ✓ Function: {func.name}")
        print(f"  ✓ Return type: {func.return_type.type_name}")
        return True
    else:
        print("  ✗ No function declaration found")
        return False

def test_semantic_analyzer():
    """Test basic semantic analysis"""
    print("Testing semantic analyzer...")
    
    from lexer.tokenizer import Tokenizer
    from parser.parser import Parser
    from semantic.analyzer import SemanticAnalyzer
    
    source = """
    void main() {
        int x = 42;
        x = x + 1;
        HW_GPIO_INIT(25, 1);
    }
    """
    
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    
    try:
        analyzer.analyze(ast)
        print("  ✓ Semantic analysis passed")
        return True
    except Exception as e:
        print(f"  ✗ Semantic analysis failed: {e}")
        return False

def test_bytecode_generation():
    """Test bytecode generation"""
    print("Testing bytecode generation...")
    
    from lexer.tokenizer import Tokenizer
    from parser.parser import Parser
    from semantic.analyzer import SemanticAnalyzer
    from bytecode.generator import BytecodeGenerator
    
    source = """
    void main() {
        HW_GPIO_INIT(25, 1);
        HW_GPIO_SET(25, 1);
    }
    """
    
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    
    generator = BytecodeGenerator()
    program = generator.generate(ast)
    
    print(f"  ✓ Generated {len(program.instructions)} instructions")
    print(f"  ✓ Functions: {list(program.functions.keys())}")
    print(f"  ✓ Constants: {len(program.constants)}")
    
    return True

def test_virtual_machine():
    """Test virtual machine execution"""
    print("Testing virtual machine...")
    
    from lexer.tokenizer import Tokenizer
    from parser.parser import Parser
    from semantic.analyzer import SemanticAnalyzer
    from bytecode.generator import BytecodeGenerator
    from vm.virtual_machine import VirtualMachine
    
    source = """
    void main() {
        int x = 42;
        DBG_PRINT("Hello from Mini-C!");
        HW_GPIO_INIT(25, 1);
        HW_GPIO_SET(25, 1);
    }
    """
    
    # Compile
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    
    generator = BytecodeGenerator()
    program = generator.generate(ast)
    
    # Execute
    vm = VirtualMachine(debug=False, trace=False)
    vm.load_program(program)
    
    try:
        vm.run()
        print("  ✓ Virtual machine execution completed")
        return True
    except Exception as e:
        print(f"  ✗ Virtual machine execution failed: {e}")
        return False

def test_example_compilation():
    """Test compilation of example files"""
    print("Testing example compilation...")
    
    examples_dir = Path(__file__).parent / "examples"
    if not examples_dir.exists():
        print("  ✗ Examples directory not found")
        return False
    
    from lexer.tokenizer import Tokenizer
    from parser.parser import Parser
    from semantic.analyzer import SemanticAnalyzer
    from bytecode.generator import BytecodeGenerator
    
    example_files = list(examples_dir.glob("*.mc"))
    if not example_files:
        print("  ✗ No example files found")
        return False
    
    for example_file in example_files:
        try:
            print(f"  Testing {example_file.name}...")
            
            with open(example_file, 'r') as f:
                source = f.read()
            
            tokenizer = Tokenizer(source)
            tokens = tokenizer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)
            
            generator = BytecodeGenerator()
            program = generator.generate(ast)
            
            print(f"    ✓ {example_file.name} compiled successfully")
            
        except Exception as e:
            print(f"    ✗ {example_file.name} failed: {e}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("Mini-C Compiler Test Suite")
    print("=" * 50)
    
    tests = [
        test_tokenizer,
        test_parser,
        test_semantic_analyzer,
        test_bytecode_generation,
        test_virtual_machine,
        test_example_compilation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("  PASSED\n")
            else:
                print("  FAILED\n")
        except Exception as e:
            print(f"  ERROR: {e}\n")
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All tests passed! The Mini-C compiler is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
