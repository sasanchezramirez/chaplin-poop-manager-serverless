#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <time.h>
#include "secrets.h"

// --- Credenciales y AWS (Desde secrets.h) ---
const char* ssid = SECRET_SSID;                                                  // Reemplaza con tu SSID
const char* pass = SECRET_PASS;                                                             // Reemplaza con tu contraseña de WiFi
const char* aws_endpoint = SECRET_AWS_ENDPOINT;  // Tu URL de AWS
const char* api_key = SECRET_API_KEY;                                                      // Tu propia API key de SAM

// --- Pines ---
#define TRIG_PIN 17
#define ECHO_PIN 16
#define LED_PIN 2
#define CLEAN_LED_PIN 26

// --- Variables de Tiempo y Estado ---
const unsigned long sampleInterval = 2000;  // Revisar el sensor cada 2 segundos
unsigned long previousMillis = 0;
unsigned int ledActivations = 0;
unsigned int activationsUntilCleaning = 0;

// Sistema Antibote (Debouncing del gato moviéndose frente al sensor)
bool chaplinIsPresent = false;
bool chaplinWasPresent = false;
int missedReadings = 0;             // Cuántas veces el sensor midió "vacío" seguido
const int MAX_MISSED_READINGS = 5;  // Si mide "vacío" 5 veces seguidas (10 seg), asumimos que salió

// Variables para medir la duración de la ida al baño
unsigned long timeEntered = 0;  // Epoch time cuando entró
unsigned long timeExited = 0;   // Epoch time cuando salió

// --- Configuración NTP (Reloj de Internet) ---
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 0;  // Usamos UTC (GMT 0) porque AWS prefiere timestamps globales
const int daylightOffset_sec = 0;

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(CLEAN_LED_PIN, OUTPUT);
  Serial.begin(115200);

  // 1. Conectar a WiFi
  Serial.print("Conectando a WiFi");
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  // 2. Sincronizar Reloj Interno del ESP32
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.println("Sincronizando reloj con NTP...");
  struct tm timeinfo;
  while (!getLocalTime(&timeinfo)) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\nReloj Sincronizado!");
}

unsigned long getCurrentTimestamp() {
  time_t now;
  time(&now);
  return now;
}

void sendDataToAWS(unsigned long timestamp, int duration_seconds) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Error: WiFi no conectado");
    return;
  }

  // Usar WiFiClientSecure ya que AWS requiere HTTPS (TLS)
  WiFiClientSecure client;
  // Permitir la conexión sin verificar la huella del SSL para máxima compatibilidad con API Gateway
  client.setInsecure();

  HTTPClient http;
  http.begin(client, aws_endpoint);

  // Headers obligatorios
  http.addHeader("Content-Type", "application/json");
  http.addHeader("x-api-key", api_key);

  // Construir el JSON como lo espera la Lambda de AWS Python
  String payload = "{";
  payload += "\"pet_id\":\"chaplin\",";
  payload += "\"duration_seconds\":" + String(duration_seconds) + ",";
  payload += "\"timestamp\":" + String(timestamp);
  payload += "}";

  Serial.print("Enviando JSON a AWS: ");
  Serial.println(payload);

  int httpResponseCode = http.POST(payload);

  if (httpResponseCode > 0) {
    Serial.print("Código de Respuesta AWS: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println("Cuerpo: " + response);
  } else {
    Serial.print("Error en el POST: ");
    Serial.println(http.errorToString(httpResponseCode).c_str());
  }
  http.end();
}

void loop() {
  unsigned long currentMillis = millis();

  // Reset diario de LEDs de limpieza (apróximado usando el reloj interno)
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    if (timeinfo.tm_hour == 23 && timeinfo.tm_min == 59 && timeinfo.tm_sec < 2) {
      ledActivations = 0;
      activationsUntilCleaning = 0;
      delay(2000);  // Evitar re-disparar en el mismo minuto
    }
  }

  if (currentMillis - previousMillis >= sampleInterval) {
    previousMillis = currentMillis;

    // --- Medir Distancia ---
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duration = pulseIn(ECHO_PIN, HIGH, 3000000UL);  // Timeout de 3s
    int distance = duration * 0.034 / 2;

    // --- Lógica del Sensor con Debouncing ---
    // Si mide entre 2cm y 30cm, el gato está ahí tapando el sensor
    if (distance > 1 && distance < 30) {
      chaplinIsPresent = true;
      missedReadings = 0;  // Reseteamos el contador de pérdidas
    } else {
      // El sensor no lo vio. Pero no lo marcamos como 'ausente' inmediatamente
      missedReadings++;

      if (missedReadings >= MAX_MISSED_READINGS) {
        // Solo si pasaron X intentos seguidos viendo vacío, confirmamos que sí salió
        chaplinIsPresent = false;
      }
    }

    // --- Lógica de Negocio (Entrar y Salir) ---

    // CASO 1: Chaplin acaba de entrar al arenero
    if (chaplinIsPresent && !chaplinWasPresent) {
      timeEntered = getCurrentTimestamp();  // Guardamos el Epoch Time inicial
      Serial.println("Chaplin acaba de ENTRAR al baño...");
      digitalWrite(LED_PIN, HIGH);
    }

    // CASO 2: Chaplin sigue adentro
    else if (chaplinIsPresent && chaplinWasPresent) {
      Serial.println("Chaplin aún está en el baño haciendo...");
    }

    // CASO 3: Chaplin acaba de SALIR (Este es el momento de enviar a AWS)
    else if (!chaplinIsPresent && chaplinWasPresent) {
      timeExited = getCurrentTimestamp();
      int durationSeconds = timeExited - timeEntered;

      Serial.println("Chaplin SALIÓ del baño.");
      digitalWrite(LED_PIN, LOW);

      // Descartar falsos positivos de menos de 10 segundos
      if (durationSeconds > 10) {
        ledActivations++;
        activationsUntilCleaning++;

        Serial.print("Duración total de Chaplin: ");
        Serial.print(durationSeconds);
        Serial.println(" segundos");

        // Enviar a la nube
        sendDataToAWS(timeEntered, durationSeconds);
      } else {
        Serial.println("Fue una estadía muy corta (falsa alarma). Descartado.");
      }
    }

    // Guardar estado
    chaplinWasPresent = chaplinIsPresent;

    // Control del foco LED de aviso de limpieza
    if (activationsUntilCleaning >= 7) {
      digitalWrite(CLEAN_LED_PIN, HIGH);
    } else {
      digitalWrite(CLEAN_LED_PIN, LOW);
    }
  }
}
