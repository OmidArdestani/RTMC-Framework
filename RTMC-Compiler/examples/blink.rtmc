// Basic GPIO LED blink example
// This example demonstrates hardware GPIO control

const int LED_PIN = 25;
const int DELAY_MS = 500;

void setup() {
    // Initialize GPIO pin as output
    HW_GPIO_INIT(LED_PIN, 1);
}

void blink_task() {
    while (1) {
        HW_GPIO_SET(LED_PIN, 1);    // Turn LED on
        RTOS_DELAY_MS(DELAY_MS);    // Wait 500ms
        HW_GPIO_SET(LED_PIN, 0);    // Turn LED off
        RTOS_DELAY_MS(DELAY_MS);    // Wait 500ms
    }
}

void main() {
    setup();
    
    // Create a task for blinking
    RTOS_CREATE_TASK(blink_task, "Blink", 1024, 5, 0);
    
    // Main loop
    while (1) {
        RTOS_DELAY_MS(1000);
        DBG_PRINT("Main task running");
    }
}
