// RT-Micro-C Task Example - New Syntax
// This demonstrates the new Task<core, priority> syntax

Task<0, 2> BlinkTask {
    int ledPin = 13;
    int blinkDelay = 500;

    void run() {
        HW_GPIO_INIT(ledPin, 1);  // Initialize as output
        
        while (1) {
            HW_GPIO_SET(ledPin, 1);
            RTOS_DELAY_MS(blinkDelay);
            HW_GPIO_SET(ledPin, 0);
            RTOS_DELAY_MS(blinkDelay);
            
            DBG_PRINT("Blink cycle completed");
        }
    }
}

Task<1, 3> SensorTask {
    int sensorPin = 25;
    int threshold = 512;

    void run() {
        HW_ADC_INIT(sensorPin);
        
        while (1) {
            int reading = HW_ADC_READ(sensorPin);
            
            if (reading > threshold) {
                DBG_PRINT("Sensor threshold exceeded");
            }
            
            RTOS_DELAY_MS(1000);
        }
    }
}

void main() {
    DBG_PRINT("RT-Micro-C Task System Starting");
    
    // Tasks are automatically created and scheduled
    // No manual task creation needed
    
    while (1) {
        RTOS_DELAY_MS(5000);
        DBG_PRINT("Main loop heartbeat");
    }
}
