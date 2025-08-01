/**
 * @file rtmc_interpreter.c
 * @brief RT-Micro-C Bytecode Interpreter Implementation for FreeRTOS on Raspberry Pi Pico
 * 
 * This file implements the complete RT-Micro-C bytecode interpreter that executes
 * RT-Micro-C programs on FreeRTOS running on the Raspberry Pi Pico (RP2040).
 * 
 * @author Omidardestani
 * @date 2025
 */

#include "rtmc_interpreter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

/* Debug and error printing */
void rtmc_debug_print(const char* format, ...) {
    va_list args;
    va_start(args, format);
    printf("[RTMC DEBUG] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

void rtmc_error_print(const char* format, ...) {
    va_list args;
    va_start(args, format);
    printf("[RTMC ERROR] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

/* ========================================================================== */
/* Virtual Machine Core Functions                                            */
/* ========================================================================== */

rtmc_vm_t* rtmc_vm_create(bool debug, bool trace) {
    rtmc_vm_t* vm = (rtmc_vm_t*)malloc(sizeof(rtmc_vm_t));
    if (!vm) {
        rtmc_error_print("Failed to allocate memory for VM");
        return NULL;
    }
    
    memset(vm, 0, sizeof(rtmc_vm_t));
    vm->debug = debug;
    vm->trace = trace;
    vm->running = false;
    vm->scheduler_running = false;
    
    /* Initialize hardware state */
    for (int i = 0; i < RTMC_MAX_GPIO_PINS; i++) {
        vm->gpio_pins[i].initialized = false;
    }
    
    for (int i = 0; i < RTMC_MAX_TIMERS; i++) {
        vm->timers[i].initialized = false;
    }
    
    for (int i = 0; i < RTMC_MAX_ADC_CHANNELS; i++) {
        vm->adc_channels[i].initialized = false;
    }
    
    if (debug) {
        rtmc_debug_print("VM created successfully");
    }
    
    return vm;
}

void rtmc_vm_destroy(rtmc_vm_t* vm) {
    if (!vm) return;
    
    /* Stop the VM */
    rtmc_vm_stop(vm);
    
    /* Clean up RTOS objects */
    for (uint32_t i = 0; i < vm->semaphore_count; i++) {
        if (vm->semaphores[i].freertos_handle) {
            vSemaphoreDelete(vm->semaphores[i].freertos_handle);
        }
    }
    
    for (uint32_t i = 0; i < vm->message_queue_count; i++) {
        if (vm->message_queues[i].freertos_handle) {
            vQueueDelete(vm->message_queues[i].freertos_handle);
        }
    }
    
    free(vm);
    
    rtmc_debug_print("VM destroyed");
}

bool rtmc_vm_load_program(rtmc_vm_t* vm, rtmc_program_t* program) {
    if (!vm || !program) {
        rtmc_error_print("NULL pointer in load_program");
        return false;
    }
    
    vm->program = program;
    
    /* Initialize global variables and message queues */
    for (uint32_t i = 0; i < program->instruction_count; i++) {
        const rtmc_instruction_t* inst = &program->instructions[i];
        
        if (inst->opcode == RTMC_OP_GLOBAL_VAR_DECLARE) {
            uint32_t address = inst->operands[0].u32;
            uint32_t const_idx = inst->operands[1].u32;
            bool is_const = inst->operands[2].u32 == 1;
            
            /* Get initial value from constants */
            rtmc_value_t initial_value = {0};
            if (const_idx < program->constant_count) {
                initial_value = program->constants[const_idx];
            }
            
            /* Initialize global variable */
            if (address < RTMC_MAX_MEMORY_SIZE) {
                vm->memory[address] = initial_value;
                if (vm->debug) {
                    rtmc_debug_print("Initialized global variable at address %u with value %d (const: %s)",
                        address, initial_value.i32, is_const ? "true" : "false");
                }
            }
        }
        else if (inst->opcode == RTMC_OP_MSG_DECLARE) {
            uint32_t message_id = inst->operands[0].u32;
            uint32_t message_type = inst->operands[1].u32;
            
            if (vm->message_queue_count < RTMC_MAX_MESSAGE_QUEUES) {
                rtmc_message_queue_t* queue = &vm->message_queues[vm->message_queue_count];
                queue->id = message_id;
                queue->message_type = message_type;
                queue->max_size = 10; /* Default queue size */
                snprintf(queue->name, sizeof(queue->name), "MessageQueue_%u", message_id);
                
                /* Create FreeRTOS queue */
                queue->freertos_handle = xQueueCreate(queue->max_size, sizeof(rtmc_value_t));
                if (!queue->freertos_handle) {
                    rtmc_error_print("Failed to create message queue %u", message_id);
                    return false;
                }
                
                vm->message_queue_count++;
                if (vm->debug) {
                    rtmc_debug_print("Created message queue ID: %u, Type: %u", message_id, message_type);
                }
            }
        }
    }
    
    /* Create main task if main function exists */
    uint32_t main_addr = rtmc_find_function_address(vm, "main");
    if (main_addr != UINT32_MAX) {
        rtmc_vm_create_main_task(vm, main_addr);
    }
    
    if (vm->debug) {
        rtmc_debug_print("Program loaded successfully: %u instructions, %u functions",
            program->instruction_count, program->function_count);
    }
    
    return true;
}

bool rtmc_vm_run(rtmc_vm_t* vm) {
    if (!vm || !vm->program) {
        rtmc_error_print("VM or program not initialized");
        return false;
    }
    
    vm->running = true;
    
    if (vm->debug) {
        rtmc_debug_print("VM starting execution");
    }
    
    /* The actual execution happens in FreeRTOS tasks */
    /* This function just sets up the environment and returns */
    /* FreeRTOS scheduler will handle task execution */
    
    return true;
}

void rtmc_vm_stop(rtmc_vm_t* vm) {
    if (!vm) return;
    
    vm->running = false;
    vm->scheduler_running = false;
    
    /* Delete all tasks */
    for (uint32_t i = 0; i < vm->task_count; i++) {
        if (vm->tasks[i].freertos_handle) {
            vTaskDelete(vm->tasks[i].freertos_handle);
            vm->tasks[i].freertos_handle = NULL;
        }
    }
    
    if (vm->debug) {
        rtmc_debug_print("VM stopped");
    }
}

/* ========================================================================== */
/* Program Management Functions                                              */
/* ========================================================================== */

rtmc_program_t* rtmc_program_create(void) {
    rtmc_program_t* program = (rtmc_program_t*)malloc(sizeof(rtmc_program_t));
    if (!program) {
        rtmc_error_print("Failed to allocate memory for program");
        return NULL;
    }
    
    memset(program, 0, sizeof(rtmc_program_t));
    return program;
}

void rtmc_program_destroy(rtmc_program_t* program) {
    if (program) {
        free(program);
    }
}

bool rtmc_program_load_from_binary(rtmc_program_t* program, const uint8_t* data, size_t size) {
    if (!program || !data || size == 0) {
        rtmc_error_print("Invalid parameters for binary load");
        return false;
    }
    
    /* This is a simplified binary loader */
    /* In a real implementation, you would parse the binary format */
    /* For now, we'll assume the data contains a serialized program */
    
    rtmc_error_print("Binary loading not yet implemented");
    return false;
}

/* ========================================================================== */
/* Task Management Functions                                                 */
/* ========================================================================== */

uint32_t rtmc_find_function_address(rtmc_vm_t* vm, const char* name) {
    if (!vm || !vm->program || !name) {
        return UINT32_MAX;
    }
    
    for (uint32_t i = 0; i < vm->program->function_count; i++) {
        if (strcmp(vm->program->functions[i].name, name) == 0) {
            return vm->program->functions[i].address;
        }
    }
    
    return UINT32_MAX;
}

bool rtmc_vm_create_main_task(rtmc_vm_t* vm, uint32_t main_addr) {
    if (!vm || vm->task_count >= RTMC_MAX_TASKS) {
        rtmc_error_print("Cannot create main task");
        return false;
    }
    
    rtmc_task_t* task = &vm->tasks[vm->task_count];
    task->id = vm->task_count;
    strncpy(task->name, "main", sizeof(task->name) - 1);
    task->func_addr = main_addr;
    task->stack_size = 1024;
    task->priority = 5;
    task->core = 0;
    task->state = RTMC_TASK_READY;
    task->pc = main_addr;
    task->stack_ptr = 0;
    task->call_stack_ptr = 0;
    task->call_depth = 0;
    
    /* Create task context */
    rtmc_task_context_t* ctx = (rtmc_task_context_t*)malloc(sizeof(rtmc_task_context_t));
    if (!ctx) {
        rtmc_error_print("Failed to allocate task context");
        return false;
    }
    
    ctx->vm = vm;
    ctx->task = task;
    ctx->pc = main_addr;
    ctx->stack_ptr = 0;
    ctx->call_stack_ptr = 0;
    ctx->call_depth = 0;
    ctx->running = true;
    
    /* Create FreeRTOS task */
    BaseType_t result = xTaskCreate(
        rtmc_task_entry_point,
        task->name,
        task->stack_size / sizeof(StackType_t),
        ctx,
        task->priority,
        &task->freertos_handle
    );
    
    if (result != pdPASS) {
        rtmc_error_print("Failed to create FreeRTOS task");
        free(ctx);
        return false;
    }
    
    vm->task_count++;
    
    if (vm->debug) {
        rtmc_debug_print("Created main task at address %u", main_addr);
    }
    
    return true;
}

void rtmc_task_entry_point(void* pvParameters) {
    rtmc_task_context_t* ctx = (rtmc_task_context_t*)pvParameters;
    if (!ctx || !ctx->vm || !ctx->task) {
        rtmc_error_print("Invalid task context");
        vTaskDelete(NULL);
        return;
    }
    
    rtmc_vm_t* vm = ctx->vm;
    rtmc_task_t* task = ctx->task;
    
    if (vm->debug) {
        rtmc_debug_print("Task %s starting execution at PC %u", task->name, ctx->pc);
    }
    
    task->state = RTMC_TASK_RUNNING;
    
    /* Execute instructions */
    while (ctx->running && vm->running && ctx->pc < vm->program->instruction_count) {
        const rtmc_instruction_t* inst = &vm->program->instructions[ctx->pc];
        
        if (vm->trace) {
            rtmc_debug_print("Task %s: PC=%u %s", task->name, ctx->pc, 
                /* We'd need to implement opcode to string conversion */
                "INSTRUCTION");
        }
        
        /* Execute instruction */
        if (!rtmc_execute_instruction(ctx, inst)) {
            rtmc_error_print("Task %s: Instruction execution failed at PC %u", task->name, ctx->pc);
            break;
        }
        
        /* Handle control flow */
        if (inst->opcode != RTMC_OP_JUMP && 
            inst->opcode != RTMC_OP_JUMPIF_TRUE && 
            inst->opcode != RTMC_OP_JUMPIF_FALSE && 
            inst->opcode != RTMC_OP_CALL && 
            inst->opcode != RTMC_OP_RET) {
            ctx->pc++;
        }
        
        /* Yield for cooperative scheduling on delay/yield instructions */
        if (inst->opcode == RTMC_OP_RTOS_YIELD || inst->opcode == RTMC_OP_RTOS_DELAY_MS) {
            taskYIELD();
        }
    }
    
    task->state = RTMC_TASK_DELETED;
    
    if (vm->debug) {
        rtmc_debug_print("Task %s finished execution", task->name);
    }
    
    /* Clean up context */
    free(ctx);
    
    /* Delete this task */
    vTaskDelete(NULL);
}

/* ========================================================================== */
/* Stack Operations                                                          */
/* ========================================================================== */

void rtmc_stack_push(rtmc_task_context_t* ctx, rtmc_value_t value) {
    if (!ctx) {
        rtmc_error_print("NULL context in stack_push");
        return;
    }
    
    if (ctx->stack_ptr >= RTMC_MAX_STACK_SIZE) {
        rtmc_error_print("Stack overflow in task");
        return;
    }
    
    ctx->stack[ctx->stack_ptr++] = value;
}

rtmc_value_t rtmc_stack_pop(rtmc_task_context_t* ctx) {
    rtmc_value_t zero = {0};
    
    if (!ctx) {
        rtmc_error_print("NULL context in stack_pop");
        return zero;
    }
    
    if (ctx->stack_ptr == 0) {
        rtmc_error_print("Stack underflow in task");
        return zero;
    }
    
    return ctx->stack[--ctx->stack_ptr];
}

rtmc_value_t rtmc_stack_peek(rtmc_task_context_t* ctx) {
    rtmc_value_t zero = {0};
    
    if (!ctx) {
        rtmc_error_print("NULL context in stack_peek");
        return zero;
    }
    
    if (ctx->stack_ptr == 0) {
        rtmc_error_print("Stack underflow in stack_peek");
        return zero;
    }
    
    return ctx->stack[ctx->stack_ptr - 1];
}

/* ========================================================================== */
/* Instruction Execution Engine                                              */
/* ========================================================================== */

bool rtmc_execute_instruction(rtmc_task_context_t* ctx, const rtmc_instruction_t* inst) {
    if (!ctx || !inst || !ctx->vm) {
        rtmc_error_print("Invalid parameters for instruction execution");
        return false;
    }
    
    rtmc_vm_t* vm = ctx->vm;
    rtmc_value_t a, b, result;
    
    switch (inst->opcode) {
        /* Control Flow Instructions */
        case RTMC_OP_JUMP:
            ctx->pc = inst->operands[0].u32;
            break;
            
        case RTMC_OP_JUMPIF_TRUE:
            a = rtmc_stack_pop(ctx);
            if (a.i32) {
                ctx->pc = inst->operands[0].u32;
            } else {
                ctx->pc++;
            }
            break;
            
        case RTMC_OP_JUMPIF_FALSE:
            a = rtmc_stack_pop(ctx);
            if (!a.i32) {
                ctx->pc = inst->operands[0].u32;
            } else {
                ctx->pc++;
            }
            break;
            
        case RTMC_OP_CALL: {
            uint32_t func_addr = inst->operands[0].u32;
            uint32_t param_count = inst->operands[1].u32;
            
            /* Save return address */
            if (ctx->call_stack_ptr < RTMC_MAX_CALL_STACK) {
                ctx->call_stack[ctx->call_stack_ptr++] = ctx->pc + 1;
                ctx->call_depth++;
                
                /* Handle parameters (simplified) */
                /* In a complete implementation, parameters would be handled properly */
                
                ctx->pc = func_addr;
            } else {
                rtmc_error_print("Call stack overflow");
                return false;
            }
            break;
        }
        
        case RTMC_OP_RET:
            if (ctx->call_stack_ptr > 0) {
                ctx->pc = ctx->call_stack[--ctx->call_stack_ptr];
                ctx->call_depth--;
            } else {
                ctx->running = false;
            }
            break;
            
        /* Data Manipulation */
        case RTMC_OP_LOAD_CONST: {
            uint32_t const_idx = inst->operands[0].u32;
            if (const_idx < vm->program->constant_count) {
                rtmc_stack_push(ctx, vm->program->constants[const_idx]);
            } else {
                result.i32 = 0;
                rtmc_stack_push(ctx, result);
            }
            break;
        }
        
        case RTMC_OP_LOAD_VAR: {
            uint32_t address = inst->operands[0].u32;
            if (address < RTMC_MAX_MEMORY_SIZE) {
                rtmc_stack_push(ctx, vm->memory[address]);
            } else {
                result.i32 = 0;
                rtmc_stack_push(ctx, result);
            }
            break;
        }
        
        case RTMC_OP_STORE_VAR: {
            uint32_t address = inst->operands[0].u32;
            a = rtmc_stack_pop(ctx);
            if (address < RTMC_MAX_MEMORY_SIZE) {
                vm->memory[address] = a;
            }
            break;
        }
        
        /* Arithmetic Operations */
        case RTMC_OP_ADD:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = a.i32 + b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_SUB:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = a.i32 - b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_MUL:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = a.i32 * b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_DIV:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            if (b.i32 == 0) {
                rtmc_error_print("Division by zero");
                return false;
            }
            result.i32 = a.i32 / b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_MOD:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            if (b.i32 == 0) {
                rtmc_error_print("Modulo by zero");
                return false;
            }
            result.i32 = a.i32 % b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        /* Logical Operations */
        case RTMC_OP_AND:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = a.i32 && b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_OR:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = a.i32 || b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_NOT:
            a = rtmc_stack_pop(ctx);
            result.i32 = !a.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_XOR:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = a.i32 ^ b.i32;
            rtmc_stack_push(ctx, result);
            break;
            
        /* Comparison Operations */
        case RTMC_OP_EQ:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = (a.i32 == b.i32) ? 1 : 0;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_NEQ:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = (a.i32 != b.i32) ? 1 : 0;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_LT:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = (a.i32 < b.i32) ? 1 : 0;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_LTE:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = (a.i32 <= b.i32) ? 1 : 0;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_GT:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = (a.i32 > b.i32) ? 1 : 0;
            rtmc_stack_push(ctx, result);
            break;
            
        case RTMC_OP_GTE:
            b = rtmc_stack_pop(ctx);
            a = rtmc_stack_pop(ctx);
            result.i32 = (a.i32 >= b.i32) ? 1 : 0;
            rtmc_stack_push(ctx, result);
            break;
            
        /* RTOS Instructions */
        case RTMC_OP_RTOS_CREATE_TASK: {
            rtmc_value_t func_addr_val = rtmc_stack_pop(ctx);
            rtmc_value_t task_id_val = rtmc_stack_pop(ctx);
            rtmc_value_t priority_val = rtmc_stack_pop(ctx);
            rtmc_value_t core_val = rtmc_stack_pop(ctx);
            rtmc_value_t stack_size_val = rtmc_stack_pop(ctx);
            
            /* Create a new task (simplified implementation) */
            if (vm->task_count < RTMC_MAX_TASKS) {
                rtmc_task_t* new_task = &vm->tasks[vm->task_count];
                new_task->id = task_id_val.u32;
                snprintf(new_task->name, sizeof(new_task->name), "Task-%u", new_task->id);
                new_task->func_addr = func_addr_val.u32;
                new_task->stack_size = stack_size_val.u32;
                new_task->priority = priority_val.u32;
                new_task->core = core_val.u32;
                new_task->state = RTMC_TASK_READY;
                new_task->pc = new_task->func_addr;
                new_task->stack_ptr = 0;
                new_task->call_stack_ptr = 0;
                new_task->call_depth = 0;
                
                /* Create task context */
                rtmc_task_context_t* new_ctx = (rtmc_task_context_t*)malloc(sizeof(rtmc_task_context_t));
                if (new_ctx) {
                    new_ctx->vm = vm;
                    new_ctx->task = new_task;
                    new_ctx->pc = new_task->func_addr;
                    new_ctx->stack_ptr = 0;
                    new_ctx->call_stack_ptr = 0;
                    new_ctx->call_depth = 0;
                    new_ctx->running = true;
                    
                    /* Create FreeRTOS task */
                    BaseType_t result = xTaskCreate(
                        rtmc_task_entry_point,
                        new_task->name,
                        new_task->stack_size / sizeof(StackType_t),
                        new_ctx,
                        new_task->priority,
                        &new_task->freertos_handle
                    );
                    
                    if (result == pdPASS) {
                        vm->task_count++;
                        if (vm->debug) {
                            rtmc_debug_print("Created task %s (ID: %u) at address %u",
                                new_task->name, new_task->id, new_task->func_addr);
                        }
                    } else {
                        rtmc_error_print("Failed to create FreeRTOS task");
                        free(new_ctx);
                    }
                }
            }
            break;
        }
        
        case RTMC_OP_RTOS_DELAY_MS: {
            a = rtmc_stack_pop(ctx);
            if (vm->debug) {
                rtmc_debug_print("Delaying %d ms", a.i32);
            }
            vTaskDelay(pdMS_TO_TICKS(a.i32));
            break;
        }
        
        case RTMC_OP_RTOS_SEMAPHORE_CREATE: {
            if (vm->semaphore_count < RTMC_MAX_SEMAPHORES) {
                rtmc_semaphore_t* sem = &vm->semaphores[vm->semaphore_count];
                sem->id = vm->semaphore_count;
                sem->count = 1;
                sem->max_count = 1;
                sem->freertos_handle = xSemaphoreCreateBinary();
                
                if (sem->freertos_handle) {
                    result.u32 = vm->semaphore_count;
                    vm->semaphore_count++;
                    rtmc_stack_push(ctx, result);
                    if (vm->debug) {
                        rtmc_debug_print("Created semaphore ID: %u", sem->id);
                    }
                } else {
                    result.u32 = 0;
                    rtmc_stack_push(ctx, result);
                    rtmc_error_print("Failed to create semaphore");
                }
            } else {
                result.u32 = 0;
                rtmc_stack_push(ctx, result);
            }
            break;
        }
        
        case RTMC_OP_RTOS_SEMAPHORE_TAKE: {
            rtmc_value_t timeout_val = rtmc_stack_pop(ctx);
            rtmc_value_t handle_val = rtmc_stack_pop(ctx);
            
            if (handle_val.u32 < vm->semaphore_count) {
                rtmc_semaphore_t* sem = &vm->semaphores[handle_val.u32];
                TickType_t timeout = (timeout_val.i32 == -1) ? portMAX_DELAY : pdMS_TO_TICKS(timeout_val.i32);
                
                BaseType_t take_result = xSemaphoreTake(sem->freertos_handle, timeout);
                result.i32 = (take_result == pdTRUE) ? 1 : 0;
                rtmc_stack_push(ctx, result);
                
                if (vm->debug) {
                    rtmc_debug_print("Semaphore take result: %d", result.i32);
                }
            } else {
                result.i32 = 0;
                rtmc_stack_push(ctx, result);
            }
            break;
        }
        
        case RTMC_OP_RTOS_SEMAPHORE_GIVE: {
            a = rtmc_stack_pop(ctx);
            if (a.u32 < vm->semaphore_count) {
                rtmc_semaphore_t* sem = &vm->semaphores[a.u32];
                xSemaphoreGive(sem->freertos_handle);
                if (vm->debug) {
                    rtmc_debug_print("Gave semaphore %u", a.u32);
                }
            }
            break;
        }
        
        case RTMC_OP_RTOS_YIELD:
            if (vm->debug) {
                rtmc_debug_print("Task yielding");
            }
            taskYIELD();
            break;
            
        /* Message Passing */
        case RTMC_OP_MSG_SEND: {
            uint32_t message_id = inst->operands[0].u32;
            rtmc_value_t payload = rtmc_stack_pop(ctx);
            
            /* Find message queue */
            for (uint32_t i = 0; i < vm->message_queue_count; i++) {
                if (vm->message_queues[i].id == message_id) {
                    BaseType_t send_result = xQueueSend(vm->message_queues[i].freertos_handle, &payload, 0);
                    if (vm->debug) {
                        rtmc_debug_print("Sent message to queue ID: %u, payload: %d, result: %d",
                            message_id, payload.i32, send_result);
                    }
                    break;
                }
            }
            break;
        }
        
        case RTMC_OP_MSG_RECV: {
            uint32_t message_id = inst->operands[0].u32;
            rtmc_value_t timeout_val = rtmc_stack_pop(ctx);
            
            /* Find message queue */
            for (uint32_t i = 0; i < vm->message_queue_count; i++) {
                if (vm->message_queues[i].id == message_id) {
                    rtmc_value_t received_msg;
                    TickType_t timeout = (timeout_val.i32 == -1) ? portMAX_DELAY : pdMS_TO_TICKS(timeout_val.i32);
                    
                    BaseType_t recv_result = xQueueReceive(vm->message_queues[i].freertos_handle, &received_msg, timeout);
                    if (recv_result == pdTRUE) {
                        rtmc_stack_push(ctx, received_msg);
                    } else {
                        result.i32 = -1; /* Timeout */
                        rtmc_stack_push(ctx, result);
                    }
                    
                    if (vm->debug) {
                        rtmc_debug_print("Received message from queue ID: %u, result: %d",
                            message_id, recv_result);
                    }
                    break;
                }
            }
            break;
        }
        
        /* Hardware Instructions */
        case RTMC_OP_HW_GPIO_INIT: {
            rtmc_value_t mode_val = rtmc_stack_pop(ctx);
            rtmc_value_t pin_val = rtmc_stack_pop(ctx);
            rtmc_hw_gpio_init(vm, pin_val.u32, mode_val.u32);
            break;
        }
        
        case RTMC_OP_HW_GPIO_SET: {
            rtmc_value_t value_val = rtmc_stack_pop(ctx);
            rtmc_value_t pin_val = rtmc_stack_pop(ctx);
            rtmc_hw_gpio_set(vm, pin_val.u32, value_val.u32);
            break;
        }
        
        case RTMC_OP_HW_GPIO_GET: {
            rtmc_value_t pin_val = rtmc_stack_pop(ctx);
            uint32_t gpio_value = rtmc_hw_gpio_get(vm, pin_val.u32);
            result.u32 = gpio_value;
            rtmc_stack_push(ctx, result);
            break;
        }
        
        /* Debug Instructions */
        case RTMC_OP_PRINT: {
            rtmc_value_t string_id_val = rtmc_stack_pop(ctx);
            if (string_id_val.u32 < vm->program->string_count) {
                rtmc_debug_print("DEBUG: %s", vm->program->strings[string_id_val.u32]);
            } else {
                rtmc_debug_print("DEBUG: <invalid string %u>", string_id_val.u32);
            }
            break;
        }
        
        case RTMC_OP_PRINTF: {
            uint32_t format_string_id = inst->operands[0].u32;
            uint32_t arg_count = inst->operands[1].u32;
            
            /* Pop arguments from stack */
            rtmc_value_t args[8]; /* Max 8 arguments */
            for (int i = arg_count - 1; i >= 0 && i < 8; i--) {
                args[i] = rtmc_stack_pop(ctx);
            }
            
            if (format_string_id < vm->program->string_count) {
                /* Simple printf implementation */
                const char* format = vm->program->strings[format_string_id];
                rtmc_debug_print("DEBUG: %s", format); /* Simplified - would need proper formatting */
            }
            break;
        }
        
        case RTMC_OP_HALT:
            ctx->running = false;
            rtmc_debug_print("Program halted");
            break;
            
        case RTMC_OP_NOP:
        case RTMC_OP_COMMENT:
            /* Do nothing */
            break;
            
        default:
            rtmc_error_print("Unknown opcode: %d", inst->opcode);
            return false;
    }
    
    return true;
}

/* ========================================================================== */
/* Hardware Abstraction Layer                                                */
/* ========================================================================== */

bool rtmc_hw_gpio_init(rtmc_vm_t* vm, uint32_t pin, uint32_t mode) {
    if (!vm || pin >= RTMC_MAX_GPIO_PINS) {
        rtmc_error_print("Invalid GPIO pin: %u", pin);
        return false;
    }
    
    rtmc_gpio_pin_t* gpio_pin = &vm->gpio_pins[pin];
    gpio_pin->pin = pin;
    gpio_pin->mode = mode; /* 0=input, 1=output */
    gpio_pin->value = 0;
    gpio_pin->pull = 0;
    gpio_pin->initialized = true;
    
    /* Initialize Pico GPIO */
    gpio_init(pin);
    if (mode == 1) {
        gpio_set_dir(pin, GPIO_OUT);
    } else {
        gpio_set_dir(pin, GPIO_IN);
    }
    
    if (vm->debug) {
        rtmc_debug_print("GPIO%u initialized as %s", pin, (mode == 1) ? "OUTPUT" : "INPUT");
    }
    
    return true;
}

bool rtmc_hw_gpio_set(rtmc_vm_t* vm, uint32_t pin, uint32_t value) {
    if (!vm || pin >= RTMC_MAX_GPIO_PINS) {
        rtmc_error_print("Invalid GPIO pin: %u", pin);
        return false;
    }
    
    rtmc_gpio_pin_t* gpio_pin = &vm->gpio_pins[pin];
    if (!gpio_pin->initialized) {
        rtmc_error_print("GPIO%u not initialized", pin);
        return false;
    }
    
    if (gpio_pin->mode != 1) {
        rtmc_error_print("GPIO%u not configured as output", pin);
        return false;
    }
    
    gpio_pin->value = value;
    gpio_put(pin, value != 0);
    
    if (vm->debug) {
        rtmc_debug_print("GPIO%u set to %u", pin, value);
    }
    
    return true;
}

uint32_t rtmc_hw_gpio_get(rtmc_vm_t* vm, uint32_t pin) {
    if (!vm || pin >= RTMC_MAX_GPIO_PINS) {
        rtmc_error_print("Invalid GPIO pin: %u", pin);
        return 0;
    }
    
    rtmc_gpio_pin_t* gpio_pin = &vm->gpio_pins[pin];
    if (!gpio_pin->initialized) {
        rtmc_error_print("GPIO%u not initialized", pin);
        return 0;
    }
    
    uint32_t value = gpio_get(pin) ? 1 : 0;
    gpio_pin->value = value;
    
    if (vm->debug) {
        rtmc_debug_print("GPIO%u read: %u", pin, value);
    }
    
    return value;
}

bool rtmc_hw_timer_init(rtmc_vm_t* vm, uint32_t timer_id, uint32_t mode, uint32_t freq) {
    if (!vm || timer_id >= RTMC_MAX_TIMERS) {
        rtmc_error_print("Invalid timer ID: %u", timer_id);
        return false;
    }
    
    rtmc_timer_t* timer = &vm->timers[timer_id];
    timer->id = timer_id;
    timer->mode = mode;
    timer->frequency = freq;
    timer->running = false;
    timer->count = 0;
    timer->pwm_duty = 0;
    timer->initialized = true;
    
    /* Initialize PWM for Pico (simplified) */
    timer->slice_num = pwm_gpio_to_slice_num(timer_id); /* Assuming timer_id maps to GPIO */
    timer->channel = pwm_gpio_to_channel(timer_id);
    
    if (vm->debug) {
        rtmc_debug_print("Timer%u initialized: mode=%u, freq=%uHz", timer_id, mode, freq);
    }
    
    return true;
}

bool rtmc_hw_timer_start(rtmc_vm_t* vm, uint32_t timer_id) {
    if (!vm || timer_id >= RTMC_MAX_TIMERS) {
        rtmc_error_print("Invalid timer ID: %u", timer_id);
        return false;
    }
    
    rtmc_timer_t* timer = &vm->timers[timer_id];
    if (!timer->initialized) {
        rtmc_error_print("Timer%u not initialized", timer_id);
        return false;
    }
    
    timer->running = true;
    pwm_set_enabled(timer->slice_num, true);
    
    if (vm->debug) {
        rtmc_debug_print("Timer%u started", timer_id);
    }
    
    return true;
}

bool rtmc_hw_timer_stop(rtmc_vm_t* vm, uint32_t timer_id) {
    if (!vm || timer_id >= RTMC_MAX_TIMERS) {
        rtmc_error_print("Invalid timer ID: %u", timer_id);
        return false;
    }
    
    rtmc_timer_t* timer = &vm->timers[timer_id];
    if (!timer->initialized) {
        rtmc_error_print("Timer%u not initialized", timer_id);
        return false;
    }
    
    timer->running = false;
    pwm_set_enabled(timer->slice_num, false);
    
    if (vm->debug) {
        rtmc_debug_print("Timer%u stopped", timer_id);
    }
    
    return true;
}

bool rtmc_hw_timer_set_pwm_duty(rtmc_vm_t* vm, uint32_t timer_id, uint32_t duty) {
    if (!vm || timer_id >= RTMC_MAX_TIMERS) {
        rtmc_error_print("Invalid timer ID: %u", timer_id);
        return false;
    }
    
    rtmc_timer_t* timer = &vm->timers[timer_id];
    if (!timer->initialized) {
        rtmc_error_print("Timer%u not initialized", timer_id);
        return false;
    }
    
    timer->pwm_duty = duty;
    
    /* Set PWM duty cycle (0-100%) */
    uint16_t wrap = pwm_get_wrap(timer->slice_num);
    uint16_t level = (wrap * duty) / 100;
    pwm_set_chan_level(timer->slice_num, timer->channel, level);
    
    if (vm->debug) {
        rtmc_debug_print("Timer%u PWM duty set to %u%%", timer_id, duty);
    }
    
    return true;
}

bool rtmc_hw_adc_init(rtmc_vm_t* vm, uint32_t pin) {
    if (!vm) {
        rtmc_error_print("NULL VM pointer");
        return false;
    }
    
    /* Find free ADC channel */
    for (uint32_t i = 0; i < RTMC_MAX_ADC_CHANNELS; i++) {
        if (!vm->adc_channels[i].initialized) {
            vm->adc_channels[i].pin = pin;
            vm->adc_channels[i].channel = i;
            vm->adc_channels[i].initialized = true;
            
            /* Initialize Pico ADC */
            adc_init();
            adc_gpio_init(pin);
            adc_select_input(i);
            
            if (vm->debug) {
                rtmc_debug_print("ADC%u initialized for pin %u", i, pin);
            }
            
            return true;
        }
    }
    
    rtmc_error_print("No free ADC channels available");
    return false;
}

uint32_t rtmc_hw_adc_read(rtmc_vm_t* vm, uint32_t pin) {
    if (!vm) {
        rtmc_error_print("NULL VM pointer");
        return 0;
    }
    
    /* Find ADC channel for pin */
    for (uint32_t i = 0; i < RTMC_MAX_ADC_CHANNELS; i++) {
        if (vm->adc_channels[i].initialized && vm->adc_channels[i].pin == pin) {
            adc_select_input(vm->adc_channels[i].channel);
            uint16_t adc_value = adc_read();
            
            if (vm->debug) {
                rtmc_debug_print("ADC%u read: %u", i, adc_value);
            }
            
            return adc_value;
        }
    }
    
    rtmc_error_print("ADC for pin %u not initialized", pin);
    return 0;
}