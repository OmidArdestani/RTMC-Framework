#!/usr/bin/env python3
"""
Quick validation test for array and struct features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_array_struct_compilation():
    """Test that our new features compile correctly"""
    print("🧪 Testing Array and Struct Feature Compilation")
    print("=" * 60)
    
    from src.lexer.tokenizer import Tokenizer
    from src.parser.parser import Parser
    from src.semantic.analyzer import SemanticAnalyzer
    from src.bytecode.generator import BytecodeGenerator
    
    # Test cases for our new features
    test_cases = [
        ("Simple Array Declaration", """
            int numbers[5] = {1, 2, 3, 4, 5};
        """),
        
        ("Array Access", """
            void test() {
                int arr[3];
                arr[0] = 42;
                int x = arr[1];
            }
        """),
        
        ("Nested Struct", """
            struct Point { int x; int y; };
            struct Rect { Point tl; Point br; };
        """),
        
        ("Complex Nested Access", """
            struct Point { int x; int y; };
            Point points[4];
            void test() {
                points[0].x = 10;
                points[0].y = 20;
                int px = points[0].x;
            }
        """),
        
        ("Array of Structs", """
            struct Point { int x; int y; };
            Point vertices[4] = {{0,0}, {1,0}, {1,1}, {0,1}};
        """)
    ]
    
    results = []
    
    for name, code in test_cases:
        print(f"\n📋 Test: {name}")
        print("-" * 40)
        
        try:
            # Tokenize
            tokenizer = Tokenizer(code)
            tokens = tokenizer.tokenize()
            print(f"   ✅ Tokenized: {len(tokens)} tokens")
            
            # Parse
            parser = Parser(tokens)
            ast = parser.parse()
            print(f"   ✅ Parsed successfully")
            
            # Semantic Analysis
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)
            print(f"   ✅ Semantic analysis passed")
            
            # Bytecode Generation
            generator = BytecodeGenerator()
            program = generator.generate(ast)
            print(f"   ✅ Generated {len(program.instructions)} instructions")
            
            results.append((name, True, None))
            print(f"   🎉 SUCCESS!")
            
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"   ❌ FAILED: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Results: {successful}/{total} tests passed ({successful/total*100:.1f}%)")
    print()
    
    for name, success, error in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
        if error:
            print(f"    Error: {error}")
    
    print()
    if successful == total:
        print("🎉 All array and struct features are working correctly!")
        return True
    else:
        print("🔧 Some features need more work.")
        return False

if __name__ == "__main__":
    success = test_array_struct_compilation()
    exit(0 if success else 1)
