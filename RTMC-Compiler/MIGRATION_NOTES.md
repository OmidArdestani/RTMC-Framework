# RT-Micro-C PLY Migration Notes

## Migration Summary

The RT-Micro-C compiler has been successfully migrated from a manual recursive descent parser to use PLY (Python Lex-Yacc). This provides better maintainability, error handling, and extensibility.

## Changes Made

### New Files
- `src/lexer/ply_lexer.py` - PLY-based lexer
- `src/parser/ply_parser.py` - PLY-based parser with complete grammar
- `main_ply.py` - Entry point using pure PLY parser

### Removed Files
- `src/lexer/tokenizer.py` - Old manual tokenizer (replaced by PLY lexer)
- `src/parser/parser.py` - Old recursive descent parser (replaced by PLY parser)
- `src/parser/ply_adapter.py` - Backward compatibility adapter (no longer needed)
- `test_*.py` - Temporary test files created during migration

### Updated Files
- `main.py` - Now uses PLY parser directly
- `requirements.txt` - Added PLY dependency

## Usage

### Primary Entry Point (PLY)
```bash
python main_ply.py input.rtmc -o output.vmb
```

### Legacy Entry Point (also uses PLY)
```bash
python main.py input.rtmc -o output.vmb
```

## Test Files Status

The test files in the `tests/` directory currently use the old parser API. To update them:

1. Replace imports:
   ```python
   # Old
   from src.lexer.tokenizer import Tokenizer
   from src.parser.parser import Parser
   
   # New
   from src.parser.ply_parser import RTMCParser
   ```

2. Replace parsing code:
   ```python
   # Old
   tokenizer = Tokenizer(source_code)
   tokens = tokenizer.tokenize()
   parser = Parser(tokens)
   ast = parser.parse()
   
   # New
   parser = RTMCParser()
   ast = parser.parse(source_code)
   ```

## Benefits of PLY Migration

1. **Reduced Codebase**: ~800 lines of parsing code removed
2. **Better Error Handling**: Automatic error recovery and reporting
3. **Maintainable Grammar**: Declarative grammar rules
4. **Standard Technology**: Industry-standard parser library
5. **Operator Precedence**: Automatic precedence handling
6. **Extensibility**: Easier to add new language features

## Features Supported

All RT-Micro-C language features are fully supported:
- Function declarations
- Struct and union declarations
- Task declarations
- Variable declarations with initialization
- Pointer types and operations (`int*`, `&variable`, `*pointer`)
- Type casting (`(int*)pointer`)
- All operators (arithmetic, logical, bitwise, assignment)
- Control flow statements
- RTOS function calls
- Hardware function calls
- Debug function calls
- Member access (`.` and `->`)

## Next Steps

1. Update test files to use new PLY parser API
2. Consider removing old test files that are no longer relevant
3. Update documentation to reflect PLY usage
4. Add PLY-specific error handling examples
