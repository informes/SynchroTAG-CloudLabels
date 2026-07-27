import json
import ssl
import time
import paho.mqtt.client as mqtt

# ============================================================
# CONFIGURACIÓN DEL BROKER (Datos exactos de tu ESP32)
# ============================================================
BROKER = "9fb9b61516d1479f82f3fb0ca571ba59.s1.eu.hivemq.cloud"
PORT = 8883
USER = "inktronic_esp32_01"
PASS = "SyncHive100"
TOPIC_CMD = "inktronic/esp32/01/cmd"
TOPIC_STATUS = "inktronic/esp32/01/status"

# ============================================================
# FUNCIONES DE CONTROL (ENVÍOS)
# ============================================================

def enviar_payload(client, payload):
    """Envía el JSON empaquetado al topic de la ESP32"""
    json_data = json.dumps(payload)
    print(f"\n[Enviando] -> {json_data}")
    client.publish(TOPIC_CMD, json_data, qos=1)

def controlar_luz(client, opcion):
    """Maneja los estados del LED interno (ON, OFF, BLINK)"""
    payload = {"estado": opcion.upper()}
    enviar_payload(client, payload)

def enviar_imagen(client, id_imagen):
    """Cambia la imagen del display usando los IDs de la tabla de la ESP32"""
    payload = {
        "cmd": "IMAGE",
        "id": id_imagen
    }
    enviar_payload(client, payload)

def enviar_texto(client, l1="", l2="", l3=""):
    """Envía líneas de texto personalizadas a la pantalla"""
    payload = {
        "cmd": "TEXT",
        "linea1": l1,
        "linea2": l2,
        "linea3": l3
    }
    enviar_payload(client, payload)

def enviar_imagen_remota(client, url, tipo="BWR"):
    """Envía la orden para que el ESP32 descargue el Blob desde Azure"""
    payload = {
        "cmd": "REMOTE_IMAGE",
        "url": url,
        "tipo": tipo
    }
    enviar_payload(client, payload)

# ============================================================
# RECEPCIÓN DE STATUS (ESCUCHA)
# ============================================================

def al_recibir_mensaje(client, userdata, msg):
    """Esta función se ejecuta sola cuando la ESP32 publica algo en el canal de status"""
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        
        print("\n" + "📢 " + "="*35)
        print("        NOTIFICACIÓN DESDE ESP32       ")
        print("="*37)
        print(f" Conectado a la Red:  {payload.get('wifi')}")
        print(f" Dirección IP Local:  {payload.get('ip')}")
        print(f" Estado Actual LED:   {payload.get('led')}")
        if 'display' in payload:
            print(f" Imagen Actual:       {payload['display'].get('current_image')}")
        if 'errores' in payload and payload['errores'].get('last_error') != "":
            print(f" Último Error:        {payload['errores'].get('last_error')}")
        print("="*37 + "\n")
    except Exception as e:
        print(f"Error al procesar el estado de la placa: {e}")

def al_conectar(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("\n Conectado exitosamente a HiveMQ Cloud.")
        # Nos suscribimos al canal de retorno
        client.subscribe(TOPIC_STATUS, qos=1) 
    else:
        print(f" Error de conexión. Código: {rc}")

def iniciar_cliente():
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()

    client.on_connect = al_conectar
    client.on_message = al_recibir_mensaje # Vinculamos el receptor
    
    client.username_pw_set(USER, PASS)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    
    print("Conectando al servidor MQTT...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start() 
    return client

# ============================================================
# FLUJO PRINCIPAL
# ============================================================

if __name__ == "__main__":
    cliente_mqtt = iniciar_cliente()
    time.sleep(2) 

    while True:
        print("\n" + "="*40)
        print("     CONTROLADOR DE ESP32 DISPLAY      ")
        print("="*40)
        print("1. Controlar Luz (ON / OFF / BLINK)")
        print("2. Enviar Imagen Registrada Local")
        print("3. Enviar Texto Personalizado")
        print("4. Enviar Imagen Remota (Azure Blob URL)")
        print("5. Salir")
        
        opc = input("\nSelecciona una opción: ").strip()

        if opc == "1":
            modo = input("Elige modo (ON / OFF / BLINK): ").strip().upper()
            if modo in ["ON", "OFF", "BLINK"]:
                controlar_luz(cliente_mqtt, modo)
            else:
                print("Modo no válido.")

        elif opc == "2":
            print("- Disponibles: imagen01, imagen02, imagen03, imagen04")
            img_id = input("Introduce el ID de la imagen: ").strip()
            enviar_imagen(cliente_mqtt, img_id)

        elif opc == "3":
            linea1 = input("Línea 1: ")
            linea2 = input("Línea 3: ")
            linea3 = input("Línea 3: ")
            enviar_texto(cliente_mqtt, linea1, linea2, linea3)

        elif opc == "4":
            print("\n--- DESCARGA DE BLOB AZURE ---")
            url_blob = input("Pega la URL del Blob (.bin): ").strip()
            if not url_blob:
                print("La URL no puede estar vacía.")
                continue
            
            tipo_img = input("Tipo de imagen (BWR / BW) [Default: BWR]: ").strip().upper()
            if tipo_img not in ["BW", "BWR"]:
                tipo_img = "BWR"
                
            enviar_imagen_remota(cliente_mqtt, url_blob, tipo_img)

        elif opc == "5":
            print("Cerrando controlador...")
            cliente_mqtt.loop_stop()
            cliente_mqtt.disconnect()
            break
        else:
            print("Opción inválida.")
        
        time.sleep(1)