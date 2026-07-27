import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

# Le decimos a Python que busque el .env un nivel más arriba (en la raíz)
ruta_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(ruta_env)

AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

def subir_a_azure(bin_file_path):
    bin_file_path = bin_file_path.strip('"\'')

    if not os.path.exists(bin_file_path):
        print(f"\n[ERROR] No se encuentra el archivo local: '{bin_file_path}'")
        return None

    if not AZURE_CONNECTION_STRING or not CONTAINER_NAME:
        print("\n[ERROR] Falta configurar AZURE_STORAGE_CONNECTION_STRING o AZURE_CONTAINER_NAME en el archivo .env")
        return None

    # Usar el nombre original del archivo para el Blob en la nube
    blob_name = os.path.basename(bin_file_path)

    try:
        print(f"\n[1/2] Conectando a Azure Blob Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)

        print(f"[2/2] Subiendo '{blob_name}' al contenedor '{CONTAINER_NAME}'...")
        with open(bin_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # La propiedad .url nos da la dirección web completa del archivo
        url_de_acceso = blob_client.url

        print("\n========================================================")
        print("   ¡ARCHIVO SUBIDO A AZURE EXITOSAMENTE!")
        print("========================================================")
        print(f" Blob de destino:  {blob_name}")
        print(f" Contenedor:        {CONTAINER_NAME}")
        print(f" URL de descarga:   {url_de_acceso}")
        print("========================================================\n")

        return url_de_acceso

    except AzureError as ae:
        print(f"\n[ERROR AZURE] Ocurrió una falla de red o autenticación: {ae}")
        return None
    except Exception as e:
        print(f"\n[ERROR INESPERADO] {e}")
        return None

if __name__ == "__main__":
    print("========================================================")
    print("     CARGADOR ATÓMICO A AZURE BLOB STORAGE (.ENV)      ")
    print("========================================================")
    ruta = input("\nPegá la ruta completa de tu archivo .bin y Enter: ")
    subir_a_azure(ruta)
    # input("Presioná Enter para salir...")