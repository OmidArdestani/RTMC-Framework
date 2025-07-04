// Comprehensive bit-field demonstration
// This example shows how to use bit-fields for efficient memory usage in embedded systems

struct ControlRegister {
    int enable : 1;      // 1 bit: 0 or 1
    int mode : 2;        // 2 bits: 0-3
    int speed : 4;       // 4 bits: 0-15
    int priority : 3;    // 3 bits: 0-7
    int reserved : 22;   // 22 bits: remaining space in 32-bit word
};

struct SensorConfig {
    int active : 1;
    int threshold : 8;
    int gain : 4;
    int filter : 3;
    int unused : 16;
};

void main() {
    struct ControlRegister ctrl;
    struct SensorConfig sensor;
    
    // Configure control register
    ctrl.enable = 1;     // Enable the device
    ctrl.mode = 2;       // Set mode to 2 (out of 0-3)
    ctrl.speed = 8;      // Set speed to 8 (out of 0-15)
    ctrl.priority = 5;   // Set priority to 5 (out of 0-7)
    ctrl.reserved = 0;   // Clear reserved bits
    
    // Configure sensor
    sensor.active = 1;      // Enable sensor
    sensor.threshold = 128; // Set threshold (0-255)
    sensor.gain = 4;        // Set gain (0-15)
    sensor.filter = 2;      // Set filter mode (0-7)
    sensor.unused = 0;      // Clear unused bits
    
    DBG_PRINT("Bit-field configuration completed");
    
    // In a real embedded system, these packed structures would be
    // mapped to hardware registers for efficient control
}
