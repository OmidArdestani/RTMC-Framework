"""
Bytecode Instructions for RT-Micro-C Virtual Machine
Defines all available opcodes and their parameters.
"""

from enum import IntEnum, auto
from typing import List, Any, Optional
from dataclasses import dataclass

class Opcode(IntEnum):
    """Bytecode instruction opcodes"""
    
    # Control Flow Instructions
    JUMP = auto()
    JUMPIF_TRUE = auto()
    JUMPIF_FALSE = auto()
    CALL = auto()
    RET = auto()
    
    # Data Manipulation - Load/Store
    LOAD_CONST = auto()
    LOAD_VAR = auto()
    STORE_VAR = auto()
    LOAD_STRUCT_MEMBER = auto()
    STORE_STRUCT_MEMBER = auto()
    LOAD_STRUCT_MEMBER_BIT = auto()
    STORE_STRUCT_MEMBER_BIT = auto()
    
    # Pointer Instructions (NEW)
    LOAD_ADDR = auto()      # Load address of variable
    LOAD_DEREF = auto()     # Dereference pointer on stack
    STORE_DEREF = auto()    # Store value at pointer address
    
    # Arithmetic and Logical
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()
    
    # Comparisons
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    
    # Memory Management
    ALLOC_VAR = auto()
    FREE_VAR = auto()
    ALLOC_STRUCT = auto()
    
    # RTOS Task Instructions
    RTOS_CREATE_TASK = auto()
    RTOS_DELETE_TASK = auto()
    RTOS_DELAY_MS = auto()
    RTOS_SEMAPHORE_CREATE = auto()
    RTOS_SEMAPHORE_TAKE = auto()
    RTOS_SEMAPHORE_GIVE = auto()
    RTOS_YIELD = auto()
    RTOS_SUSPEND_TASK = auto()
    RTOS_RESUME_TASK = auto()
    
    # Message Passing Instructions
    MSG_DECLARE = auto()  # Declare a message queue
    MSG_SEND = auto()     # Send message to queue
    MSG_RECV = auto()     # Receive message from queue
    
    # Hardware Access - GPIO
    HW_GPIO_INIT = auto()
    HW_GPIO_SET = auto()
    HW_GPIO_GET = auto()
    
    # Hardware Access - Timers
    HW_TIMER_INIT = auto()
    HW_TIMER_START = auto()
    HW_TIMER_STOP = auto()
    HW_TIMER_SET_PWM_DUTY = auto()
    
    # Hardware Access - ADC
    HW_ADC_INIT = auto()
    HW_ADC_READ = auto()
    
    # Hardware Access - Communication
    HW_UART_WRITE = auto()
    HW_SPI_TRANSFER = auto()
    HW_I2C_WRITE = auto()
    HW_I2C_READ = auto()
    
    # Debugging / System
    DBG_PRINT = auto()
    DBG_PRINTF = auto()  # Formatted print with variables
    DBG_BREAKPOINT = auto()
    SYSCALL = auto()
    
    # Special
    HALT = auto()
    NOP = auto()
    COMMENT = auto()  # NEW: For debug comments

@dataclass
class Instruction:
    """A single bytecode instruction with enhanced debug info"""
    opcode: Opcode
    operands: List[Any]
    line: Optional[int] = None
    column: Optional[int] = None  # NEW: Column information for better debug info
    
    def __str__(self):
        if self.operands:
            operand_str = ' '.join(str(op) for op in self.operands)
            return f"{self.opcode.name} {operand_str}"
        return self.opcode.name

@dataclass
class Label:
    """A label for jump targets"""
    name: str
    address: Optional[int] = None
    
    def __str__(self):
        return f"LABEL {self.name}"

class InstructionBuilder:
    """Helper class to build instructions"""
    
    @staticmethod
    def jump(address: int) -> Instruction:
        return Instruction(Opcode.JUMP, [address])
    
    @staticmethod
    def jump_if_true(cond_addr: int, jump_addr: int) -> Instruction:
        return Instruction(Opcode.JUMPIF_TRUE, [cond_addr, jump_addr])
    
    @staticmethod
    def jump_if_false(cond_addr: int, jump_addr: int) -> Instruction:
        return Instruction(Opcode.JUMPIF_FALSE, [cond_addr, jump_addr])
    
    @staticmethod
    def call(func_id: int, param_count: int = 0) -> Instruction:
        return Instruction(Opcode.CALL, [func_id, param_count])
    
    @staticmethod
    def ret() -> Instruction:
        return Instruction(Opcode.RET, [])
    
    @staticmethod
    def load_const(value: Any) -> Instruction:
        return Instruction(Opcode.LOAD_CONST, [value])
    
    @staticmethod
    def load_var(address: int) -> Instruction:
        return Instruction(Opcode.LOAD_VAR, [address])
    
    @staticmethod
    def store_var(address: int) -> Instruction:
        return Instruction(Opcode.STORE_VAR, [address])
    
    @staticmethod
    def load_struct_member(base_addr: int, offset: int) -> Instruction:
        return Instruction(Opcode.LOAD_STRUCT_MEMBER, [base_addr, offset])
    
    @staticmethod
    def store_struct_member(base_addr: int, offset: int) -> Instruction:
        return Instruction(Opcode.STORE_STRUCT_MEMBER, [base_addr, offset])
    
    @staticmethod
    def load_struct_member_bit(base_addr: int, byte_offset: int, bit_offset: int, width: int) -> Instruction:
        return Instruction(Opcode.LOAD_STRUCT_MEMBER_BIT, [base_addr, byte_offset, bit_offset, width])
    
    @staticmethod
    def store_struct_member_bit(base_addr: int, byte_offset: int, bit_offset: int, width: int) -> Instruction:
        return Instruction(Opcode.STORE_STRUCT_MEMBER_BIT, [base_addr, byte_offset, bit_offset, width])
    
    # NEW: Pointer instruction builders
    @staticmethod
    def load_addr(address: int) -> Instruction:
        return Instruction(Opcode.LOAD_ADDR, [address])
    
    @staticmethod
    def load_deref() -> Instruction:
        return Instruction(Opcode.LOAD_DEREF, [])
    
    @staticmethod
    def store_deref() -> Instruction:
        return Instruction(Opcode.STORE_DEREF, [])
    
    @staticmethod
    def comment(text: str) -> Instruction:
        return Instruction(Opcode.COMMENT, [text])
    
    @staticmethod
    def add() -> Instruction:
        return Instruction(Opcode.ADD, [])
    
    @staticmethod
    def sub() -> Instruction:
        return Instruction(Opcode.SUB, [])
    
    @staticmethod
    def mul() -> Instruction:
        return Instruction(Opcode.MUL, [])
    
    @staticmethod
    def div() -> Instruction:
        return Instruction(Opcode.DIV, [])
    
    @staticmethod
    def mod() -> Instruction:
        return Instruction(Opcode.MOD, [])
    
    @staticmethod
    def and_op() -> Instruction:
        return Instruction(Opcode.AND, [])
    
    @staticmethod
    def or_op() -> Instruction:
        return Instruction(Opcode.OR, [])
    
    @staticmethod
    def not_op() -> Instruction:
        return Instruction(Opcode.NOT, [])
    
    @staticmethod
    def xor() -> Instruction:
        return Instruction(Opcode.XOR, [])
    
    @staticmethod
    def eq() -> Instruction:
        return Instruction(Opcode.EQ, [])
    
    @staticmethod
    def neq() -> Instruction:
        return Instruction(Opcode.NEQ, [])
    
    @staticmethod
    def lt() -> Instruction:
        return Instruction(Opcode.LT, [])
    
    @staticmethod
    def lte() -> Instruction:
        return Instruction(Opcode.LTE, [])
    
    @staticmethod
    def gt() -> Instruction:
        return Instruction(Opcode.GT, [])
    
    @staticmethod
    def gte() -> Instruction:
        return Instruction(Opcode.GTE, [])
    
    @staticmethod
    def alloc_var(size: int) -> Instruction:
        return Instruction(Opcode.ALLOC_VAR, [size])
    
    @staticmethod
    def free_var(address: int) -> Instruction:
        return Instruction(Opcode.FREE_VAR, [address])
    
    @staticmethod
    def alloc_struct(size: int) -> Instruction:
        return Instruction(Opcode.ALLOC_STRUCT, [size])
    
    @staticmethod
    def rtos_create_task(func_id: int, name_id: int, stack_size: int, priority: int, core: int) -> Instruction:
        return Instruction(Opcode.RTOS_CREATE_TASK, [func_id, name_id, stack_size, priority, core])
    
    @staticmethod
    def rtos_delete_task(task_handle_addr: int) -> Instruction:
        return Instruction(Opcode.RTOS_DELETE_TASK, [task_handle_addr])
    
    @staticmethod
    def rtos_delay_ms(milliseconds: int) -> Instruction:
        return Instruction(Opcode.RTOS_DELAY_MS, [milliseconds])
    
    @staticmethod
    def rtos_semaphore_create() -> Instruction:
        return Instruction(Opcode.RTOS_SEMAPHORE_CREATE, [])
    
    @staticmethod
    def rtos_semaphore_take(handle: int, timeout: int) -> Instruction:
        return Instruction(Opcode.RTOS_SEMAPHORE_TAKE, [handle, timeout])
    
    @staticmethod
    def rtos_semaphore_give(handle: int) -> Instruction:
        return Instruction(Opcode.RTOS_SEMAPHORE_GIVE, [handle])
    
    @staticmethod
    def rtos_yield() -> Instruction:
        return Instruction(Opcode.RTOS_YIELD, [])
    
    @staticmethod
    def rtos_suspend_task(task_handle: int) -> Instruction:
        return Instruction(Opcode.RTOS_SUSPEND_TASK, [task_handle])
    
    @staticmethod
    def rtos_resume_task(task_handle: int) -> Instruction:
        return Instruction(Opcode.RTOS_RESUME_TASK, [task_handle])
    
    @staticmethod
    def hw_gpio_init(pin: int, mode: int) -> Instruction:
        return Instruction(Opcode.HW_GPIO_INIT, [pin, mode])
    
    @staticmethod
    def hw_gpio_set(pin: int, value: int) -> Instruction:
        return Instruction(Opcode.HW_GPIO_SET, [pin, value])
    
    @staticmethod
    def hw_gpio_get(pin: int) -> Instruction:
        return Instruction(Opcode.HW_GPIO_GET, [pin])
    
    @staticmethod
    def hw_timer_init(timer_id: int, mode: int, freq: int) -> Instruction:
        return Instruction(Opcode.HW_TIMER_INIT, [timer_id, mode, freq])
    
    @staticmethod
    def hw_timer_start(timer_id: int) -> Instruction:
        return Instruction(Opcode.HW_TIMER_START, [timer_id])
    
    @staticmethod
    def hw_timer_stop(timer_id: int) -> Instruction:
        return Instruction(Opcode.HW_TIMER_STOP, [timer_id])
    
    @staticmethod
    def hw_timer_set_pwm_duty(timer_id: int, duty: int) -> Instruction:
        return Instruction(Opcode.HW_TIMER_SET_PWM_DUTY, [timer_id, duty])
    
    @staticmethod
    def hw_adc_init(pin: int) -> Instruction:
        return Instruction(Opcode.HW_ADC_INIT, [pin])
    
    @staticmethod
    def hw_adc_read(pin: int) -> Instruction:
        return Instruction(Opcode.HW_ADC_READ, [pin])
    
    @staticmethod
    def hw_uart_write(buffer_addr: int, length: int) -> Instruction:
        return Instruction(Opcode.HW_UART_WRITE, [buffer_addr, length])
    
    @staticmethod
    def hw_spi_transfer(tx_addr: int, rx_addr: int, length: int) -> Instruction:
        return Instruction(Opcode.HW_SPI_TRANSFER, [tx_addr, rx_addr, length])
    
    @staticmethod
    def hw_i2c_write(addr: int, data: int) -> Instruction:
        return Instruction(Opcode.HW_I2C_WRITE, [addr, data])
    
    @staticmethod
    def hw_i2c_read(addr: int, reg: int) -> Instruction:
        return Instruction(Opcode.HW_I2C_READ, [addr, reg])
    
    @staticmethod
    def dbg_print(string_id: int) -> Instruction:
        return Instruction(Opcode.DBG_PRINT, [string_id])
    
    @staticmethod
    def dbg_printf(format_string_id: int, arg_count: int) -> Instruction:
        return Instruction(Opcode.DBG_PRINTF, [format_string_id, arg_count])
    
    @staticmethod
    def dbg_breakpoint() -> Instruction:
        return Instruction(Opcode.DBG_BREAKPOINT, [])
    
    @staticmethod
    def syscall(call_id: int, *args) -> Instruction:
        return Instruction(Opcode.SYSCALL, [call_id] + list(args))
    
    @staticmethod
    def halt() -> Instruction:
        return Instruction(Opcode.HALT, [])
    
    @staticmethod
    def nop() -> Instruction:
        return Instruction(Opcode.NOP, [])

# Instruction metadata for validation and formatting
INSTRUCTION_INFO = {
    Opcode.JUMP: {"operands": 1, "description": "Unconditional jump"},
    Opcode.JUMPIF_TRUE: {"operands": 2, "description": "Jump if condition is true"},
    Opcode.JUMPIF_FALSE: {"operands": 2, "description": "Jump if condition is false"},
    Opcode.CALL: {"operands": 2, "description": "Call function with parameter count"},
    Opcode.RET: {"operands": 0, "description": "Return from function"},
    
    Opcode.LOAD_CONST: {"operands": 1, "description": "Load constant"},
    Opcode.LOAD_VAR: {"operands": 1, "description": "Load variable"},
    Opcode.STORE_VAR: {"operands": 1, "description": "Store variable"},
    Opcode.LOAD_STRUCT_MEMBER: {"operands": 2, "description": "Load struct member"},
    Opcode.STORE_STRUCT_MEMBER: {"operands": 2, "description": "Store struct member"},
    Opcode.LOAD_STRUCT_MEMBER_BIT: {"operands": 4, "description": "Load bit-field"},
    Opcode.STORE_STRUCT_MEMBER_BIT: {"operands": 4, "description": "Store bit-field"},
    
    Opcode.ADD: {"operands": 0, "description": "Add two values"},
    Opcode.SUB: {"operands": 0, "description": "Subtract two values"},
    Opcode.MUL: {"operands": 0, "description": "Multiply two values"},
    Opcode.DIV: {"operands": 0, "description": "Divide two values"},
    Opcode.MOD: {"operands": 0, "description": "Modulo operation"},
    Opcode.AND: {"operands": 0, "description": "Logical AND"},
    Opcode.OR: {"operands": 0, "description": "Logical OR"},
    Opcode.NOT: {"operands": 0, "description": "Logical NOT"},
    Opcode.XOR: {"operands": 0, "description": "Logical XOR"},
    
    Opcode.EQ: {"operands": 0, "description": "Equal comparison"},
    Opcode.NEQ: {"operands": 0, "description": "Not equal comparison"},
    Opcode.LT: {"operands": 0, "description": "Less than comparison"},
    Opcode.LTE: {"operands": 0, "description": "Less than or equal comparison"},
    Opcode.GT: {"operands": 0, "description": "Greater than comparison"},
    Opcode.GTE: {"operands": 0, "description": "Greater than or equal comparison"},
    
    Opcode.ALLOC_VAR: {"operands": 1, "description": "Allocate variable"},
    Opcode.FREE_VAR: {"operands": 1, "description": "Free variable"},
    Opcode.ALLOC_STRUCT: {"operands": 1, "description": "Allocate struct"},
    
    Opcode.RTOS_CREATE_TASK: {"operands": 5, "description": "Create RTOS task"},
    Opcode.RTOS_DELETE_TASK: {"operands": 1, "description": "Delete RTOS task"},
    Opcode.RTOS_DELAY_MS: {"operands": 1, "description": "Delay milliseconds"},
    Opcode.RTOS_SEMAPHORE_CREATE: {"operands": 0, "description": "Create semaphore"},
    Opcode.RTOS_SEMAPHORE_TAKE: {"operands": 2, "description": "Take semaphore"},
    Opcode.RTOS_SEMAPHORE_GIVE: {"operands": 1, "description": "Give semaphore"},
    Opcode.RTOS_YIELD: {"operands": 0, "description": "Yield task"},
    Opcode.RTOS_SUSPEND_TASK: {"operands": 1, "description": "Suspend task"},
    Opcode.RTOS_RESUME_TASK: {"operands": 1, "description": "Resume task"},
    
    Opcode.HW_GPIO_INIT: {"operands": 2, "description": "Initialize GPIO"},
    Opcode.HW_GPIO_SET: {"operands": 2, "description": "Set GPIO value"},
    Opcode.HW_GPIO_GET: {"operands": 1, "description": "Get GPIO value"},
    
    Opcode.HW_TIMER_INIT: {"operands": 3, "description": "Initialize timer"},
    Opcode.HW_TIMER_START: {"operands": 1, "description": "Start timer"},
    Opcode.HW_TIMER_STOP: {"operands": 1, "description": "Stop timer"},
    Opcode.HW_TIMER_SET_PWM_DUTY: {"operands": 2, "description": "Set PWM duty"},
    
    Opcode.HW_ADC_INIT: {"operands": 1, "description": "Initialize ADC"},
    Opcode.HW_ADC_READ: {"operands": 1, "description": "Read ADC value"},
    
    Opcode.HW_UART_WRITE: {"operands": 2, "description": "Write UART data"},
    Opcode.HW_SPI_TRANSFER: {"operands": 3, "description": "SPI transfer"},
    Opcode.HW_I2C_WRITE: {"operands": 2, "description": "Write I2C data"},
    Opcode.HW_I2C_READ: {"operands": 2, "description": "Read I2C data"},
    
    Opcode.DBG_PRINT: {"operands": 1, "description": "Debug print"},
    Opcode.DBG_PRINTF: {"operands": 2, "description": "Debug formatted print"},
    Opcode.DBG_BREAKPOINT: {"operands": 0, "description": "Debug breakpoint"},
    Opcode.SYSCALL: {"operands": -1, "description": "System call"},
    
    Opcode.HALT: {"operands": 0, "description": "Halt execution"},
    Opcode.NOP: {"operands": 0, "description": "No operation"},
}
