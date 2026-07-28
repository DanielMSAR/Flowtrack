import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox

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

        # Configuración de columnas
        columns = (
            "id_cta", "fecha", "comprobante", "producto", "detalle", 
            "cantidad", "unidad", "pu", "debe", "haber", "saldo", "liquidado"
        )

        self.tree = ttk.Treeview(frame_grilla, columns=columns, show="headings", selectmode="browse")
        
        # Encabezados
        headers = {
            "id_cta": "ID", "fecha": "Fecha", "comprobante": "Comprobante",
            "producto": "Producto", "detalle": "Detalle", "cantidad": "Cant.",
            "unidad": "Unidad", "pu": "P.U.", "debe": "Debe (+)",
            "haber": "Haber (-)", "saldo": "Saldo", "liquidado": "Liq."
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text)

        # Anchos y alineaciones
        alignments = {
            "id_cta": ("center", 50), "fecha": ("center", 85), "comprobante": ("center", 110),
            "producto": ("w", 120), "detalle": ("w", 180), "cantidad": ("e", 60),
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

        self.lbl_saldo_total = ctk.CTkLabel(frame_resumen, text="Saldo Actual: $0.00", font=("Arial", 14, "bold"), text_color="#1a5276")
        self.lbl_saldo_total.pack(side="right", padx=20, pady=8)

    def _buscar_clientes(self):
        """Busca clientes por coincidencia parcial usando execute_query() de Database"""
        texto_busqueda = self.entry_buscar_cliente.get().strip()

        if not self.db:
            return

        try:
            query = """
                SELECT id, cliente 
                FROM clientes 
                WHERE cliente LIKE %s 
                ORDER BY cliente ASC 
                LIMIT 50
            """
            params = (f"%{texto_busqueda}%",)
            
            # Usamos el método nativo de tu clase Database
            filas = self.db.execute_query(query, params)

            if not filas:
                messagebox.showinfo("Búsqueda", "No se encontraron clientes con ese nombre.")
                self.combo_resultados.configure(values=["Sin resultados"])
                self.combo_resultados.set("Sin resultados")
                self.mapa_busqueda = {}
                return

            self.mapa_busqueda = {f"{row[1]} (ID: {row[0]})": row[0] for row in filas}
            opciones = list(self.mapa_busqueda.keys())

            self.combo_resultados.configure(values=opciones)
            self.combo_resultados.set(opciones[0])
            self._on_cliente_selected(opciones[0])

        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar clientes:\n{e}")

    def cargar_ctacte_cliente(self):
        """Carga los registros de la Cta. Cte. del cliente filtrando opcionalmente los liquidados"""
        if not self.cliente_seleccionado_id or not self.db:
            return

        # Limpiar grilla antes de cargar
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            ocultar_liquidados = self.var_ocultar_liquidados.get()

            # Si ocultar_liquidados es True, traemos solo liquidado = 0
            query = """
                SELECT 
                    c.id_cta,
                    c.fecha,
                    c.comprobante,
                    COALESCE(p.producto, '') AS producto,
                    c.detalle,
                    c.cantidad,
                    c.unidad,
                    c.pu,
                    c.debe,
                    c.haber,
                    c.liquidado
                FROM ctacteclientes c
                LEFT JOIN productos p ON c.idproducto = p.id
                WHERE c.idcliente = %s
                  AND (%s = FALSE OR c.liquidado = 0)
                ORDER BY c.fecha ASC, c.id_cta ASC
            """
            params = (self.cliente_seleccionado_id, ocultar_liquidados)
            
            registros = self.db.execute_query(query, params) or []

            total_debe = 0.0
            total_haber = 0.0
            saldo_acumulado = 0.0

            for reg in registros:
                (id_cta, fecha, comp, prod, det, cant, unidad, pu, debe, haber, liquidado) = reg

                debe_val = float(debe or 0.0)
                haber_val = float(haber or 0.0)

                total_debe += debe_val
                total_haber += haber_val
                saldo_acumulado += (debe_val - haber_val)

                # Formateo seguro de fecha
                fecha_str = fecha.strftime("%d/%m/%Y") if fecha and hasattr(fecha, 'strftime') else (str(fecha) if fecha else "")

                self.tree.insert("", "end", values=(
                    id_cta,
                    fecha_str,
                    comp or "",
                    prod or "",
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
        """Captura el cliente elegido del selector desplegable de resultados"""
        if hasattr(self, 'mapa_busqueda') and choice in self.mapa_busqueda:
            self.cliente_seleccionado_id = self.mapa_busqueda[choice]
            # Extraer solo el nombre de la razón social limpia para el label
            nombre_cliente = choice.split(" (ID:")[0]
            self.lbl_cliente_activo.configure(text=f"Cliente: {nombre_cliente}")
            
            # Cargar automáticamente los datos en la grilla
            self.cargar_ctacte_cliente()