"""
Semantic Analyzer for RT-Micro-C Language
Performs type checking, symbol resolution, and semantic validation.

KNOWN ISSUES:
- BUG: Variable scope management issue with multiple while loops using same variable
  Symptom: "Undefined identifier" error when same variable is used in multiple while loops
  Example code that fails:
    int x = 10;
    while (x > 0) { x--; }
    while (x < 10) { x++; }  // Error: "Undefined identifier 'x'"
  The variable 'x' should remain in scope but is lost during semantic analysis.
  Root cause: Likely issue in scope management during nested statement traversal.
"""

from typing import Dict, List, Optional, Any, Set
from src.parser.ast_nodes import *
from dataclasses import dataclass
from enum import Enum, auto

class SemanticError(Exception):
    """Semantic analysis error"""
    pass

class SymbolType(Enum):
    """Types of symbols in the symbol table"""
    VARIABLE = auto()
    FUNCTION = auto()
    STRUCT = auto()
    PARAMETER = auto()
    MESSAGE = auto()  # Message queue symbol

@dataclass
class Symbol:
    """Symbol table entry"""
    name: str
    symbol_type: SymbolType
    data_type: str
    value: Any = None
    line: int = 0
    is_const: bool = False
    struct_fields: Optional[Dict[str, 'Symbol']] = None
    function_params: Optional[List['Symbol']] = None
    function_return_type: Optional[str] = None

class SymbolTable:
    """Symbol table for scope management"""
    
    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.scope_level = 0 if parent is None else parent.scope_level + 1
    
    def define(self, symbol: Symbol):
        """Define a symbol in current scope"""
        if symbol.name in self.symbols:
            raise SemanticError(f"Symbol '{symbol.name}' already defined in this scope")
        self.symbols[symbol.name] = symbol
    
    def get(self, name: str) -> Optional[Symbol]:
        """Get a symbol from current or parent scopes"""
        if name in self.symbols:
            return self.symbols[name]
        
        if self.parent:
            return self.parent.get(name)
        
        return None
    
    def exists(self, name: str) -> bool:
        """Check if symbol exists in current or parent scopes"""
        return self.get(name) is not None
    
    def get_all_symbols(self) -> Dict[str, Symbol]:
        """Get all symbols visible in current scope"""
        all_symbols = {}
        
        # Start with parent symbols
        if self.parent:
            all_symbols.update(self.parent.get_all_symbols())
        
        # Override with current scope symbols
        all_symbols.update(self.symbols)
        
        return all_symbols

class TypeChecker:
    """Type checking utilities"""
    
    PRIMITIVE_TYPES = {'int', 'float', 'char', 'void', 'bool'}
    
    @staticmethod
    def is_numeric_type(type_name: str) -> bool:
        """Check if type is numeric"""
        return type_name in {'int', 'float', 'char'}
    
    @staticmethod
    def is_integer_type(type_name: str) -> bool:
        """Check if type is integer"""
        return type_name in {'int', 'char'}
    
    @staticmethod
    def is_condition_type(type_name: str) -> bool:
        """Check if type can be used in boolean conditions"""
        return type_name in {'int', 'float', 'char', 'bool'} or TypeChecker.is_pointer_type(type_name)
    
    @staticmethod
    def is_pointer_type(type_name: str) -> bool:
        """Check if type is a pointer type"""
        return type_name.endswith('*')
    
    @staticmethod
    def get_pointer_base_type(type_name: str) -> str:
        """Get the base type of a pointer (remove one level of indirection)"""
        if TypeChecker.is_pointer_type(type_name):
            return type_name[:-1]
        return type_name
    
    @staticmethod
    def can_convert(from_type: str, to_type: str) -> bool:
        """Check if one type can be converted to another"""
        if from_type == to_type:
            return True
        
        # Numeric conversions
        if TypeChecker.is_numeric_type(from_type) and TypeChecker.is_numeric_type(to_type):
            return True
        
        # String conversions
        if from_type == 'string' and to_type == 'string':
            return True
        
        # Pointer conversions
        if TypeChecker.is_pointer_type(from_type) and TypeChecker.is_pointer_type(to_type):
            # void* can be converted to any pointer type and vice versa
            if from_type == 'void*' or to_type == 'void*':
                return True
            # Same pointer types
            if from_type == to_type:
                return True
        
        # Address-of can be assigned to pointer
        if TypeChecker.is_pointer_type(to_type):
            base_type = TypeChecker.get_pointer_base_type(to_type)
            if from_type == base_type:
                return True
        
        return False
    
    @staticmethod
    def get_common_type(type1: str, type2: str) -> str:
        """Get common type for binary operations"""
        if type1 == type2:
            return type1
        
        # Float promotion
        if (type1 == 'float' and TypeChecker.is_numeric_type(type2)) or \
           (type2 == 'float' and TypeChecker.is_numeric_type(type1)):
            return 'float'
        
        # Integer promotion
        if TypeChecker.is_integer_type(type1) and TypeChecker.is_integer_type(type2):
            return 'int'
        
        raise SemanticError(f"Cannot find common type for {type1} and {type2}")
    
    @staticmethod
    def get_binary_result_type(op: str, left_type: str, right_type: str) -> str:
        """Get result type for binary operations"""
        # Comparison operators always return int (boolean)
        if op in ['==', '!=', '<', '<=', '>', '>=']:
            if not (TypeChecker.is_numeric_type(left_type) and TypeChecker.is_numeric_type(right_type)):
                raise SemanticError(f"Cannot compare {left_type} and {right_type}")
            return 'int'
        
        # Logical operators
        if op in ['&&', '||']:
            return 'int'
        
        # Arithmetic operators
        if op in ['+', '-', '*', '/', '%']:
            if not (TypeChecker.is_numeric_type(left_type) and TypeChecker.is_numeric_type(right_type)):
                raise SemanticError(f"Cannot perform arithmetic on {left_type} and {right_type}")
            
            # Modulo only works on integers
            if op == '%' and not (TypeChecker.is_integer_type(left_type) and TypeChecker.is_integer_type(right_type)):
                raise SemanticError("Modulo operator requires integer operands")
            
            return TypeChecker.get_common_type(left_type, right_type)
        
        # Bitwise operators
        if op in ['&', '|', '^']:
            if not (TypeChecker.is_integer_type(left_type) and TypeChecker.is_integer_type(right_type)):
                raise SemanticError(f"Bitwise operations require integer operands")
            return TypeChecker.get_common_type(left_type, right_type)
        
        raise SemanticError(f"Unknown binary operator: {op}")

class SemanticAnalyzer(ASTVisitor):
    """Main semantic analyzer"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function = None
        self.current_return_type = None
        self.in_loop = False
        self.errors: List[str] = []
        
        # Initialize built-in functions
        self._init_builtin_functions()
    
    def _init_builtin_functions(self):
        """Initialize built-in RTOS and hardware functions"""
        builtins = {
            # RTOS functions
            'RTOS_CREATE_TASK': Symbol('RTOS_CREATE_TASK', SymbolType.FUNCTION, 'void',
                                     function_params=[
                                         Symbol('func_ptr', SymbolType.PARAMETER, 'void'),
                                         Symbol('name', SymbolType.PARAMETER, 'string'),
                                         Symbol('stack_size', SymbolType.PARAMETER, 'int'),
                                         Symbol('priority', SymbolType.PARAMETER, 'int'),
                                         Symbol('core', SymbolType.PARAMETER, 'int')
                                     ], function_return_type='void'),
            'RTOS_DELETE_TASK': Symbol('RTOS_DELETE_TASK', SymbolType.FUNCTION, 'void',
                                     function_params=[Symbol('task_handle', SymbolType.PARAMETER, 'int')],
                                     function_return_type='void'),
            'RTOS_DELAY_MS': Symbol('RTOS_DELAY_MS', SymbolType.FUNCTION, 'void',
                                  function_params=[Symbol('ms', SymbolType.PARAMETER, 'int')],
                                  function_return_type='void'),
            'RTOS_SEMAPHORE_CREATE': Symbol('RTOS_SEMAPHORE_CREATE', SymbolType.FUNCTION, 'int',
                                          function_params=[], function_return_type='int'),
            'RTOS_SEMAPHORE_TAKE': Symbol('RTOS_SEMAPHORE_TAKE', SymbolType.FUNCTION, 'int',
                                        function_params=[
                                            Symbol('handle', SymbolType.PARAMETER, 'int'),
                                            Symbol('timeout', SymbolType.PARAMETER, 'int')
                                        ], function_return_type='int'),
            'RTOS_SEMAPHORE_GIVE': Symbol('RTOS_SEMAPHORE_GIVE', SymbolType.FUNCTION, 'void',
                                        function_params=[Symbol('handle', SymbolType.PARAMETER, 'int')],
                                        function_return_type='void'),
            'RTOS_YIELD': Symbol('RTOS_YIELD', SymbolType.FUNCTION, 'void',
                               function_params=[], function_return_type='void'),
            'RTOS_SUSPEND_TASK': Symbol('RTOS_SUSPEND_TASK', SymbolType.FUNCTION, 'void',
                                      function_params=[Symbol('task_handle', SymbolType.PARAMETER, 'int')],
                                      function_return_type='void'),
            'RTOS_RESUME_TASK': Symbol('RTOS_RESUME_TASK', SymbolType.FUNCTION, 'void',
                                     function_params=[Symbol('task_handle', SymbolType.PARAMETER, 'int')],
                                     function_return_type='void'),
            
            # Hardware GPIO functions
            'HW_GPIO_INIT': Symbol('HW_GPIO_INIT', SymbolType.FUNCTION, 'void',
                                 function_params=[
                                     Symbol('pin', SymbolType.PARAMETER, 'int'),
                                     Symbol('mode', SymbolType.PARAMETER, 'int')
                                 ], function_return_type='void'),
            'HW_GPIO_SET': Symbol('HW_GPIO_SET', SymbolType.FUNCTION, 'void',
                                function_params=[
                                    Symbol('pin', SymbolType.PARAMETER, 'int'),
                                    Symbol('value', SymbolType.PARAMETER, 'int')
                                ], function_return_type='void'),
            'HW_GPIO_GET': Symbol('HW_GPIO_GET', SymbolType.FUNCTION, 'int',
                                function_params=[Symbol('pin', SymbolType.PARAMETER, 'int')],
                                function_return_type='int'),
            
            # Hardware Timer functions
            'HW_TIMER_INIT': Symbol('HW_TIMER_INIT', SymbolType.FUNCTION, 'void',
                                  function_params=[
                                      Symbol('id', SymbolType.PARAMETER, 'int'),
                                      Symbol('mode', SymbolType.PARAMETER, 'int'),
                                      Symbol('freq', SymbolType.PARAMETER, 'int')
                                  ], function_return_type='void'),
            'HW_TIMER_START': Symbol('HW_TIMER_START', SymbolType.FUNCTION, 'void',
                                   function_params=[Symbol('id', SymbolType.PARAMETER, 'int')],
                                   function_return_type='void'),
            'HW_TIMER_STOP': Symbol('HW_TIMER_STOP', SymbolType.FUNCTION, 'void',
                                  function_params=[Symbol('id', SymbolType.PARAMETER, 'int')],
                                  function_return_type='void'),
            'HW_TIMER_SET_PWM_DUTY': Symbol('HW_TIMER_SET_PWM_DUTY', SymbolType.FUNCTION, 'void',
                                          function_params=[
                                              Symbol('id', SymbolType.PARAMETER, 'int'),
                                              Symbol('duty', SymbolType.PARAMETER, 'int')
                                          ], function_return_type='void'),
            
            # Hardware ADC functions
            'HW_ADC_INIT': Symbol('HW_ADC_INIT', SymbolType.FUNCTION, 'void',
                                function_params=[Symbol('pin', SymbolType.PARAMETER, 'int')],
                                function_return_type='void'),
            'HW_ADC_READ': Symbol('HW_ADC_READ', SymbolType.FUNCTION, 'int',
                                function_params=[Symbol('pin', SymbolType.PARAMETER, 'int')],
                                function_return_type='int'),
            
            # Hardware Communication functions
            'HW_UART_WRITE': Symbol('HW_UART_WRITE', SymbolType.FUNCTION, 'void',
                                  function_params=[
                                      Symbol('buffer', SymbolType.PARAMETER, 'char'),
                                      Symbol('length', SymbolType.PARAMETER, 'int')
                                  ], function_return_type='void'),
            'HW_SPI_TRANSFER': Symbol('HW_SPI_TRANSFER', SymbolType.FUNCTION, 'void',
                                    function_params=[
                                        Symbol('tx_buffer', SymbolType.PARAMETER, 'char'),
                                        Symbol('rx_buffer', SymbolType.PARAMETER, 'char'),
                                        Symbol('length', SymbolType.PARAMETER, 'int')
                                    ], function_return_type='void'),
            'HW_I2C_WRITE': Symbol('HW_I2C_WRITE', SymbolType.FUNCTION, 'void',
                                 function_params=[
                                     Symbol('addr', SymbolType.PARAMETER, 'int'),
                                     Symbol('data', SymbolType.PARAMETER, 'int')
                                 ], function_return_type='void'),
            'HW_I2C_READ': Symbol('HW_I2C_READ', SymbolType.FUNCTION, 'int',
                                function_params=[
                                    Symbol('addr', SymbolType.PARAMETER, 'int'),
                                    Symbol('reg', SymbolType.PARAMETER, 'int')
                                ], function_return_type='int'),
            
            # Debug functions
            'DBG_PRINT': Symbol('DBG_PRINT', SymbolType.FUNCTION, 'void',
                              function_params=[Symbol('string', SymbolType.PARAMETER, 'string')],
                              function_return_type='void'),
            'DBG_BREAKPOINT': Symbol('DBG_BREAKPOINT', SymbolType.FUNCTION, 'void',
                                   function_params=[], function_return_type='void'),
        }
        
        for name, symbol in builtins.items():
            self.symbol_table.define(symbol)
    
    def error(self, message: str, line: int = 0, filename: str = ""):
        """Report semantic error"""
        if filename and line > 0:
            error_msg = f"{filename}:{line}: {message}"
        elif line > 0:
            error_msg = f"Line {line}: {message}"
        else:
            error_msg = message
        self.errors.append(error_msg)
        raise SemanticError(error_msg)
    
    def is_type_compatible(self, type1: str, type2: str) -> bool:
        """Check if two types are compatible"""
        # Exact match
        if type1 == type2:
            return True
        
        # Numeric type compatibility (int can be assigned to float)
        if type1 == "int" and type2 == "float":
            return True
        
        # Pointer compatibility (void* is compatible with any pointer type)
        if type1.endswith("*") and type2 == "void*":
            return True
        if type2.endswith("*") and type1 == "void*":
            return True
        
        return False

    def analyze(self, node: ASTNode):
        """Analyze the AST"""
        try:
            node.accept(self)
        except SemanticError:
            pass  # Error already recorded
        
        if self.errors:
            raise SemanticError(f"Semantic analysis failed with {len(self.errors)} error(s):\n" + 
                              "\n".join(self.errors))
    
    def enter_scope(self):
        """Enter new scope"""
        self.symbol_table = SymbolTable(self.symbol_table)
    
    def exit_scope(self):
        """Exit current scope"""
        if self.symbol_table.parent:
            self.symbol_table = self.symbol_table.parent
    
    def get_type_from_node(self, type_node: TypeNode) -> str:
        """Get type string from type node"""
        if isinstance(type_node, PrimitiveTypeNode):
            return type_node.type_name
        elif isinstance(type_node, StructTypeNode):
            return f"struct {type_node.struct_name}"
        elif isinstance(type_node, ArrayTypeNode):
            element_type = self.get_type_from_node(type_node.element_type)
            return f"{element_type}[]"
        elif isinstance(type_node, PointerTypeNode):
            base_type = self.get_type_from_node(type_node.base_type)
            return base_type + '*' * type_node.pointer_level
        else:
            return "unknown"
    
    # Visitor methods
    
    def visit_program(self, node: ProgramNode):
        """Visit program node"""
        for declaration in node.declarations:
            declaration.accept(self)
        
        # Check if main function exists
        main_func = self.symbol_table.get('main')
        if not main_func:
            self.error("Program must have a 'main' function")
        elif main_func.symbol_type != SymbolType.FUNCTION:
            self.error("'main' must be a function")
    
    def visit_function_decl(self, node: FunctionDeclNode):
        """Visit function declaration"""
        func_name = node.name
        return_type = self.get_type_from_node(node.return_type)
        
        # Check if function already exists
        if self.symbol_table.exists(func_name):
            self.error(f"Function '{func_name}' already defined", node.line, node.filename)
        
        # Create function symbol
        param_symbols = []
        for param in node.parameters:
            param_type = self.get_type_from_node(param.type)
            param_symbols.append(Symbol(param.name, SymbolType.PARAMETER, param_type))
        
        func_symbol = Symbol(func_name, SymbolType.FUNCTION, return_type,
                           function_params=param_symbols, function_return_type=return_type)
        
        self.symbol_table.define(func_symbol)
        
        # Analyze function body
        self.current_function = func_name
        self.current_return_type = return_type
        
        self.enter_scope()
        
        # Add parameters to function scope
        for param_symbol in param_symbols:
            self.symbol_table.define(param_symbol)
        
        node.body.accept(self)
        
        self.exit_scope()
        
        self.current_function = None
        self.current_return_type = None
    
    def visit_struct_decl(self, node: StructDeclNode):
        """Visit struct declaration"""
        struct_name = node.name
        
        # Check if struct already exists
        if self.symbol_table.exists(struct_name):
            self.error(f"Struct '{struct_name}' already defined", node.line, node.filename)
        
        # Create struct symbol with field information
        field_symbols = {}
        for field in node.fields:
            field_type = self.get_type_from_node(field.type)
            field_symbols[field.name] = Symbol(field.name, SymbolType.VARIABLE, field_type)
        
        struct_symbol = Symbol(struct_name, SymbolType.STRUCT, f"struct {struct_name}",
                             struct_fields=field_symbols)
        
        self.symbol_table.define(struct_symbol)
    
    def visit_task_decl(self, node: TaskDeclNode):
        """Visit task declaration"""
        task_name = node.name
        
        # Check if task already exists
        if self.symbol_table.exists(task_name):
            self.error(f"Task '{task_name}' already defined", node.line, node.filename)
        
        # Validate core and priority values
        if node.core < 0 or node.core > 7:  # Assuming max 8 cores
            self.error(f"Invalid core number {node.core}, must be 0-7", node.line, node.filename)
        
        if node.priority < 1 or node.priority > 10:  # Assuming priority range 1-10
            self.error(f"Invalid priority {node.priority}, must be 1-10", node.line, node.filename)
        
        # Create new scope for task
        self.symbol_table = SymbolTable(self.symbol_table)
        self.current_function = f"{task_name}_context"
        
        try:
            # Visit all task members
            for member in node.members:
                member.accept(self)
            
            # Temporarily rename the run function to avoid conflicts
            original_name = node.run_function.name
            node.run_function.name = f"{task_name}_run"
            
            # Visit the run function
            node.run_function.accept(self)
            
            # Restore original name for verification
            node.run_function.name = original_name
            
            # Verify run function signature
            if (original_name != "run" or
                not isinstance(node.run_function.return_type, PrimitiveTypeNode) or
                node.run_function.return_type.type_name != "void" or
                len(node.run_function.parameters) != 0):
                self.error("Task must have exactly one 'void run()' method with no parameters", node.line, node.filename)
        
        finally:
            # Exit task scope
            self.symbol_table = self.symbol_table.parent
            self.current_function = None
        
        # Register task as a special function symbol
        task_symbol = Symbol(task_name, SymbolType.FUNCTION, "task",
                           function_return_type="void",
                           function_params=[])
        
        self.symbol_table.define(task_symbol)

    def visit_variable_decl(self, node: VariableDeclNode):
        """Visit variable declaration"""
        var_name = node.name
        var_type = self.get_type_from_node(node.type)
        
        # Check if variable already exists in current scope
        if var_name in self.symbol_table.symbols:
            self.error(f"Variable '{var_name}' already defined in this scope", node.line, node.filename)
        
        # Check initializer type if present
        if node.initializer:
            init_type = node.initializer.accept(self)
            if not TypeChecker.can_convert(init_type, var_type):
                self.error(f"Cannot initialize {var_type} with {init_type}", node.line, node.filename)
        
        # Create variable symbol
        var_symbol = Symbol(var_name, SymbolType.VARIABLE, var_type, is_const=node.is_const)
        self.symbol_table.define(var_symbol)
    
    def visit_primitive_type(self, node: PrimitiveTypeNode):
        """Visit primitive type node"""
        return node.type_name
    
    def visit_struct_type(self, node: StructTypeNode):
        """Visit struct type node"""
        struct_symbol = self.symbol_table.get(node.struct_name)
        if not struct_symbol or struct_symbol.symbol_type != SymbolType.STRUCT:
            self.error(f"Undefined struct '{node.struct_name}'", node.line, node.filename)
        
        return f"struct {node.struct_name}"
    
    def visit_array_type(self, node: ArrayTypeNode):
        """Visit array type node"""
        element_type = node.element_type.accept(self)
        return f"{element_type}[]"
    
    def visit_block_stmt(self, node: BlockStmtNode):
        """Visit block statement"""
        self.enter_scope()
        
        for stmt in node.statements:
            stmt.accept(self)
        
        self.exit_scope()
    
    def visit_expression_stmt(self, node: ExpressionStmtNode):
        """Visit expression statement"""
        node.expression.accept(self)
    
    def visit_if_stmt(self, node: IfStmtNode):
        """Visit if statement"""
        cond_type = node.condition.accept(self)
        if not TypeChecker.is_condition_type(cond_type):
            self.error(f"If condition must be numeric or boolean, got {cond_type}", node.line, node.filename)
        
        node.then_stmt.accept(self)
        
        if node.else_stmt:
            node.else_stmt.accept(self)
    
    def visit_while_stmt(self, node: WhileStmtNode):
        """Visit while statement"""
        cond_type = node.condition.accept(self)
        if not TypeChecker.is_condition_type(cond_type):
            self.error(f"While condition must be numeric or boolean, got {cond_type}", node.line, node.filename)
        
        old_in_loop = self.in_loop
        self.in_loop = True
        
        node.body.accept(self)
        
        self.in_loop = old_in_loop
    
    def visit_for_stmt(self, node: ForStmtNode):
        """Visit for statement"""
        self.enter_scope()
        
        if node.init:
            node.init.accept(self)
        
        if node.condition:
            cond_type = node.condition.accept(self)
            if not TypeChecker.is_condition_type(cond_type):
                self.error(f"For condition must be numeric or boolean, got {cond_type}", node.line, node.filename)
        
        if node.update:
            node.update.accept(self)
        
        old_in_loop = self.in_loop
        self.in_loop = True
        
        node.body.accept(self)
        
        self.in_loop = old_in_loop
        
        self.exit_scope()
    
    def visit_return_stmt(self, node: ReturnStmtNode):
        """Visit return statement"""
        if not self.current_function:
            self.error("Return statement outside function", node.line, node.filename)
        
        if node.value:
            value_type = node.value.accept(self)
            if not TypeChecker.can_convert(value_type, self.current_return_type):
                self.error(f"Cannot return {value_type} from function returning {self.current_return_type}", node.line, node.filename)
        else:
            if self.current_return_type != 'void':
                self.error(f"Function must return a value of type {self.current_return_type}", node.line, node.filename)
    
    def visit_break_stmt(self, node: BreakStmtNode):
        """Visit break statement"""
        if not self.in_loop:
            self.error("Break statement outside loop", node.line, node.filename)
    
    def visit_continue_stmt(self, node: ContinueStmtNode):
        """Visit continue statement"""
        if not self.in_loop:
            self.error("Continue statement outside loop", node.line, node.filename)
    
    def visit_binary_expr(self, node: BinaryExprNode):
        """Visit binary expression"""
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)
        
        try:
            result_type = TypeChecker.get_binary_result_type(node.operator, left_type, right_type)
            return result_type
        except SemanticError as e:
            self.error(str(e), node.line, node.filename)
            return "int"  # Default return type
    
    def visit_unary_expr(self, node: UnaryExprNode):
        """Visit unary expression"""
        operand_type = node.operand.accept(self)
        
        if node.operator == '!':
            return 'int'
        elif node.operator in ['+', '-']:
            if not TypeChecker.is_numeric_type(operand_type):
                self.error(f"Unary {node.operator} requires numeric operand", node.line, node.filename)
            return operand_type
        else:
            self.error(f"Unknown unary operator: {node.operator}", node.line, node.filename)
            return operand_type
    
    def visit_postfix_expr(self, node: PostfixExprNode):
        """Visit postfix expression (++ and --)"""
        operand_type = node.operand.accept(self)
        
        if node.operator in ['++', '--']:
            if not TypeChecker.is_numeric_type(operand_type):
                self.error(f"Postfix {node.operator} requires numeric operand", node.line, node.filename)
            # Check that operand is an lvalue (assignable)
            if not isinstance(node.operand, (IdentifierExprNode, MemberExprNode, ArrayAccessNode)):
                self.error(f"Postfix {node.operator} requires an assignable operand", node.line, node.filename)
            return operand_type
        else:
            self.error(f"Unknown postfix operator: {node.operator}", node.line, node.filename)
            return operand_type

    def visit_assignment_expr(self, node: AssignmentExprNode):
        """Visit assignment expression"""
        target_type = node.target.accept(self)
        value_type = node.value.accept(self)
        
        # Check if target is assignable
        if isinstance(node.target, IdentifierExprNode):
            symbol = self.symbol_table.get(node.target.name)
            if symbol and symbol.is_const:
                self.error(f"Cannot assign to const variable '{node.target.name}'", node.line, node.filename)
        
        if node.operator == '=':
            if not TypeChecker.can_convert(value_type, target_type):
                self.error(f"Cannot assign {value_type} to {target_type}", node.line, node.filename)
        else:
            # Compound assignment operators
            op = node.operator[:-1]  # Remove '='
            try:
                TypeChecker.get_binary_result_type(op, target_type, value_type)
            except SemanticError as e:
                self.error(str(e), node.line, node.filename)
        
        return target_type
    
    def visit_call_expr(self, node: CallExprNode):
        """Visit call expression"""
        if isinstance(node.callee, IdentifierExprNode):
            func_name = node.callee.name
            func_symbol = self.symbol_table.get(func_name)
            
            if not func_symbol:
                self.error(f"Undefined function '{func_name}'", node.line, node.filename)
                return "int"
            
            if func_symbol.symbol_type != SymbolType.FUNCTION:
                self.error(f"'{func_name}' is not a function", node.line, node.filename)
                return "int"
            
            # Check argument count
            expected_params = len(func_symbol.function_params) if func_symbol.function_params else 0
            actual_args = len(node.arguments)
            
            if actual_args != expected_params:
                self.error(f"Function '{func_name}' expects {expected_params} arguments, got {actual_args}", node.line)
            
            # Check argument types
            if func_symbol.function_params:
                for i, (arg, param) in enumerate(zip(node.arguments, func_symbol.function_params)):
                    arg_type = arg.accept(self)
                    if not TypeChecker.can_convert(arg_type, param.data_type):
                        self.error(f"Argument {i+1} to '{func_name}': cannot convert {arg_type} to {param.data_type}", node.line, node.filename)
            
            return func_symbol.function_return_type
        
        else:
            self.error("Invalid function call", node.line, node.filename)
            return "int"
    
    def visit_member_expr(self, node: MemberExprNode):
        """Visit member expression"""
        object_type = node.object.accept(self)
        
        if node.computed:
            # Array access
            if not object_type.endswith('[]'):
                self.error(f"Cannot index non-array type {object_type}", node.line, node.filename)
            
            # Index should be integer
            if isinstance(node.property, ExpressionNode):
                index_type = node.property.accept(self)
                if not TypeChecker.is_integer_type(index_type):
                    self.error(f"Array index must be integer, got {index_type}", node.line)
            
            # Return element type
            return object_type[:-2]  # Remove '[]'
        
        else:
            # Struct field access
            if not object_type.startswith('struct '):
                self.error(f"Cannot access field of non-struct type {object_type}", node.line, node.filename)
            
            struct_name = object_type[7:]  # Remove 'struct '
            struct_symbol = self.symbol_table.get(struct_name)
            
            if not struct_symbol or not struct_symbol.struct_fields:
                self.error(f"Unknown struct '{struct_name}'", node.line, node.filename)
                return "int"
            
            field_name = node.property
            if field_name not in struct_symbol.struct_fields:
                self.error(f"Struct '{struct_name}' has no field '{field_name}'", node.line, node.filename)
                return "int"
            
            return struct_symbol.struct_fields[field_name].data_type
    
    def visit_identifier_expr(self, node: IdentifierExprNode):
        """Visit identifier expression"""
        symbol = self.symbol_table.get(node.name)
        
        if not symbol:
            self.error(f"Undefined identifier '{node.name}'", node.line, node.filename)
            return "int"
        
        if symbol.symbol_type == SymbolType.FUNCTION:
            return symbol.function_return_type
        else:
            return symbol.data_type
    
    def visit_literal_expr(self, node: LiteralExprNode):
        """Visit literal expression"""
        return node.literal_type

    def visit_message_decl(self, node: MessageDeclNode):
        """Visit message declaration"""
        # Check if the message type is valid
        message_type = node.message_type.accept(self)
        
        # Messages must be declared at global scope (not inside functions or tasks)
        if self.symbol_table.scope_level > 0:
            self.error(f"Message queue '{node.name}' must be declared at global scope", node.line, node.filename)
        
        # Check if message name is already defined
        if self.symbol_table.get(node.name):
            self.error(f"Message queue '{node.name}' already defined", node.line, node.filename)
        
        # Add message to symbol table
        symbol = Symbol(
            name=node.name,
            symbol_type=SymbolType.MESSAGE,
            data_type=message_type,
            line=node.line
        )
        
        self.symbol_table.define(symbol)
        return message_type

    def visit_message_send(self, node: MessageSendNode):
        """Visit message send expression"""
        # Check if the message queue exists
        symbol = self.symbol_table.get(node.channel)
        
        if not symbol:
            self.error(f"Undefined message queue '{node.channel}'", node.line, node.filename)
            return "void"
        
        if symbol.symbol_type != SymbolType.MESSAGE:
            self.error(f"'{node.channel}' is not a message queue", node.line, node.filename)
            return "void"
        
        # Check payload type matches message type
        payload_type = node.payload.accept(self)
        
        if not self.is_type_compatible(payload_type, symbol.data_type):
            self.error(f"Type mismatch in message send: expected {symbol.data_type}, got {payload_type}", node.line)
        
        return "void"

    def visit_message_recv(self, node: MessageRecvNode):
        """Visit message receive expression"""
        # Check if the message queue exists
        symbol = self.symbol_table.get(node.channel)
        
        if not symbol:
            self.error(f"Undefined message queue '{node.channel}'", node.line, node.filename)
            return "int"
        
        if symbol.symbol_type != SymbolType.MESSAGE:
            self.error(f"'{node.channel}' is not a message queue", node.line, node.filename)
            return "int"
        
        # Check timeout parameter if present
        if node.timeout:
            timeout_type = node.timeout.accept(self)
            if timeout_type != "int":
                self.error(f"Timeout parameter must be int, got {timeout_type}", node.line)
        
        # Return the message type
        return symbol.data_type

    def visit_import_stmt(self, node: ImportStmtNode):
        """Visit import statement - handled by compiler, no semantic checking needed here"""
        # Import statements are processed by the compiler before semantic analysis
        # So we don't need to do anything here
        pass
    
    def visit_array_decl(self, node: ArrayDeclNode):
        """Visit array declaration node"""
        # Validate array size
        if node.size <= 0:
            self.error(f"Array size must be positive, got {node.size}", node.line)
        
        # Get element type
        element_type = node.element_type.accept(self)
        
        # Create array type string
        array_type = f"{element_type}[{node.size}]"
        
        # Validate initializer if present
        if node.initializer:
            init_type = node.initializer.accept(self)
            # The initializer should be an array literal
            if not isinstance(node.initializer, ArrayLiteralNode):
                self.error(f"Array initializer must be an array literal", node.line, node.filename)
        
        # Define the array symbol
        symbol = Symbol(
            name=node.name,
            symbol_type=SymbolType.VARIABLE,
            data_type=array_type,
            line=node.line
        )
        self.symbol_table.define(symbol)
        
        return array_type
    
    def visit_array_literal(self, node: ArrayLiteralNode):
        """Visit array literal node"""
        if not node.elements:
            return "void[]"  # Empty array
        
        # Check that all elements have the same type
        element_types = []
        for element in node.elements:
            element_type = element.accept(self)
            element_types.append(element_type)
        
        # For now, just return the type of the first element
        # In a more sophisticated implementation, we'd do type unification
        first_type = element_types[0]
        for i, elem_type in enumerate(element_types[1:], 1):
            if elem_type != first_type:
                self.error(f"Array element {i} has type {elem_type}, expected {first_type}", node.line)
        
        return f"{first_type}[]"
    
    def visit_array_access(self, node: ArrayAccessNode):
        """Visit array access node"""
        # Get the array type
        array_type = node.array.accept(self)
        
        # Check that it's actually an array type
        if not ('[' in array_type and ']' in array_type):
            self.error(f"Cannot index non-array type {array_type}", node.line, node.filename)
        
        # Get the index type
        index_type = node.index.accept(self)
        if index_type != "int":
            self.error(f"Array index must be int, got {index_type}", node.line)
        
        # Extract element type from array type (e.g., "int[5]" -> "int")
        element_type = array_type.split('[')[0]
        return element_type
    
    def visit_pointer_type(self, node: PointerTypeNode):
        """Visit pointer type node"""
        base_type = node.base_type.accept(self)
        
        # Build pointer type string with correct level of indirection
        pointer_type = base_type + '*' * node.pointer_level
        return pointer_type
    
    def visit_pointer_decl(self, node: PointerDeclNode):
        """Visit pointer declaration node"""
        # Get the pointer type
        pointer_type = node.type.accept(self)
        
        # Check if variable already exists in current scope
        if node.name in self.symbol_table.symbols:
            self.error(f"Pointer '{node.name}' already defined in this scope", node.line, node.filename)
        
        # Check initializer type if present
        if node.initializer:
            init_type = node.initializer.accept(self)
            if not TypeChecker.can_convert(init_type, pointer_type):
                self.error(f"Cannot initialize {pointer_type} with {init_type}", node.line, node.filename)
        
        # Create pointer symbol
        pointer_symbol = Symbol(node.name, SymbolType.VARIABLE, pointer_type, is_const=node.is_const)
        self.symbol_table.define(pointer_symbol)
        
        return pointer_type
    
    def visit_address_of(self, node: AddressOfNode):
        """Visit address-of expression (&)"""
        operand_type = node.operand.accept(self)
        
        # Check that operand is an lvalue (addressable)
        if not isinstance(node.operand, (IdentifierExprNode, MemberExprNode, ArrayAccessNode)):
            self.error("Address-of operator requires an lvalue operand", node.line, node.filename)
        
        # Return pointer to the operand type
        return operand_type + '*'
    
    def visit_dereference(self, node: DereferenceNode):
        """Visit dereference expression (*)"""
        operand_type = node.operand.accept(self)
        
        # Check that operand is a pointer type
        if not operand_type.endswith('*'):
            self.error(f"Cannot dereference non-pointer type {operand_type}", node.line, node.filename)
            return "int"  # Return default type to continue analysis
        
        # Return the base type (remove one level of pointer indirection)
        return operand_type[:-1]
