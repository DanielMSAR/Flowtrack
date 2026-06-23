# vehiculos_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class VehiculosView(ctk.CTkFrame):
    def __init__(self, master, db_connection, current_user_id=1):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.current_user_id = current_user_id  # ID del usuario logueado para auditoría
        self.pack(fill="both", expand=True)

        self.id_vehiculo_seleccionado = None

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="ADMINISTRACIÓN DE VEHÍCULOS / FLOTA", font=("Arial", 20, "bold"), text_color="black")
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- CONTENEDOR PRINCIPAL EN DOS COLUMNAS ---
        self.main_split = ctk.CTkFrame(self, fg_color="transparent")
        self.main_split.pack(fill="both", expand=True, padx=20, pady=10)

        # COLUMNA IZQUIERDA: Formulario
        self.frame_form = ctk.CTkFrame(self.main_split, width=320, fg_color="#f2f5f8", corner_radius=8)
        self.frame_form.pack(side="left", fill="y", padx=(0, 15), pady=5)
        self.frame_form.pack_propagate(False)

        # COLUMNA DERECHA: Grilla / Tabla
        self.frame_tabla = ctk.CTkFrame(self.main_split, fg_color="transparent")
        self.frame_tabla.pack(side="right", fill="both", expand=True, pady=5)

        # --- DISEÑO DEL FORMULARIO ---
        lbl_form_title = ctk.CTkLabel(self.frame_form, text="Datos del Vehículo", font=("Arial", 14, "bold"), text_color="#4d5433")
        lbl_form_title.pack(pady=(15, 15), padx=15, anchor="w")

        # Campo: Móvil / Patente / Identificador corto
        lbl_movil = ctk.CTkLabel(self.frame_form, text="Nº Móvil / Patente / Ficha:", font=("Arial", 12, "bold"), text_color="black")
        lbl_movil.pack(padx=15, anchor="w")
        self.ent_movil = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="Ej: Interno 04 / AA-123-BB")
        self.ent_movil.pack(padx=15, pady=(2, 12))

        # Campo: Marca
        lbl_marca = ctk.CTkLabel(self.frame_form, text="Marca:", font=("Arial", 12, "bold"), text_color="black")
        lbl_marca.pack(padx=15, anchor="w")
        self.ent_marca = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="Ej: Mercedes-Benz, Scania, Ford")
        self.ent_marca.pack(padx=15, pady=(2, 12))

        # Campo: Modelo
        lbl_modelo = ctk.CTkLabel(self.frame_form, text="Modelo / Descripción:", font=("Arial", 12, "bold"), text_color="black")
        lbl_modelo.pack(padx=15, anchor="w")
        self.ent_modelo = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="Ej: Axor 2035 / Cargo 1722")
        self.ent_modelo.pack(padx=15, pady=(2, 25))

        # BOTONES DE ACCIÓN
        self.btn_guardar = ctk.CTkButton(self.frame_form, text="GUARDAR / NUEVO", font=("Arial", 13, "bold"), fg_color="#8cb04e", hover_color="#73943c", text_color="black", command=self._guardar_vehiculo)
        self.btn_guardar.pack(fill="x", padx=15, pady=5)

        self.btn_modificar = ctk.CTkButton(self.frame_form, text="APLICAR CAMBIOS", font=("Arial", 13, "bold"), fg_color="#3a7ebf", hover_color="#2b5e8f", command=self._modificar_vehiculo)
        self.btn_modificar.pack(fill="x", padx=15, pady=5)
        self.btn_modificar.configure(state="disabled")

        self.btn_eliminar = ctk.CTkButton(self.frame_form, text="DAR DE BAJA (INACTIVAR)", font=("Arial", 13, "bold"), fg_color="#bf3a3a", hover_color="#8f2b2b", command=self._eliminar_vehiculo)
        self.btn_eliminar.pack(fill="x", padx=15, pady=5)
        self.btn_eliminar.configure(state="disabled")

        self.btn_limpiar = ctk.CTkButton(self.frame_form, text="LIMPIAR FORMULARIO", font=("Arial", 12), fg_color="gray", hover_color="#555555", command=self._limpiar_formulario)
        self.btn_limpiar.pack(fill="x", padx=15, pady=(15, 5))

        # --- DISEÑO DE LA TABLA (Treeview) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Vehiculos.Treeview", font=("Arial", 11), rowheight=30, background="white", fieldbackground="white", foreground="black")
        style.configure("Vehiculos.Treeview.Heading", font=("Arial", 12, "bold"), background="#8cb04e", foreground="black", relief="flat")
        style.map("Vehiculos.Treeview", background=[("selected", "#b9d291")], foreground=[("selected", "black")])

        columnas = ("id", "movil", "marca", "modelo")
        self.tree = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings", style="Vehiculos.Treeview")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("movil", text="Identificador / Móvil")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("modelo", text="Modelo")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("movil", width=150, anchor="center")
        self.tree.column("marca", width=180, anchor="w")
        self.tree.column("modelo", width=220, anchor="w")

        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_fila_seleccionada)

        # Cargar vehículos activos de la DB
        self.after(100, self.cargar_vehiculos_db)

    def cargar_vehiculos_db(self):
        """Muestra únicamente los vehículos que tienen activo = 1"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = "SELECT idvehiculo, movil, marca, modelo FROM vehiculos WHERE activo = 1 ORDER BY idvehiculo DESC"
        resultados = self.db.execute_query(query)
        
        if resultados:
            for fila in resultados:
                self.tree.insert("", "end", values=(fila[0], fila[1], fila[2], fila[3]))

    def _on_fila_seleccionada(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        
        self.id_vehiculo_seleccionado = valores[0]
        
        self.ent_movil.delete(0, "end")
        self.ent_movil.insert(0, valores[1])
        
        self.ent_marca.delete(0, "end")
        self.ent_marca.insert(0, valores[2])
        
        self.ent_modelo.delete(0, "end")
        self.ent_modelo.insert(0, valores[3])

        self.btn_guardar.configure(state="disabled")
        self.btn_modificar.configure(state="normal")
        self.btn_eliminar.configure(state="normal")

    def _limpiar_formulario(self):
        self.id_vehiculo_seleccionado = None
        self.ent_movil.delete(0, "end")
        self.ent_marca.delete(0, "end")
        self.ent_modelo.delete(0, "end")
        
        self.btn_guardar.configure(state="normal")
        self.btn_modificar.configure(state="disabled")
        self.btn_eliminar.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def _guardar_vehiculo(self):
        movil = self.ent_movil.get().strip()
        marca = self.ent_marca.get().strip()
        modelo = self.ent_modelo.get().strip()
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not movil or not marca:
            messagebox.showwarning("Campos Requeridos", "Debe completar obligatoriamente el identificador del Móvil y la Marca.")
            return

        # Evitar duplicados de patentes/móviles que estén actualmente activos
        query_check = "SELECT idvehiculo FROM vehiculos WHERE movil = %s AND activo = 1"
        if self.db.execute_query(query_check, (movil,)):
            messagebox.showerror("Duplicado", f"El móvil o patente '{movil}' ya se encuentra activo en el parque automotor.")
            return

        # Insertar inyectando metadatos de auditoría (Alta)
        query_insert = """
            INSERT INTO vehiculos (marca, modelo, movil, usualta, falta, activo) 
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        self.db.execute_non_query(query_insert, (marca, modelo, movil, self.current_user_id, fecha_actual))
        
        self.cargar_vehiculos_db()
        self._limpiar_formulario()
        messagebox.showinfo("Éxito", "Vehículo incorporado a la flota con éxito.")

    def _modificar_vehiculo(self):
        if not self.id_vehiculo_seleccionado:
            return

        movil = self.ent_movil.get().strip()
        marca = self.ent_marca.get().strip()
        modelo = self.ent_modelo.get().strip()
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not movil or not marca:
            messagebox.showwarning("Campos Requeridos", "El móvil y la marca no pueden quedar vacíos.")
            return

        # Modificar inyectando metadatos de auditoría (Modificación)
        query_update = """
            UPDATE vehiculos 
            SET marca = %s, modelo = %s, movil = %s, usumodi = %s, fmodi = %s 
            WHERE idvehiculo = %s
        """
        self.db.execute_non_query(query_update, (marca, modelo, movil, self.current_user_id, fecha_actual, self.id_vehiculo_seleccionado))
        
        self.cargar_vehiculos_db()
        self._limpiar_formulario()
        messagebox.showinfo("Éxito", "Registro del vehículo actualizado correctamente.")

    def _eliminar_vehiculo(self):
        """Aplica una Baja Lógica configurando activo = 0 para resguardar la trazabilidad"""
        if not self.id_vehiculo_seleccionado:
            return

        confirmar = messagebox.askyesno(
            "Confirmar Inactivación", 
            "¿Desea dar de baja este vehículo de la flota activa?\n\n"
            "Nota: El registro no se eliminará físicamente para conservar el historial de pesajes en los que participó."
        )
        if confirmar:
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Pasamos activo a 0 y guardamos quién ejecutó la baja
            query_baja_logica = """
                UPDATE vehiculos 
                SET activo = 0, usumodi = %s, fmodi = %s 
                WHERE idvehiculo = %s
            """
            self.db.execute_non_query(query_baja_logica, (self.current_user_id, fecha_actual, self.id_vehiculo_seleccionado))
            
            self.cargar_vehiculos_db()
            self._limpiar_formulario()
            messagebox.showinfo("Éxito", "El vehículo fue dado de baja de la flota activa.")