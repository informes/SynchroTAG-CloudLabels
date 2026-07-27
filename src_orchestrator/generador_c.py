import sys
import os
import re
from PIL import Image

def generar_c(image_path):
    if not os.path.exists(image_path):
        print(f"\n[ERROR] Archivo no encontrado: {image_path}\n")
        return

    dir_name = os.path.dirname(image_path) or os.getcwd()
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]

    # Limpiar sufijos feos para que la variable en C quede prolija
    clean_base = re.sub(r'(_obsv|_BW|_BWR)', '', base_name, flags=re.IGNORECASE)
    var_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_base)
    output_c_path = os.path.join(dir_name, f"{clean_base}.c")

    print("\n=== EMPAQUETADOR BINARIO C ===")
    print(f"[*] Leyendo:      {image_path}")
    print(f"[*] Exportando:   {output_c_path}")
    print(f"[*] Variable C:   {var_name}_blackBuffer / {var_name}_redBuffer")

    img = Image.open(image_path).convert('RGB')
    width, height = img.size

    filas_mono = []
    filas_red = []

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
                byte_mono, byte_red, bit_count = 0, 0, 0

        filas_mono.append(fila_m)
        filas_red.append(fila_r)

    with open(output_c_path, 'w') as f:
        f.write(f"// Auto-generado desde {filename} ({width}x{height} px)\n\n")
        
        # --- blackBuffer ---
        f.write(f"unsigned char const {var_name}_blackBuffer[] =\n{{\n")
        todos_mono = [b for fila in filas_mono for b in fila]
        for i, b in enumerate(todos_mono):
            f.write(f"0x{b:02x},")
            if (i + 1) % 10 == 0:
                f.write("\n")
        if len(todos_mono) % 10 != 0:
            f.write("\n")
        f.write("};\n\n")
        
        # --- redBuffer ---
        f.write(f"unsigned char const {var_name}_redBuffer[] =\n{{\n")
        todos_red = [b for fila in filas_red for b in fila]
        for i, b in enumerate(todos_red):
            f.write(f"0x{b:02x},")
            if (i + 1) % 10 == 0:
                f.write("\n")
        if len(todos_red) % 10 != 0:
            f.write("\n")
        f.write("};\n")

    print(f"[OK] Archivo C creado con éxito en: {output_c_path}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso: python generador_c.py <ruta_imagen_observable>\n")
    else:
        generar_c(sys.argv[1])