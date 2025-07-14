"""
Optimizer for RT-Micro-C Language
Performs compile-time optimizations on the AST.
"""

from src.parser.ast_nodes import *
from typing import Dict, List, Optional, Any, Set

class OptimizationError(Exception):
    """Optimization error"""
    pass

class ConstantFolder(ASTVisitor):
    def visit_pointer_type(self, node: PointerTypeNode) -> PointerTypeNode:
        """Pointer types don't need optimization"""
        return node

    def visit_pointer_decl(self, node: PointerDeclNode) -> PointerDeclNode:
        """Optimize pointer declaration"""
        optimized_initializer = None
        if node.initializer:
            optimized_initializer = node.initializer.accept(self)
        return PointerDeclNode(node.name, node.base_type, node.pointer_level, optimized_initializer, node.is_const, node.line, node.column, node.filename)

    def visit_address_of(self, node: AddressOfNode) -> AddressOfNode:
        """Optimize address-of expression"""
        optimized_operand = node.operand.accept(self)
        return AddressOfNode(optimized_operand, node.line)

    def visit_dereference(self, node: DereferenceNode) -> DereferenceNode:
        """Optimize dereference expression"""
        optimized_operand = node.operand.accept(self)
        return DereferenceNode(optimized_operand, node.line)

    def visit_cast_expr(self, node: CastExprNode) -> CastExprNode:
        """Optimize cast expression"""
        optimized_operand = node.operand.accept(self)
        return CastExprNode(node.target_type, optimized_operand, node.line)
    """Constant folding optimizer"""
    
    def __init__(self):
        self.constants: Dict[str, Any] = {}
    
    def visit_program(self, node: ProgramNode) -> ProgramNode:
        """Optimize program"""
        optimized_declarations = []
        
        for decl in node.declarations:
            optimized_decl = decl.accept(self)
            if optimized_decl:
                optimized_declarations.append(optimized_decl)
        
        return ProgramNode(optimized_declarations, node.line)
    
    def visit_function_decl(self, node: FunctionDeclNode) -> FunctionDeclNode:
        """Optimize function declaration"""
        optimized_body = node.body.accept(self)
        
        return FunctionDeclNode(node.name, node.return_type, node.parameters, 
                              optimized_body, node.line)
    
    def visit_struct_decl(self, node: StructDeclNode) -> StructDeclNode:
        """Optimize struct declaration"""
        return node  # Struct declarations don't need optimization

    def visit_union_decl(self, node: UnionDeclNode) -> UnionDeclNode:
        """Optimize union declaration"""
        return node  # Union declarations don't need optimization

    def visit_task_decl(self, node: TaskDeclNode) -> TaskDeclNode:
        """Optimize task declaration"""
        # Optimize task members
        optimized_members = []
        for member in node.members:
            optimized_member = member.accept(self)
            if optimized_member:
                optimized_members.append(optimized_member)
        
        # Optimize run function
        optimized_run_function = node.run_function.accept(self)
        
        return TaskDeclNode(node.name, node.core, node.priority, 
                           optimized_members, optimized_run_function, node.line)

    def visit_variable_decl(self, node: VariableDeclNode) -> VariableDeclNode:
        """Optimize variable declaration"""
        optimized_initializer = None
        
        if node.initializer:
            optimized_initializer = node.initializer.accept(self)
            
            # If it's a constant initializer, record it
            if isinstance(optimized_initializer, LiteralExprNode) and node.is_const:
                self.constants[node.name] = optimized_initializer.value
        
        return VariableDeclNode(node.name, node.type, optimized_initializer, 
                              node.is_const, node.line)
    
    def visit_primitive_type(self, node: PrimitiveTypeNode) -> PrimitiveTypeNode:
        """Type nodes don't need optimization"""
        return node
    
    def visit_struct_type(self, node: StructTypeNode) -> StructTypeNode:
        """Type nodes don't need optimization"""
        return node

    def visit_union_type(self, node: UnionTypeNode) -> UnionTypeNode:
        """Type nodes don't need optimization"""
        return node
    
    def visit_array_type(self, node: ArrayTypeNode) -> ArrayTypeNode:
        """Array types don't need optimization"""
        return node
        
    def visit_block_stmt(self, node: BlockStmtNode) -> BlockStmtNode:
        """Optimize block statement"""
        optimized_statements = []
        
        for stmt in node.statements:
            optimized_stmt = stmt.accept(self)
            if optimized_stmt:
                optimized_statements.append(optimized_stmt)
        
        return BlockStmtNode(optimized_statements, node.line)
    
    def visit_expression_stmt(self, node: ExpressionStmtNode) -> ExpressionStmtNode:
        """Optimize expression statement"""
        optimized_expr = node.expression.accept(self)
        
        # Remove statements with no side effects
        if isinstance(optimized_expr, LiteralExprNode):
            return None  # Dead code elimination
        
        return ExpressionStmtNode(optimized_expr, node.line)
    
    def visit_if_stmt(self, node: IfStmtNode) -> StatementNode:
        """Optimize if statement"""
        optimized_condition = node.condition.accept(self)
        
        # Constant condition optimization
        if isinstance(optimized_condition, LiteralExprNode):
            if self._is_truthy(optimized_condition.value):
                # Condition is always true, replace with then branch
                return node.then_stmt.accept(self)
            else:
                # Condition is always false, replace with else branch or remove
                if node.else_stmt:
                    return node.else_stmt.accept(self)
                else:
                    return None  # Dead code elimination
        
        optimized_then = node.then_stmt.accept(self)
        optimized_else = node.else_stmt.accept(self) if node.else_stmt else None
        
        return IfStmtNode(optimized_condition, optimized_then, optimized_else, node.line)
    
    def visit_while_stmt(self, node: WhileStmtNode) -> StatementNode:
        """Optimize while statement"""
        optimized_condition = node.condition.accept(self)
        
        # Constant condition optimization
        if isinstance(optimized_condition, LiteralExprNode):
            if not self._is_truthy(optimized_condition.value):
                # Condition is always false, remove entire loop
                return None
        
        optimized_body = node.body.accept(self)
        
        return WhileStmtNode(optimized_condition, optimized_body, node.line)
    
    def visit_for_stmt(self, node: ForStmtNode) -> StatementNode:
        """Optimize for statement"""
        optimized_init = node.init.accept(self) if node.init else None
        optimized_condition = node.condition.accept(self) if node.condition else None
        optimized_update = node.update.accept(self) if node.update else None
        
        # Constant condition optimization
        if isinstance(optimized_condition, LiteralExprNode):
            if not self._is_truthy(optimized_condition.value):
                # Condition is always false, return only init statement
                return optimized_init
        
        optimized_body = node.body.accept(self)
        
        return ForStmtNode(optimized_init, optimized_condition, optimized_update, 
                          optimized_body, node.line)
    
    def visit_return_stmt(self, node: ReturnStmtNode) -> ReturnStmtNode:
        """Optimize return statement"""
        optimized_value = node.value.accept(self) if node.value else None
        
        return ReturnStmtNode(optimized_value, node.line)
    
    def visit_break_stmt(self, node: BreakStmtNode) -> BreakStmtNode:
        """Break statements don't need optimization"""
        return node
    
    def visit_continue_stmt(self, node: ContinueStmtNode) -> ContinueStmtNode:
        """Continue statements don't need optimization"""
        return node
    
    def visit_binary_expr(self, node: BinaryExprNode) -> ExpressionNode:
        """Optimize binary expression"""
        optimized_left = node.left.accept(self)
        optimized_right = node.right.accept(self)
        
        # Constant folding
        if isinstance(optimized_left, LiteralExprNode) and isinstance(optimized_right, LiteralExprNode):
            try:
                result = self._fold_binary_constants(optimized_left.value, node.operator, optimized_right.value)
                result_type = self._get_result_type(optimized_left.literal_type, optimized_right.literal_type)
                return LiteralExprNode(result, result_type, node.line)
            except:
                pass  # Fall back to non-optimized version
        
        # Algebraic simplifications
        if node.operator == '+':
            # x + 0 = x, 0 + x = x
            if isinstance(optimized_right, LiteralExprNode) and optimized_right.value == 0:
                return optimized_left
            if isinstance(optimized_left, LiteralExprNode) and optimized_left.value == 0:
                return optimized_right
        
        elif node.operator == '-':
            # x - 0 = x
            if isinstance(optimized_right, LiteralExprNode) and optimized_right.value == 0:
                return optimized_left
        
        elif node.operator == '*':
            # x * 0 = 0, 0 * x = 0
            if isinstance(optimized_right, LiteralExprNode) and optimized_right.value == 0:
                return optimized_right
            if isinstance(optimized_left, LiteralExprNode) and optimized_left.value == 0:
                return optimized_left
            # x * 1 = x, 1 * x = x
            if isinstance(optimized_right, LiteralExprNode) and optimized_right.value == 1:
                return optimized_left
            if isinstance(optimized_left, LiteralExprNode) and optimized_left.value == 1:
                return optimized_right
        
        elif node.operator == '/':
            # x / 1 = x
            if isinstance(optimized_right, LiteralExprNode) and optimized_right.value == 1:
                return optimized_left
        
        return BinaryExprNode(optimized_left, node.operator, optimized_right, node.line)
    
    def visit_unary_expr(self, node: UnaryExprNode) -> ExpressionNode:
        """Optimize unary expression"""
        optimized_operand = node.operand.accept(self)
        
        # Constant folding
        if isinstance(optimized_operand, LiteralExprNode):
            try:
                result = self._fold_unary_constant(node.operator, optimized_operand.value)
                return LiteralExprNode(result, optimized_operand.literal_type, node.line)
            except:
                pass  # Fall back to non-optimized version
        
        return UnaryExprNode(node.operator, optimized_operand, node.line)
    
    def visit_postfix_expr(self, node: PostfixExprNode) -> PostfixExprNode:
        """Optimize postfix expression (no optimization for now)"""
        optimized_operand = node.operand.accept(self)
        return PostfixExprNode(optimized_operand, node.operator, node.line)

    def visit_assignment_expr(self, node: AssignmentExprNode) -> AssignmentExprNode:
        """Optimize assignment expression"""
        optimized_target = node.target.accept(self)
        optimized_value = node.value.accept(self)
        
        return AssignmentExprNode(optimized_target, node.operator, optimized_value, node.line)
    
    def visit_call_expr(self, node: CallExprNode) -> CallExprNode:
        """Optimize call expression"""
        optimized_callee = node.callee.accept(self)
        optimized_arguments = [arg.accept(self) for arg in node.arguments]
        
        return CallExprNode(optimized_callee, optimized_arguments, node.line)
    
    def visit_member_expr(self, node: MemberExprNode) -> MemberExprNode:
        """Optimize member expression"""
        optimized_object = node.object.accept(self)
        
        if node.computed and isinstance(node.property, ExpressionNode):
            optimized_property = node.property.accept(self)
            return MemberExprNode(optimized_object, optimized_property, node.computed, node.line)
        
        return MemberExprNode(optimized_object, node.property, node.computed, node.line)
    
    def visit_identifier_expr(self, node: IdentifierExprNode) -> ExpressionNode:
        """Optimize identifier expression"""
        # Constant propagation
        if node.name in self.constants:
            value = self.constants[node.name]
            literal_type = self._get_literal_type(value)
            return LiteralExprNode(value, literal_type, node.line)
        
        return node
    
    def visit_literal_expr(self, node: LiteralExprNode) -> LiteralExprNode:
        """Literal expressions don't need optimization"""
        return node
    
    def visit_array_decl(self, node: ArrayDeclNode) -> ArrayDeclNode:
        """Optimize array declaration"""
        optimized_initializer = None
        if node.initializer:
            optimized_initializer = node.initializer.accept(self)
        
        return ArrayDeclNode(node.name, node.element_type, node.size, optimized_initializer, node.line)
    
    def visit_array_literal(self, node: ArrayLiteralNode) -> ArrayLiteralNode:
        """Optimize array literal"""
        optimized_elements = []
        for element in node.elements:
            optimized_element = element.accept(self)
            optimized_elements.append(optimized_element)
        
        return ArrayLiteralNode(optimized_elements, node.line)
    
    def visit_array_access(self, node: ArrayAccessNode) -> ArrayAccessNode:
        """Optimize array access"""
        optimized_array = node.array.accept(self)
        optimized_index = node.index.accept(self)
        
        return ArrayAccessNode(optimized_array, optimized_index, node.line)

    def _fold_binary_constants(self, left: Any, op: str, right: Any) -> Any:
        """Fold binary constants"""
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise OptimizationError("Division by zero")
            return left / right
        elif op == '%':
            if right == 0:
                raise OptimizationError("Modulo by zero")
            return left % right
        elif op == '==':
            return 1 if left == right else 0
        elif op == '!=':
            return 1 if left != right else 0
        elif op == '<':
            return 1 if left < right else 0
        elif op == '<=':
            return 1 if left <= right else 0
        elif op == '>':
            return 1 if left > right else 0
        elif op == '>=':
            return 1 if left >= right else 0
        elif op == '&&':
            return 1 if left and right else 0
        elif op == '||':
            return 1 if left or right else 0
        elif op == '&':
            return left & right
        elif op == '|':
            return left | right
        elif op == '^':
            return left ^ right
        else:
            raise OptimizationError(f"Unknown binary operator: {op}")
    
    def _fold_unary_constant(self, op: str, operand: Any) -> Any:
        """Fold unary constants"""
        if op == '+':
            return +operand
        elif op == '-':
            return -operand
        elif op == '!':
            return 1 if not operand else 0
        elif op == '~':
            return ~operand
        else:
            raise OptimizationError(f"Unknown unary operator: {op}")
    
    def _is_truthy(self, value: Any) -> bool:
        """Check if value is truthy"""
        if isinstance(value, (int, float)):
            return value != 0
        return bool(value)
    
    def _get_result_type(self, left_type: str, right_type: str) -> str:
        """Get result type for binary operation"""
        if left_type == 'float' or right_type == 'float':
            return 'float'
        return 'int'
    
    def _get_literal_type(self, value: Any) -> str:
        """Get literal type from value"""
        if isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            return 'string' if len(value) > 1 else 'char'
        else:
            return 'int'

    def visit_message_decl(self, node: MessageDeclNode) -> MessageDeclNode:
        """Message declarations don't need optimization"""
        return node

    def visit_message_send(self, node: MessageSendNode) -> MessageSendNode:
        """Optimize message send expression"""
        optimized_payload = node.payload.accept(self)
        return MessageSendNode(node.channel, optimized_payload, node.line)

    def visit_message_recv(self, node: MessageRecvNode) -> MessageRecvNode:
        """Message receive expressions don't need optimization"""
        # Optimize timeout if present
        optimized_timeout = None
        if node.timeout:
            optimized_timeout = node.timeout.accept(self)
        return MessageRecvNode(node.channel, optimized_timeout, node.line)

    def visit_import_stmt(self, node: ImportStmtNode) -> ImportStmtNode:
        """Import statements don't need optimization"""
        return node

class DeadCodeEliminator(ASTVisitor):
    def visit_pointer_type(self, node: PointerTypeNode) -> PointerTypeNode:
        return node

    def visit_pointer_decl(self, node: PointerDeclNode) -> PointerDeclNode:
        return node

    def visit_address_of(self, node: AddressOfNode) -> AddressOfNode:
        return node

    def visit_dereference(self, node: DereferenceNode) -> DereferenceNode:
        return node

    def visit_cast_expr(self, node: CastExprNode) -> CastExprNode:
        return node
    """Dead code elimination optimizer"""
    
    def __init__(self):
        self.reachable_code = True
    
    def visit_program(self, node: ProgramNode) -> ProgramNode:
        """Eliminate dead code in program"""
        optimized_declarations = []
        
        for decl in node.declarations:
            optimized_decl = decl.accept(self)
            if optimized_decl:
                optimized_declarations.append(optimized_decl)
        
        return ProgramNode(optimized_declarations, node.line)
    
    def visit_function_decl(self, node: FunctionDeclNode) -> FunctionDeclNode:
        """Eliminate dead code in function"""
        self.reachable_code = True
        optimized_body = node.body.accept(self)
        
        return FunctionDeclNode(node.name, node.return_type, node.parameters, 
                              optimized_body, node.line)
    
    def visit_struct_decl(self, node: StructDeclNode) -> StructDeclNode:
        """Struct declarations are always reachable"""
        return node
    
    def visit_union_decl(self, node: UnionDeclNode) -> UnionDeclNode:
        """Union declarations are always reachable"""
        return node

    def visit_task_decl(self, node: TaskDeclNode) -> TaskDeclNode:
        """Task declarations are always reachable"""
        # Tasks are always reachable since they're entry points
        optimized_members = []
        for member in node.members:
            optimized_member = member.accept(self)
            if optimized_member:
                optimized_members.append(optimized_member)
        
        # Optimize run function
        self.reachable_code = True
        optimized_run_function = node.run_function.accept(self)
        
        return TaskDeclNode(node.name, node.core, node.priority, 
                           optimized_members, optimized_run_function, node.line)

    def visit_variable_decl(self, node: VariableDeclNode) -> VariableDeclNode:
        """Variable declarations are always reachable"""
        return node
    
    def visit_primitive_type(self, node: PrimitiveTypeNode) -> PrimitiveTypeNode:
        return node
    
    def visit_struct_type(self, node: StructTypeNode) -> StructTypeNode:
        return node
    
    def visit_union_type(self, node: UnionTypeNode) -> UnionTypeNode:
        return node
    
    def visit_array_type(self, node: ArrayTypeNode) -> ArrayTypeNode:
        return node
    
    def visit_block_stmt(self, node: BlockStmtNode) -> BlockStmtNode:
        """Eliminate dead code in block"""
        optimized_statements = []
        
        for stmt in node.statements:
            if not self.reachable_code:
                break  # Skip unreachable code
            
            optimized_stmt = stmt.accept(self)
            if optimized_stmt:
                optimized_statements.append(optimized_stmt)
        
        return BlockStmtNode(optimized_statements, node.line)
    
    def visit_expression_stmt(self, node: ExpressionStmtNode) -> ExpressionStmtNode:
        """Expression statements are reachable if we're in reachable code"""
        if not self.reachable_code:
            return None
        
        return node
    
    def visit_if_stmt(self, node: IfStmtNode) -> IfStmtNode:
        """If statements don't affect reachability"""
        if not self.reachable_code:
            return None
        
        return node
    
    def visit_while_stmt(self, node: WhileStmtNode) -> WhileStmtNode:
        """While statements don't affect reachability"""
        if not self.reachable_code:
            return None
        
        return node
    
    def visit_for_stmt(self, node: ForStmtNode) -> ForStmtNode:
        """For statements don't affect reachability"""
        if not self.reachable_code:
            return None
        
        return node
    
    def visit_return_stmt(self, node: ReturnStmtNode) -> ReturnStmtNode:
        """Return statements make subsequent code unreachable"""
        if not self.reachable_code:
            return None
        
        self.reachable_code = False
        return node
    
    def visit_break_stmt(self, node: BreakStmtNode) -> BreakStmtNode:
        """Break statements make subsequent code unreachable"""
        if not self.reachable_code:
            return None
        
        self.reachable_code = False
        return node
    
    def visit_continue_stmt(self, node: ContinueStmtNode) -> ContinueStmtNode:
        """Continue statements make subsequent code unreachable"""
        if not self.reachable_code:
            return None
        
        self.reachable_code = False
        return node
    
    def visit_binary_expr(self, node: BinaryExprNode) -> BinaryExprNode:
        return node
    
    def visit_unary_expr(self, node: UnaryExprNode) -> UnaryExprNode:
        return node
    
    def visit_postfix_expr(self, node: PostfixExprNode) -> PostfixExprNode:
        return node

    def visit_assignment_expr(self, node: AssignmentExprNode) -> AssignmentExprNode:
        return node
    
    def visit_call_expr(self, node: CallExprNode) -> CallExprNode:
        return node
    
    def visit_member_expr(self, node: MemberExprNode) -> MemberExprNode:
        return node
    
    def visit_identifier_expr(self, node: IdentifierExprNode) -> IdentifierExprNode:
        return node
    
    def visit_literal_expr(self, node: LiteralExprNode) -> LiteralExprNode:
        return node

    def visit_message_decl(self, node: MessageDeclNode) -> MessageDeclNode:
        """Message declarations are always needed"""
        return node

    def visit_message_send(self, node: MessageSendNode) -> MessageSendNode:
        """Message send expressions are always needed (have side effects)"""
        optimized_payload = node.payload.accept(self)
        return MessageSendNode(node.channel, optimized_payload, node.line)

    def visit_message_recv(self, node: MessageRecvNode) -> MessageRecvNode:
        """Message receive expressions are always needed (have side effects)"""
        # Optimize timeout if present
        optimized_timeout = None
        if node.timeout:
            optimized_timeout = node.timeout.accept(self)
        return MessageRecvNode(node.channel, optimized_timeout, node.line)

    def visit_import_stmt(self, node: ImportStmtNode) -> ImportStmtNode:
        """Import statements are always needed"""
        return node
    
    def visit_array_decl(self, node: ArrayDeclNode) -> ArrayDeclNode:
        """Array declarations are always reachable"""
        return node
    
    def visit_array_literal(self, node: ArrayLiteralNode) -> ArrayLiteralNode:
        """Array literals are always reachable"""
        optimized_elements = []
        for element in node.elements:
            optimized_element = element.accept(self)
            optimized_elements.append(optimized_element)
        
        return ArrayLiteralNode(optimized_elements, node.line)
    
    def visit_array_access(self, node: ArrayAccessNode) -> ArrayAccessNode:
        """Array access is always reachable"""
        optimized_array = node.array.accept(self)
        optimized_index = node.index.accept(self)
        
        return ArrayAccessNode(optimized_array, optimized_index, node.line)

class Optimizer:
    """Main optimizer class"""
    
    def __init__(self):
        self.passes = [
            ConstantFolder(),
            DeadCodeEliminator(),
        ]
    
    def optimize(self, ast: ProgramNode) -> ProgramNode:
        """Apply optimization passes"""
        optimized_ast = ast
        
        for pass_optimizer in self.passes:
            try:
                optimized_ast = optimized_ast.accept(pass_optimizer)
            except OptimizationError as e:
                print(f"Optimization warning: {e}")
                # Continue with unoptimized version
        
        return optimized_ast
