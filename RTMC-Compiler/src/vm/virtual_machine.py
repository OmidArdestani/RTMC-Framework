"""
Virtual Machine for RT-Micro-C Language
Executes bytecode programs with RTOS and hardware support.
"""

import time
import threading
from typing import List, Dict, Any, Optional, Callable
from collections import deque
from src.bytecode.generator import BytecodeProgram
from src.bytecode.instructions import Instruction, Opcode
from dataclasses import dataclass
from enum import Enum, auto

class VMError(Exception):
    """Virtual machine error"""
    pass

class TaskState(Enum):
    """RTOS task states"""
    READY = auto()
    RUNNING = auto()
    BLOCKED = auto()
    SUSPENDED = auto()
    DELETED = auto()

@dataclass
class Task:
    """RTOS task representation"""
    id: int
    name: str
    func_addr: int
    stack_size: int
    priority: int
    core: int
    state: TaskState
    thread: Optional[threading.Thread] = None
    stack: List[Any] = None
    pc: int = 0
    
    def __post_init__(self):
        if self.stack is None:
            self.stack = []

@dataclass
class Semaphore:
    """RTOS semaphore representation"""
    id: int
    count: int
    max_count: int
    waiting_tasks: List[int]
    
    def __post_init__(self):
        if not hasattr(self, 'waiting_tasks'):
            self.waiting_tasks = []

@dataclass
class MessageQueue:
    """Message queue for inter-task communication"""
    id: int
    name: str
    message_type: str
    queue: deque
    max_size: int = 10
    waiting_senders: List[int] = None  # Task IDs waiting to send
    waiting_receivers: List[int] = None  # Task IDs waiting to receive
    waiting_timeouts: Dict[int, float] = None  # Task ID -> timeout timestamp
    
    def __post_init__(self):
        if self.waiting_senders is None:
            self.waiting_senders = []
        if self.waiting_receivers is None:
            self.waiting_receivers = []
        if self.waiting_timeouts is None:
            self.waiting_timeouts = {}

class HardwareSimulator:
    """Simulates hardware peripherals"""
    
    def __init__(self):
        self.gpio_pins: Dict[int, Dict[str, Any]] = {}
        self.timers: Dict[int, Dict[str, Any]] = {}
        self.adc_channels: Dict[int, int] = {}
        self.uart_buffer: List[bytes] = []
        self.i2c_devices: Dict[int, Dict[int, int]] = {}
        self.spi_buffer: List[bytes] = []
    
    def gpio_init(self, pin: int, mode: int):
        """Initialize GPIO pin"""
        self.gpio_pins[pin] = {
            'mode': mode,  # 0=input, 1=output
            'value': 0,
            'pull': 0      # 0=none, 1=up, 2=down
        }
        print(f"GPIO{pin} initialized as {'OUTPUT' if mode == 1 else 'INPUT'}")
    
    def gpio_set(self, pin: int, value: int):
        """Set GPIO pin value"""
        if pin not in self.gpio_pins:
            raise VMError(f"GPIO{pin} not initialized")
        
        if self.gpio_pins[pin]['mode'] != 1:
            raise VMError(f"GPIO{pin} not configured as output")
        
        self.gpio_pins[pin]['value'] = value
        print(f"GPIO{pin} set to {value}")
    
    def gpio_get(self, pin: int) -> int:
        """Get GPIO pin value"""
        if pin not in self.gpio_pins:
            raise VMError(f"GPIO{pin} not initialized")
        
        # Simulate reading (return random value for inputs)
        if self.gpio_pins[pin]['mode'] == 0:
            import random
            value = random.randint(0, 1)
            self.gpio_pins[pin]['value'] = value
            print(f"GPIO{pin} read: {value}")
            return value
        else:
            return self.gpio_pins[pin]['value']
    
    def timer_init(self, timer_id: int, mode: int, freq: int):
        """Initialize timer"""
        self.timers[timer_id] = {
            'mode': mode,
            'frequency': freq,
            'running': False,
            'count': 0,
            'pwm_duty': 0
        }
        print(f"Timer{timer_id} initialized: mode={mode}, freq={freq}Hz")
    
    def timer_start(self, timer_id: int):
        """Start timer"""
        if timer_id not in self.timers:
            raise VMError(f"Timer{timer_id} not initialized")
        
        self.timers[timer_id]['running'] = True
        print(f"Timer{timer_id} started")
    
    def timer_stop(self, timer_id: int):
        """Stop timer"""
        if timer_id not in self.timers:
            raise VMError(f"Timer{timer_id} not initialized")
        
        self.timers[timer_id]['running'] = False
        print(f"Timer{timer_id} stopped")
    
    def timer_set_pwm_duty(self, timer_id: int, duty: int):
        """Set PWM duty cycle"""
        if timer_id not in self.timers:
            raise VMError(f"Timer{timer_id} not initialized")
        
        self.timers[timer_id]['pwm_duty'] = duty
        print(f"Timer{timer_id} PWM duty set to {duty}%")
    
    def adc_init(self, pin: int):
        """Initialize ADC channel"""
        self.adc_channels[pin] = 0
        print(f"ADC{pin} initialized")
    
    def adc_read(self, pin: int) -> int:
        """Read ADC value"""
        if pin not in self.adc_channels:
            raise VMError(f"ADC{pin} not initialized")
        
        # Simulate ADC reading
        import random
        value = random.randint(0, 4095)  # 12-bit ADC
        self.adc_channels[pin] = value
        print(f"ADC{pin} read: {value}")
        return value
    
    def uart_write(self, data: bytes):
        """Write data to UART"""
        self.uart_buffer.append(data)
        print(f"UART TX: {data.hex()}")
    
    def spi_transfer(self, tx_data: bytes) -> bytes:
        """SPI transfer"""
        self.spi_buffer.append(tx_data)
        # Simulate response
        rx_data = bytes([0xFF] * len(tx_data))
        print(f"SPI TX: {tx_data.hex()}, RX: {rx_data.hex()}")
        return rx_data
    
    def i2c_write(self, addr: int, data: int):
        """Write data to I2C device"""
        if addr not in self.i2c_devices:
            self.i2c_devices[addr] = {}
        
        # Simulate register write
        self.i2c_devices[addr][0] = data
        print(f"I2C write to 0x{addr:02X}: 0x{data:02X}")
    
    def i2c_read(self, addr: int, reg: int) -> int:
        """Read data from I2C device"""
        if addr not in self.i2c_devices:
            self.i2c_devices[addr] = {}
        
        # Simulate register read
        value = self.i2c_devices[addr].get(reg, 0)
        print(f"I2C read from 0x{addr:02X} reg 0x{reg:02X}: 0x{value:02X}")
        return value

class VirtualMachine:
    """RT-Micro-C Virtual Machine"""
    
    def __init__(self, debug: bool = False, trace: bool = False):
        self.debug = debug
        self.trace = trace
        
        # Program state
        self.program: Optional[BytecodeProgram] = None
        self.pc = 0  # Program counter
        self.stack: List[Any] = []
        self.call_stack: List[int] = []
        self.memory: Dict[int, Any] = {}
        self.running = False
        
        # RTOS state
        self.tasks: Dict[int, Task] = {}
        self.semaphores: Dict[int, Semaphore] = {}
        self.message_queues: Dict[int, MessageQueue] = {}
        self.current_task_id = 0
        self.task_counter = 0
        self.semaphore_counter = 0
        self.message_queue_counter = 0
        self.scheduler_running = False
        
        # Hardware simulator
        self.hardware = HardwareSimulator()
        
        # Instruction handlers
        self.handlers = {
            Opcode.JUMP: self._handle_jump,
            Opcode.JUMPIF_TRUE: self._handle_jumpif_true,
            Opcode.JUMPIF_FALSE: self._handle_jumpif_false,
            Opcode.CALL: self._handle_call,
            Opcode.RET: self._handle_ret,
            
            Opcode.LOAD_CONST: self._handle_load_const,
            Opcode.LOAD_VAR: self._handle_load_var,
            Opcode.STORE_VAR: self._handle_store_var,
            Opcode.LOAD_STRUCT_MEMBER: self._handle_load_struct_member,
            Opcode.STORE_STRUCT_MEMBER: self._handle_store_struct_member,
            Opcode.LOAD_STRUCT_MEMBER_BIT: self._handle_load_struct_member_bit,
            Opcode.STORE_STRUCT_MEMBER_BIT: self._handle_store_struct_member_bit,
            
            Opcode.ADD: self._handle_add,
            Opcode.SUB: self._handle_sub,
            Opcode.MUL: self._handle_mul,
            Opcode.DIV: self._handle_div,
            Opcode.MOD: self._handle_mod,
            Opcode.AND: self._handle_and,
            Opcode.OR: self._handle_or,
            Opcode.NOT: self._handle_not,
            Opcode.XOR: self._handle_xor,
            
            Opcode.EQ: self._handle_eq,
            Opcode.NEQ: self._handle_neq,
            Opcode.LT: self._handle_lt,
            Opcode.LTE: self._handle_lte,
            Opcode.GT: self._handle_gt,
            Opcode.GTE: self._handle_gte,
            
            Opcode.ALLOC_VAR: self._handle_alloc_var,
            Opcode.FREE_VAR: self._handle_free_var,
            Opcode.ALLOC_STRUCT: self._handle_alloc_struct,
            
            # RTOS instructions
            Opcode.RTOS_CREATE_TASK: self._handle_rtos_create_task,
            Opcode.RTOS_DELETE_TASK: self._handle_rtos_delete_task,
            Opcode.RTOS_DELAY_MS: self._handle_rtos_delay_ms,
            Opcode.RTOS_SEMAPHORE_CREATE: self._handle_rtos_semaphore_create,
            Opcode.RTOS_SEMAPHORE_TAKE: self._handle_rtos_semaphore_take,
            Opcode.RTOS_SEMAPHORE_GIVE: self._handle_rtos_semaphore_give,
            Opcode.RTOS_YIELD: self._handle_rtos_yield,
            Opcode.RTOS_SUSPEND_TASK: self._handle_rtos_suspend_task,
            Opcode.RTOS_RESUME_TASK: self._handle_rtos_resume_task,
            
            # Message passing instructions  
            Opcode.MSG_DECLARE: self._handle_msg_declare,
            Opcode.MSG_SEND: self._handle_msg_send,
            Opcode.MSG_RECV: self._handle_msg_recv,
            
            # Hardware instructions
            Opcode.HW_GPIO_INIT: self._handle_hw_gpio_init,
            Opcode.HW_GPIO_SET: self._handle_hw_gpio_set,
            Opcode.HW_GPIO_GET: self._handle_hw_gpio_get,
            Opcode.HW_TIMER_INIT: self._handle_hw_timer_init,
            Opcode.HW_TIMER_START: self._handle_hw_timer_start,
            Opcode.HW_TIMER_STOP: self._handle_hw_timer_stop,
            Opcode.HW_TIMER_SET_PWM_DUTY: self._handle_hw_timer_set_pwm_duty,
            Opcode.HW_ADC_INIT: self._handle_hw_adc_init,
            Opcode.HW_ADC_READ: self._handle_hw_adc_read,
            Opcode.HW_UART_WRITE: self._handle_hw_uart_write,
            Opcode.HW_SPI_TRANSFER: self._handle_hw_spi_transfer,
            Opcode.HW_I2C_WRITE: self._handle_hw_i2c_write,
            Opcode.HW_I2C_READ: self._handle_hw_i2c_read,
            
            # Debug instructions
            Opcode.DBG_PRINT: self._handle_dbg_print,
            Opcode.DBG_BREAKPOINT: self._handle_dbg_breakpoint,
            
            Opcode.HALT: self._handle_halt,
            Opcode.NOP: self._handle_nop,
        }
    
    def load_program(self, program: BytecodeProgram):
        """Load a bytecode program"""
        self.program = program
        self.pc = 0
        self.stack = []
        self.call_stack = []
        self.memory = {}
        
        # Initialize main task
        if 'main' in program.functions:
            main_addr = program.functions['main']
            self.create_main_task(main_addr)
    
    def create_main_task(self, main_addr: int):
        """Create the main task"""
        task = Task(
            id=0,
            name="main",
            func_addr=main_addr,
            stack_size=1024,
            priority=5,
            core=0,
            state=TaskState.READY,
            pc=main_addr
        )
        self.tasks[0] = task
        self.current_task_id = 0
    
    def run(self):
        """Run the virtual machine"""
        self.running = True
        
        if not self.program:
            raise VMError("No program loaded")
        
        # Start with main task
        if 0 in self.tasks:
            self.pc = self.tasks[0].func_addr
            self.current_task_id = 0
        
        try:
            while self.running and self.pc < len(self.program.instructions):
                instruction = self.program.instructions[self.pc]
                
                if self.trace:
                    self._trace_instruction(instruction)
                
                self._execute_instruction(instruction)
                
                if instruction.opcode not in [Opcode.JUMP, Opcode.JUMPIF_TRUE, 
                                            Opcode.JUMPIF_FALSE, Opcode.CALL, Opcode.RET]:
                    self.pc += 1
                
                # Simple task switching (cooperative)
                if instruction.opcode in [Opcode.RTOS_YIELD, Opcode.RTOS_DELAY_MS]:
                    self._yield_task()
        
        except KeyboardInterrupt:
            print("\\nExecution interrupted by user")
        except Exception as e:
            print(f"Runtime error at PC {self.pc}: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            self.running = False
    
    def _execute_instruction(self, instruction: Instruction):
        """Execute a single instruction"""
        handler = self.handlers.get(instruction.opcode)
        if handler:
            handler(instruction)
        else:
            raise VMError(f"Unknown opcode: {instruction.opcode}")
    
    def _trace_instruction(self, instruction: Instruction):
        """Trace instruction execution"""
        stack_info = f"Stack: {self.stack[-3:] if len(self.stack) > 3 else self.stack}"
        print(f"PC:{self.pc:4d} {instruction} {stack_info}")
    
    def _check_timeouts(self):
        """Check for timed out message receives"""
        current_time = time.time()
        
        for queue in self.message_queues.values():
            timed_out_tasks = []
            
            # Check which tasks have timed out
            for task_id, timeout_time in queue.waiting_timeouts.items():
                if current_time >= timeout_time:
                    timed_out_tasks.append(task_id)
            
            # Handle timed out tasks
            for task_id in timed_out_tasks:
                if task_id in self.tasks and task_id in queue.waiting_receivers:
                    # Remove from waiting lists
                    queue.waiting_receivers.remove(task_id)
                    del queue.waiting_timeouts[task_id]
                    
                    # Wake up the task and push 0 (timeout return value)
                    self.tasks[task_id].state = TaskState.READY
                    
                    # Save current state and switch to timed out task temporarily
                    # to push the timeout return value
                    saved_task = self.current_task_id
                    saved_stack = self.stack
                    
                    self.current_task_id = task_id
                    self.stack = self.tasks[task_id].stack
                    self._push(0)  # Timeout return value
                    self.tasks[task_id].stack = self.stack
                    
                    # Restore previous state
                    self.current_task_id = saved_task
                    self.stack = saved_stack
                    
                    if self.debug:
                        print(f"Task ID: {task_id} timed out waiting for message")

    def _yield_task(self):
        """Yield current task (simplified scheduling)"""
        # Check for message receive timeouts
        self._check_timeouts()
        
        # In a real RTOS, this would be more sophisticated
        time.sleep(0.001)  # Small delay to prevent busy waiting
    
    # Stack operations
    def _push(self, value: Any):
        """Push value onto stack"""
        self.stack.append(value)
    
    def _pop(self) -> Any:
        """Pop value from stack"""
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()
    
    def _peek(self) -> Any:
        """Peek at top of stack"""
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack[-1]
    
    # Instruction handlers
    
    def _handle_jump(self, instruction: Instruction):
        """Handle JUMP instruction"""
        self.pc = instruction.operands[0]
    
    def _handle_jumpif_true(self, instruction: Instruction):
        """Handle JUMPIF_TRUE instruction"""
        condition = self._pop()
        if condition:
            self.pc = instruction.operands[0]
        else:
            self.pc += 1
    
    def _handle_jumpif_false(self, instruction: Instruction):
        """Handle JUMPIF_FALSE instruction"""
        condition = self._pop()
        if not condition:
            self.pc = instruction.operands[0]
        else:
            self.pc += 1
    
    def _handle_call(self, instruction: Instruction):
        """Handle CALL instruction"""
        self.call_stack.append(self.pc + 1)
        self.pc = instruction.operands[0]
    
    def _handle_ret(self, instruction: Instruction):
        """Handle RET instruction"""
        if self.call_stack:
            self.pc = self.call_stack.pop()
        else:
            self.running = False
    
    def _handle_load_const(self, instruction: Instruction):
        """Handle LOAD_CONST instruction"""
        const_idx = instruction.operands[0]
        if const_idx < len(self.program.constants):
            self._push(self.program.constants[const_idx])
        else:
            self._push(0)
    
    def _handle_load_var(self, instruction: Instruction):
        """Handle LOAD_VAR instruction"""
        address = instruction.operands[0]
        value = self.memory.get(address, 0)
        self._push(value)
    
    def _handle_store_var(self, instruction: Instruction):
        """Handle STORE_VAR instruction"""
        address = instruction.operands[0]
        value = self._pop()
        self.memory[address] = value
    
    def _handle_load_struct_member(self, instruction: Instruction):
        """Handle LOAD_STRUCT_MEMBER instruction"""
        base_addr = instruction.operands[0]
        offset = instruction.operands[1]
        value = self.memory.get(base_addr + offset, 0)
        self._push(value)
    
    def _handle_store_struct_member(self, instruction: Instruction):
        """Handle STORE_STRUCT_MEMBER instruction"""
        base_addr = instruction.operands[0]
        offset = instruction.operands[1]
        value = self._pop()
        self.memory[base_addr + offset] = value
    
    def _handle_load_struct_member_bit(self, instruction: Instruction):
        """Handle LOAD_STRUCT_MEMBER_BIT instruction for bit-fields"""
        base_addr = instruction.operands[0]
        byte_offset = instruction.operands[1]
        bit_offset = instruction.operands[2]
        bit_width = instruction.operands[3]
        
        # Load the containing word
        word_value = self.memory.get(base_addr + byte_offset, 0)
        
        # Extract the bit-field value
        # Create a mask with 'bit_width' number of 1s
        mask = (1 << bit_width) - 1
        # Shift the word right to align the field, then mask
        field_value = (word_value >> bit_offset) & mask
        
        self._push(field_value)
    
    def _handle_store_struct_member_bit(self, instruction: Instruction):
        """Handle STORE_STRUCT_MEMBER_BIT instruction for bit-fields"""
        base_addr = instruction.operands[0]
        byte_offset = instruction.operands[1]
        bit_offset = instruction.operands[2]
        bit_width = instruction.operands[3]
        new_value = self._pop()
        
        # Load the current word
        word_value = self.memory.get(base_addr + byte_offset, 0)
        
        # Create a mask to clear the bit-field
        mask = (1 << bit_width) - 1
        clear_mask = ~(mask << bit_offset)
        
        # Clear the bit-field and set the new value
        word_value = (word_value & clear_mask) | ((new_value & mask) << bit_offset)
        
        # Store the modified word back
        self.memory[base_addr + byte_offset] = word_value

    def _handle_add(self, instruction: Instruction):
        """Handle ADD instruction"""
        b = self._pop()
        a = self._pop()
        self._push(a + b)
    
    def _handle_sub(self, instruction: Instruction):
        """Handle SUB instruction"""
        b = self._pop()
        a = self._pop()
        self._push(a - b)
    
    def _handle_mul(self, instruction: Instruction):
        """Handle MUL instruction"""
        b = self._pop()
        a = self._pop()
        self._push(a * b)
    
    def _handle_div(self, instruction: Instruction):
        """Handle DIV instruction"""
        b = self._pop()
        a = self._pop()
        if b == 0:
            raise VMError("Division by zero")
        self._push(a // b)
    
    def _handle_mod(self, instruction: Instruction):
        """Handle MOD instruction"""
        b = self._pop()
        a = self._pop()
        if b == 0:
            raise VMError("Modulo by zero")
        self._push(a % b)
    
    def _handle_and(self, instruction: Instruction):
        """Handle AND instruction"""
        b = self._pop()
        a = self._pop()
        self._push(a and b)
    
    def _handle_or(self, instruction: Instruction):
        """Handle OR instruction"""
        b = self._pop()
        a = self._pop()
        self._push(a or b)
    
    def _handle_not(self, instruction: Instruction):
        """Handle NOT instruction"""
        a = self._pop()
        self._push(not a)
    
    def _handle_xor(self, instruction: Instruction):
        """Handle XOR instruction"""
        b = self._pop()
        a = self._pop()
        self._push(a ^ b)
    
    def _handle_eq(self, instruction: Instruction):
        """Handle EQ instruction"""
        b = self._pop()
        a = self._pop()
        self._push(1 if a == b else 0)
    
    def _handle_neq(self, instruction: Instruction):
        """Handle NEQ instruction"""
        b = self._pop()
        a = self._pop()
        self._push(1 if a != b else 0)
    
    def _handle_lt(self, instruction: Instruction):
        """Handle LT instruction"""
        b = self._pop()
        a = self._pop()
        self._push(1 if a < b else 0)
    
    def _handle_lte(self, instruction: Instruction):
        """Handle LTE instruction"""
        b = self._pop()
        a = self._pop()
        self._push(1 if a <= b else 0)
    
    def _handle_gt(self, instruction: Instruction):
        """Handle GT instruction"""
        b = self._pop()
        a = self._pop()
        self._push(1 if a > b else 0)
    
    def _handle_gte(self, instruction: Instruction):
        """Handle GTE instruction"""
        b = self._pop()
        a = self._pop()
        self._push(1 if a >= b else 0)
    
    def _handle_alloc_var(self, instruction: Instruction):
        """Handle ALLOC_VAR instruction"""
        size = instruction.operands[0]
        # Simplified allocation - just return next available address
        address = len(self.memory)
        for i in range(size):
            self.memory[address + i] = 0
        self._push(address)
    
    def _handle_free_var(self, instruction: Instruction):
        """Handle FREE_VAR instruction"""
        address = instruction.operands[0]
        # Simplified - just mark as free (in real implementation, manage free list)
        if address in self.memory:
            del self.memory[address]
    
    def _handle_alloc_struct(self, instruction: Instruction):
        """Handle ALLOC_STRUCT instruction"""
        size = instruction.operands[0]
        address = len(self.memory)
        for i in range(size):
            self.memory[address + i] = 0
        self._push(address)
    
    # RTOS instruction handlers
    
    def _handle_rtos_create_task(self, instruction: Instruction):
        """Handle RTOS_CREATE_TASK instruction"""
        core = self._pop()
        priority = self._pop()
        stack_size = self._pop()
        name_id = self._pop()
        func_id = self._pop()
        
        # Get task name from string pool
        task_name = self.program.strings[name_id] if name_id < len(self.program.strings) else f"Task{self.task_counter}"
        
        # Create new task
        task = Task(
            id=self.task_counter,
            name=task_name,
            func_addr=func_id,
            stack_size=stack_size,
            priority=priority,
            core=core,
            state=TaskState.READY,
            pc=func_id
        )
        
        self.tasks[self.task_counter] = task
        self.task_counter += 1
        
        print(f"Created task '{task_name}' (ID: {task.id})")
    
    def _handle_rtos_delete_task(self, instruction: Instruction):
        """Handle RTOS_DELETE_TASK instruction"""
        task_id = self._pop()
        
        if task_id in self.tasks:
            self.tasks[task_id].state = TaskState.DELETED
            print(f"Deleted task ID: {task_id}")
        else:
            print(f"Task ID {task_id} not found")
    
    def _handle_rtos_delay_ms(self, instruction: Instruction):
        """Handle RTOS_DELAY_MS instruction"""
        ms = self._pop()
        print(f"Delaying {ms}ms")
        time.sleep(ms / 1000.0)
    
    def _handle_rtos_semaphore_create(self, instruction: Instruction):
        """Handle RTOS_SEMAPHORE_CREATE instruction"""
        semaphore = Semaphore(
            id=self.semaphore_counter,
            count=1,
            max_count=1,
            waiting_tasks=[]
        )
        
        self.semaphores[self.semaphore_counter] = semaphore
        self._push(self.semaphore_counter)
        self.semaphore_counter += 1
        
        print(f"Created semaphore ID: {semaphore.id}")
    
    def _handle_rtos_semaphore_take(self, instruction: Instruction):
        """Handle RTOS_SEMAPHORE_TAKE instruction"""
        timeout = self._pop()
        handle = self._pop()
        
        if handle in self.semaphores:
            semaphore = self.semaphores[handle]
            if semaphore.count > 0:
                semaphore.count -= 1
                self._push(1)  # Success
                print(f"Took semaphore {handle}")
            else:
                self._push(0)  # Failed
                print(f"Failed to take semaphore {handle}")
        else:
            self._push(0)  # Invalid handle
    
    def _handle_rtos_semaphore_give(self, instruction: Instruction):
        """Handle RTOS_SEMAPHORE_GIVE instruction"""
        handle = self._pop()
        
        if handle in self.semaphores:
            semaphore = self.semaphores[handle]
            if semaphore.count < semaphore.max_count:
                semaphore.count += 1
                print(f"Gave semaphore {handle}")
            else:
                print(f"Semaphore {handle} already at max count")
        else:
            print(f"Invalid semaphore handle: {handle}")
    
    def _handle_rtos_yield(self, instruction: Instruction):
        """Handle RTOS_YIELD instruction"""
        print("Task yielding")
        self._yield_task()
    
    def _handle_rtos_suspend_task(self, instruction: Instruction):
        """Handle RTOS_SUSPEND_TASK instruction"""
        task_id = self._pop()
        
        if task_id in self.tasks:
            self.tasks[task_id].state = TaskState.SUSPENDED
            print(f"Suspended task ID: {task_id}")
        else:
            print(f"Task ID {task_id} not found")
    
    def _handle_rtos_resume_task(self, instruction: Instruction):
        """Handle RTOS_RESUME_TASK instruction"""
        task_id = self._pop()
        
        if task_id in self.tasks:
            if self.tasks[task_id].state == TaskState.SUSPENDED:
                self.tasks[task_id].state = TaskState.READY
                print(f"Resumed task ID: {task_id}")
            else:
                print(f"Task ID {task_id} not suspended")
        else:
            print(f"Task ID {task_id} not found")
    
    def _handle_msg_declare(self, instruction: Instruction):
        """Handle MSG_DECLARE instruction"""
        message_id = instruction.operands[0]
        message_type = instruction.operands[1]
        
        # Create new message queue with the specified ID
        queue = MessageQueue(
            id=message_id,
            name=f"MessageQueue_{message_id}",
            message_type=message_type,
            queue=deque(),
            max_size=10  # Default queue size
        )
        
        self.message_queues[message_id] = queue
        if self.debug:
            print(f"Declared message queue ID: {message_id}, Type: {message_type}")
    
    def _handle_msg_send(self, instruction: Instruction):
        """Handle MSG_SEND instruction"""
        message_id = instruction.operands[0]
        payload = self._pop()  # Get the payload from stack
        
        if message_id in self.message_queues:
            queue = self.message_queues[message_id]
            if len(queue.queue) < queue.max_size:
                queue.queue.append(payload)
                
                # Wake up any task waiting to receive
                if queue.waiting_receivers:
                    receiver_id = queue.waiting_receivers.pop(0)
                    if receiver_id in self.tasks:
                        self.tasks[receiver_id].state = TaskState.READY
                        if self.debug:
                            print(f"Woke up receiver task ID: {receiver_id}")
                
                if self.debug:
                    print(f"Sent message to queue ID: {message_id}, payload: {payload}")
            else:
                # Queue is full, block sender (or drop message in this simple implementation)
                if self.debug:
                    print(f"Message queue ID: {message_id} is full, dropping message")
        else:
            raise VMError(f"Invalid message queue ID: {message_id}")
    
    def _handle_msg_recv(self, instruction: Instruction):
        """Handle MSG_RECV instruction with timeout support"""
        message_id = instruction.operands[0]
        
        # Pop timeout value from stack (-1 means blocking, >=0 means timeout in ms)
        timeout_ms = self._pop()
        
        if message_id in self.message_queues:
            queue = self.message_queues[message_id]
            if queue.queue:
                # Message available, return it
                message = queue.queue.popleft()
                self._push(message)
                
                # Wake up any task waiting to send
                if queue.waiting_senders:
                    sender_id = queue.waiting_senders.pop(0)
                    if sender_id in self.tasks:
                        self.tasks[sender_id].state = TaskState.READY
                        if self.debug:
                            print(f"Woke up sender task ID: {sender_id}")
                
                if self.debug:
                    print(f"Received message from queue ID: {message_id}, payload: {message}")
            else:
                # No message available
                task_id = self.current_task_id
                if task_id in self.tasks:
                    if timeout_ms == -1:
                        # Blocking receive - block indefinitely
                        self.tasks[task_id].state = TaskState.BLOCKED
                        queue.waiting_receivers.append(task_id)
                        if self.debug:
                            print(f"Task ID: {task_id} blocked indefinitely, waiting for message")
                        self._yield_task()
                    elif timeout_ms == 0:
                        # Non-blocking receive - return immediately with 0
                        self._push(0)
                        if self.debug:
                            print(f"Non-blocking receive from queue ID: {message_id}, no message available")
                    else:
                        # Timeout receive - block with timeout
                        self.tasks[task_id].state = TaskState.BLOCKED
                        queue.waiting_receivers.append(task_id)
                        queue.waiting_timeouts[task_id] = time.time() + (timeout_ms / 1000.0)
                        if self.debug:
                            print(f"Task ID: {task_id} blocked with timeout {timeout_ms}ms, waiting for message")
                        self._yield_task()
                else:
                    # In non-task context, push 0 as default value
                    self._push(0)
        else:
            raise VMError(f"Invalid message queue ID: {message_id}")

    # Hardware instruction handlers
    
    def _handle_hw_gpio_init(self, instruction: Instruction):
        """Handle HW_GPIO_INIT instruction"""
        mode = self._pop()
        pin = self._pop()
        self.hardware.gpio_init(pin, mode)
    
    def _handle_hw_gpio_set(self, instruction: Instruction):
        """Handle HW_GPIO_SET instruction"""
        value = self._pop()
        pin = self._pop()
        self.hardware.gpio_set(pin, value)
    
    def _handle_hw_gpio_get(self, instruction: Instruction):
        """Handle HW_GPIO_GET instruction"""
        pin = self._pop()
        value = self.hardware.gpio_get(pin)
        self._push(value)
    
    def _handle_hw_timer_init(self, instruction: Instruction):
        """Handle HW_TIMER_INIT instruction"""
        freq = self._pop()
        mode = self._pop()
        timer_id = self._pop()
        self.hardware.timer_init(timer_id, mode, freq)
    
    def _handle_hw_timer_start(self, instruction: Instruction):
        """Handle HW_TIMER_START instruction"""
        timer_id = self._pop()
        self.hardware.timer_start(timer_id)
    
    def _handle_hw_timer_stop(self, instruction: Instruction):
        """Handle HW_TIMER_STOP instruction"""
        timer_id = self._pop()
        self.hardware.timer_stop(timer_id)
    
    def _handle_hw_timer_set_pwm_duty(self, instruction: Instruction):
        """Handle HW_TIMER_SET_PWM_DUTY instruction"""
        duty = self._pop()
        timer_id = self._pop()
        self.hardware.timer_set_pwm_duty(timer_id, duty)
    
    def _handle_hw_adc_init(self, instruction: Instruction):
        """Handle HW_ADC_INIT instruction"""
        pin = self._pop()
        self.hardware.adc_init(pin)
    
    def _handle_hw_adc_read(self, instruction: Instruction):
        """Handle HW_ADC_READ instruction"""
        pin = self._pop()
        value = self.hardware.adc_read(pin)
        self._push(value)
    
    def _handle_hw_uart_write(self, instruction: Instruction):
        """Handle HW_UART_WRITE instruction"""
        length = self._pop()
        buffer_addr = self._pop()
        # Simulate UART write
        data = bytes([self.memory.get(buffer_addr + i, 0) for i in range(length)])
        self.hardware.uart_write(data)
    
    def _handle_hw_spi_transfer(self, instruction: Instruction):
        """Handle HW_SPI_TRANSFER instruction"""
        length = self._pop()
        rx_addr = self._pop()
        tx_addr = self._pop()
        # Simulate SPI transfer
        tx_data = bytes([self.memory.get(tx_addr + i, 0) for i in range(length)])
        rx_data = self.hardware.spi_transfer(tx_data)
        # Store received data
        for i, byte in enumerate(rx_data):
            self.memory[rx_addr + i] = byte
    
    def _handle_hw_i2c_write(self, instruction: Instruction):
        """Handle HW_I2C_WRITE instruction"""
        data = self._pop()
        addr = self._pop()
        self.hardware.i2c_write(addr, data)
    
    def _handle_hw_i2c_read(self, instruction: Instruction):
        """Handle HW_I2C_READ instruction"""
        reg = self._pop()
        addr = self._pop()
        value = self.hardware.i2c_read(addr, reg)
        self._push(value)
    
    def _handle_dbg_print(self, instruction: Instruction):
        """Handle DBG_PRINT instruction"""
        string_id = self._pop()
        if string_id < len(self.program.strings):
            print(f"DEBUG: {self.program.strings[string_id]}")
        else:
            print(f"DEBUG: <invalid string {string_id}>")
    
    def _handle_dbg_breakpoint(self, instruction: Instruction):
        """Handle DBG_BREAKPOINT instruction"""
        print(f"BREAKPOINT at PC {self.pc}")
        if self.debug:
            input("Press Enter to continue...")
    
    def _handle_halt(self, instruction: Instruction):
        """Handle HALT instruction"""
        self.running = False
        print("Program halted")
    
    def _handle_nop(self, instruction: Instruction):
        """Handle NOP instruction"""
        pass  # Do nothing
