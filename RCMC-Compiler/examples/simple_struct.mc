// Simple struct example
struct Point {
    int x;
    int y;
};

void main() {
    struct Point p;
    
    // Simple assignments work
    // p.x = 10;  // This would require member access assignment
    // p.y = 20;
    
    DBG_PRINT("Simple struct example");
    RTOS_DELAY_MS(1000);
}
