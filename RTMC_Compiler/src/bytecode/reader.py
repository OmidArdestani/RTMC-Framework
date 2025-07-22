"""
Bytecode Reader for RT-Micro-C Language
Reads bytecode programs from .vmb files.
"""

from .writer import BytecodeReader

# Re-export for convenience
__all__ = ['BytecodeReader']
