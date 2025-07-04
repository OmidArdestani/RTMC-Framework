// Minimal message test
message<int> TestMsg;

void main() {
    DBG_PRINT("Testing message declaration");
    TestMsg.send(123);
    int val = TestMsg.recv();
    DBG_PRINT("Message test done");
}
