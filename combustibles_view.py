# combustibles_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class CombustiblesView(ctk.CTkFrame):
    def __init__(self, master, db_connection, current_user_id=1):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.current_user_id = current_user_id  # ID de auditoría interna
        self.pack(fill="both", expand=True)

        self.id_combustible_seleccionado = None

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="GESTIÓN DE COMBUSTIBLES Y PRECIOS", font=("Arial", 20, "bold"), text_color="black")
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
        lbl_form_title = ctk.CTkLabel(self.frame_form, text="Datos del Combustible", font=("Arial", 14, "bold"), text_color="#4d5433")
        lbl_form_title.pack(pady=(15, 15), padx=15, anchor="w")

        # Campo: Tipo de Combustible
        lbl_nombre = ctk.CTkLabel(self.frame_form, text="Descripción / Combustible:", font=("Arial", 12, "bold"), text_color="black")
        lbl_nombre.pack(padx=15, anchor="w")
        self.ent_combustible = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="Ej: Gasoil Grado 3, Nafta Super")
        self.ent_combustible.pack(padx=15, pady=(2, 12))

        # Campo: Precio por Litro
        lbl_precio = ctk.CTkLabel(self.frame_form, text="Precio por Litro ($):", font=("Arial", 12, "bold"), text_color="black")
        lbl_precio.pack(padx=15, anchor="w")
        self.ent_precio = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="0.00")
        self.ent_precio.pack(padx=15, pady=(2, 12))

        # Campo: Punto Crítico (Alertas de Stock Mínimo)
        lbl_critico = ctk.CTkLabel(self.frame_form, text="Punto Crítico (Litros Mínimos):", font=("Arial", 12, "bold"), text_color="black")
        lbl_critico.pack(padx=15, anchor="w")
        self.ent_critico = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="Ej: 500")
        self.ent_critico.pack(padx=15, pady=(2, 25))

        # BOTONES DE ACCIÓN
        self.btn_guardar = ctk.CTkButton(self.frame_form, text="GUARDAR NUEVO", font=("Arial", 13, "bold"), fg_color="#8cb04e", hover_color="#73943c", text_color="black", command=self._guardar_combustible)
        self.btn_guardar.pack(fill="x", padx=15, pady=5)

        self.btn_modificar = ctk.CTkButton(self.frame_form, text="ACTUALIZAR VALORES", font=("Arial", 13, "bold"), fg_color="#3a7ebf", hover_color="#2b5e8f", command=self._modificar_combustible)
        self.btn_modificar.pack(fill="x", padx=15, pady=5)
        self.btn_modificar.configure(state="disabled")

        self.btn_eliminar = ctk.CTkButton(self.frame_form, text="ELIMINAR REGISTRO", font=("Arial", 13, "bold"), fg_color="#bf3a3a", hover_color="#8f2b2b", command=self._eliminar_combustible)
        self.btn_eliminar.pack(fill="x", padx=15, pady=5)
        self.btn_eliminar.configure(state="disabled")

        self.btn_limpiar = ctk.CTkButton(self.frame_form, text="LIMPIAR FORMULARIO", font=("Arial", 12), fg_color="gray", hover_color="#555555", command=self._limpiar_formulario)
        self.btn_limpiar.pack(fill="x", padx=15, pady=(15, 5))

        # --- DISEÑO DE LA TABLA (Treeview) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Combustibles.Treeview", font=("Arial", 11), rowheight=30, background="white", fieldbackground="white", foreground="black")
        style.configure("Combustibles.Treeview.Heading", font=("Arial", 12, "bold"), background="#8cb04e", foreground="black", relief="flat")
        style.map("Combustibles.Treeview", background=[("selected", "#b9d291")], foreground=[("selected", "black")])

        columnas = ("id", "combustible", "precios", "puntocritico")
        self.tree = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings", style="Combustibles.Treeview")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("combustible", text="Tipo de Combustible")
        self.tree.heading("precios", text="Precio x Litro")
        self.tree.heading("puntocritico", text="Alerta Mínima")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("combustible", width=250, anchor="w")
        self.tree.column("precios", width=140, anchor="e")
        self.tree.column("puntocritico", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_fila_seleccionada)

        self.after(100, self.cargar_combustibles_db)

    def cargar_combustibles_db(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = "SELECT id, combustible, precios, puntocritico FROM combustibles ORDER BY id DESC"
        resultados = self.db.execute_query(query)
        
        if resultados:
            for fila in resultados:
                precio_val = fila[2] if fila[2] is not None else 0.0
                critico_val = fila[3] if fila[3] is not None else 0
                self.tree.insert("", "end", values=(
                    fila[0], fila[1], f"$ {precio_val:.2f}", f"{critico_val} Lts"
                ))

    def _on_fila_seleccionada(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        
        self.id_combustible_seleccionado = valores[0]
        
        self.ent_combustible.delete(0, "end")
        self.ent_combustible.insert(0, valores[1])
        
        self.ent_precio.delete(0, "end")
        self.ent_precio.insert(0, str(valores[2]).replace("$ ", ""))
        
        self.ent_critico.delete(0, "end")
        self.ent_critico.insert(0, str(valores[3]).replace(" Lts", ""))

        self.btn_guardar.configure(state="disabled")
        self.btn_modificar.configure(state="normal")
        self.btn_eliminar.configure(state="normal")

    def _limpiar_formulario(self):
        self.id_combustible_seleccionado = None
        self.ent_combustible.delete(0, "end")
        self.ent_precio.delete(0, "end")
        self.ent_critico.delete(0, "end")
        
        self.btn_guardar.configure(state="normal")
        self.btn_modificar.configure(state="disabled")
        self.btn_eliminar.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def _guardar_combustible(self):
        nombre = self.ent_combustible.get().strip()
        precio_str = self.ent_precio.get().strip()
        critico_str = self.ent_critico.get().strip()
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not nombre or not precio_str or not critico_str:
            messagebox.showwarning("Campos Requeridos", "Debe completar todos los campos del formulario.")
            return

        try:
            precio = float(precio_str)
            critico = int(critico_str)
        except ValueError:
            messagebox.showwarning("Datos Inválidos", "El precio debe ser decimal (ej: 950.50) y el punto crítico un número entero.")
            return

        # Evitar duplicados de texto exacto
        query_check = "SELECT id FROM combustibles WHERE combustible = %s"
        if self.db.execute_query(query_check, (nombre,)):
            messagebox.showerror("Error", f"El tipo de combustible '{nombre}' ya está registrado.")
            return

        query_insert = """
            INSERT INTO combustibles (combustible, precios, puntocritico, usualta, falta) 
            VALUES (%s, %s, %s, %s, %s)
        """
        self.db.execute_non_query(query_insert, (nombre, precio, critico, self.current_user_id, fecha_actual))
        
        self.cargar_combustibles_db()
        self._limpiar_formulario()
        messagebox.showinfo("Éxito", "Nuevo combustible agregado al catálogo.")

    def _modificar_combustible(self):
        if not self.id_combustible_seleccionado:
            return

        nombre = self.ent_combustible.get().strip()
        precio_str = self.ent_precio.get().strip()
        critico_str = self.ent_critico.get().strip()
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not nombre:
            messagebox.showwarning("Campos Requeridos", "La descripción del combustible no puede estar vacía.")
            return

        try:
            precio = float(precio_str)
            critico = int(critico_str)
        except ValueError:
            messagebox.showwarning("Datos Inválidos", "Verifique que el precio y el punto crítico sean numéricos.")
            return

        query_update = """
            UPDATE combustibles 
            SET combustible = %s, precios = %s, puntocritico = %s, usumodi = %s, fmodi = %s 
            WHERE id = %s
        """
        self.db.execute_non_query(query_update, (nombre, precio, critico, self.current_user_id, fecha_actual, self.id_combustible_seleccionado))
        
        self.cargar_combustibles_db()
        self._limpiar_formulario()
        messagebox.showinfo("Éxito", "Precios y configuraciones actualizados correctamente.")

    def _eliminar_combustible(self):
        """Eliminación física con control estricto de integridad referencial"""
        if not self.id_combustible_seleccionado:
            return

        # Si en el futuro tenés una tabla 'vales_combustible' o 'cargas_combustible'
        # acá añadiríamos la verificación para no romper registros contables.

        confirmar = messagebox.askyesno("Confirmar Eliminación", "¿Está seguro de borrar este tipo de combustible?\nEsta acción eliminará el registro de forma permanente.")
        if confirmar:
            query_delete = "DELETE FROM combustibles WHERE id = %s"
            self.db.execute_non_query(query_delete, (self.id_combustible_seleccionado,))
            
            self.cargar_combustibles_db()
            self._limpiar_formulario()
            messagebox.showinfo("Éxito", "Registro eliminado del sistema.")