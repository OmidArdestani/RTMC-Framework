"""
Abstract Syntax Tree (AST) nodes for RT-Micro-C language
Defines the structure of parsed code.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum, auto

class NodeType(Enum):
    """AST node types"""
    # Program structure
    PROGRAM        = auto()
    FUNCTION_DECL  = auto()
    STRUCT_DECL    = auto()
    UNION_DECL     = auto()
    VARIABLE_DECL  = auto()
    ARRAY_DECL     = auto()
    MESSAGE_DECL   = auto()
    INCLUDE_STMT   = auto()
    POINTER_DECL   = auto()  # Pointer declaration
    
    # Statements
    BLOCK_STMT      = auto()
    EXPRESSION_STMT = auto()
    IF_STMT         = auto()
    WHILE_STMT      = auto()
    FOR_STMT        = auto()
    RETURN_STMT     = auto()
    BREAK_STMT      = auto()
    CONTINUE_STMT   = auto()
    
    # Expressions
    BINARY_EXPR     = auto()
    UNARY_EXPR      = auto()
    ASSIGNMENT_EXPR = auto()
    CALL_EXPR       = auto()
    MEMBER_EXPR     = auto()
    IDENTIFIER_EXPR = auto()
    LITERAL_EXPR    = auto()
    ARRAY_LITERAL   = auto()
    ARRAY_ACCESS    = auto()
    MESSAGE_SEND    = auto()
    MESSAGE_RECV    = auto()
    POSTFIX_EXPR    = auto()  # For ++ and --
    ADDRESS_OF      = auto()  # Address-of operator &
    DEREFERENCE     = auto()  # Dereference operator *
    CAST_EXPR       = auto()  # Cast expression
    SIZEOF_EXPR     = auto()  # Sizeof expression
    
    # Types
    PRIMITIVE_TYPE = auto()
    STRUCT_TYPE    = auto()
    UNION_TYPE     = auto()
    ARRAY_TYPE     = auto()
    POINTER_TYPE   = auto()  # Pointer type

class ASTNode(ABC):
    """Base class for all AST nodes"""
    
    def __init__(self, node_type: NodeType, line: int = 0, column: int = 0, filename: str = ""):
        self.node_type = node_type
        self.line = line
        self.column = column  # Enhanced line tracking for better debug info
        self.filename = filename
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor (visitor pattern)"""
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

# Program structure nodes

class ProgramNode(ASTNode):
    """Root node of the AST"""
    
    def __init__(self, declarations: List[ASTNode], line: int = 0, filename: str = ""):
        super().__init__(NodeType.PROGRAM, line, filename=filename)
        self.declarations = declarations
    
    def accept(self, visitor):
        return visitor.visit_program(self)

class FunctionDeclNode(ASTNode):
    """Function declaration node"""
    
    def __init__(self, name: str, return_type: 'TypeNode', parameters: List['ParameterNode'], 
                 body: 'BlockStmtNode', line: int = 0, filename: str = ""):
        super().__init__(NodeType.FUNCTION_DECL, line, filename=filename)
        self.name = name
        self.return_type = return_type
        self.parameters = parameters
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_function_decl(self)

@dataclass
class ParameterNode:
    """Function parameter"""
    name: str
    type: 'TypeNode'
    line: int = 0

class StructDeclNode(ASTNode):
    """Structure declaration node"""
    
    def __init__(self, name: str, fields: List['FieldNode'], base_struct, line: int = 0, column: int = 0, filename: str = ""):
        super().__init__(NodeType.STRUCT_DECL, line, column, filename)
        self.name = name
        self.fields = fields
        self.base_struct = base_struct
        self.total_size = 0      # Computed size during semantic analysis
        self.field_offsets = {}  # Dict mapping field_name -> offset
    
    def accept(self, visitor):
        return visitor.visit_struct_decl(self)

class UnionDeclNode(ASTNode):
    """Union declaration node"""
    
    def __init__(self, name: str, fields: List['FieldNode'], line: int = 0, column: int = 0, filename: str = ""):
        super().__init__(NodeType.UNION_DECL, line, column, filename)
        self.name = name
        self.fields = fields
        self.total_size = 0      # Computed size during semantic analysis (max of all field sizes)
        self.field_offsets = {}  # Dict mapping field_name -> offset (all start at 0 for unions)
    
    def accept(self, visitor):
        return visitor.visit_union_decl(self)

class MessageDeclNode(ASTNode):
    """Message queue declaration node for RT-Micro-C"""
    
    def __init__(self, name: str, message_type: 'TypeNode', line: int = 0):
        super().__init__(NodeType.MESSAGE_DECL, line)
        self.name = name
        self.message_type = message_type
    
    def accept(self, visitor):
        return visitor.visit_message_decl(self)

class ArrayDeclNode(ASTNode):
    """Array declaration node for fixed-length arrays"""
    
    def __init__(self, name: str, element_type: 'TypeNode', size: int, 
                 initializer: Optional['ExpressionNode'] = None, line: int = 0,
                 union_group: Optional[str] = None, bit_width: Optional[int] = None):
        super().__init__(NodeType.ARRAY_DECL, line)
        self.name = name
        self.element_type = element_type
        self.size = size
        self.initializer = initializer
        self.union_group = union_group  # For struct fields that are part of a union
        self.bit_width = bit_width      # For bitfield support
    
    def accept(self, visitor):
        return visitor.visit_array_decl(self)

@dataclass
class FieldNode:
    """Structure field with support for nested structs and bit-fields"""
    def __init__(self, name: str, type: 'TypeNode', bit_width: Optional[int] = None, 
                 offset: Optional[int] = None, initializer: Optional['ExpressionNode'] = None, 
                 line: int = 0, column: int = 0, union_group: Optional[str] = None):
        self.name = name
        self.type = type
        self.bit_width = bit_width
        self.offset = offset         # Byte offset from struct base
        self.bit_offset = 0          # Bit offset within byte (for bit-fields)
        self.size = 0                # Size in bytes (calculated during analysis)
        self.initializer = initializer  # Default initialization value
        self.is_base_struct = False  # True if this field is used for inheritance
        self.union_group = union_group  # Identifier for union grouping (fields with same group overlap)
        self.line = line
        self.column = column

class VariableDeclNode(ASTNode):
    """Variable declaration node"""
    
    def __init__(self, name: str, type: 'TypeNode', initializer: Optional['ExpressionNode'] = None, 
                 is_const: bool = False, line: int = 0, column: int = 0, filename: str = "",
                 union_group: Optional[str] = None, bit_width: Optional[int] = None):
        super().__init__(NodeType.VARIABLE_DECL, line, column, filename)
        self.name = name
        self.type = type
        self.initializer = initializer
        self.is_const = is_const
        self.union_group = union_group  # For struct fields that are part of a union
        self.bit_width = bit_width      # For bitfield support
    
    def accept(self, visitor):
        return visitor.visit_variable_decl(self)

# Type nodes

class TypeNode(ASTNode):
    """Base class for type nodes"""
    pass

class PrimitiveTypeNode(TypeNode):
    """Primitive type node (int, float, char, void)"""
    
    def __init__(self, type_name: str, line: int = 0):
        super().__init__(NodeType.PRIMITIVE_TYPE, line)
        self.type_name = type_name
    
    def accept(self, visitor):
        return visitor.visit_primitive_type(self)

class StructTypeNode(TypeNode):
    """Structure type node"""
    
    def __init__(self, struct_name: str, line: int = 0):
        super().__init__(NodeType.STRUCT_TYPE, line)
        self.struct_name = struct_name
    
    def accept(self, visitor):
        return visitor.visit_struct_type(self)

class UnionTypeNode(TypeNode):
    """Union type node"""
    
    def __init__(self, union_name: str, line: int = 0):
        super().__init__(NodeType.UNION_TYPE, line)
        self.union_name = union_name
    
    def accept(self, visitor):
        return visitor.visit_union_type(self)

class ArrayTypeNode(TypeNode):
    """Array type node"""
    
    def __init__(self, element_type: TypeNode, size: Optional[int] = None, line: int = 0, column: int = 0):
        super().__init__(NodeType.ARRAY_TYPE, line, column)
        self.element_type = element_type
        self.size = size
    
    def accept(self, visitor):
        return visitor.visit_array_type(self)

class PointerTypeNode(TypeNode):
    """Pointer type node"""
    
    def __init__(self, base_type: TypeNode, pointer_level: int = 1, line: int = 0, column: int = 0):
        super().__init__(NodeType.POINTER_TYPE, line, column)
        self.base_type = base_type
        self.pointer_level = pointer_level  # 1 = *, 2 = ** etc.
    
    def accept(self, visitor):
        return visitor.visit_pointer_type(self)

# Statement nodes

class StatementNode(ASTNode):
    """Base class for statement nodes"""
    pass

class BlockStmtNode(StatementNode):
    """Block statement node"""
    
    def __init__(self, statements: List[StatementNode], line: int = 0):
        super().__init__(NodeType.BLOCK_STMT, line)
        self.statements = statements
    
    def accept(self, visitor):
        return visitor.visit_block_stmt(self)

class ExpressionStmtNode(StatementNode):
    """Expression statement node"""
    
    def __init__(self, expression: 'ExpressionNode', line: int = 0):
        super().__init__(NodeType.EXPRESSION_STMT, line)
        self.expression = expression
    
    def accept(self, visitor):
        return visitor.visit_expression_stmt(self)

class IfStmtNode(StatementNode):
    """If statement node"""
    
    def __init__(self, condition: 'ExpressionNode', then_stmt: StatementNode, 
                 else_stmt: Optional[StatementNode] = None, line: int = 0):
        super().__init__(NodeType.IF_STMT, line)
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt
    
    def accept(self, visitor):
        return visitor.visit_if_stmt(self)

class WhileStmtNode(StatementNode):
    """While statement node"""
    
    def __init__(self, condition: 'ExpressionNode', body: StatementNode, line: int = 0):
        super().__init__(NodeType.WHILE_STMT, line)
        self.condition = condition
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_while_stmt(self)

class ForStmtNode(StatementNode):
    """For statement node"""
    
    def __init__(self, init: Optional[StatementNode], condition: Optional['ExpressionNode'], 
                 update: Optional['ExpressionNode'], body: StatementNode, line: int = 0):
        super().__init__(NodeType.FOR_STMT, line)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_for_stmt(self)

class ReturnStmtNode(StatementNode):
    """Return statement node"""
    
    def __init__(self, value: Optional['ExpressionNode'] = None, line: int = 0):
        super().__init__(NodeType.RETURN_STMT, line)
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_return_stmt(self)

class BreakStmtNode(StatementNode):
    """Break statement node"""
    
    def __init__(self, line: int = 0):
        super().__init__(NodeType.BREAK_STMT, line)
    
    def accept(self, visitor):
        return visitor.visit_break_stmt(self)

class ContinueStmtNode(StatementNode):
    """Continue statement node"""
    
    def __init__(self, line: int = 0):
        super().__init__(NodeType.CONTINUE_STMT, line)
    
    def accept(self, visitor):
        return visitor.visit_continue_stmt(self)

class IncludeStmtNode(StatementNode):
    """Include statement node"""
    
    def __init__(self, filepath: str, line: int = 0):
        super().__init__(NodeType.INCLUDE_STMT, line)
        self.filepath = filepath
    
    def accept(self, visitor):
        return visitor.visit_inlcude_stmt(self)

# Expression nodes

class ExpressionNode(ASTNode):
    """Base class for expression nodes"""
    pass

class BinaryExprNode(ExpressionNode):
    """Binary expression node"""
    
    def __init__(self, left: ExpressionNode, operator: str, right: ExpressionNode, line: int = 0):
        super().__init__(NodeType.BINARY_EXPR, line)
        self.left = left
        self.operator = operator
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_binary_expr(self)

class UnaryExprNode(ExpressionNode):
    """Unary expression node"""
    
    def __init__(self, operator: str, operand: ExpressionNode, line: int = 0):
        super().__init__(NodeType.UNARY_EXPR, line)
        self.operator = operator
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_unary_expr(self)

class PostfixExprNode(ExpressionNode):
    """Postfix expression node (++ and --)"""
    
    def __init__(self, operand: ExpressionNode, operator: str, line: int = 0):
        super().__init__(NodeType.POSTFIX_EXPR, line)
        self.operand = operand
        self.operator = operator  # "++" or "--"
    
    def accept(self, visitor):
        return visitor.visit_postfix_expr(self)

class AssignmentExprNode(ExpressionNode):
    """Assignment expression node"""
    
    def __init__(self, target: ExpressionNode, operator: str, value: ExpressionNode, line: int = 0):
        super().__init__(NodeType.ASSIGNMENT_EXPR, line)
        self.target = target
        self.operator = operator
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_assignment_expr(self)

class CallExprNode(ExpressionNode):
    """Function call expression node"""
    
    def __init__(self, callee: ExpressionNode, arguments: List[ExpressionNode], line: int = 0):
        super().__init__(NodeType.CALL_EXPR, line)
        self.callee = callee
        self.arguments = arguments
    
    def accept(self, visitor):
        return visitor.visit_call_expr(self)

class MemberExprNode(ExpressionNode):
    """Member access expression node"""
    
    def __init__(self, object: ExpressionNode, property: str, computed: bool = False, line: int = 0):
        super().__init__(NodeType.MEMBER_EXPR, line)
        self.object = object
        self.property = property
        self.computed = computed  # True for array[index], False for struct.field
    
    def accept(self, visitor):
        return visitor.visit_member_expr(self)

class IdentifierExprNode(ExpressionNode):
    """Identifier expression node"""
    
    def __init__(self, name: str, line: int = 0, filename: str = ""):
        super().__init__(NodeType.IDENTIFIER_EXPR, line, filename=filename)
        self.name = name
    
    def accept(self, visitor):
        return visitor.visit_identifier_expr(self)

class LiteralExprNode(ExpressionNode):
    """Literal expression node"""
    
    def __init__(self, value: Any, literal_type: str, line: int = 0):
        super().__init__(NodeType.LITERAL_EXPR, line)
        self.value = value
        self.literal_type = literal_type  # 'int', 'float', 'string', 'char'
    
    def accept(self, visitor):
        return visitor.visit_literal_expr(self)

class ArrayLiteralNode(ExpressionNode):
    """Array literal expression node for initializer lists"""
    
    def __init__(self, elements: List[ExpressionNode], line: int = 0):
        super().__init__(NodeType.ARRAY_LITERAL, line)
        self.elements = elements
    
    def accept(self, visitor):
        return visitor.visit_array_literal(self)

class ArrayAccessNode(ExpressionNode):
    """Array access expression node for indexed access"""
    
    def __init__(self, array: ExpressionNode, index: ExpressionNode, line: int = 0):
        super().__init__(NodeType.ARRAY_ACCESS, line)
        self.array = array
        self.index = index
    
    def accept(self, visitor):
        return visitor.visit_array_access(self)

class MessageSendNode(ExpressionNode):
    """Message send expression node"""
    
    def __init__(self, channel: str, payload: ExpressionNode, line: int = 0):
        super().__init__(NodeType.MESSAGE_SEND, line)
        self.channel = channel
        self.payload = payload
    
    def accept(self, visitor):
        return visitor.visit_message_send(self)

class MessageRecvNode(ExpressionNode):
    """Message receive expression node"""
    
    def __init__(self, channel: str, timeout: Optional['ExpressionNode'] = None, line: int = 0, column: int = 0):
        super().__init__(NodeType.MESSAGE_RECV, line, column)
        self.channel = channel
        self.timeout = timeout  # Optional timeout expression
    
    def accept(self, visitor):
        return visitor.visit_message_recv(self)

class AddressOfNode(ExpressionNode):
    """Address-of expression node (&variable)"""
    
    def __init__(self, operand: ExpressionNode, line: int = 0, column: int = 0):
        super().__init__(NodeType.ADDRESS_OF, line, column)
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_address_of(self)

class DereferenceNode(ExpressionNode):
    """Dereference expression node (*pointer)"""
    
    def __init__(self, operand: ExpressionNode, line: int = 0, column: int = 0):
        super().__init__(NodeType.DEREFERENCE, line, column)
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_dereference(self)

class CastExprNode(ExpressionNode):
    """Cast expression node (type)expression"""
    
    def __init__(self, target_type: 'TypeNode', operand: ExpressionNode, line: int = 0, column: int = 0):
        super().__init__(NodeType.CAST_EXPR, line, column)
        self.target_type = target_type
        self.operand = operand
    
    def accept(self, visitor):
        return visitor.visit_cast_expr(self)

class SizeOfExprNode(ExpressionNode):
    """Sizeof expression node"""
    
    def __init__(self, target, line: int = 0, column: int = 0):
        super().__init__(NodeType.SIZEOF_EXPR, line, column)
        self.target = target  # Can be a TypeNode, IdentifierExprNode, or other expression
    
    def accept(self, visitor):
        return visitor.visit_sizeof_expr(self)

class PointerDeclNode(VariableDeclNode):
    """Pointer declaration node"""
    
    def __init__(self, name: str, base_type: 'TypeNode', pointer_level: int = 1,
                 initializer: Optional['ExpressionNode'] = None, 
                 is_const: bool = False, line: int = 0, column: int = 0, filename: str = ""):
        # Create pointer type for the base class
        pointer_type = PointerTypeNode(base_type, pointer_level, line, column)
        super().__init__(name, pointer_type, initializer, is_const, line, column, filename)
        self.node_type = NodeType.POINTER_DECL
        self.base_type = base_type
        self.pointer_level = pointer_level
    
    def accept(self, visitor):
        return visitor.visit_pointer_decl(self)

# Visitor interface

class ASTVisitor(ABC):
    """Abstract base class for AST visitors"""
    
    @abstractmethod
    def visit_program(self, node: ProgramNode): pass
    
    @abstractmethod
    def visit_function_decl(self, node: FunctionDeclNode): pass
    
    @abstractmethod
    def visit_struct_decl(self, node: StructDeclNode): pass
    
    @abstractmethod
    def visit_union_decl(self, node: UnionDeclNode): pass
    
    @abstractmethod
    def visit_message_decl(self, node: MessageDeclNode): pass
    
    @abstractmethod
    def visit_variable_decl(self, node: VariableDeclNode): pass
    
    @abstractmethod
    def visit_array_decl(self, node: ArrayDeclNode): pass
    
    @abstractmethod
    def visit_include_stmt(self, node: IncludeStmtNode): pass
    
    @abstractmethod
    def visit_primitive_type(self, node: PrimitiveTypeNode): pass
    
    @abstractmethod
    def visit_struct_type(self, node: StructTypeNode): pass
    
    @abstractmethod
    def visit_union_type(self, node: UnionTypeNode): pass
    
    @abstractmethod
    def visit_array_type(self, node: ArrayTypeNode): pass
    
    @abstractmethod
    def visit_pointer_type(self, node: PointerTypeNode): pass
    
    @abstractmethod
    def visit_pointer_decl(self, node: PointerDeclNode): pass
    
    @abstractmethod
    def visit_address_of(self, node: AddressOfNode): pass
    
    @abstractmethod
    def visit_dereference(self, node: DereferenceNode): pass
    
    @abstractmethod
    def visit_cast_expr(self, node: CastExprNode): pass
    
    @abstractmethod
    def visit_sizeof_expr(self, node: SizeOfExprNode): pass
    
    @abstractmethod
    def visit_block_stmt(self, node: BlockStmtNode): pass
    
    @abstractmethod
    def visit_expression_stmt(self, node: ExpressionStmtNode): pass
    
    @abstractmethod
    def visit_if_stmt(self, node: IfStmtNode): pass
    
    @abstractmethod
    def visit_while_stmt(self, node: WhileStmtNode): pass
    
    @abstractmethod
    def visit_for_stmt(self, node: ForStmtNode): pass
    
    @abstractmethod
    def visit_return_stmt(self, node: ReturnStmtNode): pass
    
    @abstractmethod
    def visit_break_stmt(self, node: BreakStmtNode): pass
    
    @abstractmethod
    def visit_continue_stmt(self, node: ContinueStmtNode): pass
    
    @abstractmethod
    def visit_binary_expr(self, node: BinaryExprNode): pass
    
    @abstractmethod
    def visit_unary_expr(self, node: UnaryExprNode): pass
    
    @abstractmethod
    def visit_assignment_expr(self, node: AssignmentExprNode): pass
    
    @abstractmethod
    def visit_call_expr(self, node: CallExprNode): pass
    
    @abstractmethod
    def visit_member_expr(self, node: MemberExprNode): pass
    
    @abstractmethod
    def visit_identifier_expr(self, node: IdentifierExprNode): pass
    
    @abstractmethod
    def visit_literal_expr(self, node: LiteralExprNode): pass
    
    @abstractmethod
    def visit_array_literal(self, node: ArrayLiteralNode): pass
    
    @abstractmethod
    def visit_array_access(self, node: ArrayAccessNode): pass
    
    @abstractmethod
    def visit_message_send(self, node: MessageSendNode): pass
    
    @abstractmethod
    def visit_message_recv(self, node: MessageRecvNode): pass

# Utility functions

def ast_to_string(node: ASTNode, indent: int = 0) -> str:
    """Convert AST to string representation"""
    indent_str = "  " * indent
    
    if isinstance(node, ProgramNode):
        result = f"{indent_str}Program:\n"
        for decl in node.declarations:
            result += ast_to_string(decl, indent + 1)
        return result
    
    elif isinstance(node, FunctionDeclNode):
        result = f"{indent_str}FunctionDecl: {node.name}\n"
        result += f"{indent_str}  ReturnType: {ast_to_string(node.return_type, 0).strip()}\n"
        if node.parameters:
            result += f"{indent_str}  Parameters:\n"
            for param in node.parameters:
                result += f"{indent_str}    {param.name}: {ast_to_string(param.type, 0).strip()}\n"
        result += f"{indent_str}  Body:\n{ast_to_string(node.body, indent + 2)}"
        return result
    
    elif isinstance(node, StructDeclNode):
        result = f"{indent_str}StructDecl: {node.name}\n"
        for field in node.fields:
            bit_info = f":{field.bit_width}" if field.bit_width else ""
            result += f"{indent_str}  {field.name}: {ast_to_string(field.type, 0).strip()}{bit_info}\n"
        return result
    
    elif isinstance(node, UnionDeclNode):
        result = f"{indent_str}UnionDecl: {node.name}\n"
        for field in node.fields:
            result += f"{indent_str}  {field.name}: {ast_to_string(field.type, 0).strip()}\n"
        return result
    
    elif isinstance(node, MessageDeclNode):
        return f"{indent_str}MessageDecl: {node.name}: {ast_to_string(node.message_type, 0).strip()}\n"
    
    elif isinstance(node, VariableDeclNode):
        const_str = "const " if node.is_const else ""
        init_str = f" = {ast_to_string(node.initializer, 0).strip()}" if node.initializer else ""
        return f"{indent_str}VariableDecl: {const_str}{node.name}: {ast_to_string(node.type, 0).strip()}{init_str}\n"
    
    elif isinstance(node, ArrayDeclNode):
        init_str = f" = {ast_to_string(node.initializer, 0).strip()}" if node.initializer else ""
        return f"{indent_str}ArrayDecl: {node.name}: {ast_to_string(node.element_type, 0).strip()}[{node.size}]{init_str}\n"
    
    elif isinstance(node, PrimitiveTypeNode):
        return f"{node.type_name}"
    
    elif isinstance(node, StructTypeNode):
        return f"struct {node.struct_name}"
    
    elif isinstance(node, UnionTypeNode):
        return f"union {node.union_name}"
    
    elif isinstance(node, ArrayTypeNode):
        size_str = f"[{node.size}]" if node.size else "[]"
        return f"{ast_to_string(node.element_type, 0).strip()}{size_str}"
    
    elif isinstance(node, PointerTypeNode):
        stars = "*" * node.pointer_level
        return f"{ast_to_string(node.base_type, 0).strip()}{stars}"
    
    elif isinstance(node, PointerDeclNode):
        stars = "*" * node.pointer_level
        const_str = "const " if node.is_const else ""
        init_str = f" = {ast_to_string(node.initializer, 0).strip()}" if node.initializer else ""
        return f"{indent_str}PointerDecl: {const_str}{ast_to_string(node.base_type, 0).strip()}{stars} {node.name}{init_str}\n"
    
    elif isinstance(node, AddressOfNode):
        return f"{indent_str}AddressOf:\n{ast_to_string(node.operand, indent + 1)}"
    
    elif isinstance(node, DereferenceNode):
        return f"{indent_str}Dereference:\n{ast_to_string(node.operand, indent + 1)}"
    
    elif isinstance(node, SizeOfExprNode):
        return f"{indent_str}SizeOf:\n{ast_to_string(node.target, indent + 1)}"
    
    elif isinstance(node, BlockStmtNode):
        result = f"{indent_str}Block:\n"
        for stmt in node.statements:
            result += ast_to_string(stmt, indent + 1)
        return result
    
    elif isinstance(node, ExpressionStmtNode):
        return f"{indent_str}ExpressionStmt:\n{ast_to_string(node.expression, indent + 1)}"
    
    elif isinstance(node, IfStmtNode):
        result = f"{indent_str}If:\n"
        result += f"{indent_str}  Condition:\n{ast_to_string(node.condition, indent + 2)}"
        result += f"{indent_str}  Then:\n{ast_to_string(node.then_stmt, indent + 2)}"
        if node.else_stmt:
            result += f"{indent_str}  Else:\n{ast_to_string(node.else_stmt, indent + 2)}"
        return result
    
    elif isinstance(node, WhileStmtNode):
        result = f"{indent_str}While:\n"
        result += f"{indent_str}  Condition:\n{ast_to_string(node.condition, indent + 2)}"
        result += f"{indent_str}  Body:\n{ast_to_string(node.body, indent + 2)}"
        return result
    
    elif isinstance(node, ForStmtNode):
        result = f"{indent_str}For:\n"
        if node.init:
            result += f"{indent_str}  Init:\n{ast_to_string(node.init, indent + 2)}"
        if node.condition:
            result += f"{indent_str}  Condition:\n{ast_to_string(node.condition, indent + 2)}"
        if node.update:
            result += f"{indent_str}  Update:\n{ast_to_string(node.update, indent + 2)}"
        result += f"{indent_str}  Body:\n{ast_to_string(node.body, indent + 2)}"
        return result
    
    elif isinstance(node, ReturnStmtNode):
        result = f"{indent_str}Return:\n"
        if node.value:
            result += ast_to_string(node.value, indent + 1)
        return result
    
    elif isinstance(node, BreakStmtNode):
        return f"{indent_str}Break\n"
    
    elif isinstance(node, ContinueStmtNode):
        return f"{indent_str}Continue\n"
    
    elif isinstance(node, BinaryExprNode):
        result = f"{indent_str}BinaryExpr: {node.operator}\n"
        result += f"{indent_str}  Left:\n{ast_to_string(node.left, indent + 2)}"
        result += f"{indent_str}  Right:\n{ast_to_string(node.right, indent + 2)}"
        return result
    
    elif isinstance(node, UnaryExprNode):
        result = f"{indent_str}UnaryExpr: {node.operator}\n"
        result += f"{indent_str}  Operand:\n{ast_to_string(node.operand, indent + 2)}"
        return result
    
    elif isinstance(node, AssignmentExprNode):
        result = f"{indent_str}AssignmentExpr: {node.operator}\n"
        result += f"{indent_str}  Target:\n{ast_to_string(node.target, indent + 2)}"
        result += f"{indent_str}  Value:\n{ast_to_string(node.value, indent + 2)}"
        return result
    
    elif isinstance(node, CallExprNode):
        result = f"{indent_str}CallExpr:\n"
        result += f"{indent_str}  Callee:\n{ast_to_string(node.callee, indent + 2)}"
        if node.arguments:
            result += f"{indent_str}  Arguments:\n"
            for arg in node.arguments:
                result += ast_to_string(arg, indent + 2)
        return result
    
    elif isinstance(node, MemberExprNode):
        access_type = "[]" if node.computed else "."
        result = f"{indent_str}MemberExpr: {access_type}{node.property}\n"
        result += f"{indent_str}  Object:\n{ast_to_string(node.object, indent + 2)}"
        return result
    
    elif isinstance(node, IdentifierExprNode):
        return f"{indent_str}Identifier: {node.name}\n"
    
    elif isinstance(node, LiteralExprNode):
        return f"{indent_str}Literal: {node.value} ({node.literal_type})\n"
    
    elif isinstance(node, ArrayLiteralNode):
        result = f"{indent_str}ArrayLiteral:\n"
        for i, element in enumerate(node.elements):
            result += f"{indent_str}  [{i}]: {ast_to_string(element, indent + 2).strip()}\n"
        return result
    
    elif isinstance(node, ArrayAccessNode):
        result = f"{indent_str}ArrayAccess:\n"
        result += f"{indent_str}  Array:\n{ast_to_string(node.array, indent + 2)}"
        result += f"{indent_str}  Index:\n{ast_to_string(node.index, indent + 2)}"
        return result
    
    elif isinstance(node, MessageSendNode):
        return f"{indent_str}MessageSend: {node.channel}\n  Payload:\n{ast_to_string(node.payload, indent + 2)}"
    
    elif isinstance(node, MessageRecvNode):
        return f"{indent_str}MessageRecv: {node.channel}\n"
    
    else:
        return f"{indent_str}{node.__class__.__name__}: {node.__dict__}\n"
