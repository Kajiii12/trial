#include <ESP8266WiFi.h>

// Wi-Fi credentials
const char* ssid = "Novastar";      // Replace with your Wi-Fi SSID
const char* password = "2024@staR"; // Replace with your Wi-Fi password

// Define IR sensor pins
const int sensor1Pin = D5; // GPIO14 -> IR Sensor 1 (Slot 1)
const int sensor2Pin = D6; // GPIO12 -> IR Sensor 2 (Slot 2)
const int sensor3Pin = D7; // GPIO13 -> IR Sensor 3 (Slot 3)

// Server on port 80
WiFiServer server(80);

void setup() {
  Serial.begin(115200);

  // Initialize IR sensor pins as input
  pinMode(sensor1Pin, INPUT);
  pinMode(sensor2Pin, INPUT);
  pinMode(sensor3Pin, INPUT);

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Start the server
  server.begin();
}

void loop() {
  // Check for client connections
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client Connected");

    // Wait for client request
    while (!client.available()) {
      delay(1);
    }

    String request = client.readStringUntil('\r');
    client.flush();

    // Prepare sensor status
    String sensorData = getSensorStatus();

    // Send a proper HTTP response
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/plain");
    client.println("Connection: close");
    client.println();  // Blank line to separate headers from content
    client.println(sensorData); // Send the sensor status

    delay(1);
    Serial.println("Client disconnected");
  }
}

String getSensorStatus() {
  // Read IR sensor values
  int sensor1State = digitalRead(sensor1Pin);
  int sensor2State = digitalRead(sensor2Pin);
  int sensor3State = digitalRead(sensor3Pin);

  // Determine slot status based on sensor state
  String slot1Status = (sensor1State == LOW) ? "Occupied" : "Open";
  String slot2Status = (sensor2State == LOW) ? "Occupied" : "Open";
  String slot3Status = (sensor3State == LOW) ? "Occupied" : "Open";

  // Create a single string with all slot statuses
  String response = "Slot 1: " + slot1Status + "\n";
  response += "Slot 2: " + slot2Status + "\n";
  response += "Slot 3: " + slot3Status;

  return response;
}