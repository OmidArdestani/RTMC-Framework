// Advanced RT-Micro-C Task System Example
// Shows multiple tasks with bit-fields, structs, and hardware interaction

struct SensorData {
    int temperature : 8;    // -128 to 127
    int humidity : 7;       // 0-100% 
    int pressure : 12;      // 0-4095 range
    int valid : 1;          // validity flag
    int reserved : 4;       // padding
};

// Global shared sensor data (in real system, protected by mutex)
struct SensorData globalSensors;

Task<0, 1> HighPriorityController {
    int emergencyThreshold = 80;
    
    void run() {
        while (1) {
            // High priority safety check
            if (globalSensors.temperature > emergencyThreshold) {
                DBG_PRINT("EMERGENCY: Temperature critical!");
                HW_GPIO_SET(25, 1);  // Emergency LED
            } else {
                HW_GPIO_SET(25, 0);  // Turn off emergency LED
            }
            
            RTOS_DELAY_MS(100);  // Fast monitoring
        }
    }
}

Task<1, 3> SensorReader {
    int sensorPin = 26;
    int readInterval = 1000;
    
    void run() {
        HW_ADC_INIT(sensorPin);
        
        while (1) {
            // Read and pack sensor data using bit-fields
            int raw_temp = HW_ADC_READ(sensorPin);
            
            // Convert to temperature (simplified)
            int temperature = (raw_temp * 100) / 4095;
            
            // Update shared sensor data
            globalSensors.temperature = temperature;
            globalSensors.humidity = 65;      // Mock data
            globalSensors.pressure = 1013;    // Mock atmospheric pressure
            globalSensors.valid = 1;          // Mark as valid
            
            DBG_PRINT("Sensor data updated");
            RTOS_DELAY_MS(readInterval);
        }
    }
}

Task<0, 5> DisplayTask {
    int displayInterval = 2000;
    
    void run() {
        while (1) {
            if (globalSensors.valid) {
                DBG_PRINT("Temperature readings available");
                DBG_PRINT("System status: OK");
            } else {
                DBG_PRINT("Waiting for sensor data...");
            }
            
            RTOS_DELAY_MS(displayInterval);
        }
    }
}

void main() {
    // Initialize shared data
    globalSensors.temperature = 0;
    globalSensors.humidity = 0;
    globalSensors.pressure = 0;
    globalSensors.valid = 0;
    
    // Initialize hardware
    HW_GPIO_INIT(25, 1);  // Emergency LED as output
    
    DBG_PRINT("Advanced RT-Micro-C Task System Starting");
    DBG_PRINT("Tasks: HighPriorityController, SensorReader, DisplayTask");
    
    // Main system loop
    while (1) {
        RTOS_DELAY_MS(10000);
        DBG_PRINT("System heartbeat - all tasks running");
    }
}
