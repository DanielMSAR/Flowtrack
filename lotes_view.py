# lotes_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox  # Importamos messagebox para las advertencias visuales
from datetime import datetime

class LotesView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Estructura de control para mapear el texto del Combo con el ID real de la DB
        self.lista_id_origenes = []

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="GESTIÓN Y TRAZABILIDAD DE LOTES", font=("Arial", 20, "bold"), text_color="black")
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- SECCIÓN SUPERIOR: TABLA DE LOTES ---
        self.tabla_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tabla_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Configuración del estilo del Treeview para que combine con CustomTkinter (verde/gris)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 11), rowheight=30, background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#8cb04e", foreground="black", relief="flat")
        style.map("Treeview", background=[("selected", "#b9d291")], foreground=[("selected", "black")])

        # Columnas de la grilla
        columnas = ("id", "fechainicio", "lote", "kgsingreso", "procedencia", "procesado", "kgsprocesado", "envasado", "kgsenv")
        self.tree = ttk.Treeview(self.tabla_frame, columns=columnas, show="headings")
        
        # Encabezados
        self.tree.heading("id", text="ID")
        self.tree.heading("fechainicio", text="Fecha Inicio")
        self.tree.heading("lote", text="Nº Lote")
        self.tree.heading("kgsingreso", text="Kgs Ingreso")
        self.tree.heading("procedencia", text="Origen Agrario (Chacra)")
        self.tree.heading("procesado", text="¿Proc?")
        self.tree.heading("kgsprocesado", text="Kgs Proc.")
        self.tree.heading("envasado", text="¿Env?")
        self.tree.heading("kgsenv", text="Kgs Env.")

        # Anchos de columna
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("fechainicio", width=120, anchor="center")
        self.tree.column("lote", width=100, anchor="center")
        self.tree.column("kgsingreso", width=100, anchor="e")
        self.tree.column("procedencia", width=200, anchor="w")
        self.tree.column("procesado", width=60, anchor="center")
        self.tree.column("kgsprocesado", width=100, anchor="e")
        self.tree.column("envasado", width=60, anchor="center")
        self.tree.column("kgsenv", width=100, anchor="e")

        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Evento al seleccionar una fila
        self.tree.bind("<<TreeviewSelect>>", self._on_lote_seleccionado)

        # --- SECCIÓN INFERIOR: PANEL DE PESTAÑAS (TABS) ---
        self.tabs = ctk.CTkTabview(self, height=320, command=self._on_tab_change)
        self.tabs.pack(fill="x", padx=20, pady=(10, 20))

        # Crear las 3 pestañas del ciclo de vida
        self.tab_ingreso = self.tabs.add("1. Ingreso / Alta")
        self.tab_procesado = self.tabs.add("2. Procesamiento")
        self.tab_envasado = self.tabs.add("3. Envasado")

        self._crear_formulario_ingreso()
        self._crear_formulario_procesado()
        self._crear_formulario_envasado()

        # CORREGIDO: Esperamos 100ms a que todo Tkinter esté montado en pantalla y cargamos la DB de golpe
        self.after(100, self._inicializar_datos_db)

    def _inicializar_datos_db(self):
        """Ejecuta las consultas de base de datos de forma segura post-renderizado"""
        self._cargar_origenes_agrarios()
        self.cargar_lotes_db()

    def _crear_formulario_ingreso(self):
        """Pestaña 1: Creación de un lote nuevo con combo relacional"""
        lbl_lote = ctk.CTkLabel(self.tab_ingreso, text="Código / Nombre Lote:", font=("Arial", 14, "bold"))
        lbl_lote.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.ent_lote = ctk.CTkEntry(self.tab_ingreso, width=200, font=("Arial", 14))
        self.ent_lote.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        lbl_kgs = ctk.CTkLabel(self.tab_ingreso, text="Kilogramos Ingreso:", font=("Arial", 14, "bold"))
        lbl_kgs.grid(row=0, column=2, padx=20, pady=10, sticky="w")
        self.ent_kgs_ingreso = ctk.CTkEntry(self.tab_ingreso, width=150, font=("Arial", 14))
        self.ent_kgs_ingreso.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        lbl_origen = ctk.CTkLabel(self.tab_ingreso, text="Origen Agrario / Chacra:", font=("Arial", 14, "bold"))
        lbl_origen.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        self.cmb_origen = ctk.CTkComboBox(self.tab_ingreso, values=["Cargando orígenes..."], width=360, font=("Arial", 13))
        self.cmb_origen.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self.btn_guardar_lote = ctk.CTkButton(self.tab_ingreso, text="CREAR LOTE", font=("Arial", 14, "bold"), height=40, command=self._guardar_nuevo_lote)
        self.btn_guardar_lote.grid(row=2, column=0, columnspan=4, pady=20, padx=20, sticky="ew")

    def _cargar_origenes_agrarios(self):
        """Ejecuta el INNER JOIN dinámico para poblar el combo de orígenes agrarios y chacras"""
        query = """
            SELECT loteagrario.id, loteagrario.loteagrario, chacras.chacra
            FROM loteagrario
            INNER JOIN chacras ON loteagrario.idchacra = chacras.idchacra
            ORDER BY loteagrario.loteagrario ASC
        """
        resultados = self.db.execute_query(query)
        
        self.lista_id_origenes = []
        opciones_combo = []
        
        if resultados:
            for fila in resultados:
                id_orig = fila[0]
                nom_lote = fila[1]
                nom_chacra = fila[2]
                
                self.lista_id_origenes.append(id_orig)
                opciones_combo.append(f"{nom_lote} ({nom_chacra})")
        
        if opciones_combo:
            self.cmb_origen.configure(values=opciones_combo)
            self.cmb_origen.set(opciones_combo[0])
        else:
            self.cmb_origen.configure(values=["Sin orígenes agrarios"])
            self.cmb_origen.set("Sin orígenes agrarios")

    def _crear_formulario_procesado(self):
        """Pestaña 2: Información del procesado del lote"""
        lbl_kgs_p = ctk.CTkLabel(self.tab_procesado, text="Kgs Procesados:", font=("Arial", 14, "bold"))
        lbl_kgs_p.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.ent_kgs_proc = ctk.CTkEntry(self.tab_procesado, width=150, font=("Arial", 14))
        self.ent_kgs_proc.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        lbl_calidad = ctk.CTkLabel(self.tab_procesado, text="Calidad:", font=("Arial", 14, "bold"))
        lbl_calidad.grid(row=0, column=2, padx=20, pady=10, sticky="w")
        self.cmb_calidad = ctk.CTkComboBox(self.tab_procesado, values=["1 - Primera", "2 - Segunda", "3 - Residuo"], width=180)
        self.cmb_calidad.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        lbl_ope_p = ctk.CTkLabel(self.tab_procesado, text="Operario Proc.:", font=("Arial", 14, "bold"))
        lbl_ope_p.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.cmb_operario_proc = ctk.CTkComboBox(self.tab_procesado, values=["101 - Juan Perez", "102 - Ramon Silva"], width=200)
        self.cmb_operario_proc.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.chk_procesado = ctk.CTkCheckBox(self.tab_procesado, text="PROCESADO COMPLETADO", font=("Arial", 14, "bold"))
        self.chk_procesado.grid(row=1, column=2, columnspan=2, padx=20, pady=10, sticky="w")

        self.btn_guardar_proc = ctk.CTkButton(self.tab_procesado, text="REGISTRAR PROCESAMIENTO", fg_color="#4d5433", hover_color="#393e26", font=("Arial", 14, "bold"), height=40, command=self._guardar_procesado)
        self.btn_guardar_proc.grid(row=2, column=0, columnspan=4, pady=20, padx=20, sticky="ew")

    def _crear_formulario_envasado(self):
        """Pestaña 3: Información del envasado final"""
        lbl_kgs_e = ctk.CTkLabel(self.tab_envasado, text="Kgs Envasados:", font=("Arial", 14, "bold"))
        lbl_kgs_e.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.ent_kgs_env = ctk.CTkEntry(self.tab_envasado, width=150, font=("Arial", 14))
        self.ent_kgs_env.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        lbl_envase = ctk.CTkLabel(self.tab_envasado, text="Tipo Envase:", font=("Arial", 14, "bold"))
        lbl_envase.grid(row=0, column=2, padx=20, pady=10, sticky="w")
        self.cmb_envase = ctk.CTkComboBox(self.tab_envasado, values=["1 - Bolsa 25kg", "2 - BigBag 500kg"], width=180)
        self.cmb_envase.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        lbl_ope_e = ctk.CTkLabel(self.tab_envasado, text="Operario Env.:", font=("Arial", 14, "bold"))
        lbl_ope_e.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.cmb_operario_env = ctk.CTkComboBox(self.tab_envasado, values=["101 - Juan Perez", "103 - Carlos Gomez"], width=200)
        self.cmb_operario_env.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.chk_envasado = ctk.CTkCheckBox(self.tab_envasado, text="ENVASADO COMPLETADO", font=("Arial", 14, "bold"))
        self.chk_envasado.grid(row=1, column=2, columnspan=2, padx=20, pady=10, sticky="w")

        self.btn_guardar_env = ctk.CTkButton(self.tab_envasado, text="REGISTRAR ENVASADO", fg_color="#4d5433", hover_color="#393e26", font=("Arial", 14, "bold"), height=40, command=self._guardar_envasado)
        self.btn_guardar_env.grid(row=2, column=0, columnspan=4, pady=20, padx=20, sticky="ew")

    def cargar_lotes_db(self):
        """Trae los registros combinando la procedencia agrícola con LEFT JOIN"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = """
            SELECT 
                lotes.id, lotes.fechainicio, lotes.lote, lotes.kgsingreso, 
                CONCAT(loteagrario.loteagrario, ' (', chacras.chacra, ')') AS procedencia,
                lotes.procesado, lotes.kgsprocesado, lotes.envasado, lotes.kgsenv 
            FROM lotes
            LEFT JOIN loteagrario ON lotes.idorigen = loteagrario.id
            LEFT JOIN chacras ON loteagrario.idchacra = chacras.idchacra
            ORDER BY lotes.id DESC
        """
        resultados = self.db.execute_query(query)
        
        if resultados:
            for fila in resultados:
                proc_status = "SI" if fila[5] == 1 else "NO"
                env_status = "SI" if fila[7] == 1 else "NO"
                
                origen_visible = fila[4] if fila[4] is not None else "Sin Especificar"
                
                self.tree.insert("", "end", values=(
                    fila[0], fila[1], fila[2], fila[3], origen_visible, proc_status, fila[6], env_status, fila[8]
                ))

    def _on_lote_seleccionado(self, event):
        """Se ejecuta al hacer clic en un lote; lee idorigen y posiciona el combo de forma segura"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        id_lote = valores[0]
        
        query = "SELECT lote, kgsingreso, kgsprocesado, idcalidad, operarioproc, procesado, kgsenv, idenvase, operarioenv, envasado, idorigen FROM lotes WHERE id = %s"
        res = self.db.execute_query(query, (id_lote,))
        
        if res:
            lote, kgs_in, kgs_pr, id_cal, op_pr, proc, kgs_en, id_en, op_en, env, id_origen = res[0]
            
            # CONTROL DE NULOS: Si vienen de la DB como None, los convertimos a string vacío o 0
            lote = lote if lote is not None else ""
            kgs_in = kgs_in if kgs_in is not None else ""
            kgs_pr = kgs_pr if kgs_pr is not None else ""
            kgs_en = kgs_en if kgs_en is not None else ""
            
            # 1. Cargar Pestaña Ingreso
            self.ent_lote.delete(0, "end")
            self.ent_lote.insert(0, str(lote))
            
            self.ent_kgs_ingreso.delete(0, "end")
            self.ent_kgs_ingreso.insert(0, str(kgs_in))
            
            if id_origen in self.lista_id_origenes:
                idx = self.lista_id_origenes.index(id_origen)
                texto_combo = self.cmb_origen.cget("values")[idx]
                self.cmb_origen.set(texto_combo)
            else:
                if self.cmb_origen.cget("values"):
                    self.cmb_origen.set(self.cmb_origen.cget("values")[0])
            
            # 2. Cargar Pestaña Procesado (Ahora blindada contra None)
            self.ent_kgs_proc.delete(0, "end")
            self.ent_kgs_proc.insert(0, str(kgs_pr))
            
            if proc == 1: 
                self.chk_procesado.select() 
            else: 
                self.chk_procesado.deselect()
            
            # 3. Cargar Pestaña Envasado (Ahora blindada contra None)
            self.ent_kgs_env.delete(0, "end")
            self.ent_kgs_env.insert(0, str(kgs_en))
            
            if env == 1: 
                self.chk_envasado.select() 
            else: 
                self.chk_envasado.deselect()
    def _on_tab_change(self):
        """Evita el cambio de solapa y lanza una advertencia visual si no se seleccionó un lote"""
        seleccion = self.tree.selection()
        current_tab = self.tabs.get()
        
        if current_tab in ["2. Procesamiento", "3. Envasado"] and not seleccion:
            self.tabs.set("1. Ingreso / Alta")
            messagebox.showwarning(
                "Atención - FlowTrack",
                "Debe seleccionar un lote activo de la lista superior para poder registrar su Procesamiento o Envasado."
            )

    def _guardar_nuevo_lote(self):
        """Inserta el lote incluyendo el idorigen obtenido del mapeo del combo y valida duplicados"""
        lote_cod = self.ent_lote.get().strip()  # .strip() elimina espacios vacíos accidentales al inicio/final
        kgs = self.ent_kgs_ingreso.get()
        texto_origen = self.cmb_origen.get()
        
        # 1. Validación de campos básicos
        if not lote_cod or not kgs.isdigit() or texto_origen in ["Cargando orígenes...", "Sin orígenes agrarios", ""]:
            messagebox.showwarning("Campos Incompletos", "Por favor complete el nombre del lote, kilogramos válidos y seleccione un origen válido.")
            return

        # 2. CONTROL DE DUPLICADOS: Verificar si el lote ya existe en MariaDB
        query_verificar = "SELECT id FROM lotes WHERE lote = %s"
        existe = self.db.execute_query(query_verificar, (lote_cod,))
        
        if existe:
            messagebox.showerror(
                "Lote Duplicado - FlowTrack", 
                f"El Nº de Lote '{lote_cod}' ya se encuentra registrado en el sistema.\n\nPor favor, verifique el código e ingrese uno diferente."
            )
            return

        try:
            indice = self.cmb_origen.cget("values").index(texto_origen)
            id_origen_real = self.lista_id_origenes[indice]
            
            # 3. Inserción segura si pasó los controles
            query_insertar = "INSERT INTO lotes (lote, kgsingreso, idorigen) VALUES (%s, %s, %s)"
            self.db.non_query_result = self.db.execute_non_query(query_insertar, (lote_cod, int(kgs), id_origen_real))
            
            # Limpieza de campos y actualización de la grilla
            self.cargar_lotes_db()
            self.ent_lote.delete(0, "end")
            self.ent_kgs_ingreso.delete(0, "end")
            
            messagebox.showinfo("Éxito", f"Lote '{lote_cod}' creado correctamente con su procedencia agrícola.")
            print("Lote creado correctamente con procedencia agrícola.")
            
        except ValueError:
            messagebox.showerror("Error de Mapeo", "El origen agrario seleccionado no es válido o las tablas se encuentran vacías.")
            
    def _guardar_procesado(self):
        """Actualizada validación visual al guardar la etapa de Procesamiento"""
        seleccion = self.tree.selection()
        if not seleccion: 
            messagebox.showerror("Error de Selection", "No hay ningún lote seleccionado en la grilla para procesar.")
            return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        kgs_proc = self.ent_kgs_proc.get()
        is_proc = 1 if self.chk_procesado.get() == 1 else 0
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if kgs_proc.isdigit():
            query = """UPDATE lotes SET kgsprocesado = %s, fechaprocesado = %s, 
                       operarioproc = 101, idcalidad = 1, procesado = %s WHERE id = %s"""
            self.db.execute_non_query(query, (int(kgs_proc), fecha_actual, is_proc, id_lote))
            self.cargar_lotes_db()
            messagebox.showinfo("Éxito", "El procesamiento del lote fue registrado correctamente.")
        else:
            messagebox.showwarning("Datos Inválidos", "Por favor ingrese un valor numérico para los kilogramos procesados.")

    def _guardar_envasado(self):
        """Actualizada validación visual al guardar la etapa final de Envasado"""
        seleccion = self.tree.selection()
        if not seleccion: 
            messagebox.showerror("Error de Selección", "No hay ningún lote seleccionado en la grilla para envasar.")
            return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        kgs_env = self.ent_kgs_env.get()
        is_env = 1 if self.chk_envasado.get() == 1 else 0
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if kgs_env.isdigit():
            query = """UPDATE lotes SET kgsenv = %s, fechaenv = %s, 
                       operarioenv = 101, idenvase = 1, envasado = %s WHERE id = %s"""
            self.db.execute_non_query(query, (int(kgs_env), fecha_actual, is_env, id_lote))
            self.cargar_lotes_db()
            messagebox.showinfo("Éxito", "El envasado final del lote fue registrado correctamente.")
        else:
            messagebox.showwarning("Datos Inválidos", "Por favor ingrese un valor numérico para los kilogramos envasados.")