// Advanced struct member assignment test
// This tests complex struct operations including member assignments

struct Point {
    int x;
    int y;
};

struct Rectangle {
    struct Point top_left;
    struct Point bottom_right;
    int color;
};

void test_struct_assignments() {
    struct Point p1;
    struct Rectangle rect;
    
    // Simple member assignments
    p1.x = 10;
    p1.y = 20;
    
    // Complex member assignments
    rect.top_left.x = 0;
    rect.top_left.y = 0;
    rect.bottom_right.x = 100;
    rect.bottom_right.y = 50;
    rect.color = 255;
    
    DBG_PRINT("Advanced struct test completed");
}

void main() {
    test_struct_assignments();
}
