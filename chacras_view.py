# chacras_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox

class ChacrasView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Variable para almacenar el ID seleccionado para modificar/eliminar
        self.id_chacra_seleccionada = None

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="ADMINISTRACIÓN DE CHACRAS / PROPIEDADES", font=("Arial", 20, "bold"), text_color="black")
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- CONTENEDOR PRINCIPAL EN DOS COLUMNAS ---
        self.main_split = ctk.CTkFrame(self, fg_color="transparent")
        self.main_split.pack(fill="both", expand=True, padx=20, pady=10)

        # COLUMNA IZQUIERDA: Formulario de carga/edición
        self.frame_form = ctk.CTkFrame(self.main_split, width=320, fg_color="#f2f5f8", corner_radius=8)
        self.frame_form.pack(side="left", fill="y", padx=(0, 15), pady=5)
        self.frame_form.pack_propagate(False) # Mantiene el ancho fijo

        # COLUMNA DERECHA: Tabla de visualización
        self.frame_tabla = ctk.CTkFrame(self.main_split, fg_color="transparent")
        self.frame_tabla.pack(side="right", fill="both", expand=True, pady=5)

        # --- DISEÑO DEL FORMULARIO (COLUMNA IZQUIERDA) ---
        lbl_form_title = ctk.CTkLabel(self.frame_form, text="Datos de la Chacra", font=("Arial", 14, "bold"), text_color="#4d5433")
        lbl_form_title.pack(pady=(15, 15), padx=15, anchor="w")

        # Campo: Nombre/Identificador
        lbl_nombre = ctk.CTkLabel(self.frame_form, text="Nombre de la Chacra:", font=("Arial", 12, "bold"), text_color="black")
        lbl_nombre.pack(padx=15, anchor="w")
        self.ent_chacra = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13))
        self.ent_chacra.pack(padx=15, pady=(2, 12))

        # Campo: Coordenadas
        lbl_coords = ctk.CTkLabel(self.frame_form, text="Coordenadas (Lat, Lon / Polígono):", font=("Arial", 12, "bold"), text_color="black")
        lbl_coords.pack(padx=15, anchor="w")
        self.ent_coordenadas = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="-27.591, -55.234")
        self.ent_coordenadas.pack(padx=15, pady=(2, 12))

        # --- NUEVO CAMPO: NÚMERO CATASTRAL ---
        lbl_numero = ctk.CTkLabel(self.frame_form, text="Número Catastral:", font=("Arial", 12, "bold"), text_color="black")
        lbl_numero.pack(padx=15, anchor="w")
        self.ent_numero = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13), placeholder_text="Ej: 14-255-A")
        self.ent_numero.pack(padx=15, pady=(2, 12))

        # Campo: Hectáreas
        lbl_has = ctk.CTkLabel(self.frame_form, text="Superficie (Hectáreas):", font=("Arial", 12, "bold"), text_color="black")
        lbl_has.pack(padx=15, anchor="w")
        self.ent_hectareas = ctk.CTkEntry(self.frame_form, width=290, font=("Arial", 13))
        self.ent_hectareas.pack(padx=15, pady=(2, 20))

        # BOTONES DE ACCIÓN DEL FORMULARIO
        self.btn_guardar = ctk.CTkButton(self.frame_form, text="GUARDAR / NUEVA", font=("Arial", 13, "bold"), fg_color="#8cb04e", hover_color="#73943c", text_color="black", command=self._guardar_chacra)
        self.btn_guardar.pack(fill="x", padx=15, pady=5)

        self.btn_modificar = ctk.CTkButton(self.frame_form, text="APLICAR CAMBIOS", font=("Arial", 13, "bold"), fg_color="#3a7ebf", hover_color="#2b5e8f", command=self._modificar_chacra)
        self.btn_modificar.pack(fill="x", padx=15, pady=5)
        self.btn_modificar.configure(state="disabled") # Se habilita al seleccionar una fila

        self.btn_eliminar = ctk.CTkButton(self.frame_form, text="ELIMINAR SELECCIÓN", font=("Arial", 13, "bold"), fg_color="#bf3a3a", hover_color="#8f2b2b", command=self._eliminar_chacra)
        self.btn_eliminar.pack(fill="x", padx=15, pady=5)
        self.btn_eliminar.configure(state="disabled")

        self.btn_limpiar = ctk.CTkButton(self.frame_form, text="LIMPIAR FORMULARIO", font=("Arial", 12), fg_color="gray", hover_color="#555555", command=self._limpiar_formulario)
        self.btn_limpiar.pack(fill="x", padx=15, pady=(15, 5))


        # --- DISEÑO DE LA TABLA (COLUMNA DERECHA) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Chacras.Treeview", font=("Arial", 11), rowheight=30, background="white", fieldbackground="white", foreground="black")
        style.configure("Chacras.Treeview.Heading", font=("Arial", 12, "bold"), background="#8cb04e", foreground="black", relief="flat")
        style.map("Chacras.Treeview", background=[("selected", "#b9d291")], foreground=[("selected", "black")])

        # Definición de columnas y cabeceras
        columnas = ("id", "chacra", "coordenadas", "numero", "hectareas")
        self.tree = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings", style="Chacras.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("chacra", text="Chacra / Establecimiento")
        self.tree.heading("coordenadas", text="Ubicación / Coordenadas")
        self.tree.heading("numero", text="Nº Catastral")
        self.tree.heading("hectareas", text="Hectáreas")

        # Ancho y alineaciones de las columnas
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("chacra", width=220, anchor="w")
        self.tree.column("coordenadas", width=140, anchor="center")
        self.tree.column("numero", width=120, anchor="center")
        self.tree.column("hectareas", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_fila_seleccionada)

        # Cargar los datos iniciales de la Base de Datos de manera segura
        self.after(100, self.cargar_chacras_db)

    def cargar_chacras_db(self):
        """Refresca y vuelca las chacras desde MariaDB a la tabla Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = "SELECT idchacra, chacra, coordenadas, numero, hectareas FROM chacras ORDER BY idchacra DESC"
        resultados = self.db.execute_query(query)
        
        if resultados:
            for fila in resultados:
                coords_visibles = fila[2] if fila[2] else "Sin registrar"
                num_catastral = fila[3] if fila[3] else "Sin registrar"
                has_visibles = fila[4] if fila[4] is not None else 0.0
                
                self.tree.insert("", "end", values=(
                    fila[0], fila[1], coords_visibles, num_catastral, f"{has_visibles:.2f} Has"
                ))

    def _on_fila_seleccionada(self, event):
        """Pasa los datos de la fila marcada al formulario de edición"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        
        self.id_chacra_seleccionada = valores[0]
        
        # Limpiamos y rellenamos el nombre
        self.ent_chacra.delete(0, "end")
        self.ent_chacra.insert(0, valores[1])
        
        # Limpiamos y rellenamos coordenadas
        self.ent_coordenadas.delete(0, "end")
        texto_coords = valores[2] if valores[2] != "Sin registrar" else ""
        self.ent_coordenadas.insert(0, texto_coords)
        
        # Limpiamos y rellenamos número catastral
        self.ent_numero.delete(0, "end")
        texto_num = valores[3] if valores[3] != "Sin registrar" else ""
        self.ent_numero.insert(0, texto_num)
        
        # Limpiamos y rellenamos hectáreas
        self.ent_hectareas.delete(0, "end")
        texto_has = str(valores[4]).replace(" Has", "")
        self.ent_hectareas.insert(0, texto_has)

        # Habilitamos botones de edición
        self.btn_guardar.configure(state="disabled")
        self.btn_modificar.configure(state="normal")
        self.btn_eliminar.configure(state="normal")

    def _limpiar_formulario(self):
        """Resetea los campos y el estado de los botones"""
        self.id_chacra_seleccionada = None
        self.ent_chacra.delete(0, "end")
        self.ent_coordenadas.delete(0, "end")
        self.ent_numero.delete(0, "end")
        self.ent_hectareas.delete(0, "end")
        
        self.btn_guardar.configure(state="normal")
        self.btn_modificar.configure(state="disabled")
        self.btn_eliminar.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def _guardar_chacra(self):
        """Inserta una nueva chacra validando duplicados e integridad"""
        nombre = self.ent_chacra.get().strip()
        coords = self.ent_coordenadas.get().strip()
        num_catastro = self.ent_numero.get().strip()
        has_str = self.ent_hectareas.get().strip()

        if not nombre or not has_str:
            messagebox.showwarning("Campos Requeridos", "Debe ingresar obligatoriamente el Nombre de la chacra y su Superficie.")
            return

        try:
            hectareas = float(has_str)
        except ValueError:
            messagebox.showwarning("Dato Incorrecto", "Las hectáreas deben ser un número válido (ejemplo: 45.5 o 12).")
            return

        query_check = "SELECT idchacra FROM chacras WHERE chacra = %s"
        if self.db.execute_query(query_check, (nombre,)):
            messagebox.showerror("Error de Duplicado", f"Ya existe una chacra registrada con el nombre '{nombre}'.")
            return

        query_insert = "INSERT INTO chacras (chacra, coordenadas, numero, hectareas) VALUES (%s, %s, %s, %s)"
        self.db.execute_non_query(query_insert, (nombre, coords if coords else None, num_catastro if num_catastro else None, hectareas))
        
        self.cargar_chacras_db()
        self._limpiar_formulario()
        messagebox.showinfo("Éxito", "Chacra registrada correctamente en el sistema.")

    def _modificar_chacra(self):
        """Actualiza los datos de la chacra seleccionada con el orden de tupla correcto"""
        if not self.id_chacra_seleccionada:
            return

        nombre = self.ent_chacra.get().strip()
        coords = self.ent_coordenadas.get().strip()
        num_catastro = self.ent_numero.get().strip()
        has_str = self.ent_hectareas.get().strip()

        if not nombre or not has_str:
            messagebox.showwarning("Campos Requeridos", "El nombre y las hectáreas no pueden quedar vacíos.")
            return

        try:
            hectareas = float(has_str)
        except ValueError:
            messagebox.showwarning("Dato Incorrecto", "Las hectáreas deben ser un número válido.")
            return

        # Consulta SQL armada
        query_update = "UPDATE chacras SET chacra = %s, coordenadas = %s, numero = %s, hectareas = %s WHERE idchacra = %s"
        
        # Tupla ordenada estrictamente igual a los %s del UPDATE
        parametros = (nombre, coords if coords else None, num_catastro if num_catastro else None, hectareas, self.id_chacra_seleccionada)
        
        self.db.execute_non_query(query_update, parametros)
        
        self.cargar_chacras_db()
        self._limpiar_formulario()
        messagebox.showinfo("Éxito", "Los cambios de la chacra fueron guardados correctamente.")

    def _eliminar_chacra(self):
        """Elimina de forma física una chacra si no está enlazada a un lote activo"""
        if not self.id_chacra_seleccionada:
            return

        query_trazabilidad = "SELECT id FROM loteagrario WHERE idchacra = %s"
        asociados = self.db.execute_query(query_trazabilidad, (self.id_chacra_seleccionada,))
        
        if asociados:
            messagebox.showerror(
                "Restricción de Integridad", 
                "No se puede eliminar esta chacra porque ya cuenta con lotes agrarios o de pesajes históricos asociados.\n\n"
                "Para resguardar la trazabilidad de la materia prima, la operación fue cancelada."
            )
            return

        confirmar = messagebox.askyesno("Confirmar Eliminación", "¿Está completamente seguro de eliminar esta chacra del sistema?\nEsta acción no se puede deshacer.")
        if confirmar:
            query_delete = "DELETE FROM chacras WHERE idchacra = %s"
            self.db.execute_non_query(query_delete, (self.id_chacra_seleccionada,))
            
            self.cargar_chacras_db()
            self._limpiar_formulario()
            messagebox.showinfo("Éxito", "Chacra removida del sistema.")