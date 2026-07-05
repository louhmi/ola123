import serial
import requests
import time

# =====================================================================
# CONFIGURACIÓN DEL PUERTO SERIAL
# (Asegúrate de que el puerto sea el correcto en tu Ubuntu, ej: /dev/ttyUSB0 o /dev/ttyACM0)
# =====================================================================
PUERTO_USB = '/dev/ttyUSB0'
BAUD_RATE = 115200

print(f"🔌 Conectando al puerto {PUERTO_USB}...")
try:
    ser = serial.Serial(PUERTO_USB, BAUD_RATE, timeout=1)
    time.sleep(2)  # Esperamos a que se estabilice la conexión serial
    print("✅ Conexión serial establecida con éxito.")
except Exception as e:
    print(f"❌ Error crítico: No se pudo abrir el puerto {PUERTO_USB}. Verifícalo.")
    print(f"Detalle del error: {e}")
    exit()

# Bucle infinito de comunicación bidireccional
while True:
    # -----------------------------------------------------------------
    # TAREA 1: LEER DEL USB ➔ MANDAR A LA API (FLASK/SUPABASE)
    # -----------------------------------------------------------------
    try:
        if ser.in_waiting > 0:
            # Lee la línea enviada por la Tarjeta 2
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            
            # Verificamos que la línea tenga el formato esperado (ejemplo: "1250,ADVERTENCIA")
            if "," in linea:
                partes = linea.split(",")
                nivel_gas = partes[0]
                evento = partes[1]
                
                # Preparamos el paquete para enviarlo localmente a Flask
                payload = {
                    "tarjeta": "ESP32_Caldera_Mac", # Puedes poner la MAC real aquí si quieres
                    "nivel_gas": nivel_gas,
                    "evento": evento
                }
                
                # Hacemos la petición POST a tu servidor local
                res_post = requests.post("http://localhost:5000/api/evento", data=payload)
                if res_post.status_code == 200:
                    print(f"➔ [USB ➔ WEB] Datos enviados con éxito: Gas={nivel_gas} | Estado={evento}")
    except Exception as e:
        print(f"⚠️ Error al leer del USB o postear en Flask: {e}")

    # -----------------------------------------------------------------
    # TAREA 2: CONSULTAR A LA API ➔ MANDAR SEÑAL DE APAGADO AL USB
    # -----------------------------------------------------------------
    try:
        # Le preguntamos a Flask si hay un botón pulsado pasándole el parámetro 'desde_bridge'
        res_get = requests.get("http://localhost:5000/api/status?desde_bridge=true").json()
        
        # Si la bandera 'reset_pendiente' está en True, le avisamos al ESP32 por el cable
        if res_get.get("reset_pendiente") == True:
            ser.write(b"RESET\n") # Inyecta la palabra clave por el puerto serie
            print("🔕 [WEB ➔ USB] Se detectó clic en la web. ¡Enviando orden RESET al ESP32!")
    except Exception as e:
        print(f"⚠️ Error al consultar el estado de reinicio en Flask: {e}")
        
    # Espera un breve instante para no saturar el procesador de tu Ubuntu
    time.sleep(0.5)
