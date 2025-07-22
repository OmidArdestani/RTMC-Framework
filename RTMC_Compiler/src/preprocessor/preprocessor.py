"""
RT-Micro-C Preprocessor
Handles #define directives similar to the C preprocessor.
"""

import re
from typing import Dict, List, Tuple

class RTMCPreprocessor:
    """RT-Micro-C preprocessor for handling #define directives"""
    
    def __init__(self):
        self.defines: Dict[str, str] = {}
    
    def process(self, source_code: str) -> str:
        """Process source code and expand #define macros"""
        lines = source_code.split('\n')
        processed_lines = []
        
        for line_num, line in enumerate(lines, 1):
            processed_line = self._process_line(line, line_num)
            if processed_line is not None:  # None means line was a #define directive
                processed_lines.append(processed_line)
        
        return '\n'.join(processed_lines)
    
    def _process_line(self, line: str, line_num: int) -> str:
        """Process a single line"""
        stripped = line.strip()
        
        # Handle #define directive
        if stripped.startswith('#define'):
            self._parse_define(stripped, line_num)
            return None  # Remove #define lines from output
        
        # Expand macros in the line
        return self._expand_macros(line)
    
    def _parse_define(self, line: str, line_num: int):
        """Parse a #define directive"""
        # Remove #define and split into parts
        parts = line[7:].strip().split(None, 1)  # Skip '#define'
        
        if len(parts) < 1:
            raise ValueError(f"Line {line_num}: Invalid #define directive")
        
        macro_name = parts[0]
        
        # If no value is provided, default to empty string (like C)
        macro_value = parts[1] if len(parts) > 1 else ""
        
        # Store the macro
        self.defines[macro_name] = macro_value
        print(f"Preprocessor: Defined {macro_name} = '{macro_value}'")
    
    def _expand_macros(self, line: str) -> str:
        """Expand macros in a line"""
        result = line
        
        # Sort by length (descending) to handle longer names first
        # This prevents issues like MAX being replaced in MAXSIZE
        sorted_defines = sorted(self.defines.keys(), key=len, reverse=True)
        
        for macro_name in sorted_defines:
            macro_value = self.defines[macro_name]
            
            # Use word boundaries to ensure we only replace whole identifiers
            pattern = r'\b' + re.escape(macro_name) + r'\b'
            result = re.sub(pattern, macro_value, result)
        
        return result
    
    def get_defines(self) -> Dict[str, str]:
        """Get all current macro definitions"""
        return self.defines.copy()
    
    def clear_defines(self):
        """Clear all macro definitions"""
        self.defines.clear()

# Global preprocessor instance
preprocessor = RTMCPreprocessor()
