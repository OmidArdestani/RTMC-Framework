"""
Parser for RT-Micro-C Language
Converts tokens into an Abstract Syntax Tree (AST).
"""

from typing import List, Optional, Union
from src.lexer.tokenizer import Token, TokenType
from src.parser.ast_nodes import *

class ParseError(Exception):
    """Parser error exception"""
    pass

class Parser:
    """RT-Micro-C recursive descent parser"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
    
    def is_at_end(self) -> bool:
        """Check if we're at the end of tokens"""
        return self.current >= len(self.tokens) or self.peek().type == TokenType.EOF
    
    def peek(self) -> Token:
        """Get current token without advancing"""
        if self.current >= len(self.tokens):
            # Return the last token (should be EOF) if we're beyond the array
            return self.tokens[-1] if self.tokens else Token(TokenType.EOF, '', 0, 0)
        return self.tokens[self.current]
    
    def previous(self) -> Token:
        """Get previous token"""
        if self.current > 0:
            return self.tokens[self.current - 1]
        else:
            return self.tokens[0] if self.tokens else Token(TokenType.EOF, '', 0, 0)
    
    def advance(self) -> Token:
        """Consume and return current token"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()
    
    def check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type"""
        if self.is_at_end():
            return False
        return self.peek().type == token_type
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types"""
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
    def consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of given type or raise error"""
        if self.check(token_type):
            return self.advance()
        
        current_token = self.peek()
        raise ParseError(f"{message} at line {current_token.line}, got {current_token.type.name}")
    
    def synchronize(self):
        """Synchronize after a parse error"""
        self.advance()
        
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
            
            if self.peek().type in [TokenType.STRUCT, TokenType.INT, TokenType.FLOAT_TYPE, 
                                   TokenType.CHAR_TYPE, TokenType.VOID, TokenType.IF, 
                                   TokenType.WHILE, TokenType.FOR, TokenType.RETURN]:
                return
            
            self.advance()
    
    def parse(self) -> ProgramNode:
        """Parse the entire program"""
        declarations = []
        
        while not self.is_at_end():
            # Skip newlines
            if self.match(TokenType.NEWLINE):
                continue
            
            try:
                decl = self.declaration()
                if decl:
                    declarations.append(decl)
            except ParseError as e:
                print(f"Parse error: {e}")
                self.synchronize()
        
        return ProgramNode(declarations)
    
    def declaration(self) -> Optional[ASTNode]:
        """Parse a declaration"""
        try:
            # Check for Import statement (import "filename.rtmc";)
            if self.check(TokenType.IMPORT):
                return self.import_statement()
            
            # Check for Task declaration (Task<core, priority> Name { ... })
            if self.check(TokenType.TASK):
                return self.task_declaration()
            
            # Check for Message declaration (message<type> Name;)
            if self.check(TokenType.MESSAGE):
                return self.message_declaration()
            
            # Check for struct declaration (struct Name { ... })
            if self.check(TokenType.STRUCT):
                # Look ahead to see if this is a struct declaration or variable declaration
                saved_pos = self.current
                self.advance()  # consume 'struct'
                if self.check(TokenType.IDENTIFIER):
                    struct_name = self.peek().value
                    self.advance()  # consume identifier
                    if self.check(TokenType.LEFT_BRACE):
                        # This is a struct declaration
                        self.current = saved_pos
                        return self.struct_declaration()
                
                # Not a struct declaration, reset and treat as variable declaration
                self.current = saved_pos
            
            if self.check_type_specifier():
                return self.function_or_variable_declaration()
            
            return self.statement()
        
        except ParseError:
            self.synchronize()
            return None
    
    def check_type_specifier(self) -> bool:
        """Check if current token is a type specifier"""
        return self.check(TokenType.INT) or self.check(TokenType.FLOAT_TYPE) or \
               self.check(TokenType.CHAR_TYPE) or self.check(TokenType.VOID) or \
               self.check(TokenType.CONST) or self.check(TokenType.STRUCT) or \
               self.check(TokenType.IDENTIFIER)  # Allow custom struct types
    
    def struct_declaration(self) -> StructDeclNode:
        """Parse struct declaration"""
        self.consume(TokenType.STRUCT, "Expected 'struct'")
        name = self.consume(TokenType.IDENTIFIER, "Expected struct name").value
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after struct name")
        
        fields = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            
            field_type = self.type_specifier()
            field_name = self.consume(TokenType.IDENTIFIER, "Expected field name").value
            
            # Check for bit field
            bit_width = None
            if self.match(TokenType.COLON):
                bit_width_token = self.consume(TokenType.INTEGER, "Expected bit width")
                bit_width = int(bit_width_token.value)
            
            fields.append(FieldNode(field_name, field_type, bit_width))
            
            self.consume(TokenType.SEMICOLON, "Expected ';' after field declaration")
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after struct fields")
        self.consume(TokenType.SEMICOLON, "Expected ';' after struct declaration")
        
        return StructDeclNode(name, fields)
    
    def task_declaration(self) -> TaskDeclNode:
        """Parse Task declaration: Task<core, priority> Name { ... }"""
        self.consume(TokenType.TASK, "Expected 'Task'")
        self.consume(TokenType.LESS_THAN, "Expected '<' after Task")
        
        # Parse core number
        core_token = self.consume(TokenType.INTEGER, "Expected core number")
        core = int(core_token.value)
        
        self.consume(TokenType.COMMA, "Expected ',' after core number")
        
        # Parse priority
        priority_token = self.consume(TokenType.INTEGER, "Expected priority number")
        priority = int(priority_token.value)
        
        self.consume(TokenType.GREATER_THAN, "Expected '>' after priority")
        
        # Parse task name
        task_name = self.consume(TokenType.IDENTIFIER, "Expected task name").value
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after task name")
        
        # Parse task members (variables and functions)
        members = []
        run_function = None
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            
            # Parse member declaration
            member = self.task_member_declaration()
            if member:
                members.append(member)
                # Check if this is the run function
                if (isinstance(member, FunctionDeclNode) and 
                    member.name == "run" and 
                    isinstance(member.return_type, PrimitiveTypeNode) and 
                    member.return_type.type_name == "void"):
                    run_function = member
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after task body")
        
        if run_function is None:
            raise ParseError("Task must have a 'void run()' method")
        
        return TaskDeclNode(task_name, core, priority, members, run_function)
    
    def task_member_declaration(self) -> Optional[ASTNode]:
        """Parse a member declaration inside a Task"""
        try:
            if self.check_type_specifier():
                return self.function_or_variable_declaration()
            return None
        except ParseError:
            self.synchronize()
            return None

    def message_declaration(self) -> MessageDeclNode:
        """Parse message declaration: message<type> Name;"""
        self.consume(TokenType.MESSAGE, "Expected 'message'")
        self.consume(TokenType.LESS_THAN, "Expected '<' after message")
        
        # Parse the message type
        message_type = self.type_specifier()
        
        self.consume(TokenType.GREATER_THAN, "Expected '>' after message type")
        
        # Parse message queue name
        name = self.consume(TokenType.IDENTIFIER, "Expected message queue name").value
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after message declaration")
        
        return MessageDeclNode(name, message_type)

    def import_statement(self) -> ImportStmtNode:
        """Parse import statement: import "filename.rtmc";"""
        self.consume(TokenType.IMPORT, "Expected 'import'")
        
        # Parse the file path string
        filepath_token = self.consume(TokenType.STRING, "Expected string literal after 'import'")
        filepath = filepath_token.value.strip('"\'')  # Remove quotes
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after import statement")
        
        return ImportStmtNode(filepath)

    def function_or_variable_declaration(self) -> ASTNode:
        """Parse function or variable declaration"""
        is_const = False
        if self.match(TokenType.CONST):
            is_const = True
        
        return_type = self.type_specifier()
        name = self.consume(TokenType.IDENTIFIER, "Expected identifier").value
        
        if self.match(TokenType.LEFT_PAREN):
            # Function declaration
            parameters = []
            
            if not self.check(TokenType.RIGHT_PAREN):
                parameters.append(self.parameter())
                while self.match(TokenType.COMMA):
                    parameters.append(self.parameter())
            
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters")
            
            # Skip optional newlines before opening brace
            while self.match(TokenType.NEWLINE):
                pass
            
            self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body")
            body = self.block_statement()
            
            return FunctionDeclNode(name, return_type, parameters, body)
        
        elif self.match(TokenType.LEFT_BRACKET):
            # Array declaration
            size_token = self.consume(TokenType.INTEGER, "Expected array size")
            size = int(size_token.value)
            self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after array size")
            
            initializer = None
            if self.match(TokenType.ASSIGN):
                initializer = self.array_literal()
            
            self.consume(TokenType.SEMICOLON, "Expected ';' after array declaration")
            
            return ArrayDeclNode(name, return_type, size, initializer)
        
        else:
            # Variable declaration
            initializer = None
            if self.match(TokenType.ASSIGN):
                try:
                    initializer = self.expression()
                except Exception as e:
                    raise
            
            self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
            
            result = VariableDeclNode(name, return_type, initializer, is_const)
            return result
    
    def parameter(self) -> ParameterNode:
        """Parse function parameter"""
        param_type = self.type_specifier()
        param_name = self.consume(TokenType.IDENTIFIER, "Expected parameter name").value
        
        return ParameterNode(param_name, param_type)
    
    def array_literal(self) -> ArrayLiteralNode:
        """Parse array literal: {expr1, expr2, ...}"""
        self.consume(TokenType.LEFT_BRACE, "Expected '{' for array literal")
        
        elements = []
        if not self.check(TokenType.RIGHT_BRACE):
            elements.append(self.expression())
            while self.match(TokenType.COMMA):
                elements.append(self.expression())
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after array literal")
        return ArrayLiteralNode(elements)

    def type_specifier(self) -> TypeNode:
        """Parse type specifier"""
        if self.match(TokenType.INT):
            return PrimitiveTypeNode("int")
        
        if self.match(TokenType.FLOAT_TYPE):
            return PrimitiveTypeNode("float")
        
        if self.match(TokenType.CHAR_TYPE):
            return PrimitiveTypeNode("char")
        
        if self.match(TokenType.BOOL_TYPE):
            return PrimitiveTypeNode("bool")
        
        if self.match(TokenType.VOID):
            return PrimitiveTypeNode("void")
        
        if self.match(TokenType.STRUCT):
            struct_name = self.consume(TokenType.IDENTIFIER, "Expected struct name").value
            return StructTypeNode(struct_name)
        
        if self.check(TokenType.IDENTIFIER):
            # Assume it's a struct type
            struct_name = self.advance().value
            return StructTypeNode(struct_name)
        
        raise ParseError("Expected type specifier")
    
    def statement(self) -> StatementNode:
        """Parse statement"""
        if self.match(TokenType.IF):
            return self.if_statement()
        
        if self.match(TokenType.WHILE):
            return self.while_statement()
        
        if self.match(TokenType.FOR):
            return self.for_statement()
        
        if self.match(TokenType.RETURN):
            return self.return_statement()
        
        if self.match(TokenType.BREAK):
            self.consume(TokenType.SEMICOLON, "Expected ';' after 'break'")
            return BreakStmtNode()
        
        if self.match(TokenType.CONTINUE):
            self.consume(TokenType.SEMICOLON, "Expected ';' after 'continue'")
            return ContinueStmtNode()
        
        if self.match(TokenType.LEFT_BRACE):
            return self.block_statement()
        
        # Check for variable declaration statements
        if (self.check(TokenType.CONST) or
            self.check(TokenType.INT) or
            self.check(TokenType.FLOAT_TYPE) or
            self.check(TokenType.CHAR_TYPE) or
            self.check(TokenType.BOOL_TYPE) or
            self.check(TokenType.VOID) or
            self.check(TokenType.STRUCT)):
            return self.variable_declaration_statement()
        
        return self.expression_statement()
    
    def variable_declaration_statement(self) -> VariableDeclNode:
        """Parse variable declaration statement"""
        is_const = False
        if self.match(TokenType.CONST):
            is_const = True
        
        var_type = self.type_specifier()
        name = self.consume(TokenType.IDENTIFIER, "Expected identifier").value
        
        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.expression()
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        
        return VariableDeclNode(name, var_type, initializer, is_const)
    
    def if_statement(self) -> IfStmtNode:
        """Parse if statement"""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after if condition")
        
        # Skip optional newlines before then statement
        while self.match(TokenType.NEWLINE):
            pass
        
        then_stmt = self.statement()
        
        else_stmt = None
        if self.match(TokenType.ELSE):
            # Skip optional newlines before else statement
            while self.match(TokenType.NEWLINE):
                pass
            else_stmt = self.statement()
        
        return IfStmtNode(condition, then_stmt, else_stmt)
    
    def while_statement(self) -> WhileStmtNode:
        """Parse while statement"""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after while condition")
        
        # Skip optional newlines before body statement
        while self.match(TokenType.NEWLINE):
            pass
        
        body = self.statement()
        
        return WhileStmtNode(condition, body)
    
    def for_statement(self) -> ForStmtNode:
        """Parse for statement"""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'for'")
        
        # Initializer
        initializer = None
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.check_type_specifier():
            initializer = self.function_or_variable_declaration()
        else:
            initializer = self.expression_statement()
        
        # Condition
        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after for loop condition")
        
        # Update
        update = None
        if not self.check(TokenType.RIGHT_PAREN):
            update = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after for clauses")
        
        # Skip optional newlines before body statement
        while self.match(TokenType.NEWLINE):
            pass
        
        body = self.statement()
        
        return ForStmtNode(initializer, condition, update, body)
    
    def return_statement(self) -> ReturnStmtNode:
        """Parse return statement"""
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after return value")
        return ReturnStmtNode(value)
    
    def block_statement(self) -> BlockStmtNode:
        """Parse block statement"""
        statements = []
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after block")
        return BlockStmtNode(statements)
    
    def expression_statement(self) -> ExpressionStmtNode:
        """Parse expression statement"""
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExpressionStmtNode(expr)
    
    def expression(self) -> ExpressionNode:
        """Parse expression"""
        return self.assignment()
    
    def assignment(self) -> ExpressionNode:
        """Parse assignment expression"""
        expr = self.logical_or()
        
        if self.match(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                     TokenType.MULTIPLY_ASSIGN, TokenType.DIVIDE_ASSIGN):
            operator = self.previous().value
            value = self.assignment()
            return AssignmentExprNode(expr, operator, value)
        
        return expr
    
    def logical_or(self) -> ExpressionNode:
        """Parse logical OR expression"""
        expr = self.logical_and()
        
        while self.match(TokenType.LOGICAL_OR):
            operator = self.previous().value
            right = self.logical_and()
            expr = BinaryExprNode(expr, operator, right)
        
        return expr
    
    def logical_and(self) -> ExpressionNode:
        """Parse logical AND expression"""
        expr = self.equality()
        
        while self.match(TokenType.LOGICAL_AND):
            operator = self.previous().value
            right = self.equality()
            expr = BinaryExprNode(expr, operator, right)
        
        return expr
    
    def equality(self) -> ExpressionNode:
        """Parse equality expression"""
        expr = self.comparison()
        
        while self.match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            operator = self.previous().value
            right = self.comparison()
            expr = BinaryExprNode(expr, operator, right)
        
        return expr
    
    def comparison(self) -> ExpressionNode:
        """Parse comparison expression"""
        expr = self.term()
        
        while self.match(TokenType.GREATER_THAN, TokenType.GREATER_EQUAL,
                        TokenType.LESS_THAN, TokenType.LESS_EQUAL):
            operator = self.previous().value
            right = self.term()
            expr = BinaryExprNode(expr, operator, right)
        
        return expr
    
    def term(self) -> ExpressionNode:
        """Parse term (addition/subtraction)"""
        expr = self.factor()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous().value
            right = self.factor()
            expr = BinaryExprNode(expr, operator, right)
        
        return expr
    
    def factor(self) -> ExpressionNode:
        """Parse factor (multiplication/division)"""
        expr = self.unary()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self.previous().value
            right = self.unary()
            expr = BinaryExprNode(expr, operator, right)
        
        return expr
    
    def unary(self) -> ExpressionNode:
        """Parse unary expression"""
        if self.match(TokenType.LOGICAL_NOT, TokenType.MINUS, TokenType.PLUS):
            operator = self.previous().value
            right = self.unary()
            return UnaryExprNode(operator, right)
        
        return self.call()
    
    def call(self) -> ExpressionNode:
        """Parse function call"""
        expr = self.primary()
        
        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                # Handle message operations with special tokens
                if self.check(TokenType.SEND) and isinstance(expr, IdentifierExprNode):
                    # Parse message send: MessageQueue.send(expr)
                    self.advance()  # consume 'send'
                    self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'send'")
                    payload = self.expression()
                    self.consume(TokenType.RIGHT_PAREN, "Expected ')' after send payload")
                    return MessageSendNode(expr.name, payload)
                elif self.check(TokenType.RECV) and isinstance(expr, IdentifierExprNode):
                    # Parse message receive: MessageQueue.recv() or MessageQueue.recv(timeout: 100)
                    self.advance()  # consume 'recv'
                    self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'recv'")
                    
                    timeout = None
                    if not self.check(TokenType.RIGHT_PAREN):
                        # Check for timeout parameter
                        if self.match(TokenType.IDENTIFIER) and self.previous().value == "timeout":
                            self.consume(TokenType.COLON, "Expected ':' after 'timeout'")
                            timeout = self.expression()
                        else:
                            # If not timeout parameter, treat as error for now
                            raise ParseError("Unexpected parameter in recv(). Only 'timeout:' is supported")
                    
                    self.consume(TokenType.RIGHT_PAREN, "Expected ')' after recv parameters")
                    return MessageRecvNode(expr.name, timeout)
                else:
                    # Regular member access
                    name = self.consume(TokenType.IDENTIFIER, "Expected property name after '.'").value
                    expr = MemberExprNode(expr, name, False)
            elif self.match(TokenType.LEFT_BRACKET):
                index = self.expression()
                self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after array index")
                expr = ArrayAccessNode(expr, index)
            elif self.match(TokenType.INCREMENT, TokenType.DECREMENT):
                operator = self.previous().value
                expr = PostfixExprNode(expr, operator)
            else:
                break
        
        return expr
    
    def finish_call(self, callee: ExpressionNode) -> CallExprNode:
        """Finish parsing function call"""
        arguments = []
        
        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())
            while self.match(TokenType.COMMA):
                arguments.append(self.expression())
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments")
        return CallExprNode(callee, arguments)
    
    def primary(self) -> ExpressionNode:
        """Parse primary expression"""
        if self.match(TokenType.INTEGER):
            value = int(self.previous().value)
            return LiteralExprNode(value, "int")
        
        if self.match(TokenType.FLOAT):
            value = float(self.previous().value)
            return LiteralExprNode(value, "float")
        
        if self.match(TokenType.STRING):
            value = self.previous().value
            return LiteralExprNode(value, "string")
        
        if self.match(TokenType.CHAR):
            value = self.previous().value
            return LiteralExprNode(value, "char")
        
        if self.match(TokenType.BOOLEAN):
            value_str = self.previous().value
            value = True if value_str == "true" else False
            return LiteralExprNode(value, "bool")

        if self.match(TokenType.IDENTIFIER):
            name = self.previous().value
            return IdentifierExprNode(name)
        
        # Hardware/RTOS function calls
        if self.match(TokenType.HW_GPIO_INIT, TokenType.HW_GPIO_SET, TokenType.HW_GPIO_GET,
                     TokenType.HW_TIMER_INIT, TokenType.HW_TIMER_START, TokenType.HW_TIMER_STOP,
                     TokenType.HW_TIMER_SET_PWM_DUTY, TokenType.HW_ADC_INIT, TokenType.HW_ADC_READ,
                     TokenType.HW_UART_WRITE, TokenType.HW_SPI_TRANSFER, TokenType.HW_I2C_WRITE,
                     TokenType.HW_I2C_READ, TokenType.RTOS_CREATE_TASK, TokenType.RTOS_DELETE_TASK,
                     TokenType.RTOS_DELAY_MS, TokenType.RTOS_SEMAPHORE_CREATE, TokenType.RTOS_SEMAPHORE_TAKE,
                     TokenType.RTOS_SEMAPHORE_GIVE, TokenType.RTOS_YIELD, TokenType.RTOS_SUSPEND_TASK,
                     TokenType.RTOS_RESUME_TASK, TokenType.DBG_PRINT, TokenType.DBG_BREAKPOINT):
            name = self.previous().value
            return IdentifierExprNode(name)
        
        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return expr
        
        raise ParseError(f"Unexpected token: {self.peek().value}")
