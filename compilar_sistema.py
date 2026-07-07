# compilar_sistema.py
import os
import sys
import subprocess
import shutil

def compilar_y_limpiar():
    print("1. Compilando archivos de Python a Bytecode...")
    # Ejecuta el comando de compilación nativo en el directorio actual
    subprocess.run([sys.executable, "-m", "compileall", "."], check=True)
    
    print("\n2. Procesando y limpiando archivos .pyc...")
    archivos_procesados = 0

    # Recorremos todas las carpetas del proyecto buscando los __pycache__
    for root, dirs, files in os.walk("."):
        if "__pycache__" in root:
            # Directorio padre donde se deben mover los archivos corregidos
            carpeta_superior = os.path.dirname(root)
            
            for file in files:
                if file.endswith(".pyc") and ".cpython-" in file:
                    ruta_original = os.path.join(root, file)
                    
                    # Quitamos la marca de cpython (Ej: app.cpython-311.pyc -> app.pyc)
                    nombre_base = file.split(".cpython-")[0]
                    nuevo_nombre = f"{nombre_base}.pyc"
                    ruta_destino = os.path.join(carpeta_superior, nuevo_nombre)
                    
                    # Copiamos el archivo a la carpeta de arriba con el nombre limpio
                    shutil.copy2(ruta_original, ruta_destino)
                    print(f" -> Procesado con éxito: {nuevo_nombre}")
                    archivos_procesados += 1

    print(f"\n¡Todo listo! Se procesaron {archivos_procesados} archivos binarios.")
    print("Ya podés llevarte los archivos .pyc limpios en tu pendrive.")

if __name__ == "__main__":
    compilar_y_limpiar()