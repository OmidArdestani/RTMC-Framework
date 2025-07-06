#!/usr/bin/env python3
"""
Simple test script for Mini-C compiler
Tests basic functionality without external dependencies.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.lexer.tokenizer import Tokenizer, TokenType
from src.parser.parser import Parser
from src.parser.ast_nodes import ImportStmtNode, MessageRecvNode


def test_tokenizer():
    """Test basic tokenizer functionality"""
    print("Testing tokenizer...")
    
    from src.lexer.tokenizer import Tokenizer, TokenType
    
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
    
    from src.lexer.tokenizer import Tokenizer
    from src.parser.parser import Parser
    from src.parser.ast_nodes import FunctionDeclNode
    
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
    
    from src.lexer.tokenizer import Tokenizer
    from src.parser.parser import Parser
    from src.semantic.analyzer import SemanticAnalyzer
    
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
    
    from src.lexer.tokenizer import Tokenizer
    from src.parser.parser import Parser
    from src.semantic.analyzer import SemanticAnalyzer
    from src.bytecode.generator import BytecodeGenerator
    
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
    
    from src.lexer.tokenizer import Tokenizer
    from src.parser.parser import Parser
    from src.semantic.analyzer import SemanticAnalyzer
    from src.bytecode.generator import BytecodeGenerator
    from src.vm.virtual_machine import VirtualMachine
    
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
    
    from src.lexer.tokenizer import Tokenizer
    from src.parser.parser import Parser
    from src.semantic.analyzer import SemanticAnalyzer
    from src.bytecode.generator import BytecodeGenerator
    
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

def test_import_tokenization():
    """Test that import statements are tokenized correctly"""
    try:
        source = 'import "test.rtmc";'
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        
        assert tokens[0].type == TokenType.IMPORT
        assert tokens[1].type == TokenType.STRING
        assert tokens[1].value == "test.rtmc"
        assert tokens[2].type == TokenType.SEMICOLON
        print("✓ Import tokenization test passed")
    except AssertionError as e:
        print(f"✗ Import tokenization test failed: {e}")
        return False
    
    return True

def test_timeout_tokenization():
    """Test that timeout syntax is tokenized correctly"""
    try:
        source = 'queue.recv(timeout: 100);'
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        
        # Find the relevant tokens
        timeout_idx = None
        colon_idx = None
        for i, token in enumerate(tokens):
            if token.type == TokenType.IDENTIFIER and token.value == "timeout":
                timeout_idx = i
            elif token.type == TokenType.COLON:
                colon_idx = i
        
        assert timeout_idx is not None, "timeout identifier not found"
        assert colon_idx is not None, "colon not found"
        assert colon_idx == timeout_idx + 1, "colon should follow timeout"
        print("✓ Timeout tokenization test passed")
    except AssertionError as e:
        print(f"✗ Timeout tokenization test failed: {e}")
        return False
    
    return True

def test_import_parsing():
    """Test that import statements are parsed correctly"""
    try:
        source = 'import "test.rtmc";\nvoid main() {}'
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.declarations) == 2
        assert isinstance(ast.declarations[0], ImportStmtNode)
        assert ast.declarations[0].filepath == "test.rtmc"
        print("✓ Import parsing test passed")
    except AssertionError as e:
        print(f"✗ Import parsing test failed: {e}")
        return False
    
    return True

def test_timeout_parsing():
    """Test that timeout syntax is parsed correctly"""
    try:
        source = '''
        message<int> TestQueue;
        void main() {
            int x = TestQueue.recv(timeout: 100);
        }
        '''
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Find the variable declaration with recv call
        main_func = ast.declarations[1]  # Second declaration should be main
        block = main_func.body
        var_decl = block.statements[0]  # First statement in main
        recv_call = var_decl.initializer
        
        assert isinstance(recv_call, MessageRecvNode)
        assert recv_call.timeout is not None
        print("✓ Timeout parsing test passed")
    except AssertionError as e:
        print(f"✗ Timeout parsing test failed: {e}")
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
        test_import_tokenization,
        test_timeout_tokenization,
        test_import_parsing,
        test_timeout_parsing
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

def compile_and_run_all_examples():
    """Comprehensive test that compiles and runs all example files"""
    print("=" * 60)
    print("COMPREHENSIVE EXAMPLE TESTING")
    print("=" * 60)
    
    examples_dir = Path(__file__).parent / "examples"
    if not examples_dir.exists():
        print("❌ Examples directory not found")
        return False
    
    from src.lexer.tokenizer import Tokenizer
    from src.parser.parser import Parser
    from src.semantic.analyzer import SemanticAnalyzer
    from src.bytecode.generator import BytecodeGenerator
    from src.vm.virtual_machine import VirtualMachine
    
    # Get all source files
    rtmc_files = list(examples_dir.glob("*.rtmc"))
    mc_files = list(examples_dir.glob("*.mc"))
    all_source_files = rtmc_files + mc_files
    
    if not all_source_files:
        print("❌ No source files found")
        return False
    
    print(f"Found {len(all_source_files)} source files to test:")
    for f in all_source_files:
        print(f"  - {f.name}")
    print()
    
    results = {
        "total": len(all_source_files),
        "compiled": 0,
        "executed": 0,
        "failed": 0,
        "details": []
    }
    
    for source_file in all_source_files:
        file_result = {
            "name": source_file.name,
            "compiled": False,
            "executed": False,
            "error": None,
            "tokens": 0,
            "ast_nodes": 0,
            "instructions": 0
        }
        
        print(f"Processing {source_file.name}...")
        print("-" * 50)
        
        try:
            # Step 1: Read source
            with open(source_file, 'r') as f:
                source = f.read()
            
            print(f"  📄 Source: {len(source)} characters, {len(source.splitlines())} lines")
            
            # Step 2: Tokenize
            print("  🔤 Tokenizing...")
            tokenizer = Tokenizer(source)
            tokens = tokenizer.tokenize()
            file_result["tokens"] = len(tokens)
            print(f"     Generated {len(tokens)} tokens")
            
            # Step 3: Parse
            print("  🌳 Parsing...")
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Count AST nodes
            ast_string = str(ast)
            file_result["ast_nodes"] = ast_string.count("Node")
            print(f"     Generated AST with ~{file_result['ast_nodes']} nodes")
            
            # Step 4: Semantic Analysis
            print("  🔍 Semantic analysis...")
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)
            print("     ✅ Semantic analysis passed")
            
            # Step 5: Bytecode Generation
            print("  ⚙️  Bytecode generation...")
            generator = BytecodeGenerator()
            program = generator.generate(ast)
            file_result["instructions"] = len(program.instructions)
            print(f"     Generated {len(program.instructions)} instructions")
            
            file_result["compiled"] = True
            results["compiled"] += 1
            
            # Step 6: VM Execution (if possible)
            if len(program.instructions) > 0:
                print("  🚀 VM execution...")
                vm = VirtualMachine()
                vm.load_program(program)
                
                try:
                    # Run the VM
                    vm.run()
                    print("     ✅ Execution completed")
                    file_result["executed"] = True
                    results["executed"] += 1
                except Exception as vm_error:
                    print(f"     ⚠️  Execution warning: {vm_error}")
                    # Don't count as failure if compilation worked
                    file_result["executed"] = False
            
            print(f"  ✅ {source_file.name} processed successfully")
            
        except Exception as e:
            file_result["error"] = str(e)
            results["failed"] += 1
            print(f"  ❌ Failed: {e}")
            
            # Try to provide more specific error info
            if "SemanticAnalyzer" in str(e):
                print("     💡 This might be due to missing semantic analyzer features")
            elif "BytecodeGenerator" in str(e):
                print("     💡 This might be due to missing bytecode generator features")
            elif "parser" in str(e).lower():
                print("     💡 This might be a parsing issue with new language features")
        
        results["details"].append(file_result)
        print()
    
    # Summary Report
    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    print(f"📊 Overall Statistics:")
    print(f"   Total files tested: {results['total']}")
    print(f"   Successfully compiled: {results['compiled']}")
    print(f"   Successfully executed: {results['executed']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Success rate: {(results['compiled'] / results['total'] * 100):.1f}%")
    print()
    
    # Detailed results
    print("📋 Detailed Results:")
    for detail in results["details"]:
        status = "✅" if detail["compiled"] else "❌"
        exec_status = "🚀" if detail["executed"] else "⏹️"
        print(f"   {status} {exec_status} {detail['name']:<30} "
              f"Tokens: {detail['tokens']:<4} "
              f"Instructions: {detail['instructions']:<4}")
        if detail["error"]:
            print(f"      Error: {detail['error']}")
    
    print()
    
    # Feature Analysis
    print("🔍 Feature Analysis:")
    array_files = [d for d in results["details"] if "array" in d["name"].lower()]
    struct_files = [d for d in results["details"] if "struct" in d["name"].lower()]
    message_files = [d for d in results["details"] if "message" in d["name"].lower()]
    
    if array_files:
        array_success = sum(1 for f in array_files if f["compiled"])
        print(f"   Array features: {array_success}/{len(array_files)} files compiled")
    
    if struct_files:
        struct_success = sum(1 for f in struct_files if f["compiled"])
        print(f"   Struct features: {struct_success}/{len(struct_files)} files compiled")
    
    if message_files:
        message_success = sum(1 for f in message_files if f["compiled"])
        print(f"   Message features: {message_success}/{len(message_files)} files compiled")
    
    # Recommendations
    print()
    print("💡 Recommendations:")
    if results["failed"] > 0:
        print("   - Some files failed compilation. Check error messages above.")
        print("   - Consider implementing missing semantic analyzer features.")
        print("   - Consider implementing missing bytecode generator features.")
    
    if results["compiled"] > results["executed"]:
        print("   - Some files compiled but couldn't execute fully.")
        print("   - This is normal for incomplete VM implementations.")
    
    success_rate = results["compiled"] / results["total"]
    if success_rate >= 0.8:
        print("   - 🎉 Great! Most examples are working.")
    elif success_rate >= 0.5:
        print("   - 👍 Good progress, but more work needed.")
    else:
        print("   - 🔧 Significant work needed on compiler components.")
    
    return success_rate >= 0.5

if __name__ == "__main__":
    # Run all basic tests
    result = main()
    
    # Run comprehensive example testing
    print("=" * 50)
    print("Running comprehensive example testing...")
    print("=" * 50)
    compile_and_run_all_examples()
    
    sys.exit(0 if result else 1)
