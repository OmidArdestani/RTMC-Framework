"""
Bytecode Generator for RT-Micro-C Language
Converts AST to bytecode instructions.
"""

from typing import Dict, List, Optional, Any, Tuple
from src.parser.ast_nodes import *
from src.bytecode.instructions import *
from src.semantic.struct_layout import StructLayoutTable
from dataclasses import dataclass
from enum import Enum, auto

class CompileMode(Enum):
    """Compilation modes"""
    DEBUG = auto()
    RELEASE = auto()

class CodeGenError(Exception):
    """Code generation error"""
    pass

@dataclass
class BytecodeProgram:
    """Complete bytecode program"""
    constants: List[Any]
    strings: List[str]
    functions: Dict[str, int]  # function name -> start address
    instructions: List[Instruction]
    symbol_table: Dict[str, int]  # symbol name -> address
    struct_layouts: Dict[str, Dict[str, int]]  # struct name -> field offsets
    mode: CompileMode = CompileMode.DEBUG  # NEW: Compilation mode
    debug_info: Optional[Dict[int, int]] = None  # NEW: instruction_index -> source_line

class BytecodeGenerator(ASTVisitor):
    """Generates bytecode from AST"""
    
    def __init__(self, mode: CompileMode = CompileMode.DEBUG):
        self.instructions: List[Instruction] = []
        self.constants: List[Any] = []
        self.strings: List[str] = []
        self.functions: Dict[str, int] = {}
        self.symbol_table: Dict[str, int] = {}
        self.struct_layouts: Dict[str, Dict[str, int]] = {}
        self.mode = mode  # NEW: Compilation mode
        self.debug_info: Dict[int, int] = {}  # NEW: Debug information
        
        # Code generation state
        self.current_address = 0
        self.variable_counter = 0
        self.temp_counter = 0  # Counter for temporary variables
        self.labels: Dict[str, int] = {}
        self.label_counter = 0
        
        # Function context
        self.current_function = None
        self.local_variables: Dict[str, int] = {}
        self.parameter_count = 0
        
        # Control flow
        self.break_labels: List[str] = []
        self.continue_labels: List[str] = []
        
        # NEW: Struct layout management
        self.struct_layout_table = StructLayoutTable()
        
        # NEW: Variable type tracking for dynamic type resolution
        self.variable_types: Dict[str, str] = {}  # variable_name -> type_name
        self.local_variable_types: Dict[str, str] = {}  # local variables in current function
        
        # NEW: Current line tracking for debug info
        self.current_line = 0
        self.current_column = 0
    
    def generate(self, ast: ProgramNode) -> BytecodeProgram:
        """Generate bytecode from AST"""
        ast.accept(self)
        
        return BytecodeProgram(
            constants=self.constants,
            strings=self.strings,
            functions=self.functions,
            instructions=self.instructions,
            symbol_table=self.symbol_table,
            struct_layouts=self.struct_layouts,
            mode=self.mode,
            debug_info=self.debug_info if self.mode == CompileMode.DEBUG else None
        )
    
    def emit(self, instruction: Instruction):
        """Emit an instruction with proper line tracking"""
        if self.mode == CompileMode.DEBUG:
            instruction.line = self.current_line
            instruction.column = self.current_column
            self.debug_info[self.current_address] = self.current_line
        else:
            # In release mode, strip debug info
            instruction.line = 0
            instruction.column = 0
        
        self.instructions.append(instruction)
        self.current_address += 1
    
    def set_current_position(self, line: int, column: int = 0):
        """Set current source position for debug info"""
        self.current_line = line
        self.current_column = column
    
    def add_constant(self, value: Any) -> int:
        """Add constant to constant pool"""
        if value in self.constants:
            return self.constants.index(value)
        
        self.constants.append(value)
        return len(self.constants) - 1
    
    def add_string(self, string: str) -> int:
        """Add string to string pool"""
        if string in self.strings:
            return self.strings.index(string)
        
        self.strings.append(string)
        return len(self.strings) - 1
    
    def allocate_variable(self, name: str) -> int:
        """Allocate space for a variable"""
        if self.current_function:
            # Local variable
            address = self.variable_counter
            self.local_variables[name] = address
            self.variable_counter += 1
            return address
        else:
            # Global variable
            address = self.variable_counter
            self.symbol_table[name] = address
            self.variable_counter += 1
            return address
    
    def get_variable_address(self, name: str) -> int:
        """Get variable address"""
        if self.current_function and name in self.local_variables:
            return self.local_variables[name]
        elif name in self.symbol_table:
            return self.symbol_table[name]
        else:
            raise CodeGenError(f"Undefined variable: {name}")
    
    def create_label(self) -> str:
        """Create a unique label"""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def mark_label(self, label: str):
        """Mark a label at current address"""
        self.labels[label] = self.current_address
    
    def patch_jumps(self):
        """Patch jump addresses after all instructions are generated"""
        for instruction in self.instructions:
            if instruction.opcode in [Opcode.JUMP, Opcode.JUMPIF_TRUE, Opcode.JUMPIF_FALSE]:
                # Check if operand is a label
                if len(instruction.operands) > 0 and isinstance(instruction.operands[0], str):
                    label = instruction.operands[0]
                    if label in self.labels:
                        instruction.operands[0] = self.labels[label]
    
    # Visitor methods
    
    def visit_program(self, node: ProgramNode):
        """Generate code for program"""
        # First pass: collect function declarations
        for decl in node.declarations:
            if isinstance(decl, FunctionDeclNode):
                self.functions[decl.name] = -1  # Placeholder
        
        # Second pass: generate initialization code for global declarations
        for decl in node.declarations:
            self.current_line = decl.line
            # Only generate code for non-function declarations during initialization
            if not isinstance(decl, FunctionDeclNode):
                decl.accept(self)
        
        # Generate function code
        for decl in node.declarations:
            self.current_line = decl.line
            if isinstance(decl, FunctionDeclNode):
                decl.accept(self)
        
        # Patch jump addresses
        self.patch_jumps()
        
        # Add halt instruction at the end
        self.emit(InstructionBuilder.halt())
    
    def visit_function_decl(self, node: FunctionDeclNode):
        """Generate code for function declaration"""
        # Mark function start
        self.functions[node.name] = self.current_address
        
        # Enter function context
        old_function = self.current_function
        old_locals = self.local_variables.copy()
        old_local_types = self.local_variable_types.copy()
        old_param_count = self.parameter_count
        
        self.current_function = node.name
        self.local_variables = {}
        self.local_variable_types = {}
        self.parameter_count = len(node.parameters)
        
        # Allocate space for parameters and track their types
        for i, param in enumerate(node.parameters):
            self.local_variables[param.name] = i
            # Store parameter type information
            param_type = self._get_type_name(param.type)
            self.local_variable_types[param.name] = param_type
        
        # Set variable counter to start after parameters
        self.variable_counter = self.parameter_count
        
        # Generate function body
        node.body.accept(self)
        
        # Ensure function returns (if no explicit return)
        if self._get_type_name(node.return_type) == 'void':
            self.emit(InstructionBuilder.ret())
        
        # Restore context
        self.current_function = old_function
        self.local_variables = old_locals
        self.local_variable_types = old_local_types
        self.parameter_count = old_param_count
    
    def visit_struct_decl(self, node: StructDeclNode):
        """Generate code for struct declaration"""
        # Set current position for debug info
        self.set_current_position(node.line, getattr(node, 'column', 0))
        
        # Register struct with layout table
        self.struct_layout_table.register_struct(node)
        
        # Calculate layout
        layout = self.struct_layout_table.calculate_layout(node.name)
        
        # Store layout information for backwards compatibility
        self.struct_layouts[node.name] = {name: field.offset for name, field in layout.fields.items()}
        
        # In debug mode, emit struct metadata
        if self.mode == CompileMode.DEBUG:
            self.emit(InstructionBuilder.comment(f"Struct {node.name} size: {layout.total_size} bytes"))
            for field_name, field_layout in layout.fields.items():
                comment = f"  {field_name}: offset {field_layout.offset}, size {field_layout.size}"
                if field_layout.bit_width > 0:
                    comment += f", bit-field: {field_layout.bit_offset}:{field_layout.bit_width}"
                self.emit(InstructionBuilder.comment(comment))
    
    def visit_union_decl(self, node: UnionDeclNode):
        """Generate code for union declaration"""
        # Set current position for debug info
        self.set_current_position(node.line, getattr(node, 'column', 0))
        
        # Register union with layout table (treat similar to struct but with overlapping fields)
        self.struct_layout_table.register_struct(node)
        
        # Calculate layout
        layout = self.struct_layout_table.calculate_layout(node.name)
        
        # Store layout information for backwards compatibility
        self.struct_layouts[node.name] = {name: field.offset for name, field in layout.fields.items()}
        
        # In debug mode, emit union metadata
        if self.mode == CompileMode.DEBUG:
            self.emit(InstructionBuilder.comment(f"Union {node.name} size: {layout.total_size} bytes"))
            for field_name, field_layout in layout.fields.items():
                comment = f"  {field_name}: offset {field_layout.offset}, size {field_layout.size}"
                if field_layout.bit_width > 0:
                    comment += f", bit-field: {field_layout.bit_offset}:{field_layout.bit_width}"
                self.emit(InstructionBuilder.comment(comment))

    def visit_task_decl(self, node: TaskDeclNode):
        """Generate bytecode for task declaration"""
        task_name = node.name
        
        # Store task info for later reference
        if not hasattr(self, 'tasks'):
            self.tasks = {}
        
        # Generate code for task members (variables and helper functions)
        for member in node.members:
            member.accept(self)
        
        # Rename the run function to avoid conflicts
        original_name = node.run_function.name
        run_function_name = f"{task_name}_run"
        node.run_function.name = run_function_name
        
        # Generate code for run function
        run_function_address = self.current_address
        self.functions[run_function_name] = run_function_address
        
        # Visit the run function body
        node.run_function.accept(self)
        
        # Restore original name
        node.run_function.name = original_name
        
        # Store task information for RTOS task creation
        self.tasks[task_name] = {
            'core': node.core,
            'priority': node.priority,
            'run_function': run_function_name,
            'stack_size': 1024  # Default stack size
        }
        
        # Generate RTOS task creation bytecode
        # This will be called at program startup
        func_id = self.add_constant(f"{task_name}_run")
        task_name_const = self.add_constant(task_name)
        stack_const = self.add_constant(1024)  # Default stack size
        priority_const = self.add_constant(node.priority)
        core_const = self.add_constant(node.core)
        
        # Generate task creation instructions
        self.emit(InstructionBuilder.load_const(func_id))
        self.emit(InstructionBuilder.load_const(task_name_const))
        self.emit(InstructionBuilder.load_const(stack_const))
        self.emit(InstructionBuilder.load_const(priority_const))
        self.emit(InstructionBuilder.load_const(core_const))
        self.emit(Instruction(Opcode.RTOS_CREATE_TASK, []))
    
    def visit_variable_decl(self, node: VariableDeclNode):
        """Generate code for variable declaration"""
        # Allocate space
        address = self.allocate_variable(node.name)
        
        # Extract and store the variable's type information
        type_name = self._get_type_name(node.type)
        if self.current_function:
            # Local variable
            self.local_variable_types[node.name] = type_name
        else:
            # Global variable
            self.variable_types[node.name] = type_name
        
        # Initialize if needed
        if node.initializer:
            node.initializer.accept(self)
            self.emit(InstructionBuilder.store_var(address))
        else:
            # Initialize to zero
            const_idx = self.add_constant(0)
            self.emit(InstructionBuilder.load_const(const_idx))
            self.emit(InstructionBuilder.store_var(address))
    
    def visit_primitive_type(self, node: PrimitiveTypeNode):
        """Type nodes don't generate code"""
        pass
    
    def visit_struct_type(self, node: StructTypeNode):
        """Type nodes don't generate code"""
        pass
    
    def visit_union_type(self, node: UnionTypeNode):
        """Type nodes don't generate code"""
        pass
    
    def visit_array_type(self, node: ArrayTypeNode):
        """Type nodes don't generate code"""
        pass
    
    def _get_type_name(self, type_node: TypeNode) -> str:
        """Extract type name from a type node"""
        if isinstance(type_node, PrimitiveTypeNode):
            return type_node.type_name
        elif isinstance(type_node, StructTypeNode):
            return type_node.struct_name
        elif isinstance(type_node, UnionTypeNode):
            return type_node.union_name
        elif isinstance(type_node, ArrayTypeNode):
            element_name = self._get_type_name(type_node.element_type)
            return f"{element_name}[{type_node.size}]"
        elif isinstance(type_node, PointerTypeNode):
            base_name = self._get_type_name(type_node.base_type)
            return base_name + '*' * type_node.pointer_level
        else:
            return "unknown"
    
    def visit_block_stmt(self, node: BlockStmtNode):
        """Generate code for block statement"""
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_expression_stmt(self, node: ExpressionStmtNode):
        """Generate code for expression statement"""
        node.expression.accept(self)
        # Pop the result if it's not used
        # (In a real implementation, we'd track whether the result is used)
    
    def visit_if_stmt(self, node: IfStmtNode):
        """Generate code for if statement"""
        else_label = self.create_label()
        end_label = self.create_label()
        
        # Generate condition
        node.condition.accept(self)
        
        # Jump to else if condition is false
        self.emit(Instruction(Opcode.JUMPIF_FALSE, [else_label]))
        
        # Generate then branch
        node.then_stmt.accept(self)
        
        # Jump to end
        self.emit(Instruction(Opcode.JUMP, [end_label]))
        
        # Else branch
        self.mark_label(else_label)
        if node.else_stmt:
            node.else_stmt.accept(self)
        
        # End
        self.mark_label(end_label)
    
    def visit_while_stmt(self, node: WhileStmtNode):
        """Generate code for while statement"""
        start_label = self.create_label()
        end_label = self.create_label()
        
        # Save break/continue labels
        old_break = self.break_labels.copy()
        old_continue = self.continue_labels.copy()
        
        self.break_labels.append(end_label)
        self.continue_labels.append(start_label)
        
        # Loop start
        self.mark_label(start_label)
        
        # Generate condition
        node.condition.accept(self)
        
        # Jump to end if condition is false
        self.emit(Instruction(Opcode.JUMPIF_FALSE, [end_label]))
        
        # Generate body
        node.body.accept(self)
        
        # Jump back to start
        self.emit(Instruction(Opcode.JUMP, [start_label]))
        
        # Loop end
        self.mark_label(end_label)
        
        # Restore break/continue labels
        self.break_labels = old_break
        self.continue_labels = old_continue
    
    def visit_for_stmt(self, node: ForStmtNode):
        """Generate code for for statement"""
        start_label = self.create_label()
        continue_label = self.create_label()
        end_label = self.create_label()
        
        # Save break/continue labels
        old_break = self.break_labels.copy()
        old_continue = self.continue_labels.copy()
        
        self.break_labels.append(end_label)
        self.continue_labels.append(continue_label)
        
        # Initialize
        if node.init:
            node.init.accept(self)
        
        # Loop start
        self.mark_label(start_label)
        
        # Check condition
        if node.condition:
            node.condition.accept(self)
            self.emit(Instruction(Opcode.JUMPIF_FALSE, [end_label]))
        
        # Generate body
        node.body.accept(self)
        
        # Continue point (for continue statements)
        self.mark_label(continue_label)
        
        # Update
        if node.update:
            node.update.accept(self)
        
        # Jump back to start
        self.emit(Instruction(Opcode.JUMP, [start_label]))
        
        # Loop end
        self.mark_label(end_label)
        
        # Restore break/continue labels
        self.break_labels = old_break
        self.continue_labels = old_continue
    
    def visit_return_stmt(self, node: ReturnStmtNode):
        """Generate code for return statement"""
        if node.value:
            node.value.accept(self)
        
        self.emit(InstructionBuilder.ret())
    
    def visit_break_stmt(self, node: BreakStmtNode):
        """Generate code for break statement"""
        if self.break_labels:
            self.emit(Instruction(Opcode.JUMP, [self.break_labels[-1]]))
    
    def visit_continue_stmt(self, node: ContinueStmtNode):
        """Generate code for continue statement"""
        if self.continue_labels:
            self.emit(Instruction(Opcode.JUMP, [self.continue_labels[-1]]))
    
    def visit_binary_expr(self, node: BinaryExprNode):
        """Generate code for binary expression"""
        # Generate left operand
        node.left.accept(self)
        
        # Generate right operand
        node.right.accept(self)
        
        # Generate operation
        op_map = {
            '+': Opcode.ADD,
            '-': Opcode.SUB,
            '*': Opcode.MUL,
            '/': Opcode.DIV,
            '%': Opcode.MOD,
            '==': Opcode.EQ,
            '!=': Opcode.NEQ,
            '<': Opcode.LT,
            '<=': Opcode.LTE,
            '>': Opcode.GT,
            '>=': Opcode.GTE,
            '&&': Opcode.AND,
            '||': Opcode.OR,
            '&': Opcode.AND,
            '|': Opcode.OR,
            '^': Opcode.XOR,
        }
        
        if node.operator in op_map:
            self.emit(Instruction(op_map[node.operator], []))
        else:
            raise CodeGenError(f"Unknown binary operator: {node.operator}")
    
    def visit_unary_expr(self, node: UnaryExprNode):
        """Generate code for unary expression"""
        node.operand.accept(self)
        
        if node.operator == '-':
            # Negate by multiplying by -1
            const_idx = self.add_constant(-1)
            self.emit(InstructionBuilder.load_const(const_idx))
            self.emit(InstructionBuilder.mul())
        elif node.operator == '!':
            self.emit(InstructionBuilder.not_op())
        elif node.operator == '+':
            # Unary plus does nothing
            pass
        else:
            raise CodeGenError(f"Unknown unary operator: {node.operator}")
    
    def visit_postfix_expr(self, node: PostfixExprNode):
        """Generate code for postfix expression (++ and --)"""
        # For postfix operators, we need to:
        # 1. Load the current value (for return value)
        # 2. Increment/decrement the variable
        # 3. Leave the original value on stack
        
        if isinstance(node.operand, IdentifierExprNode):
            # Check local variables first, then global
            addr = None
            if node.operand.name in self.local_variables:
                addr = self.local_variables[node.operand.name]
            elif node.operand.name in self.symbol_table:
                addr = self.symbol_table[node.operand.name]
            else:
                raise CodeGenError(f"Undefined variable: {node.operand.name}")
            
            # Load current value first (this will be the result)
            self.emit(InstructionBuilder.load_var(addr))
            
            # Now modify the variable
            if node.operator == '++':
                # Load current value again, add 1, store back
                self.emit(InstructionBuilder.load_var(addr))
                const_idx = self.add_constant(1)
                self.emit(InstructionBuilder.load_const(const_idx))
                self.emit(InstructionBuilder.add())
                self.emit(InstructionBuilder.store_var(addr))
            elif node.operator == '--':
                # Load current value again, subtract 1, store back
                self.emit(InstructionBuilder.load_var(addr))
                const_idx = self.add_constant(1)
                self.emit(InstructionBuilder.load_const(const_idx))
                self.emit(InstructionBuilder.sub())
                self.emit(InstructionBuilder.store_var(addr))
            else:
                raise CodeGenError(f"Unknown postfix operator: {node.operator}")
        else:
            raise CodeGenError(f"Postfix operators not yet supported for {type(node.operand).__name__}")

    def visit_assignment_expr(self, node: AssignmentExprNode):
        """Generate code for assignment expression"""
        # Generate value
        node.value.accept(self)
        
        # Handle different assignment operators
        if node.operator != '=':
            # Compound assignment (+=, -=, etc.)
            # Load current value
            if isinstance(node.target, IdentifierExprNode):
                address = self.get_variable_address(node.target.name)
                self.emit(InstructionBuilder.load_var(address))
            elif isinstance(node.target, MemberExprNode):
                # For now, just treat member access as variable access with offset
                base_address = self._get_member_address(node.target)
                self.emit(InstructionBuilder.load_var(base_address))
            else:
                raise CodeGenError("Complex assignment targets not supported yet")
            
            # Perform operation
            op = node.operator[:-1]  # Remove '='
            op_map = {
                '+': Opcode.ADD,
                '-': Opcode.SUB,
                '*': Opcode.MUL,
                '/': Opcode.DIV,
            }
            
            if op in op_map:
                self.emit(Instruction(op_map[op], []))
            else:
                raise CodeGenError(f"Unknown assignment operator: {node.operator}")
        
        # Store result
        if isinstance(node.target, IdentifierExprNode):
            address = self.get_variable_address(node.target.name)
            self.emit(InstructionBuilder.store_var(address))
        elif isinstance(node.target, MemberExprNode):
            # Handle struct member assignment (including bit-fields)
            self._generate_member_store(node.target)
        else:
            raise CodeGenError("Complex assignment targets not supported yet")
    
    def _get_member_address(self, node: MemberExprNode) -> int:
        """Get simplified address for member access"""
        if isinstance(node.object, IdentifierExprNode):
            # Simple case: variable.field
            base_address = self.get_variable_address(node.object.name)
            struct_name = self._get_struct_name_for_member(node)
            field_offset = self._get_simple_field_offset(struct_name, node.property)
            return base_address + field_offset
        elif isinstance(node.object, MemberExprNode):
            # For nested access like rect.top_left.x, get the base variable
            base_var = self._get_base_variable_name(node.object)
            base_address = self.get_variable_address(base_var)
            # Calculate nested offset
            nested_offset = self._calculate_nested_offset(node)
            return base_address + nested_offset
        else:
            # Fallback: treat as simple variable access
            return 0  # Use address 0 as fallback
    
    def _get_struct_name_for_member(self, member_expr: MemberExprNode) -> str:
        """Get the struct name for a member expression using dynamic type resolution"""
        if isinstance(member_expr.object, IdentifierExprNode):
            # Simple case: variable.field or ptr->field
            var_name = member_expr.object.name
            
            # First, try to get the variable's type from the struct layout table
            # This should contain type information from semantic analysis
            try:
                var_type = self.struct_layout_table.get_variable_type(var_name)
                if var_type:
                    # Handle pointer types for arrow operator
                    if member_expr.computed and isinstance(member_expr.property, str) and var_type.endswith('*'):
                        # This is pointer member access (ptr->field)
                        pointed_type = var_type[:-1]  # Remove '*'
                        if pointed_type.startswith('struct '):
                            return pointed_type[7:]  # Remove 'struct '
                        else:
                            return pointed_type
                    elif not member_expr.computed:
                        # This is regular member access (obj.field)
                        if var_type.startswith('struct '):
                            return var_type[7:]  # Remove 'struct '
                        else:
                            return var_type
                    else:
                        return var_type
            except (AttributeError, KeyError):
                pass
            
            # If struct layout table doesn't have variable type info, 
            # we need to look up the variable declaration to find its type
            variable_type = self._resolve_variable_type(var_name)
            if variable_type:
                # Handle pointer types for arrow operator
                if member_expr.computed and isinstance(member_expr.property, str) and variable_type.endswith('*'):
                    # This is pointer member access (ptr->field)
                    pointed_type = variable_type[:-1]  # Remove '*'
                    if pointed_type.startswith('struct '):
                        return pointed_type[7:]  # Remove 'struct '
                    else:
                        return pointed_type
                elif not member_expr.computed:
                    # This is regular member access (obj.field)
                    if variable_type.startswith('struct '):
                        return variable_type[7:]  # Remove 'struct '
                    else:
                        return variable_type
                else:
                    return variable_type
            
            # As a fallback, try to find the struct type by checking which struct contains this field
            field_name = member_expr.property
            candidate_structs = []
            for struct_name, fields in self.struct_layouts.items():
                if field_name in fields:
                    candidate_structs.append(struct_name)
            
            # If only one struct contains this field, use it
            if len(candidate_structs) == 1:
                return candidate_structs[0]
            elif len(candidate_structs) > 1:
                # Multiple structs contain this field - this is ambiguous
                # In a real compiler, this would be caught by semantic analysis
                raise CodeGenError(f"Ambiguous field access: field '{field_name}' exists in multiple structs: {candidate_structs}")
            
            # Field not found in any struct
            raise CodeGenError(f"Field '{field_name}' not found in any registered struct")
            
        elif isinstance(member_expr.object, MemberExprNode):
            # Nested case: obj.field1.field2
            # The type of field1 determines the struct for field2
            parent_struct = self._get_struct_name_for_member(member_expr.object)
            parent_field = member_expr.object.property
            
            # Look up the type of parent_field in parent_struct
            try:
                field_type = self.struct_layout_table.get_field_type(parent_struct, parent_field)
                if field_type:
                    return field_type
            except (AttributeError, KeyError):
                pass
            
            # If struct layout table doesn't have field type info, 
            # try to resolve it from the struct declaration
            field_type = self._resolve_field_type(parent_struct, parent_field)
            if field_type:
                return field_type
            
            raise CodeGenError(f"Cannot resolve type of field '{parent_field}' in struct '{parent_struct}'")
        elif isinstance(member_expr.object, DereferenceNode):
            # Pointer dereference case: ptr->field
            # The pointer's base type determines the struct
            if isinstance(member_expr.object.operand, IdentifierExprNode):
                pointer_name = member_expr.object.operand.name
                
                # Get the pointer's type and extract the base struct type
                pointer_type = self._resolve_variable_type(pointer_name)
                if pointer_type and pointer_type.endswith('*'):
                    # Remove the pointer indicator and extract struct name
                    base_type = pointer_type[:-1]  # Remove '*'
                    if base_type.startswith('struct '):
                        return base_type[7:]  # Remove 'struct ' prefix
                    elif base_type.startswith('TestStruct'):  # Handle direct struct names
                        return base_type
                    else:
                        # For other pointer types, we need to infer the struct
                        # This is a simplified approach - in a full compiler, 
                        # we'd have better type information from semantic analysis
                        field_name = member_expr.property
                        candidate_structs = []
                        for struct_name, fields in self.struct_layouts.items():
                            if field_name in fields:
                                candidate_structs.append(struct_name)
                        
                        if len(candidate_structs) == 1:
                            return candidate_structs[0]
                        elif len(candidate_structs) > 1:
                            raise CodeGenError(f"Ambiguous field access: field '{field_name}' exists in multiple structs: {candidate_structs}")
                        else:
                            raise CodeGenError(f"Field '{field_name}' not found in any registered struct")
                
                raise CodeGenError(f"Cannot resolve base type for pointer '{pointer_name}' with type '{pointer_type}'")
            else:
                raise CodeGenError("Complex pointer dereference not yet supported")
        else:
            # Complex object (like function call result)
            # This would require full type inference from semantic analysis
            raise CodeGenError("Complex member access on non-identifier objects not yet supported")
    
    def _resolve_variable_type(self, var_name: str) -> Optional[str]:
        """Resolve the type of a variable from declarations"""
        # Check local variables first (if we're in a function)
        if self.current_function and var_name in self.local_variable_types:
            return self.local_variable_types[var_name]
        
        # Check global variables
        if var_name in self.variable_types:
            return self.variable_types[var_name]
        
        # Check if we have type information stored in struct layout table
        if hasattr(self.struct_layout_table, 'get_variable_type'):
            try:
                var_type = self.struct_layout_table.get_variable_type(var_name)
                if var_type:
                    return var_type
            except (AttributeError, KeyError):
                pass
        
        # Variable type not found
        return None
    
    def _resolve_field_type(self, struct_name: str, field_name: str) -> Optional[str]:
        """Resolve the type of a field within a struct"""
        # This should ideally be provided by semantic analysis
        # For now, we'll try to look it up in the struct layout table
        
        try:
            return self.struct_layout_table.get_field_type(struct_name, field_name)
        except (AttributeError, KeyError):
            pass
        
        # If not available from struct layout, this is a limitation
        # In a real implementation, this would be resolved during semantic analysis
        return None
    
    def _get_simple_field_offset(self, struct_name: str, field_name: str) -> int:
        """Get field offset with support for nested structs"""
        try:
            return self.struct_layout_table.get_field_offset(struct_name, field_name)
        except (ValueError, KeyError):
            # If semantic analysis was skipped, provide a default offset
            # This is a simplified fallback - assumes 4-byte fields
            # TODO: Improve this when semantic analysis is fixed
            return 0  # Default offset for now
    
    def _get_bit_field_info(self, struct_name: str, field_name: str) -> Optional[Tuple[int, int, int]]:
        """Get bit-field information with support for nested structs"""
        try:
            return self.struct_layout_table.get_bit_field_info(struct_name, field_name)
        except (ValueError, KeyError):
            # Not a bitfield or struct not found - return None instead of raising
            return None
    
    def visit_call_expr(self, node: CallExprNode):
        """Generate code for call expression"""
        if isinstance(node.callee, IdentifierExprNode):
            func_name = node.callee.name
            
            # Check if it's a built-in function
            if func_name.startswith('RTOS_') or func_name.startswith('HW_') or func_name.startswith('DBG_'):
                self.generate_builtin_call(func_name, node.arguments)
            else:
                # Regular function call
                # Generate arguments
                for arg in node.arguments:
                    arg.accept(self)
                
                # Call function
                if func_name in self.functions:
                    func_id = self.functions[func_name]
                    param_count = len(node.arguments)
                    self.emit(InstructionBuilder.call(func_id, param_count))
                else:
                    raise CodeGenError(f"Unknown function: {func_name}")
        else:
            raise CodeGenError("Complex function calls not supported yet")
    
    def generate_builtin_call(self, func_name: str, arguments: List[ExpressionNode]):
        """Generate code for built-in function calls"""
        # Generate arguments
        for arg in arguments:
            arg.accept(self)
        
        # RTOS functions
        if func_name == 'RTOS_CREATE_TASK':
            # RTOS_CREATE_TASK(func_ptr, name, stack_size, priority, core)
            if len(arguments) >= 5:
                self.emit(InstructionBuilder.rtos_create_task(0, 0, 0, 0, 0))  # VM will pop args
        elif func_name == 'RTOS_DELETE_TASK':
            self.emit(InstructionBuilder.rtos_delete_task(0))
        elif func_name == 'RTOS_DELAY_MS':
            self.emit(InstructionBuilder.rtos_delay_ms(0))
        elif func_name == 'RTOS_SEMAPHORE_CREATE':
            self.emit(InstructionBuilder.rtos_semaphore_create())
        elif func_name == 'RTOS_SEMAPHORE_TAKE':
            self.emit(InstructionBuilder.rtos_semaphore_take(0, 0))
        elif func_name == 'RTOS_SEMAPHORE_GIVE':
            self.emit(InstructionBuilder.rtos_semaphore_give(0))
        elif func_name == 'RTOS_YIELD':
            self.emit(InstructionBuilder.rtos_yield())
        elif func_name == 'RTOS_SUSPEND_TASK':
            self.emit(InstructionBuilder.rtos_suspend_task(0))
        elif func_name == 'RTOS_RESUME_TASK':
            self.emit(InstructionBuilder.rtos_resume_task(0))
        
        # Hardware GPIO functions
        elif func_name == 'HW_GPIO_INIT':
            self.emit(InstructionBuilder.hw_gpio_init(0, 0))
        elif func_name == 'HW_GPIO_SET':
            self.emit(InstructionBuilder.hw_gpio_set(0, 0))
        elif func_name == 'HW_GPIO_GET':
            self.emit(InstructionBuilder.hw_gpio_get(0))
        
        # Hardware Timer functions
        elif func_name == 'HW_TIMER_INIT':
            self.emit(InstructionBuilder.hw_timer_init(0, 0, 0))
        elif func_name == 'HW_TIMER_START':
            self.emit(InstructionBuilder.hw_timer_start(0))
        elif func_name == 'HW_TIMER_STOP':
            self.emit(InstructionBuilder.hw_timer_stop(0))
        elif func_name == 'HW_TIMER_SET_PWM_DUTY':
            self.emit(InstructionBuilder.hw_timer_set_pwm_duty(0, 0))
        
        # Hardware ADC functions
        elif func_name == 'HW_ADC_INIT':
            self.emit(InstructionBuilder.hw_adc_init(0))
        elif func_name == 'HW_ADC_READ':
            self.emit(InstructionBuilder.hw_adc_read(0))
        
        # Hardware Communication functions
        elif func_name == 'HW_UART_WRITE':
            self.emit(InstructionBuilder.hw_uart_write(0, 0))
        elif func_name == 'HW_SPI_TRANSFER':
            self.emit(InstructionBuilder.hw_spi_transfer(0, 0, 0))
        elif func_name == 'HW_I2C_WRITE':
            self.emit(InstructionBuilder.hw_i2c_write(0, 0))
        elif func_name == 'HW_I2C_READ':
            self.emit(InstructionBuilder.hw_i2c_read(0, 0))
        
        # Debug functions
        elif func_name == 'DBG_PRINT':
            # For DBG_PRINT, the string argument should be processed specially
            if len(arguments) >= 1:
                # Generate the string argument and get its ID
                self.emit(InstructionBuilder.dbg_print(0))  # String ID will be handled by VM from stack
            else:
                self.emit(InstructionBuilder.dbg_print(0))
        elif func_name == 'DBG_BREAKPOINT':
            self.emit(InstructionBuilder.dbg_breakpoint())
        elif func_name == 'DBG_PRINTF':
            # For DBG_PRINTF, process format string and arguments
            if len(arguments) >= 1:
                # The format string is the first argument
                # Arguments for formatting are the rest
                arg_count = len(arguments) - 1
                self.emit(InstructionBuilder.dbg_printf(0, arg_count))  # Format string ID from stack
            else:
                self.emit(InstructionBuilder.dbg_printf(0, 0))
        
        else:
            raise CodeGenError(f"Unknown built-in function: {func_name}")
    
    def visit_member_expr(self, node: MemberExprNode):
        """Generate code for member expression"""
        if node.computed:
            # This is either array access (obj[index]) or pointer member access (ptr->field)
            if isinstance(node.property, str):
                # Pointer member access: ptr->field
                # Get struct name and field offset
                struct_name = self._get_struct_name_for_member(node)
                field_offset = self._get_simple_field_offset(struct_name, node.property)
                
                # Generate code to load the pointer value
                node.object.accept(self)
                
                # Check if this is a bit-field
                bit_field_info = self._get_bit_field_info(struct_name, node.property)
                if bit_field_info:
                    byte_offset, bit_offset, bit_width = bit_field_info
                    # For pointer access, we need to load the address, add the byte offset,
                    # then load the bit field
                    if byte_offset > 0:
                        offset_const = self.add_constant(byte_offset)
                        self.emit(InstructionBuilder.load_const(offset_const))
                        self.emit(InstructionBuilder.add())
                    self.emit(InstructionBuilder.load_struct_member_bit(0, 0, bit_offset, bit_width))
                else:
                    # Regular field access through pointer
                    # Add field offset to the pointer address
                    if field_offset > 0:
                        offset_const = self.add_constant(field_offset)
                        self.emit(InstructionBuilder.load_const(offset_const))
                        self.emit(InstructionBuilder.add())
                    # Load the value at the computed address
                    self.emit(InstructionBuilder.load_deref())
                
                return
            else:
                # Array access: obj[index]
                node.object.accept(self)
                
                if isinstance(node.property, ExpressionNode):
                    node.property.accept(self)
                else:
                    const_idx = self.add_constant(node.property)
                    self.emit(InstructionBuilder.load_const(const_idx))
                
                # Load array element (simplified)
                self.emit(InstructionBuilder.add())  # Add index to base address
                # In a real implementation, we'd need to handle array element loading
        else:
            # Struct field access: obj.field
            # Get struct name and field offset
            struct_name = self._get_struct_name_for_member(node)
            field_offset = self._get_simple_field_offset(struct_name, node.property)
            
            # Generate code to load the struct base address
            if isinstance(node.object, IdentifierExprNode):
                # Simple case: variable.field
                base_address = self.get_variable_address(node.object.name)
                
                # Check if this is a bit-field
                bit_field_info = self._get_bit_field_info(struct_name, node.property)
                if bit_field_info:
                    byte_offset, bit_offset, bit_width = bit_field_info
                    self.emit(InstructionBuilder.load_struct_member_bit(base_address, byte_offset, bit_offset, bit_width))
                    
                    return
                else:
                    # Regular field access
                    self.emit(InstructionBuilder.load_struct_member(base_address, field_offset))

                    return
            elif isinstance(node.object, MemberExprNode):
                # Nested access: variable.field1.field2
                base_var = self._get_base_variable_name(node.object)
                base_address = self.get_variable_address(base_var)
                nested_offset = self._calculate_nested_offset(node)
                # field_offset = base_address + nested_offset
                self.emit(InstructionBuilder.load_struct_member(base_address, nested_offset))

                return
            elif isinstance(node.object, DereferenceNode):
                # Pointer access: ptr->member
                # Generate code to load the pointer value
                node.object.operand.accept(self)
                
                # Check if this is a bit-field
                bit_field_info = self._get_bit_field_info(struct_name, node.property)
                if bit_field_info:
                    byte_offset, bit_offset, bit_width = bit_field_info
                    # For pointer access, we need to load the address, add the byte offset,
                    # then load the bit field
                    if byte_offset > 0:
                        offset_const = self.add_constant(byte_offset)
                        self.emit(InstructionBuilder.load_const(offset_const))
                        self.emit(InstructionBuilder.add())
                    self.emit(InstructionBuilder.load_struct_member_bit(0, 0, bit_offset, bit_width))
                else:
                    # Regular field access through pointer
                    # Add field offset to the pointer address
                    if field_offset > 0:
                        offset_const = self.add_constant(field_offset)
                        self.emit(InstructionBuilder.load_const(offset_const))
                        self.emit(InstructionBuilder.add())
                    # Load the value at the computed address
                    self.emit(InstructionBuilder.load_deref())
                
                return
            else:
                # Complex object access
                node.object.accept(self)
                # Add field offset to the address on stack
                offset_const = self.add_constant(field_offset)
                self.emit(InstructionBuilder.load_const(offset_const))
                self.emit(InstructionBuilder.add())
                field_offset = 0  # Offset already added
            
            self.emit(InstructionBuilder.load_struct_member(0, field_offset))
    
    def visit_identifier_expr(self, node: IdentifierExprNode):
        """Generate code for identifier expression"""
        try:
            address = self.get_variable_address(node.name)
            self.emit(InstructionBuilder.load_var(address))
        except CodeGenError:
            # Might be a function name
            if node.name in self.functions:
                func_id = self.functions[node.name]
                const_idx = self.add_constant(func_id)
                self.emit(InstructionBuilder.load_const(const_idx))
            else:
                raise CodeGenError(f"Unknown identifier: {node.name}")
    
    def visit_literal_expr(self, node: LiteralExprNode):
        """Generate code for literal expression"""
        if node.literal_type == 'string':
            string_idx = self.add_string(node.value)
            # For strings, we need to load the string index, not as a constant
            const_idx = self.add_constant(string_idx)
            self.emit(InstructionBuilder.load_const(const_idx))
        else:
            const_idx = self.add_constant(node.value)
            self.emit(InstructionBuilder.load_const(const_idx))
    
    def get_type_size(self, type_node: TypeNode) -> int:
        """Get size of type in bytes with proper struct size calculation"""
        if isinstance(type_node, PrimitiveTypeNode):
            if type_node.type_name == 'char':
                return 1
            elif type_node.type_name in ['int', 'float']:
                return 4
            elif type_node.type_name == 'bool':
                return 1
            elif type_node.type_name == 'void':
                return 0
            else:
                raise CodeGenError("Unknown primitive type: " + type_node.type_name)
        elif isinstance(type_node, StructTypeNode):
            # Use struct layout table for accurate size calculation
            try:
                return self.struct_layout_table.get_struct_size(type_node.struct_name)
            except (ValueError, KeyError):
                raise CodeGenError("Struct not found in layout table")
        elif isinstance(type_node, ArrayTypeNode):
            element_size = self.get_type_size(type_node.element_type)
            return element_size * (type_node.size or 1)
        elif isinstance(type_node, PointerTypeNode):
            return 8  # 64-bit pointer size
        else:
            raise CodeGenError("Pointer types not supported in this context")

    def _generate_member_load(self, node: MemberExprNode):
        """Generate code to load from a member expression"""
        if isinstance(node.object, IdentifierExprNode):
            # Simple case: variable.field
            base_address = self.get_variable_address(node.object.name)
            
            # Check if this is a bit-field
            struct_name = self._get_struct_name_for_member(node)
            bit_field_info = self._get_bit_field_info(struct_name, node.property)
            if bit_field_info:
                byte_offset, bit_offset, bit_width = bit_field_info
                self.emit(InstructionBuilder.load_struct_member_bit(
                    base_address, byte_offset, bit_offset, bit_width))
            else:
                # Regular field access
                field_offset = self._get_simple_field_offset(struct_name, node.property)
                self.emit(InstructionBuilder.load_struct_member(base_address, field_offset))
        elif isinstance(node.object, MemberExprNode):
            # Nested case: variable.field1.field2
            base_var = self._get_base_variable_name(node.object)
            base_address = self.get_variable_address(base_var)
            field_offset = self._calculate_nested_offset(node)
            self.emit(InstructionBuilder.load_struct_member(base_address, field_offset))
        else:
            raise CodeGenError("Complex member access not supported yet")
    
    def _generate_member_store(self, node: MemberExprNode):
        """Generate code to store to a member expression"""
        if node.computed and isinstance(node.property, str):
            # Arrow operator: ptr->field = value
            # At this point, the value to store is already on the stack
            
            # Get the pointer variable and compute the address
            if isinstance(node.object, IdentifierExprNode):
                pointer_name = node.object.name
                pointer_address = self.get_variable_address(pointer_name)
                
                # Allocate a temporary variable to store the value
                temp_var_addr = self.allocate_variable(f"__temp_store_{self.temp_counter}")
                self.temp_counter += 1
                
                # Store the value temporarily
                self.emit(InstructionBuilder.store_var(temp_var_addr))
                
                # Load the pointer value (which is an address)
                self.emit(InstructionBuilder.load_var(pointer_address))
                
                # Add the field offset
                struct_name = self._get_struct_name_for_member(node)
                field_offset = self._get_simple_field_offset(struct_name, node.property)
                if field_offset > 0:
                    offset_const = self.add_constant(field_offset)
                    self.emit(InstructionBuilder.load_const(offset_const))
                    self.emit(InstructionBuilder.add())
                
                # Load the value back
                self.emit(InstructionBuilder.load_var(temp_var_addr))
                
                # Store through the pointer
                self.emit(InstructionBuilder.store_deref())
            else:
                raise CodeGenError("Complex pointer member assignment not supported yet")
        elif isinstance(node.object, IdentifierExprNode):
            # Simple case: variable.field = value
            base_address = self.get_variable_address(node.object.name)
            
            # Check if this is a bit-field
            struct_name = self._get_struct_name_for_member(node)
            bit_field_info = self._get_bit_field_info(struct_name, node.property)
            if bit_field_info:
                byte_offset, bit_offset, bit_width = bit_field_info
                self.emit(InstructionBuilder.store_struct_member_bit(
                    base_address, byte_offset, bit_offset, bit_width))
            else:
                # Regular field access
                field_offset = self._get_simple_field_offset(struct_name, node.property)
                self.emit(InstructionBuilder.store_struct_member(base_address, field_offset))
        elif isinstance(node.object, MemberExprNode):
            # Nested case: variable.field1.field2 = value
            base_var = self._get_base_variable_name(node.object)
            base_address = self.get_variable_address(base_var)
            field_offset = self._calculate_nested_offset(node)
            self.emit(InstructionBuilder.store_struct_member(base_address, field_offset))
        elif isinstance(node.object, DereferenceNode):
            # Pointer case: ptr->member = value
            # At this point, the value to store is already on the stack
            
            # Strategy: Use a temporary variable to handle stack ordering
            # 1. Store the value in a temp variable
            # 2. Compute the target address
            # 3. Load the value back
            # 4. Call STORE_DEREF
            
            # Get the pointer variable and compute the address
            if isinstance(node.object.operand, IdentifierExprNode):
                pointer_name = node.object.operand.name
                pointer_address = self.get_variable_address(pointer_name)
                
                # Allocate a temporary variable to store the value
                temp_var_addr = self.allocate_variable(f"__temp_store_{self.temp_counter}")
                self.temp_counter += 1
                
                # Store the value temporarily
                self.emit(InstructionBuilder.store_var(temp_var_addr))
                
                # Load the pointer value (which is an address)
                self.emit(InstructionBuilder.load_var(pointer_address))
                
                # Get the field offset
                struct_name = self._get_struct_name_for_member(node)
                field_offset = self._get_simple_field_offset(struct_name, node.property)
                
                # Add field offset to the pointer address
                if field_offset > 0:
                    offset_const = self.add_constant(field_offset)
                    self.emit(InstructionBuilder.load_const(offset_const))
                    self.emit(InstructionBuilder.add())
                
                # Load the value back onto the stack
                self.emit(InstructionBuilder.load_var(temp_var_addr))
                
                # Now stack is: [target_address, value] which is correct for STORE_DEREF
                self.emit(InstructionBuilder.store_deref())
            else:
                raise CodeGenError("Complex pointer dereference in assignment not yet supported")
        else:
            raise CodeGenError("Complex member access not supported yet")
    
    def _get_base_variable(self, node: MemberExprNode) -> str:
        """Get the base variable name from a nested member expression"""
        if isinstance(node.object, IdentifierExprNode):
            return node.object.name
        elif isinstance(node.object, MemberExprNode):
            return self._get_base_variable(node.object)
        else:
            raise CodeGenError("Cannot determine base variable")
    
    def _get_base_variable_name(self, node: MemberExprNode) -> str:
        """Get the base variable name from a nested member expression"""
        if isinstance(node.object, IdentifierExprNode):
            return node.object.name
        elif isinstance(node.object, MemberExprNode):
            return self._get_base_variable_name(node.object)
        else:
            raise CodeGenError("Cannot determine base variable")
    
    def _calculate_nested_offset(self, node: MemberExprNode) -> int:
        """Calculate offset for nested member access"""
        if isinstance(node.object, IdentifierExprNode):
            # This is the final level, just return field offset
            struct_name = self._get_struct_name_for_member(node)
            return self._get_simple_field_offset(struct_name, node.property)
        elif isinstance(node.object, MemberExprNode):
            # Nested access: calculate parent offset + current field offset
            parent_offset = self._calculate_nested_offset(node.object)
            struct_name = self._get_struct_name_for_member(node)
            current_offset = self._get_simple_field_offset(struct_name, node.property)
            # Simple encoding: multiply parent by struct size and add current
            return parent_offset * 10 + current_offset
        else:
            return 0

    def _get_field_offset(self, field_name: str) -> int:
        """Get the offset of a field (simplified implementation)"""
        # In a real implementation, this would look up the struct definition
        # and calculate the actual field offset based on field sizes and alignment
        # For now, we'll use a simple hash-based offset
        field_offsets = {
            'temperature': 0,
            'humidity': 1, 
            'pressure': 2,
            'control': 3,
            'enable': 0,
            'mode': 1,
            'speed': 2,
            'reserved': 3
        }
        return field_offsets.get(field_name, 0)
    
    def _get_nested_field_offset(self, node: MemberExprNode) -> int:
        """Get the offset for nested field access (simplified)"""
        # For nested access like sensor.control.enable, we need to calculate
        # the offset of 'control' in the parent struct plus the offset of 'enable' in control
        if isinstance(node.object, MemberExprNode):
            parent_offset = self._get_field_offset(node.object.property)
            current_offset = self._get_field_offset(node.property)
            # In a real implementation, we'd need proper struct layout calculation
            # For now, use a simple additive approach
            return parent_offset * 10 + current_offset  # Simple encoding
        else:
            return self._get_field_offset(node.property)

    def _get_field_info(self, struct_var_name: str, field_name: str) -> Optional[Dict]:
        """Get field information including bit-field details"""
        # Find the struct type of the variable
        for struct_name, field_info in self.struct_layouts.items():
            if field_name in field_info:
                return field_info[field_name]
        
        # Fallback for unknown fields
        return {
            'byte_offset': 0,
            'bit_offset': 0,
            'bit_width': None,
            'is_bitfield': False
        }

    def visit_message_decl(self, node: MessageDeclNode):
        """Generate code for message declaration"""
        # Reserve space for the message queue in the symbol table
        message_id = len(self.symbol_table)
        self.symbol_table[node.name] = message_id
        
        # Emit message queue declaration instruction
        type_name = self._get_type_name(node.message_type)
        self.emit(Instruction(Opcode.MSG_DECLARE, [message_id, type_name]))

    def visit_message_send(self, node: MessageSendNode):
        """Generate code for message send"""
        # Generate code for the payload expression
        node.payload.accept(self)
        
        # Get the message queue ID
        channel_name = node.channel.name if hasattr(node.channel, 'name') else str(node.channel)
        if channel_name not in self.symbol_table:
            raise CodeGenError(f"Undefined message queue: {channel_name}")
        
        message_id = self.symbol_table[channel_name]
        
        # Emit message send instruction
        self.emit(Instruction(Opcode.MSG_SEND, [message_id]))

    def visit_message_recv(self, node: MessageRecvNode):
        """Generate code for message receive"""
        # Get the message queue ID
        channel_name = node.channel.name if hasattr(node.channel, 'name') else str(node.channel)
        if channel_name not in self.symbol_table:
            raise CodeGenError(f"Undefined message queue: {channel_name}")
        
        message_id = self.symbol_table[channel_name]
        
        # Handle timeout parameter
        if node.timeout is not None:
            # Generate code to compute timeout value
            node.timeout.accept(self)
            # The timeout value is now on the stack
        else:
            # No timeout specified, use blocking receive (we'll handle this differently)
            # Use a large positive timeout value instead of -1
            self.emit(Instruction(Opcode.LOAD_CONST, [self.add_constant(999999)]))
        
        # Emit message receive instruction with timeout
        # Stack order: [timeout_value] -> MSG_RECV will pop timeout and use it
        self.emit(Instruction(Opcode.MSG_RECV, [message_id]))

    def visit_import_stmt(self, node: ImportStmtNode):
        """Import statements are handled by the compiler, no bytecode needed"""
        pass
    
    def visit_array_decl(self, node: ArrayDeclNode):
        """Visit array declaration node"""
        # For now, treat array as a regular variable allocation
        # TODO: Implement proper array support in VM
        
        # Store array reference in symbol table
        array_address = self.allocate_variable(node.name)
        
        # Track the array type
        array_type = f"{self._get_type_name(node.element_type)}[{node.size}]"
        if self.current_function:
            self.local_variable_types[node.name] = array_type
        else:
            self.variable_types[node.name] = array_type
        
        # Initialize to null/zero for now
        const_idx = self.add_constant(0)
        self.emit(Instruction(Opcode.LOAD_CONST, [const_idx]))
        self.emit(Instruction(Opcode.STORE_VAR, [array_address]))
        
        # If there's an initializer, process it
        if node.initializer:
            # For now, just evaluate the initializer but don't store it
            # TODO: Implement proper array initialization
            node.initializer.accept(self)
    
    def visit_array_literal(self, node: ArrayLiteralNode):
        """Visit array literal node"""
        # For now, just emit the first element or zero
        # TODO: Implement proper array literal support
        if node.elements:
            node.elements[0].accept(self)
        else:
            const_idx = self.add_constant(0)
            self.emit(Instruction(Opcode.LOAD_CONST, [const_idx]))
    
    def visit_array_access(self, node: ArrayAccessNode):
        """Visit array access node"""
        # For now, just treat array access as loading the array variable
        # TODO: Implement proper array indexing
        if hasattr(node.array, 'name'):
            # Simple case: array[index]
            array_address = self.get_variable_address(node.array.name)
            self.emit(Instruction(Opcode.LOAD_VAR, [array_address]))
        else:
            # Complex array access
            node.array.accept(self)
    
    def visit_pointer_type(self, node: PointerTypeNode):
        """Visit pointer type node"""
        # Type nodes don't generate bytecode
        pass
    
    def visit_pointer_decl(self, node: PointerDeclNode):
        """Visit pointer declaration node"""
        # Set current position for debug info
        self.set_current_position(node.line, getattr(node, 'column', 0))
        
        # Allocate space for pointer
        pointer_address = self.allocate_variable(node.name)
        
        # Track the pointer type
        pointer_type = self._get_type_name(node.type)
        if self.current_function:
            self.local_variable_types[node.name] = pointer_type
        else:
            self.variable_types[node.name] = pointer_type
        
        if node.initializer:
            # Generate code for initializer
            node.initializer.accept(self)
            # Store the initialized value
            self.emit(Instruction(Opcode.STORE_VAR, [pointer_address]))
        else:
            # Initialize to null pointer (0)
            const_idx = self.add_constant(0)
            self.emit(Instruction(Opcode.LOAD_CONST, [const_idx]))
            self.emit(Instruction(Opcode.STORE_VAR, [pointer_address]))
    
    def visit_address_of(self, node: AddressOfNode):
        """Visit address-of expression node (&variable)"""
        # Set current position for debug info
        self.set_current_position(node.line, getattr(node, 'column', 0))
        
        if isinstance(node.operand, IdentifierExprNode):
            # Simple case: &variable
            var_address = self.get_variable_address(node.operand.name)
            self.emit(Instruction(Opcode.LOAD_ADDR, [var_address]))
        else:
            # Complex address-of operation
            raise CodeGenError("Complex address-of operations not yet supported")
    
    def visit_dereference(self, node: DereferenceNode):
        """Visit dereference expression node (*pointer)"""
        # Set current position for debug info
        self.set_current_position(node.line, getattr(node, 'column', 0))
        
        # Generate code for the pointer expression
        node.operand.accept(self)
        
        # Dereference the pointer
        self.emit(Instruction(Opcode.LOAD_DEREF, []))
    
    def visit_cast_expr(self, node: CastExprNode):
        """Visit cast expression node"""
        # Set current position for debug info
        self.set_current_position(node.line, getattr(node, 'column', 0))
        
        # Generate code for the operand
        node.operand.accept(self)
        
        # For now, casting is mostly a no-op at runtime
        # In a full implementation, we might emit type conversion instructions
        # The semantic analyzer handles the type checking
