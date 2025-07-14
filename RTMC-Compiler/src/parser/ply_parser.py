"""
PLY-based parser for RT-Micro-C Language
Converts tokens into an Abstract Syntax Tree (AST) using PLY.
"""

import ply.yacc as yacc
from typing import List, Optional, Dict, Any
from src.lexer.ply_lexer import RTMCLexer
from src.parser.ast_nodes import *

class RTMCParser:
    """RT-Micro-C PLY parser"""
    
    # Get the token map from the lexer
    tokens = RTMCLexer.tokens
    
    # Operator precedence and associativity
    precedence = (
        ('left', 'LOGICAL_OR'),
        ('left', 'LOGICAL_AND'),
        ('left', 'BITWISE_OR'),
        ('left', 'BITWISE_XOR'),
        ('left', 'BITWISE_AND'),
        ('left', 'EQUAL', 'NOT_EQUAL'),
        ('left', 'LESS_THAN', 'GREATER_THAN', 'LESS_EQUAL', 'GREATER_EQUAL'),
        ('left', 'LEFT_SHIFT', 'RIGHT_SHIFT'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'MULTIPLY', 'DIVIDE', 'MODULO'),
        ('right', 'UMINUS', 'LOGICAL_NOT', 'BITWISE_NOT'),
        ('left', 'DOT', 'ARROW'),
        ('left', 'LEFT_BRACKET'),
        ('left', 'LEFT_PAREN'),
    )
    
    def __init__(self):
        self.lexer = RTMCLexer()
        self.parser = yacc.yacc(module=self, debug=False, write_tables=False)
    
    def _create_type_node(self, type_str: str) -> TypeNode:
        """Convert a type string to a proper TypeNode"""
        if not type_str:
            return PrimitiveTypeNode("void")
        
        # Handle pointer types
        if type_str.endswith('*'):
            pointer_count = 0
            base_type_str = type_str
            while base_type_str.endswith('*'):
                pointer_count += 1
                base_type_str = base_type_str[:-1].strip()
            
            # Create base type
            base_type = self._create_type_node(base_type_str)
            
            # Wrap in pointer type
            return PointerTypeNode(base_type, pointer_count)
        
        # Handle const qualifier
        if type_str.startswith('const '):
            # For now, just strip const - we might need to handle this differently
            type_str = type_str[6:].strip()
        
        # Handle struct/union types
        if type_str.startswith('struct '):
            struct_name = type_str[7:].strip()
            return StructTypeNode(struct_name)
        elif type_str.startswith('union '):
            union_name = type_str[6:].strip()
            return UnionTypeNode(union_name)
        
        # Handle primitive types
        if type_str in ['int', 'float', 'char', 'bool', 'void']:
            return PrimitiveTypeNode(type_str)
        
        # Handle custom types (might be struct/union names)
        return StructTypeNode(type_str)  # Assume it's a struct for now
    
    def parse(self, input_text: str, filename: str = "") -> ProgramNode:
        """Parse input text and return AST"""
        try:
            result = self.parser.parse(input_text, lexer=self.lexer.lexer)
            return result if result else ProgramNode([])
        except Exception as e:
            print(f"Parse error: {e}")
            return ProgramNode([])
    
    # Grammar rules
    def p_program(self, p):
        '''program : declaration_list'''
        p[0] = ProgramNode(p[1])
    
    def p_declaration_list(self, p):
        '''declaration_list : declaration
                           | declaration_list declaration'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]
    
    def p_declaration(self, p):
        '''declaration : function_declaration
                      | variable_declaration
                      | struct_declaration
                      | union_declaration
                      | task_declaration
                      | message_declaration
                      | import_declaration'''
        p[0] = p[1]
    
    # Function declaration
    def p_function_declaration(self, p):
        '''function_declaration : type_specifier IDENTIFIER LEFT_PAREN parameter_list RIGHT_PAREN compound_statement
                               | type_specifier IDENTIFIER LEFT_PAREN RIGHT_PAREN compound_statement'''
        if len(p) == 7:
            p[0] = FunctionDeclNode(p[2], p[1], p[4], p[6])
        else:
            p[0] = FunctionDeclNode(p[2], p[1], [], p[5])
    
    def p_parameter_list(self, p):
        '''parameter_list : parameter
                         | parameter_list COMMA parameter'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]
    
    def p_parameter(self, p):
        '''parameter : type_specifier IDENTIFIER
                    | type_specifier IDENTIFIER LEFT_BRACKET RIGHT_BRACKET'''
        if len(p) == 3:
            p[0] = ParameterNode(p[2], p[1])
        else:
            # For array parameters, create an array type
            array_type = ArrayTypeNode(p[1])
            p[0] = ParameterNode(p[2], array_type)
    
    # Variable declaration
    def p_variable_declaration(self, p):
        '''variable_declaration : type_specifier IDENTIFIER SEMICOLON
                               | type_specifier IDENTIFIER ASSIGN expression SEMICOLON
                               | type_specifier IDENTIFIER LEFT_BRACKET expression RIGHT_BRACKET SEMICOLON
                               | type_specifier IDENTIFIER LEFT_BRACKET expression RIGHT_BRACKET ASSIGN array_literal SEMICOLON'''
        if len(p) == 4:
            p[0] = VariableDeclNode(p[2], p[1])
        elif len(p) == 6:
            p[0] = VariableDeclNode(p[2], p[1], p[4])
        elif len(p) == 7:
            p[0] = ArrayDeclNode(p[2], p[1], p[4])
        else:
            p[0] = ArrayDeclNode(p[2], p[1], p[4], p[7])
    
    # Struct declaration
    def p_struct_declaration(self, p):
        '''struct_declaration : STRUCT IDENTIFIER LEFT_BRACE struct_member_list RIGHT_BRACE SEMICOLON'''
        p[0] = StructDeclNode(p[2], p[4])
    
    def p_struct_member_list(self, p):
        '''struct_member_list : struct_member
                             | struct_member_list struct_member'''
        if len(p) == 2:
            # Handle both single fields and lists of fields (from anonymous unions/structs)
            if isinstance(p[1], list):
                p[0] = p[1]
            else:
                p[0] = [p[1]]
        else:
            # Combine existing list with new member(s)
            result = p[1]
            if isinstance(p[2], list):
                result.extend(p[2])
            else:
                result.append(p[2])
            p[0] = result
    
    def p_struct_member(self, p):
        '''struct_member : type_specifier IDENTIFIER SEMICOLON
                        | type_specifier IDENTIFIER LEFT_BRACKET expression RIGHT_BRACKET SEMICOLON
                        | type_specifier IDENTIFIER COLON INTEGER SEMICOLON
                        | type_specifier IDENTIFIER ASSIGN expression SEMICOLON
                        | type_specifier IDENTIFIER COLON INTEGER ASSIGN expression SEMICOLON
                        | anonymous_union_declaration
                        | anonymous_struct_declaration'''
        if len(p) == 4:
            # Simple field: type_specifier IDENTIFIER SEMICOLON
            p[0] = FieldNode(p[2], p[1])
        elif len(p) == 6:
            if p[3] == ':':
                # Bitfield declaration: type_specifier IDENTIFIER COLON INTEGER SEMICOLON
                p[0] = FieldNode(p[2], p[1], bit_width=p[4])
            elif p[3] == '=':
                # Default initialization: type_specifier IDENTIFIER ASSIGN expression SEMICOLON
                p[0] = FieldNode(p[2], p[1], initializer=p[4])
            else:
                # Array declaration: type_specifier IDENTIFIER LEFT_BRACKET expression RIGHT_BRACKET SEMICOLON
                # For now, treat array size as None for struct fields, since we pass an expression
                array_type = ArrayTypeNode(p[1], None)
                p[0] = FieldNode(p[2], array_type)
        elif len(p) == 7:
            # Array declaration with initializer (handled by previous case)
            array_type = ArrayTypeNode(p[1], None)
            p[0] = FieldNode(p[2], array_type)
        elif len(p) == 8:
            # Bitfield with default value: type_specifier IDENTIFIER COLON INTEGER ASSIGN expression SEMICOLON
            p[0] = FieldNode(p[2], p[1], bit_width=p[4], initializer=p[6])
        else:
            # Anonymous struct/union - return the flattened fields
            p[0] = p[1]
    
    # Anonymous union declaration
    def p_anonymous_union_declaration(self, p):
        '''anonymous_union_declaration : UNION LEFT_BRACE struct_member_list RIGHT_BRACE SEMICOLON'''
        # Generate a unique union group name
        import uuid
        union_group_id = f"union_{uuid.uuid4().hex[:8]}"
        
        # Flatten the union - mark all fields as belonging to the same union group
        flattened_fields = []
        for field in p[3]:
            if isinstance(field, list):
                # Nested anonymous struct/union
                for subfield in field:
                    if hasattr(subfield, 'union_group'):
                        subfield.union_group = union_group_id
                    flattened_fields.append(subfield)
            else:
                if hasattr(field, 'union_group'):
                    field.union_group = union_group_id
                flattened_fields.append(field)
        
        p[0] = flattened_fields
    
    # Anonymous struct declaration
    def p_anonymous_struct_declaration(self, p):
        '''anonymous_struct_declaration : STRUCT LEFT_BRACE struct_member_list RIGHT_BRACE SEMICOLON'''
        # For anonymous structs, we just return the fields (no union grouping)
        flattened_fields = []
        for field in p[3]:
            if isinstance(field, list):
                # Nested anonymous struct/union
                flattened_fields.extend(field)
            else:
                flattened_fields.append(field)
        
        p[0] = flattened_fields
    
    # Union declaration
    def p_union_declaration(self, p):
        '''union_declaration : UNION IDENTIFIER LEFT_BRACE struct_member_list RIGHT_BRACE SEMICOLON'''
        p[0] = UnionDeclNode(p[2], p[4])
    
    # Task declaration
    def p_task_declaration(self, p):
        '''task_declaration : TASK IDENTIFIER LEFT_PAREN parameter_list RIGHT_PAREN compound_statement
                           | TASK IDENTIFIER LEFT_PAREN RIGHT_PAREN compound_statement'''
        if len(p) == 7:
            p[0] = TaskDeclNode(p[2], p[4], p[6])
        else:
            p[0] = TaskDeclNode(p[2], [], p[5])
    
    # Message declaration
    def p_message_declaration(self, p):
        '''message_declaration : MESSAGE IDENTIFIER LEFT_BRACE struct_member_list RIGHT_BRACE SEMICOLON'''
        p[0] = MessageDeclNode(p[2], p[4])
    
    # Import declaration
    def p_import_declaration(self, p):
        '''import_declaration : IMPORT STRING SEMICOLON'''
        p[0] = ImportStmtNode(p[2])
    
    # Type specifiers
    def p_type_specifier(self, p):
        '''type_specifier : INT
                         | FLOAT_TYPE
                         | CHAR_TYPE
                         | BOOL_TYPE
                         | VOID
                         | CONST type_specifier
                         | STRUCT IDENTIFIER
                         | UNION IDENTIFIER
                         | IDENTIFIER
                         | type_specifier MULTIPLY'''
        if len(p) == 2:
            # Simple type
            p[0] = self._create_type_node(p[1])
        elif len(p) == 3:
            if p[1] == 'const':
                # const type_specifier - for now just return the inner type
                p[0] = p[2]
            elif p[2] == '*':
                # pointer type
                if isinstance(p[1], str):
                    base_type = self._create_type_node(p[1])
                else:
                    base_type = p[1]
                p[0] = PointerTypeNode(base_type, 1)
            else:
                # struct/union IDENTIFIER
                type_str = f"{p[1]} {p[2]}"
                p[0] = self._create_type_node(type_str)
    
    # Statements
    def p_statement(self, p):
        '''statement : expression_statement
                    | compound_statement
                    | if_statement
                    | while_statement
                    | for_statement
                    | return_statement
                    | break_statement
                    | continue_statement
                    | variable_declaration'''
        p[0] = p[1]
    
    def p_compound_statement(self, p):
        '''compound_statement : LEFT_BRACE statement_list RIGHT_BRACE
                             | LEFT_BRACE RIGHT_BRACE'''
        if len(p) == 4:
            p[0] = BlockStmtNode(p[2])
        else:
            p[0] = BlockStmtNode([])
    
    def p_statement_list(self, p):
        '''statement_list : statement
                         | statement_list statement'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]
    
    def p_expression_statement(self, p):
        '''expression_statement : expression SEMICOLON
                               | SEMICOLON'''
        if len(p) == 3:
            p[0] = ExpressionStmtNode(p[1])
        else:
            p[0] = ExpressionStmtNode(None)
    
    def p_if_statement(self, p):
        '''if_statement : IF LEFT_PAREN expression RIGHT_PAREN statement
                       | IF LEFT_PAREN expression RIGHT_PAREN statement ELSE statement'''
        if len(p) == 6:
            p[0] = IfStmtNode(p[3], p[5])
        else:
            p[0] = IfStmtNode(p[3], p[5], p[7])
    
    def p_while_statement(self, p):
        '''while_statement : WHILE LEFT_PAREN expression RIGHT_PAREN statement'''
        p[0] = WhileStmtNode(p[3], p[5])
    
    def p_for_statement(self, p):
        '''for_statement : FOR LEFT_PAREN expression_statement expression_statement expression RIGHT_PAREN statement
                        | FOR LEFT_PAREN expression_statement expression_statement RIGHT_PAREN statement'''
        if len(p) == 8:
            p[0] = ForStmtNode(p[3], p[4], p[5], p[7])
        else:
            p[0] = ForStmtNode(p[3], p[4], None, p[6])
    
    def p_return_statement(self, p):
        '''return_statement : RETURN SEMICOLON
                           | RETURN expression SEMICOLON'''
        if len(p) == 3:
            p[0] = ReturnStmtNode()
        else:
            p[0] = ReturnStmtNode(p[2])
    
    def p_break_statement(self, p):
        '''break_statement : BREAK SEMICOLON'''
        p[0] = BreakStmtNode()
    
    def p_continue_statement(self, p):
        '''continue_statement : CONTINUE SEMICOLON'''
        p[0] = ContinueStmtNode()
    
    # Expressions
    def p_expression(self, p):
        '''expression : assignment_expression'''
        p[0] = p[1]
    
    def p_assignment_expression(self, p):
        '''assignment_expression : logical_or_expression
                                | postfix_expression ASSIGN assignment_expression
                                | postfix_expression PLUS_ASSIGN assignment_expression
                                | postfix_expression MINUS_ASSIGN assignment_expression
                                | postfix_expression MULTIPLY_ASSIGN assignment_expression
                                | postfix_expression DIVIDE_ASSIGN assignment_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = AssignmentExprNode(p[1], p[2], p[3])
    
    def p_logical_or_expression(self, p):
        '''logical_or_expression : logical_and_expression
                                | logical_or_expression LOGICAL_OR logical_and_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_logical_and_expression(self, p):
        '''logical_and_expression : bitwise_or_expression
                                 | logical_and_expression LOGICAL_AND bitwise_or_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_bitwise_or_expression(self, p):
        '''bitwise_or_expression : bitwise_xor_expression
                                | bitwise_or_expression BITWISE_OR bitwise_xor_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_bitwise_xor_expression(self, p):
        '''bitwise_xor_expression : bitwise_and_expression
                                 | bitwise_xor_expression BITWISE_XOR bitwise_and_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_bitwise_and_expression(self, p):
        '''bitwise_and_expression : equality_expression
                                 | bitwise_and_expression BITWISE_AND equality_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_equality_expression(self, p):
        '''equality_expression : relational_expression
                              | equality_expression EQUAL relational_expression
                              | equality_expression NOT_EQUAL relational_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_relational_expression(self, p):
        '''relational_expression : shift_expression
                                | relational_expression LESS_THAN shift_expression
                                | relational_expression GREATER_THAN shift_expression
                                | relational_expression LESS_EQUAL shift_expression
                                | relational_expression GREATER_EQUAL shift_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_shift_expression(self, p):
        '''shift_expression : additive_expression
                           | shift_expression LEFT_SHIFT additive_expression
                           | shift_expression RIGHT_SHIFT additive_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_additive_expression(self, p):
        '''additive_expression : multiplicative_expression
                              | additive_expression PLUS multiplicative_expression
                              | additive_expression MINUS multiplicative_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_multiplicative_expression(self, p):
        '''multiplicative_expression : unary_expression
                                    | multiplicative_expression MULTIPLY unary_expression
                                    | multiplicative_expression DIVIDE unary_expression
                                    | multiplicative_expression MODULO unary_expression'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExprNode(p[1], p[2], p[3])
    
    def p_unary_expression(self, p):
        '''unary_expression : postfix_expression
                           | PLUS unary_expression
                           | MINUS unary_expression %prec UMINUS
                           | LOGICAL_NOT unary_expression
                           | BITWISE_NOT unary_expression
                           | BITWISE_AND unary_expression
                           | MULTIPLY unary_expression
                           | INCREMENT unary_expression
                           | DECREMENT unary_expression
                           | LEFT_PAREN type_specifier RIGHT_PAREN unary_expression'''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 5:
            # Type cast: (type)expression
            p[0] = CastExprNode(p[2], p[4])
        else:
            if p[1] == '&':
                p[0] = AddressOfNode(p[2])
            elif p[1] == '*':
                p[0] = DereferenceNode(p[2])
            elif p[1] == '++':
                p[0] = PostfixExprNode(p[2], '++')
            elif p[1] == '--':
                p[0] = PostfixExprNode(p[2], '--')
            else:
                p[0] = UnaryExprNode(p[1], p[2])
    
    def p_postfix_expression(self, p):
        '''postfix_expression : primary_expression
         | postfix_expression LEFT_BRACKET expression RIGHT_BRACKET
         | postfix_expression LEFT_PAREN argument_list RIGHT_PAREN
         | postfix_expression LEFT_PAREN RIGHT_PAREN
         | postfix_expression DOT IDENTIFIER
         | postfix_expression ARROW IDENTIFIER
         | postfix_expression INCREMENT
         | postfix_expression DECREMENT'''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = PostfixExprNode(p[1], p[2])
        elif len(p) == 4:
            if p[2] == '.':
                p[0] = MemberExprNode(p[1], p[3], False)
            elif p[2] == '->':
                p[0] = MemberExprNode(p[1], p[3], True)
            else:
                p[0] = CallExprNode(p[1], [])
        else:
            if p[2] == '[':
                p[0] = ArrayAccessNode(p[1], p[3])
            else:
                p[0] = CallExprNode(p[1], p[3])
    
    def p_argument_list(self, p):
        '''argument_list : expression
                        | argument_list COMMA expression'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]
    
    def p_primary_expression(self, p):
        '''primary_expression : IDENTIFIER
                             | INTEGER
                             | FLOAT
                             | STRING
                             | CHAR
                             | TRUE
                             | FALSE
                             | LEFT_PAREN expression RIGHT_PAREN
                             | array_literal
                             | message_send
                             | message_recv
                             | rtos_call
                             | hw_call'''
        if len(p) == 2:
            # Handle based on token type, not value type
            if p.slice[1].type == 'IDENTIFIER':
                p[0] = IdentifierExprNode(p[1])
            elif p.slice[1].type == 'INTEGER':
                p[0] = LiteralExprNode(p[1], 'int')
            elif p.slice[1].type == 'FLOAT':
                p[0] = LiteralExprNode(p[1], 'float')
            elif p.slice[1].type == 'STRING':
                p[0] = LiteralExprNode(p[1], 'string')
            elif p.slice[1].type == 'CHAR':
                p[0] = LiteralExprNode(p[1], 'char')
            elif p.slice[1].type == 'TRUE':
                p[0] = LiteralExprNode(True, 'bool')
            elif p.slice[1].type == 'FALSE':
                p[0] = LiteralExprNode(False, 'bool')
            else:
                # Other node types (message_send, rtos_call, etc.)
                p[0] = p[1]
        else:
            # Parenthesized expression: (expression)
            p[0] = p[2]
    
    def p_array_literal(self, p):
        '''array_literal : LEFT_BRACE expression_list RIGHT_BRACE
                        | LEFT_BRACE RIGHT_BRACE'''
        if len(p) == 4:
            p[0] = ArrayLiteralNode(p[2])
        else:
            p[0] = ArrayLiteralNode([])
    
    def p_expression_list(self, p):
        '''expression_list : expression
                          | expression_list COMMA expression'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]
    
    def p_message_send(self, p):
        '''message_send : SEND LEFT_PAREN expression COMMA expression RIGHT_PAREN'''
        p[0] = MessageSendNode(p[3], p[5])
    
    def p_message_recv(self, p):
        '''message_recv : RECV LEFT_PAREN expression RIGHT_PAREN'''
        p[0] = MessageRecvNode(p[3])
    
    def p_rtos_call(self, p):
        '''rtos_call : RTOS_CREATE_TASK LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_DELETE_TASK LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_DELAY_MS LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_SEMAPHORE_CREATE LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_SEMAPHORE_TAKE LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_SEMAPHORE_GIVE LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_YIELD LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_SUSPEND_TASK LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_RESUME_TASK LEFT_PAREN argument_list RIGHT_PAREN
                    | RTOS_CREATE_TASK LEFT_PAREN RIGHT_PAREN
                    | RTOS_DELETE_TASK LEFT_PAREN RIGHT_PAREN
                    | RTOS_DELAY_MS LEFT_PAREN RIGHT_PAREN
                    | RTOS_SEMAPHORE_CREATE LEFT_PAREN RIGHT_PAREN
                    | RTOS_SEMAPHORE_TAKE LEFT_PAREN RIGHT_PAREN
                    | RTOS_SEMAPHORE_GIVE LEFT_PAREN RIGHT_PAREN
                    | RTOS_YIELD LEFT_PAREN RIGHT_PAREN
                    | RTOS_SUSPEND_TASK LEFT_PAREN RIGHT_PAREN
                    | RTOS_RESUME_TASK LEFT_PAREN RIGHT_PAREN'''
        if len(p) == 5:
            p[0] = CallExprNode(IdentifierExprNode(p[1]), p[3])
        else:
            p[0] = CallExprNode(IdentifierExprNode(p[1]), [])
    
    def p_hw_call(self, p):
        '''hw_call : HW_GPIO_INIT LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_GPIO_SET LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_GPIO_GET LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_TIMER_INIT LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_TIMER_START LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_TIMER_STOP LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_TIMER_SET_PWM_DUTY LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_ADC_INIT LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_ADC_READ LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_UART_WRITE LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_SPI_TRANSFER LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_I2C_WRITE LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_I2C_READ LEFT_PAREN argument_list RIGHT_PAREN
                  | HW_GPIO_INIT LEFT_PAREN RIGHT_PAREN
                  | HW_GPIO_SET LEFT_PAREN RIGHT_PAREN
                  | HW_GPIO_GET LEFT_PAREN RIGHT_PAREN
                  | HW_TIMER_INIT LEFT_PAREN RIGHT_PAREN
                  | HW_TIMER_START LEFT_PAREN RIGHT_PAREN
                  | HW_TIMER_STOP LEFT_PAREN RIGHT_PAREN
                  | HW_TIMER_SET_PWM_DUTY LEFT_PAREN RIGHT_PAREN
                  | HW_ADC_INIT LEFT_PAREN RIGHT_PAREN
                  | HW_ADC_READ LEFT_PAREN RIGHT_PAREN
                  | HW_UART_WRITE LEFT_PAREN RIGHT_PAREN
                  | HW_SPI_TRANSFER LEFT_PAREN RIGHT_PAREN
                  | HW_I2C_WRITE LEFT_PAREN RIGHT_PAREN
                  | HW_I2C_READ LEFT_PAREN RIGHT_PAREN'''
        if len(p) == 5:
            p[0] = CallExprNode(IdentifierExprNode(p[1]), p[3])
        else:
            p[0] = CallExprNode(IdentifierExprNode(p[1]), [])
    
    # Error rule for syntax errors
    def p_error(self, p):
        if p:
            print(f"Syntax error at token {p.type} ('{p.value}') at line {p.lineno}")
        else:
            print("Syntax error at EOF")

# Create a global parser instance
parser = RTMCParser()
