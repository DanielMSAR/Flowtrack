import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox
from ctacte_pdf_generator import generar_pdf_ctacte, abrir_pdf

class CtaCteClientesView:
    def __init__(self, parent_frame, db_connection):
        self.parent = parent_frame
        self.db = db_connection
        self.cliente_seleccionado_id = None
        self.clientes_encontrados = []  # Mantiene las coincidencias de la búsqueda
        self.saldo_actual_cliente = 0.0 # Mantiene el saldo calculado actual

        # Contenedor principal de la vista
        self.main_container = ctk.CTkFrame(self.parent, fg_color="white")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Configuración del TabView (Las 3 Solapas)
        self.tabview = ctk.CTkTabview(self.main_container, segmented_button_selected_color="#8cb04e")
        self.tabview.pack(fill="both", expand=True)

        self.tab_detalle = self.tabview.add("Detalle de Cuenta")
        self.tab_salidas = self.tabview.add("Salidas")
        self.tab_pagos = self.tabview.add("Pagos")

        # Construir la interfaz de la solapa "Detalle de Cuenta"
        self._build_tab_detalle()
        
        self._build_tab_salidas()  # <--- ¡AGREGA ESTA LÍNEA AQUÍ!
        
        # CARGA INICIAL AUTOMÁTICA
        self._buscar_clientes()
        

    def _build_tab_detalle(self):
        # --- 1. PANEL SUPERIOR: Búsqueda de Cliente por Nombre ---
        frame_busqueda = ctk.CTkFrame(self.tab_detalle, fg_color="#f0f0f0", corner_radius=6)
        frame_busqueda.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_busqueda, text="Buscar Cliente:", font=("Arial", 14, "bold")).pack(side="left", padx=(15, 5), pady=10)

        # Campo de entrada de texto
        self.entry_buscar_cliente = ctk.CTkEntry(
            frame_busqueda, 
            placeholder_text="Ingrese nombre o razón social...", 
            width=220,
            font=("Arial", 13)
        )
        self.entry_buscar_cliente.pack(side="left", padx=5, pady=10)
        
        # Al presionar Enter en el cuadro de búsqueda, dispara la búsqueda
        self.entry_buscar_cliente.bind("<Return>", lambda event: self._buscar_clientes())

        # Botón Buscar Cliente
        btn_buscar_cli = ctk.CTkButton(
            frame_busqueda, 
            text="🔍 Buscar", 
            width=80,
            fg_color="#8cb04e", 
            hover_color="#7ba23c",
            text_color="black",
            command=self._buscar_clientes
        )
        btn_buscar_cli.pack(side="left", padx=5, pady=10)

        # Combo que se rellena dinámicamente con los resultados encontrados
        self.combo_resultados = ctk.CTkComboBox(
            frame_busqueda, 
            width=240, 
            values=["Escriba y busque un cliente..."],
            command=self._on_cliente_selected
        )
        self.combo_resultados.pack(side="left", padx=5, pady=10)

        # Checkbox para Ocultar/Mostrar Movimientos Liquidados/Saldados
        self.var_ocultar_liquidados = ctk.BooleanVar(value=True)
        self.chk_ocultar = ctk.CTkCheckBox(
            frame_busqueda,
            text="Ocultar Liquidados",
            variable=self.var_ocultar_liquidados,
            command=self.cargar_ctacte_cliente,
            font=("Arial", 12)
        )
        self.chk_ocultar.pack(side="left", padx=10, pady=10)

        # Indicador/Etiqueta del cliente activo cargado
        self.lbl_cliente_activo = ctk.CTkLabel(
            frame_busqueda, 
            text="Cliente: (Ninguno)", 
            font=("Arial", 13, "bold"), 
            text_color="#1a5276"
        )
        self.lbl_cliente_activo.pack(side="left", padx=10, pady=10)

        # --- 2. PANEL CENTRAL: Grilla / Tabla (Treeview) ---
        frame_grilla = ctk.CTkFrame(self.tab_detalle, fg_color="transparent")
        frame_grilla.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configuración de columnas (SIN "producto")
        columns = (
            "id_cta", "fecha", "comprobante", "detalle", 
            "cantidad", "unidad", "pu", "debe", "haber", "saldo", "liquidado"
        )

        self.tree = ttk.Treeview(frame_grilla, columns=columns, show="headings", selectmode="browse")
        
        # Encabezados (SIN "producto")
        headers = {
            "id_cta": "ID", "fecha": "Fecha", "comprobante": "Comprobante",
            "detalle": "Detalle", "cantidad": "Cant.",
            "unidad": "Unidad", "pu": "P.U.", "debe": "Debe (+)",
            "haber": "Haber (-)", "saldo": "Saldo", "liquidado": "Liq."
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text)

        # Anchos y alineaciones (SIN "producto")
        alignments = {
            "id_cta": ("center", 50), "fecha": ("center", 85), "comprobante": ("center", 110),
            "detalle": ("w", 260), "cantidad": ("e", 60),
            "unidad": ("center", 60), "pu": ("e", 75), "debe": ("e", 90),
            "haber": ("e", 90), "saldo": ("e", 100), "liquidado": ("center", 50)
        }
        
        for col, (anchor, width) in alignments.items():
            self.tree.column(col, anchor=anchor, width=width, stretch=True)

        # Scrollbars
        scroll_y = ttk.Scrollbar(frame_grilla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_grilla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # --- 3. PANEL INFERIOR: Resumen de Saldos y Cierre de Período ---
        frame_resumen = ctk.CTkFrame(self.tab_detalle, fg_color="#d6e4f0", height=45)
        frame_resumen.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_total_debe = ctk.CTkLabel(frame_resumen, text="Total Debe: $0.00", font=("Arial", 13, "bold"), text_color="black")
        self.lbl_total_debe.pack(side="left", padx=15, pady=8)

        self.lbl_total_haber = ctk.CTkLabel(frame_resumen, text="Total Haber: $0.00", font=("Arial", 13, "bold"), text_color="black")
        self.lbl_total_haber.pack(side="left", padx=15, pady=8)

        # Botón para realizar Cierre de Período / Cierre de Cuenta
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
        
        # Botón Imprimir Detalle (Agregar al lado del botón de Cierre de Período)
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

    def _buscar_clientes(self):
        """Busca clientes por coincidencia parcial o carga la lista completa si el texto está vacío"""
        texto_busqueda = self.entry_buscar_cliente.get().strip()

        if not self.db:
            return

        try:
            # Si el texto está vacío trae los primeros 100 clientes, si no, filtra por nombre
            if texto_busqueda:
                query = """
                    SELECT id, cliente 
                    FROM clientes 
                    WHERE cliente LIKE %s 
                    ORDER BY cliente ASC 
                    LIMIT 50
                """
                params = (f"%{texto_busqueda}%",)
            else:
                query = """
                    SELECT id, cliente 
                    FROM clientes 
                    ORDER BY cliente ASC 
                    LIMIT 100
                """
                params = ()
            
            filas = self.db.execute_query(query, params)

            if not filas:
                messagebox.showinfo("Búsqueda", "No se encontraron clientes.")
                self.combo_resultados.configure(values=["Sin resultados"])
                self.combo_resultados.set("Sin resultados")
                self.mapa_busqueda = {}
                return

            self.mapa_busqueda = {f"{row[1]} (ID: {row[0]})": row[0] for row in filas}
            opciones = list(self.mapa_busqueda.keys())

            # Cargar opciones en el ComboBox
            self.combo_resultados.configure(values=opciones)
            
            # Placeholder inicial sugerente
            self.combo_resultados.set("Seleccione un cliente...")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar clientes:\n{e}")
            
            
    def cargar_ctacte_cliente(self):
        """Carga los registros de la Cta. Cte. del cliente filtrando opcionalmente los liquidados"""
        if not self.cliente_seleccionado_id or not self.db:
            return

        # Limpiar grilla antes de cargar
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            ocultar_liquidados = self.var_ocultar_liquidados.get()

            # Consulta SQL simplificada sin la tabla productos
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
                FROM ctacteclientes
                WHERE idcliente = %s
                  AND (%s = FALSE OR liquidado = 0)
                ORDER BY fecha ASC, id_cta ASC
            """
            params = (self.cliente_seleccionado_id, ocultar_liquidados)
            
            registros = self.db.execute_query(query, params) or []

            total_debe = 0.0
            total_haber = 0.0
            saldo_acumulado = 0.0

            for reg in registros:
                # Desempaquetado sin campo producto
                (id_cta, fecha, comp, det, cant, unidad, pu, debe, haber, liquidado) = reg

                debe_val = float(debe or 0.0)
                haber_val = float(haber or 0.0)

                total_debe += debe_val
                total_haber += haber_val
                saldo_acumulado += (debe_val - haber_val)

                # Formateo seguro de fecha
                fecha_str = fecha.strftime("%d/%m/%Y") if fecha and hasattr(fecha, 'strftime') else (str(fecha) if fecha else "")

                # Inserción en la grilla sin la columna producto
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

            # Guardar el saldo global resultante para ser usado en cierres
            self.saldo_actual_cliente = saldo_acumulado

            # Actualizar totales inferiores
            self.lbl_total_debe.configure(text=f"Total Debe: ${total_debe:,.2f}")
            self.lbl_total_haber.configure(text=f"Total Haber: ${total_haber:,.2f}")
            self.lbl_saldo_total.configure(text=f"Saldo Actual: ${saldo_acumulado:,.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar la cuenta corriente:\n{e}")
            
            
    def realizar_cierre_periodo(self):
        """Marca todos los movimientos actuales como liquidados (1) y arrastra el saldo si corresponde"""
        if not self.cliente_seleccionado_id or not self.db:
            messagebox.showwarning("Atención", "Por favor seleccione un cliente antes de realizar el cierre.")
            return

        nombre_cliente = self.lbl_cliente_activo.cget("text").replace("Cliente: ", "")
        
        # Confirmación del usuario
        mensaje_confirmacion = (
            f"¿Desea cerrar el período actual para el cliente:\n'{nombre_cliente}'?\n\n"
            f"• Los movimientos abiertos actuales quedarán liquidados/saldados.\n"
            f"• Saldo actual a arrastrar: ${self.saldo_actual_cliente:,.2f}"
        )
        
        if not messagebox.askyesno("Confirmar Cierre de Período", mensaje_confirmacion):
            return

        try:
            # 1. Marcar todos los registros no liquidados actuales como liquidados (1)
            query_update = """
                UPDATE ctacteclientes 
                SET liquidado = 1 
                WHERE idcliente = %s AND liquidado = 0
            """
            self.db.execute_non_query(query_update, (self.cliente_seleccionado_id,))

            # 2. Si existía un saldo distinto de 0, creamos la fila de apertura con el saldo arrastrado
            if abs(self.saldo_actual_cliente) > 0.001:
                fecha_hoy = datetime.date.today()
                
                debe_arrastre = self.saldo_actual_cliente if self.saldo_actual_cliente > 0 else 0.0
                haber_arrastre = abs(self.saldo_actual_cliente) if self.saldo_actual_cliente < 0 else 0.0

                query_insert = """
                    INSERT INTO ctacteclientes 
                    (idcliente, fecha, comprobante, detalle, debe, haber, liquidado)
                    VALUES (%s, %s, %s, %s, %s, %s, 0)
                """
                params_insert = (
                    self.cliente_seleccionado_id,
                    fecha_hoy,
                    "CIERRE",
                    "CIERRE DE PERÍODO - SALDO ANTERIOR ARRASTRADO",
                    debe_arrastre,
                    haber_arrastre
                )
                self.db.execute_non_query(query_insert, params_insert)

            messagebox.showinfo("Éxito", "El cierre de período se completó correctamente.")
            
            # Recargar la grilla para ver los cambios reflejados
            self.cargar_ctacte_cliente()

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al realizar el cierre de período:\n{e}")

    def _on_cliente_selected(self, choice):
        """Captura el cliente elegido del selector desplegable"""
        if hasattr(self, 'mapa_busqueda') and choice in self.mapa_busqueda:
            self.cliente_seleccionado_id = self.mapa_busqueda[choice]
            # Extraer solo el nombre limpio para el label
            nombre_cliente = choice.split(" (ID:")[0]
            self.lbl_cliente_activo.configure(text=f"Cliente: {nombre_cliente}")
            
            # Cargar automáticamente los datos del cliente en la grilla
            self.cargar_ctacte_cliente()
    def imprimir_detalle_ctacte(self):
        """Extrae los movimientos mostrados en la grilla actual y los envía a generar en PDF"""
        if not self.cliente_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un cliente para imprimir el detalle.")
            return

        filas = self.tree.get_children()
        if not filas:
            messagebox.showinfo("Impresión", "No hay movimientos cargados para imprimir.")
            return

        movimientos = []
        for item in filas:
            vals = self.tree.item(item, "values")
            # Estructura alineada con las columnas del Treeview
            movimientos.append({
                'fecha': vals[1],
                'comprobante': vals[2],
                'detalle': vals[3],
                'debe': vals[7] or "0.00",
                'haber': vals[8] or "0.00",
                'saldo': vals[9] or "0.00"
            })

        nombre_cliente = self.lbl_cliente_activo.cget("text").replace("Cliente: ", "").strip()

        try:
            # Calcular / parsear totales
            debe_txt = self.lbl_total_debe.cget("text").replace("Total Debe: $", "").replace(",", "")
            haber_txt = self.lbl_total_haber.cget("text").replace("Total Haber: $", "").replace(",", "")
            saldo_txt = self.lbl_saldo_total.cget("text").replace("Saldo Actual: $", "").replace(",", "")

            total_debe = float(debe_txt) if debe_txt else 0.0
            total_haber = float(haber_txt) if haber_txt else 0.0
            saldo_total = float(saldo_txt) if saldo_txt else 0.0

            filepath = generar_pdf_ctacte(
                nombre_cliente=nombre_cliente,
                movimientos=movimientos,
                total_debe=total_debe,
                total_haber=total_haber,
                saldo_total=saldo_total
            )
            abrir_pdf(filepath)

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la impresión:\n{e}")
    def _build_tab_salidas(self):
        """Construye la interfaz Maestro-Detalle para el registro de Salidas"""
        # --- 1. PANEL SUPERIOR: Datos de la Salida (Cabecera) ---
        frame_cabecera = ctk.CTkFrame(self.tab_salidas, fg_color="#f8f9fa", corner_radius=6)
        frame_cabecera.pack(fill="x", padx=10, pady=10)

        # Cliente
        ctk.CTkLabel(frame_cabecera, text="Cliente:", font=("Arial", 12, "bold"),text_color="black").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.entry_buscar_cli_salida = ctk.CTkEntry(frame_cabecera, placeholder_text="Buscar cliente...", width=180)
        self.entry_buscar_cli_salida.grid(row=0, column=1, padx=5, pady=10)
        self.entry_buscar_cli_salida.bind("<Return>", lambda e: self._buscar_clientes_salida())

        btn_buscar_cli_salida = ctk.CTkButton(
            frame_cabecera, text="🔍", width=40, fg_color="#8cb04e", hover_color="#7ba23c",
            text_color="black", command=self._buscar_clientes_salida
        )
        btn_buscar_cli_salida.grid(row=0, column=2, padx=5, pady=10)

        self.combo_clientes_salida = ctk.CTkComboBox(
            frame_cabecera, width=220, values=["Seleccione cliente..."], command=self._on_cliente_salida_selected
        )
        self.combo_clientes_salida.grid(row=0, column=3, padx=5, pady=10)

        # Comprobante
        ctk.CTkLabel(frame_cabecera, text="N° Comprobante:", font=("Arial", 12, "bold"),text_color="black").grid(row=0, column=4, padx=(15, 5), pady=10, sticky="w")
        self.entry_comprobante = ctk.CTkEntry(frame_cabecera, placeholder_text="Ej: REM-0001", width=120)
        self.entry_comprobante.grid(row=0, column=5, padx=5, pady=10)

        # Checkbox Agregar a Cta Cte
        self.var_agregar_ctacte = ctk.BooleanVar(value=True)
        self.chk_ctacte = ctk.CTkCheckBox(
            frame_cabecera, text="Agregar a Cta. Cte.", variable=self.var_agregar_ctacte,
            font=("Arial", 12, "bold"), text_color="#1a5276"
        )
        self.chk_ctacte.grid(row=0, column=6, padx=15, pady=10)

        # --- 2. PANEL INTERMEDIO: Entrada de Productos (Detalle) ---
        frame_item = ctk.CTkFrame(self.tab_salidas, fg_color="#edf2f7", corner_radius=6)
        frame_item.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(frame_item, text="Producto:", font=("Arial", 11, "bold"),text_color="black").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.entry_producto = ctk.CTkEntry(frame_item, placeholder_text="Nombre / Descripción", width=220)
        self.entry_producto.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(frame_item, text="Cant.:", font=("Arial", 11, "bold"),text_color="black").grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.entry_cantidad = ctk.CTkEntry(frame_item, width=70)
        self.entry_cantidad.grid(row=0, column=3, padx=5, pady=8)

        ctk.CTkLabel(frame_item, text="P.U. ($):", font=("Arial", 11, "bold"),text_color="black").grid(row=0, column=4, padx=5, pady=8, sticky="w")
        self.entry_pu = ctk.CTkEntry(frame_item, width=90)
        self.entry_pu.grid(row=0, column=5, padx=5, pady=8)

        btn_agregar_item = ctk.CTkButton(
            frame_item, text="➕ Agregar Ítem", fg_color="#27ae60", hover_color="#1e8449",
            width=110, command=self._agregar_item_salida
        )
        btn_agregar_item.grid(row=0, column=6, padx=10, pady=8)

        btn_quitar_item = ctk.CTkButton(
            frame_item, text="❌ Quitar Ítem", fg_color="#e74c3c", hover_color="#c0392b",
            width=100, command=self._quitar_item_salida
        )
        btn_quitar_item.grid(row=0, column=7, padx=5, pady=8)

        # --- 3. GRILLA DE ÍTEMS INGRESADOS ---
        frame_tabla_salida = ctk.CTkFrame(self.tab_salidas, fg_color="transparent")
        frame_tabla_salida.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols_salida = ("id_prod", "producto", "cantidad", "pu", "subtotal")
        self.tree_salida = ttk.Treeview(frame_tabla_salida, columns=cols_salida, show="headings", selectmode="browse")

        self.tree_salida.heading("id_prod", text="ID Prod.")
        self.tree_salida.heading("producto", text="Producto / Detalle")
        self.tree_salida.heading("cantidad", text="Cantidad")
        self.tree_salida.heading("pu", text="P. Unitario")
        self.tree_salida.heading("subtotal", text="Subtotal")

        self.tree_salida.column("id_prod", anchor="center", width=70)
        self.tree_salida.column("producto", anchor="w", width=300)
        self.tree_salida.column("cantidad", anchor="e", width=90)
        self.tree_salida.column("pu", anchor="e", width=100)
        self.tree_salida.column("subtotal", anchor="e", width=120)

        scroll_salida_y = ttk.Scrollbar(frame_tabla_salida, orient="vertical", command=self.tree_salida.yview)
        self.tree_salida.configure(yscrollcommand=scroll_salida_y.set)

        scroll_salida_y.pack(side="right", fill="y")
        self.tree_salida.pack(fill="both", expand=True)

        # --- 4. PIE: TOTAL Y BOTÓN DE GUARDAR ---
        frame_footer_salida = ctk.CTkFrame(self.tab_salidas, fg_color="#d6e4f0", height=45)
        frame_footer_salida.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_total_salida = ctk.CTkLabel(
            frame_footer_salida, text="TOTAL SALIDA: $0.00", font=("Arial", 15, "bold"), text_color="#1a5276"
        )
        self.lbl_total_salida.pack(side="left", padx=20, pady=8)

        btn_guardar_salida = ctk.CTkButton(
            frame_footer_salida, text="💾 Registrar Salida", fg_color="#2980b9", hover_color="#1f618d",
            font=("Arial", 13, "bold"), command=self.guardar_salida
        )
        btn_guardar_salida.pack(side="right", padx=15, pady=8)

        # Estado interno de la salida
        self.cliente_salida_id = None
        self.cliente_salida_nombre = ""
        self._buscar_clientes_salida()    
        
    def _buscar_clientes_salida(self):
        """Busca clientes para el selector de la solapa Salidas"""
        texto = self.entry_buscar_cli_salida.get().strip()
        if not self.db:
            return
        try:
            if texto:
                query = "SELECT id, cliente FROM clientes WHERE cliente LIKE %s ORDER BY cliente ASC LIMIT 50"
                params = (f"%{texto}%",)
            else:
                query = "SELECT id, cliente FROM clientes ORDER BY cliente ASC LIMIT 100"
                params = ()
            
            filas = self.db.execute_query(query, params) or []
            self.mapa_clientes_salida = {f"{row[1]} (ID: {row[0]})": (row[0], row[1]) for row in filas}
            opciones = list(self.mapa_clientes_salida.keys())
            self.combo_clientes_salida.configure(values=opciones if opciones else ["Sin resultados"])
            self.combo_clientes_salida.set("Seleccione cliente...")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar clientes:\n{e}")

    def _on_cliente_salida_selected(self, choice):
        if hasattr(self, 'mapa_clientes_salida') and choice in self.mapa_clientes_salida:
            self.cliente_salida_id, self.cliente_salida_nombre = self.mapa_clientes_salida[choice]

    def _agregar_item_salida(self):
        """Valida e inserta un ítem en el Treeview temporal de la Salida"""
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
        id_producto_dummy = 0  # Si no usas tabla de productos estricta

        self.tree_salida.insert("", "end", values=(
            id_producto_dummy, prod, f"{cant:.2f}", f"{pu:.2f}", f"{subtotal:.2f}"
        ))

        # Limpiar campos de ítem
        self.entry_producto.delete(0, "end")
        self.entry_cantidad.delete(0, "end")
        self.entry_pu.delete(0, "end")
        self._recalcular_total_salida()

    def _quitar_item_salida(self):
        selected = self.tree_salida.selection()
        if selected:
            self.tree_salida.delete(selected[0])
            self._recalcular_total_salida()

    def _recalcular_total_salida(self):
        total = 0.0
        for item in self.tree_salida.get_children():
            vals = self.tree_salida.item(item, "values")
            total += float(vals[4])
        self.lbl_total_salida.configure(text=f"TOTAL SALIDA: ${total:,.2f}")

    def guardar_salida(self):
        """Persiste el Maestro-Detalle de Salida e impacta opcionalmente en la Cta Cte"""
        if not self.cliente_salida_id:
            messagebox.showwarning("Atención", "Seleccione un cliente para la salida.")
            return

        items = self.tree_salida.get_children()
        if not items:
            messagebox.showwarning("Atención", "Debe agregar al menos un ítem al detalle.")
            return

        comprobante = self.entry_comprobante.get().strip() or "S/N"
        fecha_actual = datetime.datetime.now()
        agregar_a_ctacte = self.var_agregar_ctacte.get()

        try:
            # 1. Insertar Cabecera de Salida
            query_salida = """
                INSERT INTO salidas (fecha, idcliente, cliente, comprobante)
                VALUES (%s, %s, %s, %s)
            """
            params_salida = (fecha_actual, self.cliente_salida_id, self.cliente_salida_nombre, comprobante)
            id_salida_generado = self.db.execute_insert_get_id(query_salida, params_salida)

            # 2. Insertar Detalle e Impactar en Cta. Cte.
            for item in items:
                vals = self.tree_salida.item(item, "values")
                id_prod = int(vals[0])
                prod_nombre = vals[1]
                cant = float(vals[2])
                pu = float(vals[3])
                subtotal = float(vals[4])

                # Guardar en detalle_salida
                query_det = """
                    INSERT INTO detalle_salida (idsalida, idproducto, producto, cantidad, pu, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.db.execute_non_query(query_det, (id_salida_generado, id_prod, prod_nombre, cant, pu, subtotal))

                # 3. Si está tildado, impactar en Cta Cte
                if agregar_a_ctacte:
                    query_cta = """
                        INSERT INTO ctacteclientes 
                        (idcliente, fecha, comprobante, detalle, cantidad, unidad, pu, debe, haber, liquidado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                    """
                    params_cta = (
                        self.cliente_salida_id,
                        fecha_actual.date(),
                        comprobante,
                        prod_nombre,
                        cant,
                        "unid",
                        pu,
                        subtotal,  # Debe (aumenta deuda)
                        0.0
                    )
                    self.db.execute_non_query(query_cta, params_cta)

            messagebox.showinfo("Éxito", f"Salida N° {id_salida_generado} registrada correctamente.")
            
            # Limpiar formulario
            for item in items:
                self.tree_salida.delete(item)
            self.entry_comprobante.delete(0, "end")
            self._recalcular_total_salida()

            # Si se afectó la Cta Cte y es el cliente actualmente activo en la Solapa 1, recargar
            if self.cliente_seleccionado_id == self.cliente_salida_id:
                self.cargar_ctacte_cliente()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la salida:\n{e}")    