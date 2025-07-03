// ADC sensor reading example
// This example demonstrates ADC input and PWM output

const int SENSOR_PIN = 2;
const int PWM_TIMER = 0;
const int SAMPLE_RATE = 100;

void sensor_task() {
    int sensor_value;
    int pwm_duty;
    
    while (1) {
        // Read ADC value
        sensor_value = HW_ADC_READ(SENSOR_PIN);
        
        // Convert to PWM duty cycle (0-100%)
        pwm_duty = (sensor_value * 100) / 4095;
        
        // Set PWM duty cycle
        HW_TIMER_SET_PWM_DUTY(PWM_TIMER, pwm_duty);
        
        // Debug output
        DBG_PRINT("Sensor value read");
        
        // Wait for next sample
        RTOS_DELAY_MS(SAMPLE_RATE);
    }
}

void main() {
    // Initialize ADC
    HW_ADC_INIT(SENSOR_PIN);
    
    // Initialize PWM timer
    HW_TIMER_INIT(PWM_TIMER, 1, 1000);  // 1kHz PWM
    HW_TIMER_START(PWM_TIMER);
    
    // Create sensor reading task
    RTOS_CREATE_TASK(sensor_task, "Sensor", 512, 10, 0);
    
    // Main loop
    while (1) {
        RTOS_DELAY_MS(1000);
        DBG_PRINT("System running");
    }
}
