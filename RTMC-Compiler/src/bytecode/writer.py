"""
Bytecode Writer for RT-Micro-C Language
Writes bytecode programs to .vmb files.
"""

import struct
from typing import Dict, List, Any, BinaryIO
from .generator import BytecodeProgram
from .instructions import Instruction, Opcode

class BytecodeWriter:
    """Writes bytecode programs to binary files"""
    
    # Magic header for .vmb files
    MAGIC_HEADER = b'MINICRTOS'
    VERSION = 1
    
    def __init__(self):
        pass
    
    def write(self, program: BytecodeProgram, filename: str):
        """Write bytecode program to file"""
        with open(filename, 'wb') as f:
            self._write_header(f)
            self._write_constant_pool(f, program.constants)
            self._write_string_pool(f, program.strings)
            self._write_symbol_table(f, program.symbol_table)
            self._write_function_table(f, program.functions)
            self._write_struct_layouts(f, program.struct_layouts)
            self._write_bytecode(f, program.instructions)
    
    def _write_header(self, f: BinaryIO):
        """Write file header"""
        f.write(self.MAGIC_HEADER)
        f.write(struct.pack('<I', self.VERSION))
    
    def _write_constant_pool(self, f: BinaryIO, constants: List[Any]):
        """Write constant pool"""
        f.write(struct.pack('<I', len(constants)))
        
        for const in constants:
            if isinstance(const, int):
                f.write(struct.pack('<BI', 0, const))  # Type 0 = int (unsigned)
            elif isinstance(const, float):
                f.write(struct.pack('<Bf', 1, const))  # Type 1 = float
            elif isinstance(const, str):
                encoded = const.encode('utf-8')
                f.write(struct.pack('<BH', 2, len(encoded)))  # Type 2 = string
                f.write(encoded)
            else:
                # Default to int
                f.write(struct.pack('<BI', 0, 0))
    
    def _write_string_pool(self, f: BinaryIO, strings: List[str]):
        """Write string pool"""
        f.write(struct.pack('<I', len(strings)))
        
        for string in strings:
            encoded = string.encode('utf-8')
            f.write(struct.pack('<H', len(encoded)))
            f.write(encoded)
    
    def _write_symbol_table(self, f: BinaryIO, symbol_table: Dict[str, int]):
        """Write symbol table"""
        f.write(struct.pack('<I', len(symbol_table)))
        
        for name, address in symbol_table.items():
            encoded_name = name.encode('utf-8')
            f.write(struct.pack('<H', len(encoded_name)))
            f.write(encoded_name)
            f.write(struct.pack('<I', address))
    
    def _write_function_table(self, f: BinaryIO, functions: Dict[str, int]):
        """Write function table"""
        f.write(struct.pack('<I', len(functions)))
        
        for name, address in functions.items():
            encoded_name = name.encode('utf-8')
            f.write(struct.pack('<H', len(encoded_name)))
            f.write(encoded_name)
            f.write(struct.pack('<I', address))
    
    def _write_struct_layouts(self, f: BinaryIO, struct_layouts: Dict[str, Dict[str, int]]):
        """Write struct layout table"""
        f.write(struct.pack('<I', len(struct_layouts)))
        
        for struct_name, fields in struct_layouts.items():
            encoded_name = struct_name.encode('utf-8')
            f.write(struct.pack('<H', len(encoded_name)))
            f.write(encoded_name)
            
            f.write(struct.pack('<I', len(fields)))
            for field_name, offset in fields.items():
                encoded_field = field_name.encode('utf-8')
                f.write(struct.pack('<H', len(encoded_field)))
                f.write(encoded_field)
                f.write(struct.pack('<I', offset))
    
    def _write_bytecode(self, f: BinaryIO, instructions: List[Instruction]):
        """Write bytecode instructions"""
        f.write(struct.pack('<I', len(instructions)))
        
        for instruction in instructions:
            # Write opcode
            f.write(struct.pack('<B', instruction.opcode.value))
            
            # Write operand count
            f.write(struct.pack('<B', len(instruction.operands)))
            
            # Write operands
            for operand in instruction.operands:
                if isinstance(operand, int):
                    f.write(struct.pack('<I', operand))
                elif isinstance(operand, float):
                    f.write(struct.pack('<f', operand))
                elif isinstance(operand, str):
                    # String operands should be converted to indices
                    f.write(struct.pack('<I', 0))  # Placeholder
                else:
                    f.write(struct.pack('<I', 0))  # Default to 0

class BytecodeDisassembler:
    """Disassembles bytecode for debugging"""
    
    def __init__(self):
        pass
    
    def disassemble(self, program: BytecodeProgram) -> str:
        """Disassemble bytecode program to text"""
        output = []
        
        output.append("=== CONSTANTS ===")
        for i, const in enumerate(program.constants):
            output.append(f"{i:4d}: {const}")
        
        output.append("\n=== STRINGS ===")
        for i, string in enumerate(program.strings):
            output.append(f"{i:4d}: \"{string}\"")
        
        output.append("\n=== FUNCTIONS ===")
        for name, address in program.functions.items():
            output.append(f"{name}: {address}")
        
        output.append("\n=== SYMBOLS ===")
        for name, address in program.symbol_table.items():
            output.append(f"{name}: {address}")
        
        output.append("\n=== STRUCTS ===")
        for struct_name, fields in program.struct_layouts.items():
            output.append(f"{struct_name}:")
            for field_name, offset in fields.items():
                output.append(f"  {field_name}: {offset}")
        
        output.append("\n=== BYTECODE ===")
        for i, instruction in enumerate(program.instructions):
            output.append(f"{i:4d}: {instruction}")
        
        return "\n".join(output)
    
    def disassemble_file(self, filename: str) -> str:
        """Disassemble bytecode file"""
        reader = BytecodeReader()
        program = reader.read(filename)
        return self.disassemble(program)

class BytecodeReader:
    """Reads bytecode from .vmb files"""
    
    def __init__(self):
        pass
    
    def read(self, filename: str) -> BytecodeProgram:
        """Read bytecode program from file"""
        with open(filename, 'rb') as f:
            self._read_header(f)
            constants = self._read_constant_pool(f)
            strings = self._read_string_pool(f)
            symbol_table = self._read_symbol_table(f)
            functions = self._read_function_table(f)
            struct_layouts = self._read_struct_layouts(f)
            instructions = self._read_bytecode(f)
            
            return BytecodeProgram(
                constants=constants,
                strings=strings,
                functions=functions,
                instructions=instructions,
                symbol_table=symbol_table,
                struct_layouts=struct_layouts
            )
    
    def _read_header(self, f: BinaryIO):
        """Read and validate file header"""
        magic = f.read(len(BytecodeWriter.MAGIC_HEADER))
        if magic != BytecodeWriter.MAGIC_HEADER:
            raise ValueError("Invalid bytecode file: bad magic header")
        
        version = struct.unpack('<I', f.read(4))[0]
        if version != BytecodeWriter.VERSION:
            raise ValueError(f"Unsupported bytecode version: {version}")
    
    def _read_constant_pool(self, f: BinaryIO) -> List[Any]:
        """Read constant pool"""
        count = struct.unpack('<I', f.read(4))[0]
        constants = []
        
        for _ in range(count):
            const_type = struct.unpack('<B', f.read(1))[0]
            
            if const_type == 0:  # int
                value = struct.unpack('<I', f.read(4))[0]
                constants.append(value)
            elif const_type == 1:  # float
                value = struct.unpack('<f', f.read(4))[0]
                constants.append(value)
            elif const_type == 2:  # string
                length = struct.unpack('<H', f.read(2))[0]
                value = f.read(length).decode('utf-8')
                constants.append(value)
            else:
                constants.append(0)  # Default
        
        return constants
    
    def _read_string_pool(self, f: BinaryIO) -> List[str]:
        """Read string pool"""
        count = struct.unpack('<I', f.read(4))[0]
        strings = []
        
        for _ in range(count):
            length = struct.unpack('<H', f.read(2))[0]
            string = f.read(length).decode('utf-8')
            strings.append(string)
        
        return strings
    
    def _read_symbol_table(self, f: BinaryIO) -> Dict[str, int]:
        """Read symbol table"""
        count = struct.unpack('<I', f.read(4))[0]
        symbol_table = {}
        
        for _ in range(count):
            name_length = struct.unpack('<H', f.read(2))[0]
            name = f.read(name_length).decode('utf-8')
            address = struct.unpack('<I', f.read(4))[0]
            symbol_table[name] = address
        
        return symbol_table
    
    def _read_function_table(self, f: BinaryIO) -> Dict[str, int]:
        """Read function table"""
        count = struct.unpack('<I', f.read(4))[0]
        functions = {}
        
        for _ in range(count):
            name_length = struct.unpack('<H', f.read(2))[0]
            name = f.read(name_length).decode('utf-8')
            address = struct.unpack('<I', f.read(4))[0]
            functions[name] = address
        
        return functions
    
    def _read_struct_layouts(self, f: BinaryIO) -> Dict[str, Dict[str, int]]:
        """Read struct layout table"""
        count = struct.unpack('<I', f.read(4))[0]
        struct_layouts = {}
        
        for _ in range(count):
            name_length = struct.unpack('<H', f.read(2))[0]
            name = f.read(name_length).decode('utf-8')
            
            field_count = struct.unpack('<I', f.read(4))[0]
            fields = {}
            
            for _ in range(field_count):
                field_name_length = struct.unpack('<H', f.read(2))[0]
                field_name = f.read(field_name_length).decode('utf-8')
                offset = struct.unpack('<I', f.read(4))[0]
                fields[field_name] = offset
            
            struct_layouts[name] = fields
        
        return struct_layouts
    
    def _read_bytecode(self, f: BinaryIO) -> List[Instruction]:
        """Read bytecode instructions"""
        count = struct.unpack('<I', f.read(4))[0]
        instructions = []
        
        for _ in range(count):
            opcode_value = struct.unpack('<B', f.read(1))[0]
            opcode = Opcode(opcode_value)
            
            operand_count = struct.unpack('<B', f.read(1))[0]
            operands = []
            
            for _ in range(operand_count):
                operand = struct.unpack('<I', f.read(4))[0]
                operands.append(operand)
            
            instructions.append(Instruction(opcode, operands))
        
        return instructions
