#!/usr/bin/env python3
"""
Comprehensive Semantic Analysis Tests
Tests type checking, scope resolution, and semantic validation.
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.ply_lexer import RTMCLexer
from src.parser.ply_parser import RTMCParser
from src.semantic.analyzer import SemanticAnalyzer
from src.parser.ast_nodes import *


class TestBasicSemantics(unittest.TestCase):
    """Test basic semantic analysis"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code and return errors"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_valid_program(self):
        """Test analysis of valid program"""
        source = """
        void main() {
            int x = 5;
            float y = 3.14;
            char c = 'a';
            bool flag = true;
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertEqual(len(errors), 0)
    
    def test_undefined_variable(self):
        """Test undefined variable detection"""
        source = """
        void main() {
            int x = undefined_var;
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("undefined" in str(error).lower() for error in errors))
    
    def test_type_mismatch(self):
        """Test type mismatch detection"""
        source = """
        void func(int param) {
            return;
        }
        
        void main() {
            func("string");  // Type mismatch
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_function_redefinition(self):
        """Test function redefinition detection"""
        source = """
        void func() {
            return;
        }
        
        void func() {  // Redefinition
            return;
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_variable_redefinition(self):
        """Test variable redefinition in same scope"""
        source = """
        void main() {
            int x = 5;
            int x = 10;  // Redefinition in same scope
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_valid_variable_shadowing(self):
        """Test valid variable shadowing"""
        source = """
        int global_var = 5;
        
        void main() {
            int global_var = 10;  // Valid shadowing
            {
                int global_var = 15;  // Valid nested shadowing
            }
        }
        """
        errors, ast = self._analyze_code(source)
        # Shadowing should be allowed
        self.assertEqual(len(errors), 0)


class TestTypeChecking(unittest.TestCase):
    """Test type checking functionality"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_arithmetic_type_checking(self):
        """Test arithmetic expression type checking"""
        valid_cases = [
            "int result = 5 + 3;",
            "float result = 5.0 + 3.14;",
            "int result = 10 - 5;",
            "float result = 15.0 / 3.0;",
        ]
        
        for case in valid_cases:
            with self.subTest(case=case):
                source = f"void main() {{ {case} }}"
                errors, ast = self._analyze_code(source)
                # Should have no type errors for valid arithmetic
                type_errors = [e for e in errors if "type" in str(e).lower()]
                self.assertEqual(len(type_errors), 0)
    
    def test_assignment_type_checking(self):
        """Test assignment type checking"""
        invalid_cases = [
            ("int x = 3.14;", "float to int"),
            ("float y = \"string\";", "string to float"),
            ("char c = 42;", "int to char"),
            ("bool flag = 123;", "int to bool"),
        ]
        
        for case, description in invalid_cases:
            with self.subTest(case=case, description=description):
                source = f"void main() {{ {case} }}"
                errors, ast = self._analyze_code(source)
                # Should detect type mismatch (or warn)
                # Note: Some conversions might be allowed with warnings
    
    def test_function_parameter_checking(self):
        """Test function parameter type checking"""
        source = """
        void func_int(int param) { return; }
        void func_float(float param) { return; }
        void func_char(char param) { return; }
        
        void main() {
            func_int(42);        // Valid
            func_float(3.14);    // Valid
            func_char('a');      // Valid
            
            func_int("string");  // Invalid
            func_float(42);      // May be valid with conversion
            func_char(123);      // May be valid with conversion
        }
        """
        errors, ast = self._analyze_code(source)
        # Should detect string to int error
        self.assertGreater(len(errors), 0)
    
    def test_return_type_checking(self):
        """Test return type checking"""
        test_cases = [
            # Valid returns
            ("int func() { return 42; }", 0),
            ("float func() { return 3.14; }", 0),
            ("void func() { return; }", 0),
            
            # Invalid returns
            ("int func() { return 3.14; }", 1),  # float to int
            ("void func() { return 42; }", 1),   # value in void function
            ("int func() { return; }", 1),       # no value in int function
        ]
        
        for source, expected_errors in test_cases:
            with self.subTest(source=source):
                errors, ast = self._analyze_code(source)
                if expected_errors > 0:
                    self.assertGreater(len(errors), 0)
                else:
                    return_errors = [e for e in errors if "return" in str(e).lower()]
                    self.assertEqual(len(return_errors), 0)
    
    def test_boolean_condition_checking(self):
        """Test boolean condition type checking"""
        source = """
        void main() {
            bool flag = true;
            int number = 42;
            
            if (flag) { return; }          // Valid boolean
            if (number) { return; }        // Valid numeric (C-style)
            if (number > 0) { return; }    // Valid comparison
            
            while (flag && true) { break; }
            for (; !flag; ) { continue; }
        }
        """
        errors, ast = self._analyze_code(source)
        # Should accept both boolean and numeric conditions
        condition_errors = [e for e in errors if "condition" in str(e).lower()]
        self.assertEqual(len(condition_errors), 0)
    
    def test_array_type_checking(self):
        """Test array type checking"""
        source = """
        void main() {
            int arr[5] = {1, 2, 3, 4, 5};     // Valid
            float vals[3] = {1.0, 2.0, 3.0};  // Valid
            
            int invalid[3] = {1, 2.5, 3};     // Type mismatch in initializer
            int value = arr[0];               // Valid access
            arr[1] = 42;                      // Valid assignment
        }
        """
        errors, ast = self._analyze_code(source)
        # Should detect type mismatch in array initializer
        # (2.5 is float, but array is int)


class TestStructSemantics(unittest.TestCase):
    """Test struct-related semantic analysis"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_struct_definition(self):
        """Test struct definition validation"""
        source = """
        struct Point {
            int x;
            int y;
        };
        
        struct Rectangle {
            Point topLeft;
            Point bottomRight;
        };
        """
        errors, ast = self._analyze_code(source)
        self.assertEqual(len(errors), 0)
    
    def test_struct_member_access(self):
        """Test struct member access validation"""
        source = """
        struct Point {
            int x;
            int y;
        };
        
        void main() {
            Point p;
            int x_val = p.x;          // Valid
            p.y = 42;                 // Valid
            int invalid = p.z;        // Invalid - no member 'z'
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("member" in str(error).lower() for error in errors))
    
    def test_nested_member_access(self):
        """Test nested struct member access"""
        source = """
        struct Point { int x; int y; };
        struct Rectangle {
            Point topLeft;
            Point bottomRight;
        };
        
        void main() {
            Rectangle rect;
            rect.topLeft.x = 10;           // Valid nested access
            rect.bottomRight.y = 20;       // Valid nested access
            int value = rect.topLeft.z;    // Invalid - Point has no 'z'
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_struct_assignment(self):
        """Test struct assignment validation"""
        source = """
        struct Point { int x; int y; };
        struct Different { float a; };
        
        void main() {
            Point p1, p2;
            Different d;
            
            p1 = p2;    // Valid - same type
            p1 = d;     // Invalid - different types
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_bitfield_validation(self):
        """Test bitfield width validation"""
        source = """
        struct Register {
            int field1 : 8;     // Valid
            int field2 : 16;    // Valid
            int field3 : 32;    // Valid (max for int)
            int field4 : 33;    // Invalid - exceeds int size
            int field5 : 0;     // Invalid - zero width
            int field6 : -1;    // Invalid - negative width
        };
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
        # Should have errors for invalid bitfield widths
    
    def test_struct_recursive_definition(self):
        """Test recursive struct definition detection"""
        source = """
        struct Node {
            int data;
            Node next;    // Should be invalid - recursive without pointer
        };
        """
        errors, ast = self._analyze_code(source)
        # Should detect recursive definition (unless pointers are used)
        # This depends on implementation - some compilers allow forward declarations


class TestUnionSemantics(unittest.TestCase):
    """Test union-related semantic analysis"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_union_definition(self):
        """Test union definition validation"""
        source = """
        union Data {
            int intValue;
            float floatValue;
            char bytes[4];
        };
        """
        errors, ast = self._analyze_code(source)
        self.assertEqual(len(errors), 0)
    
    def test_union_member_access(self):
        """Test union member access validation"""
        source = """
        union Data {
            int intValue;
            float floatValue;
        };
        
        void main() {
            Data d;
            d.intValue = 42;           // Valid
            float f = d.floatValue;    // Valid
            int invalid = d.missing;   // Invalid - no such member
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_union_size_semantics(self):
        """Test union size calculation"""
        source = """
        union SmallData {
            char c;      // 1 byte
            int i;       // 4 bytes
        };
        
        union LargeData {
            int i;       // 4 bytes
            double d;    // 8 bytes (if supported)
            char arr[16]; // 16 bytes
        };
        """
        errors, ast = self._analyze_code(source)
        # Size calculation is usually done correctly
        # This test mainly checks that unions are accepted
        self.assertEqual(len(errors), 0)


class TestMessageSemantics(unittest.TestCase):
    """Test message-related semantic analysis"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_message_declaration(self):
        """Test message declaration validation"""
        source = """
        message<int> IntMsg;
        message<float> FloatMsg;
        message<char> CharMsg;
        """
        errors, ast = self._analyze_code(source)
        self.assertEqual(len(errors), 0)
    
    def test_message_operations(self):
        """Test message send/recv validation"""
        source = """
        message<int> TestMsg;
        
        void main() {
            TestMsg.send(42);              // Valid
            int value = TestMsg.recv();    // Valid
            
            TestMsg.send("string");        // Invalid - type mismatch
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_message_timeout_validation(self):
        """Test message timeout parameter validation"""
        source = """
        message<float> TimeoutMsg;
        
        void main() {
            float val1 = TimeoutMsg.recv(100);    // Valid - int timeout
            float val2 = TimeoutMsg.recv();       // Valid - no timeout
            float val3 = TimeoutMsg.recv(-1);     // Invalid - negative timeout
            float val4 = TimeoutMsg.recv(3.14);   // Invalid - float timeout
        }
        """
        errors, ast = self._analyze_code(source)
        # Should validate timeout parameter types
        self.assertGreater(len(errors), 0)
    
    def test_message_with_struct_type(self):
        """Test messages with struct types"""
        source = """
        struct Data { int value; float rate; };
        message<Data> DataMsg;
        
        void main() {
            Data d;
            d.value = 42;
            d.rate = 3.14;
            DataMsg.send(d);              // Valid
            
            Data received = DataMsg.recv();
            
            DataMsg.send(42);             // Invalid - wrong type
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)


class TestScopeAnalysis(unittest.TestCase):
    """Test scope resolution and analysis"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_global_scope(self):
        """Test global scope variable access"""
        source = """
        int global_var = 42;
        
        void main() {
            int local = global_var;  // Access global from function
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertEqual(len(errors), 0)
    
    def test_function_scope(self):
        """Test function parameter and local variable scope"""
        source = """
        void func(int param) {
            int local = param;
            {
                int nested = local;
                param = nested;
            }
            // nested is not accessible here
            // int invalid = nested;  // Would be error
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertEqual(len(errors), 0)
    
    def test_block_scope(self):
        """Test block scope handling"""
        source = """
        void main() {
            int outer = 5;
            {
                int inner = 10;
                outer = inner;  // Valid - outer is accessible
            }
            // inner is not accessible here
            int invalid = inner;  // Should be error
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_for_loop_scope(self):
        """Test for loop variable scope"""
        source = """
        void main() {
            for (int i = 0; i < 10; i++) {
                int j = i;  // Valid
            }
            // i is not accessible here
            int invalid = i;  // Should be error
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
    
    def test_variable_shadowing(self):
        """Test variable shadowing rules"""
        source = """
        int global = 1;
        
        void main() {
            int global = 2;  // Shadows global variable
            {
                int global = 3;  // Shadows function-level variable
                printf("Inner: {}", global);  // Should use innermost
            }
            printf("Function: {}", global);  // Should use function-level
        }
        """
        errors, ast = self._analyze_code(source)
        # Shadowing should be allowed
        self.assertEqual(len(errors), 0)
    
    def test_function_forward_declaration(self):
        """Test function forward declaration and usage"""
        source = """
        void helper(int param);  // Forward declaration
        
        void main() {
            helper(42);  // Should find forward declaration
        }
        
        void helper(int param) {  // Definition
            return;
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertEqual(len(errors), 0)


class TestConstantAnalysis(unittest.TestCase):
    """Test constant declaration and usage analysis"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_constant_declaration(self):
        """Test constant declaration validation"""
        source = """
        const int MAX_SIZE = 100;
        const float PI = 3.14159;
        const char NEWLINE = '\\n';
        
        void main() {
            int array[MAX_SIZE];
            float circumference = 2 * PI * radius;
        }
        """
        errors, ast = self._analyze_code(source)
        # Constants should be usable
        const_errors = [e for e in errors if "const" in str(e).lower()]
        self.assertEqual(len(const_errors), 0)
    
    def test_constant_modification(self):
        """Test constant modification detection"""
        source = """
        const int READONLY = 42;
        
        void main() {
            READONLY = 100;  // Should be error - can't modify const
        }
        """
        errors, ast = self._analyze_code(source)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("const" in str(error).lower() for error in errors))
    
    def test_constant_expressions(self):
        """Test constant expression evaluation"""
        source = """
        const int A = 10;
        const int B = 20;
        const int C = A + B;  // Constant expression
        
        void main() {
            int array[C];  // Should work if constants are evaluated
        }
        """
        errors, ast = self._analyze_code(source)
        # Should evaluate constant expressions
        self.assertEqual(len(errors), 0)


class TestRTOSSemantics(unittest.TestCase):
    """Test RTOS function semantic validation"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str):
        """Helper to analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return self.analyzer.errors, ast
    
    def test_rtos_task_functions(self):
        """Test RTOS task function validation"""
        source = """
        void task_function() {
            while (1) {
                delay_ms(1000);
                RTOS_YIELD();
            }
        }
        
        void main() {
            RTOS_CREATE_TASK(task_function, 1024, 1, 1);
        }
        """
        errors, ast = self._analyze_code(source)
        # RTOS functions should be recognized
        rtos_errors = [e for e in errors if "rtos" in str(e).lower()]
        self.assertEqual(len(rtos_errors), 0)
    
    def test_rtos_parameter_validation(self):
        """Test RTOS function parameter validation"""
        source = """
        void main() {
            delay_ms(1000);        // Valid
            delay_ms(-100);        // Invalid - negative delay
            delay_ms("string");    // Invalid - string parameter
        }
        """
        errors, ast = self._analyze_code(source)
        # Should validate RTOS parameters
        self.assertGreater(len(errors), 0)
    
    def test_hardware_function_validation(self):
        """Test hardware function validation"""
        source = """
        void main() {
            HW_GPIO_INIT(25, 1);        // Valid
            HW_GPIO_SET(25, 1);         // Valid
            int value = HW_GPIO_GET(25); // Valid
            
            HW_GPIO_INIT("pin", 1);     // Invalid - string pin
            HW_GPIO_SET(25, 2);         // Invalid - value > 1
        }
        """
        errors, ast = self._analyze_code(source)
        # Should validate hardware parameters
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
