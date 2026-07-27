# Usar una imagen oficial de Python liviana
FROM python:3.11-slim

# Establecer la carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiar todo el contenido de la carpeta actual al contenedor
COPY . /app/

# Instalar dependencias (si existe un archivo requirements.txt, lo instala; si no, sigue de largo)
RUN pip install --no-cache-dir -r src_orchestrator/requirements.txt

# Ejecutar el código Python
# OJO ACÁ: Cambiá 'main.py' por el nombre real de tu archivo principal
CMD ["python", "src_orchestrator/orquestador_03.py"]
