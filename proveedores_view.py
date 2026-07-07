# proveedores_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
import os

class ProveedoresView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # ID del proveedor seleccionado para edición (None = Nuevo Registro)
        self.id_proveedor_sel = None

        # --- DISEÑO EN COLUMNAS (Formulario Izquierda, Tabla Derecha) ---
        self.grid_columnconfigure(0, weight=0)  # Panel de carga (Ancho fijo)
        self.grid_columnconfigure(1, weight=1)  # Panel de visualización (Expandible)
        self.grid_rowconfigure(0, weight=1)

        # =================================================================
        # COLUMNA 1: FORMULARIO DE ALTA Y EDICIÓN
        # =================================================================
        self.form_frame = ctk.CTkFrame(self, width=320, fg_color="#f8f9fa", corner_radius=10, border_width=1, border_color="#e0e0e0")
        self.form_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.form_frame.grid_propagate(False)

        # Título del Formulario
        self.lbl_form_title = ctk.CTkLabel(self.form_frame, text="REGISTRO DE PROVEEDOR", font=("Arial", 16, "bold"), text_color="#4d5433")
        self.lbl_form_title.pack(pady=(20, 15), padx=20, anchor="w")

        # Campo: Proveedor / Razón Social
        ctk.CTkLabel(self.form_frame, text="Proveedor / Razón Social *", font=("Arial", 12, "bold"), text_color="black").pack(padx=20, anchor="w")
        self.ent_proveedor = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: Central de Insumos S.A.", fg_color="white", text_color="black")
        self.ent_proveedor.pack(fill="x", padx=20, pady=(0, 12))

        # Campo: CUIT
        ctk.CTkLabel(self.form_frame, text="CUIT (Sin guiones)", font=("Arial", 12, "bold"), text_color="black").pack(padx=20, anchor="w")
        self.ent_cuit = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: 30123456789", fg_color="white", text_color="black")
        self.ent_cuit.pack(fill="x", padx=20, pady=(0, 12))

        # Campo: Teléfono
        ctk.CTkLabel(self.form_frame, text="Teléfono de Contacto", font=("Arial", 12, "bold"), text_color="black").pack(padx=20, anchor="w")
        self.ent_telefono = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: 3755421100", fg_color="white", text_color="black")
        self.ent_telefono.pack(fill="x", padx=20, pady=(0, 20))

        # Botón Principal: Guardar / Actualizar
        self.btn_guardar = ctk.CTkButton(self.form_frame, text="Guardar Registro", fg_color="#7a8754", hover_color="#636e43", text_color="white", font=("Arial", 13, "bold"), command=self.guardar_registro)
        self.btn_guardar.pack(fill="x", padx=20, pady=5)

        # Botón Secundario: Cancelar Edición / Limpiar
        self.btn_limpiar = ctk.CTkButton(self.form_frame, text="Limpiar Campos", fg_color="#e0e0e0", hover_color="#d5d5d5", text_color="black", font=("Arial", 13), command=self.limpiar_formulario)
        self.btn_limpiar.pack(fill="x", padx=20, pady=5)

        # =================================================================
        # COLUMNA 2: TABLA DE VISUALIZACIÓN Y ACCIONES
        # =================================================================
        self.data_frame = ctk.CTkFrame(self, fg_color="white")
        self.data_frame.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        
        # Barra de herramientas superior de la tabla
        self.top_bar = ctk.CTkFrame(self.data_frame, fg_color="white")
        self.top_bar.pack(fill="x", pady=(0, 10))
        
        self.lbl_tabla_title = ctk.CTkLabel(self.top_bar, text="Proveedores", font=("Arial", 18, "bold"), text_color="black")
        self.lbl_tabla_title.pack(side="left", anchor="w")

        self.btn_eliminar = ctk.CTkButton(self.top_bar, text="Eliminar Seleccionado", fg_color="#bc4749", hover_color="#a73c3e", text_color="white", font=("Arial", 12, "bold"), width=150, command=self.eliminar_registro)
        self.btn_eliminar.pack(side="right", padx=5)

        # Contenedor para la Grilla (Treeview) con su Scrollbar
        self.tree_container = ctk.CTkFrame(self.data_frame, fg_color="white")
        self.tree_container.pack(fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_container, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        # Configuración del estilo clásico de la grilla
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black", rowheight=28, font=("Arial", 11))
        style.configure("Treeview.Heading", background="#264653", foreground="white", font=("Arial", 11, "bold"))
        style.map("Treeview.Heading", background=[('active', '#1d3557')])

        # Creación del Treeview con las columnas solicitadas
        self.tree = ttk.Treeview(
            self.tree_container, 
            columns=("id", "proveedor", "cuit", "telefono"), 
            show="headings", 
            yscrollcommand=self.scrollbar.set
        )
        self.tree.pack(fill="both", expand=True)
        self.scrollbar.config(command=self.tree.yview)

        # Encabezados y anchos
        self.tree.heading("id", text="ID")
        self.tree.heading("proveedor", text="PROVEEDOR / RAZÓN SOCIAL")
        self.tree.heading("cuit", text="CUIT")
        self.tree.heading("telefono", text="TELÉFONO")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("proveedor", width=280, anchor="w")
        self.tree.column("cuit", width=130, anchor="center")
        self.tree.column("telefono", width=140, anchor="center")

        # Evento de selección en la tabla para pasar a modo edición
        self.tree.bind("<<TreeviewSelect>>", self.cargar_fila_seleccionada)

        # Cargar los datos iniciales de la base de datos
        self.cargar_grid()

    # =================================================================
    # LÓGICA INTERNA Y CONSULTAS A LA BASE DE DATOS
    # =================================================================
    
    def cargar_grid(self):
        """Limpia la grilla y consulta MariaDB para poblarla con los datos vigentes"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            query = "SELECT id, proveedor, cuit, telefono FROM proveedores ORDER BY proveedor ASC"
            resultados = self.db.execute_query(query)
            
            if resultados:
                for fila in resultados:
                    # Si viene un dato None de la DB, lo transformamos visualmente a un guion prolijo
                    cuit_vis = fila[2] if fila[2] else "-"
                    tel_vis = fila[3] if fila[3] else "-"
                    self.tree.insert("", "end", values=(fila[0], fila[1], cuit_vis, tel_vis))
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudo consultar la tabla proveedores:\n{e}")

    def guardar_registro(self):
        """Maneja tanto las altas como las modificaciones basadas en self.id_proveedor_sel"""
        nom_prov = self.ent_proveedor.get().strip()
        cuit_val = self.ent_cuit.get().strip()
        tel_val = self.ent_telefono.get().strip()

        if not nom_prov:
            messagebox.showwarning("Atención", "El campo 'Proveedor / Razón Social' es obligatorio para operar.")
            return

        # Convertir vacíos a None para que impacten correctamente como NULL en MariaDB
        cuit_db = cuit_val if cuit_val else None
        tel_db = tel_val if tel_val else None

        try:
            if self.id_proveedor_sel is None:
                # MODO ALTA (NUEVO REGISTRO)
                query = "INSERT INTO proveedores (proveedor, cuit, telefono) VALUES (%s, %s, %s)"
                params = (nom_prov, cuit_db, tel_db)
                mensaje_exito = "Proveedor guardado exitosamente."
            else:
                # MODO EDICIÓN (ACTUALIZAR EXISTENTE)
                query = "UPDATE proveedores SET proveedor = %s, cuit = %s, telefono = %s WHERE id = %s"
                params = (nom_prov, cuit_db, tel_db, self.id_proveedor_sel)
                mensaje_exito = "Datos del proveedor actualizados correctamente."

            self.db.execute_query(query, params)
            
            # Forzar el Commit manual si tu clase DB lo requiere
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.commit()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.commit()

            messagebox.showinfo("Éxito", mensaje_exito)
            self.limpiar_formulario()
            self.cargar_grid()

        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"No se pudo completar la operación:\n{e}")

    def cargar_fila_seleccionada(self, event):
        """Pasa los datos de la fila seleccionada al formulario lateral y activa el modo edición"""
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]

        # Guardamos el ID para saber que estamos editando
        self.id_proveedor_sel = valores[0]

        # Limpiamos y rellenamos las entradas
        self.ent_proveedor.delete(0, "end")
        self.ent_proveedor.insert(0, valores[1])

        self.ent_cuit.delete(0, "end")
        self.ent_cuit.insert(0, "" if valores[2] == "-" else valores[2])

        self.ent_telefono.delete(0, "end")
        self.ent_telefono.insert(0, "" if valores[3] == "-" else valores[3])

        # Cambiamos la estética visual del formulario para alertar el modo EDICIÓN
        self.lbl_form_title.configure(text="MODIFICAR PROVEEDOR", text_color="#1d3557")
        self.btn_guardar.configure(text="Actualizar Cambios", fg_color="#1d3557", hover_color="#457b9d")

    def eliminar_registro(self):
        """Elimina físicamente el proveedor de la base de datos previa confirmación"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debe seleccionar un proveedor de la grilla para eliminar.")
            return

        item = self.tree.item(seleccion[0])
        id_eliminar = item["values"][0]
        nombre_eliminar = item["values"][1]

        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación", 
            f"¿Está seguro de que desea eliminar permanentemente al proveedor:\n'{nombre_eliminar}'?\n\nEsta acción no se puede deshacer."
        )

        if confirmacion:
            try:
                query = "DELETE FROM proveedores WHERE id = %s"
                self.db.execute_query(query, (id_eliminar,))
                
                if hasattr(self.db, "connection") and self.db.connection:
                    self.db.connection.commit()
                elif hasattr(self.db, "conn") and self.db.conn:
                    self.db.conn.commit()

                messagebox.showinfo("Eliminado", "El registro ha sido removido de la base de datos.")
                self.limpiar_formulario()
                self.cargar_grid()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro (puede que esté vinculado a movimientos históricos):\n{e}")

    def limpiar_formulario(self):
        """Resetea todas las variables y devuelve el formulario a modo ALTA nativo"""
        self.id_proveedor_sel = None
        self.ent_proveedor.delete(0, "end")
        self.ent_cuit.delete(0, "end")
        self.ent_telefono.delete(0, "end")
        
        # Volvemos a los textos y colores originales de ALTA
        self.lbl_form_title.configure(text="REGISTRO DE PROVEEDOR", text_color="#4d5433")
        self.btn_guardar.configure(text="Guardar Registro", fg_color="#7a8754", hover_color="#636e43")
        self.tree.selection_remove(self.tree.selection())