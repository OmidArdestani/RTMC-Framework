/**
 * @file rtmc_interpreter.h
 * @brief RT-Micro-C Bytecode Interpreter for FreeRTOS on Raspberry Pi Pico
 * 
 * This interpreter executes RT-Micro-C bytecode programs on FreeRTOS running
 * on the Raspberry Pi Pico (RP2040). It provides RTOS task management,
 * hardware abstraction, and message passing capabilities.
 * 
 * @author Omidardestani
 * @date 2025
 */

#ifndef RTMC_INTERPRETER_H
#define RTMC_INTERPRETER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* FreeRTOS includes */
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "timers.h"

/* Pico SDK includes */
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/timer.h"
#include "hardware/adc.h"
#include "hardware/uart.h"
#include "hardware/spi.h"
#include "hardware/i2c.h"
#include "hardware/pwm.h"

/* Configuration */
#define RTMC_MAX_INSTRUCTIONS       10000
#define RTMC_MAX_CONSTANTS         1000
#define RTMC_MAX_STRINGS           500
#define RTMC_MAX_FUNCTIONS         100
#define RTMC_MAX_SYMBOLS           1000
#define RTMC_MAX_TASKS             16
#define RTMC_MAX_SEMAPHORES        32
#define RTMC_MAX_MESSAGE_QUEUES    16
#define RTMC_MAX_STACK_SIZE        256
#define RTMC_MAX_CALL_STACK        32
#define RTMC_MAX_MEMORY_SIZE       4096
#define RTMC_MAX_GPIO_PINS         30
#define RTMC_MAX_TIMERS            8
#define RTMC_MAX_ADC_CHANNELS      4

/* RTMC Bytecode Opcodes - Must match Python implementation */
typedef enum {
    /* Control Flow Instructions */
    RTMC_OP_JUMP = 1,
    RTMC_OP_JUMPIF_TRUE,
    RTMC_OP_JUMPIF_FALSE,
    RTMC_OP_CALL,
    RTMC_OP_RET,
    
    /* Data Manipulation - Load/Store */
    RTMC_OP_LOAD_CONST,
    RTMC_OP_LOAD_VAR,
    RTMC_OP_STORE_VAR,
    RTMC_OP_LOAD_STRUCT_MEMBER,
    RTMC_OP_STORE_STRUCT_MEMBER,
    RTMC_OP_LOAD_STRUCT_MEMBER_BIT,
    RTMC_OP_STORE_STRUCT_MEMBER_BIT,
    
    /* Pointer Instructions */
    RTMC_OP_LOAD_ADDR,
    RTMC_OP_LOAD_DEREF,
    RTMC_OP_STORE_DEREF,
    
    /* Arithmetic and Logical */
    RTMC_OP_ADD,
    RTMC_OP_SUB,
    RTMC_OP_MUL,
    RTMC_OP_DIV,
    RTMC_OP_MOD,
    RTMC_OP_AND,
    RTMC_OP_OR,
    RTMC_OP_NOT,
    RTMC_OP_XOR,
    
    /* Comparisons */
    RTMC_OP_EQ,
    RTMC_OP_NEQ,
    RTMC_OP_LT,
    RTMC_OP_LTE,
    RTMC_OP_GT,
    RTMC_OP_GTE,
    
    /* Memory Management */
    RTMC_OP_ALLOC_VAR,
    RTMC_OP_FREE_VAR,
    RTMC_OP_ALLOC_STRUCT,
    RTMC_OP_ALLOC_FRAME,
    RTMC_OP_FREE_FRAME,
    
    /* Array Instructions */
    RTMC_OP_ALLOC_ARRAY,
    RTMC_OP_LOAD_ARRAY_ELEM,
    RTMC_OP_STORE_ARRAY_ELEM,
    
    /* RTOS Task Instructions */
    RTMC_OP_RTOS_CREATE_TASK,
    RTMC_OP_RTOS_DELETE_TASK,
    RTMC_OP_RTOS_DELAY_MS,
    RTMC_OP_RTOS_SEMAPHORE_CREATE,
    RTMC_OP_RTOS_SEMAPHORE_TAKE,
    RTMC_OP_RTOS_SEMAPHORE_GIVE,
    RTMC_OP_RTOS_YIELD,
    RTMC_OP_RTOS_SUSPEND_TASK,
    RTMC_OP_RTOS_RESUME_TASK,
    
    /* Global Variable Declaration */
    RTMC_OP_GLOBAL_VAR_DECLARE,
    
    /* Message Passing Instructions */
    RTMC_OP_MSG_DECLARE,
    RTMC_OP_MSG_SEND,
    RTMC_OP_MSG_RECV,
    
    /* Hardware Access - GPIO */
    RTMC_OP_HW_GPIO_INIT,
    RTMC_OP_HW_GPIO_SET,
    RTMC_OP_HW_GPIO_GET,
    
    /* Hardware Access - Timers */
    RTMC_OP_HW_TIMER_INIT,
    RTMC_OP_HW_TIMER_START,
    RTMC_OP_HW_TIMER_STOP,
    RTMC_OP_HW_TIMER_SET_PWM_DUTY,
    
    /* Hardware Access - ADC */
    RTMC_OP_HW_ADC_INIT,
    RTMC_OP_HW_ADC_READ,
    
    /* Hardware Access - Communication */
    RTMC_OP_HW_UART_WRITE,
    RTMC_OP_HW_SPI_TRANSFER,
    RTMC_OP_HW_I2C_WRITE,
    RTMC_OP_HW_I2C_READ,
    
    /* Debugging / System */
    RTMC_OP_PRINT,
    RTMC_OP_PRINTF,
    RTMC_OP_DBG_BREAKPOINT,
    RTMC_OP_SYSCALL,
    
    /* Special */
    RTMC_OP_HALT,
    RTMC_OP_NOP,
    RTMC_OP_COMMENT
} rtmc_opcode_t;

/* RTMC Value Type */
typedef union {
    int32_t i32;
    uint32_t u32;
    float f32;
    void* ptr;
} rtmc_value_t;

/* RTMC Instruction */
typedef struct {
    rtmc_opcode_t opcode;
    uint32_t operand_count;
    rtmc_value_t operands[4];  /* Max 4 operands per instruction */
    uint32_t line;             /* Source line for debugging */
} rtmc_instruction_t;

/* RTMC Task State */
typedef enum {
    RTMC_TASK_READY = 0,
    RTMC_TASK_RUNNING,
    RTMC_TASK_BLOCKED,
    RTMC_TASK_SUSPENDED,
    RTMC_TASK_DELETED
} rtmc_task_state_t;

/* RTMC Task */
typedef struct {
    uint32_t id;
    char name[32];
    uint32_t func_addr;
    uint32_t stack_size;
    uint32_t priority;
    uint32_t core;
    rtmc_task_state_t state;
    TaskHandle_t freertos_handle;
    uint32_t pc;
    rtmc_value_t stack[RTMC_MAX_STACK_SIZE];
    uint32_t stack_ptr;
    uint32_t call_stack[RTMC_MAX_CALL_STACK];
    uint32_t call_stack_ptr;
    uint32_t call_depth;
} rtmc_task_t;

/* RTMC Semaphore */
typedef struct {
    uint32_t id;
    SemaphoreHandle_t freertos_handle;
    uint32_t count;
    uint32_t max_count;
} rtmc_semaphore_t;

/* RTMC Message Queue */
typedef struct {
    uint32_t id;
    char name[32];
    uint32_t message_type;
    QueueHandle_t freertos_handle;
    uint32_t max_size;
} rtmc_message_queue_t;

/* RTMC Hardware GPIO Pin */
typedef struct {
    uint32_t pin;
    uint32_t mode;      /* 0=input, 1=output */
    uint32_t value;
    uint32_t pull;      /* 0=none, 1=up, 2=down */
    bool initialized;
} rtmc_gpio_pin_t;

/* RTMC Hardware Timer */
typedef struct {
    uint32_t id;
    uint32_t mode;
    uint32_t frequency;
    bool running;
    uint32_t count;
    uint32_t pwm_duty;
    bool initialized;
    uint32_t slice_num;     /* PWM slice number for Pico */
    uint32_t channel;       /* PWM channel */
} rtmc_timer_t;

/* RTMC Hardware ADC Channel */
typedef struct {
    uint32_t pin;
    uint32_t channel;
    bool initialized;
} rtmc_adc_channel_t;

/* RTMC Program */
typedef struct {
    rtmc_instruction_t instructions[RTMC_MAX_INSTRUCTIONS];
    uint32_t instruction_count;
    
    rtmc_value_t constants[RTMC_MAX_CONSTANTS];
    uint32_t constant_count;
    
    char strings[RTMC_MAX_STRINGS][64];
    uint32_t string_count;
    
    struct {
        char name[32];
        uint32_t address;
    } functions[RTMC_MAX_FUNCTIONS];
    uint32_t function_count;
    
    struct {
        char name[32];
        uint32_t address;
    } symbols[RTMC_MAX_SYMBOLS];
    uint32_t symbol_count;
} rtmc_program_t;

/* RTMC Virtual Machine */
typedef struct {
    /* Program */
    rtmc_program_t* program;
    bool running;
    bool debug;
    bool trace;
    
    /* Memory */
    rtmc_value_t memory[RTMC_MAX_MEMORY_SIZE];
    
    /* RTOS Objects */
    rtmc_task_t tasks[RTMC_MAX_TASKS];
    uint32_t task_count;
    
    rtmc_semaphore_t semaphores[RTMC_MAX_SEMAPHORES];
    uint32_t semaphore_count;
    
    rtmc_message_queue_t message_queues[RTMC_MAX_MESSAGE_QUEUES];
    uint32_t message_queue_count;
    
    /* Hardware State */
    rtmc_gpio_pin_t gpio_pins[RTMC_MAX_GPIO_PINS];
    rtmc_timer_t timers[RTMC_MAX_TIMERS];
    rtmc_adc_channel_t adc_channels[RTMC_MAX_ADC_CHANNELS];
    
    /* Task Management */
    TaskHandle_t scheduler_task;
    bool scheduler_running;
} rtmc_vm_t;

/* RTMC Task Context for FreeRTOS tasks */
typedef struct {
    rtmc_vm_t* vm;
    rtmc_task_t* task;
    uint32_t pc;
    rtmc_value_t stack[RTMC_MAX_STACK_SIZE];
    uint32_t stack_ptr;
    uint32_t call_stack[RTMC_MAX_CALL_STACK];
    uint32_t call_stack_ptr;
    uint32_t call_depth;
    bool running;
} rtmc_task_context_t;

/* Function Prototypes */

/* Virtual Machine Core */
rtmc_vm_t* rtmc_vm_create(bool debug, bool trace);
void rtmc_vm_destroy(rtmc_vm_t* vm);
bool rtmc_vm_load_program(rtmc_vm_t* vm, rtmc_program_t* program);
bool rtmc_vm_run(rtmc_vm_t* vm);
void rtmc_vm_stop(rtmc_vm_t* vm);

/* Program Management */
rtmc_program_t* rtmc_program_create(void);
void rtmc_program_destroy(rtmc_program_t* program);
bool rtmc_program_load_from_binary(rtmc_program_t* program, const uint8_t* data, size_t size);

/* Task Management */
bool rtmc_vm_create_main_task(rtmc_vm_t* vm, uint32_t main_addr);
void rtmc_task_entry_point(void* pvParameters);

/* Instruction Execution */
bool rtmc_execute_instruction(rtmc_task_context_t* ctx, const rtmc_instruction_t* inst);

/* Stack Operations */
void rtmc_stack_push(rtmc_task_context_t* ctx, rtmc_value_t value);
rtmc_value_t rtmc_stack_pop(rtmc_task_context_t* ctx);
rtmc_value_t rtmc_stack_peek(rtmc_task_context_t* ctx);

/* Hardware Abstraction */
bool rtmc_hw_gpio_init(rtmc_vm_t* vm, uint32_t pin, uint32_t mode);
bool rtmc_hw_gpio_set(rtmc_vm_t* vm, uint32_t pin, uint32_t value);
uint32_t rtmc_hw_gpio_get(rtmc_vm_t* vm, uint32_t pin);

bool rtmc_hw_timer_init(rtmc_vm_t* vm, uint32_t timer_id, uint32_t mode, uint32_t freq);
bool rtmc_hw_timer_start(rtmc_vm_t* vm, uint32_t timer_id);
bool rtmc_hw_timer_stop(rtmc_vm_t* vm, uint32_t timer_id);
bool rtmc_hw_timer_set_pwm_duty(rtmc_vm_t* vm, uint32_t timer_id, uint32_t duty);

bool rtmc_hw_adc_init(rtmc_vm_t* vm, uint32_t pin);
uint32_t rtmc_hw_adc_read(rtmc_vm_t* vm, uint32_t pin);

/* Utility Functions */
void rtmc_debug_print(const char* format, ...);
void rtmc_error_print(const char* format, ...);
uint32_t rtmc_find_function_address(rtmc_vm_t* vm, const char* name);

/* Error Codes */
typedef enum {
    RTMC_OK = 0,
    RTMC_ERROR_NULL_POINTER,
    RTMC_ERROR_INVALID_OPCODE,
    RTMC_ERROR_STACK_OVERFLOW,
    RTMC_ERROR_STACK_UNDERFLOW,
    RTMC_ERROR_DIVISION_BY_ZERO,
    RTMC_ERROR_INVALID_MEMORY_ACCESS,
    RTMC_ERROR_TASK_CREATION_FAILED,
    RTMC_ERROR_SEMAPHORE_CREATION_FAILED,
    RTMC_ERROR_QUEUE_CREATION_FAILED,
    RTMC_ERROR_HARDWARE_INIT_FAILED,
    RTMC_ERROR_INVALID_GPIO_PIN,
    RTMC_ERROR_INVALID_TIMER_ID,
    RTMC_ERROR_INVALID_ADC_CHANNEL,
    RTMC_ERROR_PROGRAM_LOAD_FAILED
} rtmc_error_t;

#endif /* RTMC_INTERPRETER_H */