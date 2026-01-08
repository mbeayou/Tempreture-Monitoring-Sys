#include <WiFi.h>
#include <ESPAsyncWebServer.h> // https://github.com/me-no-dev/ESPAsyncWebServer
#include <OneWire.h>
#include <DallasTemperature.h>
#include <U8g2lib.h>
#include <ArduinoJson.h>

// --- Configuration ---
const char* ssid = "GIGA";
const char* password = "47474747";

// Hardware Pins
#define ONE_WIRE_BUS 4
#define BUZZER_PIN 5

// --- Global Objects ---
// Display: SSH1106 I2C 128x64. Address usually 0x3C or 0x3D.
// U8G2_SH1106_128X64_NONAME_F_HW_I2C(rotation, [reset [, clock, data]])
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// Sensors
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Networking
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// State
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 2000; // 2 seconds
int deviceCount = 0;
float temps[4] = {0.0}; // Support up to 4 sensors, though requirement says 3
bool alarmTriggered = false;

// --- WebSocket Event Handler ---
void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
  if (type == WS_EVT_CONNECT) {
    Serial.printf("WebSocket client #%u connected from %s\n", client->id(), client->remoteIP().toString().c_str());
  } else if (type == WS_EVT_DISCONNECT) {
    Serial.printf("WebSocket client #%u disconnected\n", client->id());
  }
}

// --- Setup ---
void setup() {
  Serial.begin(115200);
  
  // Pin Modes
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, HIGH); // Assume Active LOW, so HIGH is OFF

  // Initialize Sensors
  sensors.begin();
  deviceCount = sensors.getDeviceCount();
  Serial.printf("Found %d devices\n", deviceCount);
  if (deviceCount > 4) deviceCount = 4; // Cap at 4 for this array

  // Initialize Display
  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 10, "Connecting WiFi...");
  u8g2.sendBuffer();

  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");
  Serial.println(WiFi.localIP());

  u8g2.clearBuffer();
  u8g2.drawStr(0, 10, "WiFi OK");
  u8g2.setCursor(0, 25);
  u8g2.print("IP: ");
  u8g2.print(WiFi.localIP());
  u8g2.sendBuffer();
  delay(1000);

  // WebSocket
  ws.onEvent(onEvent);
  server.addHandler(&ws);
  server.begin();
}

// --- Main Loop ---
void loop() {


  unsigned long now = millis();
  
  if (now - lastUpdate > 2000) {
    lastUpdate = now;
    sensors.requestTemperatures();
    float t1 = sensors.getTempCByIndex(0);

    // Create the JSON string
    StaticJsonDocument<200> doc;
    doc["t1"] = (t1 == DEVICE_DISCONNECTED_C) ? -127.0 : t1;
    doc["t2"] = 0.0;
    doc["t3"] = 0.0;
    doc["alarm"] = (t1 > 100);

    String jsonString;
    serializeJson(doc, jsonString);

    // SAFER BROADCAST: Only send if there are clients connected
    if (ws.count() > 0) {
      ws.textAll(jsonString);
      Serial.println("Sent to Dashboard: " + jsonString);
    } else {
      Serial.println("Waiting for Dashboard to connect... ( " + jsonString + " )");
    }
  }

  // Very important: cleanupClients must run frequently
  ws.cleanupClients();
  
  // Give the background WiFi tasks some time to breathe
  delay(1); 

}

