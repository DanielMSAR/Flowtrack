# varios_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox

class VariosView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        self.id_seleccionado = None

        # TÍTULO PRINCIPAL
        self.titulo = ctk.CTkLabel(
            self, 
            text="CONFIGURACIONES Y PARÁMETROS VARIOS", 
            font=("Arial", 20, "bold"), 
            text_color="black"
        )
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- CONTENEDOR DE PESTAÑAS (Para agregar más a futuro) ---
        self.tabview = ctk.CTkTabview(
            self, 
            segmented_button_selected_color="#8cb04e", 
            segmented_button_selected_hover_color="#73943c"
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Compatibilidad de color de texto en pestañas
        try:
            self.tabview._segmented_button.configure(text_color="black")
        except:
            pass

        # Agregar la primera pestaña: Envases
        self.tab_envases = self.tabview.add("Gestión de Envases")
        self._armar_pestana_envases()

    # =================================================================
    # PESTAÑA: GESTIÓN DE ENVASES (ABM)
    # =================================================================
    def _armar_pestana_envases(self):
        # Layout de 2 columnas: Izquierda (Formulario), Derecha (Grilla/Tabla)
        self.tab_envases.grid_columnconfigure(0, weight=0) # Ancho fijo para inputs
        self.tab_envases.grid_columnconfigure(1, weight=1) # Grilla se expande
        self.tab_envases.grid_rowconfigure(0, weight=1)

        # ---------------- COLUMNA IZQUIERDA: FORMULARIO ----------------
        frame_form = ctk.CTkFrame(self.tab_envases, fg_color="#f8f9fa", width=300, corner_radius=8)
        frame_form.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_form.grid_propagate(False) # Forzar el ancho de 300px

        ctk.CTkLabel(frame_form, text="Datos del Envase", font=("Arial", 14, "bold"), text_color="black").pack(pady=10, padx=15, anchor="w")

        # Entrada: Nombre del Envase
        ctk.CTkLabel(frame_form, text="Nombre del Envase *", text_color="black").pack(padx=15, anchor="w")
        self.ent_envase = ctk.CTkEntry(frame_form, width=270)
        self.ent_envase.pack(padx=15, pady=(2, 12))

        # Entrada: Capacidad (Double / Real)
        ctk.CTkLabel(frame_form, text="Capacidad * (Ej: 1.5 o 500)", text_color="black").pack(padx=15, anchor="w")
        self.ent_capacidad = ctk.CTkEntry(frame_form, width=270)
        self.ent_capacidad.pack(padx=15, pady=(2, 20))

        # Botones de Acción
        self.btn_guardar = ctk.CTkButton(
            frame_form, 
            text="GUARDAR NUEVO", 
            fg_color="#8cb04e", 
            hover_color="#73943c", 
            text_color="black", 
            font=("Arial", 11, "bold"),
            command=self._guardar_envase
        )
        self.btn_guardar.pack(fill="x", padx=15, pady=5)

        self.btn_eliminar = ctk.CTkButton(
            frame_form, 
            text="ELIMINAR SELECCIONADO", 
            fg_color="#bf3a3a", 
            hover_color="#8f2b2b", 
            text_color="white", 
            font=("Arial", 11, "bold"),
            command=self._eliminar_envase,
            state="disabled"
        )
        self.btn_eliminar.pack(fill="x", padx=15, pady=5)

        self.btn_limpiar = ctk.CTkButton(
            frame_form, 
            text="LIMPIAR CAMPOS", 
            fg_color="#e2e8f0", 
            hover_color="#cbd5e1", 
            text_color="black", 
            font=("Arial", 11, "bold"),
            command=self._limpiar_campos
        )
        self.btn_limpiar.pack(fill="x", padx=15, pady=5)

        # ---------------- COLUMNA DERECHA: GRILLA ----------------
        frame_tabla = ctk.CTkFrame(self.tab_envases, fg_color="white")
        frame_tabla.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_tabla, text="Envases Registrados", font=("Arial", 13, "bold"), text_color="black").pack(anchor="w", pady=(0, 5))

        self.tree_envases = ttk.Treeview(frame_tabla, columns=("id", "envase", "capacidad"), show="headings")
        self.tree_envases.heading("id", text="ID")
        self.tree_envases.heading("envase", text="Envase / Descripción")
        self.tree_envases.heading("capacidad", text="Capacidad")

        self.tree_envases.column("id", width=60, anchor="center")
        self.tree_envases.column("envase", width=250, anchor="w")
        self.tree_envases.column("capacidad", width=120, anchor="e")
        
        self.tree_envases.pack(fill="both", expand=True)
        self.tree_envases.bind("<<TreeviewSelect>>", self._on_seleccionar_grilla)

        # Cargar los datos iniciales de la Base de Datos
        self._cargar_envases_db()

    # =================================================================
    # LOGICA DE NEGOCIO Y CONSULTAS A LA BD
    # =================================================================
    def _cargar_envases_db(self):
        # Limpiar grilla
        for item in self.tree_envases.get_children():
            self.tree_envases.delete(item)
            
        try:
            # Reemplaza 'envases' por el nombre exacto que le diste a tu tabla en MariaDB
            query = "SELECT idenvase, envase, capacidad FROM envases ORDER BY envase ASC"
            resultados = self.db.execute_query(query)
            if resultados:
                for fila in resultados:
                    self.tree_envases.insert("", "end", values=fila)
        except Exception as e:
            print(f"Error al cargar envases de la BD: {e}")

    def _guardar_envase(self):
        nombre = self.ent_envase.get().strip()
        capacidad_str = self.ent_capacidad.get().strip().replace(",", ".") # Reemplaza coma por punto decimal

        if not nombre or not capacidad_str:
            messagebox.showwarning("Atención", "Todos los campos marcados con asterisco (*) son obligatorios.")
            return

        try:
            capacidad = float(capacidad_str)
        except ValueError:
            messagebox.showerror("Error de tipo", "La capacidad debe ser un número decimal o entero válido (Ej: 12.50).")
            return

        try:
            if self.id_seleccionado is None:
                # INSERTAR NUEVO
                query = "INSERT INTO envases (envase, capacidad) VALUES (%s, %s)"
                self.db.execute_non_query(query, (nombre, capacidad))
                messagebox.showinfo("Éxito", f"Envase '{nombre}' registrado correctamente.")
            else:
                # MODIFICAR EXISTENTE
                query = "UPDATE envases SET envase = %s, capacidad = %s WHERE idenvase = %s"
                self.db.execute_non_query(query, (nombre, capacidad, self.id_seleccionado))
                messagebox.showinfo("Éxito", f"Envase actualizado correctamente.")

            self._limpiar_campos()
            self._cargar_envases_db()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el envase:\n{e}")

    def _eliminar_envase(self):
        if not self.id_seleccionado:
            return
            
        confirmar = messagebox.askyesno(
            "Confirmar eliminación", 
            "¿Está seguro de que desea eliminar este envase?\nEsta acción no se puede deshacer."
        )
        if confirmar:
            try:
                query = "DELETE FROM envases WHERE idenvase = %s"
                self.db.execute_non_query(query, (self.id_seleccionado,))
                messagebox.showinfo("Éxito", "Envase eliminado correctamente.")
                self._limpiar_campos()
                self._cargar_envases_db()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el envase. Puede que esté asociado a otros registros.\nDetalle: {e}")

    def _on_seleccionar_grilla(self, event):
        seleccion = self.tree_envases.selection()
        if not seleccion:
            return

        valores = self.tree_envases.item(seleccion[0], "values")
        self.id_seleccionado = valores[0]
        
        # Rellenar campos
        self.ent_envase.delete(0, "end")
        self.ent_envase.insert(0, valores[1])
        
        self.ent_capacidad.delete(0, "end")
        self.ent_capacidad.insert(0, valores[2])

        # Cambiar comportamiento del botón guardar a Modificar
        self.btn_guardar.configure(text="GUARDAR CAMBIOS", fg_color="#3a7ebf", hover_color="#2b5e8f", text_color="white")
        self.btn_eliminar.configure(state="normal")

    def _limpiar_campos(self):
        self.id_seleccionado = None
        self.ent_envase.delete(0, "end")
        self.ent_capacidad.delete(0, "end")
        self.btn_guardar.configure(text="GUARDAR NUEVO", fg_color="#8cb04e", hover_color="#73943c", text_color="black")
        self.btn_eliminar.configure(state="disabled")
        self.tree_envases.selection_remove(self.tree_envases.selection())