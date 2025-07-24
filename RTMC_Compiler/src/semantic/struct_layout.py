"""
Struct Layout Management for RT-Micro-C Language
Handles struct size calculation and field offset resolution.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from RTMC_Compiler.src.parser.ast_nodes import *

@dataclass
class FieldLayout:
    """Layout information for a struct field"""
    name: str
    offset: int           # Byte offset from struct base
    size: int             # Size in bytes
    bit_offset: int = 0   # Bit offset within byte (for bit-fields)
    bit_width: int = 0    # Bit width (0 = not a bit-field)
    is_base_struct: bool = False  # True if this field is used for inheritance

@dataclass
class StructLayout:
    """Complete layout information for a struct"""
    name: str
    total_size: int
    alignment: int
    fields: Dict[str, FieldLayout]
    base_struct: Optional[str] = None  # Name of base struct if inherited

class StructLayoutTable:
    """Manages struct layouts and field offset calculations"""
    
    def __init__(self):
        self.layouts: Dict[str, StructLayout] = {}
        self.struct_decls: Dict[str, StructDeclNode] = {}
    
    def register_struct(self, struct_decl):
        """Register a struct or union declaration for layout calculation"""
        self.struct_decls[struct_decl.name] = struct_decl
    
    def calculate_layout(self, struct_name: str) -> StructLayout:
        """Calculate and cache the layout for a struct or union"""
        if struct_name in self.layouts:
            return self.layouts[struct_name]
        
        if struct_name not in self.struct_decls:
            raise ValueError(f"Unknown struct/union: {struct_name}")
        
        struct_decl = self.struct_decls[struct_name]
        
        # Check if it's a union
        if isinstance(struct_decl, UnionDeclNode):
            layout = self._calculate_union_layout(struct_decl)
        else:
            layout = self._calculate_struct_layout(struct_decl)
            
        self.layouts[struct_name] = layout
        return layout
    
    def _calculate_struct_layout(self, struct_decl: StructDeclNode) -> StructLayout:
        """Calculate the layout for a struct declaration"""
        fields = {}
        current_offset = 0
        current_bit_offset = 0
        max_alignment = 1
        base_struct = None
        
        # Group fields by union_group
        union_groups = {}
        regular_fields = []
        
        for field in struct_decl.fields:
            if field.union_group:
                if field.union_group not in union_groups:
                    union_groups[field.union_group] = []
                union_groups[field.union_group].append(field)
            else:
                regular_fields.append(field)
        
        # Process union groups first
        for union_group_id, union_fields in union_groups.items():
            # Align for union start
            if current_bit_offset > 0:
                current_offset += 1
                current_bit_offset = 0
            
            # Find alignment requirement for this union
            union_alignment = 1
            for field in union_fields:
                field_alignment = self._get_field_alignment(field.type)
                union_alignment = max(union_alignment, field_alignment)
            
            # Align current offset for union
            if current_offset % union_alignment != 0:
                current_offset += union_alignment - (current_offset % union_alignment)
            
            union_base_offset = current_offset
            union_size = 0
            union_bit_offset = 0
            
            # Calculate layout for each field in the union
            for field in union_fields:
                if field.bit_width and field.bit_width > 0:
                    # Bitfield - they are sequential within the union
                    field_layout = FieldLayout(
                        name=field.name,
                        offset=union_base_offset,
                        size=0,
                        bit_offset=union_bit_offset,
                        bit_width=field.bit_width
                    )
                    union_bit_offset += field.bit_width
                    # Update union size to include this bitfield
                    union_size = max(union_size, (union_bit_offset + 7) // 8)
                else:
                    # Regular field - starts at union base, resets bit offset
                    field_size = self._get_field_size(field.type)
                    field_layout = FieldLayout(
                        name=field.name,
                        offset=union_base_offset,
                        size=field_size,
                        bit_offset=0,
                        bit_width=0
                    )
                    union_size = max(union_size, field_size)
                    # Reset bit offset for regular fields
                    union_bit_offset = 0
                
                fields[field.name] = field_layout
            
            # Advance offset by union size
            current_offset += union_size
            max_alignment = max(max_alignment, union_alignment)
        
        # Process regular fields
        for i, field in enumerate(regular_fields):
            field_layout = self._calculate_field_layout(field, current_offset, current_bit_offset)
            fields[field.name] = field_layout
            
            # Update offset for next field
            if field.bit_width and field.bit_width > 0:
                # Bit-field
                current_bit_offset += field.bit_width
                if current_bit_offset >= 8:
                    current_offset += current_bit_offset // 8
                    current_bit_offset = current_bit_offset % 8
            else:
                # Regular field
                if current_bit_offset > 0:
                    current_offset += 1  # Complete current byte
                    current_bit_offset = 0
                
                field_size = field_layout.size
                field_alignment = self._get_field_alignment(field.type)
                
                # Align current offset
                if current_offset % field_alignment != 0:
                    current_offset += field_alignment - (current_offset % field_alignment)
                
                field_layout.offset = current_offset
                current_offset += field_size
                max_alignment = max(max_alignment, field_alignment)
        
        # Final padding to align struct size
        if current_bit_offset > 0:
            current_offset += 1
        
        if current_offset % max_alignment != 0:
            current_offset += max_alignment - (current_offset % max_alignment)
        
        layout = StructLayout(
            name=struct_decl.name,
            total_size=current_offset,
            alignment=max_alignment,
            fields=fields,
            base_struct=base_struct
        )
        
        # Update the struct declaration with computed values
        struct_decl.total_size = current_offset
        struct_decl.field_offsets = {name: field.offset for name, field in fields.items()}
        struct_decl.base_struct = base_struct
        
        return layout
    
    def _calculate_field_layout(self, field: FieldNode, current_offset: int, current_bit_offset: int) -> FieldLayout:
        """Calculate layout for a single field"""
        field_size = self._get_field_size(field.type)
        
        if field.bit_width and field.bit_width > 0:
            # Bit-field
            return FieldLayout(
                name=field.name,
                offset=current_offset,
                size=0,  # Bit-fields don't contribute to size directly
                bit_offset=current_bit_offset,
                bit_width=field.bit_width
            )
        else:
            # Regular field
            return FieldLayout(
                name=field.name,
                offset=current_offset,
                size=field_size,
                bit_offset=0,
                bit_width=0
            )
    
    def _get_field_size(self, type_node: TypeNode) -> int:
        """Get the size of a field type"""
        if isinstance(type_node, PrimitiveTypeNode):
            return self._get_primitive_size(type_node.type_name)
        elif isinstance(type_node, StructTypeNode):
            # Recursively calculate struct size
            nested_layout = self.calculate_layout(type_node.struct_name)
            return nested_layout.total_size
        elif isinstance(type_node, UnionTypeNode):
            # Recursively calculate union size
            nested_layout = self.calculate_layout(type_node.union_name)
            return nested_layout.total_size
        elif isinstance(type_node, ArrayTypeNode):
            element_size = self._get_field_size(type_node.element_type)
            return element_size * (type_node.size or 1)
        elif isinstance(type_node, PointerTypeNode):
            return 8  # Pointer size (64-bit)
        else:
            return 4  # Default size
    
    def _get_field_alignment(self, type_node: TypeNode) -> int:
        """Get the alignment requirement for a field type"""
        if isinstance(type_node, PrimitiveTypeNode):
            if type_node.type_name == 'char':
                return 1
            elif type_node.type_name in ['int', 'float']:
                return 4
            else:
                return 1
        elif isinstance(type_node, StructTypeNode):
            nested_layout = self.calculate_layout(type_node.struct_name)
            return nested_layout.alignment
        elif isinstance(type_node, PointerTypeNode):
            return 8  # Pointer alignment
        else:
            return 4  # Default alignment
    
    def _get_primitive_size(self, type_name: str) -> int:
        """Get size of primitive types"""
        sizes = {
            'char': 1,
            'int': 4,
            'float': 4,
            'void': 0,
            'bool': 1
        }
        return sizes.get(type_name, 4)
    
    def get_field_offset(self, struct_name: str, field_path: str) -> int:
        """Get field offset, supporting nested field access (e.g., 'outer.inner.field')"""
        parts = field_path.split('.')
        current_struct = struct_name
        total_offset = 0
        
        for part in parts:
            layout = self.calculate_layout(current_struct)
            
            if part not in layout.fields:
                raise ValueError(f"Field '{part}' not found in struct '{current_struct}'")
            
            field_layout = layout.fields[part]
            total_offset += field_layout.offset
            
            # If this field is a struct, continue with nested access
            if isinstance(self.struct_decls[current_struct].fields[0].type, StructTypeNode):
                for field in self.struct_decls[current_struct].fields:
                    if field.name == part and isinstance(field.type, StructTypeNode):
                        current_struct = field.type.struct_name
                        break
        
        return total_offset
    
    def get_bit_field_info(self, struct_name: str, field_path: str) -> Optional[Tuple[int, int, int]]:
        """Get bit-field information (byte_offset, bit_offset, bit_width)"""
        parts = field_path.split('.')
        current_struct = struct_name
        total_offset = 0
        
        for part in parts:
            layout = self.calculate_layout(current_struct)
            
            if part not in layout.fields:
                return None
            
            field_layout = layout.fields[part]
            
            if field_layout.bit_width > 0:
                # This is a bit-field
                return (total_offset + field_layout.offset, field_layout.bit_offset, field_layout.bit_width)
            
            total_offset += field_layout.offset
            
            # Continue with nested struct if applicable
            for field in self.struct_decls[current_struct].fields:
                if field.name == part and isinstance(field.type, StructTypeNode):
                    current_struct = field.type.struct_name
                    break
        
        return None
    
    def get_struct_size(self, struct_name: str) -> int:
        """Get total size of a struct"""
        layout = self.calculate_layout(struct_name)
        return layout.total_size
    
    def get_base_struct(self, struct_name: str) -> Optional[str]:
        """Get the base struct name if this struct inherits from another"""
        layout = self.calculate_layout(struct_name)
        return layout.base_struct
    
    def is_substruct(self, child_struct: str, base_struct: str) -> bool:
        """Check if child_struct inherits from base_struct"""
        current = child_struct
        while current:
            layout = self.calculate_layout(current)
            if layout.base_struct == base_struct:
                return True
            current = layout.base_struct
        return False
    
    def get_field_type(self, struct_name: str, field_name: str) -> Optional[str]:
        """Get the type name of a field in a struct"""
        if struct_name not in self.struct_decls:
            return None
        
        struct_decl = self.struct_decls[struct_name]
        
        # Find the field in the struct declaration
        for field in struct_decl.fields:
            if field.name == field_name:
                return self._get_type_name_from_node(field.type)
        
        # Check base struct if present
        layout = self.calculate_layout(struct_name)
        if layout.base_struct:
            return self.get_field_type(layout.base_struct, field_name)
        
        return None
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """Get the type of a variable (placeholder - would be enhanced with symbol table)"""
        # This is a placeholder method that would typically be enhanced
        # to work with a symbol table or semantic analyzer
        # For now, it returns None to indicate the information is not available
        return None
    
    def _get_type_name_from_node(self, type_node: TypeNode) -> str:
        """Extract type name from a type node"""
        if isinstance(type_node, PrimitiveTypeNode):
            return type_node.type_name
        elif isinstance(type_node, StructTypeNode):
            return type_node.struct_name
        elif isinstance(type_node, ArrayTypeNode):
            element_name = self._get_type_name_from_node(type_node.element_type)
            return f"{element_name}[{type_node.size}]"
        elif isinstance(type_node, PointerTypeNode):
            pointed_type = self._get_type_name_from_node(type_node.pointed_type)
            return f"{pointed_type}*"
        else:
            return "unknown"
    
    def _calculate_union_layout(self, union_decl: UnionDeclNode) -> StructLayout:
        """Calculate layout for a union - all fields start at offset 0"""
        fields = {}
        max_size = 0
        max_alignment = 1
        
        for field in union_decl.fields:
            field_layout = FieldLayout(
                name=field.name,
                offset=0,  # All union fields start at offset 0
                size=self._get_field_size(field.type),
                bit_offset=0,
                bit_width=field.bit_width or 0
            )
            
            fields[field.name] = field_layout
            max_size = max(max_size, field_layout.size)
            field_alignment = self._get_field_alignment(field.type)
            max_alignment = max(max_alignment, field_alignment)
        
        # Union size is the maximum of all field sizes
        total_size = max_size
        if total_size % max_alignment != 0:
            total_size += max_alignment - (total_size % max_alignment)
        
        layout = StructLayout(
            name=union_decl.name,
            total_size=total_size,
            alignment=max_alignment,
            fields=fields
        )
        
        # Update the union declaration with computed values
        union_decl.total_size = total_size
        union_decl.field_offsets = {name: field.offset for name, field in fields.items()}
        
        return layout
