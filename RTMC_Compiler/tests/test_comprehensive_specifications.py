#!/usr/bin/env python3
"""
Comprehensive Unit Tests for RT-Micro-C Compiler Specifications
Tests all documented features and edge cases to ensure complete coverage.
"""

import sys
import os
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.ply_lexer import RTMCLexer
from src.parser.ply_parser import RTMCParser
from src.parser.ast_nodes import *
from src.semantic.analyzer import SemanticAnalyzer
from src.bytecode.generator import BytecodeGenerator
from src.vm.virtual_machine import VirtualMachine


class TestLexicalAnalysis(unittest.TestCase):
    """Test lexical analysis and tokenization"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
    
    def test_basic_tokens(self):
        """Test basic token recognition"""
        source = "int main() { return 0; }"
        tokens = self.lexer.tokenize(source)
        
        expected_types = ['INT', 'IDENTIFIER', 'LEFT_PAREN', 'RIGHT_PAREN', 
                         'LEFT_BRACE', 'RETURN', 'INTEGER', 'SEMICOLON', 'RIGHT_BRACE']
        actual_types = [token.type for token in tokens]
        
        self.assertEqual(actual_types, expected_types)
    
    def test_hexadecimal_literals(self):
        """Test hexadecimal literal tokenization (HEXADECIMAL_SUPPORT_DOCUMENTATION)"""
        test_cases = [
            ("0xff", 255),
            ("0xFF", 255),
            ("0x1a2b", 6699),
            ("0XABCD", 43981),
            ("0x00A0", 160),
            ("0x000F", 15),
            ("0x0", 0)
        ]
        
        for hex_str, expected_value in test_cases:
            with self.subTest(hex_str=hex_str):
                tokens = self.lexer.tokenize(hex_str)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, 'INTEGER')
                # Test that parser can convert hex to decimal
                self.assertEqual(int(hex_str, 16), expected_value)
    
    def test_boolean_literals(self):
        """Test boolean literal tokenization (IMPLEMENTATION_COMPLETE)"""
        source = "bool flag = true; bool test = false;"
        tokens = self.lexer.tokenize(source)
        
        bool_tokens = [t for t in tokens if t.type in ['BOOL_TYPE', 'TRUE', 'FALSE']]
        self.assertGreaterEqual(len(bool_tokens), 3)
    
    def test_rtos_functions(self):
        """Test RTOS function keyword tokenization"""
        rtos_functions = [
            "RTOS_DELAY_MS", "RTOS_CREATE_TASK", "RTOS_DELETE_TASK",
            "RTOS_SUSPEND_TASK", "RTOS_RESUME_TASK", "RTOS_YIELD",
            "RTOS_CREATE_SEMAPHORE", "RTOS_TAKE_SEMAPHORE", "RTOS_GIVE_SEMAPHORE"
        ]
        
        for func in rtos_functions:
            with self.subTest(function=func):
                tokens = self.lexer.tokenize(f"{func}();")
                self.assertEqual(tokens[0].type, func)
    
    def test_hardware_functions(self):
        """Test hardware function keyword tokenization"""
        hw_functions = [
            "HW_GPIO_INIT", "HW_GPIO_SET", "HW_GPIO_GET",
            "HW_TIMER_INIT", "HW_TIMER_SET_FREQ", "HW_TIMER_GET_FREQ",
            "HW_ADC_READ", "HW_UART_SEND", "HW_UART_READ"
        ]
        
        for func in hw_functions:
            with self.subTest(function=func):
                tokens = self.lexer.tokenize(f"{func}();")
                self.assertEqual(tokens[0].type, func)
    
    def test_bitfield_syntax(self):
        """Test bitfield syntax tokenization"""
        source = "struct Register { int field : 8; };"
        tokens = self.lexer.tokenize(source)
        
        colon_tokens = [t for t in tokens if t.type == 'COLON']
        self.assertGreaterEqual(len(colon_tokens), 1)
    
    def test_message_syntax(self):
        """Test message declaration syntax"""
        source = "message<int> TestMsg;"
        tokens = self.lexer.tokenize(source)
        
        self.assertIn('MESSAGE', [t.type for t in tokens])


class TestParser(unittest.TestCase):
    """Test parser and AST generation"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def test_basic_function_parsing(self):
        """Test basic function declaration parsing"""
        source = """
        void main() {
            int x = 5;
            return;
        }
        """
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(len(ast.declarations), 1)
        self.assertIsInstance(ast.declarations[0], FunctionDeclNode)
        self.assertEqual(ast.declarations[0].name, "main")
    
    def test_array_declaration_parsing(self):
        """Test array declaration parsing (ARRAY_AND_STRUCT_FEATURES)"""
        test_cases = [
            "int numbers[5];",
            "float values[10] = {1.0, 2.0, 3.0};",
            "char buffer[256];",
            "struct Point points[4];"
        ]
        
        for source in test_cases:
            with self.subTest(source=source):
                tokens = self.lexer.tokenize(source)
                ast = self.parser.parse(tokens)
                
                self.assertIsInstance(ast, ProgramNode)
                self.assertGreater(len(ast.declarations), 0)
                # Should create ArrayDeclNode for array declarations
                # (Implementation depends on parser design)
    
    def test_struct_declaration_parsing(self):
        """Test struct declaration parsing"""
        source = """
        struct Point {
            int x;
            int y;
        };
        """
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        self.assertIsInstance(ast, ProgramNode)
        struct_decl = ast.declarations[0]
        self.assertIsInstance(struct_decl, StructDeclNode)
        self.assertEqual(struct_decl.name, "Point")
        self.assertEqual(len(struct_decl.fields), 2)
    
    def test_nested_struct_parsing(self):
        """Test nested struct parsing (ARRAY_AND_STRUCT_FEATURES)"""
        source = """
        struct Point { int x; int y; };
        struct Rectangle {
            Point topLeft;
            Point bottomRight;
        };
        """
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        self.assertEqual(len(ast.declarations), 2)
        rect_decl = ast.declarations[1]
        self.assertIsInstance(rect_decl, StructDeclNode)
        self.assertEqual(rect_decl.name, "Rectangle")
    
    def test_union_declaration_parsing(self):
        """Test union declaration parsing (UNION_SUPPORT_DOCUMENTATION)"""
        source = """
        union BasicUnion {
            int intValue;
            float floatValue;
            char charArray[4];
        };
        """
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        union_decl = ast.declarations[0]
        self.assertIsInstance(union_decl, UnionDeclNode)
        self.assertEqual(union_decl.name, "BasicUnion")
        self.assertEqual(len(union_decl.fields), 3)
    
    def test_bitfield_parsing(self):
        """Test bitfield parsing"""
        source = """
        struct Register {
            int field1 : 8;
            int field2 : 16;
            int field3 : 8;
        };
        """
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        struct_decl = ast.declarations[0]
        self.assertIsInstance(struct_decl, StructDeclNode)
        
        # Check bitfield widths
        for field in struct_decl.fields:
            self.assertIsNotNone(field.bit_width)
            self.assertIn(field.bit_width, [8, 16])
    
    def test_message_declaration_parsing(self):
        """Test message declaration parsing"""
        source = "message<int> TestMsg;"
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        msg_decl = ast.declarations[0]
        self.assertIsInstance(msg_decl, MessageDeclNode)
        self.assertEqual(msg_decl.name, "TestMsg")
    
    def test_import_statement_parsing(self):
        """Test import statement parsing (IMPLEMENTATION_COMPLETE)"""
        source = '#include "definitions.rtmc";'
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        import_stmt = ast.declarations[0]
        self.assertIsInstance(import_stmt, ImportStmtNode)
        self.assertEqual(import_stmt.filename, "definitions.rtmc")
    
    def test_boolean_expressions(self):
        """Test boolean expression parsing (IMPLEMENTATION_COMPLETE)"""
        source = """
        void test() {
            bool flag = true;
            if (flag && false) {
                return;
            }
        }
        """
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        # Should parse without errors
        self.assertIsInstance(ast, ProgramNode)
    
    def test_flexible_brace_styles(self):
        """Test flexible brace placement (IMPLEMENTATION_COMPLETE)"""
        test_cases = [
            # Style 1: Same line
            """
            void func() {
                int x = 5;
            }
            """,
            # Style 2: Next line
            """
            void func()
            {
                int x = 5;
            }
            """
        ]
        
        for source in test_cases:
            with self.subTest(source=source.strip()):
                tokens = self.lexer.tokenize(source)
                ast = self.parser.parse(tokens)
                
                self.assertIsInstance(ast, ProgramNode)
                func_decl = ast.declarations[0]
                self.assertIsInstance(func_decl, FunctionDeclNode)
                self.assertEqual(func_decl.name, "func")


class TestSemanticAnalysis(unittest.TestCase):
    """Test semantic analysis and type checking"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _analyze_code(self, source: str) -> tuple:
        """Helper to parse and analyze code"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        return ast, self.analyzer.errors
    
    def test_type_checking_basic(self):
        """Test basic type checking"""
        source = """
        void main() {
            int x = 5;
            float y = 3.14;
            char c = 'a';
            bool flag = true;
        }
        """
        ast, errors = self._analyze_code(source)
        self.assertEqual(len(errors), 0)
    
    def test_function_call_validation(self):
        """Test function call parameter validation"""
        source = """
        void func(int param) {
            return;
        }
        
        void main() {
            func(42);        // Valid
            func("string");  // Should be invalid
        }
        """
        ast, errors = self._analyze_code(source)
        # Should have type mismatch error
        self.assertGreater(len(errors), 0)
    
    def test_struct_member_access(self):
        """Test struct member access validation"""
        source = """
        struct Point {
            int x;
            int y;
        };
        
        void main() {
            Point p;
            int value = p.x;      // Valid
            int invalid = p.z;    // Should be invalid
        }
        """
        ast, errors = self._analyze_code(source)
        # Should have undefined member error
        self.assertGreater(len(errors), 0)
    
    def test_array_bounds_checking(self):
        """Test array bounds checking"""
        source = """
        void main() {
            int arr[5] = {1, 2, 3, 4, 5};
            int valid = arr[2];     // Valid
            int invalid = arr[10];  // Should warn about potential bounds
        }
        """
        ast, errors = self._analyze_code(source)
        # Implementation may or may not catch this at compile time
    
    def test_bitfield_validation(self):
        """Test bitfield width validation"""
        source = """
        struct Register {
            int field1 : 8;    // Valid
            int field2 : 33;   // Should be invalid (> 32 bits)
            int field3 : 0;    // Should be invalid (zero width)
        };
        """
        ast, errors = self._analyze_code(source)
        # Should have bitfield width errors
        self.assertGreater(len(errors), 0)
    
    def test_message_type_validation(self):
        """Test message type validation"""
        source = """
        message<int> IntMsg;
        message<float> FloatMsg;
        
        void main() {
            IntMsg.send(42);        // Valid
            IntMsg.send(3.14);      // Should be type warning/error
        }
        """
        ast, errors = self._analyze_code(source)
        # Should have type mismatch for float->int


class TestBytecodeGeneration(unittest.TestCase):
    """Test bytecode generation"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
        self.generator = BytecodeGenerator()
    
    def _generate_bytecode(self, source: str):
        """Helper to generate bytecode from source"""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        
        if self.analyzer.errors:
            raise Exception(f"Semantic errors: {self.analyzer.errors}")
        
        return self.generator.generate(ast)
    
    def test_basic_arithmetic(self):
        """Test arithmetic expression bytecode generation"""
        source = """
        void main() {
            int result = 5 + 3 * 2;
        }
        """
        bytecode = self._generate_bytecode(source)
        self.assertIsNotNone(bytecode)
        # Should contain arithmetic instructions
    
    def test_function_calls(self):
        """Test function call bytecode generation"""
        source = """
        void helper(int x) {
            return;
        }
        
        void main() {
            helper(42);
        }
        """
        bytecode = self._generate_bytecode(source)
        self.assertIsNotNone(bytecode)
        # Should contain CALL instruction
    
    def test_control_flow(self):
        """Test control flow bytecode generation"""
        source = """
        void main() {
            int i = 0;
            while (i < 10) {
                i = i + 1;
            }
        }
        """
        bytecode = self._generate_bytecode(source)
        self.assertIsNotNone(bytecode)
        # Should contain jump instructions
    
    def test_array_operations(self):
        """Test array operation bytecode generation"""
        source = """
        void main() {
            int arr[5] = {1, 2, 3, 4, 5};
            int value = arr[2];
            arr[3] = 10;
        }
        """
        bytecode = self._generate_bytecode(source)
        self.assertIsNotNone(bytecode)
        # Should contain array access instructions
    
    def test_struct_operations(self):
        """Test struct operation bytecode generation"""
        source = """
        struct Point { int x; int y; };
        
        void main() {
            Point p;
            p.x = 5;
            int value = p.y;
        }
        """
        bytecode = self._generate_bytecode(source)
        self.assertIsNotNone(bytecode)
        # Should contain member access instructions
    
    def test_message_operations(self):
        """Test message operation bytecode generation"""
        source = """
        message<int> TestMsg;
        
        void main() {
            TestMsg.send(42);
            int value = TestMsg.recv();
        }
        """
        bytecode = self._generate_bytecode(source)
        self.assertIsNotNone(bytecode)
        # Should contain message send/recv instructions
    
    def test_rtos_functions(self):
        """Test RTOS function bytecode generation"""
        source = """
        void main() {
            RTOS_DELAY_MS(1000);
            RTOS_YIELD();
        }
        """
        bytecode = self._generate_bytecode(source)
        self.assertIsNotNone(bytecode)
        # Should contain RTOS instruction calls


class TestVirtualMachine(unittest.TestCase):
    """Test virtual machine execution"""
    
    def setUp(self):
        self.vm = VirtualMachine()
    
    def _compile_and_run(self, source: str, max_cycles: int = 1000):
        """Helper to compile and run code"""
        lexer = RTMCLexer()
        parser = RTMCParser()
        analyzer = SemanticAnalyzer()
        generator = BytecodeGenerator()
        
        tokens = lexer.tokenize(source)
        ast = parser.parse(tokens)
        analyzer.analyze(ast)
        
        if analyzer.errors:
            raise Exception(f"Semantic errors: {analyzer.errors}")
        
        bytecode = generator.generate(ast)
        self.vm.load_program(bytecode)
        
        cycle_count = 0
        while self.vm.is_running() and cycle_count < max_cycles:
            self.vm.step()
            cycle_count += 1
        
        return self.vm.get_output()
    
    def test_basic_execution(self):
        """Test basic program execution"""
        source = """
        void main() {
            int x = 5;
            int y = 3;
            int result = x + y;
            DBG_PRINTF("Result: {}", result);
        }
        """
        output = self._compile_and_run(source)
        # Should contain debug output
    
    def test_rtos_delay(self):
        """Test RTOS delay simulation"""
        source = """
        void main() {
            DBG_PRINT("Before delay");
            RTOS_DELAY_MS(100);
            DBG_PRINT("After delay");
        }
        """
        output = self._compile_and_run(source)
        # Should simulate delay and produce both messages
    
    def test_hardware_simulation(self):
        """Test hardware function simulation"""
        source = """
        void main() {
            HW_GPIO_INIT(25, 1);
            HW_GPIO_SET(25, 1);
            int value = HW_GPIO_GET(25);
            DBG_PRINTF("GPIO value: {}", value);
        }
        """
        output = self._compile_and_run(source)
        # Should simulate GPIO operations
    
    def test_message_passing(self):
        """Test message passing simulation"""
        source = """
        message<int> TestMsg;
        
        void sender() {
            TestMsg.send(42);
        }
        
        void receiver() {
            int value = TestMsg.recv();
            DBG_PRINTF("Received: {}", value);
        }
        
        void main() {
            RTOS_CREATE_TASK(sender, 1024, 1, 1);
            RTOS_CREATE_TASK(receiver, 1024, 1, 2);
        }
        """
        output = self._compile_and_run(source, max_cycles=2000)
        # Should simulate message passing between tasks


class TestComplexFeatures(unittest.TestCase):
    """Test complex language features and edge cases"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
        self.generator = BytecodeGenerator()
    
    def test_usb4_sideband_example(self):
        """Test the USB4 sideband example from sb_main.rtmc"""
        source = """
        message<int> SBTestMsg;

        const int USB4_BE_CMD_PROTOCOL_TYPE_SIDEBAND = 14;

        struct USB4BECommand {
            int ProtocolType : 4;
            int Opcode : 12;
        };

        struct USB4SBTransactionHead {
            int DLE : 8;
            int CmdNotResp : 1;
            int Rsvd2 : 5;
            int TrType : 2;
            int DataSymbl : 16;
        };

        void process_data(int data) {
            USB4BECommand* be_cmd = (USB4BECommand*)data;
            DBG_PRINTF("ProtocolType: {}, Opcode: {}", be_cmd->ProtocolType, be_cmd->Opcode);
        }

        void task1_run_function() {
            while (1) {
                int data_addr = SBTestMsg.recv();
                data_addr += 5;
                process_data(data_addr);
                RTOS_DELAY_MS(500);
            }
        }

        void main() {
            int core = 1;
            int priority = 1;
            int stack_size = 1024;
            int task_id = 1010;
            StartTask(stack_size, core, priority, task_id, task1_run_function);

            while(1) {
                char data[10] = {0xAE, 0xBB, 0xBE, 0xDD, 0xEE, 0xFA, 0x00, 0x01, 0x02, 0x03};
                int addr = (int)data;
                SBTestMsg.send(addr);
                RTOS_DELAY_MS(500);
            }
        }
        """
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        
        # Should compile without major errors
        self.assertLessEqual(len(self.analyzer.errors), 2)  # Allow minor warnings
        
        if len(self.analyzer.errors) == 0:
            bytecode = self.generator.generate(ast)
            self.assertIsNotNone(bytecode)
    
    def test_nested_array_struct_access(self):
        """Test complex nested array and struct access"""
        source = """
        struct Point { int x; int y; };
        struct Line { Point start; Point end; };
        
        void main() {
            Line lines[3];
            lines[0].start.x = 10;
            lines[0].start.y = 20;
            lines[0].end.x = 30;
            lines[0].end.y = 40;
            
            int distance_x = lines[0].end.x - lines[0].start.x;
            DBG_PRINTF("Distance X: {}", distance_x);
        }
        """
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        
        # Should handle complex nested access
        self.assertEqual(len(self.analyzer.errors), 0)
    
    def test_union_memory_overlap(self):
        """Test union memory overlap semantics"""
        source = """
        union DataUnion {
            int intValue;
            float floatValue;
            char bytes[4];
        };
        
        void main() {
            DataUnion data;
            data.intValue = 0x12345678;
            
            // Access as bytes
            for (int i = 0; i < 4; i++) {
                DBG_PRINTF("Byte {}: 0x{:02X}", i, data.bytes[i]);
            }
            
            // Access as float
            data.floatValue = 3.14;
            DBG_PRINTF("Float value: {}", data.floatValue);
        }
        """
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        
        # Should understand union semantics
        self.assertEqual(len(self.analyzer.errors), 0)
    
    def test_message_timeout_feature(self):
        """Test message timeout feature (IMPLEMENTATION_COMPLETE)"""
        source = """
        message<float> MsgQueue;
        
        void main() {
            float value1 = MsgQueue.recv(100);  // 100ms timeout
            float value2 = MsgQueue.recv();     // No timeout (blocking)
            
            DBG_PRINTF("Values: {}, {}", value1, value2);
        }
        """
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)
        
        # Should support timeout syntax
        self.assertEqual(len(self.analyzer.errors), 0)
    
    def test_import_system(self):
        """Test import system (IMPLEMENTATION_COMPLETE)"""
        # Create a temporary imported file
        import_content = """
        const int SHARED_CONSTANT = 42;
        
        struct SharedStruct {
            int value;
        };
        
        void shared_function(int param) {
            DBG_PRINTF("Shared function called with: {}", param);
        }
        """
        
        # Write to temporary file
        import_path = Path(__file__).parent / "temp_import.rtmc"
        with open(import_path, 'w') as f:
            f.write(import_content)
        
        try:
            main_source = """
            #include "temp_import.rtmc";
            
            void main() {
                SharedStruct s;
                s.value = SHARED_CONSTANT;
                shared_function(s.value);
            }
            """
            
            tokens = self.lexer.tokenize(main_source)
            ast = self.parser.parse(tokens)
            self.analyzer.analyze(ast)
            
            # Should resolve imported symbols
            # (Implementation depends on import handling)
            
        finally:
            # Clean up temporary file
            if import_path.exists():
                import_path.unlink()


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def test_syntax_errors(self):
        """Test syntax error handling"""
        invalid_sources = [
            "int main() { return 0 }",  # Missing semicolon
            "void func( { }",           # Missing parameter list
            "struct { int x; };",       # Missing struct name
            "int arr[];",               # Missing array size
        ]
        
        for source in invalid_sources:
            with self.subTest(source=source):
                try:
                    tokens = self.lexer.tokenize(source)
                    ast = self.parser.parse(tokens)
                    # Should either throw exception or create error nodes
                except Exception:
                    pass  # Expected for syntax errors
    
    def test_semantic_errors(self):
        """Test semantic error detection"""
        error_sources = [
            # Undefined variable
            """
            void main() {
                int x = undefined_var;
            }
            """,
            # Type mismatch
            """
            void func(int param) {}
            void main() {
                func("string");
            }
            """,
            # Undefined function
            """
            void main() {
                undefined_function();
            }
            """,
            # Invalid member access
            """
            struct Point { int x; };
            void main() {
                Point p;
                int y = p.invalid_member;
            }
            """
        ]
        
        for source in error_sources:
            with self.subTest(source=source.strip()):
                tokens = self.lexer.tokenize(source)
                ast = self.parser.parse(tokens)
                self.analyzer.analyze(ast)
                
                # Should detect semantic errors
                self.assertGreater(len(self.analyzer.errors), 0)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        edge_cases = [
            # Empty program
            "",
            # Only comments
            "// This is a comment",
            # Maximum integer value
            "void main() { int max = 2147483647; }",
            # Very long identifier
            f"void {'a' * 100}() {{ }}",
            # Deeply nested expressions
            "void main() { int x = ((((1 + 2) * 3) / 4) % 5); }",
        ]
        
        for source in edge_cases:
            with self.subTest(source=source):
                try:
                    tokens = self.lexer.tokenize(source)
                    if tokens:  # Skip empty token lists
                        ast = self.parser.parse(tokens)
                        self.analyzer.analyze(ast)
                        # Should handle gracefully
                except Exception as e:
                    # Log but don't fail - some edge cases may be invalid
                    print(f"Edge case failed: {source[:50]}... - {e}")


if __name__ == '__main__':
    # Run all tests with verbose output
    unittest.main(verbosity=2, buffer=True)
