#!/usr/bin/env python3
"""
RTMC Bytecode Sender Utility

This script sends compiled RTMC bytecode files to the Pico via UART
and provides a command-line interface for controlling the interpreter.

Usage:
    python rtmc_sender.py <port> [command] [file]

Examples:
    python rtmc_sender.py COM3 load program.vmb
    python rtmc_sender.py /dev/ttyUSB0 status
    python rtmc_sender.py COM3 interactive
"""

import serial
import sys
import os
import time
import argparse
from typing import Optional

class RTMCController:
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        
    def connect(self) -> bool:
        """Connect to the RTMC interpreter"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                write_timeout=1
            )
            time.sleep(0.1)  # Give it a moment to settle
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the device"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("Disconnected")
    
    def send_command(self, command: str) -> str:
        """Send a command and return the response"""
        if not self.serial or not self.serial.is_open:
            return "ERROR: Not connected"
        
        try:
            # Send command
            self.serial.write(f"{command}\r\n".encode())
            self.serial.flush()
            
            # Read response (with timeout)
            response_lines = []
            start_time = time.time()
            timeout = 5.0  # 5 second timeout
            
            while time.time() - start_time < timeout:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                        # Check for prompt (indicating command completed)
                        if 'Ready>' in line or 'ERROR:' in line:
                            break
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
            
            return '\n'.join(response_lines)
            
        except Exception as e:
            return f"ERROR: Communication failed: {e}"
    
    def load_program(self, filename: str) -> bool:
        """Load a bytecode program file"""
        if not os.path.exists(filename):
            print(f"ERROR: File {filename} not found")
            return False
        
        # Get file size
        file_size = os.path.getsize(filename)
        print(f"Loading {filename} ({file_size} bytes)")
        
        # Send LOAD command
        response = self.send_command(f"LOAD {file_size}")
        print("LOAD response:", response)
        
        if "ERROR:" in response:
            print("Failed to initiate load")
            return False
        
        # Wait a moment for the device to prepare
        time.sleep(0.5)
        
        # Send binary data
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                print(f"Sending {len(data)} bytes...")
                
                # Send data in chunks to avoid buffer overflow
                chunk_size = 256
                bytes_sent = 0
                
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    self.serial.write(chunk)
                    self.serial.flush()
                    bytes_sent += len(chunk)
                    
                    # Show progress
                    progress = (bytes_sent / len(data)) * 100
                    print(f"\rProgress: {progress:.1f}% ({bytes_sent}/{len(data)} bytes)", end='')
                    
                    # Small delay between chunks
                    time.sleep(0.01)
                
                print()  # New line after progress
                
                # Wait for confirmation
                print("Waiting for confirmation...")
                time.sleep(2)
                
                # Read any remaining response
                response_lines = []
                while self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                
                final_response = '\n'.join(response_lines)
                print("Load response:", final_response)
                
                return "successfully" in final_response.lower()
                
        except Exception as e:
            print(f"ERROR: Failed to send file: {e}")
            return False
    
    def interactive_mode(self):
        """Enter interactive command mode"""
        print("Entering interactive mode. Type 'quit' to exit.")
        print("Available commands: LOAD, RUN, STOP, STATUS, RESET, HELP")
        
        while True:
            try:
                command = input("\nRTMC> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                
                if command.lower().startswith('load '):
                    # Handle file loading
                    parts = command.split(' ', 1)
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        self.load_program(filename)
                    else:
                        print("Usage: load <filename>")
                else:
                    # Send regular command
                    if command:
                        response = self.send_command(command)
                        print(response)
                        
            except KeyboardInterrupt:
                print("\nExiting interactive mode...")
                break
            except EOFError:
                break

def main():
    parser = argparse.ArgumentParser(description='RTMC Bytecode Sender and Controller')
    parser.add_argument('port', help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('command', nargs='?', default='interactive', 
                       help='Command to execute (load, run, stop, status, reset, help, interactive)')
    parser.add_argument('file', nargs='?', help='Bytecode file to load (for load command)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200, 
                       help='Baud rate (default: 115200)')
    
    args = parser.parse_args()
    
    # Create controller
    controller = RTMCController(args.port, args.baudrate)
    
    # Connect to device
    if not controller.connect():
        return 1
    
    try:
        if args.command == 'interactive':
            controller.interactive_mode()
        elif args.command == 'load':
            if not args.file:
                print("ERROR: Load command requires a file argument")
                return 1
            success = controller.load_program(args.file)
            if success:
                print("Program loaded successfully. Use 'run' command to execute.")
            else:
                print("Failed to load program.")
                return 1
        else:
            # Send single command
            response = controller.send_command(args.command.upper())
            print(response)
    
    finally:
        controller.disconnect()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
