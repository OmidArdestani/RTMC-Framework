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
    vm_instance: Optional['VirtualMachine'] = None  # Reference to VM for thread execution
    
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

class TaskContextSharedMaterial:
    """Shared material for task context"""
    
    def __init__(self):
        self.tasks: Dict[int, Task] = {}  # Task ID -> Task object
        self.semaphores: Dict[int, Semaphore] = {}  # Semaphore ID -> Semaphore object
        self.message_queues: Dict[int, MessageQueue] = {}  # Queue ID -> MessageQueue object
        self.hardware = HardwareSimulator()  # Simulated hardware peripherals
        self.tasks ={}
        self.trace = False  # Enable tracing for debugging
        self.debug = False  # Enable debug mode
        self.program: Optional[BytecodeProgram] = None  # Loaded bytecode program
        self.hwd_simulator = None
        self.task_counter = 0
        self.semaphore_counter = 0
        self.message_queue_counter = 0
        self.memory = {}  # Task-local memory

    def _run_task_thread(self, task: Task):
        """Run a task in its own thread"""
        try:
            print(f"\nStarting task thread: {task.name} (ID: {task.id})")
            task.state = TaskState.RUNNING
            
            # Create a separate VM context for this task
            task_vm = TaskVMContext(task, self)
            
            # Execute the task's run function
            task_vm.execute_function(task.func_addr)
            
        except Exception as e:
            print(f"\nTask {task.name} (ID: {task.id}) encountered error: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            task.state = TaskState.DELETED
            print(f"\nTask {task.name} (ID: {task.id}) finished")
    
    def _start_task_thread(self, task: Task):
        """Start a task as a Python thread"""
        if task.thread is None or not task.thread.is_alive():
            task.thread = threading.Thread(
                target=self._run_task_thread,
                args=(task,),
                name=f"Task-{task.name}-{task.id}"
            )
            task.thread.daemon = True  # Don't block program exit
            task.thread.start()
            print(f"\nStarted task '{task.name}' (ID: {task.id}) as thread")
            
            return True
        
        print(f"\nTask '{task.name}' (ID: {task.id}) is already running")

        return False

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
        print(f"\nGPIO{pin} initialized as {'OUTPUT' if mode == 1 else 'INPUT'}")
    
    def gpio_set(self, pin: int, value: int):
        """Set GPIO pin value"""
        if pin not in self.gpio_pins:
            raise VMError(f"GPIO{pin} not initialized")
        
        if self.gpio_pins[pin]['mode'] != 1:
            raise VMError(f"GPIO{pin} not configured as output")
        
        self.gpio_pins[pin]['value'] = value
        print(f"\nGPIO{pin} set to {value}")
    
    def gpio_get(self, pin: int) -> int:
        """Get GPIO pin value"""
        if pin not in self.gpio_pins:
            raise VMError(f"GPIO{pin} not initialized")
        
        # Simulate reading (return random value for inputs)
        if self.gpio_pins[pin]['mode'] == 0:
            import random
            value = random.randint(0, 1)
            self.gpio_pins[pin]['value'] = value
            print(f"\nGPIO{pin} read: {value}")
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
        print(f"\nTimer{timer_id} initialized: mode={mode}, freq={freq}Hz")
    
    def timer_start(self, timer_id: int):
        """Start timer"""
        if timer_id not in self.timers:
            raise VMError(f"Timer{timer_id} not initialized")
        
        self.timers[timer_id]['running'] = True
        print(f"\nTimer{timer_id} started")
    
    def timer_stop(self, timer_id: int):
        """Stop timer"""
        if timer_id not in self.timers:
            raise VMError(f"Timer{timer_id} not initialized")
        
        self.timers[timer_id]['running'] = False
        print(f"\nTimer{timer_id} stopped")
    
    def timer_set_pwm_duty(self, timer_id: int, duty: int):
        """Set PWM duty cycle"""
        if timer_id not in self.timers:
            raise VMError(f"Timer{timer_id} not initialized")
        
        self.timers[timer_id]['pwm_duty'] = duty
        print(f"\nTimer{timer_id} PWM duty set to {duty}%")
    
    def adc_init(self, pin: int):
        """Initialize ADC channel"""
        self.adc_channels[pin] = 0
        print(f"\nADC{pin} initialized")
    
    def adc_read(self, pin: int) -> int:
        """Read ADC value"""
        if pin not in self.adc_channels:
            raise VMError(f"ADC{pin} not initialized")
        
        # Simulate ADC reading
        import random
        value = random.randint(0, 4095)  # 12-bit ADC
        self.adc_channels[pin] = value
        print(f"\nADC{pin} read: {value}")
        return value
    
    def uart_write(self, data: bytes):
        """Write data to UART"""
        self.uart_buffer.append(data)
        print(f"\nUART TX: {data.hex()}")
    
    def spi_transfer(self, tx_data: bytes) -> bytes:
        """SPI transfer"""
        self.spi_buffer.append(tx_data)
        # Simulate response
        rx_data = bytes([0xFF] * len(tx_data))
        print(f"\nSPI TX: {tx_data.hex()}, RX: {rx_data.hex()}")
        return rx_data
    
    def i2c_write(self, addr: int, data: int):
        """Write data to I2C device"""
        if addr not in self.i2c_devices:
            self.i2c_devices[addr] = {}
        
        # Simulate register write
        self.i2c_devices[addr][0] = data
        print(f"\nI2C write to 0x{addr:02X}: 0x{data:02X}")
    
    def i2c_read(self, addr: int, reg: int) -> int:
        """Read data from I2C device"""
        if addr not in self.i2c_devices:
            self.i2c_devices[addr] = {}
        
        # Simulate register read
        value = self.i2c_devices[addr].get(reg, 0)
        print(f"\nI2C read from 0x{addr:02X} reg 0x{reg:02X}: 0x{value:02X}")
        return value

class TaskVMContext:
    """Separate VM context for executing tasks in threads"""
    
    def __init__(self, task: Task, task_context_shared : TaskContextSharedMaterial):
        self.task = task
        self.pc = 0
        self.stack = []
        self.call_stack = []
        self.running = True
        self.saved_params = []  # For parameter restoration on function return
        self.call_depth = 0  # Track nested function call depth

        self.task_context_shared = task_context_shared
        
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
            
            # Pointer instructions
            Opcode.LOAD_ADDR: self._handle_load_addr,
            Opcode.LOAD_DEREF: self._handle_load_deref,
            Opcode.STORE_DEREF: self._handle_store_deref,
            
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
            Opcode.ALLOC_FRAME: self._handle_alloc_frame,
            Opcode.FREE_FRAME: self._handle_free_frame,
            
            # Array instructions
            Opcode.ALLOC_ARRAY: self._handle_alloc_array,
            Opcode.LOAD_ARRAY_ELEM: self._handle_load_array_elem,
            Opcode.STORE_ARRAY_ELEM: self._handle_store_array_elem,
            
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
            Opcode.GLOBAL_VAR_DECLARE: self._handle_global_var_declare,
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
            Opcode.DBG_PRINTF: self._handle_dbg_printf,
            Opcode.DBG_BREAKPOINT: self._handle_dbg_breakpoint,
            
            Opcode.HALT: self._handle_halt,
            Opcode.NOP: self._handle_nop,
            Opcode.COMMENT: self._handle_comment,
        }
    
    def execute_function(self, func_addr: int):
        """Execute a function starting at the given address"""
        self.pc = func_addr
        
        try:
            while self.running and self.pc < len(self.task_context_shared.program.instructions):
                instruction = self.task_context_shared.program.instructions[self.pc]
                
                if self.task_context_shared.trace:
                    print(f"\nTask {self.task.name}: PC={self.pc} {instruction}")
                
                self._execute_instruction(instruction)
                
                # Handle control flow
                if instruction.opcode not in [Opcode.JUMP, Opcode.JUMPIF_TRUE, 
                                            Opcode.JUMPIF_FALSE, Opcode.CALL, Opcode.RET]:
                    self.pc += 1
                
                # Check if task should yield or delay
                if instruction.opcode in [Opcode.RTOS_YIELD, Opcode.RTOS_DELAY_MS]:
                    time.sleep(0.001)  # Small yield for cooperative threading
                    
        except Exception as e:
            print(f"\nTask {self.task.name} execution error: {e}")
            raise
    
    def _execute_instruction(self, instruction: Instruction):
        """Execute a single instruction"""
        handler = self.handlers.get(instruction.opcode)
        if handler:
            handler(instruction)
        else:
            raise VMError(f"Unknown opcode: {instruction.opcode}")
    
    def _pop(self):
        """Pop value from stack"""
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()
    
    def _push(self, value):
        """Push value to stack"""
        self.stack.append(value)
    
    
    def _check_timeouts(self):
        """Check for timed out message receives"""
        current_time = time.time()
        
        for queue in self.task_context_shared.message_queues.values():
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
                    self.task_context_shared.tasks[task_id].state = TaskState.READY
                    
                    # Save current state and switch to timed out task temporarily
                    # to push the timeout return value
                    saved_task = self.current_task_id
                    saved_stack = self.stack
                    
                    self.current_task_id = task_id
                    self.stack = self.task_context_shared.tasks[task_id].stack
                    self._push(0)  # Timeout return value
                    self.task_context_shared.tasks[task_id].stack = self.stack
                    
                    # Restore previous state
                    self.current_task_id = saved_task
                    self.stack = saved_stack
                    
                    if self.task_context_shared.debug:
                        print(f"\nTask ID: {task_id} timed out waiting for message")

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
            raise VMError(f"Stack underflow at PC {self.pc}")
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
        func_address = instruction.operands[0]
        param_count = instruction.operands[1] if len(instruction.operands) > 1 else 0
        
        # Increment call depth for nested function tracking
        self.call_depth += 1
        
        # Save current state
        self.call_stack.append((self.pc + 1, self.call_depth))
        
        # Pop parameters from stack and store them in function's parameter slots
        # Parameters are popped in reverse order (last argument first)
        params = []
        for _ in range(param_count):
            params.append(self._pop())
        params.reverse()  # Restore correct parameter order
        
        # Use a separate address space for parameters (starting from high addresses)
        # This avoids conflicts with constants and global variables
        param_base = 10000  # Base address for parameters
        old_param_values = {}
        for i, param_value in enumerate(params):
            param_addr = param_base + i
            # Save old values to restore later
            if param_addr in self.task_context_shared.memory:
                old_param_values[param_addr] = self.task_context_shared.memory[param_addr]
            self.task_context_shared.memory[param_addr] = param_value
        
        # Store old values for restoration on return
        if not hasattr(self, 'saved_params'):
            self.saved_params = []
        self.saved_params.append((old_param_values, param_base, param_count, self.call_depth))
        
        # Jump to function
        self.pc = func_address
    
    def _handle_ret(self, instruction: Instruction):
        """Handle RET instruction"""
        if self.call_stack:
            # Restore saved parameter values
            if hasattr(self, 'saved_params') and self.saved_params:
                old_values, param_base, param_count, call_depth = self.saved_params.pop()
                # Restore the old values
                for addr, value in old_values.items():
                    self.task_context_shared.memory[addr] = value
                # Remove parameter values that didn't exist before
                for i in range(param_count):
                    param_addr = param_base + i
                    if param_addr not in old_values and param_addr in self.task_context_shared.memory:
                        del self.task_context_shared.memory[param_addr]
            
            # Decrement call depth
            self.call_depth -= 1
            
            # Restore PC from call stack
            self.pc, saved_depth = self.call_stack.pop()
        else:
            self.running = False
    
    def _handle_load_const(self, instruction: Instruction):
        """Handle LOAD_CONST instruction"""
        const_idx = instruction.operands[0]
        if const_idx < len(self.task_context_shared.program.constants):
            self._push(self.task_context_shared.program.constants[const_idx])
        else:
            self._push(0)
    
    def _map_variable_address(self, compile_time_address: int) -> int:
        """Map compile-time address to runtime address considering call depth"""
        if compile_time_address < 10000:
            # Global variable - use as-is
            return compile_time_address
        elif compile_time_address < 20000:
            # Parameter - use as-is
            return compile_time_address
        else:
            # Local variable - add call depth offset
            base_local = 20000
            offset = compile_time_address - base_local
            # Each call depth gets 1000 addresses to avoid conflicts
            runtime_address = base_local + (self.call_depth * 1000) + offset
            return runtime_address
    
    def _handle_load_var(self, instruction: Instruction):
        """Handle LOAD_VAR instruction"""
        address = instruction.operands[0]
        
        # Check if this is a parameter load (addresses 0-9 are typically parameters)
        # and we're in a function call context
        if hasattr(self, 'saved_params') and self.saved_params and address < 10:
            param_base = 10000
            param_addr = param_base + address
            if param_addr in self.task_context_shared.memory:
                value = self.task_context_shared.memory[param_addr]
                self._push(value)
                return
        
        # Map to runtime address considering call depth
        runtime_address = self._map_variable_address(address)
        
        # Normal variable load
        value = self.task_context_shared.memory.get(runtime_address, 0)
        self._push(value)
    
    def _handle_store_var(self, instruction: Instruction):
        """Handle STORE_VAR instruction"""
        address = instruction.operands[0]
        value = self._pop()
        
        # Map to runtime address considering call depth
        runtime_address = self._map_variable_address(address)
        
        self.task_context_shared.memory[runtime_address] = value
    
    def _handle_load_struct_member(self, instruction: Instruction):
        """Handle LOAD_STRUCT_MEMBER instruction"""
        base_addr = instruction.operands[0]
        offset = instruction.operands[1]
        value = self.task_context_shared.memory.get(base_addr + offset, 0)
        self._push(value)
    
    def _handle_store_struct_member(self, instruction: Instruction):
        """Handle STORE_STRUCT_MEMBER instruction"""
        base_addr = instruction.operands[0]
        offset = instruction.operands[1]
        value = self._pop()
        self.task_context_shared.memory[base_addr + offset] = value
    
    def _handle_load_struct_member_bit(self, instruction: Instruction):
        """Handle LOAD_STRUCT_MEMBER_BIT instruction for bit-fields"""
        base_addr = instruction.operands[0]
        byte_offset = instruction.operands[1]
        bit_offset = instruction.operands[2]
        bit_width = instruction.operands[3]
        
        if base_addr == 0:
            base_addr = self._pop()  # Pop base address if not provided

        # Load the containing word
        word_value = self.task_context_shared.memory.get(base_addr + byte_offset, 0)
        
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
        word_value = self.task_context_shared.memory.get(base_addr + byte_offset, 0)
        
        # Create a mask to clear the bit-field
        mask = (1 << bit_width) - 1
        clear_mask = ~(mask << bit_offset)
        
        # Clear the bit-field and set the new value
        word_value = (word_value & clear_mask) | ((new_value & mask) << bit_offset)
        
        # Store the modified word back
        self.task_context_shared.memory[base_addr + byte_offset] = word_value

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
        address = len(self.task_context_shared.memory)
        for i in range(size):
            self.task_context_shared.memory[address + i] = 0
        self._push(address)
    
    def _handle_free_var(self, instruction: Instruction):
        """Handle FREE_VAR instruction"""
        address = instruction.operands[0]
        # Simplified - just mark as free (in real implementation, manage free list)
        if address in self.task_context_shared.memory:
            del self.task_context_shared.memory[address]
    
    def _handle_alloc_struct(self, instruction: Instruction):
        """Handle ALLOC_STRUCT instruction"""
        size = instruction.operands[0]
        address = len(self.task_context_shared.memory)
        for i in range(size):
            self.task_context_shared.memory[address + i] = 0
        self._push(address)
    
    def _handle_alloc_frame(self, instruction: Instruction):
        """Handle ALLOC_FRAME instruction - allocate function frame"""
        size = instruction.operands[0]
        if self.task_context_shared.debug:
            print(f"\nAllocating function frame of size {size}")
        # Frame allocation is handled by the address space separation in the bytecode generator
        # The actual memory allocation happens when variables are accessed
        # This instruction is mainly for tracking/debugging purposes
        pass
    
    def _handle_free_frame(self, instruction: Instruction):
        """Handle FREE_FRAME instruction - free function frame"""
        size = instruction.operands[0]
        if self.task_context_shared.debug:
            print(f"\nFreeing function frame of size {size} at call depth {self.call_depth}")
        
        # Find and clean up function-local variables for the current call depth
        # Function local variables use addresses starting from 20000 + (call_depth * 1000)
        base_local_address = 20000 + (self.call_depth * 1000)
        max_local_address = base_local_address + size
        
        # Clean up local variables in the current call frame
        addresses_to_remove = []
        for addr in self.task_context_shared.memory:
            if base_local_address <= addr < max_local_address:
                addresses_to_remove.append(addr)
        
        for addr in addresses_to_remove:
            del self.task_context_shared.memory[addr]
        
        if self.task_context_shared.debug and addresses_to_remove:
            print(f"\nCleaned up {len(addresses_to_remove)} local variables at depth {self.call_depth}: {addresses_to_remove}")
    
    def _handle_alloc_array(self, instruction: Instruction):
        """Handle ALLOC_ARRAY instruction"""
        element_size = instruction.operands[0]
        count = instruction.operands[1]
        total_size = element_size * count
        address = len(self.task_context_shared.memory)
        for i in range(total_size):
            self.task_context_shared.memory[address + i] = 0
        self._push(address)
    
    def _handle_load_array_elem(self, instruction: Instruction):
        """Handle LOAD_ARRAY_ELEM instruction"""
        # Pop values from stack
        index = self._pop()
        base_addr = self._pop()
        element_size = instruction.operands[0] if len(instruction.operands) > 0 else 4
        
        # Calculate element address
        element_addr = base_addr + (index * element_size)
        value = self.task_context_shared.memory.get(element_addr, 0)
        self._push(value)
    
    def _handle_store_array_elem(self, instruction: Instruction):
        """Handle STORE_ARRAY_ELEM instruction"""
        # Pop values from stack
        value = self._pop()
        index = self._pop()
        base_addr = self._pop()
        element_size = instruction.operands[0] if len(instruction.operands) > 0 else 4
        
        # Calculate element address
        element_addr = base_addr + (index * element_size)
        self.task_context_shared.memory[element_addr] = value
    
    # RTOS instruction handlers
    
    def _handle_rtos_create_task(self, instruction: Instruction):
        """Handle RTOS_CREATE_TASK instruction"""
        func_addr    = self._pop()
        task_id      = self._pop()
        priority     = self._pop()
        core         = self._pop()
        stack_size   = self._pop()
        
        # Get task name from string pool
        task_name = f"Task-{task_id}"
        
        # Get function name and resolve to address
        # Get function name from function dict using func_addr
        func_name = None
        for name, addr in self.task_context_shared.program.functions.items():
            if addr == func_addr:
                func_name = name
                break
        
        if not func_name:
            func_name = f"func_at_{func_addr}"
        
        # Create new task
        task = Task(
            id=task_id,
            name=task_name,
            func_addr=func_addr,
            stack_size=stack_size,
            priority=priority,
            core=core,
            state=TaskState.READY,
            pc=func_addr,
            vm_instance=self
        )
        
        self.task_context_shared.tasks[self.task_context_shared.task_counter] = task
        self.task_context_shared.task_counter += 1
        
        print(f"\nCreated task '{task_name}' (ID: {task.id}) -> function '{func_name}' at address {func_addr}")

        self.task_context_shared._start_task_thread(task)
    
    def _handle_rtos_delete_task(self, instruction: Instruction):
        """Handle RTOS_DELETE_TASK instruction"""
        task_id = self._pop()
        
        if task_id in self.task_context_shared.tasks:
            self.task_context_shared.tasks[task_id].state = TaskState.DELETED
            print(f"\nDeleted task ID: {task_id}")
        else:
            print(f"\nTask ID {task_id} not found")
    
    def _handle_rtos_delay_ms(self, instruction: Instruction):
        """Handle RTOS_DELAY_MS instruction"""
        ms = self._pop()

        if self.task_context_shared.debug:
            print(f"\nDelaying {ms}ms")

        time.sleep(ms / 1000.0)
    
    def _handle_rtos_semaphore_create(self, instruction: Instruction):
        """Handle RTOS_SEMAPHORE_CREATE instruction"""
        semaphore = Semaphore(
            id=self.task_context_shared.semaphore_counter,
            count=1,
            max_count=1,
            waiting_tasks=[]
        )
        
        self.task_context_shared.semaphores[self.task_context_shared.semaphore_counter] = semaphore
        self._push(self.task_context_shared.semaphore_counter)
        self.task_context_shared.semaphore_counter += 1
        
        print(f"\nCreated semaphore ID: {semaphore.id}")
    
    def _handle_rtos_semaphore_take(self, instruction: Instruction):
        """Handle RTOS_SEMAPHORE_TAKE instruction"""
        timeout = self._pop()
        handle = self._pop()
        
        if handle in self.task_context_shared.semaphores:
            semaphore = self.task_context_shared.semaphores[handle]
            if semaphore.count > 0:
                semaphore.count -= 1
                self._push(1)  # Success
                print(f"\nTook semaphore {handle}")
            else:
                self._push(0)  # Failed
                print(f"\nFailed to take semaphore {handle}")
        else:
            self._push(0)  # Invalid handle
    
    def _handle_rtos_semaphore_give(self, instruction: Instruction):
        """Handle RTOS_SEMAPHORE_GIVE instruction"""
        handle = self._pop()
        
        if handle in self.task_context_shared.semaphores:
            semaphore = self.task_context_shared.semaphores[handle]
            if semaphore.count < semaphore.max_count:
                semaphore.count += 1
                print(f"\nGave semaphore {handle}")
            else:
                print(f"\nSemaphore {handle} already at max count")
        else:
            print(f"\nInvalid semaphore handle: {handle}")
    
    def _handle_rtos_yield(self, instruction: Instruction):
        """Handle RTOS_YIELD instruction"""
        print("Task yielding")
        self._yield_task()
    
    def _handle_rtos_suspend_task(self, instruction: Instruction):
        """Handle RTOS_SUSPEND_TASK instruction"""
        task_id = self._pop()
        
        if task_id in self.task_context_shared.tasks:
            self.task_context_shared.tasks[task_id].state = TaskState.SUSPENDED
            print(f"\nSuspended task ID: {task_id}")
        else:
            print(f"\nTask ID {task_id} not found")
    
    def _handle_rtos_resume_task(self, instruction: Instruction):
        """Handle RTOS_RESUME_TASK instruction"""
        task_id = self._pop()
        
        if task_id in self.task_context_shared.tasks:
            if self.task_context_shared.tasks[task_id].state == TaskState.SUSPENDED:
                self.task_context_shared.tasks[task_id].state = TaskState.READY
                print(f"\nResumed task ID: {task_id}")
            else:
                print(f"\nTask ID {task_id} not suspended")
        else:
            print(f"\nTask ID {task_id} not found")
    
    
    def _handle_global_var_declare(self, instruction: Instruction):
        """Handle GLOBAL_VAR_DECLARE instruction - should only be called during initialization"""
        address = instruction.operands[0]
        const_idx = instruction.operands[1]
        is_const = instruction.operands[2] == 1
        
        # Get the initial value from constants
        if const_idx < len(self.task_context_shared.program.constants):
            initial_value = self.task_context_shared.program.constants[const_idx]
        else:
            initial_value = 0
        
        # Initialize the global variable
        self.task_context_shared.memory[address] = initial_value
        
        if self.task_context_shared.debug:
            print(f"\nInitialized global variable at address {address} with value {initial_value} (const: {is_const})")
    
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
        
        self.task_context_shared.message_queues[message_id] = queue
        if self.task_context_shared.debug:
            print(f"\nDeclared message queue ID: {message_id}, Type: {message_type}")
    
    def _handle_msg_send(self, instruction: Instruction):
        """Handle MSG_SEND instruction"""
        message_id = instruction.operands[0]
        payload = self._pop()  # Get the payload from stack
        
        if message_id in self.task_context_shared.message_queues:
            queue = self.task_context_shared.message_queues[message_id]
            if len(queue.queue) < queue.max_size:
                queue.queue.append(payload)
                
                if self.task_context_shared.debug:
                    print(f"\nSent message to queue ID: {message_id}, payload: {payload}")
            else:
                # Queue is full, block sender (or drop message in this simple implementation)
                if self.task_context_shared.debug:
                    print(f"\nMessage queue ID: {message_id} is full, dropping message")
        else:
            raise VMError(f"Invalid message queue ID: {message_id}")
    
    def _handle_msg_recv(self, instruction: Instruction):
        """Handle MSG_RECV instruction with timeout support"""
        message_id = instruction.operands[0]
        
        # Pop timeout value from stack (999999 means blocking, 0 means non-blocking, >0 means timeout in ms)
        timeout_ms = self._pop()
        
        if message_id in self.task_context_shared.message_queues:
            msg_queue = self.task_context_shared.message_queues[message_id]
            if timeout_ms > 9999:
                msg_wait_end_time = time.time() + timeout_ms
            else:
                msg_wait_end_time = time.time() + (timeout_ms / 1000.0)

            # Wait for message
            while(1):
                if msg_queue.queue:
                    if len(msg_queue.queue) > 0:
                        # Message available, return it
                        message = msg_queue.queue.popleft()
                        self._push(message)
                        break
                elif time.time() > msg_wait_end_time:
                    self._push(-1)
                    break
                else:
                    time.sleep(0.01)
        else:
            raise VMError(f"Invalid message queue ID: {message_id}")

    # Hardware instruction handlers
    def _handle_hw_gpio_init(self, instruction: Instruction):
        """Handle HW_GPIO_INIT instruction"""
        mode = self._pop()
        pin = self._pop()
        self.task_context_shared.hardware.gpio_init(pin, mode)
    
    def _handle_hw_gpio_set(self, instruction: Instruction):
        """Handle HW_GPIO_SET instruction"""
        value = self._pop()
        pin = self._pop()
        self.task_context_shared.hardware.gpio_set(pin, value)
    
    def _handle_hw_gpio_get(self, instruction: Instruction):
        """Handle HW_GPIO_GET instruction"""
        pin = self._pop()
        value = self.task_context_shared.hardware.gpio_get(pin)
        self._push(value)
    
    def _handle_hw_timer_init(self, instruction: Instruction):
        """Handle HW_TIMER_INIT instruction"""
        freq = self._pop()
        mode = self._pop()
        timer_id = self._pop()
        self.task_context_shared.hardware.timer_init(timer_id, mode, freq)
    
    def _handle_hw_timer_start(self, instruction: Instruction):
        """Handle HW_TIMER_START instruction"""
        timer_id = self._pop()
        self.task_context_shared.hardware.timer_start(timer_id)
    
    def _handle_hw_timer_stop(self, instruction: Instruction):
        """Handle HW_TIMER_STOP instruction"""
        timer_id = self._pop()
        self.task_context_shared.hardware.timer_stop(timer_id)
    
    def _handle_hw_timer_set_pwm_duty(self, instruction: Instruction):
        """Handle HW_TIMER_SET_PWM_DUTY instruction"""
        duty = self._pop()
        timer_id = self._pop()
        self.task_context_shared.hardware.timer_set_pwm_duty(timer_id, duty)
    
    def _handle_hw_adc_init(self, instruction: Instruction):
        """Handle HW_ADC_INIT instruction"""
        pin = self._pop()
        self.task_context_shared.hardware.adc_init(pin)
    
    def _handle_hw_adc_read(self, instruction: Instruction):
        """Handle HW_ADC_READ instruction"""
        pin = self._pop()
        value = self.task_context_shared.hardware.adc_read(pin)
        self._push(value)
    
    def _handle_hw_uart_write(self, instruction: Instruction):
        """Handle HW_UART_WRITE instruction"""
        length = self._pop()
        buffer_addr = self._pop()
        # Simulate UART write
        data = bytes([self.task_context_shared.memory.get(buffer_addr + i, 0) for i in range(length)])
        self.task_context_shared.hardware.uart_write(data)
    
    def _handle_hw_spi_transfer(self, instruction: Instruction):
        """Handle HW_SPI_TRANSFER instruction"""
        length = self._pop()
        rx_addr = self._pop()
        tx_addr = self._pop()
        # Simulate SPI transfer
        tx_data = bytes([self.task_context_shared.memory.get(tx_addr + i, 0) for i in range(length)])
        rx_data = self.task_context_shared.hardware.spi_transfer(tx_data)
        # Store received data
        for i, byte in enumerate(rx_data):
            self.task_context_shared.memory[rx_addr + i] = byte
    
    def _handle_hw_i2c_write(self, instruction: Instruction):
        """Handle HW_I2C_WRITE instruction"""
        data = self._pop()
        addr = self._pop()
        self.task_context_shared.hardware.i2c_write(addr, data)
    
    def _handle_hw_i2c_read(self, instruction: Instruction):
        """Handle HW_I2C_READ instruction"""
        reg = self._pop()
        addr = self._pop()
        value = self.task_context_shared.hardware.i2c_read(addr, reg)
        self._push(value)
    
    def _handle_dbg_print(self, instruction: Instruction):
        """Handle DBG_PRINT instruction"""
        string_id = self._pop()
        if string_id < len(self.task_context_shared.program.strings):
            print(f"\nDEBUG: {self.task_context_shared.program.strings[string_id]}")
        else:
            print(f"\nDEBUG: <invalid string {string_id}>")
    
    def _handle_dbg_printf(self, instruction: Instruction):
        """Handle DBG_PRINTF instruction with variable formatting"""
        format_string_id = instruction.operands[0]
        arg_count = instruction.operands[1]
        
        # Pop arguments from stack (in reverse order)
        args = []
        for _ in range(arg_count):
            args.append(self._pop())
        args.reverse()  # Restore correct order
        
        # Get format string
        if format_string_id == 0:
            # Format string is on stack
            format_string_id = self._pop()
        
        if format_string_id < len(self.task_context_shared.program.strings):
            format_string = self.task_context_shared.program.strings[format_string_id]
            try:
                # Simple formatting - replace {0}, {1}, etc. with arguments
                output = format_string
                for i, arg in enumerate(args):
                    placeholder = "{" + str(i) + "}"
                    if placeholder in output:
                        output = output.replace(placeholder, str(arg))
                
                # Also support simple {} placeholders in order
                arg_index = 0
                while "{}" in output and arg_index < len(args):
                    output = output.replace("{}", str(args[arg_index]), 1)
                    arg_index += 1
                
                print(f"\nDEBUG: {output}")
            except Exception as e:
                print(f"\nDEBUG: <formatting error: {e}>")
        else:
            print(f"\nDEBUG: <invalid format string {format_string_id}>")
    
    def _handle_dbg_breakpoint(self, instruction: Instruction):
        """Handle DBG_BREAKPOINT instruction"""
        print(f"\nBREAKPOINT at PC {self.pc}")
        if self.debug:
            input("Press Enter to continue...")
    
    def _handle_halt(self, instruction: Instruction):
        """Handle HALT instruction"""
        self.running = False
        print("Program halted")
    
    def _handle_nop(self, instruction: Instruction):
        """Handle NOP instruction"""
        pass  # Do nothing

    def _handle_comment(self, instruction: Instruction):
        """Handle COMMENT instruction"""
        pass  # Comments are ignored at runtime

    # Pointer instruction handlers
    def _handle_load_addr(self, instruction: Instruction):
        """Handle LOAD_ADDR instruction - pushes address of variable onto stack"""
        address = instruction.operands[0]
        self._push(address)
    
    def _handle_load_deref(self, instruction: Instruction):
        """Handle LOAD_DEREF instruction - dereferences pointer on top of stack"""
        pointer_value = self._pop()
        # The pointer value is the address to read from
        if pointer_value not in self.task_context_shared.memory:
            raise VMError(f"Dereferencing null or invalid pointer: {pointer_value}")
        value = self.task_context_shared.memory[pointer_value]
        self._push(value)
    
    def _handle_store_deref(self, instruction: Instruction):
        """Handle STORE_DEREF instruction - stores value at pointer address"""
        value = self._pop()  # Value to store
        pointer_value = self._pop()  # Address to store at
        if pointer_value is None:
            raise VMError("Cannot dereference null pointer")
        self.task_context_shared.memory[pointer_value] = value

    def _trace_instruction(self, instruction: Instruction):
        """Trace instruction execution"""
        stack_info = f"Stack: {self.stack[-3:] if len(self.stack) > 3 else self.stack}"
        print(f"\nPC:{self.pc:4d} {instruction} {stack_info}")

class VirtualMachine:
    """RT-Micro-C Virtual Machine"""
    
    def __init__(self, debug: bool = False, trace: bool = False):
        
        # Program state
        self.program: Optional[BytecodeProgram] = None
        self.running = False
        
        self.task_context_shared = TaskContextSharedMaterial()
        # RTOS state
        self.task_context_shared.tasks = {}
        self.task_context_shared.semaphores = {}
        self.task_context_shared.message_queues = {}
        self.current_task_id = 0
        self.task_context_shared.task_counter = 0
        self.task_context_shared.semaphore_counter = 0
        self.task_context_shared.message_queue_counter = 0
        self.task_context_shared.debug = debug
        self.task_context_shared.trace = trace
        self.scheduler_running = False
        
        # Hardware simulator
        self.task_context_shared.hardware = HardwareSimulator()
        
    
    def load_program(self, program: BytecodeProgram):
        """Load a bytecode program"""
        self.task_context_shared.program = program
        
        # Create main task if main function exists
        if 'main' in program.functions:
            main_addr = program.functions['main']
            self.create_main_task(main_addr)
    
    def create_main_task(self, main_addr: int):
        """Create the main task"""
        task = Task(
            id=self.task_context_shared.task_counter,
            name="main",
            func_addr=main_addr,
            stack_size=1024,
            priority=5,
            core=0,
            state=TaskState.READY,
            pc=main_addr,
            vm_instance=self
        )
        self.task_context_shared.tasks[self.task_context_shared.task_counter] = task
        self.task_context_shared.task_counter += 1

    def program_initialization(self):
        """Initialize the program state"""
        if not self.task_context_shared.program:
            raise VMError("No program loaded")
        
        # Initialize memory with constants and global variables
        for i, instruction in enumerate(self.task_context_shared.program.instructions):
            if instruction.opcode == Opcode.GLOBAL_VAR_DECLARE:
                # Initialize global variable
                address = instruction.operands[0]
                const_idx = instruction.operands[1]
                is_const = instruction.operands[2] == 1
                
                # Get the initial value from constants
                if const_idx < len(self.task_context_shared.program.constants):
                    initial_value = self.task_context_shared.program.constants[const_idx]
                else:
                    initial_value = 0
                
                # Initialize the global variable
                self.task_context_shared.memory[address] = initial_value
                
                if self.task_context_shared.debug:
                    print(f"\nInitialized global variable at address {address} with value {initial_value} (const: {is_const})")
                    
            elif instruction.opcode == Opcode.MSG_DECLARE:
                # Initialize message queue
                message_id = instruction.operands[0]
                message_type = instruction.operands[1]
                queue = MessageQueue(
                    id=message_id,
                    name=f"MessageQueue_{message_id}",
                    message_type=message_type,
                    queue=deque(),
                    max_size=10  # Default queue size
                )
                self.task_context_shared.message_queues[message_id] = queue
        
        # Start the main task thread
        self.task_context_shared._start_task_thread(self.task_context_shared.tasks[0])

    def run(self):
        """Run the virtual machine with threaded tasks"""
        self.running = True
        
        if not self.task_context_shared.program:
            raise VMError("No program loaded")
        
        try:
            self.program_initialization()

            # Wait for all tasks to complete or until interrupted
            print("\nVM running, waiting for tasks to complete...")
            while self.running:
                # Check if any tasks are still running
                active_tasks = [task for task in self.task_context_shared.tasks.values() 
                              if task.thread and task.thread.is_alive()]
                
                if not active_tasks:
                    print("All tasks completed")
                    break
                
                # Wait a bit and check again
                time.sleep(0.1)
                
                # Check for any task errors or completions
                for task in list(self.task_context_shared.tasks.values()):
                    if task.thread and not task.thread.is_alive() and task.state != TaskState.DELETED:
                        print(f"\nTask {task.name} (ID: {task.id}) finished")
                        task.state = TaskState.DELETED
        
        except KeyboardInterrupt:
            print("\\nExecution interrupted by user")
            self.running = False
            
            # Wait for threads to finish gracefully
            for task in self.task_context_shared.tasks.values():
                if task.thread and task.thread.is_alive():
                    print(f"\nWaiting for task {task.name} to finish...")
                    task.thread.join(timeout=1.0)
                    
        except Exception as e:
            print(f"\nRuntime error: {e}")
            if self.task_context_shared.debug:
                import traceback
                traceback.print_exc()
        finally:
            self.running = False
            print("VM execution finished")
