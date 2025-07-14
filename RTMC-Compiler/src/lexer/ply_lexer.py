"""
PLY-based lexer for RT-Micro-C Language
Converts source code into tokens using PLY (Python Lex-Yacc).
"""

import ply.lex as lex
from typing import List, Optional

class RTMCLexer:
    """RT-Micro-C PLY lexer"""
    
    # Token list - required by PLY
    tokens = [
        # Literals
        'INTEGER', 'FLOAT', 'STRING', 'CHAR',
        
        # Identifiers
        'IDENTIFIER',
        
        # Operators
        'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE', 'MODULO',
        'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'MULTIPLY_ASSIGN', 'DIVIDE_ASSIGN',
        'INCREMENT', 'DECREMENT',
        
        # Comparison operators
        'EQUAL', 'NOT_EQUAL', 'LESS_THAN', 'LESS_EQUAL', 'GREATER_THAN', 'GREATER_EQUAL',
        
        # Logical operators
        'LOGICAL_AND', 'LOGICAL_OR', 'LOGICAL_NOT',
        
        # Bitwise operators
        'BITWISE_AND', 'BITWISE_OR', 'BITWISE_XOR', 'BITWISE_NOT',
        'LEFT_SHIFT', 'RIGHT_SHIFT',
        
        # Delimiters
        'SEMICOLON', 'COMMA', 'DOT', 'ARROW', 'COLON',
        
        # Brackets
        'LEFT_PAREN', 'RIGHT_PAREN', 'LEFT_BRACE', 'RIGHT_BRACE',
        'LEFT_BRACKET', 'RIGHT_BRACKET',
    ]
    
    # Reserved words (keywords)
    reserved = {
        # Data types
        'int': 'INT',
        'float': 'FLOAT_TYPE',
        'char': 'CHAR_TYPE',
        'bool': 'BOOL_TYPE',
        'void': 'VOID',
        'const': 'CONST',
        'struct': 'STRUCT',
        'union': 'UNION',
        'Task': 'TASK',
        'message': 'MESSAGE',
        'import': 'IMPORT',
        
        # Boolean literals
        'true': 'TRUE',
        'false': 'FALSE',
        
        # Message operations
        'send': 'SEND',
        'recv': 'RECV',
        
        # Control flow
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'break': 'BREAK',
        'continue': 'CONTINUE',
        'return': 'RETURN',
        
        # RTOS functions
        'RTOS_CREATE_TASK': 'RTOS_CREATE_TASK',
        'RTOS_DELETE_TASK': 'RTOS_DELETE_TASK',
        'RTOS_DELAY_MS': 'RTOS_DELAY_MS',
        'RTOS_SEMAPHORE_CREATE': 'RTOS_SEMAPHORE_CREATE',
        'RTOS_SEMAPHORE_TAKE': 'RTOS_SEMAPHORE_TAKE',
        'RTOS_SEMAPHORE_GIVE': 'RTOS_SEMAPHORE_GIVE',
        'RTOS_YIELD': 'RTOS_YIELD',
        'RTOS_SUSPEND_TASK': 'RTOS_SUSPEND_TASK',
        'RTOS_RESUME_TASK': 'RTOS_RESUME_TASK',
        
        # Hardware functions
        'HW_GPIO_INIT': 'HW_GPIO_INIT',
        'HW_GPIO_SET': 'HW_GPIO_SET',
        'HW_GPIO_GET': 'HW_GPIO_GET',
        'HW_TIMER_INIT': 'HW_TIMER_INIT',
        'HW_TIMER_START': 'HW_TIMER_START',
        'HW_TIMER_STOP': 'HW_TIMER_STOP',
        'HW_TIMER_SET_PWM_DUTY': 'HW_TIMER_SET_PWM_DUTY',
        'HW_ADC_INIT': 'HW_ADC_INIT',
        'HW_ADC_READ': 'HW_ADC_READ',
        'HW_UART_WRITE': 'HW_UART_WRITE',
        'HW_SPI_TRANSFER': 'HW_SPI_TRANSFER',
        'HW_I2C_WRITE': 'HW_I2C_WRITE',
        'HW_I2C_READ': 'HW_I2C_READ',
    }
    
    # Add reserved words to tokens
    tokens += list(reserved.values())
    
    # Token rules
    def t_FLOAT(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t
    
    def t_INTEGER(self, t):
        r'0[xX][0-9a-fA-F]+|[0-9]+'
        if t.value.lower().startswith('0x'):
            t.value = int(t.value, 16)
        else:
            t.value = int(t.value)
        return t
    
    def t_STRING(self, t):
        r'"([^"\\]|\\.)*"'
        # Remove quotes and handle escape sequences
        t.value = t.value[1:-1]
        t.value = t.value.replace('\\n', '\n')
        t.value = t.value.replace('\\t', '\t')
        t.value = t.value.replace('\\r', '\r')
        t.value = t.value.replace('\\"', '"')
        t.value = t.value.replace('\\\\', '\\')
        return t
    
    def t_CHAR(self, t):
        r"'([^'\\]|\\.)*'"
        # Remove quotes and handle escape sequences
        t.value = t.value[1:-1]
        t.value = t.value.replace('\\n', '\n')
        t.value = t.value.replace('\\t', '\t')
        t.value = t.value.replace('\\r', '\r')
        t.value = t.value.replace("\\'", "'")
        t.value = t.value.replace('\\\\', '\\')
        return t
    
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = self.reserved.get(t.value, 'IDENTIFIER')
        return t
    
    # Two-character operators
    def t_INCREMENT(self, t):
        r'\+\+'
        return t
    
    def t_DECREMENT(self, t):
        r'--'
        return t
    
    def t_PLUS_ASSIGN(self, t):
        r'\+='
        return t
    
    def t_MINUS_ASSIGN(self, t):
        r'-='
        return t
    
    def t_MULTIPLY_ASSIGN(self, t):
        r'\*='
        return t
    
    def t_DIVIDE_ASSIGN(self, t):
        r'/='
        return t
    
    def t_EQUAL(self, t):
        r'=='
        return t
    
    def t_NOT_EQUAL(self, t):
        r'!='
        return t
    
    def t_LESS_EQUAL(self, t):
        r'<='
        return t
    
    def t_GREATER_EQUAL(self, t):
        r'>='
        return t
    
    def t_LOGICAL_AND(self, t):
        r'&&'
        return t
    
    def t_LOGICAL_OR(self, t):
        r'\|\|'
        return t
    
    def t_LEFT_SHIFT(self, t):
        r'<<'
        return t
    
    def t_RIGHT_SHIFT(self, t):
        r'>>'
        return t
    
    def t_ARROW(self, t):
        r'->'
        return t
    
    # Single-character operators
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_MULTIPLY = r'\*'
    t_DIVIDE = r'/'
    t_MODULO = r'%'
    t_ASSIGN = r'='
    t_LESS_THAN = r'<'
    t_GREATER_THAN = r'>'
    t_LOGICAL_NOT = r'!'
    t_BITWISE_AND = r'&'
    t_BITWISE_OR = r'\|'
    t_BITWISE_XOR = r'\^'
    t_BITWISE_NOT = r'~'
    
    # Delimiters
    t_SEMICOLON = r';'
    t_COMMA = r','
    t_DOT = r'\.'
    t_COLON = r':'
    
    # Brackets
    t_LEFT_PAREN = r'\('
    t_RIGHT_PAREN = r'\)'
    t_LEFT_BRACE = r'\{'
    t_RIGHT_BRACE = r'\}'
    t_LEFT_BRACKET = r'\['
    t_RIGHT_BRACKET = r'\]'
    
    # Ignored characters (spaces, tabs, and newlines)
    t_ignore = ' \t\r'
    
    # Track newlines for line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
    
    # Comments
    def t_comment(self, t):
        r'//.*'
        pass  # No return value. Token discarded
    
    def t_comment_multiline(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')
        pass  # No return value. Token discarded
    
    # Error handling
    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
        t.lexer.skip(1)
    
    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
    
    def tokenize(self, data: str, filename: str = ""):
        """Tokenize input data"""
        self.lexer.input(data)
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            # Add filename information
            tok.filename = filename
            tokens.append(tok)
        return tokens
    
    def test(self, data: str):
        """Test the lexer with input data"""
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)

# Create a global instance for use by the parser
lexer = RTMCLexer()
