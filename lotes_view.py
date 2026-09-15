import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class LotesView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        self.lista_id_origenes = []
        self.lista_envases = []  # Para guardar mapeos (id, nombre, capacidad) de la BD

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="GESTIÓN Y TRAZABILIDAD DE LOTES", font=("Arial", 20, "bold"), text_color="black")
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- SECCIÓN SUPERIOR: PANEL MAESTRO-DETALLE ---
        self.tabla_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tabla_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Configuramos el peso de las columnas: la grilla izquierda (0) se estira, la derecha (1) es fija
        self.tabla_frame.columnconfigure(0, weight=1)
        self.tabla_frame.columnconfigure(1, weight=0)
        self.tabla_frame.rowconfigure(0, weight=1)

        # Sub-Contenedor IZQUIERDO: Tabla de Lotes
        frame_maestro = ctk.CTkFrame(self.tabla_frame, fg_color="transparent")
        frame_maestro.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        columnas = ("id", "fechainicio", "lote", "kgsingreso", "procesado", "tiempo_proc", "kgsprocesado", "envasado", "tiempo_env", "kgsenv")
        self.tree = ttk.Treeview(frame_maestro, columns=columnas, show="headings")
        
        # Encabezados y anchos de columnas
        self.tree.heading("id", text="ID")
        self.tree.heading("fechainicio", text="Fecha Inicio")
        self.tree.heading("lote", text="Nº Lote")
        self.tree.heading("kgsingreso", text="Kgs Verde")
        self.tree.heading("procesado", text="¿Proc?")
        self.tree.heading("tiempo_proc", text="Tiempo Proc.")
        self.tree.heading("kgsprocesado", text="Kgs Proc.")
        self.tree.heading("envasado", text="¿Env?")
        self.tree.heading("tiempo_env", text="Tiempo Env.")
        self.tree.heading("kgsenv", text="Kgs Env.")

        self.tree.column("id", width=30, anchor="center")
        self.tree.column("fechainicio", width=130, anchor="center")
        self.tree.column("lote", width=90, anchor="center")
        self.tree.column("kgsingreso", width=90, anchor="e")
        self.tree.column("procesado", width=60, anchor="center")
        self.tree.column("tiempo_proc", width=110, anchor="center")
        self.tree.column("kgsprocesado", width=90, anchor="e")
        self.tree.column("envasado", width=60, anchor="center")
        self.tree.column("tiempo_env", width=110, anchor="center")
        self.tree.column("kgsenv", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(frame_maestro, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_lote_seleccionado)

        # Sub-Contenedor DERECHO: Detalle de Pesajes (Ancho estático de 380px)
        frame_detalle = ctk.CTkFrame(self.tabla_frame, width=380, fg_color="#f5f5f5", corner_radius=8, border_width=1, border_color="#dbdbdb")
        frame_detalle.grid(row=0, column=1, sticky="nsew")
        frame_detalle.pack_propagate(False)

        lbl_det_titulo = ctk.CTkLabel(frame_detalle, text="PESAJES INCLUIDOS EN EL LOTE", font=("Arial", 11, "bold"), text_color="#4d5433")
        lbl_det_titulo.pack(pady=(12, 4), padx=10, anchor="w")

        # Tabla Auxiliar: detalle_lote
        columnas_det = ("iddetalle", "idpesaje", "kgs", "origen")
        self.tree_detalle = ttk.Treeview(frame_detalle, columns=columnas_det, show="headings")
        self.tree_detalle.heading("iddetalle", text="ID Det.")
        self.tree_detalle.heading("idpesaje", text="ID Pes.")
        self.tree_detalle.heading("kgs", text="Kgs")
        self.tree_detalle.heading("origen", text="Origen")

        self.tree_detalle.column("iddetalle", width=55, anchor="center")
        self.tree_detalle.column("idpesaje", width=55, anchor="center")
        self.tree_detalle.column("kgs", width=80, anchor="e")
        self.tree_detalle.column("origen", width=150, anchor="w")

        scrollbar_det = ttk.Scrollbar(frame_detalle, orient="vertical", command=self.tree_detalle.yview)
        self.tree_detalle.configure(yscrollcommand=scrollbar_det.set)
        
        self.tree_detalle.pack(side="top", fill="both", expand=True, padx=(10, 0), pady=5)
        scrollbar_det.pack(side="right", fill="y", pady=5, padx=(0, 10))

        # Botonera operativa inferior de la derecha
        frame_botones_det = ctk.CTkFrame(frame_detalle, fg_color="transparent")
        frame_botones_det.pack(side="bottom", fill="x", padx=10, pady=10)

        self.btn_add_pesaje = ctk.CTkButton(frame_botones_det, text="➕ Asociar", font=("Arial", 12, "bold"), fg_color="#8cb04e", hover_color="#769641", text_color="black", height=32, command=self._abrir_selector_pesajes)
        self.btn_add_pesaje.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_del_pesaje = ctk.CTkButton(frame_botones_det, text="➖ Quitar", font=("Arial", 12, "bold"), fg_color="#d9534f", hover_color="#c9302c", text_color="white", height=32, command=self._quitar_pesaje_lote)
        self.btn_del_pesaje.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # --- SECCIÓN INFERIOR: PANEL DE PESTAÑAS (TABS) ---
        self.tabs = ctk.CTkTabview(self, height=200, command=self._on_tab_change)
        self.tabs.pack(fill="x", padx=20, pady=(10, 20))

        self.tab_ingreso = self.tabs.add("1. Cultivo / Ingreso")
        self.tab_procesado = self.tabs.add("2. Procesamiento")
        self.tab_envasado = self.tabs.add("3. Envasado")

        self.horas_validas = [f"{i:02d}" for i in range(24)]
        self.minutos_validas = [f"{i:02d}" for i in range(60)]

        self._crear_formulario_ingreso()
        self._crear_formulario_procesado()
        self._crear_formulario_envasado()

        self.after(100, self._inicializar_datos_db)

    def _inicializar_datos_db(self):
        self.cargar_lotes_db()
        self._cargar_combo_envases()
        self._cargar_combo_productos()
        self._setear_tiempos_actuales()

    def _setear_tiempos_actuales(self):
        ahora = datetime.now()
        fecha_hoy_ar = ahora.strftime('%d-%m-%Y')
        hora_actual = ahora.strftime('%H')
        minuto_actual = ahora.strftime('%M')

        self.ent_fecha_ingreso.delete(0, "end")
        self.ent_fecha_ingreso.insert(0, fecha_hoy_ar)
        self.cmb_hora_ingreso.set(hora_actual)
        self.cmb_min_ingreso.set(minuto_actual)
        
        self.ent_fecha_proc.delete(0, "end")
        self.ent_fecha_proc.insert(0, fecha_hoy_ar)
        self.cmb_hora_proc.set(hora_actual)
        self.cmb_min_proc.set(minuto_actual)

    def _convertir_a_sql(self, fecha_ar, hora, minuto):
        try:
            dt = datetime.strptime(f"{fecha_ar} {hora}:{minuto}:00", '%d-%m-%Y %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

    def _formatear_delta_tiempo(self, inicio, fin):
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
        lbl_lote.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        self.ent_lote = ctk.CTkEntry(self.tab_ingreso, width=180, font=("Arial", 14))
        self.ent_lote.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        lbl_kgs = ctk.CTkLabel(self.tab_ingreso, text="Kilogramos Ingreso:", font=("Arial", 14, "bold"))
        lbl_kgs.grid(row=0, column=2, padx=(20, 10), pady=10, sticky="w")
        
        self.ent_kgs_ingreso = ctk.CTkEntry(self.tab_ingreso, width=150, font=("Arial", 14), state="readonly")
        self.ent_kgs_ingreso.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        frame_time = ctk.CTkFrame(self.tab_ingreso, fg_color="transparent")
        frame_time.grid(row=0, column=4, padx=(20, 10), pady=10, sticky="w")

        ctk.CTkLabel(frame_time, text="Fecha:", font=("Arial", 13, "bold")).pack(side="left", padx=2)
        self.ent_fecha_ingreso = ctk.CTkEntry(frame_time, width=105, font=("Arial", 13), placeholder_text="DD-MM-YYYY")
        self.ent_fecha_ingreso.pack(side="left", padx=5)

        ctk.CTkLabel(frame_time, text="Hora:", font=("Arial", 13, "bold")).pack(side="left", padx=(8, 2))
        self.cmb_hora_ingreso = ctk.CTkComboBox(frame_time, values=self.horas_validas, width=65, state="readonly")
        self.cmb_hora_ingreso.pack(side="left", padx=2)

        ctk.CTkLabel(frame_time, text="Min:", font=("Arial", 13, "bold")).pack(side="left", padx=(5, 2))
        self.cmb_min_ingreso = ctk.CTkComboBox(frame_time, values=self.minutos_validas, width=65, state="readonly")
        self.cmb_min_ingreso.pack(side="left", padx=2)

        frame_acciones = ctk.CTkFrame(self.tab_ingreso, fg_color="transparent")
        frame_acciones.grid(row=1, column=0, columnspan=5, pady=(15, 5), padx=20, sticky="ew")

        frame_acciones.columnconfigure(0, weight=1)
        frame_acciones.columnconfigure(1, weight=1)
        frame_acciones.columnconfigure(2, weight=1)

        self.btn_guardar_lote = ctk.CTkButton(frame_acciones, text="CREAR LOTE", font=("Arial", 14, "bold"), height=38, command=self._guardar_nuevo_lote)
        self.btn_guardar_lote.grid(row=0, column=0, padx=5, sticky="ew")

        self.btn_eliminar_lote = ctk.CTkButton(frame_acciones, text="🗑️ ELIMINAR LOTE", fg_color="#d9534f", hover_color="#c9302c", font=("Arial", 14, "bold"), height=38, command=self._eliminar_lote)
        self.btn_eliminar_lote.grid(row=0, column=1, padx=5, sticky="ew")

        self.btn_imprimir_lote = ctk.CTkButton(frame_acciones, text="🖨️ IMPRIMIR DETALLE", fg_color="#2b5c8f", hover_color="#1f4268", font=("Arial", 14, "bold"), height=38, command=self._imprimir_detalle_lote)
        self.btn_imprimir_lote.grid(row=0, column=2, padx=5, sticky="ew")

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

    def _cargar_combo_envases(self):
        self.lista_envases = []
        try:
            query = "SELECT idenvase, envase, capacidad FROM envases ORDER BY envase ASC"
            resultados = self.db.execute_query(query)
            
            valores = []
            if resultados:
                for fila in resultados:
                    id_env, nombre, cap = fila
                    self.lista_envases.append((id_env, nombre, cap))
                    valores.append(f"{id_env} - {nombre} ({cap} kg)")
            
            # Verificación de existencia del widget para evitar errores
            if hasattr(self, 'cmb_envase'):
                if valores:
                    self.cmb_envase.configure(values=valores)
                    self.cmb_envase.set(valores[0])
                else:
                    self.cmb_envase.configure(values=["No hay envases cargados"])
                    self.cmb_envase.set("No hay envases cargados")
        except Exception as e:
            print(f"Error al cargar combo de envases: {e}")

    def _cargar_combo_productos(self):
        try:
            query = "SELECT producto FROM productos ORDER BY producto ASC"
            resultados = self.db.execute_query(query)
            
            valores = []
            if resultados:
                for fila in resultados:
                    valores.append(str(fila[0]))
            
            if valores:
                self.cmb_producto_bolson.configure(values=valores)
                self.cmb_producto_bolson.set(valores[0])
            else:
                self.cmb_producto_bolson.configure(values=["No hay productos"])
                self.cmb_producto_bolson.set("No hay productos")
        except Exception as e:
            print(f"Error al cargar combo de productos: {e}")

    def cargar_lotes_db(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = """
            SELECT lotes.id, lotes.fechainicio, lotes.lote, lotes.kgsingreso, 
                lotes.procesado, lotes.kgsprocesado, lotes.envasado, lotes.kgsenv,
                lotes.fechaprocesado, lotes.fechaenv
            FROM lotes
            WHERE lotes.activo = 1
            ORDER BY lotes.id DESC
        """
        resultados = self.db.execute_query(query)
        
        if resultados:
            for fila in resultados:
                id_lote = fila[0]
                f_inicio = fila[1]
                lote_cod = fila[2]
                kgs_in = fila[3]
                proc_status = "SI" if fila[4] == 1 else "NO"
                kgs_pr = fila[5]
                env_status = "SI" if fila[6] == 1 else "NO"
                kgs_env = fila[7]
                f_proc = fila[8]
                f_env = fila[9]
                
                t_hasta_procesado = "-"
                t_hasta_envasado = "-"
                
                if fila[4] == 1:
                    t_hasta_procesado = self._formatear_delta_tiempo(f_inicio, f_proc)
                    
                if fila[6] == 1:
                    t_hasta_envasado = self._formatear_delta_tiempo(f_proc, f_env)
                
                fecha_str = f_inicio.strftime('%d-%m-%Y %H:%M') if isinstance(f_inicio, datetime) else str(f_inicio)
                
                self.tree.insert("", "end", values=(
                    id_lote, fecha_str, lote_cod, kgs_in,  
                    proc_status, t_hasta_procesado, kgs_pr, 
                    env_status, t_hasta_envasado, kgs_env
                ))

    def _on_lote_seleccionado(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        
        query = """SELECT lote, kgsingreso, kgsprocesado, idcalidad, operarioproc, procesado, 
                        kgsenv, idenvase, operarioenv, envasado, idorigen, fechainicio, fechaprocesado, fechaenv,
                        cantenvases
                    FROM lotes WHERE id = %s AND activo = 1"""
        res = self.db.execute_query(query, (id_lote,))
        
        if res:
            (lote, kgs_in, kgs_pr, id_cal, op_pr, proc, kgs_en, id_en, op_en, env, 
            id_origen, f_inicio, f_proc, f_env, cant_envases) = res[0]
            
            lote = lote if lote is not None else ""
            kgs_in = kgs_in if kgs_in is not None else "0"
            kgs_pr = kgs_pr if kgs_pr is not None else ""

            ahora = datetime.now()
            f_in_dt = f_inicio if isinstance(f_inicio, datetime) else ahora
            f_pr_dt = f_proc if isinstance(f_proc, datetime) else ahora

            self.ent_lote.delete(0, "end")
            self.ent_lote.insert(0, str(lote))
            
            self.ent_kgs_ingreso.configure(state="normal")
            self.ent_kgs_ingreso.delete(0, "end")
            self.ent_kgs_ingreso.insert(0, str(kgs_in))
            self.ent_kgs_ingreso.configure(state="readonly")
            
            self.ent_fecha_ingreso.delete(0, "end")
            self.ent_fecha_ingreso.insert(0, f_in_dt.strftime('%d-%m-%Y'))
            self.cmb_hora_ingreso.set(f_in_dt.strftime('%H'))
            self.cmb_min_ingreso.set(f_in_dt.strftime('%M'))
            
            self.ent_kgs_proc.delete(0, "end")
            self.ent_kgs_proc.insert(0, str(kgs_pr))
            
            self.ent_fecha_proc.delete(0, "end")
            self.ent_fecha_proc.insert(0, f_pr_dt.strftime('%d-%m-%Y'))
            self.cmb_hora_proc.set(f_pr_dt.strftime('%H'))
            self.cmb_min_proc.set(f_pr_dt.strftime('%M'))
            
            if proc == 1: self.chk_procesado.select()
            else: self.chk_procesado.deselect()

        self._cargar_detalle_lote(id_lote)
        self._cargar_bolsones_lote(id_lote)

    def _on_tab_change(self):
        seleccion = self.tree.selection()
        current_tab = self.tabs.get()
        if current_tab in ["2. Procesamiento", "3. Envasado"] and not seleccion:
            self.tabs.set("1. Cultivo / Ingreso")
            messagebox.showwarning("Atención", "Debe marcar un lote de la lista para registrar procesamiento o envasado.")

    def _guardar_nuevo_lote(self):
        lote_cod = self.ent_lote.get().strip()
        kgs = "0"
        
        fecha_usr = self.ent_fecha_ingreso.get().strip()
        h_usr = self.cmb_hora_ingreso.get()
        m_usr = self.cmb_min_ingreso.get()
        
        if not lote_cod:
            messagebox.showwarning("Campos Incompletos", "Verifique el identificador del lote.")
            return

        fecha_sql = self._convertir_a_sql(fecha_usr, h_usr, m_usr)
        if not fecha_sql:
            messagebox.showerror("Fecha Inválida", "La fecha ingresada no corresponde a un calendario válido.\nUse el formato: DD-MM-YYYY")
            return

        query_verificar = "SELECT id FROM lotes WHERE lote = %s AND activo = 1"
        if self.db.execute_query(query_verificar, (lote_cod,)):
            messagebox.showerror("Duplicado", f"El lote '{lote_cod}' ya se encuentra registrado y activo.")
            return

        try:
            query_insertar = "INSERT INTO lotes (lote, kgsingreso, fechainicio) VALUES (%s, %s, %s)"
            self.db.execute_non_query(query_insertar, (lote_cod, int(kgs), fecha_sql))
            
            self.cargar_lotes_db()
            self.ent_lote.delete(0, "end")
            
            self.ent_kgs_ingreso.configure(state="normal")
            self.ent_kgs_ingreso.delete(0, "end")
            self.ent_kgs_ingreso.configure(state="readonly")
            
            self._setear_tiempos_actuales()
            messagebox.showinfo("Éxito", f"Lote '{lote_cod}' dado de alta exitosamente.")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el lote: {str(e)}")

    def _eliminar_lote(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debe seleccionar un lote de la grilla para eliminarlo.")
            return

        id_lote = self.tree.item(seleccion[0])["values"][0]
        lote_num = self.tree.item(seleccion[0])["values"][2]

        pregunta = messagebox.askyesno(
            "Confirmar Baja", 
            f"¿Está seguro de que desea eliminar el Lote N° {lote_num}?\n\nEsta acción quitará el lote del sistema de forma lógica.",
            icon='warning'
        )

        if pregunta:
            try:
                query_update = "UPDATE lotes SET activo = 0 WHERE id = %s"
                self.db.execute_non_query(query_update, (id_lote,))
                
                self.cargar_lotes_db()
                self.ent_lote.delete(0, "end")
                
                self.ent_kgs_ingreso.configure(state="normal")
                self.ent_kgs_ingreso.delete(0, "end")
                self.ent_kgs_ingreso.configure(state="readonly")
                
                self.ent_kgs_proc.delete(0, "end")
                self.chk_procesado.deselect()
                
                for item in self.tree_detalle.get_children():
                    self.tree_detalle.delete(item)

                self._setear_tiempos_actuales()
                messagebox.showinfo("Éxito", f"El lote '{lote_num}' ha sido eliminado del sistema.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo completar la operación: {str(e)}")

    def _guardar_procesado(self):
        seleccion = self.tree.selection()
        if not seleccion: return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        kgs_proc = self.ent_kgs_proc.get().strip()
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

    def _imprimir_detalle_lote(self):
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
                lotes.kgsingreso, 
                lotes.kgsenv,
                lotes.procesado
            FROM lotes
            WHERE lotes.id = %s
        """
        res = self.db.execute_query(query, (id_lote,))
        
        if not res:
            messagebox.showerror("Error", "No se pudieron recuperar los datos del lote seleccionado.")
            return
            
        lote_num, f_inicio, f_proc, kgs_verde, kgs_env, es_proc = res[0]
        
        f_inicio_str = f_inicio.strftime('%d-%m-%Y %H:%M:%S') if isinstance(f_inicio, datetime) else str(f_inicio or '-')
        
        f_proc_str = "PENDIENTE"
        if es_proc == 1 and f_proc:
            f_proc_str = f_proc.strftime('%d-%m-%Y %H:%M:%S') if isinstance(f_proc, datetime) else str(f_proc)
            
        kgs_verde_str = f"{int(kgs_verde):,} Kgs" if kgs_verde is not None else "0 Kgs"
        kgs_env_str = f"{int(kgs_env):,} Kgs" if kgs_env is not None else "Pendiente"

        directorio = "impresiones"
        if not os.path.exists(directorio):
            os.makedirs(directorio)

        qr_texto = (
            f"LOTE:{lote_num}\n"
            f"ING: {f_inicio_str}\n"
            f"PROC: {f_proc_str}\n"
            f"KGS_VERDE: {kgs_verde_str}\n"
            f"KGS_ENV: {kgs_env_str}"
        )
        
        nombre_qr_img = os.path.join(directorio, f"qr_lote_{lote_num}.png")
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(qr_texto)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        img_qr.save(nombre_qr_img)

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

    def _cargar_detalle_lote(self, id_lote):
        for item in self.tree_detalle.get_children():
            self.tree_detalle.delete(item)

        query = """
            SELECT iddetalle, idpesaje, kgs, origen 
            FROM detalle_lote 
            WHERE idlote = %s 
            ORDER BY iddetalle DESC
        """
        resultados = self.db.execute_query(query, (id_lote,))
        if resultados:
            for fila in resultados:
                self.tree_detalle.insert("", "end", values=fila)

    def _quitar_pesaje_lote(self):
        seleccion_lote = self.tree.selection()
        seleccion_det = self.tree_detalle.selection()
        
        if not seleccion_lote or not seleccion_det:
            messagebox.showwarning("Atención", "Seleccione un lote y luego el pesaje que desea quitar del mismo.")
            return

        id_lote = self.tree.item(seleccion_lote[0])["values"][0]
        id_detalle = self.tree_detalle.item(seleccion_det[0])["values"][0]
        id_pesaje = self.tree_detalle.item(seleccion_det[0])["values"][1]

        if messagebox.askyesno("Confirmar", f"¿Desea desvincular el pesaje ID {id_pesaje} de este lote?"):
            query = "DELETE FROM detalle_lote WHERE iddetalle = %s"
            self.db.execute_non_query(query, (id_detalle,))
            
            self._on_pesajes_actualizados(id_lote)
            messagebox.showinfo("Éxito", "Pesaje desvinculado correctamente.")

    def _abrir_selector_pesajes(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debe seleccionar un lote en la grilla izquierda para poder asignarle pesajes.")
            return
            
        id_lote = self.tree.item(seleccion[0])["values"][0]
        num_lote = self.tree.item(seleccion[0])["values"][2]
        
        SelectorPesajesModal(self, id_lote, num_lote, self.db, callback_on_success=lambda: self._on_pesajes_actualizados(id_lote))
    
    def _on_pesajes_actualizados(self, id_lote):
        self._cargar_detalle_lote(id_lote)
        self._recalcular_kilos_lote(id_lote)

    def _recalcular_kilos_lote(self, id_lote):
        query_sum = "SELECT SUM(kgs) FROM detalle_lote WHERE idlote = %s"
        res = self.db.execute_query(query_sum, (id_lote,))
        total_kgs = res[0][0] if res and res[0][0] is not None else 0

        query_update = "UPDATE lotes SET kgsingreso = %s WHERE id = %s"
        self.db.execute_non_query(query_update, (total_kgs, id_lote))

        self.cargar_lotes_db()

        self.ent_kgs_ingreso.configure(state="normal")
        self.ent_kgs_ingreso.delete(0, "end")
        self.ent_kgs_ingreso.insert(0, str(total_kgs))
        self.ent_kgs_ingreso.configure(state="readonly")

    def _crear_formulario_envasado(self):
        frame_inputs = ctk.CTkFrame(self.tab_envasado, fg_color="transparent")
        frame_inputs.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_inputs, text="Nº Bolsón:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.ent_num_bolson = ctk.CTkEntry(frame_inputs, width=80)
        self.ent_num_bolson.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_inputs, text="Producto:", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=5, pady=5)
        self.cmb_producto_bolson = ctk.CTkComboBox(frame_inputs, values=[], width=150)
        self.cmb_producto_bolson.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_inputs, text="Lote MP:", font=("Arial", 12, "bold")).grid(row=0, column=4, padx=5, pady=5)
        self.ent_lote_mp = ctk.CTkEntry(frame_inputs, width=100)
        self.ent_lote_mp.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(frame_inputs, text="KG:", font=("Arial", 12, "bold")).grid(row=0, column=6, padx=5, pady=5)
        self.ent_kg_bolson = ctk.CTkEntry(frame_inputs, width=90)
        self.ent_kg_bolson.grid(row=0, column=7, padx=5, pady=5)

        ctk.CTkLabel(frame_inputs, text="Conservadora:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=5, pady=5)
        self.ent_conservadora = ctk.CTkEntry(frame_inputs, width=80)
        self.ent_conservadora.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_inputs, text="Turno:", font=("Arial", 12, "bold")).grid(row=1, column=2, padx=5, pady=5)
        self.cmb_turno = ctk.CTkComboBox(frame_inputs, values=["DÍA", "NOCHE"], width=110)
        self.cmb_turno.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_inputs, text="Responsable:", font=("Arial", 12, "bold")).grid(row=1, column=4, padx=5, pady=5)
        self.ent_responsable = ctk.CTkEntry(frame_inputs, width=150)
        self.ent_responsable.grid(row=1, column=5, columnspan=2, padx=5, pady=5)

        self.btn_agregar_bolson = ctk.CTkButton(
            frame_inputs, text="➕ Agregar Bolsón", fg_color="#8cb04e", text_color="black", 
            font=("Arial", 12, "bold"), command=self._guardar_bolson_individual
        )
        self.btn_agregar_bolson.grid(row=1, column=7, padx=5, pady=5)

        frame_tabla_bolsones = ctk.CTkFrame(self.tab_envasado, fg_color="transparent")
        frame_tabla_bolsones.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("num", "prod", "mp", "cons", "turno", "kg", "resp")
        self.tree_bolsones = ttk.Treeview(frame_tabla_bolsones, columns=cols, show="headings", height=5)
        
        self.tree_bolsones.heading("num", text="Nº Bolsón")
        self.tree_bolsones.heading("prod", text="Producto")
        self.tree_bolsones.heading("mp", text="Lote MP")
        self.tree_bolsones.heading("cons", text="Conservadora")
        self.tree_bolsones.heading("turno", text="Turno")
        self.tree_bolsones.heading("kg", text="KGs")
        self.tree_bolsones.heading("resp", text="Responsable")

        for col in cols:
            self.tree_bolsones.column(col, anchor="center", width=85)

        self.tree_bolsones.pack(side="left", fill="both", expand=True)

    def _guardar_bolson_individual(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debe seleccionar un lote primero.")
            return

        id_lote = self.tree.item(seleccion[0])["values"][0]
        num_bolson = self.ent_num_bolson.get().strip()
        producto = self.cmb_producto_bolson.get()
        lote_mp = self.ent_lote_mp.get().strip()
        kgs_str = self.ent_kg_bolson.get().strip()
        conservadora = self.ent_conservadora.get().strip()
        turno = self.cmb_turno.get()
        responsable = self.ent_responsable.get().strip()

        if not (num_bolson and kgs_str):
            messagebox.showwarning("Datos Faltantes", "Ingrese al menos el número de bolsón y los KGs.")
            return

        try:
            kgs = float(kgs_str)
        except ValueError:
            messagebox.showwarning("Datos Inválidos", "El peso en KG debe ser un número entero o decimal válido.")
            return

        query = """
            INSERT INTO bolsones (idlote, num_bolson, fecha_hora, producto, lote_mp, conservadora, turno, kgs, responsable)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s, %s)
        """
        self.db.execute_non_query(query, (id_lote, num_bolson, producto, lote_mp, conservadora, turno, kgs, responsable))
        self._cargar_bolsones_lote(id_lote)
        self._recalcular_kilos_envasados(id_lote)

    def _cargar_bolsones_lote(self, id_lote):
        for item in self.tree_bolsones.get_children():
            self.tree_bolsones.delete(item)

        query = "SELECT num_bolson, producto, lote_mp, conservadora, turno, kgs, responsable FROM bolsones WHERE idlote = %s ORDER BY num_bolson ASC"
        res = self.db.execute_query(query, (id_lote,))
        if res:
            for fila in res:
                self.tree_bolsones.insert("", "end", values=fila)

    def _recalcular_kilos_envasados(self, id_lote):
        query = "SELECT SUM(kgs), COUNT(id) FROM bolsones WHERE idlote = %s"
        res = self.db.execute_query(query, (id_lote,))
        if res and res[0][0] is not None:
            total_kgs, total_cant = res[0]
            query_update = "UPDATE lotes SET kgsenv = %s, cantenvases = %s, envasado = 1 WHERE id = %s"
            self.db.execute_non_query(query_update, (total_kgs, total_cant, id_lote))
            self.cargar_lotes_db()


class SelectorPesajesModal(ctk.CTkToplevel):
    def __init__(self, parent, id_lote, num_lote, db_connection, callback_on_success):
        super().__init__(parent)
        self.db = db_connection
        self.id_lote = id_lote
        self.callback = callback_on_success

        self.title(f"Asociar Pesajes al Lote: {num_lote}")
        self.geometry("550x400")
        self.configure(fg_color="white")
        
        self.grab_set()
        self.resizable(False, False)

        ctk.CTkLabel(self, text="Pesajes Disponibles en FlowTrack", font=("Arial", 16, "bold"), text_color="black").pack(pady=10)
        ctk.CTkLabel(self, text="Seleccione los pesajes que formarán parte de este lote de producción.", font=("Arial", 11), text_color="gray").pack(pady=(0, 10))

        self.frame_tabla = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=5)

        columnas = ("idpesaje", "kgs", "fecha", "origen")
        self.tree_libres = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings", selectmode="extended")
        
        self.tree_libres.heading("idpesaje", text="ID Pesaje")
        self.tree_libres.heading("kgs", text="Kilos")
        self.tree_libres.heading("fecha", text="Fecha / Hora")
        self.tree_libres.heading("origen", text="Origen")

        self.tree_libres.column("idpesaje", width=70, anchor="center")
        self.tree_libres.column("kgs", width=90, anchor="e")
        self.tree_libres.column("fecha", width=130, anchor="center")
        self.tree_libres.column("origen", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree_libres.yview)
        self.tree_libres.configure(yscrollcommand=scrollbar.set)
        self.tree_libres.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.btn_confirmar = ctk.CTkButton(self, text="AGREGAR SELECCIONADOS", font=("Arial", 13, "bold"), height=35, fg_color="#8cb04e", hover_color="#769641", text_color="black", command=self._procesar_asociacion)
        self.btn_confirmar.pack(fill="x", padx=20, pady=15)

        self._cargar_pesajes_disponibles()

    def _cargar_pesajes_disponibles(self):
        query = """
            SELECT idregistro, pesofinal, fecha, origen 
            FROM pesajes 
            WHERE idregistro NOT IN (SELECT idpesaje FROM detalle_lote)
            ORDER BY idregistro DESC
        """
        resultados = self.db.execute_query(query)
        if resultados:
            for fila in resultados:
                f_str = fila[2].strftime('%d-%m-%Y %H:%M') if hasattr(fila[2], 'strftime') else str(fila[2])
                self.tree_libres.insert("", "end", values=(fila[0], fila[1], f_str, fila[3]))

    def _procesar_asociacion(self):
        items_seleccionados = self.tree_libres.selection()
        if not items_seleccionados:
            messagebox.showwarning("Atención", "No seleccionó ningún pesaje de la lista.", parent=self)
            return
        try:
            query_insert = """
                INSERT INTO detalle_lote (idlote, idpesaje, kgs, fecha, origen) 
                VALUES (%s, %s, %s, %s, %s)
            """
            for item in items_seleccionados:
                valores = self.tree_libres.item(item)["values"]
                id_pesaje = valores[0]
                kgs = valores[1]
                fecha_str = valores[2]
                origen = valores[3]
                
                try:
                    dt = datetime.strptime(str(fecha_str), '%d-%m-%Y %H:%M')
                    fecha_sql = dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    fecha_sql = fecha_str
                
                self.db.execute_non_query(query_insert, (self.id_lote, id_pesaje, kgs, fecha_sql, origen))

            self.callback()
            self.destroy()
            messagebox.showinfo("Éxito", "Los pesajes se vincularon correctamente al lote.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el detalle: {str(e)}", parent=self)