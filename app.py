# app.py
import bcrypt
import customtkinter as ctk
import configparser
import os
import sys
import urllib.request
import json
from database import Database
from login_view import LoginView
from main_view import MainView

# =====================================================================
# CONFIGURACIÓN DE ACTUALIZACIÓN AUTOMÁTICA (GITHUB PÚBLICO)
# =====================================================================
VERSION_LOCAL = "1.0.0"  # <-- Cambiá esto a mano en tu código cada vez que lances una versión
USER_GIT = "DanielMSAR"      # <-- Colocá tu usuario real de GitHub
REPO_GIT = "Flowtrack"  # <-- Colocá el nombre exacto de tu repo

# Lista exacta de los archivos .py de tu sistema que querés que se actualicen
ARCHIVOS_SISTEMA = [
    "app.py",
    "main_view.py",
    "login_view.py",
    "database.py",
    "insumos_view.py",
    "movinsumos_view.py",
    "lotes_view.py",
    "chacras_view.py",
    "loteagrario_view.py",
    "vehiculos_view.py",
    "combustibles_view.py"
]

def verificar_actualizaciones_al_inicio():
    """Consulta GitHub y actualiza los archivos .py si hay una versión nueva"""
    # Buscamos el contenido del archivo version.txt en la rama main de tu GitHub
    url_version_git = f"https://raw.githubusercontent.com/{USER_GIT}/{REPO_GIT}/main/version.txt"
    
    try:
        # Petición rápida para leer el texto de la versión remota
        req = urllib.request.Request(url_version_git, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            version_remota = response.read().decode('utf-8').strip()
        
        # Si la versión en Git es distinta a la local, ofrecemos actualizar
        if version_remota != VERSION_LOCAL:
            from tkinter import messagebox
            root_temporal = ctk.CTk()
            root_temporal.withdraw() # Ocultamos una ventana vacía de Tkinter para el mensaje
            
            confirmar = messagebox.askyesno(
                "Actualización de FlowTrack", 
                f"Se detectó una nueva actualización disponible (Versión {version_remota}).\n"
                f"Tu versión actual es la {VERSION_LOCAL}.\n\n"
                "¿Deseas descargar e instalar las mejoras ahora mismo?"
            )
            
            if confirmar:
                print("Iniciando descarga de actualizaciones...")
                # Recorremos y descargamos únicamente los archivos de código fuente
                for archivo in ARCHIVOS_SISTEMA:
                    url_archivo_git = f"https://raw.githubusercontent.com/{USER_GIT}/{REPO_GIT}/main/{archivo}"
                    try:
                        urllib.request.urlretrieve(url_archivo_git, archivo)
                        print(f"-> {archivo} actualizado con éxito.")
                    except Exception as e_archivo:
                        print(f"Error al descargar {archivo}: {e_archivo}")
                
                messagebox.showinfo("Éxito", "El sistema se actualizó correctamente. Se reiniciará la aplicación.")
                root_temporal.destroy()
                
                # Reiniciamos el script en caliente con los nuevos archivos .py cargados
                os.execv(sys.executable, ['python'] + sys.argv)
            else:
                root_temporal.destroy() # Si dice que no, destruimos el root temporal y sigue el inicio normal
                
    except Exception as e:
        # Si el cliente no tiene internet o falla Git, imprime el error en consola y arranca igual
        print(f"No se pudo verificar actualizaciones (saltando paso): {e}")

# Ejecutamos el control de actualización antes de levantar cualquier interfaz
verificar_actualizaciones_al_inicio()
# =====================================================================


class FlowTrackApp:
    def __init__(self):
        ctk.set_appearance_mode("System")  
        ctk.set_default_color_theme("green")  

        self.root = ctk.CTk()
        self.root.title("FlowTrack")
        
        self._set_app_icon()
        
        self.root.update_idletasks()
        self.root.after(0, lambda: self.root.wm_state('zoomed'))

        self.db = Database()
        self.current_user_id = None 
        self.login_view = None
        self.main_view = None

        self.show_login()

    def _set_app_icon(self):
        ruta_ico = os.path.join(os.path.dirname(__file__), "icono_app.ico")
        if os.path.exists(ruta_ico):
            try:
                self.root.iconbitmap(ruta_ico)
            except Exception as e:
                print(f"Error al aplicar iconbitmap: {e}")

    def show_login(self):
        if self.login_view:
            self.login_view.destroy()
        self.login_view = LoginView(self.root, self.on_login_success)

    def guardar_ultimo_usuario(self, username):
        config = configparser.ConfigParser()
        if os.path.exists('config.ini'):
            config.read('config.ini', encoding='utf-8')
        if not config.has_section('Parametros'):
            config.add_section('Parametros')
            
        config.set('Parametros', 'LU', f'"{username}"')
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def on_login_success(self, username, password):
        query = "SELECT id, password FROM users WHERE usuario = %s"
        params = (username,)
        result = self.db.execute_query(query, params)

        if result and len(result) > 0:
            user_id = result[0][0]
            password_hasheada_db = result[0][1]

            if bcrypt.checkpw(password.encode('utf-8'), password_hasheada_db.encode('utf-8')):
                self.current_user_id = user_id
                
                # Seteamos los datos en el root antes de instanciar MainView
                self.root.current_user_id = user_id
                self.root.current_user_name = username
                
                self.guardar_ultimo_usuario(username)
                self.show_main_window()
                return
            else:
                print("Login fallido: Contraseña incorrecta.")
        else:
            print("Login fallido: Usuario no encontrado.")

    def show_main_window(self):
        if self.login_view:
            self.login_view.destroy()
            self.login_view = None
        
        self.main_view = MainView(self.root, self.db)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FlowTrackApp()
    app.run()