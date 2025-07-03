// Struct and bit-field example
// This example demonstrates struct usage with bit-fields

struct ControlRegister {
    int enable : 1;
    int mode : 2;
    int speed : 4;
    int reserved : 25;
};

struct SensorData {
    int temperature;
    int humidity;
    int pressure;
    struct ControlRegister control;
};

void configure_sensor() {
    struct SensorData sensor;
    
    // Configure control register
    sensor.control.enable = 1;
    sensor.control.mode = 2;
    sensor.control.speed = 8;
    
    // Initialize sensor data
    sensor.temperature = 0;
    sensor.humidity = 0;
    sensor.pressure = 0;
    
    DBG_PRINT("Sensor configured");
}

void main() {
    configure_sensor();
    
    while (1) {
        RTOS_DELAY_MS(1000);
        DBG_PRINT("System running");
    }
}
