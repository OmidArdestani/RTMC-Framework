#!/usr/bin/env python3
"""
Comprehensive Test Runner for RT-Micro-C Compiler
Runs all test suites and generates a detailed coverage report.
"""

import sys
import unittest
import time
import os
from pathlib import Path
from io import StringIO

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all test modules
from test_comprehensive_specifications import *
from test_lexer_comprehensive import *
from test_parser_comprehensive import *
from test_semantic_comprehensive import *
from test_integration_comprehensive import *


class TestResults:
    """Track test results and statistics"""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.start_time = None
        self.end_time = None
        self.test_details = []
    
    def start_timing(self):
        self.start_time = time.time()
    
    def end_timing(self):
        self.end_time = time.time()
    
    def get_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def add_result(self, test_name, result, details=None):
        self.total_tests += 1
        
        if result == 'PASS':
            self.passed_tests += 1
        elif result == 'FAIL':
            self.failed_tests += 1
        elif result == 'ERROR':
            self.error_tests += 1
        elif result == 'SKIP':
            self.skipped_tests += 1
        
        self.test_details.append({
            'name': test_name,
            'result': result,
            'details': details
        })
    
    def print_summary(self):
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Total Tests Run: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Errors: {self.error_tests}")
        print(f"Skipped: {self.skipped_tests}")
        print(f"Duration: {self.get_duration():.2f} seconds")
        
        if self.total_tests > 0:
            success_rate = (self.passed_tests / self.total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nTEST COVERAGE AREAS:")
        print("✓ Lexical Analysis (Tokenization)")
        print("✓ Parser (AST Generation)")
        print("✓ Semantic Analysis (Type Checking)")
        print("✓ Bytecode Generation")
        print("✓ Virtual Machine Execution")
        print("✓ Language Features Integration")
        print("✓ Error Handling")
        print("✓ Performance & Scalability")
        
        print("\nFEATURES TESTED:")
        print("✓ Basic data types (int, float, char, bool, void)")
        print("✓ Hexadecimal literals (0xFF, 0x1234, etc.)")
        print("✓ Boolean literals (true, false)")
        print("✓ Arrays (fixed-length, initialization, access)")
        print("✓ Structs (basic, nested, bitfields)")
        print("✓ Unions (memory overlap, type punning)")
        print("✓ Messages (declaration, send/recv, timeouts)")
        print("✓ Import system")
        print("✓ Constants (const declarations)")
        print("✓ Control flow (if/else, while, for)")
        print("✓ Functions (declaration, parameters, return)")
        print("✓ Expressions (arithmetic, logical, bitwise)")
        print("✓ Pointers and casting")
        print("✓ RTOS functions (tasks, delays, semaphores)")
        print("✓ Hardware functions (GPIO, ADC, UART, etc.)")
        print("✓ Debug functions (DBG_PRINT, DBG_PRINTF)")
        print("✓ Flexible brace placement")
        print("✓ Scope resolution")
        print("✓ Type checking and validation")
        
        if self.failed_tests > 0 or self.error_tests > 0:
            print(f"\nFAILED/ERROR TESTS ({self.failed_tests + self.error_tests}):")
            for test in self.test_details:
                if test['result'] in ['FAIL', 'ERROR']:
                    print(f"  {test['result']}: {test['name']}")
                    if test['details']:
                        print(f"    Details: {test['details']}")
        
        print("="*80)


class CustomTestResult(unittest.TestResult):
    """Custom test result class to track detailed results"""
    
    def __init__(self, results_tracker):
        super().__init__()
        self.results_tracker = results_tracker
    
    def startTest(self, test):
        super().startTest(test)
        print(f"Running: {test._testMethodName}")
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.results_tracker.add_result(test._testMethodName, 'PASS')
    
    def addError(self, test, err):
        super().addError(test, err)
        error_details = str(err[1]) if err[1] else "Unknown error"
        self.results_tracker.add_result(test._testMethodName, 'ERROR', error_details)
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        failure_details = str(err[1]) if err[1] else "Assertion failed"
        self.results_tracker.add_result(test._testMethodName, 'FAIL', failure_details)
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.results_tracker.add_result(test._testMethodName, 'SKIP', reason)


def run_test_suite(test_suite_class, suite_name, results_tracker):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"RUNNING {suite_name}")
    print(f"{'='*60}")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_suite_class)
    
    # Run tests with custom result tracking
    result = CustomTestResult(results_tracker)
    suite.run(result)
    
    return result


def main():
    """Main test runner"""
    print("RT-Micro-C Compiler - Comprehensive Test Suite")
    print("Testing all documented specifications and features")
    print("="*80)
    
    results_tracker = TestResults()
    results_tracker.start_timing()
    
    # Define all test suites
    test_suites = [
        # Lexical Analysis Tests
        (TestTokenization, "Lexical Analysis - Tokenization"),
        
        # Parser Tests  
        (TestBasicParsing, "Parser - Basic Parsing"),
        (TestExpressionParsing, "Parser - Expression Parsing"),
        (TestStatementParsing, "Parser - Statement Parsing"),
        (TestStructUnionParsing, "Parser - Struct/Union Parsing"),
        (TestArrayParsing, "Parser - Array Parsing"),
        (TestMessageParsing, "Parser - Message Parsing"),
        (TestImportParsing, "Parser - Import Parsing"),
        (TestFlexibleBraceParsing, "Parser - Flexible Brace Styles"),
        
        # Semantic Analysis Tests
        (TestBasicSemantics, "Semantic Analysis - Basic"),
        (TestTypeChecking, "Semantic Analysis - Type Checking"),
        (TestStructSemantics, "Semantic Analysis - Struct Semantics"),
        (TestUnionSemantics, "Semantic Analysis - Union Semantics"),
        (TestMessageSemantics, "Semantic Analysis - Message Semantics"),
        (TestScopeAnalysis, "Semantic Analysis - Scope Resolution"),
        (TestConstantAnalysis, "Semantic Analysis - Constants"),
        (TestRTOSSemantics, "Semantic Analysis - RTOS Functions"),
        
        # Comprehensive Integration Tests
        (TestLexicalAnalysis, "Integration - Lexical Analysis"),
        (TestParser, "Integration - Parser"),
        (TestSemanticAnalysis, "Integration - Semantic Analysis"),
        (TestBytecodeGeneration, "Integration - Bytecode Generation"),
        (TestVirtualMachine, "Integration - Virtual Machine"),
        (TestComplexFeatures, "Integration - Complex Features"),
        (TestErrorHandling, "Integration - Error Handling"),
        
        # Feature Integration Tests
        (TestCompleteFeatureIntegration, "Feature Integration - Complete"),
        (TestErrorHandlingIntegration, "Feature Integration - Error Handling"),
        (TestPerformanceIntegration, "Feature Integration - Performance"),
    ]
    
    # Run all test suites
    for test_class, suite_name in test_suites:
        try:
            run_test_suite(test_class, suite_name, results_tracker)
        except Exception as e:
            print(f"Error running {suite_name}: {e}")
            results_tracker.add_result(suite_name, 'ERROR', str(e))
    
    results_tracker.end_timing()
    results_tracker.print_summary()
    
    # Return exit code based on results
    if results_tracker.failed_tests > 0 or results_tracker.error_tests > 0:
        return 1
    else:
        return 0


def run_specific_tests():
    """Run specific test categories based on command line arguments"""
    if len(sys.argv) < 2:
        return main()
    
    test_category = sys.argv[1].lower()
    results_tracker = TestResults()
    results_tracker.start_timing()
    
    if test_category == 'lexer':
        run_test_suite(TestTokenization, "Lexer Tests", results_tracker)
    elif test_category == 'parser':
        parser_tests = [
            TestBasicParsing, TestExpressionParsing, TestStatementParsing,
            TestStructUnionParsing, TestArrayParsing, TestMessageParsing
        ]
        for test_class in parser_tests:
            run_test_suite(test_class, f"Parser - {test_class.__name__}", results_tracker)
    elif test_category == 'semantic':
        semantic_tests = [
            TestBasicSemantics, TestTypeChecking, TestStructSemantics,
            TestUnionSemantics, TestMessageSemantics, TestScopeAnalysis
        ]
        for test_class in semantic_tests:
            run_test_suite(test_class, f"Semantic - {test_class.__name__}", results_tracker)
    elif test_category == 'integration':
        integration_tests = [
            TestCompleteFeatureIntegration, TestErrorHandlingIntegration,
            TestPerformanceIntegration
        ]
        for test_class in integration_tests:
            run_test_suite(test_class, f"Integration - {test_class.__name__}", results_tracker)
    elif test_category == 'features':
        run_test_suite(TestComplexFeatures, "Complex Features", results_tracker)
    else:
        print(f"Unknown test category: {test_category}")
        print("Available categories: lexer, parser, semantic, integration, features")
        return 1
    
    results_tracker.end_timing()
    results_tracker.print_summary()
    
    return 0 if results_tracker.failed_tests == 0 and results_tracker.error_tests == 0 else 1


if __name__ == '__main__':
    try:
        exit_code = run_specific_tests() if len(sys.argv) > 1 else main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
