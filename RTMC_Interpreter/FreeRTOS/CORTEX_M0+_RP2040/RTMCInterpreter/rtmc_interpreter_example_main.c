/**
 * @file rtmc_interpreter_example_main.c
 * @brief RTMC Interpreter Example with UART Control
 * 
 * This example demonstrates the RTMC interpreter with UART-based control:
 * - Receives bytecode files through UART
 * - Provides command interface to run/stop/status
 * - Supports real-time program loading and execution
 * 
 * UART Commands:
 * - "LOAD <size>" - Load bytecode program of specified size
 * - "RUN" - Start executing the loaded program
 * - "STOP" - Stop the currently running program
 * - "STATUS" - Get current VM status
 * - "RESET" - Reset the VM and clear loaded program
 * - "HELP" - Show available commands
 * 
 * @author Based on RTMC Framework
 * @date 2025
 */

#include "rtmc_interpreter.h"
#include "rtmc_binary_loader.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* UART Configuration */
#define UART_ID         uart0
#define UART_BAUD_RATE  115200
#define UART_TX_PIN     0
#define UART_RX_PIN     1

/* Buffer sizes */
#define UART_RX_BUFFER_SIZE     1024
#define UART_COMMAND_BUFFER_SIZE 256
#define MAX_BYTECODE_SIZE       (64 * 1024)  /* 64KB max program size */

/* Command parsing */
#define MAX_COMMAND_ARGS        4

/* Application state */
typedef enum {
    APP_STATE_IDLE,
    APP_STATE_LOADING,
    APP_STATE_RUNNING,
    APP_STATE_ERROR
} app_state_t;

typedef struct {
    app_state_t state;
    rtmc_vm_t* vm;
    rtmc_program_t* program;
    uint8_t* bytecode_buffer;
    size_t bytecode_size;
    size_t bytes_received;
    bool vm_running;
} rtmc_app_t;

/* Global application instance */
static rtmc_app_t g_app = {0};

/* UART receive buffer and management */
static uint8_t uart_rx_buffer[UART_RX_BUFFER_SIZE];
static volatile size_t uart_rx_head = 0;
static volatile size_t uart_rx_tail = 0;

/* Command buffer */
static char command_buffer[UART_COMMAND_BUFFER_SIZE];
static size_t command_length = 0;

/* Function prototypes */
static void uart_init_custom(void);
static void uart_puts_custom(const char* str);
static void uart_printf_custom(const char* format, ...);
static bool uart_gets_line(char* buffer, size_t max_len, uint32_t timeout_ms);
static size_t uart_read_bytes(uint8_t* buffer, size_t max_bytes, uint32_t timeout_ms);
static void process_command(const char* command);
static void handle_load_command(const char* args);
static void handle_run_command(void);
static void handle_stop_command(void);
static void handle_status_command(void);
static void handle_reset_command(void);
static void handle_help_command(void);
static void show_welcome_message(void);
static void app_init(void);
static void app_cleanup(void);

/* Command processing task */
void command_task(void *pvParameters);

/* VM monitoring task */
void monitor_task(void *pvParameters);

/* ========================================================================== */
/* UART Functions                                                            */
/* ========================================================================== */

static void uart_init_custom(void) {
    /* Initialize UART */
    uart_init(UART_ID, UART_BAUD_RATE);
    
    /* Set the GPIO pin mux to the UART */
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    
    /* Set UART flow control CTS/RTS, we don't want these, so turn them off */
    uart_set_hw_flow(UART_ID, false, false);
    
    /* Set data format */
    uart_set_format(UART_ID, 8, 1, UART_PARITY_NONE);
    
    /* Turn off FIFO's - we want to do this character by character */
    uart_set_fifo_enabled(UART_ID, false);
}

static void uart_puts_custom(const char* str) {
    uart_puts(UART_ID, str);
}

static void uart_printf_custom(const char* format, ...) {
    va_list args;
    char buffer[512];
    
    va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    
    uart_puts_custom(buffer);
}

static bool uart_gets_line(char* buffer, size_t max_len, uint32_t timeout_ms) {
    size_t index = 0;
    absolute_time_t timeout_time = make_timeout_time_ms(timeout_ms);
    
    while (index < max_len - 1) {
        /* Check for timeout */
        if (timeout_ms > 0 && absolute_time_diff_us(get_absolute_time(), timeout_time) <= 0) {
            return false;
        }
        
        /* Check if character is available */
        if (uart_is_readable(UART_ID)) {
            char c = uart_getc(UART_ID);
            
            /* Handle different line endings */
            if (c == '\r' || c == '\n') {
                buffer[index] = '\0';
                return index > 0; /* Return true if we got some characters */
            }
            
            /* Handle backspace */
            if (c == '\b' || c == 127) { /* Backspace or DEL */
                if (index > 0) {
                    index--;
                    uart_puts_custom("\b \b"); /* Echo backspace */
                }
                continue;
            }
            
            /* Only accept printable characters */
            if (isprint(c)) {
                buffer[index++] = c;
                uart_putc(UART_ID, c); /* Echo character */
            }
        } else {
            /* Small delay to prevent busy waiting */
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
    
    buffer[index] = '\0';
    return index > 0;
}

static size_t uart_read_bytes(uint8_t* buffer, size_t max_bytes, uint32_t timeout_ms) {
    size_t bytes_read = 0;
    absolute_time_t timeout_time = make_timeout_time_ms(timeout_ms);
    
    while (bytes_read < max_bytes) {
        /* Check for timeout */
        if (timeout_ms > 0 && absolute_time_diff_us(get_absolute_time(), timeout_time) <= 0) {
            break;
        }
        
        /* Check if byte is available */
        if (uart_is_readable(UART_ID)) {
            buffer[bytes_read++] = uart_getc(UART_ID);
        } else {
            /* Small delay to prevent busy waiting */
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
    
    return bytes_read;
}

/* ========================================================================== */
/* Application Functions                                                     */
/* ========================================================================== */

static void app_init(void) {
    memset(&g_app, 0, sizeof(g_app));
    g_app.state = APP_STATE_IDLE;
    g_app.vm_running = false;
    
    /* Allocate bytecode buffer */
    g_app.bytecode_buffer = malloc(MAX_BYTECODE_SIZE);
    if (!g_app.bytecode_buffer) {
        uart_printf_custom("ERROR: Failed to allocate bytecode buffer\r\n");
        return;
    }
    
    uart_printf_custom("RTMC Interpreter initialized successfully\r\n");
}

static void app_cleanup(void) {
    if (g_app.vm) {
        rtmc_vm_stop(g_app.vm);
        rtmc_vm_destroy(g_app.vm);
        g_app.vm = NULL;
    }
    
    if (g_app.program) {
        rtmc_program_destroy(g_app.program);
        g_app.program = NULL;
    }
    
    if (g_app.bytecode_buffer) {
        free(g_app.bytecode_buffer);
        g_app.bytecode_buffer = NULL;
    }
    
    g_app.state = APP_STATE_IDLE;
    g_app.vm_running = false;
    g_app.bytecode_size = 0;
    g_app.bytes_received = 0;
}

/* ========================================================================== */
/* Command Handlers                                                          */
/* ========================================================================== */

static void handle_load_command(const char* args) {
    if (g_app.state == APP_STATE_RUNNING) {
        uart_printf_custom("ERROR: Cannot load while program is running. Stop first.\r\n");
        return;
    }
    
    /* Parse size argument */
    size_t size = 0;
    if (sscanf(args, "%zu", &size) != 1 || size == 0 || size > MAX_BYTECODE_SIZE) {
        uart_printf_custom("ERROR: Invalid size. Must be 1-%d bytes\r\n", MAX_BYTECODE_SIZE);
        return;
    }
    
    uart_printf_custom("Loading %zu bytes of bytecode...\r\n", size);
    uart_printf_custom("Send binary data now (timeout: 30 seconds)\r\n");
    
    g_app.state = APP_STATE_LOADING;
    g_app.bytecode_size = size;
    g_app.bytes_received = 0;
    
    /* Receive bytecode data */
    size_t bytes_read = uart_read_bytes(g_app.bytecode_buffer, size, 30000); /* 30 second timeout */
    
    if (bytes_read != size) {
        uart_printf_custom("ERROR: Received %zu bytes, expected %zu\r\n", bytes_read, size);
        g_app.state = APP_STATE_ERROR;
        return;
    }
    
    uart_printf_custom("Received %zu bytes. Parsing bytecode...\r\n", bytes_read);
    
    /* Create new program */
    if (g_app.program) {
        rtmc_program_destroy(g_app.program);
    }
    g_app.program = rtmc_program_create();
    if (!g_app.program) {
        uart_printf_custom("ERROR: Failed to create program structure\r\n");
        g_app.state = APP_STATE_ERROR;
        return;
    }
    
    /* Load binary program */
    if (!rtmc_load_binary_program(g_app.program, g_app.bytecode_buffer, bytes_read)) {
        uart_printf_custom("ERROR: Failed to parse bytecode\r\n");
        rtmc_program_destroy(g_app.program);
        g_app.program = NULL;
        g_app.state = APP_STATE_ERROR;
        return;
    }
    
    uart_printf_custom("Bytecode loaded successfully!\r\n");
    uart_printf_custom("  Instructions: %u\r\n", g_app.program->instruction_count);
    uart_printf_custom("  Constants: %u\r\n", g_app.program->constant_count);
    uart_printf_custom("  Strings: %u\r\n", g_app.program->string_count);
    uart_printf_custom("  Functions: %u\r\n", g_app.program->function_count);
    uart_printf_custom("  Symbols: %u\r\n", g_app.program->symbol_count);
    
    g_app.state = APP_STATE_IDLE;
}

static void handle_run_command(void) {
    if (!g_app.program) {
        uart_printf_custom("ERROR: No program loaded. Use LOAD command first.\r\n");
        return;
    }
    
    if (g_app.state == APP_STATE_RUNNING) {
        uart_printf_custom("ERROR: Program is already running\r\n");
        return;
    }
    
    uart_printf_custom("Starting RTMC Virtual Machine...\r\n");
    
    /* Create VM */
    g_app.vm = rtmc_vm_create(true, false); /* debug=true, trace=false */
    if (!g_app.vm) {
        uart_printf_custom("ERROR: Failed to create VM\r\n");
        g_app.state = APP_STATE_ERROR;
        return;
    }
    
    /* Load program into VM */
    if (!rtmc_vm_load_program(g_app.vm, g_app.program)) {
        uart_printf_custom("ERROR: Failed to load program into VM\r\n");
        rtmc_vm_destroy(g_app.vm);
        g_app.vm = NULL;
        g_app.state = APP_STATE_ERROR;
        return;
    }
    
    /* Run VM */
    if (!rtmc_vm_run(g_app.vm)) {
        uart_printf_custom("ERROR: Failed to start VM\r\n");
        rtmc_vm_destroy(g_app.vm);
        g_app.vm = NULL;
        g_app.state = APP_STATE_ERROR;
        return;
    }
    
    g_app.state = APP_STATE_RUNNING;
    g_app.vm_running = true;
    uart_printf_custom("VM started successfully. Program is now running.\r\n");
}

static void handle_stop_command(void) {
    if (g_app.state != APP_STATE_RUNNING) {
        uart_printf_custom("ERROR: No program is currently running\r\n");
        return;
    }
    
    uart_printf_custom("Stopping VM...\r\n");
    
    if (g_app.vm) {
        rtmc_vm_stop(g_app.vm);
        rtmc_vm_destroy(g_app.vm);
        g_app.vm = NULL;
    }
    
    g_app.state = APP_STATE_IDLE;
    g_app.vm_running = false;
    uart_printf_custom("VM stopped.\r\n");
}

static void handle_status_command(void) {
    uart_printf_custom("=== RTMC Interpreter Status ===\r\n");
    
    switch (g_app.state) {
        case APP_STATE_IDLE:
            uart_printf_custom("State: IDLE\r\n");
            break;
        case APP_STATE_LOADING:
            uart_printf_custom("State: LOADING\r\n");
            break;
        case APP_STATE_RUNNING:
            uart_printf_custom("State: RUNNING\r\n");
            break;
        case APP_STATE_ERROR:
            uart_printf_custom("State: ERROR\r\n");
            break;
    }
    
    uart_printf_custom("Program loaded: %s\r\n", g_app.program ? "YES" : "NO");
    uart_printf_custom("VM running: %s\r\n", g_app.vm_running ? "YES" : "NO");
    
    if (g_app.program) {
        uart_printf_custom("Program details:\r\n");
        uart_printf_custom("  Instructions: %u\r\n", g_app.program->instruction_count);
        uart_printf_custom("  Functions: %u\r\n", g_app.program->function_count);
        uart_printf_custom("  Constants: %u\r\n", g_app.program->constant_count);
        uart_printf_custom("  Strings: %u\r\n", g_app.program->string_count);
    }
    
    if (g_app.vm) {
        uart_printf_custom("VM details:\r\n");
        uart_printf_custom("  Tasks: %u\r\n", g_app.vm->task_count);
        uart_printf_custom("  Semaphores: %u\r\n", g_app.vm->semaphore_count);
        uart_printf_custom("  Message queues: %u\r\n", g_app.vm->message_queue_count);
    }
    
    /* System information */
    uart_printf_custom("System info:\r\n");
    uart_printf_custom("  Free heap: %u bytes\r\n", xPortGetFreeHeapSize());
    uart_printf_custom("  FreeRTOS tasks: %u\r\n", uxTaskGetNumberOfTasks());
    uart_printf_custom("================================\r\n");
}

static void handle_reset_command(void) {
    uart_printf_custom("Resetting RTMC Interpreter...\r\n");
    app_cleanup();
    app_init();
    uart_printf_custom("Reset complete.\r\n");
}

static void handle_help_command(void) {
    uart_printf_custom("=== RTMC Interpreter Commands ===\r\n");
    uart_printf_custom("LOAD <size>  - Load bytecode program of <size> bytes\r\n");
    uart_printf_custom("RUN          - Start executing the loaded program\r\n");
    uart_printf_custom("STOP         - Stop the currently running program\r\n");
    uart_printf_custom("STATUS       - Show current VM status and information\r\n");
    uart_printf_custom("RESET        - Reset VM and clear loaded program\r\n");
    uart_printf_custom("HELP         - Show this help message\r\n");
    uart_printf_custom("\r\n");
    uart_printf_custom("Example usage:\r\n");
    uart_printf_custom("1. LOAD 1024      # Prepare to load 1024 bytes\r\n");
    uart_printf_custom("2. <send binary>  # Send your .vmb file data\r\n");
    uart_printf_custom("3. RUN            # Execute the program\r\n");
    uart_printf_custom("4. STATUS         # Check execution status\r\n");
    uart_printf_custom("5. STOP           # Stop execution\r\n");
    uart_printf_custom("===================================\r\n");
}

static void show_welcome_message(void) {
    uart_printf_custom("\r\n");
    uart_printf_custom("============================================\r\n");
    uart_printf_custom("    RTMC Interpreter for Raspberry Pi Pico\r\n");
    uart_printf_custom("    Real-Time Micro-C Bytecode Execution\r\n");
    uart_printf_custom("============================================\r\n");
    uart_printf_custom("Version: 1.0\r\n");
    uart_printf_custom("Build: %s %s\r\n", __DATE__, __TIME__);
    uart_printf_custom("Free heap: %u bytes\r\n", xPortGetFreeHeapSize());
    uart_printf_custom("\r\n");
    uart_printf_custom("Type 'HELP' for available commands\r\n");
    uart_printf_custom("\r\n");
}

/* ========================================================================== */
/* Command Processing                                                        */
/* ========================================================================== */

static void process_command(const char* command) {
    /* Skip leading whitespace */
    while (*command && isspace(*command)) {
        command++;
    }
    
    /* Check for empty command */
    if (*command == '\0') {
        return;
    }
    
    /* Convert to uppercase for case-insensitive comparison */
    char cmd_upper[UART_COMMAND_BUFFER_SIZE];
    strncpy(cmd_upper, command, sizeof(cmd_upper) - 1);
    cmd_upper[sizeof(cmd_upper) - 1] = '\0';
    
    for (char* p = cmd_upper; *p; p++) {
        *p = toupper(*p);
    }
    
    /* Parse command and arguments */
    char* args = strchr(cmd_upper, ' ');
    if (args) {
        *args = '\0';
        args++;
        /* Skip leading whitespace in args */
        while (*args && isspace(*args)) {
            args++;
        }
    }
    
    /* Handle commands */
    if (strcmp(cmd_upper, "LOAD") == 0) {
        if (args) {
            handle_load_command(args);
        } else {
            uart_printf_custom("ERROR: LOAD command requires size argument\r\n");
            uart_printf_custom("Usage: LOAD <size>\r\n");
        }
    }
    else if (strcmp(cmd_upper, "RUN") == 0) {
        handle_run_command();
    }
    else if (strcmp(cmd_upper, "STOP") == 0) {
        handle_stop_command();
    }
    else if (strcmp(cmd_upper, "STATUS") == 0) {
        handle_status_command();
    }
    else if (strcmp(cmd_upper, "RESET") == 0) {
        handle_reset_command();
    }
    else if (strcmp(cmd_upper, "HELP") == 0) {
        handle_help_command();
    }
    else {
        uart_printf_custom("ERROR: Unknown command '%s'\r\n", cmd_upper);
        uart_printf_custom("Type 'HELP' for available commands\r\n");
    }
}

/* ========================================================================== */
/* FreeRTOS Tasks                                                           */
/* ========================================================================== */

void command_task(void *pvParameters) {
    (void)pvParameters;
    
    char command_line[UART_COMMAND_BUFFER_SIZE];
    
    uart_printf_custom("Command task started\r\n");
    uart_printf_custom("Ready for commands> ");
    
    while (1) {
        /* Read command from UART */
        if (uart_gets_line(command_line, sizeof(command_line), 100)) { /* 100ms timeout */
            uart_printf_custom("\r\n"); /* New line after command input */
            
            /* Process the command */
            process_command(command_line);
            
            /* Show prompt for next command */
            uart_printf_custom("\r\nReady> ");
        }
        
        /* Small delay to yield to other tasks */
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void monitor_task(void *pvParameters) {
    (void)pvParameters;
    
    TickType_t last_status_time = 0;
    const TickType_t status_interval = pdMS_TO_TICKS(10000); /* 10 seconds */
    
    while (1) {
        /* Monitor VM status */
        if (g_app.vm && g_app.vm_running) {
            /* Check if VM is still running */
            if (!g_app.vm->running) {
                uart_printf_custom("\r\n[MONITOR] VM execution completed\r\n");
                g_app.vm_running = false;
                g_app.state = APP_STATE_IDLE;
            }
        }
        
        /* Periodic status update (every 10 seconds) */
        TickType_t current_time = xTaskGetTickCount();
        if ((current_time - last_status_time) >= status_interval) {
            if (g_app.state == APP_STATE_RUNNING) {
                uart_printf_custom("\r\n[MONITOR] VM running, Free heap: %u bytes\r\n", 
                    xPortGetFreeHeapSize());
                uart_printf_custom("Ready> ");
            }
            last_status_time = current_time;
        }
        
        /* Sleep for 1 second */
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

/* ========================================================================== */
/* Main Function                                                             */
/* ========================================================================== */

int main() {
    /* Initialize stdio and hardware */
    stdio_init_all();
    
    /* Initialize custom UART */
    uart_init_custom();
    
    /* Small delay to let UART settle */
    sleep_ms(100);
    
    /* Show welcome message */
    show_welcome_message();
    
    /* Initialize application */
    app_init();
    
    /* Create FreeRTOS tasks */
    BaseType_t result;
    
    /* Command processing task */
    result = xTaskCreate(
        command_task,
        "CommandTask",
        2048,  /* Stack size */
        NULL,
        2,     /* Priority */
        NULL
    );
    
    if (result != pdPASS) {
        uart_printf_custom("ERROR: Failed to create command task\r\n");
        return -1;
    }
    
    /* VM monitoring task */
    result = xTaskCreate(
        monitor_task,
        "MonitorTask", 
        1024,  /* Stack size */
        NULL,
        1,     /* Priority (lower than command task) */
        NULL
    );
    
    if (result != pdPASS) {
        uart_printf_custom("ERROR: Failed to create monitor task\r\n");
        return -1;
    }
    
    uart_printf_custom("Starting FreeRTOS scheduler...\r\n");
    
    /* Start the FreeRTOS scheduler */
    vTaskStartScheduler();
    
    /* Should never reach here */
    while (1) {
        tight_loop_contents();
    }
    
    return 0;
}