#include "pico/stdlib.h"
#include "hardware/uart.h"

#define UART_ID uart0
#define BAUD_RATE 115200

#define UART_TX_PIN 0 // GPIO0
#define UART_RX_PIN 1 // GPIO1

void send_at_command(const char *command) {
    uart_puts(UART_ID, command);
    uart_puts(UART_ID, "\r\n");
}

void read_response() {
    while (uart_is_readable(UART_ID)) {
        char c = uart_getc(UART_ID);
        putchar(c); // Print response to console
    }
}

int InitWifi() {
    // Initialize UART
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    printf("Initializing ESP8266...\n");

    // Send AT commands to ESP8266
    send_at_command("AT"); // Test command
    sleep_ms(1000);
    read_response();

    send_at_command("AT+CWMODE=1"); // Set Wi-Fi mode to Station
    sleep_ms(1000);
    read_response();

    send_at_command("AT+CWJAP=\"SSID\",\"PASSWORD\""); // Connect to Wi-Fi
    sleep_ms(5000);
    read_response();
}