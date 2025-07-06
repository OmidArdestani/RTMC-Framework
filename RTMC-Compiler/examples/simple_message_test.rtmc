// Simple Message Passing Test
// Testing basic message<int> functionality

message<int> TestQueue;

Task<0, 2> SenderTask {
    void run() {
        while (1) {
            TestQueue.send(42);
            DBG_PRINT("Sender: Sent message");
            RTOS_DELAY_MS(1000);
        }
    }
}

Task<1, 2> ReceiverTask {
    void run() {
        while (1) {
            int value = TestQueue.recv();
            DBG_PRINT("Receiver: Got message");
            RTOS_DELAY_MS(500);
        }
    }
}

void main() {
    DBG_PRINT("Simple Message Test Starting");
    
    while (1) {
        RTOS_DELAY_MS(5000);
        DBG_PRINT("Main: heartbeat");
    }
}
