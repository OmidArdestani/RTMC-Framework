# Change Log

All notable changes to the RTMC Language Support extension will be documented in this file.

## [1.0.0] - 2025-07-08

### Added
- Initial release of RTMC Language Support extension
- Complete syntax highlighting for RTMC language
- IntelliSense support with auto-completion
- Hover information for functions and keywords
- Code snippets for common RTMC patterns
- Build and run integration
- Custom RTMC Dark theme
- Support for Task definitions with core and priority
- Hardware function highlighting (GPIO, ADC, Timer, UART, SPI, I2C)
- RTOS function highlighting and completion
- Debug function support
- Bitfield syntax highlighting
- Struct definition support
- Import statement support
- Bracket matching and auto-closing
- Comment toggling support
- Code folding support
- Indentation rules

### Features
- **Syntax Highlighting**: Complete coverage of RTMC language constructs
- **Code Snippets**: 20+ snippets for rapid development
- **IntelliSense**: Smart completion for keywords and functions
- **Build Integration**: Compile and run RTMC programs directly from VS Code
- **Theme**: Custom dark theme optimized for RTMC syntax
- **Language Configuration**: Proper bracket matching and commenting

### Commands
- `RTMC: Compile RTMC File` (Ctrl+Shift+B)
- `RTMC: Run RTMC Program` (Ctrl+F5)
- `RTMC: Debug RTMC Program`

### Settings
- `rtmc.compilerPath`: Path to Python interpreter
- `rtmc.compilerScript`: Path to RTMC compiler script
- `rtmc.vmRunnerScript`: Path to RTMC VM runner script
- `rtmc.enableDebugMode`: Enable debug mode for programs

### File Extensions
- `.rtmc` files are now recognized and highlighted
- `.vmb` bytecode files are supported for execution
