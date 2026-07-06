#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

// =====================================================================
// CONFIGURACIÓN DE LA MAC DE LA OTRA TARJETA
// =====================================================================
// Dirección MAC física de tu Tarjeta 1 (Emisora) para poder responderle por el aire
uint8_t addressTarjeta1[] = {0x70, 0x4B, 0xCA, 0x4C, 0xD0, 0xEC}; // REVISE QUE SEA LA MAC REAL

// =====================================================================
// ESTRUCTURAS DE DATOS (Paquetes que viajan por el aire)
// =====================================================================
// Estructura para RECIBIR los datos del sensor de gas
typedef struct struct_mensaje {
  int valor_gas;
  char estado[20];
} struct_mensaje;

// Estructura para ENVIAR la orden de apagado (Reset)
typedef struct struct_comando {
  char accion[20];
} struct_comando;

// Instanciamos las variables basadas en las estructuras anteriores
struct_mensaje datosRecibidos;
struct_comando comandoAEnviar;
esp_now_peer_info_t peerInfo;

// =====================================================================
// CALLBACK: FUNCIÓN QUE ESCUCHA CUANDO LLEGA UN DATO POR EL AIRE
// =====================================================================
void onDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  // Copiamos los bytes que llegaron por el aire a nuestra variable estructurada
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  
  // TRUCO CLAVE: Lo imprimimos en el monitor serie separado por una coma (Ej: "1450,SEGURO")
  // Esto es exactamente lo que el script 'bridge.py' va a leer desde el cable USB
  Serial.printf("%d,%s\n", datosRecibidos.valor_gas, datosRecibidos.estado);
}

// =====================================================================
// CONFIGURACIÓN INICIAL (Se ejecuta una sola vez)
// =====================================================================
void setup() {
  // Inicializamos el puerto serie a la misma velocidad que 'bridge.py' (115200)
  Serial.begin(115200);
  
  // Configuramos el ESP32 en modo Estación (necesario para ESP-NOW)
  WiFi.mode(WIFI_STA);
  
  // Forzamos a que use el canal 11 del WiFi (debe ser idéntico en ambas tarjetas)
  esp_wifi_set_channel(11, WIFI_SECOND_CHAN_NONE);

  // Inicializamos el protocolo ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error inicializando ESP-NOW");
    return;
  }
  
  // Registramos la función de arriba para que se ejecute automáticamente cada vez que llegue un mensaje
  esp_now_register_recv_cb(esp_now_recv_cb_t(onDataRecv));

  // Registramos a la Tarjeta 1 en la tabla de emparejamiento para poder enviarle comandos
  memcpy(peerInfo.peer_addr, addressTarjeta1, 6);
  peerInfo.channel = 11;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);
}

// =====================================================================
// BUCLE PRINCIPAL (Se ejecuta en ciclo infinito)
// =====================================================================
void loop() {
  // CANAL DE BAJADA: Revisamos si la computadora escribió algo por el cable USB
  if (Serial.available() > 0) {
    // Leemos la línea completa que mandó el script 'bridge.py'
    String str = Serial.readStringUntil('\n');
    str.trim(); // Limpiamos espacios o saltos de línea raros
    
    // Si la computadora mandó la palabra clave "RESET"
    if (str == "RESET") {
      // Metemos la orden en nuestra estructura
      strcpy(comandoAEnviar.accion, "RESET_ALARMA");
      
      // La lanzamos por el aire directo a la dirección MAC de la Tarjeta 1
      esp_now_send(addressTarjeta1, (uint8_t *) &comandoAEnviar, sizeof(comandoAEnviar));
    }
  }
  
  // Mini delay de estabilidad para no saturar el núcleo del procesador
  delay(20);
}