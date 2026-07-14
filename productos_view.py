# productos_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class ProductosView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Captura de usuario de forma segura
        self.current_user_id = None
        if hasattr(master, "root"):
            self.current_user_id = getattr(master.root, "current_user_id", None)
        elif hasattr(master, "current_user_id"):
            self.current_user_id = getattr(master, "current_user_id", None)
        else:
            try:
                self.current_user_id = getattr(master.winfo_toplevel(), "current_user_id", None)
            except:
                self.current_user_id = 1  # ID de respaldo por defecto

        self.id_seleccionado = None  # Almacena el ID cuando editamos

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="ADMINISTRACIÓN DE PRODUCTOS", font=("Arial", 20, "bold"), text_color="black")
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- CONTENEDOR PRINCIPAL PRINCIPAL (2 COLUMNAS) ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.main_container.grid_columnconfigure(0, weight=4)  # Formulario (más angosto)
        self.main_container.grid_columnconfigure(1, weight=6)  # Tabla (más ancho)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Inicializar paneles
        self._armar_formulario()
        self._armar_tabla_y_busqueda()
        
        # Cargar datos iniciales
        self._cargar_productos_db()

    # =================================================================
    # PANEL IZQUIERDO: FORMULARIO DE CARGA / EDICIÓN
    # =================================================================
    def _armar_formulario(self):
        self.frame_form = ctk.CTkFrame(self.main_container, fg_color="#f8f9fa", corner_radius=8)
        self.frame_form.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_form, text="Datos del Producto", font=("Arial", 14, "bold"), text_color="black").pack(pady=15, padx=15, anchor="w")

        # Campo: Nombre del Producto
        ctk.CTkLabel(self.frame_form, text="Nombre del Producto *", text_color="black", font=("Arial", 12, "bold")).pack(padx=15, anchor="w")
        self.ent_producto = ctk.CTkEntry(self.frame_form, width=280, placeholder_text="Ej: Yerba Mate Canchada")
        self.ent_producto.pack(padx=15, pady=(2, 20))

        # Indicador de estado visual (solo lectura informativa)
        self.lbl_estado_actual = ctk.CTkLabel(self.frame_form, text="Estado: Nuevo Registro", font=("Arial", 11, "italic"), text_color="gray")
        self.lbl_estado_actual.pack(padx=15, anchor="w", pady=(0, 20))

        # --- BOTONERA DE ACCIONES ---
        self.btn_guardar = ctk.CTkButton(self.frame_form, text="GUARDAR PRODUCTO", fg_color="#8cb04e", hover_color="#73943c", text_color="black", font=("Arial", 12, "bold"), height=35, command=self._guardar_producto)
        self.btn_guardar.pack(fill="x", padx=15, pady=5)

        self.btn_cambiar_estado = ctk.CTkButton(self.frame_form, text="DAR DE BAJA", fg_color="#4a5568", hover_color="#2d3748", text_color="white", font=("Arial", 11, "bold"), height=30, command=self._alternar_estado_producto, state="disabled")
        self.btn_cambiar_estado.pack(fill="x", padx=15, pady=5)

        self.btn_limpiar = ctk.CTkButton(self.frame_form, text="LIMPIAR / NUEVO", fg_color="#e2e8f0", hover_color="#cbd5e1", text_color="black", font=("Arial", 11), height=30, command=self._limpiar_formulario)
        self.btn_limpiar.pack(fill="x", padx=15, pady=15)

    # =================================================================
    # PANEL DERECHO: BUSCADOR Y TABLA DE REGISTROS
    # =================================================================
    def _armar_tabla_y_busqueda(self):
        frame_derecho = ctk.CTkFrame(self.main_container, fg_color="white")
        frame_derecho.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")

        # Barra Superior de Búsqueda
        frame_busqueda = ctk.CTkFrame(frame_derecho, fg_color="transparent")
        frame_busqueda.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(frame_busqueda, text="🔍 Buscar:", text_color="black", font=("Arial", 12, "bold")).pack(side="left", padx=(0, 5))
        self.ent_buscar = ctk.CTkEntry(frame_busqueda, placeholder_text="Escriba el nombre del producto...", width=250)
        self.ent_buscar.pack(side="left", fill="x", expand=True)
        self.ent_buscar.bind("<KeyRelease>", self._filtrar_productos)

        # Grilla de Datos (Treeview)
        self.tree = ttk.Treeview(frame_derecho, columns=("id", "producto", "estado"), show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("producto", text="Producto")
        self.tree.heading("estado", text="Estado")
        
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("producto", width=250, anchor="w")
        self.tree.column("estado", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

    # =================================================================
    # LÓGICA DE BASE DE DATOS Y EVENTOS
    # =================================================================
    def _cargar_productos_db(self, filtro=""):
        """Trae todos los productos de la tabla, permitiendo buscar en tiempo real"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if filtro.strip():
            query = "SELECT id, Producto, IF(activo=1, 'ACTIVO', 'INACTIVO') FROM productos WHERE Producto LIKE %s ORDER BY Producto ASC"
            resultados = self.db.execute_query(query, (f"%{filtro.strip()}%",))
        else:
            query = "SELECT id, Producto, IF(activo=1, 'ACTIVO', 'INACTIVO') FROM productos ORDER BY Producto ASC"
            resultados = self.db.execute_query(query)

        if resultados:
            for fila in resultados:
                self.tree.insert("", "end", values=fila)

    def _filtrar_productos(self, event):
        """Dispara la consulta SQL a medida que el cliente escribe"""
        self._cargar_productos_db(self.ent_buscar.get())

    def _al_seleccionar_fila(self, event):
        """Pasa los datos de la grilla al formulario para editar"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        valores = self.tree.item(seleccion[0])["values"]
        self.id_seleccionado = valores[0]
        nombre_prod = valores[1]
        estado = valores[2]

        # Rellenar Entry
        self.ent_producto.delete(0, "end")
        self.ent_producto.insert(0, nombre_prod)

        # Configurar UI para Edición
        self.lbl_estado_actual.configure(text=f"Editando ID #{self.id_seleccionado} ({estado})", text_color="#1d3557")
        self.btn_cambiar_estado.configure(state="normal")
        
        if estado == "ACTIVO":
            self.btn_cambiar_estado.configure(text="DAR DE BAJA", fg_color="#bf3a3a", hover_color="#8f2b2b")
        else:
            self.btn_cambiar_estado.configure(text="REACTIVAR", fg_color="#2a9d8f", hover_color="#1e7166")

    def _guardar_producto(self):
        """Maneja de forma inteligente el INSERT (Nuevo) o el UPDATE (Existente)"""
        nombre = self.ent_producto.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "El nombre del producto es obligatorio.")
            return

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.id_seleccionado is None:
            # --- NUEVO REGISTRO (INSERT) ---
            query = "INSERT INTO productos (Producto, activo, usualta, falta) VALUES (%s, 1, %s, %s)"
            params = (nombre, self.current_user_id, ahora)
            msg_exito = f"Producto '{nombre}' creado con éxito."
        else:
            # --- EDICIÓN (UPDATE) ---
            query = "UPDATE productos SET Producto = %s, usumodi = %s, fmodi = %s WHERE id = %s"
            params = (nombre, self.current_user_id, ahora, self.id_seleccionado)
            msg_exito = "Producto actualizado correctamente."

        try:
            self.db.execute_non_query(query, params)
            messagebox.showinfo("Éxito", msg_exito)
            self._limpiar_formulario()
            self._cargar_productos_db()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo procesar la solicitud:\n{e}")

    def _alternar_estado_producto(self):
        """Cambia el flag 'activo' (Baja lógica / Alta técnica)"""
        if not self.id_seleccionado:
            return

        seleccion = self.tree.selection()
        estado_actual = self.tree.item(seleccion[0])["values"][2]
        nuevo_estado = 0 if estado_actual == "ACTIVO" else 1
        accion_texto = "dar de BAJA" if nuevo_estado == 0 else "REACTIVAR"

        confirmar = messagebox.askyesno("Confirmar", f"¿Está seguro de que desea {accion_texto} este producto?")
        if not confirmar:
            return

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = "UPDATE productos SET activo = %s, usumodi = %s, fmodi = %s WHERE id = %s"
        
        try:
            self.db.execute_non_query(query, (nuevo_estado, self.current_user_id, ahora, self.id_seleccionado))
            messagebox.showinfo("Éxito", f"Estado del producto modificado correctamente.")
            self._limpiar_formulario()
            self._cargar_productos_db()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar el estado:\n{e}")

    def _limpiar_formulario(self):
        """Reinicia los controles para una nueva carga limpia"""
        self.id_seleccionado = None
        self.ent_producto.delete(0, "end")
        self.lbl_estado_actual.configure(text="Estado: Nuevo Registro", text_color="gray")
        self.btn_cambiar_estado.configure(state="disabled", text="DAR DE BAJA", fg_color="#4a5568")
        self.tree.selection_remove(self.tree.selection())