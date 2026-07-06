#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

uint8_t broadcastAddress[] = {0x70, 0x4B, 0xCA, 0x4C, 0xD0, 0xEC}; // Tu MAC real

const int ledVerde = 12;
const int ledAmarillo = 14;
const int ledRojo = 27;
const int pinBuzzer = 25; // PIN DEL BUZZER
const int pinSensor = 34; 

// Variable para congelar la alarma
bool alarmaActiva = false;

typedef struct struct_mensaje {
  int valor_gas;
  char estado[20];
} struct_mensaje;

typedef struct struct_comando {
  char accion[20];
} struct_comando;

struct_mensaje misDatos;
struct_comando comandoRecibido;
esp_now_peer_info_t peerInfo;

void onDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  // Monitoreo de envío
}

// 🚨 NUEVO: Función que escucha cuando la página web manda a APAGAR la alarma
void onDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  memcpy(&comandoRecibido, incomingData, sizeof(comandoRecibido));
  
  if (strcmp(comandoRecibido.accion, "RESET_ALARMA") == 0) {
    alarmaActiva = false; // Desactivamos el bloqueo
    digitalWrite(pinBuzzer, LOW);
    digitalWrite(ledRojo, LOW);
    Serial.println("¡Alarma desactivada desde la página web!");
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(ledVerde, OUTPUT);
  pinMode(ledAmarillo, OUTPUT);
  pinMode(ledRojo, OUTPUT);
  pinMode(pinBuzzer, OUTPUT);

  WiFi.mode(WIFI_STA);
  esp_wifi_set_channel(11, WIFI_SECOND_CHAN_NONE);

  if (esp_now_init() != ESP_OK) return;

  esp_now_register_send_cb(onDataSent);
  esp_now_register_recv_cb(esp_now_recv_cb_t(onDataRecv)); // Escuchar comandos
  
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 11; 
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);
}

void loop() {
  int lectura = analogRead(pinSensor); 
  misDatos.valor_gas = lectura;

  // Si ya se disparó la alarma, se queda bloqueada ignorando lecturas bajas
  if (alarmaActiva) {
    strcpy(misDatos.estado, "PELIGRO CRÍTICO");
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarillo, LOW);
    digitalWrite(ledRojo, HIGH);
    digitalWrite(pinBuzzer, HIGH); // Sigue pitando
  } 
  else {
    // Lógica normal si la alarma no está retenida
    if (lectura < 1000) {
      strcpy(misDatos.estado, "SEGURO");
      digitalWrite(ledVerde, HIGH);
      digitalWrite(ledAmarillo, LOW);
      digitalWrite(ledRojo, LOW);
      digitalWrite(pinBuzzer, LOW);
    } 
    else if (lectura < 2500) {
      strcpy(misDatos.estado, "ADVERTENCIA");
      digitalWrite(ledVerde, LOW);
      digitalWrite(ledAmarillo, HIGH);
      digitalWrite(ledRojo, LOW);
      digitalWrite(pinBuzzer, LOW);
    } 
    else {
      // ¡DISPARA Y CONGELA LA ALARMA!
      strcpy(misDatos.estado, "PELIGRO CRÍTICO");
      alarmaActiva = true; 
    }
  }

  esp_now_send(broadcastAddress, (uint8_t *) &misDatos, sizeof(misDatos));
  delay(1500); 
}