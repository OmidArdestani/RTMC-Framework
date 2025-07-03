"""
Test suite for Mini-C compiler
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lexer.tokenizer import Tokenizer, TokenType
from parser.parser import Parser
from semantic.analyzer import SemanticAnalyzer
from optimizer.optimizer import Optimizer
from bytecode.generator import BytecodeGenerator
from bytecode.writer import BytecodeWriter, BytecodeReader
from vm.virtual_machine import VirtualMachine

class TestTokenizer(unittest.TestCase):
    """Test tokenizer functionality"""
    
    def test_basic_tokens(self):
        """Test basic token recognition"""
        source = "int main() { return 0; }"
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        
        expected_types = [
            TokenType.INT, TokenType.IDENTIFIER, TokenType.LEFT_PAREN,
            TokenType.RIGHT_PAREN, TokenType.LEFT_BRACE, TokenType.RETURN,
            TokenType.INTEGER, TokenType.SEMICOLON, TokenType.RIGHT_BRACE,
            TokenType.EOF
        ]
        
        actual_types = [token.type for token in tokens]
        self.assertEqual(actual_types, expected_types)
    
    def test_hardware_keywords(self):
        """Test hardware function keywords"""
        source = "HW_GPIO_INIT(25, 1);"
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.HW_GPIO_INIT)
        self.assertEqual(tokens[1].type, TokenType.LEFT_PAREN)
        self.assertEqual(tokens[2].type, TokenType.INTEGER)
        self.assertEqual(tokens[2].value, "25")
    
    def test_rtos_keywords(self):
        """Test RTOS function keywords"""
        source = "RTOS_CREATE_TASK(func, \"name\", 1024, 5, 0);"
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.RTOS_CREATE_TASK)
        self.assertEqual(tokens[4].type, TokenType.STRING)
        self.assertEqual(tokens[4].value, "name")
    
    def test_string_literals(self):
        """Test string literal parsing"""
        source = '"Hello, World!"'
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, "Hello, World!")
    
    def test_numeric_literals(self):
        """Test numeric literal parsing"""
        source = "42 3.14 'A'"
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.INTEGER)
        self.assertEqual(tokens[0].value, "42")
        self.assertEqual(tokens[1].type, TokenType.FLOAT)
        self.assertEqual(tokens[1].value, "3.14")
        self.assertEqual(tokens[2].type, TokenType.CHAR)
        self.assertEqual(tokens[2].value, "A")

class TestParser(unittest.TestCase):
    """Test parser functionality"""
    
    def test_function_declaration(self):
        """Test function declaration parsing"""
        source = "void main() { return; }"
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        self.assertEqual(len(ast.declarations), 1)
        func_decl = ast.declarations[0]
        self.assertEqual(func_decl.name, "main")
        self.assertEqual(func_decl.return_type.type_name, "void")
    
    def test_variable_declaration(self):
        """Test variable declaration parsing"""
        source = "int x = 42;"
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        self.assertEqual(len(ast.declarations), 1)
        var_decl = ast.declarations[0]
        self.assertEqual(var_decl.name, "x")
        self.assertEqual(var_decl.type.type_name, "int")
        self.assertIsNotNone(var_decl.initializer)
    
    def test_struct_declaration(self):
        """Test struct declaration parsing"""
        source = """
        struct Point {
            int x;
            int y;
        };
        """
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        self.assertEqual(len(ast.declarations), 1)
        struct_decl = ast.declarations[0]
        self.assertEqual(struct_decl.name, "Point")
        self.assertEqual(len(struct_decl.fields), 2)
    
    def test_if_statement(self):
        """Test if statement parsing"""
        source = """
        void main() {
            if (x > 0) {
                return 1;
            } else {
                return 0;
            }
        }
        """
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        func_decl = ast.declarations[0]
        if_stmt = func_decl.body.statements[0]
        self.assertIsNotNone(if_stmt.condition)
        self.assertIsNotNone(if_stmt.then_stmt)
        self.assertIsNotNone(if_stmt.else_stmt)

class TestSemanticAnalyzer(unittest.TestCase):
    """Test semantic analyzer functionality"""
    
    def test_undefined_variable(self):
        """Test undefined variable detection"""
        source = """
        void main() {
            int x = y;  // y is undefined
        }
        """
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception):
            analyzer.analyze(ast)
    
    def test_type_mismatch(self):
        """Test type mismatch detection"""
        source = """
        void main() {
            int x = "string";  // Type mismatch
        }
        """
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception):
            analyzer.analyze(ast)
    
    def test_valid_program(self):
        """Test valid program analysis"""
        source = """
        void main() {
            int x = 42;
            x = x + 1;
        }
        """
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = SemanticAnalyzer()
        # Should not raise exception
        analyzer.analyze(ast)

class TestBytecodeGeneration(unittest.TestCase):
    """Test bytecode generation"""
    
    def test_simple_program(self):
        """Test simple program bytecode generation"""
        source = """
        void main() {
            int x = 42;
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
        
        self.assertIsNotNone(program)
        self.assertGreater(len(program.instructions), 0)
        self.assertIn('main', program.functions)
    
    def test_bytecode_file_io(self):
        """Test bytecode file writing and reading"""
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
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix='.vmb', delete=False) as f:
            temp_filename = f.name
        
        try:
            writer = BytecodeWriter()
            writer.write(program, temp_filename)
            
            # Read back
            reader = BytecodeReader()
            loaded_program = reader.read(temp_filename)
            
            self.assertEqual(len(program.instructions), len(loaded_program.instructions))
            self.assertEqual(program.functions, loaded_program.functions)
        
        finally:
            os.unlink(temp_filename)

class TestVirtualMachine(unittest.TestCase):
    """Test virtual machine functionality"""
    
    def test_basic_execution(self):
        """Test basic program execution"""
        source = """
        void main() {
            int x = 42;
            DBG_PRINT("Hello World");
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
        
        vm = VirtualMachine()
        vm.load_program(program)
        
        # Should not raise exception
        vm.run()

class TestExamples(unittest.TestCase):
    """Test example programs"""
    
    def test_blink_example(self):
        """Test blink example compilation"""
        example_path = Path(__file__).parent.parent / "examples" / "blink.mc"
        if example_path.exists():
            with open(example_path, 'r') as f:
                source = f.read()
            
            tokenizer = Tokenizer(source)
            tokens = tokenizer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)
            
            generator = BytecodeGenerator()
            program = generator.generate(ast)
            
            self.assertIsNotNone(program)
            self.assertGreater(len(program.instructions), 0)

if __name__ == '__main__':
    unittest.main()
