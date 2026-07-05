from flask import Flask, render_template, request, jsonify

from supabase import create_client, Client

from datetime import datetime



app = Flask(__name__)



# =====================================================================

# CONFIGURACIÓN DE TU SUPABASE

# (Reemplaza con el Project ID y la clave anon public reales de tu panel)

# =====================================================================

SUPABASE_URL = "https://ydpwsqpmknloivekfrbi.supabase.co"

SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlkcHdzcXBta25sb2l2ZWtmcmJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI2ODM0NTYsImV4cCI6MjA5ODI1OTQ1Nn0.86lTR6ftTHI7fF_jpZzvRUMbWpGT0tUk05613QYFmxU"



# Inicializamos el cliente de Supabase conectado a la nube

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



# Variable global para recordar el último estado en tiempo real en el Dashboard

ultimo_dato = {

    "tarjeta": "Desconectado",

    "nivel_gas": 0,

    "estado": "Esperando dispositivo..."

}



# Variable global para avisarle a bridge.py que el usuario presionó "Desactivar"

solicitud_reset = False





# 1. RUTA PRINCIPAL: Renderiza la página web y trae el historial de Supabase

@app.route('/')

def index():

    try:

        # Trae los últimos 10 registros de la tabla que creamos en el SQL Editor

        respuesta = supabase.table("historial_gas").select("*").order("id", desc=True).limit(10).execute()

        historial = respuesta.data

    except Exception as e:

        print(f"⚠️ Alerta al leer Supabase: {e}")

        historial = []

        

    return render_template('index.html', historial=historial)





# 2. RUTA DE ESTATUS: El JavaScript del HTML y el script 'bridge.py' consultan aquí en vivo

@app.route('/api/status', methods=['GET'])

def obtener_estatus():

    global solicitud_reset

    

    # Preparamos la respuesta con los datos en vivo y el estado del botón

    response = {

        "tarjeta": ultimo_dato["tarjeta"],

        "nivel_gas": ultimo_dato["nivel_gas"],

        "estado": ultimo_dato["estado"],

        "reset_pendiente": solicitud_reset

    }

    

    # Si quien consulta es el script de Python bridge.py, bajamos la bandera del reset

    if request.args.get('desde_bridge') == 'true':

        solicitud_reset = False

        

    return jsonify(response)





# 3. RUTA DE EVENTO (POST): Aquí 'bridge.py' inyecta los datos que lee del cable USB

@app.route('/api/evento', methods=['POST'])

def recibir_evento():

    global ultimo_dato

    tarjeta = request.form.get('tarjeta')

    evento = request.form.get('evento')

    nivel_gas = request.form.get('nivel_gas')

    

    # Capturamos la hora de tu Ubuntu para guardarla en la columna 'fecha_hora'

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



    if nivel_gas and evento:

        # Actualizamos la variable global para que el Dashboard cambie al instante

        ultimo_dato = {

            "tarjeta": tarjeta,

            "nivel_gas": int(nivel_gas),

            "estado": evento

        }

        

        try:

            # Armamos el diccionario con los nombres EXACTOS de la tabla en Supabase

            datos_a_insertar = {

                "fecha_hora": fecha_actual,

                "tarjeta": tarjeta,

                "nivel_gas": int(nivel_gas),

                "estado": evento

            }

            

            # Subimos el registro directo a la nube de Supabase

            supabase.table("historial_gas").insert(datos_a_insertar).execute()

            print(f"☁️ [SUPABASE GUARDADO] -> Gas: {nivel_gas} | Estado: {evento}")

            return jsonify({"status": "success"}), 200

            

        except Exception as e:

            print(f"❌ Error al guardar en Supabase: {e}")

            return jsonify({"status": "error", "message": str(e)}), 500

            

    return jsonify({"status": "error", "message": "Datos incompletos"}), 400





# 4. RUTA DE REINICIO (POST): Se ejecuta cuando haces clic en el botón de la página web

@app.route('/api/reset', methods=['POST'])

def reset_alarma():

    global solicitud_reset

    solicitud_reset = True  # Activamos la señal para que bridge.py la detecte

    print("🔕 Solicitud de apagado de alarma registrada en la API")

    return jsonify({"status": "success", "message": "Orden de reinicio enviada"}), 200





if __name__ == '__main__':

    # Ejecuta el servidor en el puerto 5000

    app.run(host='0.0.0.0', port=5000, debug=True)
