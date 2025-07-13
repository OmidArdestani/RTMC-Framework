"""
Tokenizer for RT-Micro-C Language
Performs lexical analysis to convert source code into tokens.
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Iterator
from io import StringIO

class TokenType(Enum):
    # Literals
    INTEGER = auto()
    FLOAT   = auto()
    STRING  = auto()
    CHAR    = auto()
    BOOLEAN = auto()  # Boolean literal
    
    # Identifiers and keywords
    IDENTIFIER = auto()
    
    # Data types
    INT         = auto()
    FLOAT_TYPE  = auto()
    CHAR_TYPE   = auto()
    BOOL_TYPE   = auto()
    VOID        = auto()
    CONST       = auto()
    STRUCT      = auto()
    TASK        = auto()  # Task keyword
    MESSAGE     = auto()  # Message keyword
    IMPORT      = auto()  # Import keyword
    
    # Message operations
    SEND = auto()
    RECV = auto()
    
    # Control flow
    IF       = auto()
    ELSE     = auto()
    WHILE    = auto()
    FOR      = auto()
    BREAK    = auto()
    CONTINUE = auto()
    RETURN   = auto()
    
    # RTOS Keywords
    RTOS_CREATE_TASK      = auto()
    RTOS_DELETE_TASK      = auto()
    RTOS_DELAY_MS         = auto()
    RTOS_SEMAPHORE_CREATE = auto()
    RTOS_SEMAPHORE_TAKE   = auto()
    RTOS_SEMAPHORE_GIVE   = auto()
    RTOS_YIELD            = auto()
    RTOS_SUSPEND_TASK     = auto()
    RTOS_RESUME_TASK      = auto()
    
    # Hardware Keywords
    HW_GPIO_INIT         = auto()
    HW_GPIO_SET          = auto()
    HW_GPIO_GET          = auto()
    HW_TIMER_INIT        = auto()
    HW_TIMER_START       = auto()
    HW_TIMER_STOP        = auto()
    HW_TIMER_SET_PWM_DUTY = auto()
    # TODO: Add timer reset and get
    HW_ADC_INIT          = auto()
    HW_ADC_READ          = auto()
    HW_UART_WRITE        = auto()
    # TODO: Add UART read
    HW_SPI_TRANSFER      = auto()
    HW_I2C_WRITE         = auto()
    HW_I2C_READ          = auto()
    
    # Debug Keywords
    DBG_PRINT      = auto()
    DBG_BREAKPOINT = auto()
    
    # Operators
    PLUS             = auto()
    MINUS            = auto()
    MULTIPLY         = auto()
    DIVIDE           = auto()
    MODULO           = auto()
    ASSIGN           = auto()
    PLUS_ASSIGN      = auto()
    MINUS_ASSIGN     = auto()
    MULTIPLY_ASSIGN  = auto()
    DIVIDE_ASSIGN    = auto()
    INCREMENT        = auto()  # ++
    DECREMENT        = auto()  # --
    # TODO: Add sqrt and power operators
    
    # Comparison operators
    EQUAL         = auto()
    NOT_EQUAL     = auto()
    LESS_THAN     = auto()
    LESS_EQUAL    = auto()
    GREATER_THAN  = auto()
    GREATER_EQUAL = auto()
    
    # Logical operators
    LOGICAL_AND = auto()
    LOGICAL_OR  = auto()
    LOGICAL_NOT = auto()
    
    # Bitwise operators
    BITWISE_AND   = auto()
    BITWISE_OR    = auto()
    BITWISE_XOR   = auto()
    BITWISE_NOT   = auto()
    LEFT_SHIFT    = auto()
    RIGHT_SHIFT   = auto()
    
    # Delimiters
    SEMICOLON = auto()
    COMMA     = auto()
    DOT       = auto()
    ARROW     = auto()
    COLON     = auto()
    
    # Brackets
    LEFT_PAREN    = auto()
    RIGHT_PAREN   = auto()
    LEFT_BRACE    = auto()
    RIGHT_BRACE   = auto()
    LEFT_BRACKET  = auto()
    RIGHT_BRACKET = auto()
    
    # Special
    NEWLINE    = auto()
    EOF        = auto()
    COMMENT    = auto()
    WHITESPACE = auto()

@dataclass
class Token:
    type:   TokenType
    value:  str
    line:   int
    column: int
    filename: str = ""

class Tokenizer:
    """RT-Micro-C tokenizer"""
    
    KEYWORDS = {
        # Data types
        'int': TokenType.INT,
        'float': TokenType.FLOAT_TYPE,
        'char': TokenType.CHAR_TYPE,
        'bool': TokenType.BOOL_TYPE,
        'void': TokenType.VOID,
        'const': TokenType.CONST,
        'struct': TokenType.STRUCT,
        'Task': TokenType.TASK,
        'message': TokenType.MESSAGE,
        'import': TokenType.IMPORT,
        
        # Boolean literals
        'true': TokenType.BOOLEAN,
        'false': TokenType.BOOLEAN,
        
        # Message operations
        'send': TokenType.SEND,
        'recv': TokenType.RECV,
        
        # Control flow
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'break': TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'return': TokenType.RETURN,
        
        # RTOS functions
        'RTOS_CREATE_TASK': TokenType.RTOS_CREATE_TASK,
        'RTOS_DELETE_TASK': TokenType.RTOS_DELETE_TASK,
        'RTOS_DELAY_MS': TokenType.RTOS_DELAY_MS,
        'RTOS_SEMAPHORE_CREATE': TokenType.RTOS_SEMAPHORE_CREATE,
        'RTOS_SEMAPHORE_TAKE': TokenType.RTOS_SEMAPHORE_TAKE,
        'RTOS_SEMAPHORE_GIVE': TokenType.RTOS_SEMAPHORE_GIVE,
        'RTOS_YIELD': TokenType.RTOS_YIELD,
        'RTOS_SUSPEND_TASK': TokenType.RTOS_SUSPEND_TASK,
        'RTOS_RESUME_TASK': TokenType.RTOS_RESUME_TASK,
        
        # Hardware functions
        'HW_GPIO_INIT': TokenType.HW_GPIO_INIT,
        'HW_GPIO_SET': TokenType.HW_GPIO_SET,
        'HW_GPIO_GET': TokenType.HW_GPIO_GET,
        'HW_TIMER_INIT': TokenType.HW_TIMER_INIT,
        'HW_TIMER_START': TokenType.HW_TIMER_START,
        'HW_TIMER_STOP': TokenType.HW_TIMER_STOP,
        'HW_TIMER_SET_PWM_DUTY': TokenType.HW_TIMER_SET_PWM_DUTY,
        'HW_ADC_INIT': TokenType.HW_ADC_INIT,
        'HW_ADC_READ': TokenType.HW_ADC_READ,
        'HW_UART_WRITE': TokenType.HW_UART_WRITE,
        'HW_SPI_TRANSFER': TokenType.HW_SPI_TRANSFER,
        'HW_I2C_WRITE': TokenType.HW_I2C_WRITE,
        'HW_I2C_READ': TokenType.HW_I2C_READ,
        
        # Debug functions
        'DBG_PRINT': TokenType.DBG_PRINT,
        'DBG_BREAKPOINT': TokenType.DBG_BREAKPOINT,
    }
    
    def __init__(self, source: str, filename: str = ""):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
    
    def current_char(self) -> Optional[str]:
        """Get the current character"""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Look ahead at the next character"""
        peek_pos = self.pos + offset
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]
    
    def advance(self) -> None:
        """Move to the next character"""
        if self.pos < len(self.source):
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters (except newlines)"""
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()
    
    def read_number(self) -> Token:
        """Read a numeric literal"""
        start_pos = self.pos
        start_column = self.column
        
        # Read integer part
        while self.current_char() and self.current_char().isdigit():
            self.advance()
        
        # Check for decimal point
        if self.current_char() == '.' and self.peek_char() and self.peek_char().isdigit():
            self.advance()  # consume '.'
            while self.current_char() and self.current_char().isdigit():
                self.advance()
            
            value = self.source[start_pos:self.pos]
            return Token(TokenType.FLOAT, value, self.line, start_column, self.filename)
        
        value = self.source[start_pos:self.pos]
        return Token(TokenType.INTEGER, value, self.line, start_column, self.filename)
    
    def read_string(self) -> Token:
        """Read a string literal"""
        start_column = self.column
        quote_char = self.current_char()
        self.advance()  # consume opening quote
        
        value = ""
        while self.current_char() and self.current_char() != quote_char:
            if self.current_char() == '\\':
                self.advance()
                if self.current_char():
                    # Handle escape sequences
                    escape_char = self.current_char()
                    if escape_char == 'n':
                        value += '\n'
                    elif escape_char == 't':
                        value += '\t'
                    elif escape_char == 'r':
                        value += '\r'
                    elif escape_char == '\\':
                        value += '\\'
                    elif escape_char == '"':
                        value += '"'
                    elif escape_char == "'":
                        value += "'"
                    else:
                        value += escape_char
                    self.advance()
            else:
                value += self.current_char()
                self.advance()
        
        if self.current_char() == quote_char:
            self.advance()  # consume closing quote
        
        token_type = TokenType.STRING if quote_char == '"' else TokenType.CHAR
        return Token(token_type, value, self.line, start_column, self.filename)
    
    def read_identifier(self) -> Token:
        """Read an identifier or keyword"""
        start_pos = self.pos
        start_column = self.column
        
        while (self.current_char() and 
               (self.current_char().isalnum() or self.current_char() == '_')):
            self.advance()
        
        value = self.source[start_pos:self.pos]
        token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, self.line, start_column, self.filename)
    
    def read_comment(self) -> Token:
        """Read a comment"""
        start_column = self.column
        
        if self.current_char() == '/' and self.peek_char() == '/':
            # Single-line comment
            while self.current_char() and self.current_char() != '\n':
                self.advance()
            return Token(TokenType.COMMENT, "", self.line, start_column, self.filename)
        
        elif self.current_char() == '/' and self.peek_char() == '*':
            # Multi-line comment
            self.advance()  # consume '/'
            self.advance()  # consume '*'
            
            while self.current_char():
                if self.current_char() == '*' and self.peek_char() == '/':
                    self.advance()  # consume '*'
                    self.advance()  # consume '/'
                    break
                self.advance()
            
            return Token(TokenType.COMMENT, "", self.line, start_column, self.filename)
        
        return None
    
    def tokenize(self) -> List[Token]:
        """Tokenize the source code"""
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if not self.current_char():
                break
            
            char = self.current_char()
            start_column = self.column
            
            # Newlines
            if char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, char, self.line, start_column, self.filename))
                self.advance()
                continue
            
            # Numbers
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Strings and characters
            if char in '"\'':
                self.tokens.append(self.read_string())
                continue
            
            # Comments
            if char == '/':
                comment = self.read_comment()
                if comment:
                    # Skip comments in normal tokenization
                    continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Two-character operators
            if char == '+' and self.peek_char() == '+':
                self.tokens.append(Token(TokenType.INCREMENT, '++', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '+' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.PLUS_ASSIGN, '+=', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '-' and self.peek_char() == '-':
                self.tokens.append(Token(TokenType.DECREMENT, '--', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '-' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.MINUS_ASSIGN, '-=', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '*' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.MULTIPLY_ASSIGN, '*=', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '/' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.DIVIDE_ASSIGN, '/=', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '=' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.EQUAL, '==', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '!' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.NOT_EQUAL, '!=', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '<' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.LESS_EQUAL, '<=', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '>' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.GREATER_EQUAL, '>=', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '&' and self.peek_char() == '&':
                self.tokens.append(Token(TokenType.LOGICAL_AND, '&&', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '|' and self.peek_char() == '|':
                self.tokens.append(Token(TokenType.LOGICAL_OR, '||', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '<' and self.peek_char() == '<':
                self.tokens.append(Token(TokenType.LEFT_SHIFT, '<<', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '>' and self.peek_char() == '>':
                self.tokens.append(Token(TokenType.RIGHT_SHIFT, '>>', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            if char == '-' and self.peek_char() == '>':
                self.tokens.append(Token(TokenType.ARROW, '->', self.line, start_column, self.filename))
                self.advance()
                self.advance()
                continue
            
            # Single-character tokens
            single_char_tokens = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '%': TokenType.MODULO,
                '=': TokenType.ASSIGN,
                '<': TokenType.LESS_THAN,
                '>': TokenType.GREATER_THAN,
                '!': TokenType.LOGICAL_NOT,
                '&': TokenType.BITWISE_AND,
                '|': TokenType.BITWISE_OR,
                '^': TokenType.BITWISE_XOR,
                '~': TokenType.BITWISE_NOT,
                ';': TokenType.SEMICOLON,
                ',': TokenType.COMMA,
                '.': TokenType.DOT,
                ':': TokenType.COLON,
                '(': TokenType.LEFT_PAREN,
                ')': TokenType.RIGHT_PAREN,
                '{': TokenType.LEFT_BRACE,
                '}': TokenType.RIGHT_BRACE,
                '[': TokenType.LEFT_BRACKET,
                ']': TokenType.RIGHT_BRACKET,
            }
            
            if char in single_char_tokens:
                self.tokens.append(Token(single_char_tokens[char], char, self.line, start_column, self.filename))
                self.advance()
                continue
            
            # Unknown character
            error_msg = f"Unexpected character '{char}' at {self.filename}:{self.line}:{self.column}" if self.filename else f"Unexpected character '{char}' at line {self.line}, column {self.column}"
            raise SyntaxError(error_msg)
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column, self.filename))
        return self.tokens
