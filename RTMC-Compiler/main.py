#!/usr/bin/env python3
"""
RT-Micro-C Compiler Main Entry Point
Compiles RT-Micro-C source code to bytecode for the RT-Micro-C virtual machine.
"""

import sys
import argparse
from pathlib import Path
from typing import Set, Dict

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.lexer.tokenizer import Tokenizer
from src.parser.parser import Parser
from src.parser.ast_nodes import ProgramNode, ImportStmtNode
from src.semantic.analyzer import SemanticAnalyzer
from src.optimizer.optimizer import Optimizer
from src.bytecode.generator import BytecodeGenerator
from src.bytecode.writer import BytecodeWriter

imported_filepaths = set()

def parse_with_imports(file_path: Path, imported_files: Set[Path] = None) -> ProgramNode:
    """Parse a file and recursively parse any imported files"""
    if imported_files is None:
        imported_files = set()
    
    # Convert to absolute path to prevent duplicate imports
    abs_path = file_path.resolve()
    
    # Check for circular imports
    if abs_path in imported_files:
        return ProgramNode([])  # Return empty program for circular imports
    
    imported_files.add(abs_path)
    
    # Read the file
    try:
        with open(abs_path, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Import file not found: {file_path}")
    
    # Tokenize and parse
    tokenizer = Tokenizer(source_code, str(abs_path))
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Collect import statements and other statements separately
    imports = []
    other_statements = []
    
    for stmt in ast.declarations:
        if isinstance(stmt, ImportStmtNode):
            if stmt.filepath not in imported_filepaths:
                imports.append(stmt)
                imported_filepaths.add(stmt.filepath)
        else:
            other_statements.append(stmt)
    
    # Process imports recursively
    imported_statements = []
    for import_stmt in imports:
        # Resolve import path relative to current file
        import_path = abs_path.parent / import_stmt.filepath
        imported_ast = parse_with_imports(import_path, imported_files.copy())
        imported_statements.extend(imported_ast.declarations)
    
    # Combine imported statements with current file statements
    # Put imports first to ensure proper dependency order
    all_statements = imported_statements + other_statements
    
    return ProgramNode(all_statements, filename=file_path.name)

def main():
    parser = argparse.ArgumentParser(description='RT-Micro-C Compiler for RTOS')
    parser.add_argument('input', help='Input RT-Micro-C source file')
    parser.add_argument('-o', '--output', help='Output bytecode file (.vmb)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--ast', action='store_true', help='Print AST')
    parser.add_argument('--tokens', action='store_true', help='Print tokens')
    parser.add_argument('--no-optimize', action='store_true', help='Skip optimization')
    parser.add_argument('--no-semantic', action='store_true', help='Skip semantic analysis')
    parser.add_argument('--release', action='store_true', help='Compile in release mode (strip debug info)')
    parser.add_argument('--run', action='store_true', help='Run the compiled program')

    args = parser.parse_args()
    
    # Determine compilation mode
    from src.bytecode.generator import CompileMode
    compile_mode = CompileMode.RELEASE if args.release else CompileMode.DEBUG
    
    # Read input file
    input_path = Path(args.input)
    
    # Set output file
    if args.output:
        output_file = args.output
    else:
        output_file = input_path.with_suffix('.vmb')
    
    try:
        # Compilation pipeline with import support
        if args.verbose:
            print("Stage 1: Lexical Analysis and Parsing (with imports)...")
        
        # Parse with recursive import handling
        ast = parse_with_imports(input_path)
        
        # Extract tokens for debugging if requested
        if args.tokens:
            print("=== TOKENS (main file only) ===")
            with open(input_path, 'r') as f:
                source_code = f.read()
            tokenizer = Tokenizer(source_code, str(input_path))
            tokens = tokenizer.tokenize()
            for token in tokens:
                print(f"{token.type.name}: '{token.value}' at {token.filename}:{token.line}")
            print()
        
        if args.ast:
            print("=== AST ===")
            print(ast)
            print()
        
        if args.verbose:
            print("Stage 3: Semantic Analysis...")
        
        if not args.no_semantic:
            semantic_analyzer = SemanticAnalyzer()
            semantic_analyzer.analyze(ast)
        
        if not args.no_optimize:
            if args.verbose:
                print("Stage 4: Optimization...")
            
            optimizer = Optimizer()
            ast = optimizer.optimize(ast)
        
        if args.verbose:
            print("Stage 5: Bytecode Generation...")
        
        bytecode_generator = BytecodeGenerator(compile_mode)
        bytecode_program = bytecode_generator.generate(ast)
        
        if args.verbose:
            print(f"Generated {len(bytecode_program.instructions)} instructions")
            print(f"Compilation mode: {compile_mode.name}")
            if compile_mode == CompileMode.DEBUG:
                print(f"Debug info: {len(bytecode_program.debug_info)} entries")
        
        if args.verbose:
            print("Stage 6: Writing Output...")
        
        writer = BytecodeWriter()
        writer.write(bytecode_program, output_file)
        
        if args.verbose:
            print(f"Compilation successful! Output: {output_file}")
            print(f"Mode: {compile_mode.name}")

        if args.run:
            from src.vm.virtual_machine import VirtualMachine
            vm = VirtualMachine()
            vm.load_program(bytecode_program)
            vm.run()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Compilation error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
