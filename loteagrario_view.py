# loteagrario_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox

class LoteAgrarioView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Estructura para mapear el índice del Combo con el idchacra real de la DB
        self.lista_id_chacras = []
        self.id_lote_seleccionado = None

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="ADMINISTRACIÓN DE PARCELAS / LOTES AGRARIOS", font=("Arial", 20, "bold"), text_color="black")
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
        lbl_form_title = ctk.CTkLabel(self.frame_form, text="Datos de la Parcela", font=("Arial", 14, "bold"), text_color="#4d5433")
        lbl_form_title.pack(pady=(15, 15), padx=15, anchor="w")

        # Campo: Identificador del Lote Agrario
        lbl_nombre = ctk.CTkLabel(self.frame_form, text="Nombre / Código de Parcela:", font=("Arial", 12, "bold"), text_color="black")
        lbl_nombre.pack(padx=15, anchor="w")
        self.ent_loteagrario = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="Ej: Cuadro 1, Parcela Norte")
        self.ent_loteagrario.pack(padx=15, pady=(2, 15))

        # Campo Relacional: Selección de Chacra (FK)
        lbl_chacra = ctk.CTkLabel(self.frame_form, text="Chacra / Establecimiento Madre:", font=("Arial", 12, "bold"), text_color="black")
        lbl_chacra.pack(padx=15, anchor="w")
        
        self.cmb_chacra = ctk.CTkComboBox(self.frame_form, values=["Cargando chacras..."], width=290, font=("Arial", 13))
        self.cmb_chacra.pack(padx=15, pady=(2, 25))

        # BOTONES DE ACCIÓN
        self.btn_guardar = ctk.CTkButton(self.frame_form, text="GUARDAR / NUEVA", font=("Arial", 13, "bold"), fg_color="#8cb04e", hover_color="#73943c", text_color="black", command=self._guardar_lote)
        self.btn_guardar.pack(fill="x", padx=15, pady=5)

        self.btn_modificar = ctk.CTkButton(self.frame_form, text="APLICAR CAMBIOS", font=("Arial", 13, "bold"), fg_color="#3a7ebf", hover_color="#2b5e8f", command=self._modificar_lote)
        self.btn_modificar.pack(fill="x", padx=15, pady=5)
        self.btn_modificar.configure(state="disabled")

        self.btn_eliminar = ctk.CTkButton(self.frame_form, text="ELIMINAR SELECCIÓN", font=("Arial", 13, "bold"), fg_color="#bf3a3a", hover_color="#8f2b2b", command=self._eliminar_lote)
        self.btn_eliminar.pack(fill="x", padx=15, pady=5)
        self.btn_eliminar.configure(state="disabled")

        self.btn_limpiar = ctk.CTkButton(self.frame_form, text="LIMPIAR FORMULARIO", font=("Arial", 12), fg_color="gray", hover_color="#555555", command=self._limpiar_formulario)
        self.btn_limpiar.pack(fill="x", padx=15, pady=(15, 5))

        # --- DISEÑO DE LA TABLA (Treeview) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("LotesAg.Treeview", font=("Arial", 11), rowheight=30, background="white", fieldbackground="white", foreground="black")
        style.configure("LotesAg.Treeview.Heading", font=("Arial", 12, "bold"), background="#8cb04e", foreground="black", relief="flat")
        style.map("LotesAg.Treeview", background=[("selected", "#b9d291")], foreground=[("selected", "black")])

        columnas = ("id", "loteagrario", "chacra")
        self.tree = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings", style="LotesAg.Treeview")
        
        self.tree.heading("id", text="ID Parcela")
        self.tree.heading("loteagrario", text="Nombre de la Parcela / Lote Agrario")
        self.tree.heading("chacra", text="Chacra Vinculada")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("loteagrario", width=250, anchor="w")
        self.tree.column("chacra", width=250, anchor="w")

        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_fila_seleccionada)

        # Cargar los componentes dinámicos
        self._cargar_combo_chacras()
        self.after(100, self.cargar_lotes_agrarios_db)

    def _cargar_combo_chacras(self):
        """Puebla el combobox de selección con las chacras registradas en el sistema"""
        query = "SELECT idchacra, chacra FROM chacras ORDER BY chacra ASC"
        resultados = self.db.execute_query(query)
        
        self.lista_id_chacras = []
        opciones = []
        
        if resultados:
            for fila in resultados:
                self.lista_id_chacras.append(fila[0])
                opciones.append(fila[1])
            self.cmb_chacra.configure(values=opciones)
            self.cmb_chacra.set(opciones[0])
        else:
            self.cmb_chacra.configure(values=[])
            self.cmb_chacra.set("Sin chacras disponibles")

    def cargar_lotes_agrarios_db(self):
        """Refresca la grilla ejecutando un INNER JOIN para ver el nombre legible de la chacra"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = """
            SELECT loteagrario.id, loteagrario.loteagrario, chacras.chacra 
            FROM loteagrario
            INNER JOIN chacras ON loteagrario.idchacra = chacras.idchacra
            ORDER BY loteagrario.id DESC
        """
        resultados = self.db.execute_query(query)
        
        if resultados:
            for fila in resultados:
                self.tree.insert("", "end", values=(fila[0], fila[1], fila[2]))

    def _on_fila_seleccionada(self, event):
        """Pasa los datos del elemento marcado al formulario"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        
        self.id_lote_seleccionado = valores[0]
        
        self.ent_loteagrario.delete(0, "end")
        self.ent_loteagrario.insert(0, valores[1])
        
        # Sincronizar el combobox con el nombre de la chacra que viene en la grilla
        nombre_chacra_grilla = valores[2]
        opciones_visibles = self.cmb_chacra.cget("values")
        if nombre_chacra_grilla in opciones_visibles:
            self.cmb_chacra.set(nombre_chacra_grilla)

        self.btn_guardar.configure(state="disabled")
        self.btn_modificar.configure(state="normal")
        self.btn_eliminar.configure(state="normal")

    def _limpiar_formulario(self):
        self.id_lote_seleccionado = None
        self.ent_loteagrario.delete(0, "end")
        
        opciones = self.cmb_chacra.cget("values")
        if opciones:
            self.cmb_chacra.set(opciones[0])
            
        self.btn_guardar.configure(state="normal")
        self.btn_modificar.configure(state="disabled")
        self.btn_eliminar.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def _guardar_lote(self):
        nombre = self.ent_loteagrario.get().strip()
        texto_chacra = self.cmb_chacra.get()

        if not nombre or texto_chacra in ["Cargando chacras...", "Sin chacras disponibles", ""]:
            messagebox.showwarning("Campos Incompletos", "Por favor, ingrese el nombre de la parcela y seleccione una chacra madre.")
            return

        try:
            indice = self.cmb_chacra.cget("values").index(texto_chacra)
            id_chacra_real = self.lista_id_chacras[indice]
            
            # Control de Duplicidad: No repetir la misma parcela dentro de la MISMA chacra
            query_check = "SELECT id FROM loteagrario WHERE loteagrario = %s AND idchacra = %s"
            if self.db.execute_query(query_check, (nombre, id_chacra_real)):
                messagebox.showerror("Error de Duplicado", f"La parcela '{nombre}' ya se encuentra registrada bajo esa misma chacra.")
                return

            query_insert = "INSERT INTO loteagrario (loteagrario, idchacra) VALUES (%s, %s)"
            self.db.execute_non_query(query_insert, (nombre, id_chacra_real))
            
            self.cargar_lotes_agrarios_db()
            self._limpiar_formulario()
            messagebox.showinfo("Éxito", "Parcela registrada correctamente.")
            
        except ValueError:
            messagebox.showerror("Error de Mapeo", "Hubo un problema al procesar la chacra seleccionada.")

    def _modificar_lote(self):
        if not self.id_lote_seleccionado:
            return

        nombre = self.ent_loteagrario.get().strip()
        texto_chacra = self.cmb_chacra.get()

        if not nombre:
            messagebox.showwarning("Campos Requeridos", "El nombre de la parcela no puede quedar vacío.")
            return

        try:
            indice = self.cmb_chacra.cget("values").index(texto_chacra)
            id_chacra_real = self.lista_id_chacras[indice]

            query_update = "UPDATE loteagrario SET loteagrario = %s, idchacra = %s WHERE id = %s"
            self.db.execute_non_query(query_update, (nombre, id_chacra_real, self.id_lote_seleccionado))
            
            self.cargar_lotes_agrarios_db()
            self._limpiar_formulario()
            messagebox.showinfo("Éxito", "Los cambios de la parcela fueron guardados correctamente.")
            
        except ValueError:
            messagebox.showerror("Error", "La chacra seleccionada no es válida.")

    def _eliminar_lote(self):
        if not self.id_lote_seleccionado:
            return

        # Restricción de Integridad: No eliminar si ya está vinculada a un pesaje/lote industrial
        query_check_lotes = "SELECT id FROM lotes WHERE idorigen = %s"
        en_uso = self.db.execute_query(query_check_lotes, (self.id_lote_seleccionado,))
        
        if en_uso:
            messagebox.showerror(
                "Cancelado por Seguridad", 
                "Esta parcela no puede ser eliminada debido a que ya cuenta con ingresos de materia prima vinculados en la tabla de Lotes.\n\n"
                "Para preservar la consistencia de auditoría del sistema, la operación fue cancelada."
            )
            return

        confirmar = messagebox.askyesno("Confirmar Baja", "¿Está seguro de eliminar esta parcela del sistema?\nEsta acción es irreversible.")
        if confirmar:
            query_delete = "DELETE FROM loteagrario WHERE id = %s"
            self.db.execute_non_query(query_delete, (self.id_lote_seleccionado,))
            
            self.cargar_lotes_agrarios_db()
            self._limpiar_formulario()
            messagebox.showinfo("Éxito", "Parcela removida del sistema.")