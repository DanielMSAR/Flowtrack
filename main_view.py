# main_view.py

import customtkinter as ctk
from lotes_view import LotesView  # Importación de la vista que creamos
from chacras_view import ChacrasView
from loteagrario_view import LoteAgrarioView
from vehiculos_view import VehiculosView
from combustibles_view import CombustiblesView
from insumos_view import InsumosView
from movinsumos_view import MovInsumosView
from PIL import Image
import os

class MainView:
    def __init__(self, root, db_connection=None):  # Agregamos db_connection para pasarle el control a los módulos
        self.root = root
        self.db = db_connection  # Guardamos la referencia de la base de datos
        
        # Contenedor principal que ocupa toda la pantalla
        self.main_container = ctk.CTkFrame(self.root, fg_color="white")
        self.main_container.pack(fill="both", expand=True)

        # 1. BARRA INFERIOR DE ESTADO
        self.status_bar = ctk.CTkFrame(self.main_container, height=45, fg_color="#4d5433", corner_radius=0)
        self.status_bar.pack(side="bottom", fill="x")
        
        # Solo calculamos el saludo con la hora del sistema
        from datetime import datetime
        nombre_usuario = getattr(self.root, "current_user_name", "DANIEL").upper()
        texto_saludo = f"DG SOLUCIONES - BUENOS DIAS {nombre_usuario}" if datetime.now().hour < 12 else f"DG SOLUCIONES - BUENAS TARDES {nombre_usuario}"
        
        # Texto de la barra inferior
        self.status_label = ctk.CTkLabel(
            self.status_bar, 
            text=texto_saludo, 
            text_color="white", 
            font=("Arial", 14, "bold")
        )
        self.status_label.pack(side="left", padx=20, pady=10)

        # 2. PANEL LATERAL (MENU) - ¡Ajustado a 280 de ancho!
        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=230, fg_color="#d6e4f0", corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # 3. PANEL CENTRAL (CONTENIDO DINÁMICO)
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="white", corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Texto temporal en el centro
        self.welcome_label = ctk.CTkLabel(
            self.content_frame, 
            text="Área de Trabajo - FlowTrack", 
            text_color="gray", 
            font=("Arial", 24)
        )
        self.welcome_label.pack(pady=100)

        # Diccionario para controlar el estado abierto/cerrado de los acordeones
        self.menu_states = {
            "MOVIMIENTOS": False,
            "ABM": False,
            "SISTEMA": False
        }
        
        # Contenedores para los submenús
        self.submenus = {}

        # Construir los botones del menú
        self.crear_menus()
        self._reorganizar_orden_menu()

    def _cargar_icono(self, nombre_archivo):
        """Carga una imagen PNG nativa de 35x35 píxeles de forma segura"""
        ruta_iconos = os.path.join(os.path.dirname(__file__), "iconos")
        ruta_completa = os.path.join(ruta_iconos, nombre_archivo)
        
        if os.path.exists(ruta_completa):
            try:
                return ctk.CTkImage(light_image=Image.open(ruta_completa), size=(35, 35))
            except Exception as e:
                print(f"Error al cargar el icono {nombre_archivo}: {e}")
        return None

    def crear_menus(self):
        # --- SECCIÓN MOVIMIENTOS ---
        self.btn_movimientos = ctk.CTkButton(
            self.sidebar_frame, text="▶ MOVIMIENTOS", fg_color="#8cb04e", text_color="black",
            hover_color="#7ba23c", font=("Arial", 15, "bold"), anchor="w", corner_radius=0,
            height=45, command=lambda: self.toggle_menu("MOVIMIENTOS")
        )
        
        self.submenus["MOVIMIENTOS"] = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        
        opciones_mov = [
            {"texto": "Lotes", "icono": "lote.png"},
            {"texto": "Sistema Balanza", "icono": "balanza.png"},
            {"texto": "Mov. Combustibles", "icono": "combustible.png"},
            {"texto": "Mov. Insumos", "icono": "insumo.png"}
        ]
        
        for opc in opciones_mov:
            img_icono = self._cargar_icono(opc["icono"])
            texto_final = f"  {opc['texto']}" if img_icono else f"  • {opc['texto']}"
            
            btn = ctk.CTkButton(
                self.submenus["MOVIMIENTOS"], text=texto_final, image=img_icono,
                fg_color="transparent", text_color="black", hover_color="#b9d291", 
                anchor="w", font=("Arial", 16), height=42, command=lambda o=opc["texto"]: self.abrir_modulo(o)
            )
            btn.pack(fill="x", pady=3)

        # --- SECCIÓN ABM ---
        self.btn_abm = ctk.CTkButton(
            self.sidebar_frame, text="▶ ABM", fg_color="#8cb04e", text_color="black",
            hover_color="#7ba23c", font=("Arial", 15, "bold"), anchor="w", corner_radius=0,
            height=45, command=lambda: self.toggle_menu("ABM")
        )
        
        self.submenus["ABM"] = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        
        opciones_abm = [
            {"texto": "Productos", "icono": "producto.png"},
            {"texto": "Insumos", "icono": "insumo.png"},
            {"texto": "Combustibles", "icono": "combustible.png"},
            {"texto": "Clientes", "icono": "cliente.png"},
            {"texto": "Vehiculos", "icono": "vehiculo.png"},
            {"texto": "Parcelas", "icono": "chacra.png"},
            {"texto": "Chacras", "icono": "chacra.png"}
        ]
        
        for opc in opciones_abm:
            img_icono = self._cargar_icono(opc["icono"])
            texto_final = f"  {opc['texto']}" if img_icono else f"  • {opc['texto']}"
            
            btn = ctk.CTkButton(
                self.submenus["ABM"], text=texto_final, image=img_icono,
                fg_color="transparent", text_color="black", hover_color="#b9d291", 
                anchor="w", font=("Arial", 16), height=42, command=lambda o=opc["texto"]: self.abrir_modulo(o)
            )
            btn.pack(fill="x", pady=3)

        # --- SECCIÓN SISTEMA ---
        self.btn_sistema = ctk.CTkButton(
            self.sidebar_frame, text="▶ SISTEMA", fg_color="#8cb04e", text_color="black",
            hover_color="#7ba23c", font=("Arial", 15, "bold"), anchor="w", corner_radius=0,
            height=45, command=lambda: self.toggle_menu("SISTEMA")
        )
        
        self.submenus["SISTEMA"] = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        
        opciones_sis = [
            {"texto": "Actualizar", "icono": "actualizar.png"},
            {"texto": "Usuarios", "icono": "usuario.png"}
        ]
        
        for opc in opciones_sis:
            img_icono = self._cargar_icono(opc["icono"])
            texto_final = f"  {opc['texto']}" if img_icono else f"  • {opc['texto']}"
            
            btn = ctk.CTkButton(
                self.submenus["SISTEMA"], text=texto_final, image=img_icono,
                fg_color="transparent", text_color="black", hover_color="#b9d291", 
                anchor="w", font=("Arial", 16), height=42, command=lambda o=opc["texto"]: self.abrir_modulo(o)
            )
            btn.pack(fill="x", pady=3)
            
        # Botón Salir independiente
        img_salir = self._cargar_icono("salir.png")
        txt_salir = "  Salir" if img_salir else "  • Salir"
        btn_salir = ctk.CTkButton(
            self.submenus["SISTEMA"], text=txt_salir, image=img_salir,
            fg_color="transparent", text_color="black", hover_color="#b9d291", 
            anchor="w", font=("Arial", 16), height=42, command=self.root.quit
        )
        btn_salir.pack(fill="x", pady=3)

    def toggle_menu(self, menu_name):
        """Maneja el estado abierto/cerrado de los acordeones cambiando las flechas"""
        self.menu_states[menu_name] = not self.menu_states[menu_name]
        
        if self.menu_states["MOVIMIENTOS"]: self.btn_movimientos.configure(text="▼ MOVIMIENTOS")
        else: self.btn_movimientos.configure(text="▶ MOVIMIENTOS")
            
        if self.menu_states["ABM"]: self.btn_abm.configure(text="▼ ABM")
        else: self.btn_abm.configure(text="▶ ABM")
            
        if self.menu_states["SISTEMA"]: self.btn_sistema.configure(text="▼ SISTEMA")
        else: self.btn_sistema.configure(text="▶ SISTEMA")
            
        self._reorganizar_orden_menu()

    def _reorganizar_orden_menu(self):
        """Remueve temporalmente todo y vuelve a empaquetar respetando la posición real del acordeón"""
        self.btn_movimientos.pack_forget()
        self.submenus["MOVIMIENTOS"].pack_forget()
        self.btn_abm.pack_forget()
        self.submenus["ABM"].pack_forget()
        self.btn_sistema.pack_forget()
        self.submenus["SISTEMA"].pack_forget()

        # Re-empaquetado secuencial con espaciados cómodos
        self.btn_movimientos.pack(fill="x", pady=(10, 0))
        if self.menu_states["MOVIMIENTOS"]:
            self.submenus["MOVIMIENTOS"].pack(fill="x", padx=10, pady=5)
        
        self.btn_abm.pack(fill="x", pady=(10, 0))
        if self.menu_states["ABM"]:
            self.submenus["ABM"].pack(fill="x", padx=10, pady=5)
        
        self.btn_sistema.pack(fill="x", pady=(10, 0))
        if self.menu_states["SISTEMA"]:
            self.submenus["SISTEMA"].pack(fill="x", padx=10, pady=5)

    def abrir_modulo(self, nombre_modulo):
        """Limpia el panel de contenido central y carga dinámicamente la vista seleccionada"""
        print(f"Abriendo el módulo: {nombre_modulo}")
        
        # Limpiamos todos los elementos viejos cargados en el panel derecho
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # CONTROL DE ENRUTAMIENTO DE MÓDULOS ACTIVOS
        if nombre_modulo == "Lotes":
            # Instanciamos la vista pasándole el contenedor central y la DB
            self.vista_lotes = LotesView(self.content_frame, self.db)
            
        elif nombre_modulo == "Chacras":
            # Agregamos el ruteo seguro para inyectar el ABM de Chacras en el centro
            self.vista_chacras = ChacrasView(self.content_frame, self.db)
            
        elif nombre_modulo == "Parcelas":
            # NUEVO: Ruteo dinámico para levantar el ABM de LoteAgrario
            self.vista_lote_agrario = LoteAgrarioView(self.content_frame, self.db)
        elif nombre_modulo == "Vehiculos":
            # NUEVO: Ruteo seguro para inyectar el ABM de Vehículos con ID de usuario dinámico
            user_id = getattr(self.root, "current_user_id", 1) # Captura el ID desde app.py si existe, sino usa 1
            self.vista_vehiculos = VehiculosView(self.content_frame, self.db, current_user_id=user_id)    
        elif nombre_modulo == "Combustibles":
            # NUEVO: Ruteo dinámico para levantar la gestión de Combustibles y Precios
            user_id = getattr(self.root, "current_user_id", 1)
            self.vista_combustibles = CombustiblesView(self.content_frame, self.db, current_user_id=user_id)
        elif nombre_modulo == "Insumos":
            self.vista_insumos = InsumosView(self.content_frame, self.db)  
        elif nombre_modulo == "Mov. Insumos":
            self.vista_mov_insumos = MovInsumosView(self.content_frame, self.db)
        elif nombre_modulo == "Mov. Combustibles":
            # NUEVO: Cuando hagamos la vista de cargas, apuntará aquí sin pisar el ABM
            # Por ahora, como todavía no lo creamos, caerá de forma segura en el cartel "En desarrollo..."
            user_id = getattr(self.root, "current_user_id", 1)
            # self.vista_mov_combustibles = MovCombustiblesView(self.content_frame, self.db, current_user_id=user_id)
            # Dejamos temporalmente el aviso para que no falle al hacer clic:
            self.welcome_label = ctk.CTkLabel(
                self.content_frame, 
                text="Módulo de Registro de Entradas y Salidas de Combustible en desarrollo...", 
                font=("Arial", 16, "bold"), 
                text_color="gray"
            )
            self.welcome_label.pack(expand=True)
        else:
            # Mensaje temporal para los módulos que aún no creamos
            self.welcome_label = ctk.CTkLabel(
                self.content_frame, 
                text=f"Módulo Activo: {nombre_modulo.upper()}\n(Próximamente en desarrollo)", 
                text_color="gray", 
                font=("Arial", 24)
            )
            self.welcome_label.pack(pady=100)