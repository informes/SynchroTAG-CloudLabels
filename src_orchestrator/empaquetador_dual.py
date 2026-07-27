import sys
import os
import re
from PIL import Image

TAMANO_CANAL = 15000

def empaquetar_dual(image_path):
    image_path = image_path.strip('"\'')
    if not os.path.exists(image_path):
        print(f"\n[ERROR] Archivo no encontrado: {image_path}\n")
        return

    dir_name = os.path.dirname(image_path) or os.getcwd()
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]

    # Limpiamos el nombre para los archivos de salida
    clean_base = re.sub(r'(_obsv|_BW|_BWR)', '', base_name, flags=re.IGNORECASE)
    var_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_base)
    
    output_c_path = os.path.join(dir_name, f"{clean_base}.c")
    output_bin_path = os.path.join(dir_name, f"{clean_base}_full.bin")

    img = Image.open(image_path).convert('RGB')
    width, height = img.size

    print(f"\n[*] Empaquetando píxeles desde: {filename}")

    filas_mono, filas_red = [], []
    black_bytes, red_bytes = bytearray(), bytearray()

    for y in range(height):
        byte_mono, byte_red, bit_count = 0, 0, 0
        fila_m, fila_r = [], []
        
        for x in range(width):
            r, g, b = img.getpixel((x, y))

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
                fila_m.append(byte_mono)
                fila_r.append(byte_red)
                black_bytes.append(byte_mono)
                red_bytes.append(byte_red)
                byte_mono, byte_red, bit_count = 0, 0, 0

        filas_mono.append(fila_m)
        filas_red.append(fila_r)

    # 1. ESCRITURA DEL ARCHIVO .C (Para tu paz mental y debug local)
    with open(output_c_path, 'w') as f:
        f.write(f"// Imagen auto-generada desde observable ({width}x{height})\n")
        f.write("// Formato Pervasive preservado para debug\n\n")
        
        f.write(f"unsigned char const {var_name}_blackBuffer[] =\n{{\n")
        for i, b in enumerate(black_bytes):
            f.write(f"0x{b:02x},")
            if (i + 1) % 10 == 0: f.write("\n")
        f.write("};\n\n")
        
        f.write(f"unsigned char const {var_name}_redBuffer[] =\n{{\n")
        for i, b in enumerate(red_bytes):
            f.write(f"0x{b:02x},")
            if (i + 1) % 10 == 0: f.write("\n")
        f.write("};\n")

    # 2. ESCRITURA DEL ARCHIVO .BIN (Para tu pipeline de Azure)
    if len(black_bytes) == TAMANO_CANAL and len(red_bytes) == TAMANO_CANAL:
        with open(output_bin_path, "wb") as f_bin:
            f_bin.write(black_bytes + red_bytes)
        
        print("\n[OK] GENERACIÓN DUAL COMPLETADA")
        print(f" -> Creado para Debug: {output_c_path}")
        print(f" -> Creado para Azure: {output_bin_path} ({len(black_bytes + red_bytes)} bytes)")
    else:
        print("\n[ERROR DE GEOMETRÍA] Los canales no miden 15.000 bytes cada uno.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso: python empaquetador_dual.py <ruta_imagen_obsv.png>\n")
    else:
        empaquetar_dual(sys.argv[1])