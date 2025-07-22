# RT-Micro-C Compiler - Comprehensive Unit Test Suite

## Overview

This directory contains a comprehensive unit test suite designed to validate all documented specifications and features of the RT-Micro-C compiler. The tests provide extensive coverage across all compiler components and language features.

## Test Structure

### Test Files

1. **`test_comprehensive_specifications.py`** - Main comprehensive test file covering all major features
2. **`test_lexer_comprehensive.py`** - Focused lexical analysis tests
3. **`test_parser_comprehensive.py`** - Comprehensive parser and AST generation tests
4. **`test_semantic_comprehensive.py`** - Semantic analysis and type checking tests
5. **`test_integration_comprehensive.py`** - Feature integration and end-to-end tests
6. **`run_comprehensive_tests.py`** - Test runner with detailed reporting
7. **`validate_tests.py`** - Test validation and setup verification

### Test Categories

#### 1. Lexical Analysis Tests (`TestLexicalAnalysis`, `TestTokenization`)
- **Data Types**: `int`, `float`, `char`, `bool`, `void`
- **Keywords**: Control flow, struct/union, constants
- **Operators**: Arithmetic, logical, bitwise, assignment
- **Literals**: Integer, float, string, char, boolean, hexadecimal
- **RTOS Functions**: Task management, timing, synchronization
- **Hardware Functions**: GPIO, ADC, UART, SPI, I2C, timers
- **Debug Functions**: `DBG_PRINT`, `DBG_PRINTF`, `DBG_BREAKPOINT`
- **Special Tokens**: Messages, imports, delimiters
- **Edge Cases**: Empty input, malformed literals, comments

#### 2. Parser Tests (Multiple Test Classes)
- **Basic Parsing**: Functions, variables, simple expressions
- **Expressions**: Arithmetic, logical, bitwise, assignments, function calls
- **Statements**: Control flow (`if`, `while`, `for`), returns, blocks
- **Structures**: Struct/union declarations, nested types, bitfields
- **Arrays**: Declarations, initialization, access, multidimensional
- **Messages**: Declaration, send/recv operations, timeouts
- **Imports**: Import statements, multiple imports
- **Flexible Braces**: Both `func() {` and `func()\n{` styles
- **Complex Expressions**: Nested calls, operator precedence

#### 3. Semantic Analysis Tests (Multiple Test Classes)
- **Type Checking**: Assignment compatibility, function parameters, returns
- **Scope Resolution**: Global, function, block, variable shadowing
- **Struct Semantics**: Member access, nested structs, assignment validation
- **Union Semantics**: Member access, size calculation, type punning
- **Message Semantics**: Type validation, timeout parameters
- **Constants**: Declaration, modification detection, expression evaluation
- **RTOS Validation**: Parameter checking, function recognition
- **Error Detection**: Undefined variables, type mismatches, redefinitions

#### 4. Bytecode Generation Tests (`TestBytecodeGeneration`)
- **Arithmetic Operations**: Basic math, complex expressions
- **Function Calls**: Parameter passing, return values
- **Control Flow**: Loops, conditionals, jumps
- **Array Operations**: Access, assignment, initialization
- **Struct Operations**: Member access, field assignment
- **Message Operations**: Send/recv bytecode generation
- **RTOS Functions**: Task management, delays, synchronization

#### 5. Virtual Machine Tests (`TestVirtualMachine`)
- **Basic Execution**: Simple programs, variable operations
- **RTOS Simulation**: Delays, task switching, synchronization
- **Hardware Simulation**: GPIO, ADC, communication interfaces
- **Message Passing**: Inter-task communication simulation

#### 6. Complex Feature Tests (`TestComplexFeatures`)
- **USB4 Sideband Example**: Complete real-world example from `sb_main.rtmc`
- **Nested Array/Struct Access**: Complex data structure manipulation
- **Union Memory Overlap**: Type punning and memory sharing
- **Message Timeouts**: Timeout parameter handling
- **Import System**: Multi-file compilation simulation

#### 7. Integration Tests (`TestCompleteFeatureIntegration`)
- **End-to-End Compilation**: Full pipeline testing
- **Feature Combinations**: Multiple features working together
- **Real-World Examples**: Complete embedded programs
- **Error Handling**: Comprehensive error detection
- **Performance Testing**: Large programs, deep nesting, complex expressions

## Language Features Tested

### Core Language Features
- ✅ **Data Types**: `int`, `float`, `char`, `bool`, `void`
- ✅ **Literals**: Decimal, hexadecimal (`0xFF`), boolean (`true`/`false`), strings, chars
- ✅ **Variables**: Declaration, initialization, scope management
- ✅ **Constants**: `const` declarations, compile-time evaluation
- ✅ **Arrays**: Fixed-length arrays, initialization, multi-dimensional access
- ✅ **Pointers**: Basic pointer operations, casting
- ✅ **Functions**: Declaration, parameters, return values, recursion

### Advanced Features
- ✅ **Structs**: Basic structs, nested structs, bitfields
- ✅ **Unions**: Memory overlap, type punning, anonymous unions
- ✅ **Messages**: Type-safe message queues, timeout support
- ✅ **Import System**: Multi-file compilation, dependency resolution
- ✅ **Flexible Syntax**: Multiple brace placement styles

### RTOS Features
- ✅ **Task Management**: `RTOS_CREATE_TASK`, `RTOS_DELETE_TASK`, etc.
- ✅ **Synchronization**: Semaphores, mutexes, task coordination
- ✅ **Timing**: `RTOS_DELAY_MS`, `RTOS_GET_TICK`, precise timing
- ✅ **Scheduling**: Task priorities, cooperative multitasking

### Hardware Abstraction
- ✅ **GPIO**: Pin configuration, digital I/O operations
- ✅ **ADC**: Analog input reading, multi-channel support
- ✅ **Timers**: PWM generation, frequency control
- ✅ **Communication**: UART, SPI, I2C interfaces
- ✅ **Debug**: Print statements, breakpoints, tracing

### Expression Support
- ✅ **Arithmetic**: `+`, `-`, `*`, `/`, `%`, with proper precedence
- ✅ **Logical**: `&&`, `||`, `!`, boolean evaluation
- ✅ **Bitwise**: `&`, `|`, `^`, `~`, `<<`, `>>`
- ✅ **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- ✅ **Assignment**: `=`, `+=`, `-=`, `*=`, `/=`
- ✅ **Increment/Decrement**: `++`, `--` (prefix and postfix)

### Control Flow
- ✅ **Conditionals**: `if`/`else`, nested conditions
- ✅ **Loops**: `while`, `for`, loop control (`break`, `continue`)
- ✅ **Functions**: `return` statements, parameter passing

## Running Tests

### Prerequisites
```bash
# Ensure you're in the RTMC-Compiler directory
cd "path/to/RTMC-Compiler"

# Validate test setup
python tests/validate_tests.py
```

### Run All Tests
```bash
# Run comprehensive test suite
python tests/run_comprehensive_tests.py
```

### Run Specific Test Categories
```bash
# Lexical analysis tests only
python tests/run_comprehensive_tests.py lexer

# Parser tests only
python tests/run_comprehensive_tests.py parser

# Semantic analysis tests only
python tests/run_comprehensive_tests.py semantic

# Integration tests only
python tests/run_comprehensive_tests.py integration

# Complex feature tests only
python tests/run_comprehensive_tests.py features
```

### Run Individual Test Files
```bash
# Run specific test file
python -m unittest tests.test_lexer_comprehensive -v

# Run specific test class
python -m unittest tests.test_parser_comprehensive.TestBasicParsing -v

# Run specific test method
python -m unittest tests.test_semantic_comprehensive.TestBasicSemantics.test_valid_program -v
```

## Test Output

The test runner provides detailed output including:

- **Test Results**: Pass/fail status for each test
- **Coverage Summary**: Features and areas tested
- **Error Details**: Specific failure information
- **Performance Metrics**: Execution time and statistics
- **Success Rate**: Overall test success percentage

Example output:
```
================================================================================
COMPREHENSIVE TEST RESULTS SUMMARY
================================================================================
Total Tests Run: 247
Passed: 235
Failed: 8
Errors: 4
Skipped: 0
Duration: 45.23 seconds
Success Rate: 95.1%

FEATURES TESTED:
✓ Basic data types (int, float, char, bool, void)
✓ Hexadecimal literals (0xFF, 0x1234, etc.)
✓ Boolean literals (true, false)
✓ Arrays (fixed-length, initialization, access)
✓ Structs (basic, nested, bitfields)
✓ Unions (memory overlap, type punning)
✓ Messages (declaration, send/recv, timeouts)
...
```

## Test Coverage Analysis

### Documentation Coverage
The tests comprehensively cover all features documented in:
- `IMPLEMENTATION_COMPLETE.md` - All completed features
- `ARRAY_AND_STRUCT_FEATURES.md` - Array and struct implementations
- `UNION_SUPPORT_DOCUMENTATION.md` - Union and field initialization
- `HEXADECIMAL_SUPPORT_DOCUMENTATION.md` - Hexadecimal literal support
- `ARCHITECTURE.md` - Overall system architecture

### Code Coverage
Tests validate functionality across all major components:
- **Lexer** (`src/lexer/`) - Token recognition and classification
- **Parser** (`src/parser/`) - AST generation and syntax validation
- **Semantic Analyzer** (`src/semantic/`) - Type checking and validation
- **Bytecode Generator** (`src/bytecode/`) - Code generation
- **Virtual Machine** (`src/vm/`) - Execution simulation
- **Optimizer** (`src/optimizer/`) - Code optimization (if implemented)

### Real-World Validation
Tests include real-world examples:
- **USB4 Sideband Protocol**: Complete implementation from `sb_main.rtmc`
- **Embedded Systems**: GPIO, ADC, UART communication patterns
- **RTOS Applications**: Multi-task programs with synchronization
- **Hardware Control**: Sensor reading, actuator control, communication

## Extending Tests

### Adding New Tests
1. Create test methods in appropriate test class
2. Follow naming convention: `test_feature_description`
3. Use descriptive docstrings
4. Include both positive and negative test cases

### Test Structure Template
```python
def test_new_feature(self):
    """Test description of what this validates"""
    # Arrange
    source = """
    // Test code here
    """
    
    # Act
    result = self._test_helper_method(source)
    
    # Assert
    self.assertEqual(expected, result)
    self.assertIsNotNone(result)
```

### Error Testing Template
```python
def test_error_detection(self):
    """Test that specific errors are detected"""
    invalid_source = """
    // Code that should produce errors
    """
    
    errors, ast = self._analyze_code(invalid_source)
    self.assertGreater(len(errors), 0)
    self.assertTrue(any("expected_error_type" in str(e) for e in errors))
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the RTMC-Compiler root directory
   - Check that all source modules exist and are importable
   - Run `python tests/validate_tests.py` to diagnose issues

2. **Test Failures**
   - Check if the feature is fully implemented
   - Some tests may fail if compiler components are incomplete
   - Review error messages for specific failure reasons

3. **Missing Dependencies**
   - Ensure all required Python packages are installed
   - Check that PLY (Python Lex-Yacc) is available if used

### Getting Help
- Review the test output for specific error messages
- Check the compiler's implementation status
- Examine the source code comments for implementation notes
- Run individual test files to isolate issues

## Contributing

When adding new features to the compiler:

1. **Add corresponding tests** for the new functionality
2. **Update existing tests** if behavior changes
3. **Test both success and failure cases**
4. **Document any new test patterns** in this README
5. **Ensure tests pass** before committing changes

The test suite serves as both validation and documentation of the compiler's capabilities, helping ensure that all documented features work correctly and continue to work as the codebase evolves.
