from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client, Client
from datetime import datetime

app = Flask(__name__)
# datos de supabase para iniciarlo
SUPABASE_URL = "https://ydpwsqpmknloivekfrbi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlkcHdzcXBta25sb2l2ZWtmcmJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI2ODM0NTYsImV4cCI6MjA5ODI1OTQ1Nn0.86lTR6ftTHI7fF_jpZzvRUMbWpGT0tUk05613QYFmxU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# variables globales
ultimo_dato = {
    "tarjeta": "Ninguno",
    "nivel_gas": 0,
    "estado": "SEGURO"
} 
solicitud_reset = False
# pagina web
@app.route('/')
def index():
    try:
    # traer los ultimos 10 registros
        respuesta = supabase.table("historial_gas").select("*").order("id", desc=True).limit(10).execute()
        historial = respuesta.data
    except Exception as e:
        print(f" Alerta al leer Supabase: {e}")
        historial = []
        
    # ponemos el historial de la base de datos y el dato actual en el html
    return render_template('index.html', historial=historial, ultimo=ultimo_dato)
# ruta para el brigde.py 
@app.route('/api/status', methods=['GET'])
def obtener_estatus():
    global solicitud_reset
    #guardamos la informacion actual del sensor  y ver si hay un reset 
    response = {
        "tarjeta": ultimo_dato["tarjeta"],
        "nivel_gas": ultimo_dato["nivel_gas"],
        "estado": ultimo_dato["estado"],
        "reset_pendiente": solicitud_reset
    }
    if request.args.get('desde_bridge') == 'true': #si se activa desde el sricpt bridge, apagamos el ciclo 
        solicitud_reset = False
    return jsonify(response)
#ruta 3, el puente mete los datos al usb 
@app.route('/api/evento', methods=['POST'])
def recibir_evento():
    global ultimo_dato
    tarjeta = request.form.get('tarjeta')
    evento = request.form.get('evento')
    nivel_gas = request.form.get('nivel_gas')
    #guardamos la fecha actual
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if nivel_gas and evento:
    #cambiamos las variables globales 
        ultimo_dato = {
            "tarjeta": tarjeta,
            "nivel_gas": int(nivel_gas),
            "estado": evento
        }
        try: #estructura para meter la fila en la nube 
            datos_a_insertar = {
                "fecha_hora": fecha_actual,
                "tarjeta": tarjeta,
                "nivel_gas": int(nivel_gas),
                "estado": evento
            }
            supabase.table("historial_gas").insert(datos_a_insertar).execute()
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error"}), 400

# ruta de reset, se ejecuta al pulsar el boton de la web
@app.route('/api/reset', methods=['POST'])
def reset_alarma():
    global solicitud_reset
    solicitud_reset = True
    print(" Solicitud de apagado de alarma registrada ")
    return redirect(url_for('index')) # Redirección HTML nativa

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
