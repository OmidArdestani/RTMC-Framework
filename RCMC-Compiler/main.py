#!/usr/bin/env python3
"""
Mini-C Compiler Main Entry Point
Compiles Mini-C source code to bytecode for the RT-App-Lang virtual machine.
"""

import sys
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lexer.tokenizer import Tokenizer
from parser.parser import Parser
from semantic.analyzer import SemanticAnalyzer
from optimizer.optimizer import Optimizer
from bytecode.generator import BytecodeGenerator
from bytecode.writer import BytecodeWriter

def main():
    parser = argparse.ArgumentParser(description='Mini-C Compiler for RTOS')
    parser.add_argument('input', help='Input Mini-C source file')
    parser.add_argument('-o', '--output', help='Output bytecode file (.vmb)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--ast', action='store_true', help='Print AST')
    parser.add_argument('--tokens', action='store_true', help='Print tokens')
    parser.add_argument('--no-optimize', action='store_true', help='Skip optimization')
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.input}' not found")
        sys.exit(1)
    
    # Set output file
    if args.output:
        output_file = args.output
    else:
        output_file = Path(args.input).with_suffix('.vmb')
    
    try:
        # Compilation pipeline
        if args.verbose:
            print("Stage 1: Lexical Analysis...")
        
        tokenizer = Tokenizer(source_code)
        tokens = tokenizer.tokenize()
        
        if args.tokens:
            print("=== TOKENS ===")
            for token in tokens:
                print(f"{token.type.name}: '{token.value}' at line {token.line}")
            print()
        
        if args.verbose:
            print("Stage 2: Parsing...")
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        if args.ast:
            print("=== AST ===")
            print(ast)
            print()
        
        if args.verbose:
            print("Stage 3: Semantic Analysis...")
        
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(ast)
        
        if not args.no_optimize:
            if args.verbose:
                print("Stage 4: Optimization...")
            
            optimizer = Optimizer()
            ast = optimizer.optimize(ast)
        
        if args.verbose:
            print("Stage 5: Bytecode Generation...")
        
        bytecode_generator = BytecodeGenerator()
        bytecode_program = bytecode_generator.generate(ast)
        
        if args.verbose:
            print("Stage 6: Writing Output...")
        
        writer = BytecodeWriter()
        writer.write(bytecode_program, output_file)
        
        if args.verbose:
            print(f"Compilation successful! Output: {output_file}")
        
    except Exception as e:
        print(f"Compilation error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
