# VS Code Extension Build Instructions

## Prerequisites

1. **Node.js and npm**: Install Node.js (version 16 or later) from [nodejs.org](https://nodejs.org)
2. **VS Code**: Install Visual Studio Code
3. **VS Code Extension Manager**: Install the `@vscode/vsce` package globally

## Installation

1. Open a terminal in the extension directory
2. Install dependencies:
   ```bash
   npm install
   ```

3. Install the VS Code Extension Manager globally:
   ```bash
   npm install -g @vscode/vsce
   ```

## Building the Extension

1. Compile TypeScript:
   ```bash
   npm run compile
   ```

2. Package the extension:
   ```bash
   vsce package
   ```

   This creates a `.vsix` file that can be installed in VS Code.

## Installing the Extension

1. **From VSIX file**:
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Click the "..." menu
   - Select "Install from VSIX..."
   - Choose the generated `.vsix` file

2. **For Development**:
   - Press F5 in VS Code while the extension project is open
   - This opens a new Extension Development Host window
   - The extension is automatically loaded

## Testing the Extension

1. Create a new file with `.rtmc` extension
2. Start typing RTMC code - syntax highlighting should work
3. Try snippets like `task`, `gpio-blink`, `struct`, etc.
4. Use Ctrl+Space for IntelliSense suggestions

## Configuration

After installation, configure the extension:

1. Open VS Code Settings (Ctrl+,)
2. Search for "RTMC"
3. Set the following paths:
   - `rtmc.compilerPath`: Path to your Python executable
   - `rtmc.compilerScript`: Path to your RTMC compiler's main.py
   - `rtmc.vmRunnerScript`: Path to your RTMC VM runner script

Example configuration:
```json
{
  "rtmc.compilerPath": "python",
  "rtmc.compilerScript": "C:/path/to/RTMC-Compiler/main.py",
  "rtmc.vmRunnerScript": "C:/path/to/RTMC-Compiler/vm_runner.py",
  "rtmc.enableDebugMode": false
}
```

## Usage

1. **Compile**: Press Ctrl+Shift+B to compile an RTMC file
2. **Run**: Press Ctrl+F5 to run the compiled program
3. **Debug**: Use Command Palette (Ctrl+Shift+P) and run "RTMC: Debug RTMC Program"

## Features

- Syntax highlighting for RTMC language
- Code snippets for common patterns
- IntelliSense support
- Build and run integration
- Custom dark theme optimized for RTMC
- Hover information for functions

## Troubleshooting

1. **Extension not loading**: Check the VS Code Developer Tools (Help -> Toggle Developer Tools)
2. **Compilation errors**: Ensure Python and RTMC compiler paths are correct
3. **Syntax highlighting not working**: Verify the file has `.rtmc` extension

## Development

To modify the extension:

1. Edit source files in `src/`
2. Run `npm run compile` to build
3. Press F5 to test changes
4. Use `npm run watch` for automatic compilation during development
