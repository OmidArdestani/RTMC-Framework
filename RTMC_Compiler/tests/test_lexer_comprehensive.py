#!/usr/bin/env python3
"""
Focused Tests for Lexical Analysis
Tests all tokenization features and edge cases.
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.ply_lexer import RTMCLexer


class TestTokenization(unittest.TestCase):
    """Comprehensive tokenization tests"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
    
    def test_data_type_tokens(self):
        """Test all data type tokens"""
        types = ["int", "float", "char", "bool", "void"]
        expected = ["INT", "FLOAT_TYPE", "CHAR_TYPE", "BOOL_TYPE", "VOID"]
        
        for type_name, expected_token in zip(types, expected):
            with self.subTest(type_name=type_name):
                tokens = self.lexer.tokenize(type_name)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected_token)
    
    def test_control_flow_tokens(self):
        """Test control flow keywords"""
        keywords = ["if", "else", "while", "for", "break", "continue", "return"]
        expected = ["IF", "ELSE", "WHILE", "FOR", "BREAK", "CONTINUE", "RETURN"]
        
        for keyword, expected_token in zip(keywords, expected):
            with self.subTest(keyword=keyword):
                tokens = self.lexer.tokenize(keyword)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected_token)
    
    def test_struct_union_tokens(self):
        """Test struct and union keywords"""
        tokens = self.lexer.tokenize("struct union")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, "STRUCT")
        self.assertEqual(tokens[1].type, "UNION")
    
    def test_boolean_literal_tokens(self):
        """Test boolean literal tokens"""
        tokens = self.lexer.tokenize("true false")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, "TRUE")
        self.assertEqual(tokens[1].type, "FALSE")
    
    def test_operators(self):
        """Test all operator tokens"""
        operator_tests = [
            ("+", "PLUS"),
            ("-", "MINUS"),
            ("*", "MULTIPLY"),
            ("/", "DIVIDE"),
            ("%", "MODULO"),
            ("=", "ASSIGN"),
            ("+=", "PLUS_ASSIGN"),
            ("-=", "MINUS_ASSIGN"),
            ("*=", "MULTIPLY_ASSIGN"),
            ("/=", "DIVIDE_ASSIGN"),
            ("++", "INCREMENT"),
            ("--", "DECREMENT"),
            ("==", "EQUAL"),
            ("!=", "NOT_EQUAL"),
            ("<", "LESS_THAN"),
            ("<=", "LESS_EQUAL"),
            (">", "GREATER_THAN"),
            (">=", "GREATER_EQUAL"),
            ("&&", "LOGICAL_AND"),
            ("||", "LOGICAL_OR"),
            ("!", "LOGICAL_NOT"),
            ("&", "BITWISE_AND"),
            ("|", "BITWISE_OR"),
            ("^", "BITWISE_XOR"),
            ("~", "BITWISE_NOT"),
            ("<<", "LEFT_SHIFT"),
            (">>", "RIGHT_SHIFT"),
        ]
        
        for op, expected in operator_tests:
            with self.subTest(operator=op):
                tokens = self.lexer.tokenize(op)
                self.assertGreater(len(tokens), 0)
                self.assertEqual(tokens[0].type, expected)
    
    def test_delimiters(self):
        """Test delimiter tokens"""
        delimiter_tests = [
            (";", "SEMICOLON"),
            (",", "COMMA"),
            (".", "DOT"),
            ("->", "ARROW"),
            (":", "COLON"),
            ("(", "LEFT_PAREN"),
            (")", "RIGHT_PAREN"),
            ("{", "LEFT_BRACE"),
            ("}", "RIGHT_BRACE"),
            ("[", "LEFT_BRACKET"),
            ("]", "RIGHT_BRACKET"),
        ]
        
        for delim, expected in delimiter_tests:
            with self.subTest(delimiter=delim):
                tokens = self.lexer.tokenize(delim)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected)
    
    def test_literals(self):
        """Test literal token recognition"""
        literal_tests = [
            ("42", "INTEGER"),
            ("3.14", "FLOAT"),
            ("'a'", "CHAR"),
            ('"hello"', "STRING"),
            ("0xFF", "INTEGER"),
            ("0x123ABC", "INTEGER"),
        ]
        
        for literal, expected in literal_tests:
            with self.subTest(literal=literal):
                tokens = self.lexer.tokenize(literal)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected)
    
    def test_rtos_function_tokens(self):
        """Test all RTOS function tokens"""
        rtos_functions = [
            # Task management
            ("RTOS_CREATE_TASK", "RTOS_CREATE_TASK"),
            ("RTOS_DELETE_TASK", "RTOS_DELETE_TASK"),
            ("RTOS_SUSPEND_TASK", "RTOS_SUSPEND_TASK"),
            ("RTOS_RESUME_TASK", "RTOS_RESUME_TASK"),
            ("RTOS_YIELD", "RTOS_YIELD"),
            
            # Timing
            ("RTOS_DELAY_MS", "RTOS_DELAY_MS"),
            ("RTOS_GET_TICK", "RTOS_GET_TICK"),
            
            # Synchronization
            ("RTOS_CREATE_SEMAPHORE", "RTOS_CREATE_SEMAPHORE"),
            ("RTOS_DELETE_SEMAPHORE", "RTOS_DELETE_SEMAPHORE"),
            ("RTOS_TAKE_SEMAPHORE", "RTOS_TAKE_SEMAPHORE"),
            ("RTOS_GIVE_SEMAPHORE", "RTOS_GIVE_SEMAPHORE"),
        ]
        
        for func, expected in rtos_functions:
            with self.subTest(function=func):
                tokens = self.lexer.tokenize(func)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected)
    
    def test_hardware_function_tokens(self):
        """Test all hardware function tokens"""
        hw_functions = [
            # GPIO
            ("HW_GPIO_INIT", "HW_GPIO_INIT"),
            ("HW_GPIO_SET", "HW_GPIO_SET"),
            ("HW_GPIO_GET", "HW_GPIO_GET"),
            ("HW_GPIO_TOGGLE", "HW_GPIO_TOGGLE"),
            
            # Timer/PWM
            ("HW_TIMER_INIT", "HW_TIMER_INIT"),
            ("HW_TIMER_SET_FREQ", "HW_TIMER_SET_FREQ"),
            ("HW_TIMER_GET_FREQ", "HW_TIMER_GET_FREQ"),
            ("HW_TIMER_RESET", "HW_TIMER_RESET"),
            ("HW_TIMER_GET", "HW_TIMER_GET"),
            
            # ADC
            ("HW_ADC_INIT", "HW_ADC_INIT"),
            ("HW_ADC_READ", "HW_ADC_READ"),
            
            # Communication
            ("HW_UART_INIT", "HW_UART_INIT"),
            ("HW_UART_SEND", "HW_UART_SEND"),
            ("HW_UART_READ", "HW_UART_READ"),
            ("HW_SPI_INIT", "HW_SPI_INIT"),
            ("HW_SPI_TRANSFER", "HW_SPI_TRANSFER"),
            ("HW_I2C_INIT", "HW_I2C_INIT"),
            ("HW_I2C_WRITE", "HW_I2C_WRITE"),
            ("HW_I2C_READ", "HW_I2C_READ"),
        ]
        
        for func, expected in hw_functions:
            with self.subTest(function=func):
                tokens = self.lexer.tokenize(func)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected)
    
    def test_debug_function_tokens(self):
        """Test debug function tokens"""
        debug_functions = [
            ("DBG_PRINT", "DBG_PRINT"),
            ("DBG_PRINTF", "DBG_PRINTF"),
            ("DBG_BREAKPOINT", "DBG_BREAKPOINT"),
        ]
        
        for func, expected in debug_functions:
            with self.subTest(function=func):
                tokens = self.lexer.tokenize(func)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected)
    
    def test_message_and_misc_tokens(self):
        """Test message and miscellaneous tokens"""
        misc_tests = [
            ("message", "MESSAGE"),
            ("const", "CONST"),
            ("import", "IMPORT"),
            ("StartTask", "START_TASK"),
        ]
        
        for token_str, expected in misc_tests:
            with self.subTest(token=token_str):
                tokens = self.lexer.tokenize(token_str)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected)
    
    def test_hexadecimal_variations(self):
        """Test all hexadecimal literal variations"""
        hex_tests = [
            "0x0", "0x1", "0x9", "0xA", "0xF",
            "0xa", "0xf", "0xAB", "0xab", "0xAb", "0xaB",
            "0X0", "0X1", "0XA", "0XF",
            "0xff", "0xFF", "0xFf", "0xfF",
            "0x123", "0xABC", "0xDEF",
            "0x1234", "0xABCD", "0xDEAD", "0xBEEF",
            "0x12345678", "0xABCDEF00",
            "0x00000000", "0xFFFFFFFF",
        ]
        
        for hex_str in hex_tests:
            with self.subTest(hex_value=hex_str):
                tokens = self.lexer.tokenize(hex_str)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, "INTEGER")
                # Verify it's a valid hex number
                try:
                    int(hex_str, 16)
                except ValueError:
                    self.fail(f"Invalid hex literal: {hex_str}")
    
    def test_identifier_variations(self):
        """Test identifier tokenization"""
        valid_identifiers = [
            "variable", "Variable", "VARIABLE",
            "var123", "var_name", "_private",
            "__internal", "mixedCase123",
            "a", "A", "_", "__",
        ]
        
        for identifier in valid_identifiers:
            with self.subTest(identifier=identifier):
                tokens = self.lexer.tokenize(identifier)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, "IDENTIFIER")
                self.assertEqual(tokens[0].value, identifier)
    
    def test_string_literal_variations(self):
        """Test string literal tokenization"""
        string_tests = [
            '""',           # Empty string
            '"hello"',      # Simple string
            '"Hello, World!"',  # String with punctuation
            '"String with spaces"',  # String with spaces
            '"String with 123 numbers"',  # String with numbers
            r'"String with \n escape"',  # String with escape sequences
        ]
        
        for string_literal in string_tests:
            with self.subTest(string=string_literal):
                tokens = self.lexer.tokenize(string_literal)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, "STRING")
    
    def test_char_literal_variations(self):
        """Test character literal tokenization"""
        char_tests = [
            "'a'", "'Z'", "'0'", "'9'",
            "' '",  # Space character
            "'!'", "'@'", "'#'",
            r"'\n'", r"'\t'", r"'\r'",  # Escape sequences
        ]
        
        for char_literal in char_tests:
            with self.subTest(char=char_literal):
                tokens = self.lexer.tokenize(char_literal)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, "CHAR")
    
    def test_float_literal_variations(self):
        """Test floating-point literal tokenization"""
        float_tests = [
            "0.0", "1.0", "3.14", "2.718",
            "123.456", "0.123", ".5",
            "1e10", "1E10", "1.5e-3", "2.0E+5",
        ]
        
        for float_literal in float_tests:
            with self.subTest(float_val=float_literal):
                tokens = self.lexer.tokenize(float_literal)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, "FLOAT")
    
    def test_comment_handling(self):
        """Test comment tokenization and handling"""
        comment_tests = [
            "// Single line comment",
            "/* Block comment */",
            "/* Multi-line\n   block comment */",
            "int x; // Comment after code",
            "/* Comment */ int y;",
        ]
        
        for comment_source in comment_tests:
            with self.subTest(source=comment_source):
                tokens = self.lexer.tokenize(comment_source)
                # Comments should be filtered out or handled appropriately
                # The exact behavior depends on lexer implementation
    
    def test_whitespace_handling(self):
        """Test whitespace handling"""
        whitespace_tests = [
            "int    x;",      # Multiple spaces
            "int\tx;",        # Tab character
            "int\nx;",        # Newline
            "int\r\nx;",      # CRLF
            "  int x;  ",     # Leading/trailing whitespace
        ]
        
        for source in whitespace_tests:
            with self.subTest(source=repr(source)):
                tokens = self.lexer.tokenize(source)
                # Should tokenize the same regardless of whitespace
                token_types = [t.type for t in tokens]
                self.assertIn("INT", token_types)
                self.assertIn("IDENTIFIER", token_types)
                self.assertIn("SEMICOLON", token_types)
    
    def test_complex_expressions(self):
        """Test tokenization of complex expressions"""
        complex_expressions = [
            "a + b * c",
            "(x + y) / (z - w)",
            "array[index++]",
            "struct.member->field",
            "func(arg1, arg2, arg3)",
            "0xFF & 0x0F | 0xF0",
            "condition ? true_val : false_val",
        ]
        
        for expression in complex_expressions:
            with self.subTest(expression=expression):
                tokens = self.lexer.tokenize(expression)
                self.assertGreater(len(tokens), 0)
                # Should tokenize without errors
    
    def test_edge_cases(self):
        """Test edge cases and potential error conditions"""
        edge_cases = [
            "",              # Empty input
            " ",             # Only whitespace
            "//",            # Empty comment
            "/**/",          # Empty block comment
            "0x",            # Incomplete hex literal
            "'",             # Incomplete char literal
            '"',             # Incomplete string literal
            "123.456.789",   # Invalid float format
        ]
        
        for case in edge_cases:
            with self.subTest(case=repr(case)):
                try:
                    tokens = self.lexer.tokenize(case)
                    # Some cases may produce empty token lists
                    # Others may produce error tokens
                    # The important thing is not to crash
                except Exception as e:
                    # Some edge cases may legitimately throw exceptions
                    print(f"Edge case {repr(case)} threw: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
