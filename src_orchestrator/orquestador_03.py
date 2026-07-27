import os
import sys
import subprocess
import time

# Importamos tus módulos atómicos de Python
from empaquetador_dual import empaquetar_dual
from azure_blob_up import subir_a_azure
import controlador_esp32_t as mqtt_ctrl

def ejecutar_pipeline(ruta_o_url, nodo_destino=None, es_directo=False):
    print("\n" + "="*50)
    print("      ORQUESTADOR CORE: INICIO DE PIPELINE BWR")
    print("="*50)

    url_azure = ""

    if es_directo:
        # ==========================================================
        # MODO DIRECTO (Bypass a MQTT)
        # ==========================================================
        print("\n[MODO DIRECTO] Omitiendo procesamiento local.")
        print(f"Tomando URL cruda de origen: {ruta_o_url}")
        url_azure = ruta_o_url
        
    else:
        # ==========================================================
        # FLUJO NORMAL (Procesar -> Empaquetar -> Subir)
        # ==========================================================
        if not os.path.exists(ruta_o_url):
            print(f"[ERROR] No se encontró la imagen original: {ruta_o_url}")
            return False

        dir_name = os.path.dirname(ruta_o_url) or os.getcwd()
        base_name = os.path.splitext(os.path.basename(ruta_o_url))[0]

        ruta_observable = os.path.join(dir_name, f"{base_name}_obsv.png")
        ruta_binario = os.path.join(dir_name, f"{base_name}_full.bin")

        print("\n[PASO 1] Ejecutando Normalizador (Node.js)...")
        try:
            resultado_node = subprocess.run(
                ["node", "normalizador.js", ruta_o_url],
                check=True, text=True, capture_output=True
            )
            print(resultado_node.stdout)
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR FATAL] Falló el Normalizador. Código: {e.returncode}")
            return False

        print("\n[PASO 2] Ejecutando Empaquetador Binario...")
        try:
            empaquetar_dual(ruta_observable)
        except Exception as e:
            print(f"\n[ERROR FATAL] Falló el Empaquetador: {e}")
            return False

        print("\n[PASO 3] Ejecutando Uploader a Azure...")
        try:
            url_azure = subir_a_azure(ruta_binario)
            if not url_azure:
                print("\n[ERROR FATAL] Falló la subida a Azure (URL vacía).")
                return False
        except Exception as e:
            print(f"\n[ERROR FATAL] Excepción al contactar Azure: {e}")
            return False

    # ==========================================================
    # PASO 4: DESPACHO MQTT AL NODO
    # ==========================================================
    if nodo_destino:
        print(f"\n[PASO 4] Despachando URL vía MQTT a la Etiqueta '{nodo_destino}'...")
        try:
            mqtt_ctrl.TOPIC_CMD = f"inktronic/esp32/{nodo_destino}/cmd"
            
            cliente = mqtt_ctrl.iniciar_cliente()
            time.sleep(2) 
            
            mqtt_ctrl.enviar_imagen_remota(cliente, url_azure, "BWR")
            time.sleep(1) 
            
            cliente.loop_stop()
            cliente.disconnect()
            print(f"[OK] Orden MQTT despachada exitosamente al canal: {mqtt_ctrl.TOPIC_CMD}")
        except Exception as e:
            print(f"\n[ERROR] El proceso MQTT falló: {e}")

    print("\n" + "="*50)
    print("      PIPELINE COMPLETADO CON ÉXITO")
    print("="*50)
    print(f" URL Final: {url_azure}")
    print("========================================================\n")
    
    return url_azure


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso Normal : python orquestador.py <ruta_imagen_local> [<nodo>]")
        print("Uso Directo: python orquestador.py direct <nodo> <URL_Azure>\n")
    else:
        modo = sys.argv[1].lower()

        if modo == "direct":
            if len(sys.argv) < 4:
                print("[ERROR] Faltan parámetros para el modo directo.")
                print("Ejemplo: python orquestador.py direct 01 https://azure.../foto.bin")
            else:
                nodo = sys.argv[2]
                url = sys.argv[3]
                ejecutar_pipeline(ruta_o_url=url, nodo_destino=nodo, es_directo=True)
        else:
            # Flujo normal
            ruta = sys.argv[1]
            nodo = sys.argv[2] if len(sys.argv) > 2 else None
            ejecutar_pipeline(ruta_o_url=ruta, nodo_destino=nodo, es_directo=False)