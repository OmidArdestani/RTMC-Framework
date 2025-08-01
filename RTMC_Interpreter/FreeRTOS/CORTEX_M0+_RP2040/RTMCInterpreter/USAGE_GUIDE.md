# RTMC Interpreter UART Control Guide

This guide explains how to use the UART-based control system for the RTMC interpreter running on Raspberry Pi Pico.

## Overview

The RTMC interpreter now supports loading and executing bytecode programs through UART commands. This allows for dynamic program loading and execution control without needing to reflash the firmware.

## Hardware Setup

1. **UART Connection:**
   - Connect Pico GPIO 0 (UART0 TX) to your PC's RX
   - Connect Pico GPIO 1 (UART0 RX) to your PC's TX  
   - Connect GND between Pico and PC
   - UART settings: 115200 baud, 8N1, no flow control

2. **Optional LED:**
   - Connect LED with resistor to GPIO 25 for visual feedback

## UART Commands

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `HELP` | Show available commands | `HELP` |
| `STATUS` | Show current VM status | `STATUS` |
| `RESET` | Reset VM and clear program | `RESET` |

### Program Control

| Command | Description | Example |
|---------|-------------|---------|
| `LOAD <size>` | Load bytecode program | `LOAD 1024` |
| `RUN` | Start executing loaded program | `RUN` |
| `STOP` | Stop currently running program | `STOP` |

## Usage Examples

### Using Serial Terminal

1. **Connect via Serial Terminal:**
   ```bash
   # Linux/Mac
   screen /dev/ttyUSB0 115200
   
   # Windows (PuTTY)
   putty -serial COM3 -serspeed 115200
   ```

2. **Load and Run Program:**
   ```
   Ready> HELP
   === RTMC Interpreter Commands ===
   LOAD <size>  - Load bytecode program of <size> bytes
   RUN          - Start executing the loaded program
   STOP         - Stop the currently running program
   STATUS       - Show current VM status and information
   RESET        - Reset VM and clear loaded program
   HELP         - Show this help message
   
   Ready> LOAD 1024
   Loading 1024 bytes of bytecode...
   Send binary data now (timeout: 30 seconds)
   [Send your .vmb file here]
   Received 1024 bytes. Parsing bytecode...
   Bytecode loaded successfully!
     Instructions: 256
     Constants: 10
     Strings: 5
     Functions: 3
     Symbols: 15
   
   Ready> RUN
   Starting RTMC Virtual Machine...
   VM started successfully. Program is now running.
   
   Ready> STATUS
   === RTMC Interpreter Status ===
   State: RUNNING
   Program loaded: YES
   VM running: YES
   Program details:
     Instructions: 256
     Functions: 3
     Constants: 10
     Strings: 5
   VM details:
     Tasks: 2
     Semaphores: 1
     Message queues: 0
   System info:
     Free heap: 98304 bytes
     FreeRTOS tasks: 4
   ================================
   
   Ready> STOP
   Stopping VM...
   VM stopped.
   ```

### Using Python Utility

The included `rtmc_sender.py` script provides an easier way to interact with the interpreter:

1. **Interactive Mode:**
   ```bash
   python rtmc_sender.py COM3 interactive
   ```
   
   ```
   Connected to COM3 at 115200 baud
   Entering interactive mode. Type 'quit' to exit.
   Available commands: LOAD, RUN, STOP, STATUS, RESET, HELP
   
   RTMC> load blink.vmb
   Loading blink.vmb (1024 bytes)
   LOAD response: Loading 1024 bytes of bytecode...
   Sending 1024 bytes...
   Progress: 100.0% (1024/1024 bytes)
   Waiting for confirmation...
   Load response: Bytecode loaded successfully!
   
   RTMC> run
   Starting RTMC Virtual Machine...
   VM started successfully. Program is now running.
   
   RTMC> status
   === RTMC Interpreter Status ===
   State: RUNNING
   Program loaded: YES
   VM running: YES
   
   RTMC> quit
   Exiting interactive mode...
   Disconnected
   ```

2. **Single Commands:**
   ```bash
   # Load a program
   python rtmc_sender.py COM3 load blink.vmb
   
   # Run the program
   python rtmc_sender.py COM3 run
   
   # Check status
   python rtmc_sender.py COM3 status
   
   # Stop execution
   python rtmc_sender.py COM3 stop
   ```

## Program Development Workflow

1. **Write RT-Micro-C Program:**
   ```c
   // blink.rtmc
   task blink_task() {
       gpio_init(25, OUTPUT);
       while(1) {
           gpio_set(25, 1);
           delay_ms(500);
           gpio_set(25, 0);
           delay_ms(500);
       }
   }
   
   int main() {
       create_task(blink_task, 1024, 5, 0);
       return 0;
   }
   ```

2. **Compile to Bytecode:**
   ```bash
   cd "RTMC_Compiler"
   python main.py ../examples/blink.rtmc -o blink.vmb
   ```

3. **Upload and Execute:**
   ```bash
   python rtmc_sender.py COM3 load blink.vmb
   python rtmc_sender.py COM3 run
   ```

4. **Monitor Execution:**
   - Watch the LED blink on GPIO 25
   - Use `STATUS` command to check VM state
   - Use `STOP` command to halt execution

## Binary Format

The interpreter expects bytecode in the RTMC binary format:

```c
struct rtmc_binary_header {
    uint32_t magic;              // 'RTMC' (0x434D5452)
    uint32_t version;            // Format version (1)
    uint32_t instruction_count;  // Number of instructions
    uint32_t constant_count;     // Number of constants
    uint32_t string_count;       // Number of strings
    uint32_t function_count;     // Number of functions
    uint32_t symbol_count;       // Number of symbols
    uint32_t checksum;           // CRC32 checksum
};
```

Followed by:
- Instructions array
- Constants array  
- Strings (length-prefixed)
- Functions (name + address)
- Symbols (name + address)

## Error Handling

The interpreter provides detailed error messages:

| Error | Cause | Solution |
|-------|--------|----------|
| `Invalid size` | LOAD size too large/small | Use correct program size |
| `Checksum mismatch` | Corrupted data transmission | Retransmit the file |
| `Failed to parse bytecode` | Invalid binary format | Check compiler output |
| `No program loaded` | RUN without LOAD | Load program first |
| `Already running` | RUN while program active | STOP first, then RUN |

## Monitoring Features

1. **Real-time Status:**
   - VM state (IDLE, LOADING, RUNNING, ERROR)
   - Memory usage (free heap)
   - Task count and status
   - Program information

2. **Automatic Monitoring:**
   - VM completion detection
   - Periodic status updates every 10 seconds
   - Memory leak detection

3. **Debug Output:**
   - Instruction tracing (if enabled)
   - Hardware operation logging
   - Task creation/deletion events

## Performance Considerations

1. **UART Speed:**
   - 115200 baud = ~11.5 KB/s transfer rate
   - Large programs (>10KB) may take several seconds to load
   - Consider using higher baud rates for faster loading

2. **Memory Limits:**
   - Maximum program size: 64KB
   - Available heap: ~128KB (configurable)
   - Stack per task: configurable in program

3. **Real-time Performance:**
   - Command processing runs at low priority
   - VM execution maintains real-time characteristics
   - UART operations don't interrupt critical tasks

## Troubleshooting

### Connection Issues
- Check UART wiring (TX/RX crossed)
- Verify baud rate settings
- Ensure proper ground connection
- Check cable/USB adapter

### Loading Problems
- Verify file size matches LOAD command
- Check file is valid RTMC bytecode
- Ensure sufficient memory available
- Try smaller test programs first

### Execution Issues
- Check program for infinite loops
- Verify hardware pin assignments
- Monitor memory usage with STATUS
- Use RESET to clear stuck states

### Communication Problems
- Power cycle the Pico
- Close/reopen serial connection
- Check for other programs using the port
- Verify UART is properly initialized

## Advanced Features

### Custom Baud Rates
Modify `UART_BAUD_RATE` in the source code for different speeds:
```c
#define UART_BAUD_RATE  230400  // 2x faster loading
```

### Extended Timeouts
For very large programs, modify timeout values:
```c
size_t bytes_read = uart_read_bytes(g_app.bytecode_buffer, size, 60000); // 60 second timeout
```

### Debug Mode
Enable verbose debugging:
```c
g_app.vm = rtmc_vm_create(true, true); // debug=true, trace=true
```

This comprehensive UART control system allows for flexible development and deployment of RT-Micro-C programs on the Raspberry Pi Pico platform.
