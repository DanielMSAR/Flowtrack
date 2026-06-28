# movinsumos_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class MovInsumosView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Capturamos los datos del usuario activo desde app.py (Auditoría interna)
        self.current_user_name = getattr(master.winfo_toplevel(), "current_user_name", "DANIEL").upper()
        
        # Mapeos internos para recuperar los IDs reales de los Comboboxes
        self.insumos_dict = {}
        self.vehiculos_dict = {}

        # --- CONTENEDOR DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color="#7a8754", segmented_button_selected_hover_color="#636e43", text_color="black")
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)

        # Creación de las tres pestañas
        self.tab_stock = self.tabview.add("STOCK")
        self.tab_ingresos = self.tabview.add("INGRESOS")
        self.tab_salidas = self.tabview.add("SALIDAS")

        # Inicializar cada pestaña
        self._configurar_tab_stock()
        self._configurar_tab_ingresos()
        self._configurar_tab_salidas()

        # Poblar los diccionarios y combos de forma centralizada
        self.cargar_combos_ingresos()

    # =====================================================================
    # PESTAÑA: STOCK (SISTEMA MAESTRO-DETALLE DOBLE GRILLA CON IMPRESIÓN)
    # =====================================================================
    def _configurar_tab_stock(self):
        # Contenedor principal de la pestaña
        self.stock_container = ctk.CTkFrame(self.tab_stock, fg_color="white", corner_radius=0)
        self.stock_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Configuramos los estilos generales de las tablas
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="black", rowheight=28, fieldbackground="white", font=("Arial", 11))
        style.configure("Treeview.Heading", background="#f1f3f5", foreground="black", font=("Arial", 11, "bold"), borderwidth=1)
        style.map("Treeview", background=[("selected", "#8cb04e")], foreground=[("selected", "black")])

        # -----------------------------------------------------------------
        # MITAD SUPERIOR: PANEL DE MAESTRO (STOCK ACTUAL)
        # -----------------------------------------------------------------
        self.header_superior = ctk.CTkFrame(self.stock_container, fg_color="white", height=35, corner_radius=0)
        self.header_superior.pack(fill="x", pady=(0, 5))
        self.header_superior.pack_propagate(False)

        ctk.CTkLabel(self.header_superior, text="📋 ESTADO DE STOCK CONSOLIDADO", font=("Arial", 12, "bold"), text_color="#4d5433").pack(side="left", anchor="w")
        
        self.btn_imp_stock = ctk.CTkButton(
            self.header_superior, text="🖨️ IMPRIMIR STOCK", fg_color="#6c757d", hover_color="#5a6268",
            text_color="white", font=("Arial", 11, "bold"), width=140, height=28, command=self.imprimir_stock_completo
        )
        self.btn_imp_stock.pack(side="right", anchor="e", padx=(0, 20))

        self.frame_superior = ctk.CTkFrame(self.stock_container, fg_color="white", corner_radius=0)
        self.frame_superior.pack(fill="both", expand=True, pady=(0, 15))

        columnas_stock = ("idarticulo", "insumo", "cantidad", "puntocritico")
        self.tree_stock = ttk.Treeview(self.frame_superior, columns=columnas_stock, show="headings")
        self.tree_stock.tag_configure("critico", background="#f8d7da", foreground="#721c24")
        
        self.tree_stock.heading("idarticulo", text="ID ARTÍCULO")
        self.tree_stock.heading("insumo", text="INSUMO / DESCRIPCIÓN")
        self.tree_stock.heading("cantidad", text="STOCK ACTUAL")
        self.tree_stock.heading("puntocritico", text="PUNTO CRÍTICO")

        self.tree_stock.column("idarticulo", width=100, anchor="center")
        self.tree_stock.column("insumo", width=350, anchor="w")
        self.tree_stock.column("cantidad", width=150, anchor="center")
        self.tree_stock.column("puntocritico", width=150, anchor="center")

        sb_sup = ttk.Scrollbar(self.frame_superior, orient="vertical", command=self.tree_stock.yview)
        self.tree_stock.configure(yscrollcommand=sb_sup.set)
        self.tree_stock.pack(side="left", fill="both", expand=True)
        sb_sup.pack(side="right", fill="y")

        self.tree_stock.bind("<<TreeviewSelect>>", self._al_seleccionar_insumo)

        # -----------------------------------------------------------------
        # MITAD INFERIOR: PANEL DE DETALLE (HISTORIAL DE MOVIMIENTOS)
        # -----------------------------------------------------------------
        self.header_inferior = ctk.CTkFrame(self.stock_container, fg_color="white", height=35, corner_radius=0)
        self.header_inferior.pack(fill="x", pady=(5, 5))
        self.header_inferior.pack_propagate(False)

        self.lbl_historial_titulo = ctk.CTkLabel(self.header_inferior, text="📜 HISTORIAL DE MOVIMIENTOS: (Seleccione un insumo)", font=("Arial", 12, "bold"), text_color="#333333")
        self.lbl_historial_titulo.pack(side="left", anchor="w")

        self.btn_imp_detalle = ctk.CTkButton(
            self.header_inferior, text="🖨️ IMPRIMIR HISTORIAL", fg_color="#6c757d", hover_color="#5a6268",
            text_color="white", font=("Arial", 11, "bold"), width=160, height=28, state="disabled", command=self.imprimir_historial_insumo
        )
        self.btn_imp_detalle.pack(side="right", anchor="e", padx=(0, 20))

        self.frame_inferior = ctk.CTkFrame(self.stock_container, fg_color="white", corner_radius=0)
        self.frame_inferior.pack(fill="both", expand=True)

        columnas_movs = ("fecha", "tipo", "inicial", "agrega", "descuenta", "final", "comp", "empleado", "vehiculo")
        self.tree_movs = ttk.Treeview(self.frame_inferior, columns=columnas_movs, show="headings")
        self.tree_movs.tag_configure("ingreso", background="#e8f5e9")
        self.tree_movs.tag_configure("egreso", background="#fff3e0")

        self.tree_movs.heading("fecha", text="FECHA / HORA")
        self.tree_movs.heading("tipo", text="TIPO MOV.")
        self.tree_movs.heading("inicial", text="ST. INICIAL")
        self.tree_movs.heading("agrega", text="ENTRADA (+)")
        self.tree_movs.heading("descuenta", text="SALIDA (-)")
        self.tree_movs.heading("final", text="ST. FINAL")
        self.tree_movs.heading("comp", text="COMPROBANTE")
        self.tree_movs.heading("empleado", text="RESPONSABLE") # Cambiado el encabezado visible a Responsable
        self.tree_movs.heading("vehiculo", text="VEHÍCULO")

        self.tree_movs.column("fecha", width=140, anchor="center")
        self.tree_movs.column("tipo", width=110, anchor="center")
        self.tree_movs.column("inicial", width=90, anchor="center")
        self.tree_movs.column("agrega", width=90, anchor="center")
        self.tree_movs.column("descuenta", width=90, anchor="center")
        self.tree_movs.column("final", width=90, anchor="center")
        self.tree_movs.column("comp", width=130, anchor="w")
        self.tree_movs.column("empleado", width=130, anchor="center")
        self.tree_movs.column("vehiculo", width=110, anchor="center")

        sb_inf = ttk.Scrollbar(self.frame_inferior, orient="vertical", command=self.tree_movs.yview)
        self.tree_movs.configure(yscrollcommand=sb_inf.set)
        self.tree_movs.pack(side="left", fill="both", expand=True)
        sb_inf.pack(side="right", fill="y")

        self.btn_refrescar = ctk.CTkButton(
            self.tab_stock, text="ACTUALIZAR PANEL", fg_color="#4d5433", hover_color="#3b4026",
            text_color="white", font=("Arial", 12, "bold"), height=35, command=self.cargar_grid_stock
        )
        self.btn_refrescar.pack(pady=(10, 0), anchor="e")

        self.cargar_grid_stock()

    def cargar_grid_stock(self):
        for fila in self.tree_stock.get_children():
            self.tree_stock.delete(fila)
            
        for fila in self.tree_movs.get_children():
            self.tree_movs.delete(fila)
        
        self.lbl_historial_titulo.configure(text="📜 HISTORIAL DE MOVIMIENTOS: (Seleccione un insumo)")
        self.btn_detalle_activo = None
        self.btn_imp_detalle.configure(state="disabled", fg_color="#6c757d")

        try:
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.commit()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.commit()
        except Exception:
            pass

        query = """
            SELECT insumos.id, insumos.insumo, IFNULL(stockinsumos.cantidad, 0.0) AS cantidad, insumos.puntocritico 
            FROM insumos 
            LEFT JOIN stockinsumos ON insumos.id = stockinsumos.idarticulo
            ORDER BY insumos.insumo ASC
        """
        registros = self.db.execute_query(query)
        if registros:
            for r in registros:
                cantidad_actual = r[2]
                punto_critico = r[3] if r[3] is not None else 0.0
                qty_fmt = f"{cantidad_actual:.2f}"
                pc_fmt = f"{punto_critico:.2f}"
                
                if cantidad_actual <= punto_critico:
                    self.tree_stock.insert("", "end", values=(r[0], r[1], qty_fmt, pc_fmt), tags=("critico",))
                else:
                    self.tree_stock.insert("", "end", values=(r[0], r[1], qty_fmt, pc_fmt))

    def _al_seleccionar_insumo(self, event):
        items_seleccionados = self.tree_stock.selection()
        if not items_seleccionados:
            return

        item = items_seleccionados[0]
        valores = self.tree_stock.item(item, "values")
        id_insumo = valores[0]
        nombre_insumo = valores[1]

        self.lbl_historial_titulo.configure(text=f"📜 HISTORIAL DE MOVIMIENTOS: {nombre_insumo.upper()} (ID: {id_insumo})")

        for fila in self.tree_movs.get_children():
            self.tree_movs.delete(fila)

        query_movs = """
            SELECT m.fecha, m.stocki, m.agrega, m.descuenta, m.stockf, m.comp, m.empleado, IFNULL(v.dominio, 'N/A') as patente
            FROM regmovinsumos m
            LEFT JOIN vehiculos v ON m.idvehiculo = v.idvehiculo
            WHERE m.idinsumo = %s
            ORDER BY m.fecha DESC
        """
        historial = self.db.execute_query(query_movs, (id_insumo,))
        
        if historial:
            for m in historial:
                fecha_dt = m[0]
                fecha_fmt = fecha_dt.strftime("%d/%m/%Y %H:%M") if isinstance(fecha_dt, datetime) else str(fecha_dt)
                
                st_i = f"{m[1]:.2f}"
                agrega = f"{m[2]:.2f}"
                descuenta = f"{m[3]:.2f}"
                st_f = f"{m[4]:.2f}"
                comprobante = m[5] if m[5] else "-"
                empleado_mov = m[6] if m[6] else "-"  # Muestra el nombre cargado textualmente
                vehiculo = m[7]

                if m[2] > 0:
                    tipo_mov = "INGRESO (+)"
                    tag_color = "ingreso"
                else:
                    tipo_mov = "CONSUMO (-)"
                    tag_color = "egreso"

                self.tree_movs.insert("", "end", values=(fecha_fmt, tipo_mov, st_i, agrega, descuenta, st_f, comprobante, empleado_mov, vehiculo), tags=(tag_color,))

        self.btn_detalle_activo = {"id": id_insumo, "nombre": nombre_insumo}
        self.btn_imp_detalle.configure(state="normal", fg_color="#4d5433", hover_color="#3b4026")

    # =====================================================================
    # PESTAÑA: INGRESOS (ALTAS DE STOCK)
    # =====================================================================
    def _configurar_tab_ingresos(self):
        self.ingresos_container = ctk.CTkFrame(self.tab_ingresos, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e9ecef")
        self.ingresos_container.pack(fill="none", expand=True, padx=50, pady=15)

        ctk.CTkLabel(self.ingresos_container, text="REGISTRO DE INGRESO / COMPRA DE MATERIAL", font=("Arial", 16, "bold"), text_color="#4d5433").grid(row=0, column=0, columnspan=2, pady=15, padx=30, sticky="w")

        # Combo Insumos
        ctk.CTkLabel(self.ingresos_container, text="Seleccione Insumo:", font=("Arial", 12, "bold"), text_color="black").grid(row=1, column=0, padx=30, pady=(5, 2), sticky="w")
        self.cmb_insumos = ctk.CTkComboBox(self.ingresos_container, width=320, height=35, values=[], command=self._actualizar_lbl_stock_inicial)
        self.cmb_insumos.grid(row=2, column=0, padx=30, pady=(0, 10), sticky="w")
        self.cmb_insumos.set("Seleccione un insumo...")

        self.lbl_stock_previo = ctk.CTkLabel(self.ingresos_container, text="Stock Actual en Depósito: --", font=("Arial", 12, "italic"), text_color="blue")
        self.lbl_stock_previo.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="w")

        # Combo Vehículos
        ctk.CTkLabel(self.ingresos_container, text="Vehículo Asociado:", font=("Arial", 12, "bold"), text_color="black").grid(row=3, column=0, padx=30, pady=(5, 2), sticky="w")
        self.cmb_vehiculos = ctk.CTkComboBox(self.ingresos_container, width=320, height=35, values=[])
        self.cmb_vehiculos.grid(row=4, column=0, padx=30, pady=(0, 10), sticky="w")
        self.cmb_vehiculos.set("Seleccione un vehículo (Opcional)...")

        # NUEVO NUEVO: Cuadro de texto para Nombre del Proveedor / Chofer que trae
        ctk.CTkLabel(self.ingresos_container, text="Entregado por (Nombre de Persona):", font=("Arial", 12, "bold"), text_color="black").grid(row=5, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_empleado_ingreso = ctk.CTkEntry(self.ingresos_container, width=320, height=35, font=("Arial", 13), placeholder_text="Nombre de quien entrega...")
        self.ent_empleado_ingreso.grid(row=6, column=0, padx=30, pady=(0, 10), sticky="w")

        # Cantidad
        ctk.CTkLabel(self.ingresos_container, text="Cantidad a Ingresar:", font=("Arial", 12, "bold"), text_color="black").grid(row=7, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_cantidad = ctk.CTkEntry(self.ingresos_container, width=320, height=35, font=("Arial", 13))
        self.ent_cantidad.grid(row=8, column=0, padx=30, pady=(0, 10), sticky="w")

        # Comprobante
        ctk.CTkLabel(self.ingresos_container, text="Remito / Factura / Comprobante:", font=("Arial", 12, "bold"), text_color="black").grid(row=9, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_comp = ctk.CTkEntry(self.ingresos_container, width=320, height=35, font=("Arial", 13))
        self.ent_comp.grid(row=10, column=0, padx=30, pady=(0, 20), sticky="w")

        # Botón
        self.btn_guardar_ingreso = ctk.CTkButton(
            self.ingresos_container, text="PROCESAR INGRESO", fg_color="#4d5433", hover_color="#3b4026",
            text_color="white", font=("Arial", 13, "bold"), height=45, width=320, command=self.guardar_ingreso
        )
        self.btn_guardar_ingreso.grid(row=11, column=0, columnspan=2, padx=30, pady=(0, 20))

    def _actualizar_lbl_stock_inicial(self, valor_combo):
        id_insumo = self.insumos_dict.get(valor_combo)
        if id_insumo:
            stock_actual = self._obtener_stock_actual_db(id_insumo)
            self.lbl_stock_previo.configure(text=f"Stock Actual en Depósito: {stock_actual:.2f}")

    def _obtener_stock_actual_db(self, id_insumo):
        query = "SELECT cantidad FROM stockinsumos WHERE idarticulo = %s"
        resultado = self.db.execute_query(query, (id_insumo,))
        return float(resultado[0][0]) if resultado and resultado[0][0] is not None else 0.0

    def guardar_ingreso(self):
        insumo_sel = self.cmb_insumos.get()
        vehiculo_sel = self.cmb_vehiculos.get()
        empleado_tipeado = self.ent_empleado_ingreso.get().strip().upper() # Captura el cuadro de texto
        cantidad_raw = self.ent_cantidad.get().strip()
        comprobante = self.ent_comp.get().strip()

        if not insumo_sel or insumo_sel == "Seleccione un insumo...":
            messagebox.showwarning("Atención", "Debe seleccionar un insumo válido de la lista.")
            return

        try:
            cantidad_agrega = float(cantidad_raw)
            if cantidad_agrega <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido mayor a cero.")
            return

        # Si el usuario no escribe un nombre, ponemos el usuario de sistema por seguridad, sino usamos lo tipeado
        responsable_final = empleado_tipeado if empleado_tipeado else self.current_user_name

        id_insumo = self.insumos_dict.get(insumo_sel)
        id_vehiculo = self.vehiculos_dict.get(vehiculo_sel) if (vehiculo_sel and vehiculo_sel != "Seleccione un vehículo (Opcional)...") else None

        stock_inicial = self._obtener_stock_actual_db(id_insumo)
        stock_final = stock_inicial + cantidad_agrega

        try:
            query_mov = """
                INSERT INTO regmovinsumos (detalle, fecha, stocki, agrega, descuenta, stockf, comp, idinsumo, empleado, idvehiculo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params_mov = (insumo_sel, datetime.now(), stock_inicial, cantidad_agrega, 0.0, stock_final, comprobante, id_insumo, responsable_final, id_vehiculo)
            self.db.execute_query(query_mov, params_mov)

            chk = self.db.execute_query("SELECT idstock FROM stockinsumos WHERE idarticulo = %s", (id_insumo,))
            if chk:
                self.db.execute_query("UPDATE stockinsumos SET cantidad = %s WHERE idarticulo = %s", (stock_final, id_insumo))
            else:
                self.db.execute_query("INSERT INTO stockinsumos (idarticulo, cantidad) VALUES (%s, %s)", (id_insumo, stock_final))

            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.commit()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.commit()

            messagebox.showinfo("Éxito", f"Ingreso procesado correctamente.\nStock final: {stock_final:.2f}")
            
            self.ent_cantidad.delete(0, "end")
            self.ent_comp.delete(0, "end")
            self.ent_empleado_ingreso.delete(0, "end")
            self.cmb_insumos.set("Seleccione un insumo...")
            self.cmb_vehiculos.set("Seleccione un vehículo (Opcional)...")
            self.lbl_stock_previo.configure(text="Stock Actual en Depósito: --")
            self.cargar_grid_stock()
            
        except Exception as e:
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.rollback()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.rollback()
            messagebox.showerror("Error", f"No se pudo completar el ingreso:\n{e}")

    # =====================================================================
    # PESTAÑA: SALIDAS (EGRESOS Y CONSUMOS DE STOCK)
    # =====================================================================
    def _configurar_tab_salidas(self):
        self.salidas_container = ctk.CTkFrame(self.tab_salidas, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e9ecef")
        self.salidas_container.pack(fill="none", expand=True, padx=50, pady=15)

        ctk.CTkLabel(self.salidas_container, text="REGISTRO DE SALIDA / CONSUMO DE STOCK", font=("Arial", 16, "bold"), text_color="#bc4749").grid(row=0, column=0, columnspan=2, pady=15, padx=30, sticky="w")

        # Combo Insumos para Salida
        ctk.CTkLabel(self.salidas_container, text="Seleccione Insumo a Retirar:", font=("Arial", 12, "bold"), text_color="black").grid(row=1, column=0, padx=30, pady=(5, 2), sticky="w")
        self.cmb_insumos_salida = ctk.CTkComboBox(self.salidas_container, width=320, height=35, values=[], command=self._actualizar_lbl_stock_inicial_salida)
        self.cmb_insumos_salida.grid(row=2, column=0, padx=30, pady=(0, 10), sticky="w")
        self.cmb_insumos_salida.set("Seleccione un insumo...")

        self.lbl_stock_previo_salida = ctk.CTkLabel(self.salidas_container, text="Stock Actual en Depósito: --", font=("Arial", 12, "italic"), text_color="red")
        self.lbl_stock_previo_salida.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="w")

        # Combo Vehículos para Salida
        ctk.CTkLabel(self.salidas_container, text="Vehículo / Destino Asociado:", font=("Arial", 12, "bold"), text_color="black").grid(row=3, column=0, padx=30, pady=(5, 2), sticky="w")
        self.cmb_vehiculos_salida = ctk.CTkComboBox(self.salidas_container, width=320, height=35, values=[])
        self.cmb_vehiculos_salida.grid(row=4, column=0, padx=30, pady=(0, 10), sticky="w")
        self.cmb_vehiculos_salida.set("Seleccione un vehículo (Opcional)...")

        # NUEVO NUEVO: Cuadro de texto para Nombre del Operario / Chofer que retira el insumo
        ctk.CTkLabel(self.salidas_container, text="Retirado por (Nombre de Persona):", font=("Arial", 12, "bold"), text_color="black").grid(row=5, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_empleado_salida = ctk.CTkEntry(self.salidas_container, width=320, height=35, font=("Arial", 13), placeholder_text="Nombre de quien retira...")
        self.ent_empleado_salida.grid(row=6, column=0, padx=30, pady=(0, 10), sticky="w")

        # Cantidad a Retirar
        ctk.CTkLabel(self.salidas_container, text="Cantidad a Descontar:", font=("Arial", 12, "bold"), text_color="black").grid(row=7, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_cantidad_salida = ctk.CTkEntry(self.salidas_container, width=320, height=35, font=("Arial", 13))
        self.ent_cantidad_salida.grid(row=8, column=0, padx=30, pady=(0, 10), sticky="w")

        # Número de Vale / Comprobante de consumo
        ctk.CTkLabel(self.salidas_container, text="Nº de Vale o Comprobante (Opcional):", font=("Arial", 12, "bold"), text_color="black").grid(row=9, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_comp_salida = ctk.CTkEntry(self.salidas_container, width=320, height=35, font=("Arial", 13))
        self.ent_comp_salida.grid(row=10, column=0, padx=30, pady=(0, 20), sticky="w")

        # Botón Procesar Salida
        self.btn_guardar_salida = ctk.CTkButton(
            self.salidas_container, text="PROCESAR RETIRO / SALIDA", fg_color="#bc4749", hover_color="#9b2226",
            text_color="white", font=("Arial", 13, "bold"), height=45, width=320, command=self.guardar_salida
        )
        self.btn_guardar_salida.grid(row=11, column=0, columnspan=2, padx=30, pady=(0, 20))

    def _actualizar_lbl_stock_inicial_salida(self, valor_combo):
        id_insumo = self.insumos_dict.get(valor_combo)
        if id_insumo:
            stock_actual = self._obtener_stock_actual_db(id_insumo)
            self.lbl_stock_previo_salida.configure(text=f"Stock Actual en Depósito: {stock_actual:.2f}")

    def guardar_salida(self):
        insumo_sel = self.cmb_insumos_salida.get()
        vehiculo_sel = self.cmb_vehiculos_salida.get()
        empleado_tipeado = self.ent_empleado_salida.get().strip().upper() # Captura el cuadro de texto
        cantidad_raw = self.ent_cantidad_salida.get().strip()
        comprobante = self.ent_comp_salida.get().strip()

        if not insumo_sel or insumo_sel == "Seleccione un insumo...":
            messagebox.showwarning("Atención", "Debe seleccionar un insumo válido de la lista.")
            return

        try:
            cantidad_descuenta = float(cantidad_raw)
            if cantidad_descuenta <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "La cantidad a descontar debe ser un valor numérico mayor a cero.")
            return

        # Si el usuario no escribe un nombre, usamos el de sistema por seguridad, sino lo tipeado
        responsable_final = empleado_tipeado if empleado_tipeado else self.current_user_name

        id_insumo = self.insumos_dict.get(insumo_sel)
        id_vehiculo = self.vehiculos_dict.get(vehiculo_sel) if (vehiculo_sel and vehiculo_sel != "Seleccione un vehículo (Opcional)...") else None

        stock_inicial = self._obtener_stock_actual_db(id_insumo)
        
        if cantidad_descuenta > stock_inicial:
            messagebox.showwarning(
                "Stock Insuficiente", 
                f"No se puede registrar la salida.\n\nStock actual disponible: {stock_inicial:.2f}\nCantidad solicitada: {cantidad_descuenta:.2f}"
            )
            return

        stock_final = stock_inicial - cantidad_descuenta

        try:
            query_mov = """
                INSERT INTO regmovinsumos (detalle, fecha, stocki, agrega, descuenta, stockf, comp, idinsumo, empleado, idvehiculo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params_mov = (insumo_sel, datetime.now(), stock_inicial, 0.0, cantidad_descuenta, stock_final, comprobante, id_insumo, responsable_final, id_vehiculo)
            self.db.execute_query(query_mov, params_mov)

            self.db.execute_query("UPDATE stockinsumos SET cantidad = %s WHERE idarticulo = %s", (stock_final, id_insumo))

            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.commit()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.commit()

            messagebox.showinfo("Éxito", f"Egreso de stock procesado correctamente.\nStock remanente: {stock_final:.2f}")
            
            self.ent_cantidad_salida.delete(0, "end")
            self.ent_comp_salida.delete(0, "end")
            self.ent_empleado_salida.delete(0, "end")
            self.cmb_insumos_salida.set("Seleccione un insumo...")
            self.cmb_vehiculos_salida.set("Seleccione un vehículo (Opcional)...")
            self.lbl_stock_previo_salida.configure(text="Stock Actual en Depósito: --")
            
            self.cargar_grid_stock()
            
        except Exception as e:
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.rollback()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.rollback()
            messagebox.showerror("Error", f"No se pudo completar la transacción de salida:\n{e}")

    # =====================================================================
    # CONTROL DE DATOS Y CARGA GENERAL DE COMBOS
    # =====================================================================
    def cargar_combos_ingresos(self):
        res_insumos = self.db.execute_query("SELECT id, insumo FROM insumos ORDER BY insumo ASC")
        if res_insumos:
            self.insumos_dict = {r[1]: r[0] for r in res_insumos}
            self.cmb_insumos.configure(values=list(self.insumos_dict.keys()))
            self.cmb_insumos_salida.configure(values=list(self.insumos_dict.keys()))

        res_vehiculos = self.db.execute_query("SELECT idvehiculo, dominio FROM vehiculos ORDER BY dominio ASC")
        if res_vehiculos:
            self.vehiculos_dict = {r[1]: r[0] for r in res_vehiculos}
            self.cmb_vehiculos.configure(values=list(self.vehiculos_dict.keys()))
            self.cmb_vehiculos_salida.configure(values=list(self.vehiculos_dict.keys()))

    # =====================================================================
    # LÓGICA DE EMISIÓN DE REPORTES REALES (PDF A4 - REPORTLAB)
    # =====================================================================
    def imprimir_stock_completo(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            import os
            import webbrowser

            carpeta_reportes = os.path.abspath("reportes")
            if not os.path.exists(carpeta_reportes):
                os.makedirs(carpeta_reportes)
            
            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_pdf = os.path.join(carpeta_reportes, f"stock_consolidado_{fecha_str}.pdf")

            doc = SimpleDocTemplate(ruta_pdf, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()

            style_titulo = ParagraphStyle('TituloReporte', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor("#4d5433"), spaceAfter=6)
            style_subtitulo = ParagraphStyle('SubTituloReporte', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray, spaceAfter=20)
            style_celda_header = ParagraphStyle('CeldaHeader', parent=styles['Normal'], fontSize=10, leading=12, fontName="Helvetica-Bold", textColor=colors.white, alignment=1)
            style_celda_datos = ParagraphStyle('CeldaDatos', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.black)
            style_celda_centro = ParagraphStyle('CeldaCentro', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.black, alignment=1)

            story.append(Paragraph("FLOWTRACK - GESTIÓN INDUSTRIAL", style_titulo))
            story.append(Paragraph(f"<b>Reporte:</b> Estado de Stock Consolidado de Insumos<br/><b>Fecha de emisión:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/><b>Operario:</b> {self.current_user_name}", style_subtitulo))
            story.append(Spacer(1, 10))

            items = self.tree_stock.get_children()
            if not items:
                messagebox.showwarning("Reporte Vacío", "No hay filas de stock disponibles para exportar.")
                return

            data_tabla = [[
                Paragraph("<b>ID ARTÍCULO</b>", style_celda_header),
                Paragraph("<b>INSUMO / DESCRIPCIÓN</b>", style_celda_header),
                Paragraph("<b>STOCK ACTUAL</b>", style_celda_header),
                Paragraph("<b>PUNTO CRÍTICO</b>", style_celda_header)
            ]]

            for item in items:
                v = self.tree_stock.item(item, "values")
                data_tabla.append([
                    Paragraph(v[0], style_celda_centro),
                    Paragraph(v[1], style_celda_datos),
                    Paragraph(v[2], style_celda_centro),
                    Paragraph(v[3], style_celda_centro)
                ])

            tabla_reporte = Table(data_tabla, colWidths=[80, 250, 95, 90])
            tabla_reporte.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4d5433")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))

            story.append(tabla_reporte)
            doc.build(story)
            webbrowser.open(ruta_pdf)

        except Exception as e:
            messagebox.showerror("Error de Impresión", f"Ocurrió un error al intentar estructurar el PDF:\n{e}")

    def imprimir_historial_insumo(self):
        if not hasattr(self, 'btn_detalle_activo') or not self.btn_detalle_activo:
            return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            import os
            import webbrowser

            id_sel = self.btn_detalle_activo["id"]
            nom_sel = self.btn_detalle_activo["nombre"]

            carpeta_reportes = os.path.abspath("reportes")
            if not os.path.exists(carpeta_reportes):
                os.makedirs(carpeta_reportes)
            
            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_pdf = os.path.join(carpeta_reportes, f"historial_insumo_{id_sel}_{fecha_str}.pdf")

            from reportlab.lib.pagesizes import landscape
            doc = SimpleDocTemplate(ruta_pdf, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()

            style_titulo = ParagraphStyle('TituloHistorial', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#264653"), spaceAfter=4)
            style_subtitulo = ParagraphStyle('SubTituloHistorial', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray, spaceAfter=20)
            style_celda_header = ParagraphStyle('CeldaHeaderH', parent=styles['Normal'], fontSize=9, fontName="Helvetica-Bold", textColor=colors.white, alignment=1)
            style_celda_centro = ParagraphStyle('CeldaCentroH', parent=styles['Normal'], fontSize=9, alignment=1)
            style_celda_datos = ParagraphStyle('CeldaDatosH', parent=styles['Normal'], fontSize=9)

            story.append(Paragraph("FLOWTRACK - AUDITORÍA DE MOVIMIENTOS", style_titulo))
            story.append(Paragraph(f"<b>Artículo Consultado:</b> {nom_sel.upper()} (ID Sistema: {id_sel})<br/><b>Fecha de Reporte:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/><b>Emitido por:</b> {self.current_user_name}", style_subtitulo))
            story.append(Spacer(1, 10))

            items_movs = self.tree_movs.get_children()
            if not items_movs:
                messagebox.showwarning("Atención", "Este insumo no registra movimientos históricos para exportar.")
                return

            data_tabla = [[
                Paragraph("<b>FECHA / HORA</b>", style_celda_header),
                Paragraph("<b>TIPO MOV.</b>", style_celda_header),
                Paragraph("<b>ST. INICIAL</b>", style_celda_header),
                Paragraph("<b>ENTRADA (+)</b>", style_celda_header),
                Paragraph("<b>SALIDA (-)</b>", style_celda_header),
                Paragraph("<b>ST. FINAL</b>", style_celda_header),
                Paragraph("<b>COMPROBANTE</b>", style_celda_header),
                Paragraph("<b>RESPONSABLE</b>", style_celda_header), # Actualizado en el PDF
                Paragraph("<b>VEHÍCULO</b>", style_celda_header)
            ]]

            filas_ingreso = []
            filas_egreso = []
            
            for idx, item in enumerate(items_movs, start=1):
                v = self.tree_movs.item(item, "values")
                if "INGRESO" in v[1]:
                    filas_ingreso.append(idx)
                else:
                    filas_egreso.append(idx)

                data_tabla.append([
                    Paragraph(v[0], style_celda_centro),
                    Paragraph(v[1], style_celda_centro),
                    Paragraph(v[2], style_celda_centro),
                    Paragraph(v[3], style_celda_centro),
                    Paragraph(v[4], style_celda_centro),
                    Paragraph(v[5], style_celda_centro),
                    Paragraph(v[6], style_celda_datos),
                    Paragraph(v[7], style_celda_centro),
                    Paragraph(v[8], style_celda_centro)
                ])

            tabla_movs = Table(data_tabla, colWidths=[110, 85, 70, 75, 75, 70, 100, 95, 100])
            estilos_celdas = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#264653")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]

            for r_ing in filas_ingreso:
                estilos_celdas.append(('BACKGROUND', (0, r_ing), (-1, r_ing), colors.HexColor("#e8f5e9")))
            for r_egr in filas_egreso:
                estilos_celdas.append(('BACKGROUND', (0, r_egr), (-1, r_egr), colors.HexColor("#fff3e0")))

            tabla_movs.setStyle(TableStyle(estilos_celdas))
            story.append(tabla_movs)

            doc.build(story)
            webbrowser.open(ruta_pdf)

        except Exception as e:
            messagebox.showerror("Error de Impresión", f"No se pudo estructurar el historial en formato PDF:\n{e}")