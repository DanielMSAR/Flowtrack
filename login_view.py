# login_view.py
import customtkinter as ctk
import configparser
import os

class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        # Centramos un poco más el contenedor en la pantalla gigante
        self.pack(pady=150, padx=60, fill="none", expand=True)

        # Título principal más grande y robusto
        self.label = ctk.CTkLabel(self, text="Iniciar Sesión", font=("Arial", 28, "bold"))
        self.label.pack(pady=(30, 20), padx=40)

        # Intentamos leer el último usuario guardado
        ultimo_usuario = self._obtener_ultimo_usuario()

        # Input de Usuario - Letra tamaño 16 y caja más ancha y alta
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

        # Input de Contraseña - Letra tamaño 16 y caja más ancha y alta
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

        # Botón de Login - Texto cambiado a "ACCEDER", más grande y llamativo
        self.login_button = ctk.CTkButton(
            self, 
            text="ACCEDER", 
            width=350, 
            height=50, 
            font=("Arial", 16, "bold"),
            command=self._login
        )
        self.login_button.pack(pady=(20, 30), padx=40)

        # Enfoque del cursor según corresponda
        if ultimo_usuario:
            self.password_entry.focus()
        else:
            self.user_entry.focus()

        self.on_login_success = on_login_success

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
                print(f"Error al leer config.ini: {e}")
        return ""

    def _login(self):
        username = self.user_entry.get()
        password = self.password_entry.get()
        self.on_login_success(username, password)