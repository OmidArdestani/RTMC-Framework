// RT-Micro-C Message Passing Example
// This demonstrates the new message<T> syntax for inter-task communication

struct SensorData {
    int id;
    float temperature;
    int timestamp;
};

// Global message queues
message<int> ControlSignal;
message<SensorData> SensorReadings;

Task<0, 2> SensorTask {
    int sensorPin = 25;
    int readingId = 0;

    void run() {
        HW_ADC_INIT(sensorPin);
        
        while (1) {
            // Read sensor data
            int rawValue = HW_ADC_READ(sensorPin);
            
            // Create sensor data packet
            struct SensorData reading;
            reading.id = readingId;
            reading.temperature = rawValue * 0.1;  // Convert to temperature
            reading.timestamp = 1000 + readingId;   // Simulated timestamp
            
            // Send sensor reading to processing task
            SensorReadings.send(reading);
            
            readingId = readingId + 1;
            
            DBG_PRINT("Sensor: Sent reading");
            RTOS_DELAY_MS(2000);  // Read every 2 seconds
        }
    }
}

Task<1, 2> ProcessorTask {
    float temperatureThreshold = 25.0;

    void run() {
        while (1) {
            // Wait for sensor data
            struct SensorData data = SensorReadings.recv();
            
            DBG_PRINT("Processor: Received sensor data");
            
            // Process the data
            if (data.temperature > temperatureThreshold) {
                // Send alert signal to control task
                ControlSignal.send(1);  // Alert signal
                DBG_PRINT("Processor: Temperature alert sent");
            } else {
                // Send normal signal
                ControlSignal.send(0);  // Normal signal
            }
        }
    }
}

Task<1, 1> ControlTask {
    int alertPin = 13;
    int fanPin = 12;

    void run() {
        HW_GPIO_INIT(alertPin, 1);   // Output for alert LED
        HW_GPIO_INIT(fanPin, 1);     // Output for fan control
        
        while (1) {
            // Wait for control signal
            int signal = ControlSignal.recv();
            
            if (signal == 1) {
                // Alert condition
                HW_GPIO_SET(alertPin, 1);   // Turn on alert LED
                HW_GPIO_SET(fanPin, 1);     // Turn on fan
                DBG_PRINT("Control: Alert mode activated");
            } else {
                // Normal condition
                HW_GPIO_SET(alertPin, 0);   // Turn off alert LED
                HW_GPIO_SET(fanPin, 0);     // Turn off fan
                DBG_PRINT("Control: Normal mode");
            }
        }
    }
}

void main() {
    DBG_PRINT("RT-Micro-C Message Passing System Starting");
    
    // Tasks are automatically created and scheduled
    // Message queues are automatically created from declarations
    
    while (1) {
        RTOS_DELAY_MS(10000);
        DBG_PRINT("Main: System heartbeat");
    }
}
