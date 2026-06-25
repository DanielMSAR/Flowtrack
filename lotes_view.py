# lotes_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class LotesView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        self.lista_id_origenes = []

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="GESTIÓN Y TRAZABILIDAD DE LOTES", font=("Arial", 20, "bold"), text_color="black")
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- SECCIÓN SUPERIOR: TABLA DE LOTES ---
        self.tabla_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tabla_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 11), rowheight=30, background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#8cb04e", foreground="black", relief="flat")
        style.map("Treeview", background=[("selected", "#b9d291")], foreground=[("selected", "black")])

        # Definición exacta de columnas incluyendo los nuevos tiempos medidos
        columnas = ("id", "fechainicio", "lote", "kgsingreso", "procedencia", "procesado", "tiempo_proc", "kgsprocesado", "envasado", "tiempo_env", "kgsenv")
        self.tree = ttk.Treeview(self.tabla_frame, columns=columnas, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("fechainicio", text="Fecha Inicio")
        self.tree.heading("lote", text="Nº Lote")
        self.tree.heading("kgsingreso", text="Kgs Verde")
        self.tree.heading("procedencia", text="Origen (Chacra)")
        self.tree.heading("procesado", text="¿Proc?")
        self.tree.heading("tiempo_proc", text="Tiempo Proc.")
        self.tree.heading("kgsprocesado", text="Kgs Proc.")
        self.tree.heading("envasado", text="¿Env?")
        self.tree.heading("tiempo_env", text="Tiempo Env.")
        self.tree.heading("kgsenv", text="Kgs Env.")

        # Ajuste proporcional de anchos de columna para que entre todo cómodo en pantalla
        self.tree.column("id", width=30, anchor="center")
        self.tree.column("fechainicio", width=130, anchor="center")
        self.tree.column("lote", width=90, anchor="center")
        self.tree.column("kgsingreso", width=90, anchor="e")
        self.tree.column("procedencia", width=180, anchor="w")
        self.tree.column("procesado", width=60, anchor="center")
        self.tree.column("tiempo_proc", width=110, anchor="center")
        self.tree.column("kgsprocesado", width=90, anchor="e")
        self.tree.column("envasado", width=60, anchor="center")
        self.tree.column("tiempo_env", width=110, anchor="center")
        self.tree.column("kgsenv", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_lote_seleccionado)

        # --- SECCIÓN INFERIOR: PANEL DE PESTAÑAS (TABS) ---
        self.tabs = ctk.CTkTabview(self, height=320, command=self._on_tab_change)
        self.tabs.pack(fill="x", padx=20, pady=(10, 20))

        self.tab_ingreso = self.tabs.add("1. Cultivo / Ingreso")
        self.tab_procesado = self.tabs.add("2. Procesamiento")
        self.tab_envasado = self.tabs.add("3. Envasado")

        # Listas de horas y minutos para los combos bloqueados
        self.horas_validas = [f"{i:02d}" for i in range(24)]
        self.minutos_validas = [f"{i:02d}" for i in range(60)]

        self._crear_formulario_ingreso()
        self._crear_formulario_procesado()
        self._crear_formulario_envasado()

        self.after(100, self._inicializar_datos_db)

    def _inicializar_datos_db(self):
        self._cargar_origenes_agrarios()
        self.cargar_lotes_db()
        self._setear_tiempos_actuales()

    def _setear_tiempos_actuales(self):
        """Pre-carga los controles con la fecha de hoy en DD-MM-YYYY y hora/minutos actuales"""
        ahora = datetime.now()
        fecha_hoy_ar = ahora.strftime('%d-%m-%Y')
        hora_actual = ahora.strftime('%H')
        minuto_actual = ahora.strftime('%M')

        # Pestaña 1
        self.ent_fecha_ingreso.delete(0, "end")
        self.ent_fecha_ingreso.insert(0, fecha_hoy_ar)
        self.cmb_hora_ingreso.set(hora_actual)
        self.cmb_min_ingreso.set(minuto_actual)
        
        # Pestaña 2
        self.ent_fecha_proc.delete(0, "end")
        self.ent_fecha_proc.insert(0, fecha_hoy_ar)
        self.cmb_hora_proc.set(hora_actual)
        self.cmb_min_proc.set(minuto_actual)
        
        # Pestaña 3
        self.ent_fecha_env.delete(0, "end")
        self.ent_fecha_env.insert(0, fecha_hoy_ar)
        self.cmb_hora_env.set(hora_actual)
        self.cmb_min_env.set(minuto_actual)

    def _convertir_a_sql(self, fecha_ar, hora, minuto):
        """Pasa de DD-MM-YYYY HH:MM a formato ISO para MariaDB. Si falla devuelve None"""
        try:
            dt = datetime.strptime(f"{fecha_ar} {hora}:{minuto}:00", '%d-%m-%Y %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

    def _formatear_delta_tiempo(self, inicio, fin):
        """Calcula de forma exacta el tiempo transcurrido entre dos datetimes"""
        if not inicio or not fin or not isinstance(inicio, datetime) or not isinstance(fin, datetime):
            return "-"
        
        diff = fin - inicio
        dias = diff.days
        horas, residuo = divmod(diff.seconds, 3600)
        minutos, _ = divmod(residuo, 60)
        
        if dias > 0:
            return f"{dias}d {horas}h {minutos}m"
        elif horas > 0:
            return f"{horas}h {minutos}m"
        else:
            return f"{minutos}m"

    def _crear_formulario_ingreso(self):
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
        
        self.cmb_origen = ctk.CTkComboBox(self.tab_ingreso, values=["Cargando orígenes..."], width=320, font=("Arial", 13))
        self.cmb_origen.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # CONTENEDOR DE TIEMPO BLINDADO (Ingreso)
        frame_time = ctk.CTkFrame(self.tab_ingreso, fg_color="transparent")
        frame_time.grid(row=1, column=3, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(frame_time, text="Fecha:", font=("Arial", 13, "bold")).pack(side="left", padx=2)
        self.ent_fecha_ingreso = ctk.CTkEntry(frame_time, width=105, font=("Arial", 13), placeholder_text="DD-MM-YYYY")
        self.ent_fecha_ingreso.pack(side="left", padx=5)

        ctk.CTkLabel(frame_time, text="Hora:", font=("Arial", 13, "bold")).pack(side="left", padx=(8, 2))
        self.cmb_hora_ingreso = ctk.CTkComboBox(frame_time, values=self.horas_validas, width=65, state="readonly")
        self.cmb_hora_ingreso.pack(side="left", padx=2)

        ctk.CTkLabel(frame_time, text="Min:", font=("Arial", 13, "bold")).pack(side="left", padx=(5, 2))
        self.cmb_min_ingreso = ctk.CTkComboBox(frame_time, values=self.minutos_validas, width=65, state="readonly")
        self.cmb_min_ingreso.pack(side="left", padx=2)

        # DISTRIBUCIÓN PARALELA DE BOTONES OPERATIVOS
        self.btn_guardar_lote = ctk.CTkButton(self.tab_ingreso, text="CREAR LOTE", font=("Arial", 14, "bold"), height=40, command=self._guardar_nuevo_lote)
        self.btn_guardar_lote.grid(row=2, column=0, columnspan=2, pady=20, padx=20, sticky="ew")

        self.btn_imprimir_lote = ctk.CTkButton(self.tab_ingreso, text="🖨️ IMPRIMIR DETALLE", fg_color="#2b5c8f", hover_color="#1f4268", font=("Arial", 14, "bold"), height=40, command=self._imprimir_detalle_lote)
        self.btn_imprimir_lote.grid(row=2, column=2, columnspan=3, pady=20, padx=20, sticky="ew")

    def _cargar_origenes_agrarios(self):
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
                self.lista_id_origenes.append(fila[0])
                opciones_combo.append(f"{fila[1]} ({fila[2]})")
        
        if opciones_combo:
            self.cmb_origen.configure(values=opciones_combo)
            self.cmb_origen.set(opciones_combo[0])
        else:
            self.cmb_origen.configure(values=["Sin orígenes agrarios"])
            self.cmb_origen.set("Sin orígenes agrarios")

    def _crear_formulario_procesado(self):
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

        # CONTENEDOR DE TIEMPO BLINDADO (Procesado)
        frame_time_p = ctk.CTkFrame(self.tab_procesado, fg_color="transparent")
        frame_time_p.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(frame_time_p, text="Fecha:", font=("Arial", 13, "bold")).pack(side="left", padx=2)
        self.ent_fecha_proc = ctk.CTkEntry(frame_time_p, width=105, font=("Arial", 13), placeholder_text="DD-MM-YYYY")
        self.ent_fecha_proc.pack(side="left", padx=5)

        ctk.CTkLabel(frame_time_p, text="Hora:", font=("Arial", 13, "bold")).pack(side="left", padx=(8, 2))
        self.cmb_hora_proc = ctk.CTkComboBox(frame_time_p, values=self.horas_validas, width=65, state="readonly")
        self.cmb_hora_proc.pack(side="left", padx=2)

        ctk.CTkLabel(frame_time_p, text="Min:", font=("Arial", 13, "bold")).pack(side="left", padx=(5, 2))
        self.cmb_min_proc = ctk.CTkComboBox(frame_time_p, values=self.minutos_validas, width=65, state="readonly")
        self.cmb_min_proc.pack(side="left", padx=2)

        self.chk_procesado = ctk.CTkCheckBox(self.tab_procesado, text="PROCESADO COMPLETADO", font=("Arial", 14, "bold"))
        self.chk_procesado.grid(row=1, column=4, padx=20, pady=10, sticky="w")

        self.btn_guardar_proc = ctk.CTkButton(self.tab_procesado, text="REGISTRAR PROCESAMIENTO", fg_color="#4d5433", hover_color="#393e26", font=("Arial", 14, "bold"), height=40, command=self._guardar_procesado)
        self.btn_guardar_proc.grid(row=2, column=0, columnspan=5, pady=20, padx=20, sticky="ew")

    def _crear_formulario_envasado(self):
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

        # CONTENEDOR DE TIEMPO BLINDADO (Envasado)
        frame_time_e = ctk.CTkFrame(self.tab_envasado, fg_color="transparent")
        frame_time_e.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(frame_time_e, text="Fecha:", font=("Arial", 13, "bold")).pack(side="left", padx=2)
        self.ent_fecha_env = ctk.CTkEntry(frame_time_e, width=105, font=("Arial", 13), placeholder_text="DD-MM-YYYY")
        self.ent_fecha_env.pack(side="left", padx=5)

        ctk.CTkLabel(frame_time_e, text="Hora:", font=("Arial", 13, "bold")).pack(side="left", padx=(8, 2))
        self.cmb_hora_env = ctk.CTkComboBox(frame_time_e, values=self.horas_validas, width=65, state="readonly")
        self.cmb_hora_env.pack(side="left", padx=2)

        ctk.CTkLabel(frame_time_e, text="Min:", font=("Arial", 13, "bold")).pack(side="left", padx=(5, 2))
        self.cmb_min_env = ctk.CTkComboBox(frame_time_e, values=self.minutos_validas, width=65, state="readonly")
        self.cmb_min_env.pack(side="left", padx=2)

        self.chk_envasado = ctk.CTkCheckBox(self.tab_envasado, text="ENVASADO COMPLETADO", font=("Arial", 14, "bold"))
        self.chk_envasado.grid(row=1, column=4, padx=20, pady=10, sticky="w")

        self.btn_guardar_env = ctk.CTkButton(self.tab_envasado, text="REGISTRAR ENVASADO", fg_color="#4d5433", hover_color="#393e26", font=("Arial", 14, "bold"), height=40, command=self._guardar_envasado)
        self.btn_guardar_env.grid(row=2, column=0, columnspan=5, pady=20, padx=20, sticky="ew")

    def cargar_lotes_db(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = """
            SELECT lotes.id, lotes.fechainicio, lotes.lote, lotes.kgsingreso, 
                   CONCAT(loteagrario.loteagrario, ' (', chacras.chacra, ')') AS procedencia,
                   lotes.procesado, lotes.kgsprocesado, lotes.envasado, lotes.kgsenv,
                   lotes.fechaprocesado, lotes.fechaenv
            FROM lotes
            LEFT JOIN loteagrario ON lotes.idorigen = loteagrario.id
            LEFT JOIN chacras ON loteagrario.idchacra = chacras.idchacra
            ORDER BY lotes.id DESC
        """
        resultados = self.db.execute_query(query)
        
        if resultados:
            for fila in resultados:
                id_lote = fila[0]
                f_inicio = fila[1]
                lote_cod = fila[2]
                kgs_in = fila[3]
                procedencia = fila[4] if fila[4] is not None else "Sin Especificar"
                proc_status = "SI" if fila[5] == 1 else "NO"
                kgs_pr = fila[6]
                env_status = "SI" if fila[7] == 1 else "NO"
                kgs_env = fila[8]
                f_proc = fila[9]
                f_env = fila[10]
                
                t_hasta_procesado = "-"
                t_hasta_envasado = "-"
                
                if fila[5] == 1:
                    t_hasta_procesado = self._formatear_delta_tiempo(f_inicio, f_proc)
                    
                if fila[7] == 1:
                    t_hasta_envasado = self._formatear_delta_tiempo(f_proc, f_env)
                
                fecha_str = f_inicio.strftime('%d-%m-%Y %H:%M') if isinstance(f_inicio, datetime) else str(f_inicio)
                
                self.tree.insert("", "end", values=(
                    id_lote, fecha_str, lote_cod, kgs_in, procedencia, 
                    proc_status, t_hasta_procesado, kgs_pr, 
                    env_status, t_hasta_envasado, kgs_env
                ))

    def _on_lote_seleccionado(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        
        query = """SELECT lote, kgsingreso, kgsprocesado, idcalidad, operarioproc, procesado, 
                          kgsenv, idenvase, operarioenv, envasado, idorigen, fechainicio, fechaprocesado, fechaenv 
                   FROM lotes WHERE id = %s"""
        res = self.db.execute_query(query, (id_lote,))
        
        if res:
            (lote, kgs_in, kgs_pr, id_cal, op_pr, proc, kgs_en, id_en, op_en, env, 
             id_origen, f_inicio, f_proc, f_env) = res[0]
            
            lote = lote if lote is not None else ""
            kgs_in = kgs_in if kgs_in is not None else ""
            kgs_pr = kgs_pr if kgs_pr is not None else ""
            kgs_en = kgs_en if kgs_en is not None else ""
            
            ahora = datetime.now()
            
            f_in_dt = f_inicio if isinstance(f_inicio, datetime) else ahora
            f_pr_dt = f_proc if isinstance(f_proc, datetime) else ahora
            f_ev_dt = f_env if isinstance(f_env, datetime) else ahora

            self.ent_lote.delete(0, "end")
            self.ent_lote.insert(0, str(lote))
            self.ent_kgs_ingreso.delete(0, "end")
            self.ent_kgs_ingreso.insert(0, str(kgs_in))
            
            self.ent_fecha_ingreso.delete(0, "end")
            self.ent_fecha_ingreso.insert(0, f_in_dt.strftime('%d-%m-%Y'))
            self.cmb_hora_ingreso.set(f_in_dt.strftime('%H'))
            self.cmb_min_ingreso.set(f_in_dt.strftime('%M'))
            
            if id_origen in self.lista_id_origenes:
                idx = self.lista_id_origenes.index(id_origen)
                texto_combo = self.cmb_origen.cget("values")[idx]
                self.cmb_origen.set(texto_combo)
            
            self.ent_kgs_proc.delete(0, "end")
            self.ent_kgs_proc.insert(0, str(kgs_pr))
            
            self.ent_fecha_proc.delete(0, "end")
            self.ent_fecha_proc.insert(0, f_pr_dt.strftime('%d-%m-%Y'))
            self.cmb_hora_proc.set(f_pr_dt.strftime('%H'))
            self.cmb_min_proc.set(f_pr_dt.strftime('%M'))
            
            if proc == 1: self.chk_procesado.select()
            else: self.chk_procesado.deselect()
            
            self.ent_kgs_env.delete(0, "end")
            self.ent_kgs_env.insert(0, str(kgs_en))
            
            self.ent_fecha_env.delete(0, "end")
            self.ent_fecha_env.insert(0, f_ev_dt.strftime('%d-%m-%Y'))
            self.cmb_hora_env.set(f_ev_dt.strftime('%H'))
            self.cmb_min_env.set(f_ev_dt.strftime('%M'))
            
            if env == 1: self.chk_envasado.select()
            else: self.chk_envasado.deselect()

    def _on_tab_change(self):
        seleccion = self.tree.selection()
        current_tab = self.tabs.get()
        if current_tab in ["2. Procesamiento", "3. Envasado"] and not seleccion:
            self.tabs.set("1. Cultivo / Ingreso")
            messagebox.showwarning("Atención", "Debe marcar un lote de la lista para registrar procesamiento o envasado.")

    def _guardar_nuevo_lote(self):
        lote_cod = self.ent_lote.get().strip()
        kgs = self.ent_kgs_ingreso.get()
        texto_origen = self.cmb_origen.get()
        
        fecha_usr = self.ent_fecha_ingreso.get().strip()
        h_usr = self.cmb_hora_ingreso.get()
        m_usr = self.cmb_min_ingreso.get()
        
        if not lote_cod or not kgs.isdigit() or texto_origen in ["Cargando orígenes...", "Sin orígenes agrarios", ""]:
            messagebox.showwarning("Campos Incompletos", "Verifique el identificador del lote, kilos y origen agrario.")
            return

        fecha_sql = self._convertir_a_sql(fecha_usr, h_usr, m_usr)
        if not fecha_sql:
            messagebox.showerror("Fecha Inválida", "La fecha ingresada no corresponde a un calendario válido.\nUse el formato: DD-MM-YYYY")
            return

        query_verificar = "SELECT id FROM lotes WHERE lote = %s"
        if self.db.execute_query(query_verificar, (lote_cod,)):
            messagebox.showerror("Duplicado", f"El lote '{lote_cod}' ya se encuentra registrado.")
            return

        try:
            indice = self.cmb_origen.cget("values").index(texto_origen)
            id_origen_real = self.lista_id_origenes[indice]
            
            query_insertar = "INSERT INTO lotes (lote, kgsingreso, idorigen, fechainicio) VALUES (%s, %s, %s, %s)"
            self.db.execute_non_query(query_insertar, (lote_cod, int(kgs), id_origen_real, fecha_sql))
            
            self.cargar_lotes_db()
            self.ent_lote.delete(0, "end")
            self.ent_kgs_ingreso.delete(0, "end")
            self._setear_tiempos_actuales()
            messagebox.showinfo("Éxito", f"Lote '{lote_cod}' dado de alta exitosamente.")
            
        except ValueError:
            messagebox.showerror("Error", "El origen agrario es inválido.")
            
    def _guardar_procesado(self):
        seleccion = self.tree.selection()
        if not seleccion: return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        kgs_proc = self.ent_kgs_proc.get()
        is_proc = 1 if self.chk_procesado.get() == 1 else 0
        
        fecha_usr = self.ent_fecha_proc.get().strip()
        h_usr = self.cmb_hora_proc.get()
        m_usr = self.cmb_min_proc.get()
        
        if not kgs_proc.isdigit():
            messagebox.showwarning("Datos Inválidos", "Ingrese un valor numérico para los kilogramos.")
            return

        fecha_sql = self._convertir_a_sql(fecha_usr, h_usr, m_usr)
        if not fecha_sql:
            messagebox.showerror("Fecha Inválida", "Verifique que la fecha tenga el formato DD-MM-YYYY.")
            return

        query = """UPDATE lotes SET kgsprocesado = %s, fechaprocesado = %s, 
                operarioproc = 101, idcalidad = 1, procesado = %s WHERE id = %s"""
        self.db.execute_non_query(query, (int(kgs_proc), fecha_sql, is_proc, id_lote))
        
        self.cargar_lotes_db()
        messagebox.showinfo("Éxito", "Etapa de procesamiento guardada correctamente.")

    def _guardar_envasado(self):
        seleccion = self.tree.selection()
        if not seleccion: return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        kgs_env = self.ent_kgs_env.get()
        is_env = 1 if self.chk_envasado.get() == 1 else 0
        
        fecha_usr = self.ent_fecha_env.get().strip()
        h_usr = self.cmb_hora_env.get()
        m_usr = self.cmb_min_env.get()
        
        if not kgs_env.isdigit():
            messagebox.showwarning("Datos Inválidos", "Ingrese un valor numérico para los kilogramos envasados.")
            return

        fecha_sql = self._convertir_a_sql(fecha_usr, h_usr, m_usr)
        if not fecha_sql:
            messagebox.showerror("Fecha Inválida", "Verifique que la fecha tenga el formato DD-MM-YYYY.")
            return

        query = """UPDATE lotes SET kgsenv = %s, fechaenv = %s, 
                operarioenv = 101, idenvase = 1, envasado = %s WHERE id = %s"""
        self.db.execute_non_query(query, (int(kgs_env), fecha_sql, is_env, id_lote))
        
        self.cargar_lotes_db()
        messagebox.showinfo("Éxito", "Etapa final de envasado registrada con éxito.")

    def _imprimir_detalle_lote(self):
        """Genera un ticket de impresión en HTML con un código QR de trazabilidad integrado"""
        import os
        try:
            import qrcode
        except ImportError:
            messagebox.showerror("Librería Faltante", "Por favor, instale las librerías necesarias ejecutando:\npip install qrcode pillow")
            return
        
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Impresión", "Por favor, seleccione un lote de la grilla superior para imprimir su detalle.")
            return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        
        query = """
            SELECT 
                lotes.lote, 
                lotes.fechainicio, 
                lotes.fechaprocesado, 
                loteagrario.loteagrario AS parcela, 
                chacras.chacra AS chacra, 
                lotes.kgsingreso, 
                lotes.kgsenv,
                lotes.procesado
            FROM lotes
            LEFT JOIN loteagrario ON lotes.idorigen = loteagrario.id
            LEFT JOIN chacras ON loteagrario.idchacra = chacras.idchacra
            WHERE lotes.id = %s
        """
        res = self.db.execute_query(query, (id_lote,))
        
        if not res:
            messagebox.showerror("Error", "No se pudieron recuperar los datos del lote seleccionado.")
            return
            
        lote_num, f_inicio, f_proc, parcela, chacra, kgs_verde, kgs_env, es_proc = res[0]
        
        origen_string = f"{chacra or 'S/D'} - Parcela: {parcela or 'S/D'}"
        f_inicio_str = f_inicio.strftime('%d-%m-%Y %H:%M:%S') if isinstance(f_inicio, datetime) else str(f_inicio or '-')
        
        f_proc_str = "PENDIENTE"
        if es_proc == 1 and f_proc:
            f_proc_str = f_proc.strftime('%d-%m-%Y %H:%M:%S') if isinstance(f_proc, datetime) else str(f_proc)
            
        kgs_verde_str = f"{int(kgs_verde):,} Kgs" if kgs_verde is not None else "0 Kgs"
        kgs_env_str = f"{int(kgs_env):,} Kgs" if kgs_env is not None else "Pendiente"

        directorio = "impresiones"
        if not os.path.exists(directorio):
            os.makedirs(directorio)

        # 1. CONSTRUCCIÓN DEL CONTENIDO E IMAGEN DEL CÓDIGO QR
        qr_texto = (
            f"LOTE:{lote_num}\n"
            f"ING: {f_inicio_str}\n"
            f"PROC: {f_proc_str}\n"
            f"ORIGEN: {origen_string}\n"
            f"KGS_VERDE: {kgs_verde_str}\n"
            f"KGS_ENV: {kgs_env_str}"
        )
        
        nombre_qr_img = os.path.join(directorio, f"qr_lote_{lote_num}.png")
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(qr_texto)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        img_qr.save(nombre_qr_img)

        # 2. RUTA ABSOLUTA PARA INTEGRACIÓN DE RECURSO LOCAL EN EL HTML
        ruta_absoluta_qr = os.path.abspath(nombre_qr_img).replace("\\", "/")
        
        html_contenido = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 14px;
                    width: 290px;
                    margin: 0;
                    padding: 10px;
                    color: #000;
                }}
                .text-center {{ text-align: center; }}
                .linea {{ border-top: 1px dashed #000; margin: 8px 0; }}
                .titulo {{ font-size: 18px; font-weight: bold; margin-bottom: 2px; }}
                .sub {{ font-size: 11px; margin-bottom: 10px; }}
                .campo {{ margin: 4px 0; word-wrap: break-word; }}
                .label {{ font-weight: bold; }}
                .qr-container {{ margin-top: 15px; text-align: center; }}
                .qr-container img {{ width: 150px; height: 150px; }}
            </style>
        </head>
        <body>
            <div class="text-center titulo">FLOWTRACK</div>
            <div class="text-center sub">COMPROBANTE DE TRAZABILIDAD</div>
            <div class="linea"></div>
            
            <div class="campo"><span class="label">LOTE:</span> {lote_num}</div>
            <div class="linea"></div>
            
            <div class="campo"><span class="label">FECHA/HORA INGRESO:</span><br>{f_inicio_str}</div>
            <div class="campo"><span class="label">FECHA/HORA PROCESO:</span><br>{f_proc_str}</div>
            <div class="linea"></div>
            
            <div class="campo"><span class="label">ORIGEN:</span><br>{origen_string}</div>
            <div class="linea"></div>
            
            <div class="campo"><span class="label">KILOS VERDE:</span> {kgs_verde_str}</div>
            <div class="campo"><span class="label">KILOS ENVASADO:</span> {kgs_env_str}</div>
            <div class="linea"></div>
            
            <div class="qr-container">
                <img src="file:///{ruta_absoluta_qr}" alt="Código QR de Trazabilidad">
                <div style="font-size: 10px; margin-top: 5px;">ESCANEAME PARA TRAZABILIDAD</div>
            </div>
            
            <div class="linea"></div>
            <div class="text-center" style="font-size: 11px;">DG SOLUCIONES - INDUSTRIAL</div>
        </body>
        </html>
        """

        nombre_html = os.path.join(directorio, f"ticket_lote_{lote_num}.html")
        with open(nombre_html, "w", encoding="utf-8") as archivo_html:
            archivo_html.write(html_contenido)
            
        os.startfile(os.path.abspath(nombre_html))