# movinsumos_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class MovInsumosView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Capturamos los datos del usuario activo desde app.py
        self.current_user_name = getattr(master.winfo_toplevel(), "current_user_name", "DANIEL").upper()
        
        # Mapeos internos para recuperar los IDs reales de los Comboboxes
        self.insumos_dict = {}
        self.vehiculos_dict = {}

        # --- CONTENEDOR DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color="#7a8754", segmented_button_selected_hover_color="#636e43", text_color="black")
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)

        # Creación de las tres pestañas solicitadas
        self.tab_stock = self.tabview.add("STOCK")
        self.tab_ingresos = self.tabview.add("INGRESOS")
        self.tab_salidas = self.tabview.add("SALIDAS")

        # Inicializar cada pestaña
        self._configurar_tab_stock()
        self._configurar_tab_ingresos()
        self._configurar_tab_salidas()

    # =====================================================================
    # PESTAÑA: STOCK
    # =====================================================================
    def _configurar_tab_stock(self):
        # Contenedor interno para que mantenga fondo blanco
        self.stock_container = ctk.CTkFrame(self.tab_stock, fg_color="white", corner_radius=0)
        self.stock_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Estilo para la grilla Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", font=("Arial", 11))
        style.configure("Treeview.Heading", background="#f1f3f5", foreground="black", font=("Arial", 11, "bold"), borderwidth=1)
        style.map("Treeview", background=[("selected", "#8cb04e")], foreground=[("selected", "black")])

        columnas = ("idarticulo", "insumo", "cantidad", "puntocritico")
        self.tree_stock = ttk.Treeview(self.stock_container, columns=columnas, show="headings")
        
        self.tree_stock.heading("idarticulo", text="ID ARTÍCULO")
        self.tree_stock.heading("insumo", text="INSUMO / DESCRIPCIÓN")
        self.tree_stock.heading("cantidad", text="STOCK ACTUAL")
        self.tree_stock.heading("puntocritico", text="PUNTO CRÍTICO")

        self.tree_stock.column("idarticulo", width=100, anchor="center")
        self.tree_stock.column("insumo", width=350, anchor="w")
        self.tree_stock.column("cantidad", width=150, anchor="center")
        self.tree_stock.column("puntocritico", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(self.stock_container, orient="vertical", command=self.tree_stock.yview)
        self.tree_stock.configure(yscrollcommand=scrollbar.set)

        self.tree_stock.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botón para refrescar el stock manualmente
        self.btn_refrescar = ctk.CTkButton(
            self.tab_stock, text="ACTUALIZAR PANEL DE STOCK", fg_color="#4d5433", hover_color="#3b4026",
            text_color="white", font=("Arial", 12, "bold"), height=35, command=self.cargar_grid_stock
        )
        self.btn_refrescar.pack(pady=(10, 0), anchor="e")

        self.cargar_grid_stock()

    def cargar_grid_stock(self):
        """Ejecuta la consulta INNER JOIN solicitada"""
        for fila in self.tree_stock.get_children():
            self.tree_stock.delete(fila)

        query = """
            SELECT 
                stockinsumos.idarticulo, 
                insumos.insumo, 
                stockinsumos.cantidad, 
                insumos.puntocritico 
            FROM stockinsumos 
            INNER JOIN insumos ON stockinsumos.idarticulo = insumos.id
            ORDER BY insumos.insumo ASC
        """
        registros = self.db.execute_query(query)
        if registros:
            for r in registros:
                qty_fmt = f"{r[2]:.2f}" if r[2] is not None else "0.00"
                pc_fmt = f"{r[3]:.2f}" if r[3] is not None else "0.00"
                self.tree_stock.insert("", "end", values=(r[0], r[1], qty_fmt, pc_fmt))

    # =====================================================================
    # PESTAÑA: INGRESOS
    # =====================================================================
    def _configurar_tab_ingresos(self):
        self.ingresos_container = ctk.CTkFrame(self.tab_ingresos, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e9ecef")
        self.ingresos_container.pack(fill="none", expand=True, padx=50, pady=20)

        # Formulario de carga centrado
        ctk.CTkLabel(self.ingresos_container, text="REGISTRO DE ENTRADA / INGRESO DE STOCK", font=("Arial", 16, "bold"), text_color="#4d5433").grid(row=0, column=0, columnspan=2, pady=20, padx=30, sticky="w")

        # Combo Insumos
        ctk.CTkLabel(self.ingresos_container, text="Seleccione Insumo:", font=("Arial", 12, "bold"), text_color="black").grid(row=1, column=0, padx=30, pady=(10, 2), sticky="w")
        self.cmb_insumos = ctk.CTkComboBox(self.ingresos_container, width=320, height=35, values=[], command=self._actualizar_lbl_stock_inicial)
        self.cmb_insumos.grid(row=2, column=0, padx=30, pady=(0, 15), sticky="w")

        # Indicador de Stock Inicial dinámico
        self.lbl_stock_previo = ctk.CTkLabel(self.ingresos_container, text="Stock Actual en Depósito: --", font=("Arial", 12, "italic"), text_color="blue")
        self.lbl_stock_previo.grid(row=2, column=1, padx=10, pady=(0, 15), sticky="w")

        # Combo Vehículos
        ctk.CTkLabel(self.ingresos_container, text="Vehículo Asociado:", font=("Arial", 12, "bold"), text_color="black").grid(row=3, column=0, padx=30, pady=(5, 2), sticky="w")
        self.cmb_vehiculos = ctk.CTkComboBox(self.ingresos_container, width=320, height=35, values=[])
        self.cmb_vehiculos.grid(row=4, column=0, padx=30, pady=(0, 15), sticky="w")

        # Cantidad a Ingresar
        ctk.CTkLabel(self.ingresos_container, text="Cantidad a Agregar:", font=("Arial", 12, "bold"), text_color="black").grid(row=5, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_cantidad = ctk.CTkEntry(self.ingresos_container, width=320, height=35, font=("Arial", 13))
        self.ent_cantidad.grid(row=6, column=0, padx=30, pady=(0, 15), sticky="w")

        # Número de Comprobante
        ctk.CTkLabel(self.ingresos_container, text="Número de Comprobante (Opcional):", font=("Arial", 12, "bold"), text_color="black").grid(row=7, column=0, padx=30, pady=(5, 2), sticky="w")
        self.ent_comp = ctk.CTkEntry(self.ingresos_container, width=320, height=35, font=("Arial", 13))
        self.ent_comp.grid(row=8, column=0, padx=30, pady=(0, 25), sticky="w")

        # Botón Guardar Entrada
        self.btn_guardar_ingreso = ctk.CTkButton(
            self.ingresos_container, text="PROCESAR INGRESO", fg_color="#4d5433", hover_color="#3b4026",
            text_color="white", font=("Arial", 13, "bold"), height=45, width=320, command=self.guardar_ingreso
        )
        self.btn_guardar_ingreso.grid(row=9, column=0, columnspan=2, padx=30, pady=(0, 30))

        self.cargar_combos_ingresos()

    def cargar_combos_ingresos(self):
        """Puebla los desplegables desde la base de datos de forma segura"""
        # Cargar Insumos
        res_insumos = self.db.execute_query("SELECT id, insumo FROM insumos ORDER BY insumo ASC")
        if res_insumos:
            self.insumos_dict = {r[1]: r[0] for r in res_insumos}
            self.cmb_insumos.configure(values=list(self.insumos_dict.keys()))

        # Cargar Vehículos (se adapta al nombre de tu tabla de vehículos)
        res_vehiculos = self.db.execute_query("SELECT idvehiculo, dominio FROM vehiculos ORDER BY dominio ASC")
        if res_vehiculos:
            self.vehiculos_dict = {r[1]: r[0] for r in res_vehiculos}
            self.cmb_vehiculos.configure(values=list(self.vehiculos_dict.keys()))

    def _obtener_stock_actual_db(self, id_insumo):
        """Busca el saldo actual en stockinsumos. Si no existe registro, devuelve 0.0"""
        res = self.db.execute_query("SELECT cantidad FROM stockinsumos WHERE idarticulo = %s", (id_insumo,))
        return float(res[0][0]) if res and res[0][0] is not None else 0.0

    def _actualizar_lbl_stock_inicial(self, valor_combo):
        id_insumo = self.insumos_dict.get(valor_combo)
        if id_insumo:
            stock_actual = self._obtener_stock_actual_db(id_insumo)
            self.lbl_stock_previo.configure(text=f"Stock Actual en Depósito: {stock_actual:.2f}")

    def guardar_ingreso(self):
        insumo_sel = self.cmb_insumos.get()
        vehiculo_sel = self.cmb_vehiculos.get()
        cantidad_raw = self.ent_cantidad.get().strip()
        comprobante = self.ent_comp.get().strip()

        if not insumo_sel:
            messagebox.showwarning("Atención", "Debe seleccionar un insumo.")
            return

        try:
            cantidad_agrega = float(cantidad_raw)
            if cantidad_agrega <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "La cantidad a agregar debe ser un valor numérico mayor a cero.")
            return

        id_insumo = self.insumos_dict.get(insumo_sel)
        id_vehiculo = self.vehiculos_dict.get(vehiculo_sel) if vehiculo_sel else None

        # 1. Obtener Stock Inicial antes del movimiento
        stock_inicial = self._obtener_stock_actual_db(id_insumo)
        stock_final = stock_inicial + cantidad_agrega

        try:
            # 2. Registrar en el historial regmovinsumos
            query_mov = """
                INSERT INTO regmovinsumos (detalle, fecha, stocki, agrega, descuenta, stockf, comp, idinsumo, empleado, idvehiculo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params_mov = (insumo_sel, datetime.now(), stock_inicial, cantidad_agrega, 0.0, stock_final, comprobante, id_insumo, self.current_user_name, id_vehiculo)
            self.db.execute_query(query_mov, params_mov)

            # 3. Actualizar o Insertar el saldo consolidado en stockinsumos
            query_check = "SELECT idarticulo FROM stockinsumos WHERE idarticulo = %s"
            if self.db.execute_query(query_check, (id_insumo,)):
                query_stock = "UPDATE stockinsumos SET cantidad = %s WHERE idarticulo = %s"
                params_stock = (stock_final, id_insumo)
            else:
                query_stock = "INSERT INTO stockinsumos (idarticulo, cantidad) VALUES (%s, %s)"
                params_stock = (id_insumo, stock_final)
            
            self.db.execute_query(query_stock, params_stock)

            # =====================================================================
            # SOLUCIÓN: Confirmar la transacción para que impacte en MariaDB
            # =====================================================================
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.commit()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.commit()
            # =====================================================================

            messagebox.showinfo("Éxito", f"Ingreso procesado correctamente.\nStock final: {stock_final:.2f}")
            
            # Limpiar entradas y actualizar grillas
            self.ent_cantidad.delete(0, "end")
            self.ent_comp.delete(0, "end")
            self.lbl_stock_previo.configure(text="Stock Actual en Depósito: --")
            self.cargar_grid_stock()
            
        except Exception as e:
            # Si algo falla en el proceso, deshacemos para no dejar datos inconsistentes
            if hasattr(self.db, "connection") and self.db.connection:
                self.db.connection.rollback()
            elif hasattr(self.db, "conn") and self.db.conn:
                self.db.conn.rollback()
                
            messagebox.showerror("Error", f"No se pudo completar la transacción en la base de datos:\n{e}")
    # =====================================================================
    # PESTAÑA: SALIDAS (RESERVA FUTURA)
    # =====================================================================
    def _configurar_tab_salidas(self):
        self.salidas_container = ctk.CTkFrame(self.tab_salidas, fg_color="white", corner_radius=0)
        self.salidas_container.pack(fill="both", expand=True)

        self.lbl_futuro = ctk.CTkLabel(
            self.salidas_container, 
            text="Estructura de Salidas Reservada.\n\nAquí diseñaremos próximamente el formulario de consumos y egresos.", 
            font=("Arial", 14, "italic"), 
            text_color="gray"
        )
        self.lbl_futuro.pack(expand=True)