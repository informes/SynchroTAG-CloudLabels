import sys
import os
import re
from PIL import Image

# Parámetros estrictos de tu arquitectura
TAMANO_CANAL = 15000
TAMANO_TOTAL_ESPERADO = 30000

def generar_bin_azure(image_path):
    image_path = image_path.strip('"\'')
    if not os.path.exists(image_path):
        print(f"\n[ERROR] Archivo no encontrado: {image_path}\n")
        return

    dir_name = os.path.dirname(image_path) or os.getcwd()
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]

    # Limpiar sufijos (_obsv, _BW) para el archivo final
    clean_base = re.sub(r'(_obsv|_BW|_BWR)', '', base_name, flags=re.IGNORECASE)
    output_bin_path = os.path.join(dir_name, f"{clean_base}_full.bin")

    print("\n========================================================")
    print("   EMPAQUETADOR ATÓMICO DIRECTO A BINARIO (AZURE)       ")
    print("========================================================")
    print(f"[*] Origen:  {filename}")
    
    img = Image.open(image_path).convert('RGB')
    width, height = img.size

    # Validación rápida de geometría (400x300 = 15000 bytes por canal)
    if (width * height // 8) != TAMANO_CANAL:
        print(f"[ERROR FATAL] La imagen mide {width}x{height}. Se requiere 400x300.")
        return

    # Usamos bytearray nativos (mucho más rápido y directo que el texto .c)
    black_bytes = bytearray()
    red_bytes = bytearray()

    print("[*] Empaquetando píxeles purificados...")
    for y in range(height):
        byte_mono, byte_red, bit_count = 0, 0, 0
        
        for x in range(width):
            r, g, b = img.getpixel((x, y))

            # Lectura del observable (colores puros)
            if r > 128 and g < 128 and b < 128:   # Rojo
                mono_bit, red_bit = 0, 1
            elif r < 128 and g < 128 and b < 128: # Negro
                mono_bit, red_bit = 1, 0
            else:                                 # Blanco
                mono_bit, red_bit = 0, 0

            byte_mono = (byte_mono << 1) | mono_bit
            byte_red = (byte_red << 1) | red_bit
            bit_count += 1

            if bit_count == 8:
                black_bytes.append(byte_mono)
                red_bytes.append(byte_red)
                byte_mono, byte_red, bit_count = 0, 0, 0

    print("[*] Validando geometría de los buffers...")
    if len(black_bytes) == TAMANO_CANAL and len(red_bytes) == TAMANO_CANAL:
        payload_full = black_bytes + red_bytes
        
        with open(output_bin_path, "wb") as f_bin:
            f_bin.write(payload_full)

        print("\n========================================================")
        print("   ¡CONVERSIÓN A BINARIO COMPLETA Y EXITOSA!")
        print("========================================================")
        print(f" Archivo listo: {output_bin_path}")
        print(f" Tamaño total:  {len(payload_full)} bytes (30.000 B confirmados)")
        print(" Destino:       Subir directamente a Azure Blob Storage")
        print("========================================================\n")
    else:
        print("\n[ERROR DE GEOMETRÍA] Los canales no miden 15.000 bytes cada uno.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso: python empaquetador_azure.py <ruta_imagen_observable_obsv.png>\n")
    else:
        generar_bin_azure(sys.argv[1])