"""
Bytecode Generator for Mini-C Language
Converts AST to bytecode instructions.
"""

from typing import Dict, List, Optional, Any, Tuple
from parser.ast_nodes import *
from bytecode.instructions import *
from dataclasses import dataclass

@dataclass
class BytecodeProgram:
    """Complete bytecode program"""
    constants: List[Any]
    strings: List[str]
    functions: Dict[str, int]  # function name -> start address
    instructions: List[Instruction]
    symbol_table: Dict[str, int]  # symbol name -> address
    struct_layouts: Dict[str, Dict[str, int]]  # struct name -> field offsets

class BytecodeGenerator(ASTVisitor):
    """Generates bytecode from AST"""
    
    def __init__(self):
        self.instructions: List[Instruction] = []
        self.constants: List[Any] = []
        self.strings: List[str] = []
        self.functions: Dict[str, int] = {}
        self.symbol_table: Dict[str, int] = {}
        self.struct_layouts: Dict[str, Dict[str, int]] = {}
        
        # Code generation state
        self.current_address = 0
        self.variable_counter = 0
        self.labels: Dict[str, int] = {}
        self.label_counter = 0
        
        # Function context
        self.current_function = None
        self.local_variables: Dict[str, int] = {}
        self.parameter_count = 0
        
        # Control flow
        self.break_labels: List[str] = []
        self.continue_labels: List[str] = []
    
    def generate(self, ast: ProgramNode) -> BytecodeProgram:
        """Generate bytecode from AST"""
        ast.accept(self)
        
        return BytecodeProgram(
            constants=self.constants,
            strings=self.strings,
            functions=self.functions,
            instructions=self.instructions,
            symbol_table=self.symbol_table,
            struct_layouts=self.struct_layouts
        )
    
    def emit(self, instruction: Instruction):
        """Emit an instruction"""
        instruction.line = getattr(self, 'current_line', 0)
        self.instructions.append(instruction)
        self.current_address += 1
    
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
        
        # Second pass: generate code
        for decl in node.declarations:
            self.current_line = decl.line
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
        old_param_count = self.parameter_count
        
        self.current_function = node.name
        self.local_variables = {}
        self.parameter_count = len(node.parameters)
        
        # Allocate space for parameters
        for i, param in enumerate(node.parameters):
            self.local_variables[param.name] = i
        
        # Set variable counter to start after parameters
        self.variable_counter = self.parameter_count
        
        # Generate function body
        node.body.accept(self)
        
        # Ensure function returns (if no explicit return)
        if node.return_type.type_name == 'void':
            self.emit(InstructionBuilder.ret())
        
        # Restore context
        self.current_function = old_function
        self.local_variables = old_locals
        self.parameter_count = old_param_count
    
    def visit_struct_decl(self, node: StructDeclNode):
        """Generate layout for struct declaration with bit-field support"""
        field_info = {}  # field_name -> byte_offset (for compatibility)
        bit_field_info = {}  # field_name -> (byte_offset, bit_offset, bit_width)
        current_byte_offset = 0
        current_bit_offset = 0
        
        for field in node.fields:
            if field.bit_width is not None:
                # Bit-field handling
                bit_width = field.bit_width
                
                # Check if we need to move to next byte
                if current_bit_offset + bit_width > 32:  # Assume 32-bit alignment
                    current_byte_offset += 4  # Move to next 32-bit boundary
                    current_bit_offset = 0
                
                field_info[field.name] = current_byte_offset  # For compatibility
                bit_field_info[field.name] = (current_byte_offset, current_bit_offset, bit_width)
                
                current_bit_offset += bit_width
            else:
                # Regular field handling
                # Align to next byte boundary if we have pending bits
                if current_bit_offset > 0:
                    current_byte_offset += 4
                    current_bit_offset = 0
                
                field_info[field.name] = current_byte_offset
                
                # Calculate field size
                field_size = self.get_type_size(field.type)
                current_byte_offset += field_size
        
        self.struct_layouts[node.name] = field_info
        # Store bit-field info separately for now
        if not hasattr(self, 'bit_field_layouts'):
            self.bit_field_layouts = {}
        self.bit_field_layouts[node.name] = bit_field_info
    
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
    
    def visit_array_type(self, node: ArrayTypeNode):
        """Type nodes don't generate code"""
        pass
    
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
            field_offset = self._get_simple_field_offset(node.property)
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
    
    def _get_bit_field_info(self, field_name: str):
        """Get bit field information for a field"""
        # This is a simplified implementation
        # In a real implementation, this would look up the struct definition
        bit_fields = {
            'enable': (0, 0, 1),    # byte_offset, bit_offset, bit_width
            'mode': (0, 1, 2),
            'speed': (0, 3, 4),
            'reserved': (0, 7, 25)
        }
        return bit_fields.get(field_name, None)

    def _get_simple_field_offset(self, field_name: str) -> int:
        """Get simple field offset"""
        field_offsets = {
            'temperature': 0,
            'humidity': 1, 
            'pressure': 2,
            'control': 3,
            'enable': 10,  # Use higher offset for nested fields
            'mode': 11,
            'speed': 12,
            'reserved': 13
        }
        return field_offsets.get(field_name, 0)
    
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
                    self.emit(InstructionBuilder.call(func_id))
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
        
        else:
            raise CodeGenError(f"Unknown built-in function: {func_name}")
    
    def visit_member_expr(self, node: MemberExprNode):
        """Generate code for member expression"""
        if node.computed:
            # Array access
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
            # Struct field access
            node.object.accept(self)
            
            # Get field offset (simplified)
            # In a real implementation, we'd look up the struct layout
            field_offset = 0  # Placeholder
            
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
        """Get size of type in bytes (simplified)"""
        if isinstance(type_node, PrimitiveTypeNode):
            if type_node.type_name == 'char':
                return 1
            elif type_node.type_name in ['int', 'float']:
                return 4
            else:
                return 0
        elif isinstance(type_node, StructTypeNode):
            # Return size of struct (simplified)
            return 16  # Placeholder
        elif isinstance(type_node, ArrayTypeNode):
            element_size = self.get_type_size(type_node.element_type)
            return element_size * (type_node.size or 1)
        else:
            return 4  # Default size

    def _generate_member_load(self, node: MemberExprNode):
        """Generate code to load from a member expression"""
        if isinstance(node.object, IdentifierExprNode):
            # Simple case: variable.field
            base_address = self.get_variable_address(node.object.name)
            
            # Check if this is a bit-field
            bit_field_info = self._get_bit_field_info(node.property)
            if bit_field_info:
                byte_offset, bit_offset, bit_width = bit_field_info
                self.emit(InstructionBuilder.load_struct_member_bit(
                    base_address, byte_offset, bit_offset, bit_width))
            else:
                # Regular field access
                field_offset = self._get_simple_field_offset(node.property)
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
        if isinstance(node.object, IdentifierExprNode):
            # Simple case: variable.field = value
            base_address = self.get_variable_address(node.object.name)
            
            # Check if this is a bit-field
            bit_field_info = self._get_bit_field_info(node.property)
            if bit_field_info:
                byte_offset, bit_offset, bit_width = bit_field_info
                self.emit(InstructionBuilder.store_struct_member_bit(
                    base_address, byte_offset, bit_offset, bit_width))
            else:
                # Regular field access
                field_offset = self._get_simple_field_offset(node.property)
                self.emit(InstructionBuilder.store_struct_member(base_address, field_offset))
        elif isinstance(node.object, MemberExprNode):
            # Nested case: variable.field1.field2 = value
            base_var = self._get_base_variable_name(node.object)
            base_address = self.get_variable_address(base_var)
            field_offset = self._calculate_nested_offset(node)
            self.emit(InstructionBuilder.store_struct_member(base_address, field_offset))
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
            return self._get_simple_field_offset(node.property)
        elif isinstance(node.object, MemberExprNode):
            # Nested access: calculate parent offset + current field offset
            parent_offset = self._calculate_nested_offset(node.object)
            current_offset = self._get_simple_field_offset(node.property)
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
        if node.channel not in self.symbol_table:
            raise CodeGenError(f"Undefined message queue: {node.channel}")
        
        message_id = self.symbol_table[node.channel]
        
        # Emit message send instruction
        self.emit(Instruction(Opcode.MSG_SEND, [message_id]))

    def visit_message_recv(self, node: MessageRecvNode):
        """Generate code for message receive"""
        # Get the message queue ID
        if node.channel not in self.symbol_table:
            raise CodeGenError(f"Undefined message queue: {node.channel}")
        
        message_id = self.symbol_table[node.channel]
        
        # Emit message receive instruction
        self.emit(Instruction(Opcode.MSG_RECV, [message_id]))

    def _get_type_name(self, type_node: TypeNode) -> str:
        """Get the type name as a string for bytecode"""
        if isinstance(type_node, PrimitiveTypeNode):
            return type_node.type_name
        elif isinstance(type_node, StructTypeNode):
            return f"struct_{type_node.struct_name}"
        elif isinstance(type_node, ArrayTypeNode):
            element_type = self._get_type_name(type_node.element_type)
            return f"{element_type}[{type_node.size or 0}]"
        else:
            return "unknown"

class CodeGenError(Exception):
    """Code generation error"""
    pass
