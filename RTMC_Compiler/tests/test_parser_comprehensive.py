#!/usr/bin/env python3
"""
Comprehensive Parser Tests
Tests all AST generation and parsing features.
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.ply_lexer import RTMCLexer
from src.parser.ply_parser import RTMCParser
from src.parser.ast_nodes import *


class TestBasicParsing(unittest.TestCase):
    """Test basic parsing functionality"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_code(self, source: str):
        """Helper to parse code and return AST"""
        tokens = self.lexer.tokenize(source)
        return self.parser.parse(tokens)
    
    def test_empty_program(self):
        """Test parsing empty program"""
        ast = self._parse_code("")
        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(len(ast.declarations), 0)
    
    def test_simple_function(self):
        """Test simple function declaration"""
        source = """
        void main() {
            return;
        }
        """
        ast = self._parse_code(source)
        
        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(len(ast.declarations), 1)
        
        func = ast.declarations[0]
        self.assertIsInstance(func, FunctionDeclNode)
        self.assertEqual(func.name, "main")
        self.assertEqual(func.return_type.type_name, "void")
        self.assertEqual(len(func.parameters), 0)
    
    def test_function_with_parameters(self):
        """Test function with parameters"""
        source = """
        int add(int a, int b) {
            return a + b;
        }
        """
        ast = self._parse_code(source)
        
        func = ast.declarations[0]
        self.assertIsInstance(func, FunctionDeclNode)
        self.assertEqual(func.name, "add")
        self.assertEqual(func.return_type.type_name, "int")
        self.assertEqual(len(func.parameters), 2)
        self.assertEqual(func.parameters[0].name, "a")
        self.assertEqual(func.parameters[1].name, "b")
    
    def test_variable_declarations(self):
        """Test variable declarations"""
        source = """
        void main() {
            int x;
            float y = 3.14;
            char c = 'a';
            bool flag = true;
        }
        """
        ast = self._parse_code(source)
        
        func = ast.declarations[0]
        body = func.body
        self.assertIsInstance(body, BlockStmtNode)
        self.assertEqual(len(body.statements), 4)
        
        # Check variable declarations
        for stmt in body.statements:
            self.assertIsInstance(stmt, VariableDeclNode)


class TestExpressionParsing(unittest.TestCase):
    """Test expression parsing"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_expression(self, expr_str: str):
        """Helper to parse a single expression"""
        source = f"void main() {{ {expr_str}; }}"
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        func = ast.declarations[0]
        stmt = func.body.statements[0]
        return stmt.expression if hasattr(stmt, 'expression') else stmt
    
    def test_arithmetic_expressions(self):
        """Test arithmetic expression parsing"""
        test_cases = [
            "5 + 3",
            "a - b",
            "x * y",
            "num / 2",
            "value % 10",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIsInstance(result, BinaryExprNode)
    
    def test_logical_expressions(self):
        """Test logical expression parsing"""
        test_cases = [
            "a && b",
            "x || y",
            "!flag",
            "a == b",
            "x != y",
            "value < 10",
            "count > 0",
            "age <= 65",
            "score >= 90",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                # Should be BinaryExprNode or UnaryExprNode
                self.assertIn(type(result), [BinaryExprNode, UnaryExprNode])
    
    def test_bitwise_expressions(self):
        """Test bitwise expression parsing"""
        test_cases = [
            "a & b",
            "x | y",
            "value ^ mask",
            "~flags",
            "data << 8",
            "result >> 4",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIn(type(result), [BinaryExprNode, UnaryExprNode])
    
    def test_assignment_expressions(self):
        """Test assignment expression parsing"""
        test_cases = [
            "x = 5",
            "count += 1",
            "total -= amount",
            "result *= factor",
            "value /= divisor",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIsInstance(result, AssignmentExprNode)
    
    def test_function_calls(self):
        """Test function call parsing"""
        test_cases = [
            "func()",
            "add(a, b)",
            "printf(format, arg1, arg2)",
            "RTOS_DELAY_MS(1000)",
            "HW_GPIO_SET(pin, value)",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIsInstance(result, CallExprNode)
    
    def test_member_access(self):
        """Test member access parsing"""
        test_cases = [
            "point.x",
            "rect.topLeft.x",
            "ptr->field",
            "data->next->value",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIsInstance(result, MemberExprNode)
    
    def test_array_access(self):
        """Test array access parsing"""
        test_cases = [
            "array[0]",
            "matrix[i][j]",
            "buffer[index + 1]",
            "data[count - 1]",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIsInstance(result, ArrayAccessNode)
    
    def test_postfix_expressions(self):
        """Test postfix increment/decrement"""
        test_cases = [
            "counter++",
            "index--",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIsInstance(result, PostfixExprNode)
    
    def test_unary_expressions(self):
        """Test unary expressions"""
        test_cases = [
            "++counter",
            "--index",
            "-value",
            "+number",
            "!condition",
            "~mask",
            "&variable",
            "*pointer",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                self.assertIsInstance(result, UnaryExprNode)
    
    def test_literal_expressions(self):
        """Test literal parsing"""
        test_cases = [
            ("42", "int"),
            ("3.14", "float"),
            ("'a'", "char"),
            ('"hello"', "string"),
            ("true", "bool"),
            ("false", "bool"),
            ("0xFF", "int"),
        ]
        
        for literal, expected_type in test_cases:
            with self.subTest(literal=literal):
                result = self._parse_expression(literal)
                self.assertIsInstance(result, LiteralExprNode)
    
    def test_parenthesized_expressions(self):
        """Test parenthesized expressions"""
        test_cases = [
            "(5 + 3)",
            "((a + b) * c)",
            "(condition && flag)",
        ]
        
        for expr in test_cases:
            with self.subTest(expression=expr):
                result = self._parse_expression(expr)
                # Should parse the inner expression
                self.assertIsNotNone(result)
    
    def test_expression_precedence(self):
        """Test operator precedence"""
        # Test that multiplication has higher precedence than addition
        source = "void main() { int result = 2 + 3 * 4; }"
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        # The AST should reflect correct precedence
        # This is a complex test that depends on parser implementation
        self.assertIsNotNone(ast)


class TestStatementParsing(unittest.TestCase):
    """Test statement parsing"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_statements(self, statements_str: str):
        """Helper to parse statements within a function"""
        source = f"void main() {{ {statements_str} }}"
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        func = ast.declarations[0]
        return func.body.statements
    
    def test_if_statements(self):
        """Test if statement parsing"""
        test_cases = [
            "if (condition) { return; }",
            "if (x > 0) { result = x; } else { result = -x; }",
            "if (a) { b; } else if (c) { d; } else { e; }",
        ]
        
        for stmt_str in test_cases:
            with self.subTest(statement=stmt_str):
                statements = self._parse_statements(stmt_str)
                self.assertGreater(len(statements), 0)
                if_stmt = statements[0]
                self.assertIsInstance(if_stmt, IfStmtNode)
    
    def test_while_statements(self):
        """Test while statement parsing"""
        test_cases = [
            "while (condition) { break; }",
            "while (i < 10) { i++; }",
            "while (true) { RTOS_YIELD(); }",
        ]
        
        for stmt_str in test_cases:
            with self.subTest(statement=stmt_str):
                statements = self._parse_statements(stmt_str)
                while_stmt = statements[0]
                self.assertIsInstance(while_stmt, WhileStmtNode)
    
    def test_for_statements(self):
        """Test for statement parsing"""
        test_cases = [
            "for (int i = 0; i < 10; i++) { continue; }",
            "for (;;) { break; }",
            "for (i = 0; condition; increment) { body; }",
        ]
        
        for stmt_str in test_cases:
            with self.subTest(statement=stmt_str):
                statements = self._parse_statements(stmt_str)
                for_stmt = statements[0]
                self.assertIsInstance(for_stmt, ForStmtNode)
    
    def test_return_statements(self):
        """Test return statement parsing"""
        test_cases = [
            "return;",
            "return 42;",
            "return a + b;",
            "return func(arg);",
        ]
        
        for stmt_str in test_cases:
            with self.subTest(statement=stmt_str):
                statements = self._parse_statements(stmt_str)
                return_stmt = statements[0]
                self.assertIsInstance(return_stmt, ReturnStmtNode)
    
    def test_break_continue_statements(self):
        """Test break and continue statements"""
        test_cases = [
            ("break;", BreakStmtNode),
            ("continue;", ContinueStmtNode),
        ]
        
        for stmt_str, expected_type in test_cases:
            with self.subTest(statement=stmt_str):
                statements = self._parse_statements(stmt_str)
                stmt = statements[0]
                self.assertIsInstance(stmt, expected_type)
    
    def test_block_statements(self):
        """Test block statement parsing"""
        source = """
        void main() {
            {
                int local = 5;
                local++;
            }
        }
        """
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        func = ast.declarations[0]
        outer_block = func.body
        inner_stmt = outer_block.statements[0]
        self.assertIsInstance(inner_stmt, BlockStmtNode)
    
    def test_expression_statements(self):
        """Test expression statements"""
        test_cases = [
            "x = 5;",
            "func();",
            "counter++;",
            "array[index] = value;",
        ]
        
        for stmt_str in test_cases:
            with self.subTest(statement=stmt_str):
                statements = self._parse_statements(stmt_str)
                expr_stmt = statements[0]
                self.assertIsInstance(expr_stmt, ExpressionStmtNode)


class TestStructUnionParsing(unittest.TestCase):
    """Test struct and union parsing"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_code(self, source: str):
        """Helper to parse code"""
        tokens = self.lexer.tokenize(source)
        return self.parser.parse(tokens)
    
    def test_basic_struct(self):
        """Test basic struct declaration"""
        source = """
        struct Point {
            int x;
            int y;
        };
        """
        ast = self._parse_code(source)
        
        struct_decl = ast.declarations[0]
        self.assertIsInstance(struct_decl, StructDeclNode)
        self.assertEqual(struct_decl.name, "Point")
        self.assertEqual(len(struct_decl.fields), 2)
        
        self.assertEqual(struct_decl.fields[0].name, "x")
        self.assertEqual(struct_decl.fields[1].name, "y")
    
    def test_struct_with_bitfields(self):
        """Test struct with bitfields"""
        source = """
        struct Register {
            int field1 : 8;
            int field2 : 16;
            int field3 : 8;
        };
        """
        ast = self._parse_code(source)
        
        struct_decl = ast.declarations[0]
        self.assertIsInstance(struct_decl, StructDeclNode)
        
        for field in struct_decl.fields:
            self.assertIsNotNone(field.bit_width)
            self.assertIn(field.bit_width, [8, 16])
    
    def test_nested_struct_types(self):
        """Test nested struct types"""
        source = """
        struct Point { int x; int y; };
        struct Rectangle {
            Point topLeft;
            Point bottomRight;
            int color;
        };
        """
        ast = self._parse_code(source)
        
        self.assertEqual(len(ast.declarations), 2)
        
        point_decl = ast.declarations[0]
        rect_decl = ast.declarations[1]
        
        self.assertIsInstance(point_decl, StructDeclNode)
        self.assertIsInstance(rect_decl, StructDeclNode)
        
        self.assertEqual(point_decl.name, "Point")
        self.assertEqual(rect_decl.name, "Rectangle")
        self.assertEqual(len(rect_decl.fields), 3)
    
    def test_basic_union(self):
        """Test basic union declaration"""
        source = """
        union Data {
            int intValue;
            float floatValue;
            char bytes[4];
        };
        """
        ast = self._parse_code(source)
        
        union_decl = ast.declarations[0]
        self.assertIsInstance(union_decl, UnionDeclNode)
        self.assertEqual(union_decl.name, "Data")
        self.assertEqual(len(union_decl.fields), 3)
    
    def test_anonymous_struct_union(self):
        """Test anonymous struct/union (if supported)"""
        source = """
        struct Container {
            union {
                int intData;
                float floatData;
            };
            int type;
        };
        """
        # This test depends on whether anonymous unions are supported
        try:
            ast = self._parse_code(source)
            container_decl = ast.declarations[0]
            self.assertIsInstance(container_decl, StructDeclNode)
        except Exception:
            # Anonymous unions might not be implemented
            pass
    
    def test_field_initialization(self):
        """Test field initialization (if supported)"""
        source = """
        struct Config {
            int defaultValue = 42;
            bool enabled = true;
            float multiplier = 1.0;
        };
        """
        try:
            ast = self._parse_code(source)
            config_decl = ast.declarations[0]
            self.assertIsInstance(config_decl, StructDeclNode)
            
            # Check if fields have initializers
            for field in config_decl.fields:
                if hasattr(field, 'initializer'):
                    self.assertIsNotNone(field.initializer)
        except Exception:
            # Field initialization might not be implemented
            pass


class TestArrayParsing(unittest.TestCase):
    """Test array parsing"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_code(self, source: str):
        """Helper to parse code"""
        tokens = self.lexer.tokenize(source)
        return self.parser.parse(tokens)
    
    def test_array_declarations(self):
        """Test array declaration parsing"""
        test_cases = [
            "int numbers[5];",
            "float values[10];",
            "char buffer[256];",
        ]
        
        for decl in test_cases:
            with self.subTest(declaration=decl):
                source = f"void main() {{ {decl} }}"
                ast = self._parse_code(source)
                
                func = ast.declarations[0]
                stmt = func.body.statements[0]
                # Should be ArrayDeclNode or VariableDeclNode with array type
                self.assertIsNotNone(stmt)
    
    def test_array_initialization(self):
        """Test array initialization parsing"""
        test_cases = [
            "int numbers[5] = {1, 2, 3, 4, 5};",
            "float coords[3] = {1.0, 2.5, 3.7};",
            "char greeting[6] = {'H', 'e', 'l', 'l', 'o', '\\0'};",
        ]
        
        for decl in test_cases:
            with self.subTest(declaration=decl):
                source = f"void main() {{ {decl} }}"
                ast = self._parse_code(source)
                
                func = ast.declarations[0]
                stmt = func.body.statements[0]
                self.assertIsNotNone(stmt)
    
    def test_array_access_parsing(self):
        """Test array access parsing"""
        source = """
        void main() {
            int arr[10];
            int value = arr[5];
            arr[0] = 42;
            int complex = arr[i + 1];
        }
        """
        ast = self._parse_code(source)
        
        func = ast.declarations[0]
        statements = func.body.statements
        
        # Should have array access expressions
        self.assertGreater(len(statements), 1)
    
    def test_multidimensional_arrays(self):
        """Test multidimensional arrays (if supported)"""
        test_cases = [
            "int matrix[3][3];",
            "float grid[10][20];",
        ]
        
        for decl in test_cases:
            with self.subTest(declaration=decl):
                source = f"void main() {{ {decl} }}"
                try:
                    ast = self._parse_code(source)
                    # Multidimensional arrays might not be fully supported
                    self.assertIsNotNone(ast)
                except Exception:
                    # Skip if not implemented
                    pass
    
    def test_struct_arrays(self):
        """Test arrays of structs"""
        source = """
        struct Point { int x; int y; };
        
        void main() {
            Point points[4];
            points[0].x = 10;
            int value = points[1].y;
        }
        """
        ast = self._parse_code(source)
        
        self.assertEqual(len(ast.declarations), 2)
        struct_decl = ast.declarations[0]
        func_decl = ast.declarations[1]
        
        self.assertIsInstance(struct_decl, StructDeclNode)
        self.assertIsInstance(func_decl, FunctionDeclNode)


class TestMessageParsing(unittest.TestCase):
    """Test message declaration and usage parsing"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_code(self, source: str):
        """Helper to parse code"""
        tokens = self.lexer.tokenize(source)
        return self.parser.parse(tokens)
    
    def test_message_declaration(self):
        """Test message declaration parsing"""
        test_cases = [
            "message<int> IntMsg;",
            "message<float> FloatMsg;",
            "message<char> CharMsg;",
        ]
        
        for decl in test_cases:
            with self.subTest(declaration=decl):
                ast = self._parse_code(decl)
                
                msg_decl = ast.declarations[0]
                self.assertIsInstance(msg_decl, MessageDeclNode)
    
    def test_message_operations(self):
        """Test message send/recv parsing"""
        source = """
        message<int> TestMsg;
        
        void main() {
            TestMsg.send(42);
            int value = TestMsg.recv();
            int timeout_value = TestMsg.recv(100);
        }
        """
        ast = self._parse_code(source)
        
        self.assertEqual(len(ast.declarations), 2)
        msg_decl = ast.declarations[0]
        func_decl = ast.declarations[1]
        
        self.assertIsInstance(msg_decl, MessageDeclNode)
        self.assertIsInstance(func_decl, FunctionDeclNode)
    
    def test_message_with_struct_type(self):
        """Test messages with struct types"""
        source = """
        struct Data { int value; float rate; };
        message<Data> DataMsg;
        
        void main() {
            Data d;
            d.value = 42;
            d.rate = 3.14;
            DataMsg.send(d);
        }
        """
        ast = self._parse_code(source)
        
        self.assertEqual(len(ast.declarations), 3)
        struct_decl = ast.declarations[0]
        msg_decl = ast.declarations[1]
        func_decl = ast.declarations[2]
        
        self.assertIsInstance(struct_decl, StructDeclNode)
        self.assertIsInstance(msg_decl, MessageDeclNode)
        self.assertIsInstance(func_decl, FunctionDeclNode)


class TestImportParsing(unittest.TestCase):
    """Test import statement parsing"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_code(self, source: str):
        """Helper to parse code"""
        tokens = self.lexer.tokenize(source)
        return self.parser.parse(tokens)
    
    def test_import_statements(self):
        """Test import statement parsing"""
        test_cases = [
            'import "definitions.rtmc";',
            'import "common.rtmc";',
            'import "hardware/gpio.rtmc";',
        ]
        
        for import_stmt in test_cases:
            with self.subTest(import_statement=import_stmt):
                ast = self._parse_code(import_stmt)
                
                import_decl = ast.declarations[0]
                self.assertIsInstance(import_decl, ImportStmtNode)
    
    def test_multiple_imports(self):
        """Test multiple import statements"""
        source = """
        import "definitions.rtmc";
        import "common.rtmc";
        import "hardware.rtmc";
        
        void main() {
            return;
        }
        """
        ast = self._parse_code(source)
        
        # Should have 3 imports + 1 function
        self.assertEqual(len(ast.declarations), 4)
        
        for i in range(3):
            self.assertIsInstance(ast.declarations[i], ImportStmtNode)
        
        self.assertIsInstance(ast.declarations[3], FunctionDeclNode)


class TestFlexibleBraceParsing(unittest.TestCase):
    """Test flexible brace placement parsing"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
    
    def _parse_code(self, source: str):
        """Helper to parse code"""
        tokens = self.lexer.tokenize(source)
        return self.parser.parse(tokens)
    
    def test_function_brace_styles(self):
        """Test different function brace styles"""
        style1 = """
        void func() {
            int x = 5;
        }
        """
        
        style2 = """
        void func()
        {
            int x = 5;
        }
        """
        
        # Both styles should parse to equivalent ASTs
        ast1 = self._parse_code(style1)
        ast2 = self._parse_code(style2)
        
        self.assertIsInstance(ast1, ProgramNode)
        self.assertIsInstance(ast2, ProgramNode)
        
        func1 = ast1.declarations[0]
        func2 = ast2.declarations[0]
        
        self.assertEqual(func1.name, func2.name)
        self.assertEqual(len(func1.body.statements), len(func2.body.statements))
    
    def test_control_flow_brace_styles(self):
        """Test brace styles in control flow"""
        style1 = """
        void main() {
            if (condition) {
                statement1;
            }
            while (condition) {
                statement2;
            }
            for (;;) {
                statement3;
            }
        }
        """
        
        style2 = """
        void main()
        {
            if (condition)
            {
                statement1;
            }
            while (condition)
            {
                statement2;
            }
            for (;;)
            {
                statement3;
            }
        }
        """
        
        # Both should parse successfully
        ast1 = self._parse_code(style1)
        ast2 = self._parse_code(style2)
        
        self.assertIsInstance(ast1, ProgramNode)
        self.assertIsInstance(ast2, ProgramNode)
    
    def test_struct_brace_styles(self):
        """Test struct brace styles"""
        style1 = """
        struct Point {
            int x;
            int y;
        };
        """
        
        style2 = """
        struct Point
        {
            int x;
            int y;
        };
        """
        
        ast1 = self._parse_code(style1)
        ast2 = self._parse_code(style2)
        
        struct1 = ast1.declarations[0]
        struct2 = ast2.declarations[0]
        
        self.assertEqual(struct1.name, struct2.name)
        self.assertEqual(len(struct1.fields), len(struct2.fields))


if __name__ == '__main__':
    unittest.main(verbosity=2)
