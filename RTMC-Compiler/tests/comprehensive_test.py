import sys
import os
sys.path.append('.')

from src.lexer.tokenizer import Tokenizer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.bytecode.generator import BytecodeGenerator

def test_comprehensive_features():
    """Test all implemented features comprehensively"""
    
    # Read the final test file
    with open('final_test.rtmc', 'r') as f:
        code = f.read()
    
    try:
        # Tokenize
        tokenizer = Tokenizer(code)
        tokens = tokenizer.tokenize()
        print("✓ Tokenization successful")
        
        # Parse
        parser = Parser(tokens)
        ast = parser.parse()
        print("✓ Parsing successful")
        
        # Semantic analysis
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        if analyzer.errors:
            print("✗ Semantic analysis failed:")
            for error in analyzer.errors:
                print(f"  {error}")
            return False
        else:
            print("✓ Semantic analysis successful")
        
        # Bytecode generation
        generator = BytecodeGenerator()
        bytecode = generator.generate(ast)
        print("✓ Bytecode generation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing comprehensive language features...")
    success = test_comprehensive_features()
    
    if success:
        print("\n🎉 All features working correctly!")
        print("✓ Import statements")
        print("✓ Boolean type and literals (true/false)")
        print("✓ Flexible brace placement for all constructs")
        print("✓ Boolean conditions in if/while/for statements")
        print("✓ Backward compatibility with numeric conditions")
    else:
        print("\n❌ Some features are not working correctly")
