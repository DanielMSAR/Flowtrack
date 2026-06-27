# insumos_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class InsumosView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Capturamos el ID del usuario logueado en app.py (a través del root)
        self.current_user_id = getattr(master.winfo_toplevel(), "current_user_id", 1)
        self.selected_id = None  # Almacena el ID del insumo seleccionado para editar

        # --- ESTRUCTURA DE DISEÑO ---
        # Panel Izquierdo: Formulario de Carga
        self.form_frame = ctk.CTkFrame(self, width=320, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e9ecef")
        self.form_frame.pack(side="left", fill="y", padx=15, pady=15)
        self.form_frame.pack_propagate(False)

        # Panel Derecho: Tabla de Visualización
        self.table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.table_frame.pack(side="right", fill="both", expand=True, padx=(0, 15), pady=15)

        self._crear_formulario()
        self._crear_tabla()
        self.cargar_datos()

    def _crear_formulario(self):
        # Título del Formulario
        self.form_title = ctk.CTkLabel(self.form_frame, text="GESTIÓN DE INSUMOS", font=("Arial", 16, "bold"), text_color="#4d5433")
        self.form_title.pack(pady=(20, 15), padx=15, anchor="w")

        # Campo: Insumo (Nombre)
        self.lbl_insumo = ctk.CTkLabel(self.form_frame, text="Descripción del Insumo:", font=("Arial", 12, "bold"), text_color="black")
        self.lbl_insumo.pack(pady=(10, 2), padx=15, anchor="w")
        self.ent_insumo = ctk.CTkEntry(self.form_frame, width=280, height=35, font=("Arial", 13))
        self.ent_insumo.pack(padx=15, pady=(0, 10))

        # Campo: Precios
        self.lbl_precio = ctk.CTkLabel(self.form_frame, text="Precio ($):", font=("Arial", 12, "bold"), text_color="black")
        self.lbl_precio.pack(pady=(5, 2), padx=15, anchor="w")
        self.ent_precio = ctk.CTkEntry(self.form_frame, width=280, height=35, font=("Arial", 13))
        self.ent_precio.pack(padx=15, pady=(0, 10))

        # Campo: Punto Crítico
        self.lbl_critico = ctk.CTkLabel(self.form_frame, text="Punto Crítico (Stock Mínimo):", font=("Arial", 12, "bold"), text_color="black")
        self.lbl_critico.pack(pady=(5, 2), padx=15, anchor="w")
        self.ent_critico = ctk.CTkEntry(self.form_frame, width=280, height=35, font=("Arial", 13))
        self.ent_critico.pack(padx=15, pady=(0, 20))

        # Botón: Guardar / Actualizar
        self.btn_guardar = ctk.CTkButton(
            self.form_frame, text="GUARDAR INSUMO", fg_color="#4d5433", hover_color="#3b4026",
            text_color="white", font=("Arial", 13, "bold"), height=40, command=self.guardar_datos
        )
        self.btn_guardar.pack(fill="x", padx=15, pady=5)

        # Botón: Cancelar / Limpiar Selección
        self.btn_limpiar = ctk.CTkButton(
            self.form_frame, text="CANCELAR", fg_color="#e2e6ea", hover_color="#dae0e5",
            text_color="black", font=("Arial", 13, "bold"), height=35, command=self.limpiar_formulario
        )
        self.btn_limpiar.pack(fill="x", padx=15, pady=5)

        # Botón: Eliminar Insumo
        self.btn_eliminar = ctk.CTkButton(
            self.form_frame, text="ELIMINAR SELECCIONADO", fg_color="#dc3545", hover_color="#bd2130",
            text_color="white", font=("Arial", 13, "bold"), height=35, command=self.eliminar_datos
        )
        self.btn_eliminar.pack(fill="x", padx=15, pady=(20, 5))

    def _crear_tabla(self):
        # Configuración de estilos del Treeview para acoplarlo a CustomTkinter de forma limpia
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", font=("Arial", 11))
        style.configure("Treeview.Heading", background="#f1f3f5", foreground="black", font=("Arial", 11, "bold"), borderwidth=1)
        style.map("Treeview", background=[("selected", "#8cb04e")], foreground=[("selected", "black")])

        # Definición de columnas visibles basándonos en tu diseño original
        columnas = ("id", "insumo", "precios", "puntocritico", "falta", "fmodi")
        self.tree = ttk.Treeview(self.table_frame, columns=columnas, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("insumo", text="INSUMO")
        self.tree.heading("precios", text="PRECIO")
        self.tree.heading("puntocritico", text="PUNTO CRÍTICO")
        self.tree.heading("falta", text="FECHA ALTA")
        self.tree.heading("fmodi", text="ÚLT. MODIF.")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("insumo", width=250, anchor="w")
        self.tree.column("precios", width=100, anchor="e")
        self.tree.column("puntocritico", width=110, anchor="center")
        self.tree.column("falta", width=140, anchor="center")
        self.tree.column("fmodi", width=140, anchor="center")

        # Scrollbar vertical para la grilla
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Evento de selección de fila
        self.tree.bind("<<TreeviewSelect>>", self.on_fila_seleccionada)

    def cargar_datos(self):
        """Trae todos los registros ordenados desde la base de datos"""
        for fila in self.tree.get_children():
            self.tree.delete(fila)

        query = "SELECT id, insumo, precios, puntocritico, falta, fmodi FROM insumos ORDER BY id DESC"
        registros = self.db.execute_query(query)

        if registros:
            for r in registros:
                # Formatear visualmente los Floats y Datetimes para que se lean prolijos en planta
                precio_fmt = f"$ {r[2]:,.2f}" if r[2] is not None else "$ 0.00"
                critico_fmt = f"{r[3]:.2f}" if r[3] is not None else "0.00"
                falta_fmt = r[4].strftime('%d/%m/%Y %H:%M') if r[4] else ""
                fmodi_fmt = r[5].strftime('%d/%m/%Y %H:%M') if r[5] else "-"

                self.tree.insert("", "end", values=(r[0], r[1], precio_fmt, critico_fmt, falta_fmt, fmodi_fmt))

    def on_fila_seleccionada(self, event):
        """Carga la fila elegida en las cajas de texto del panel izquierdo"""
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]

        self.selected_id = valores[0]
        self.ent_insumo.delete(0, "end")
        self.ent_insumo.insert(0, valores[1])

        # Quitamos el formato de moneda para poder editar el número plano
        precio_limpio = str(valores[2]).replace("$", "").replace(",", "").strip()
        self.ent_precio.delete(0, "end")
        self.ent_precio.insert(0, precio_limpio)

        self.ent_critico.delete(0, "end")
        self.ent_critico.insert(0, valores[3])

        self.btn_guardar.configure(text="ACTUALIZAR INSUMO", fg_color="#8cb04e", hover_color="#769641", text_color="black")

    def guardar_datos(self):
        """Inserta un nuevo insumo o actualiza uno existente"""
        insumo = self.ent_insumo.get().strip()
        precio_raw = self.ent_precio.get().strip()
        critico_raw = self.ent_critico.get().strip()

        if not insumo:
            messagebox.showwarning("Atención", "El nombre del insumo es obligatorio.")
            return

        # Conversión segura de tipos de datos Float
        try:
            precio = float(precio_raw) if precio_raw else 0.0
            puntocritico = float(critico_raw) if critico_raw else 0.0
        except ValueError:
            messagebox.showerror("Error", "El precio y el punto crítico deben ser valores numéricos válidos.")
            return

        if self.selected_id is None:
            # Operación: ALTA NUEVA (Usamos usualta)
            query = """INSERT INTO insumos (insumo, precios, puntocritico, usualta, falta) 
                       VALUES (%s, %s, %s, %s, %s)"""
            params = (insumo, precio, puntocritico, self.current_user_id, datetime.now())
            mensaje_exito = "Insumo creado correctamente."
        else:
            # Operación: MODIFICACIÓN (Usamos usumodi y fmodi)
            query = """UPDATE insumos 
                       SET insumo = %s, precios = %s, puntocritico = %s, usumodi = %s, fmodi = %s 
                       WHERE id = %s"""
            params = (insumo, precio, puntocritico, self.current_user_id, datetime.now(), self.selected_id)
            mensaje_exito = "Insumo actualizado de forma exitosa."

        try:
            self.db.execute_query(query, params)
            
            # =====================================================================
            # CONFIRMACIÓN (COMMIT) EN MARIADB
            # =====================================================================
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.commit()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.commit()
            # =====================================================================

            messagebox.showinfo("Éxito", mensaje_exito)
            self.limpiar_formulario()
            self.cargar_datos()
        except Exception as e:
            # Revertimos en caso de falla extrema
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.rollback()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.rollback()
                
            messagebox.showerror("Error de Base de Datos", f"No se pudo guardar el registro:\n{e}")

    def eliminar_datos(self):
        """Borra por completo el insumo seleccionado de la tabla"""
        if self.selected_id is None:
            messagebox.showwarning("Atención", "Por favor, seleccione un insumo de la lista para eliminar.")
            return

        confirmar = messagebox.askyesno("Confirmar Baja", "¿Está seguro de que desea eliminar permanentemente este insumo?")
        if confirmar:
            query = "DELETE FROM insumos WHERE id = %s"
            try:
                self.db.execute_query(query, (self.selected_id,))
                
                # =====================================================================
                # CONFIRMACIÓN (COMMIT) PARA LA BAJA
                # =====================================================================
                if hasattr(self.db, "connection") and self.db.connection:
                    self.db.connection.commit()
                elif hasattr(self.db, "conn") and self.db.conn:
                    self.db.conn.commit()
                # =====================================================================

                messagebox.showinfo("Eliminado", "El insumo fue removido correctamente.")
                self.limpiar_formulario()
                self.cargar_datos()
            except Exception as e:
                if hasattr(self.db, "connection") and self.db.connection:
                    self.db.connection.rollback()
                elif hasattr(self.db, "conn") and self.db.conn:
                    self.db.conn.rollback()
                    
                messagebox.showerror("Error", f"No se pudo eliminar el registro:\n{e}")

    def limpiar_formulario(self):
        """Blanquea las variables de control y cajas de texto"""
        self.selected_id = None
        self.ent_insumo.delete(0, "end")
        self.ent_precio.delete(0, "end")
        self.ent_critico.delete(0, "end")
        self.btn_guardar.configure(text="GUARDAR INSUMO", fg_color="#4d5433", hover_color="#3b4026", text_color="white")
        self.tree.selection_remove(self.tree.selection())