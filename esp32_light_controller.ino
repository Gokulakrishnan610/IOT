#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

const char* ssid = "Gokul";
const char* password = "12345678";


struct TrafficTiming {
  int green;
  int yellow;
  int red;
};


TrafficTiming north = {5, 5, 5};
TrafficTiming south = {5, 5, 5};
TrafficTiming east  = {5, 5, 5};
TrafficTiming west  = {5, 5, 5};


struct TrafficLights {
  int greenPin;
  int yellowPin;
  int redPin;
};

TrafficLights lightsNorth = {14, 27, 26};
TrafficLights lightsSouth = {25, 33, 32};
TrafficLights lightsEast  = {18, 19, 21};
TrafficLights lightsWest  = {22, 23, 4};

AsyncWebServer server(80);


void setupPins() {
  TrafficLights dirs[] = {lightsNorth, lightsSouth, lightsEast, lightsWest};
  for (auto dir : dirs) {
    pinMode(dir.greenPin, OUTPUT);
    pinMode(dir.yellowPin, OUTPUT);
    pinMode(dir.redPin, OUTPUT);
    digitalWrite(dir.greenPin, LOW);
    digitalWrite(dir.yellowPin, LOW);
    digitalWrite(dir.redPin, LOW);
  }
}


void allRed() {
  digitalWrite(lightsNorth.redPin, HIGH);
  digitalWrite(lightsSouth.redPin, HIGH);
  digitalWrite(lightsEast.redPin, HIGH);
  digitalWrite(lightsWest.redPin, HIGH);

  digitalWrite(lightsNorth.greenPin, LOW);
  digitalWrite(lightsSouth.greenPin, LOW);
  digitalWrite(lightsEast.greenPin, LOW);
  digitalWrite(lightsWest.greenPin, LOW);

  digitalWrite(lightsNorth.yellowPin, LOW);
  digitalWrite(lightsSouth.yellowPin, LOW);
  digitalWrite(lightsEast.yellowPin, LOW);
  digitalWrite(lightsWest.yellowPin, LOW);
}

void runDirection(TrafficLights lights, TrafficTiming timing) {
  allRed(); 
  digitalWrite(lights.redPin, LOW);
  digitalWrite(lights.greenPin, HIGH);
  delay(timing.green * 1000);

  digitalWrite(lights.greenPin, LOW);
  digitalWrite(lights.yellowPin, HIGH);
  delay(timing.yellow * 1000);
  digitalWrite(lights.yellowPin, LOW);
  digitalWrite(lights.redPin, HIGH);
}

void setup() {
  Serial.begin(115200);
  setupPins();

  WiFi.begin(ssid, password);
  Serial.printf("🔌 Connecting to %s", ssid);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected!");
  Serial.println(WiFi.localIP());

  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(200, "text/plain", "ESP32 Traffic Controller Online");
  });

  server.on("/update_timings", HTTP_POST, [](AsyncWebServerRequest *request){}, NULL,
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t, size_t) {
      StaticJsonDocument<512> doc;
      if (deserializeJson(doc, data)) {
        request->send(400, "application/json", "{\"status\":\"error\",\"msg\":\"Invalid JSON\"}");
        return;
      }

      north = { doc["north"]["green"], doc["north"]["yellow"], doc["north"]["red"] };
      south = { doc["south"]["green"], doc["south"]["yellow"], doc["south"]["red"] };
      east  = { doc["east"]["green"],  doc["east"]["yellow"],  doc["east"]["red"] };
      west  = { doc["west"]["green"],  doc["west"]["yellow"],  doc["west"]["red"] };

      Serial.println("✅ New timings received:");
      serializeJsonPretty(doc, Serial);

      request->send(200, "application/json", "{\"status\":\"success\"}");
    });

  server.begin();
}

void loop() {
  runDirection(lightsNorth, north);
  runDirection(lightsEast, east);
  runDirection(lightsSouth, south);
  runDirection(lightsWest, west);
}
