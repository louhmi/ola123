# Sistema de Monitoreo y registro Sensor de Gas 
### Jefferson Borja JuanPablo Pinto
## Funcionamiento
* El sistema de monitoreo funciona con dos microcontroladores esp32, un sensor de Gas MQ-2, un led RGB y un buzzer, uno de los esp32 esta programado para leer el sensor y activar el led rgb, tambien guarda un paquete de datos de los datos de el sensor y el estado del led y se lo envia por el protocolo ESP-NOW a la segunda esp32 mediante la direccion mac.
* El esp32 recibe este dato y se lo envia al servidor mediante USB gracias a un programa de python (bridge.py) el cual sirve para leer el puerto USB
* mientras tanto, el servidor envia los datos a la base de datos supabase en la tabla historial_gas, mientras tanto la pagina web(index.html) va actualizandose en base al servidor, cambiando el color y mostrando las alertas.
## Como usarlo 
* lo primero es tener el circuito funcionando, iniciar el bridge.py y el app.py (en el entorno virtual) luego abrir la pagina web y probar el sistema, la pagina web cuenta con un boton para desactivar la alarma.
