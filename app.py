# app.py
import bcrypt
import customtkinter as ctk
import configparser
import os
from database import Database
from login_view import LoginView
from main_view import MainView

class FlowTrackApp:
    def __init__(self):
        # Configuración general de CustomTkinter
        ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

        self.root = ctk.CTk()
        self.root.title("FlowTrack")
        
        # 1. ESTABLECER ICONO PERSONALIZADO NATIVO (.ICO)
        self._set_app_icon()
        
        # 2. MAXIMIZADO SEGURO
        self.root.update_idletasks()
        self.root.after(0, lambda: self.root.wm_state('zoomed'))

        self.db = Database()
        self.current_user_id = None 
        self.login_view = None
        self.main_view = None

        self.show_login()

    def _set_app_icon(self):
        """Aplica el archivo .ico de forma nativa para obligar a Windows a cambiar el icono de la barra"""
        ruta_ico = os.path.join(os.path.dirname(__file__), "icono_app.ico")
        
        if os.path.exists(ruta_ico):
            try:
                # El método iconbitmap es el estándar directo y más compatible con Windows para archivos .ico
                self.root.iconbitmap(ruta_ico)
                print("Icono nativo .ico cargado con éxito.")
            except Exception as e:
                print(f"Error al aplicar iconbitmap: {e}")
        else:
            print("No se encontró el archivo 'icono_app.ico' en la raíz del proyecto.")

    def show_login(self):
        if self.login_view:
            self.login_view.destroy()
        self.login_view = LoginView(self.root, self.on_login_success)

    def guardar_ultimo_usuario(self, username):
        """Guarda el nombre del último usuario logueado en config.ini"""
        config = configparser.ConfigParser()
        
        if os.path.exists('config.ini'):
            config.read('config.ini', encoding='utf-8')
        
        if not config.has_section('Parametros'):
            config.add_section('Parametros')
            
        config.set('Parametros', 'LU', f'"{username}"')
        
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        print("Usuario guardado en config.ini")

    def on_login_success(self, username, password):
        # Tu tabla real 'users' y campo de ID 'id'
        query = "SELECT id, password FROM users WHERE usuario = %s"
        params = (username,)
        result = self.db.execute_query(query, params)

        if result and len(result) > 0:
            user_id = result[0][0]
            password_hasheada_db = result[0][1]

            # Verificamos la contraseña (Cambiá por texto plano si tus contraseñas aún no usan hash)
            if bcrypt.checkpw(password.encode('utf-8'), password_hasheada_db.encode('utf-8')):
                self.current_user_id = user_id
                print(f"Login exitoso para el usuario ID: {self.current_user_id}")
                
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
        
        # AJUSTE: Le pasamos la conexión self.db a la vista principal
        self.main_view = MainView(self.root, self.db)
        print("Ventana Principal Cargada.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FlowTrackApp()
    app.run()