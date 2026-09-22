import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox
from ctacte_pdf_generator import generar_pdf_ctacte, abrir_pdf

class CtaCteProveedoresView:
    def __init__(self, parent_frame, db_connection):
        self.parent = parent_frame
        self.db = db_connection
        self.proveedor_seleccionado_id = None
        self.proveedores_encontrados = []
        self.saldo_actual_proveedor = 0.0

        # Contenedor principal
        self.main_container = ctk.CTkFrame(self.parent, fg_color="white")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # TabView (3 Solapas)
        self.tabview = ctk.CTkTabview(self.main_container, segmented_button_selected_color="#8cb04e")
        self.tabview.pack(fill="both", expand=True)

        self.tab_detalle = self.tabview.add("Detalle de Cuenta")
        self.tab_ingresos = self.tabview.add("Ingresos / Compras")
        self.tab_pagos = self.tabview.add("Pagos / Remesas")

        # Construcción de la interfaz
        self._build_tab_detalle()
        self._build_tab_ingresos()
        self._build_tab_pagos()

        # Carga inicial de proveedores
        self._buscar_proveedores()

    def _build_tab_detalle(self):
        # --- 1. PANEL SUPERIOR: Búsqueda de Proveedor ---
        frame_busqueda = ctk.CTkFrame(self.tab_detalle, fg_color="#f0f0f0", corner_radius=6)
        frame_busqueda.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_busqueda, text="Buscar Proveedor:", font=("Arial", 14, "bold")).pack(side="left", padx=(15, 5), pady=10)

        self.entry_buscar_proveedor = ctk.CTkEntry(
            frame_busqueda, 
            placeholder_text="Nombre o Razón Social...", 
            width=220,
            font=("Arial", 13)
        )
        self.entry_buscar_proveedor.pack(side="left", padx=5, pady=10)
        self.entry_buscar_proveedor.bind("<Return>", lambda event: self._buscar_proveedores())

        btn_buscar_prov = ctk.CTkButton(
            frame_busqueda, 
            text="🔍 Buscar", 
            width=80,
            fg_color="#8cb04e", 
            hover_color="#7ba23c",
            text_color="black",
            command=self._buscar_proveedores
        )
        btn_buscar_prov.pack(side="left", padx=5, pady=10)

        self.combo_resultados = ctk.CTkComboBox(
            frame_busqueda, 
            width=240, 
            values=["Escriba y busque un proveedor..."],
            command=self._on_proveedor_selected
        )
        self.combo_resultados.pack(side="left", padx=5, pady=10)

        self.var_ocultar_liquidados = ctk.BooleanVar(value=True)
        self.chk_ocultar = ctk.CTkCheckBox(
            frame_busqueda,
            text="Ocultar Liquidados",
            variable=self.var_ocultar_liquidados,
            command=self.cargar_ctacte_proveedor,
            font=("Arial", 12)
        )
        self.chk_ocultar.pack(side="left", padx=10, pady=10)

        self.lbl_proveedor_activo = ctk.CTkLabel(
            frame_busqueda, 
            text="Proveedor: (Ninguno)", 
            font=("Arial", 13, "bold"), 
            text_color="#1a5276"
        )
        self.lbl_proveedor_activo.pack(side="left", padx=10, pady=10)

        # --- 2. PANEL CENTRAL: Grilla ---
        frame_grilla = ctk.CTkFrame(self.tab_detalle, fg_color="transparent")
        frame_grilla.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = (
            "id_cta", "fecha", "comprobante", "detalle", 
            "cantidad", "unidad", "pu", "debe", "haber", "saldo", "liquidado"
        )

        self.tree = ttk.Treeview(frame_grilla, columns=columns, show="headings", selectmode="browse")
        
        headers = {
            "id_cta": "ID", "fecha": "Fecha", "comprobante": "Comprobante",
            "detalle": "Detalle", "cantidad": "Cant.",
            "unidad": "Unidad", "pu": "P.U.", "debe": "Debe (-)",
            "haber": "Haber (+)", "saldo": "Saldo", "liquidado": "Liq."
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text)

        alignments = {
            "id_cta": ("center", 50), "fecha": ("center", 85), "comprobante": ("center", 110),
            "detalle": ("w", 260), "cantidad": ("e", 60),
            "unidad": ("center", 60), "pu": ("e", 75), "debe": ("e", 90),
            "haber": ("e", 90), "saldo": ("e", 100), "liquidado": ("center", 50)
        }
        
        for col, (anchor, width) in alignments.items():
            self.tree.column(col, anchor=anchor, width=width, stretch=True)

        scroll_y = ttk.Scrollbar(frame_grilla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_grilla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # --- 3. PANEL INFERIOR: Resumen de Saldos ---
        frame_resumen = ctk.CTkFrame(self.tab_detalle, fg_color="#d6e4f0", height=45)
        frame_resumen.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_total_debe = ctk.CTkLabel(frame_resumen, text="Total Debe: $0.00", font=("Arial", 13, "bold"), text_color="black")
        self.lbl_total_debe.pack(side="left", padx=15, pady=8)

        self.lbl_total_haber = ctk.CTkLabel(frame_resumen, text="Total Haber: $0.00", font=("Arial", 13, "bold"), text_color="black")
        self.lbl_total_haber.pack(side="left", padx=15, pady=8)

        btn_cierre = ctk.CTkButton(
            frame_resumen,
            text="🔒 Realizar Cierre de Período",
            fg_color="#c0392b",
            hover_color="#922b21",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self.realizar_cierre_periodo
        )
        btn_cierre.pack(side="right", padx=15, pady=8)
        
        btn_imprimir = ctk.CTkButton(
            frame_resumen,
            text="🖨️ Imprimir Detalle",
            fg_color="#27ae60",
            hover_color="#1e8449",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self.imprimir_detalle_ctacte
        )
        btn_imprimir.pack(side="right", padx=10, pady=8)

        self.lbl_saldo_total = ctk.CTkLabel(frame_resumen, text="Saldo Actual: $0.00", font=("Arial", 14, "bold"), text_color="#1a5276")
        self.lbl_saldo_total.pack(side="right", padx=20, pady=8)

    def _buscar_proveedores(self):
        """Busca proveedores por coincidencia parcial o carga la lista completa"""
        texto_busqueda = self.entry_buscar_proveedor.get().strip()

        if not self.db:
            return

        try:
            if texto_busqueda:
                query = """
                    SELECT id, proveedor 
                    FROM proveedores 
                    WHERE proveedor LIKE %s 
                    ORDER BY proveedor ASC 
                    LIMIT 50
                """
                params = (f"%{texto_busqueda}%",)
            else:
                query = """
                    SELECT id, proveedor 
                    FROM proveedores 
                    ORDER BY proveedor ASC 
                    LIMIT 100
                """
                params = ()
            
            filas = self.db.execute_query(query, params)

            if not filas:
                messagebox.showinfo("Búsqueda", "No se encontraron proveedores.")
                self.combo_resultados.configure(values=["Sin resultados"])
                self.combo_resultados.set("Sin resultados")
                self.mapa_busqueda = {}
                return

            self.mapa_busqueda = {f"{row[1]} (ID: {row[0]})": row[0] for row in filas}
            opciones = list(self.mapa_busqueda.keys())

            self.combo_resultados.configure(values=opciones)
            self.combo_resultados.set("Seleccione un proveedor...")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar proveedores:\n{e}")

    def cargar_ctacte_proveedor(self):
        """Carga los registros de la Cta. Cte. del proveedor filtrando opcionalmente los liquidados"""
        if not self.proveedor_seleccionado_id or not self.db:
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            ocultar_liquidados = self.var_ocultar_liquidados.get()

            query = """
                SELECT 
                    id_cta,
                    fecha,
                    comprobante,
                    detalle,
                    cantidad,
                    unidad,
                    pu,
                    debe,
                    haber,
                    liquidado
                FROM ctacteprov
                WHERE idproveedor = %s
                  AND (%s = FALSE OR liquidado = 0)
                ORDER BY fecha ASC, id_cta ASC
            """
            params = (self.proveedor_seleccionado_id, ocultar_liquidados)
            
            registros = self.db.execute_query(query, params) or []

            total_debe = 0.0
            total_haber = 0.0
            saldo_acumulado = 0.0

            for reg in registros:
                (id_cta, fecha, comp, det, cant, unidad, pu, debe, haber, liquidado) = reg

                debe_val = float(debe or 0.0)
                haber_val = float(haber or 0.0)

                total_debe += debe_val
                total_haber += haber_val
                # En cuentas corrientes de proveedores: Haber suma a la deuda, Debe la disminuye
                saldo_acumulado += (haber_val - debe_val)

                fecha_str = fecha.strftime("%d/%m/%Y") if fecha and hasattr(fecha, 'strftime') else (str(fecha) if fecha else "")

                self.tree.insert("", "end", values=(
                    id_cta,
                    fecha_str,
                    comp or "",
                    det or "",
                    f"{cant:.2f}" if cant is not None else "",
                    unidad or "",
                    f"{pu:.2f}" if pu is not None else "",
                    f"{debe_val:.2f}" if debe_val > 0 else "",
                    f"{haber_val:.2f}" if haber_val > 0 else "",
                    f"{saldo_acumulado:.2f}",
                    "Sí" if liquidado == 1 else "No"
                ))

            self.saldo_actual_proveedor = saldo_acumulado

            self.lbl_total_debe.configure(text=f"Total Debe: ${total_debe:,.2f}")
            self.lbl_total_haber.configure(text=f"Total Haber: ${total_haber:,.2f}")
            self.lbl_saldo_total.configure(text=f"Saldo Actual: ${saldo_acumulado:,.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar la cuenta corriente:\n{e}")

    def realizar_cierre_periodo(self):
        """Marca todos los movimientos actuales como liquidados (1) y arrastra el saldo si corresponde"""
        if not self.proveedor_seleccionado_id or not self.db:
            messagebox.showwarning("Atención", "Por favor seleccione un proveedor antes de realizar el cierre.")
            return

        nombre_proveedor = self.lbl_proveedor_activo.cget("text").replace("Proveedor: ", "")
        
        mensaje_confirmacion = (
            f"¿Desea cerrar el período actual para el proveedor:\n'{nombre_proveedor}'?\n\n"
            f"• Los movimientos abiertos actuales quedarán liquidados/saldados.\n"
            f"• Saldo actual a arrastrar: ${self.saldo_actual_proveedor:,.2f}"
        )
        
        if not messagebox.askyesno("Confirmar Cierre de Período", mensaje_confirmacion):
            return

        try:
            query_update = """
                UPDATE ctacteprov 
                SET liquidado = 1 
                WHERE idproveedor = %s AND liquidado = 0
            """
            self.db.execute_non_query(query_update, (self.proveedor_seleccionado_id,))

            if abs(self.saldo_actual_proveedor) > 0.001:
                fecha_hoy = datetime.date.today()
                
                haber_arrastre = self.saldo_actual_proveedor if self.saldo_actual_proveedor > 0 else 0.0
                debe_arrastre = abs(self.saldo_actual_proveedor) if self.saldo_actual_proveedor < 0 else 0.0

                query_insert = """
                    INSERT INTO ctacteprov 
                    (idproveedor, fecha, comprobante, detalle, debe, haber, liquidado)
                    VALUES (%s, %s, %s, %s, %s, %s, 0)
                """
                params_insert = (
                    self.proveedor_seleccionado_id,
                    fecha_hoy,
                    "CIERRE",
                    "CIERRE DE PERÍODO - SALDO ANTERIOR ARRASTRADO",
                    debe_arrastre,
                    haber_arrastre
                )
                self.db.execute_non_query(query_insert, params_insert)

            messagebox.showinfo("Éxito", "El cierre de período se completó correctamente.")
            self.cargar_ctacte_proveedor()

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al realizar el cierre de período:\n{e}")

    def _on_proveedor_selected(self, choice):
        if hasattr(self, 'mapa_busqueda') and choice in self.mapa_busqueda:
            self.proveedor_seleccionado_id = self.mapa_busqueda[choice]
            nombre_proveedor = choice.split(" (ID:")[0]
            self.lbl_proveedor_activo.configure(text=f"Proveedor: {nombre_proveedor}")
            self.cargar_ctacte_proveedor()

    def imprimir_detalle_ctacte(self):
        """Extrae los movimientos mostrados en la grilla actual y los envía a generar en PDF"""
        if not self.proveedor_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un proveedor para imprimir el detalle.")
            return

        filas = self.tree.get_children()
        if not filas:
            messagebox.showinfo("Impresión", "No hay movimientos cargados para imprimir.")
            return

        movimientos = []
        for item in filas:
            vals = self.tree.item(item, "values")
            movimientos.append({
                'fecha': vals[1],
                'comprobante': vals[2],
                'detalle': vals[3],
                'debe': vals[7] or "0.00",
                'haber': vals[8] or "0.00",
                'saldo': vals[9] or "0.00"
            })

        nombre_proveedor = self.lbl_proveedor_activo.cget("text").replace("Proveedor: ", "").strip()

        try:
            debe_txt = self.lbl_total_debe.cget("text").replace("Total Debe: $", "").replace(",", "")
            haber_txt = self.lbl_total_haber.cget("text").replace("Total Haber: $", "").replace(",", "")
            saldo_txt = self.lbl_saldo_total.cget("text").replace("Saldo Actual: $", "").replace(",", "")

            total_debe = float(debe_txt) if debe_txt else 0.0
            total_haber = float(haber_txt) if haber_txt else 0.0
            saldo_total = float(saldo_txt) if saldo_txt else 0.0

            filepath = generar_pdf_ctacte(
                nombre_cliente=f"PROVEEDOR: {nombre_proveedor}",
                movimientos=movimientos,
                total_debe=total_debe,
                total_haber=total_haber,
                saldo_total=saldo_total
            )
            abrir_pdf(filepath)

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la impresión:\n{e}")

    def _build_tab_ingresos(self):
        """Construye la interfaz Maestro-Detalle para el registro de Ingresos/Compras"""
        frame_cabecera = ctk.CTkFrame(self.tab_ingresos, fg_color="#f8f9fa", corner_radius=6)
        frame_cabecera.pack(fill="x", padx=10, pady=10)

        # Proveedor
        ctk.CTkLabel(frame_cabecera, text="Proveedor:", font=("Arial", 12, "bold"), text_color="black").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.entry_buscar_prov_ingreso = ctk.CTkEntry(frame_cabecera, placeholder_text="Buscar proveedor...", width=180)
        self.entry_buscar_prov_ingreso.grid(row=0, column=1, padx=5, pady=10)
        self.entry_buscar_prov_ingreso.bind("<Return>", lambda e: self._buscar_proveedores_ingreso())

        btn_buscar_prov_ingreso = ctk.CTkButton(
            frame_cabecera, text="🔍", width=40, fg_color="#8cb04e", hover_color="#7ba23c",
            text_color="black", command=self._buscar_proveedores_ingreso
        )
        btn_buscar_prov_ingreso.grid(row=0, column=2, padx=5, pady=10)

        self.combo_proveedores_ingreso = ctk.CTkComboBox(
            frame_cabecera, width=220, values=["Seleccione proveedor..."], command=self._on_proveedor_ingreso_selected
        )
        self.combo_proveedores_ingreso.grid(row=0, column=3, padx=5, pady=10)

        # Comprobante
        ctk.CTkLabel(frame_cabecera, text="N° Comprobante:", font=("Arial", 12, "bold"), text_color="black").grid(row=0, column=4, padx=(15, 5), pady=10, sticky="w")
        self.entry_comprobante_ingreso = ctk.CTkEntry(frame_cabecera, placeholder_text="Ej: FC-0001", width=120)
        self.entry_comprobante_ingreso.grid(row=0, column=5, padx=5, pady=10)

        # Checkbox Agregar a Cta Cte
        self.var_agregar_ctacte = ctk.BooleanVar(value=True)
        self.chk_ctacte = ctk.CTkCheckBox(
            frame_cabecera, text="Agregar a Cta. Cte.", variable=self.var_agregar_ctacte,
            font=("Arial", 12, "bold"), text_color="#1a5276"
        )
        self.chk_ctacte.grid(row=0, column=6, padx=15, pady=10)

        # Panel de Ítems
        frame_item = ctk.CTkFrame(self.tab_ingresos, fg_color="#edf2f7", corner_radius=6)
        frame_item.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(frame_item, text="Producto/Item:", font=("Arial", 11, "bold"), text_color="black").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.entry_producto = ctk.CTkEntry(frame_item, placeholder_text="Nombre / Descripción", width=220)
        self.entry_producto.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(frame_item, text="Cant.:", font=("Arial", 11, "bold"), text_color="black").grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.entry_cantidad = ctk.CTkEntry(frame_item, width=70)
        self.entry_cantidad.grid(row=0, column=3, padx=5, pady=8)

        ctk.CTkLabel(frame_item, text="P.U. ($):", font=("Arial", 11, "bold"), text_color="black").grid(row=0, column=4, padx=5, pady=8, sticky="w")
        self.entry_pu = ctk.CTkEntry(frame_item, width=90)
        self.entry_pu.grid(row=0, column=5, padx=5, pady=8)

        btn_agregar_item = ctk.CTkButton(
            frame_item, text="➕ Agregar Ítem", fg_color="#27ae60", hover_color="#1e8449",
            width=110, command=self._agregar_item_ingreso
        )
        btn_agregar_item.grid(row=0, column=6, padx=10, pady=8)

        btn_quitar_item = ctk.CTkButton(
            frame_item, text="❌ Quitar Ítem", fg_color="#e74c3c", hover_color="#c0392b",
            width=100, command=self._quitar_item_ingreso
        )
        btn_quitar_item.grid(row=0, column=7, padx=5, pady=8)

        # Grilla de Ítems
        frame_tabla_ingreso = ctk.CTkFrame(self.tab_ingresos, fg_color="transparent")
        frame_tabla_ingreso.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols_ingreso = ("id_prod", "producto", "cantidad", "pu", "subtotal")
        self.tree_ingreso = ttk.Treeview(frame_tabla_ingreso, columns=cols_ingreso, show="headings", selectmode="browse")

        self.tree_ingreso.heading("id_prod", text="ID Prod.")
        self.tree_ingreso.heading("producto", text="Producto / Detalle")
        self.tree_ingreso.heading("cantidad", text="Cantidad")
        self.tree_ingreso.heading("pu", text="P. Unitario")
        self.tree_ingreso.heading("subtotal", text="Subtotal")

        self.tree_ingreso.column("id_prod", anchor="center", width=70)
        self.tree_ingreso.column("producto", anchor="w", width=300)
        self.tree_ingreso.column("cantidad", anchor="e", width=90)
        self.tree_ingreso.column("pu", anchor="e", width=100)
        self.tree_ingreso.column("subtotal", anchor="e", width=120)

        scroll_ingreso_y = ttk.Scrollbar(frame_tabla_ingreso, orient="vertical", command=self.tree_ingreso.yview)
        self.tree_ingreso.configure(yscrollcommand=scroll_ingreso_y.set)

        scroll_ingreso_y.pack(side="right", fill="y")
        self.tree_ingreso.pack(fill="both", expand=True)

        # Pie
        frame_footer_ingreso = ctk.CTkFrame(self.tab_ingresos, fg_color="#d6e4f0", height=45)
        frame_footer_ingreso.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_total_ingreso = ctk.CTkLabel(
            frame_footer_ingreso, text="TOTAL INGRESO: $0.00", font=("Arial", 15, "bold"), text_color="#1a5276"
        )
        self.lbl_total_ingreso.pack(side="left", padx=20, pady=8)

        btn_guardar_ingreso = ctk.CTkButton(
            frame_footer_ingreso, text="💾 Registrar Ingreso", fg_color="#2980b9", hover_color="#1f618d",
            font=("Arial", 13, "bold"), command=self.guardar_ingreso
        )
        btn_guardar_ingreso.pack(side="right", padx=15, pady=8)

        self.proveedor_ingreso_id = None
        self.proveedor_ingreso_nombre = ""
        self._buscar_proveedores_ingreso()

    def _buscar_proveedores_ingreso(self):
        texto = self.entry_buscar_prov_ingreso.get().strip()
        if not self.db:
            return
        try:
            if texto:
                query = "SELECT id, proveedor FROM proveedores WHERE proveedor LIKE %s ORDER BY proveedor ASC LIMIT 50"
                params = (f"%{texto}%",)
            else:
                query = "SELECT id, proveedor FROM proveedores ORDER BY proveedor ASC LIMIT 100"
                params = ()
            
            filas = self.db.execute_query(query, params) or []
            self.mapa_proveedores_ingreso = {f"{row[1]} (ID: {row[0]})": (row[0], row[1]) for row in filas}
            opciones = list(self.mapa_proveedores_ingreso.keys())
            self.combo_proveedores_ingreso.configure(values=opciones if opciones else ["Sin resultados"])
            self.combo_proveedores_ingreso.set("Seleccione proveedor...")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar proveedores:\n{e}")

    def _on_proveedor_ingreso_selected(self, choice):
        if hasattr(self, 'mapa_proveedores_ingreso') and choice in self.mapa_proveedores_ingreso:
            self.proveedor_ingreso_id, self.proveedor_ingreso_nombre = self.mapa_proveedores_ingreso[choice]

    def _agregar_item_ingreso(self):
        prod = self.entry_producto.get().strip()
        cant_str = self.entry_cantidad.get().strip()
        pu_str = self.entry_pu.get().strip()

        if not prod:
            messagebox.showwarning("Atención", "Ingrese el nombre o descripción del producto.")
            return

        try:
            cant = float(cant_str)
            pu = float(pu_str)
            if cant <= 0 or pu < 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atención", "Ingrese valores numéricos válidos para Cantidad y P.U.")
            return

        subtotal = cant * pu
        id_producto_dummy = 0

        self.tree_ingreso.insert("", "end", values=(
            id_producto_dummy, prod, f"{cant:.2f}", f"{pu:.2f}", f"{subtotal:.2f}"
        ))

        self.entry_producto.delete(0, "end")
        self.entry_cantidad.delete(0, "end")
        self.entry_pu.delete(0, "end")
        self._recalcular_total_ingreso()

    def _quitar_item_ingreso(self):
        selected = self.tree_ingreso.selection()
        if selected:
            self.tree_ingreso.delete(selected[0])
            self._recalcular_total_ingreso()

    def _recalcular_total_ingreso(self):
        total = 0.0
        for item in self.tree_ingreso.get_children():
            vals = self.tree_ingreso.item(item, "values")
            total += float(vals[4])
        self.lbl_total_ingreso.configure(text=f"TOTAL INGRESO: ${total:,.2f}")

    def _build_tab_pagos(self):
        """Construye la interfaz para el registro de Pagos a Proveedores"""
        frame_pago = ctk.CTkFrame(self.tab_pagos, fg_color="#f8f9fa", corner_radius=6)
        frame_pago.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame_pago, text="💳 Registro de Pago a Proveedor", 
            font=("Arial", 16, "bold"), text_color="#1a5276"
        ).pack(pady=(15, 20))

        frame_prov = ctk.CTkFrame(frame_pago, fg_color="transparent")
        frame_prov.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_prov, text="Proveedor:", font=("Arial", 12, "bold"), text_color="black", width=120, anchor="w").pack(side="left")
        
        self.entry_buscar_prov_pago = ctk.CTkEntry(frame_prov, placeholder_text="Buscar proveedor...", width=180)
        self.entry_buscar_prov_pago.pack(side="left", padx=5)
        self.entry_buscar_prov_pago.bind("<Return>", lambda e: self._buscar_proveedores_pago())

        btn_buscar_prov_pago = ctk.CTkButton(
            frame_prov, text="🔍", width=40, fg_color="#8cb04e", hover_color="#7ba23c",
            text_color="black", command=self._buscar_proveedores_pago
        )
        btn_buscar_prov_pago.pack(side="left", padx=5)

        self.combo_proveedores_pago = ctk.CTkComboBox(
            frame_prov, width=250, values=["Seleccione proveedor..."], command=self._on_proveedor_pago_selected
        )
        self.combo_proveedores_pago.pack(side="left", padx=5)

        fields = [
            ("N° Comprobante / Orden Pago:", "entry_comp_pago", "Ej: OP-0001"),
            ("Monto Abonado ($):", "entry_monto_pago", "0.00"),
            ("Forma de Pago:", "combo_forma_pago", ["Efectivo", "Transferencia", "Cheque", "Mercado Pago", "Otro"]),
            ("Detalle / Observación:", "entry_detalle_pago", "Ej: Pago a cuenta / Cancela factura N° X")
        ]

        for label_text, attr_name, default_val in fields:
            f = ctk.CTkFrame(frame_pago, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=8)

            ctk.CTkLabel(f, text=label_text, font=("Arial", 12, "bold"), text_color="black", width=160, anchor="w").pack(side="left")

            if isinstance(default_val, list):
                widget = ctk.CTkComboBox(f, values=default_val, width=250)
                widget.set(default_val[0])
            else:
                widget = ctk.CTkEntry(f, placeholder_text=default_val, width=250)
            
            setattr(self, attr_name, widget)
            widget.pack(side="left", padx=5)

        btn_registrar = ctk.CTkButton(
            frame_pago, text="💾 Registrar Pago", fg_color="#27ae60", hover_color="#1e8449",
            font=("Arial", 14, "bold"), height=40, command=self.guardar_pago
        )
        btn_registrar.pack(pady=30)

        self.proveedor_pago_id = None
        self._buscar_proveedores_pago()

    def _buscar_proveedores_pago(self):
        texto = self.entry_buscar_prov_pago.get().strip()
        if not self.db:
            return
        try:
            if texto:
                query = "SELECT id, proveedor FROM proveedores WHERE proveedor LIKE %s ORDER BY proveedor ASC LIMIT 50"
                params = (f"%{texto}%",)
            else:
                query = "SELECT id, proveedor FROM proveedores ORDER BY proveedor ASC LIMIT 100"
                params = ()
            
            filas = self.db.execute_query(query, params) or []
            self.mapa_proveedores_pago = {f"{row[1]} (ID: {row[0]})": row[0] for row in filas}
            opciones = list(self.mapa_proveedores_pago.keys())
            self.combo_proveedores_pago.configure(values=opciones if opciones else ["Sin resultados"])
            self.combo_proveedores_pago.set("Seleccione proveedor...")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar proveedores:\n{e}")

    def _on_proveedor_pago_selected(self, choice):
        if hasattr(self, 'mapa_proveedores_pago') and choice in self.mapa_proveedores_pago:
            self.proveedor_pago_id = self.mapa_proveedores_pago[choice]

    def guardar_pago(self):
        """Persiste el pago al proveedor impactando en el DEBE (Reduce la deuda)"""
        if not self.proveedor_pago_id:
            messagebox.showwarning("Atención", "Seleccione un proveedor para registrar el pago.")
            return

        comprobante = self.entry_comp_pago.get().strip() or "ORDEN DE PAGO"
        monto_str = self.entry_monto_pago.get().strip()
        forma_pago = self.combo_forma_pago.get()
        obs = self.entry_detalle_pago.get().strip()

        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atención", "Ingrese un monto válido y mayor a 0.")
            return

        detalle = f"PAGO PROVEEDOR ({forma_pago})"
        if obs:
            detalle += f" - {obs}"

        try:
            fecha_actual = datetime.date.today()
            
            # En proveedores, los Pagos Realizados impactan en el DEBE para reducir el saldo
            query_cta = """
                INSERT INTO ctacteprov 
                (idproveedor, fecha, comprobante, detalle, cantidad, unidad, pu, debe, haber, liquidado)
                VALUES (%s, %s, %s, %s, NULL, NULL, NULL, %s, 0.0, 0)
            """
            params_cta = (self.proveedor_pago_id, fecha_actual, comprobante, detalle, monto)
            self.db.execute_non_query(query_cta, params_cta)

            messagebox.showinfo("Éxito", f"Pago de ${monto:,.2f} registrado correctamente.")

            self.entry_monto_pago.delete(0, "end")
            self.entry_comp_pago.delete(0, "end")
            self.entry_detalle_pago.delete(0, "end")

            if self.proveedor_seleccionado_id == self.proveedor_pago_id:
                self.cargar_ctacte_proveedor()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el pago:\n{e}")

    def guardar_ingreso(self):
        """Persiste la compra/ingreso e impacta opcionalmente en el HABER de ctacteprov"""
        if not self.proveedor_ingreso_id:
            messagebox.showwarning("Atención", "Seleccione un proveedor para el ingreso.")
            return

        items = self.tree_ingreso.get_children()
        if not items:
            messagebox.showwarning("Atención", "Debe agregar al menos un ítem al detalle.")
            return

        comprobante = self.entry_comprobante_ingreso.get().strip() or "S/N"
        fecha_actual = datetime.datetime.now()
        agregar_a_ctacte = self.var_agregar_ctacte.get()

        try:
            # 1. Registro de Ingreso / Compra
            query_ingreso = """
                INSERT INTO ingresos (fecha, idproveedor, proveedor, comprobante)
                VALUES (%s, %s, %s, %s)
            """
            params_ingreso = (fecha_actual, self.proveedor_ingreso_id, self.proveedor_ingreso_nombre, comprobante)
            id_ingreso_generado = self.db.execute_insert_get_id(query_ingreso, params_ingreso)

            # 2. Registrar Detalle e Impactar Cta Cte
            for item in items:
                vals = self.tree_ingreso.item(item, "values")
                id_prod = int(vals[0])
                prod_nombre = vals[1]
                cant = float(vals[2])
                pu = float(vals[3])
                subtotal = float(vals[4])

                query_det = """
                    INSERT INTO detalle_ingreso (idingreso, idproducto, producto, cantidad, pu, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.db.execute_non_query(query_det, (id_ingreso_generado, id_prod, prod_nombre, cant, pu, subtotal))

                # En cuentas de proveedores, las compras aumentan la deuda (HABER)
                if agregar_a_ctacte:
                    query_cta = """
                        INSERT INTO ctacteprov 
                        (idproveedor, fecha, comprobante, detalle, cantidad, unidad, pu, debe, haber, liquidado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                    """
                    params_cta = (
                        self.proveedor_ingreso_id,
                        fecha_actual.date(),
                        comprobante,
                        prod_nombre,
                        cant,
                        "unid",
                        pu,
                        0.0,
                        subtotal  # Haber (Aumenta deuda con proveedor)
                    )
                    self.db.execute_non_query(query_cta, params_cta)

            messagebox.showinfo("Éxito", f"Ingreso N° {id_ingreso_generado} registrado correctamente.")
            
            for item in items:
                self.tree_ingreso.delete(item)
            self.entry_comprobante_ingreso.delete(0, "end")
            self._recalcular_total_ingreso()

            if self.proveedor_seleccionado_id == self.proveedor_ingreso_id:
                self.cargar_ctacte_proveedor()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el ingreso:\n{e}")