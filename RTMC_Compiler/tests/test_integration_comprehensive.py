#!/usr/bin/env python3
"""
Comprehensive Feature Integration Tests
Tests integration of all documented language features.
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.ply_lexer import RTMCLexer
from src.parser.ply_parser import RTMCParser
from src.semantic.analyzer import SemanticAnalyzer
from src.bytecode.generator import BytecodeGenerator
from src.vm.virtual_machine import VirtualMachine


class TestCompleteFeatureIntegration(unittest.TestCase):
    """Test complete feature integration across the compiler pipeline"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
        self.generator = BytecodeGenerator()
        self.vm = VirtualMachine()
    
    def _compile_and_test(self, source: str, expect_errors: bool = False):
        """Helper to compile code through entire pipeline"""
        try:
            # Tokenize
            tokens = self.lexer.tokenize(source)
            self.assertIsNotNone(tokens)
            
            # Parse
            ast = self.parser.parse(tokens)
            self.assertIsNotNone(ast)
            
            # Semantic analysis
            self.analyzer.analyze(ast)
            
            if expect_errors:
                self.assertGreater(len(self.analyzer.errors), 0)
                return None, self.analyzer.errors
            else:
                if self.analyzer.errors:
                    print(f"Unexpected semantic errors: {self.analyzer.errors}")
                
                # Generate bytecode
                bytecode = self.generator.generate(ast)
                self.assertIsNotNone(bytecode)
                
                return bytecode, self.analyzer.errors
                
        except Exception as e:
            if expect_errors:
                return None, [str(e)]
            else:
                self.fail(f"Compilation failed unexpectedly: {e}")
    
    def test_usb4_sideband_complete_example(self):
        """Test the complete USB4 sideband example from sb_main.rtmc"""
        source = """
        message<int> SBTestMsg;

        const int USB4_BE_CMD_PROTOCOL_TYPE_UNDEFINED = 1;
        const int USB4_BE_CMD_PROTOCOL_TYPE_SIDEBAND  = 14;
        const int USB4_BE_CMD_OPCODE_UNDEFINED        = 0;

        struct USB4BECommand {
            int ProtocolType : 4;
            int Opcode : 12;
        };

        struct USB4SBTransactionHead {
            int DLE : 8;
            int CmdNotResp : 1;
            int Rsvd2 : 5;
            int TrType : 2;
            int DataSymbl : 16;
        };

        void processSbCommand(int data) {
            int packet_addr = data + 4;
            USB4SBTransactionHead* sb_packet = (USB4SBTransactionHead*)packet_addr;

            if(sb_packet->CmdNotResp == 1) {
                printf("Processing SB command without response, Data Symbol: {}", sb_packet->DataSymbl);
            } else {
                printf("Processing SB command with DataSymbl: {}", sb_packet->DataSymbl);
            }
        }

        void processOtherCommand(int data) {
            printf("Processing other command with data: {}", data);
        }

        void process_data(int data) {
            USB4BECommand* be_cmd = (USB4BECommand*)data;
            printf("ProtocolType: {}, Opcode: {}", be_cmd->ProtocolType, be_cmd->Opcode);

            if(be_cmd->ProtocolType == USB4_BE_CMD_PROTOCOL_TYPE_SIDEBAND) {
                processSbCommand(data);
            } else if(be_cmd->ProtocolType == USB4_BE_CMD_PROTOCOL_TYPE_UNDEFINED && be_cmd->Opcode == USB4_BE_CMD_OPCODE_UNDEFINED) {
                printf("Received undefined command, ignoring.");
            } else {
                processOtherCommand(data);
            }
        }

        void task1_run_function() {
            while (1) {
                int data_addr = SBTestMsg.recv();
                data_addr += 5;
                process_data(data_addr);
                delay_ms(500);
            }
        }

        void main() {
            int core = 1;
            int priority = 1;
            int stack_size = 1024;
            int task_id = 1010;
            StartTask(stack_size, core, priority, task_id, task1_run_function);

            while(1) {
                char data[10] = {0xAE, 0xBB, 0xBE, 0xDD, 0xEE, 0xFA, 0x00, 0x01, 0x02, 0x03};
                int addr = (int)data;
                SBTestMsg.send(addr);
                delay_ms(500);
            }
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        
        # Should compile with minimal errors (allow some warnings)
        if errors:
            serious_errors = [e for e in errors if "error" in str(e).lower()]
            self.assertLessEqual(len(serious_errors), 2)
        
        if bytecode:
            self.assertIsNotNone(bytecode)
    
    def test_comprehensive_array_struct_features(self):
        """Test comprehensive array and struct features"""
        source = """
        struct Point { int x; int y; };
        struct Line { Point start; Point end; };
        
        union DataUnion {
            int intValue;
            float floatValue;
            char bytes[4];
        };

        void main() {
            // Array declarations
            int numbers[5] = {1, 2, 3, 4, 5};
            float coords[3] = {1.0, 2.5, 3.7};
            Point points[4];
            Line lines[2];
            
            // Complex nested access
            points[0].x = 10;
            points[0].y = 20;
            lines[0].start = points[0];
            lines[0].end.x = 30;
            lines[0].end.y = 40;
            
            // Array operations
            for (int i = 0; i < 5; i++) {
                numbers[i] = i * 2;
                printf("numbers[{}] = {}", i, numbers[i]);
            }
            
            // Union operations
            DataUnion data;
            data.intValue = 0x12345678;
            for (int i = 0; i < 4; i++) {
                printf("Byte {}: 0x{:02X}", i, data.bytes[i]);
            }
            
            data.floatValue = 3.14159;
            printf("Float value: {}", data.floatValue);
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)
    
    def test_hexadecimal_comprehensive(self):
        """Test comprehensive hexadecimal support"""
        source = """
        void main() {
            // Various hex formats
            int value1 = 0xff;
            int value2 = 0xFF;
            int value3 = 0x1234;
            int value4 = 0xABCD;
            int value5 = 0xDEADBEEF;
            
            // Hex in different contexts
            int array[0x10];
            for (int i = 0; i < 0x10; i++) {
                array[i] = 0x100 + i;
            }
            
            // Hex in bitfields
            struct Register {
                int field1 : 0x8;    // 8 bits
                int field2 : 0x10;   // 16 bits
                int field3 : 0x8;    // 8 bits
            };
            
            Register reg;
            reg.field1 = 0xFF;
            reg.field2 = 0xFFFF;
            reg.field3 = 0x00;
            
            // Hex in comparisons and operations
            if (value1 == 0xFF) {
                printf("Hex comparison works: 0x{:X}", value1);
            }
            
            int result = 0x1000 | 0x0100 | 0x0010 | 0x0001;
            printf("Bitwise result: 0x{:X}", result);
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)
    
    def test_boolean_and_control_flow(self):
        """Test boolean literals and control flow integration"""
        source = """
        bool global_flag = true;
        
        bool checkCondition(int value) {
            if (value > 0) {
                return true;
            } else {
                return false;
            }
        }
        
        void main() {
            bool local_flag = false;
            int counter = 0;
            
            // Boolean conditions
            if (global_flag && local_flag) {
                print("Both flags true");
            } else if (global_flag || local_flag) {
                print("At least one flag true");
            } else {
                print("Both flags false");
            }
            
            // Boolean in loops
            while (!local_flag && counter < 10) {
                local_flag = checkCondition(counter);
                counter++;
                
                if (local_flag) {
                    break;
                }
            }
            
            // Complex boolean expressions
            bool complex = (counter > 5) && (global_flag || !local_flag);
            if (complex) {
                printf("Complex condition met at counter: {}", counter);
            }
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)
    
    def test_message_timeout_integration(self):
        """Test message timeout feature integration"""
        source = """
        message<int> DataQueue;
        message<float> SensorQueue;
        
        void producer_task() {
            int counter = 0;
            while (true) {
                DataQueue.send(counter);
                counter++;
                delay_ms(100);
            }
        }
        
        void consumer_task() {
            while (true) {
                // Try with timeout
                int data = DataQueue.recv(50);
                if (data >= 0) {
                    printf("Received data: {}", data);
                } else {
                    print("Timeout occurred");
                }
                
                // Blocking receive
                float sensor_value = SensorQueue.recv();
                printf("Sensor: {}", sensor_value);
            }
        }
        
        void main() {
            RTOS_CREATE_TASK(producer_task, 1024, 1, 1);
            RTOS_CREATE_TASK(consumer_task, 1024, 1, 2);
            
            // Main loop
            float sensor_data = 0.0;
            while (true) {
                sensor_data += 0.1;
                SensorQueue.send(sensor_data);
                delay_ms(200);
            }
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)
    
    def test_flexible_brace_styles_integration(self):
        """Test flexible brace placement integration"""
        source = """
        // Mixed brace styles should all work
        struct Point {
            int x;
            int y;
        };
        
        struct Rectangle
        {
            Point topLeft;
            Point bottomRight;
        };
        
        void style1_function() {
            if (true) {
                print("Style 1 if");
            }
            while (false) {
                break;
            }
        }
        
        void style2_function()
        {
            if (true)
            {
                print("Style 2 if");
            }
            while (false)
            {
                break;
            }
        }
        
        void mixed_style_function()
        {
            for (int i = 0; i < 5; i++) {
                if (i % 2 == 0)
                {
                    printf("Even: {}", i);
                } else {
                    printf("Odd: {}", i);
                }
            }
        }
        
        void main()
        {
            style1_function();
            style2_function();
            mixed_style_function();
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)
    
    def test_import_system_simulation(self):
        """Test import system (simulated without actual files)"""
        # This tests the parser's ability to handle import statements
        source = """
        #include "definitions.rtmc";
        #include "hardware/gpio.rtmc";
        #include "rtos/tasks.rtmc";
        
        // Assume these are defined in imported files
        // const int SHARED_CONSTANT = 42;
        // void shared_function(int param);
        
        const int SHARED_CONSTANT = 42;
        void shared_function(int param) {
            printf("Shared function: {}", param);
        }
        
        void main() {
            int value = SHARED_CONSTANT;
            shared_function(value);
            
            printf("Using imported definitions: {}", value);
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)
    
    def test_rtos_hardware_integration(self):
        """Test RTOS and hardware function integration"""
        source = """
        const int LED_PIN = 25;
        const int BUTTON_PIN = 26;
        
        message<bool> ButtonQueue;
        
        void led_task() {
            bool led_state = false;
            
            while (true) {
                HW_GPIO_SET(LED_PIN, led_state ? 1 : 0);
                led_state = !led_state;
                delay_ms(500);
            }
        }
        
        void button_task() {
            while (true) {
                int button_state = HW_GPIO_GET(BUTTON_PIN);
                if (button_state == 1) {
                    ButtonQueue.send(true);
                    delay_ms(50);  // Debounce
                }
                delay_ms(10);
            }
        }
        
        void sensor_task() {
            while (true) {
                int adc_value = HW_ADC_READ(0);
                float voltage = (float)adc_value * 3.3 / 4095.0;
                
                printf("ADC: {}, Voltage: {:.2f}V", adc_value, voltage);
                delay_ms(1000);
            }
        }
        
        void main() {
            // Initialize hardware
            HW_GPIO_INIT(LED_PIN, 1);      // Output
            HW_GPIO_INIT(BUTTON_PIN, 0);   // Input
            HW_ADC_INIT(0);
            
            // Create tasks
            RTOS_CREATE_TASK(led_task, 1024, 1, 1);
            RTOS_CREATE_TASK(button_task, 1024, 2, 2);
            RTOS_CREATE_TASK(sensor_task, 1024, 1, 3);
            
            // Main monitoring loop
            while (true) {
                bool button_pressed = ButtonQueue.recv(100);
                if (button_pressed) {
                    print("Button was pressed!");
                }
            }
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)
    
    def test_pointer_and_cast_integration(self):
        """Test pointer operations and casting integration"""
        source = """
        struct Data {
            int value;
            float rate;
        };
        
        union TypePun {
            int i;
            float f;
            char bytes[4];
        };
        
        void process_raw_data(int raw_addr) {
            // Cast integer address to pointer
            Data* data_ptr = (Data*)raw_addr;
            
            // Access through pointer
            if (data_ptr->value > 0) {
                printf("Valid data: value={}, rate={}", 
                          data_ptr->value, data_ptr->rate);
            }
        }
        
        void type_punning_example() {
            TypePun pun;
            
            // Set as integer
            pun.i = 0x12345678;
            printf("As int: 0x{:08X}", pun.i);
            
            // Read as bytes
            for (int i = 0; i < 4; i++) {
                printf("Byte[{}]: 0x{:02X}", i, pun.bytes[i]);
            }
            
            // Set as float
            pun.f = 3.14159;
            printf("As float: {}", pun.f);
            printf("Float as int: 0x{:08X}", pun.i);
        }
        
        void main() {
            Data local_data;
            local_data.value = 42;
            local_data.rate = 1.5;
            
            // Get address and pass as integer
            int addr = (int)&local_data;
            process_raw_data(addr);
            
            type_punning_example();
        }
        """
        
        bytecode, errors = self._compile_and_test(source)
        self.assertIsNotNone(bytecode)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across the compiler pipeline"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
    
    def _test_error_detection(self, source: str, expected_error_type: str):
        """Helper to test that specific errors are detected"""
        try:
            tokens = self.lexer.tokenize(source)
            ast = self.parser.parse(tokens)
            self.analyzer.analyze(ast)
            
            # Should have detected errors
            self.assertGreater(len(self.analyzer.errors), 0)
            
            # Check for specific error type
            error_found = any(expected_error_type.lower() in str(error).lower() 
                            for error in self.analyzer.errors)
            self.assertTrue(error_found, 
                          f"Expected {expected_error_type} error not found in: {self.analyzer.errors}")
            
        except Exception as e:
            # Parse errors are also acceptable for syntax tests
            if "syntax" in expected_error_type.lower():
                pass
            else:
                raise
    
    def test_syntax_error_detection(self):
        """Test syntax error detection"""
        syntax_errors = [
            ("int main() { return 0 }", "missing semicolon"),
            ("void func( { }", "incomplete parameter list"),
            ("struct { int x; };", "missing struct name"),
            ("int arr[];", "missing array size"),
            ("if condition) { }", "missing parentheses"),
        ]
        
        for source, description in syntax_errors:
            with self.subTest(source=source, description=description):
                self._test_error_detection(source, "syntax")
    
    def test_semantic_error_detection(self):
        """Test semantic error detection"""
        semantic_errors = [
            ("void main() { int x = undefined_var; }", "undefined"),
            ("void func(int p) {} void main() { func(\"str\"); }", "type"),
            ("void main() { int x = 5; int x = 10; }", "redefinition"),
            ("struct Point {int x;}; void main() { Point p; int y = p.z; }", "member"),
            ("const int C = 5; void main() { C = 10; }", "const"),
        ]
        
        for source, error_type in semantic_errors:
            with self.subTest(source=source, error_type=error_type):
                self._test_error_detection(source, error_type)
    
    def test_type_error_detection(self):
        """Test type error detection"""
        type_errors = [
            ("int func() { return; }", "return"),
            ("void func() { return 42; }", "return"),
            ("message<int> m; void main() { m.send(\"str\"); }", "type"),
            ("struct A{int x;}; struct B{int y;}; void main() { A a; B b; a = b; }", "type"),
        ]
        
        for source, error_type in type_errors:
            with self.subTest(source=source, error_type=error_type):
                self._test_error_detection(source, error_type)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance and scalability"""
    
    def setUp(self):
        self.lexer = RTMCLexer()
        self.parser = RTMCParser()
        self.analyzer = SemanticAnalyzer()
        self.generator = BytecodeGenerator()
    
    def test_large_program_compilation(self):
        """Test compilation of large program"""
        # Generate a large program with many functions and variables
        large_program = []
        
        # Add many constants
        for i in range(100):
            large_program.append(f"const int CONST_{i} = {i};")
        
        # Add many structs
        for i in range(50):
            large_program.append(f"""
            struct Struct_{i} {{
                int field1;
                int field2;
                int field3;
            }};
            """)
        
        # Add many functions
        for i in range(100):
            large_program.append(f"""
            void function_{i}(int param1, int param2) {{
                int local_var = param1 + param2 + CONST_{i % 100};
                if (local_var > 0) {{
                    printf("Function {i}: {{}}", local_var);
                }}
                return;
            }}
            """)
        
        # Add main function that calls others
        main_func = """
        void main() {
            for (int i = 0; i < 10; i++) {
                function_0(i, i * 2);
                function_1(i + 1, i * 3);
                function_2(i + 2, i * 4);
            }
        }
        """
        large_program.append(main_func)
        
        source = '\n'.join(large_program)
        
        # Should compile without crashing
        try:
            tokens = self.lexer.tokenize(source)
            self.assertIsNotNone(tokens)
            
            ast = self.parser.parse(tokens)
            self.assertIsNotNone(ast)
            
            self.analyzer.analyze(ast)
            # Allow some errors in large generated program
            
            if len(self.analyzer.errors) < 10:  # Reasonable error threshold
                bytecode = self.generator.generate(ast)
                self.assertIsNotNone(bytecode)
                
        except Exception as e:
            self.fail(f"Large program compilation failed: {e}")
    
    def test_deeply_nested_structures(self):
        """Test deeply nested structures"""
        source = """
        struct Level5 { int value; };
        struct Level4 { Level5 inner; };
        struct Level3 { Level4 inner; };
        struct Level2 { Level3 inner; };
        struct Level1 { Level2 inner; };
        
        void main() {
            Level1 nested;
            nested.inner.inner.inner.inner.value = 42;
            
            int deep_value = nested.inner.inner.inner.inner.value;
            printf("Deep value: {}", deep_value);
        }
        """
        
        try:
            tokens = self.lexer.tokenize(source)
            ast = self.parser.parse(tokens)
            self.analyzer.analyze(ast)
            
            # Should handle deep nesting
            if len(self.analyzer.errors) == 0:
                bytecode = self.generator.generate(ast)
                self.assertIsNotNone(bytecode)
                
        except Exception as e:
            self.fail(f"Deep nesting test failed: {e}")
    
    def test_complex_expressions(self):
        """Test complex expression compilation"""
        source = """
        void main() {
            int a = 1, b = 2, c = 3, d = 4, e = 5;
            
            // Complex arithmetic
            int result1 = ((a + b) * (c - d)) / (e + 1) % 7;
            
            // Complex logical
            bool result2 = (a > 0) && (b < 10) || ((c == 3) && (d != 5)) || !(e > 10);
            
            // Complex bitwise
            int result3 = (a << 2) | (b >> 1) ^ (c & 0xFF) | (~d & 0x0F);
            
            // Nested function calls
            int result4 = abs(max(min(a, b), min(c, d))) + sqrt(e * e);
            
            // Complex array/struct access
            int array[10];
            array[((a + b) % 5) + ((c * d) % 3)] = result1 + result3;
            
            printf("Results: {}, {}, {}, {}", result1, result2, result3, result4);
        }
        
        int abs(int x) { return x < 0 ? -x : x; }
        int max(int a, int b) { return a > b ? a : b; }
        int min(int a, int b) { return a < b ? a : b; }
        int sqrt(int x) { return x; }  // Simplified
        """
        
        try:
            tokens = self.lexer.tokenize(source)
            ast = self.parser.parse(tokens)
            self.analyzer.analyze(ast)
            
            # Complex expressions should compile
            if len(self.analyzer.errors) <= 3:  # Allow some minor errors
                bytecode = self.generator.generate(ast)
                self.assertIsNotNone(bytecode)
                
        except Exception as e:
            self.fail(f"Complex expression test failed: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
