# login_view.py
import customtkinter as ctk
import configparser
import os

class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success, last_user=""):
        super().__init__(master)
        # Centramos un poco más el contenedor en la pantalla gigante
        self.pack(pady=150, padx=60, fill="none", expand=True)

        # Título principal más grande y robusto
        self.label = ctk.CTkLabel(self, text="Iniciar Sesión", font=("Arial", 28, "bold"))
        self.label.pack(pady=(30, 20), padx=40)

        # Usamos el usuario que nos pasa app.py, o el de respaldo del config local
        ultimo_usuario = last_user if last_user else self._obtener_ultimo_usuario()

        # Input de Usuario
        self.user_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Usuario", 
            width=350, 
            height=45, 
            font=("Arial", 16)
        )
        self.user_entry.pack(pady=15, padx=40)
        
        if ultimo_usuario:
            self.user_entry.insert(0, ultimo_usuario)

        # Input de Contraseña
        self.password_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Contraseña", 
            show="*", 
            width=350, 
            height=45, 
            font=("Arial", 16)
        )
        self.password_entry.pack(pady=15, padx=40)
        
        # Vincular la tecla "Enter" al cuadro de contraseña
        self.password_entry.bind("<Return>", lambda event: self._login())

        # Botón de Login
        self.login_button = ctk.CTkButton(
            self, 
            text="ACCEDER", 
            width=350, 
            height=50, 
            font=("Arial", 16, "bold"),
            command=self._login
        )
        self.login_button.pack(pady=(20, 30), padx=40)
        # --- NUEVO: LABEL PARA MOSTRAR ERRORES DE LOGUEO ---
        self.lbl_error = ctk.CTkLabel(
            self, 
            text="", 
            font=("Arial", 14, "bold"), 
            text_color="#bc4749" # Usamos el rojo ladrillo del sistema para alertas
        )
        self.lbl_error.pack(pady=(0, 20), padx=40)

        # Enfoque del cursor según corresponda
        if ultimo_usuario:
            self.password_entry.focus()
        else:
            self.user_entry.focus()

        # Guardamos el callback que viene de app.py
        self.on_login_success_callback = on_login_success

    def _login(self):
        """Extrae los datos ingresados y ejecuta la validación de app.py"""
        username = self.user_entry.get().strip()
        password = self.password_entry.get()
        
        if username and password:
            # Ejecuta la función on_login_success pasándole los datos
            self.on_login_success_callback(username, password)

    def _obtener_ultimo_usuario(self):
        """Lee el config.ini y devuelve el usuario si existe"""
        if os.path.exists('config.ini'):
            try:
                config = configparser.ConfigParser()
                config.read('config.ini', encoding='utf-8')
                if config.has_option('Parametros', 'LU'):
                    usuario_raw = config.get('Parametros', 'LU')
                    return usuario_raw.replace('"', '')
            except Exception as e:
                print(f"Error al leer último usuario en login_view: {e}")
        return ""
    def mostrar_error(self, mensaje="Contraseña o usuario incorrectos"):
        """Muestra el texto de error en rojo y limpia el campo de contraseña"""
        self.lbl_error.configure(text=mensaje)
        self.password_entry.delete(0, "end")
        self.password_entry.focus()