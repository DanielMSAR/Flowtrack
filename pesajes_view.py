# pesajes_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import configparser

class PesajesView(ctk.CTkFrame):
    def __init__(self, master, db_connection):
        super().__init__(master, fg_color="white", corner_radius=0)
        self.db = db_connection
        self.pack(fill="both", expand=True)

        # Captura de usuario desde la app principal de forma segura (Previene pantallas en blanco)
        self.current_user_id = None
        if hasattr(master, "root"):
            self.current_user_id = getattr(master.root, "current_user_id", None)
        elif hasattr(master, "current_user_id"):
            self.current_user_id = getattr(master, "current_user_id", None)
        else:
            try:
                self.current_user_id = getattr(master.winfo_toplevel(), "current_user_id", None)
            except:
                self.current_user_id = 1 # ID de respaldo por defecto

        # TÍTULO DEL MÓDULO
        self.titulo = ctk.CTkLabel(self, text="SISTEMA DE CONTROL DE BALANZA", font=("Arial", 20, "bold"), text_color="black")
        self.titulo.pack(pady=(15, 10), padx=20, anchor="w")

        # --- CREACIÓN DE LAS TRES PESTAÑAS CONTENEDORAS ---
        self.tabview = ctk.CTkTabview(
            self, 
            segmented_button_selected_color="#8cb04e", 
            segmented_button_selected_hover_color="#73943c"
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Forzar color de texto negro de forma compatible en las solapas
        try:
            self.tabview._segmented_button.configure(text_color="black")
        except:
            pass

        self.tab_primera = self.tabview.add("Primer Pesada")
        self.tab_segunda = self.tabview.add("Segunda Pesada")
        self.tab_historial = self.tabview.add("Pesajes Realizados")

        # Inicializadores de las estructuras internas
        self._armar_pestaña_primera()
        self._armar_pestaña_segunda()
        self._armar_pestaña_historial()

# =================================================================
    # PESTAÑA 1: PRIMER PESADA (ALTAS / ENTRADAS)
    # =================================================================
    def _armar_pestaña_primera(self):
        # Layout de 2 columnas para el formulario
        self.tab_primera.grid_columnconfigure(0, weight=1)
        self.tab_primera.grid_columnconfigure(1, weight=1)

        # Panel Izquierdo: Datos del Transporte
        frame_izq = ctk.CTkFrame(self.tab_primera, fg_color="#f8f9fa", corner_radius=8)
        frame_izq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_izq, text="Datos del Transporte & Origen", font=("Arial", 14, "bold"), text_color="black").pack(pady=10, padx=15, anchor="w")

        ctk.CTkLabel(frame_izq, text="Chasis / Patente *", text_color="black").pack(padx=15, anchor="w")
        self.cb_chasis = ctk.CTkComboBox(frame_izq, values=self._obtener_lista_vehiculos(), width=280)
        self.cb_chasis.pack(padx=15, pady=(2, 10))

        ctk.CTkLabel(frame_izq, text="Chofer", text_color="black").pack(padx=15, anchor="w")
        self.ent_chofer = ctk.CTkEntry(frame_izq, width=280)
        self.ent_chofer.pack(padx=15, pady=(2, 10))

        ctk.CTkLabel(frame_izq, text="Proveedor (ABM)", text_color="black").pack(padx=15, anchor="w")
        self.cb_proveedor = ctk.CTkComboBox(frame_izq, values=self._obtener_lista_proveedores(), width=280)
        self.cb_proveedor.pack(padx=15, pady=(2, 10))

        # --- MODIFICADO: ORIGEN COMBOBOX CON FORMATO LOTE Y CHACRA ---
        ctk.CTkLabel(frame_izq, text="Origen (Lote / Chacra) *", text_color="black", font=("Arial", 12, "bold")).pack(padx=15, anchor="w")
        self.cb_origen = ctk.CTkComboBox(frame_izq, values=self._obtener_lista_lotes_agrarios(), width=280)
        self.cb_origen.pack(padx=15, pady=(2, 10))

        # Panel Derecho: Datos de Carga y Kilos Iniciales
        frame_der = ctk.CTkFrame(self.tab_primera, fg_color="#f8f9fa", corner_radius=8)
        frame_der.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_der, text="Datos de Carga y Pesaje", font=("Arial", 14, "bold"), text_color="black").pack(pady=10, padx=15, anchor="w")

        # 1. Agrupación limpia de los campos de texto
        ctk.CTkLabel(frame_der, text="Producto", text_color="black").pack(padx=15, anchor="w")
        self.ent_producto = ctk.CTkEntry(frame_der, width=280)
        self.ent_producto.pack(padx=15, pady=(2, 10))

        ctk.CTkLabel(frame_der, text="Transporte / Empresa", text_color="black").pack(padx=15, anchor="w")
        self.ent_transporte = ctk.CTkEntry(frame_der, width=280)
        self.ent_transporte.pack(padx=15, pady=(2, 10))

        ctk.CTkLabel(frame_der, text="Comprobante / Remito No.", text_color="black").pack(padx=15, anchor="w")
        self.ent_comprobante = ctk.CTkEntry(frame_der, width=280)
        self.ent_comprobante.pack(padx=15, pady=(2, 10))

        # 2. Sección de Peso y captura inmediata
        ctk.CTkLabel(frame_der, text="Peso Entrada (KG) *", font=("Arial", 12, "bold"), text_color="black").pack(padx=15, anchor="w")
        frame_balanza_1 = ctk.CTkFrame(frame_der, fg_color="transparent")
        frame_balanza_1.pack(fill="x", padx=15, pady=(2, 10))
        
        self.ent_peso_entrada = ctk.CTkEntry(frame_balanza_1, width=160, font=("Arial", 16, "bold"), text_color="#1b4332")
        self.ent_peso_entrada.pack(side="left", padx=(0, 10))
        
        self.btn_leer_balanza_1 = ctk.CTkButton(frame_balanza_1, text="Capturar Balanza", fg_color="#3a7ebf", hover_color="#2b5e8f", font=("Arial", 11, "bold"), command=lambda: self._leer_puerto_balanza(1))
        self.btn_leer_balanza_1.pack(side="left", fill="x", expand=True)

        # 3. MOVIDO AQUÍ: El acceso de configuración queda abajo, integrado con el flujo técnico
        self.btn_config_balanza = ctk.CTkButton(
            frame_der, 
            text="⚙ Configurar Puerto Balanza", 
            fg_color="#4a5568", 
            hover_color="#2d3748", 
            font=("Arial", 11, "bold"), 
            command=self._abrir_ventana_config_balanza
        )
        self.btn_config_balanza.pack(padx=15, pady=(5, 10), fill="x")

        # 4. Acción de confirmación principal
        self.btn_registrar_entrada = ctk.CTkButton(frame_der, text="REGISTRAR ENTRADA CAMIÓN", fg_color="#8cb04e", hover_color="#73943c", text_color="black", font=("Arial", 13, "bold"), height=40, command=self._guardar_primer_pesada)
        self.btn_registrar_entrada.pack(fill="x", padx=15, pady=(5, 10))

    # =================================================================
    # PESTAÑA 2: SEGUNDA PESADA (EGRESOS / CAMIONES ADENTRO)
    # =================================================================
    def _armar_pestaña_segunda(self):
        self.tab_segunda.grid_columnconfigure(0, weight=1)
        self.tab_segunda.grid_columnconfigure(1, weight=1)
        
        # LADO IZQUIERDO: Tabla de camiones pendientes
        frame_lista = ctk.CTkFrame(self.tab_segunda, fg_color="white")
        frame_lista.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(frame_lista, text="Camiones en Establecimiento (Pendientes de Salida)", font=("Arial", 13, "bold"), text_color="black").pack(anchor="w", pady=5)
        
        self.tree_pendientes = ttk.Treeview(frame_lista, columns=("id", "fecha", "patente", "chofer", "entrada"), show="headings", height=12)
        self.tree_pendientes.heading("id", text="ID")
        self.tree_pendientes.heading("fecha", text="Fecha Ent.")
        self.tree_pendientes.heading("patente", text="Patente")
        self.tree_pendientes.heading("chofer", text="Chofer")
        self.tree_pendientes.heading("entrada", text="Peso Ent. (KG)")
        
        self.tree_pendientes.column("id", width=50, anchor="center")
        self.tree_pendientes.column("fecha", width=110, anchor="center")
        self.tree_pendientes.column("patente", width=90, anchor="center")
        self.tree_pendientes.column("chofer", width=140, anchor="w")
        self.tree_pendientes.column("entrada", width=100, anchor="e")
        self.tree_pendientes.pack(fill="both", expand=True)
        self.tree_pendientes.bind("<<TreeviewSelect>>", self._cargar_camion_para_salida)

        # LADO DERECHO: Formulario de Cierre de Ticket
        self.frame_cierre = ctk.CTkFrame(self.tab_segunda, fg_color="#f2f5f8", corner_radius=8)
        self.frame_cierre.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_cierre, text="Liquidar Segundo Pesaje", font=("Arial", 14, "bold"), text_color="#1d3557").pack(pady=10, padx=15, anchor="w")
        
        self.lbl_info_camion = ctk.CTkLabel(self.frame_cierre, text="Seleccione un camión de la grilla izquierda para operar.", font=("Arial", 12, "italic"), text_color="gray")
        self.lbl_info_camion.pack(padx=15, anchor="w", pady=5)

        ctk.CTkLabel(self.frame_cierre, text="Destino Final", text_color="black").pack(padx=15, anchor="w")
        self.ent_destino = ctk.CTkEntry(self.frame_cierre, width=280)
        self.ent_destino.pack(padx=15, pady=(2, 10))

        ctk.CTkLabel(self.frame_cierre, text="Observaciones", text_color="black").pack(padx=15, anchor="w")
        self.ent_obs = ctk.CTkEntry(self.frame_cierre, width=280)
        self.ent_obs.pack(padx=15, pady=(2, 10))

        # Campo peso salida
        ctk.CTkLabel(self.frame_cierre, text="Peso Salida (KG) *", font=("Arial", 12, "bold"), text_color="black").pack(padx=15, anchor="w")
        frame_balanza_2 = ctk.CTkFrame(self.frame_cierre, fg_color="transparent")
        frame_balanza_2.pack(fill="x", padx=15, pady=(2, 15))
        
        self.ent_peso_salida = ctk.CTkEntry(frame_balanza_2, width=160, font=("Arial", 16, "bold"), text_color="#bc4749")
        self.ent_peso_salida.pack(side="left", padx=(0, 10))
        
        self.btn_leer_balanza_2 = ctk.CTkButton(frame_balanza_2, text="Capturar Balanza", fg_color="#3a7ebf", hover_color="#2b5e8f", font=("Arial", 11, "bold"), command=lambda: self._leer_puerto_balanza(2))
        self.btn_leer_balanza_2.pack(side="left", fill="x", expand=True)

        self.btn_registrar_salida = ctk.CTkButton(self.frame_cierre, text="COMPLETAR TICKET Y SALIDA", fg_color="#1d3557", hover_color="#457b9d", text_color="white", font=("Arial", 13, "bold"), height=40, command=self._guardar_segunda_pesada, state="disabled")
        self.btn_registrar_salida.pack(fill="x", padx=15, pady=15)

        # Vincular cambio de pestaña para recargar datos
        self.tabview.configure(command=self._al_cambiar_pestaña)
        self._cargar_pendientes_db()

    # =================================================================
    # PESTAÑA 3: PESAJES REALIZADOS (HISTORIAL)
    # =================================================================
    def _armar_pestaña_historial(self):
        frame_top = ctk.CTkFrame(self.tab_historial, fg_color="transparent")
        frame_top.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame_top, text="Historial General de Pesajes", font=("Arial", 14, "bold"), text_color="black").pack(side="left")
        
        self.btn_anular = ctk.CTkButton(frame_top, text="Anular Ticket Seleccionado", fg_color="#bf3a3a", hover_color="#8f2b2b", command=self._anular_ticket)
        self.btn_anular.pack(side="right", padx=5)

        self.tree_historial = ttk.Treeview(self.tab_historial, columns=("id", "fecha", "patente", "remito", "entrada", "salida", "neto", "producto", "estado"), show="headings")
        self.tree_historial.heading("id", text="Ticket ID")
        self.tree_historial.heading("fecha", text="Fecha Mov.")
        self.tree_historial.heading("patente", text="Patente")
        self.tree_historial.heading("remito", text="Remito")
        self.tree_historial.heading("entrada", text="Bruto (KG)")
        self.tree_historial.heading("salida", text="Tara (KG)")
        self.tree_historial.heading("neto", text="Neto (KG)")
        self.tree_historial.heading("producto", text="Producto")
        self.tree_historial.heading("estado", text="Estado")

        for col in ("id", "fecha", "patente", "remito", "entrada", "salida", "neto", "estado"):
            self.tree_historial.column(col, width=95, anchor="center")
        self.tree_historial.column("producto", width=150, anchor="w")
        
        self.tree_historial.pack(fill="both", expand=True, pady=5)
        self._cargar_historial_db()

    # =================================================================
    # LÓGICA DE NEGOCIO Y CONSULTAS BASE DE DATOS
    # =================================================================
    def _al_cambiar_pestaña(self):
        pestaña_activa = self.tabview.get()
        if pestaña_activa == "Segunda Pesada":
            self._cargar_pendientes_db()
        elif pestaña_activa == "Pesajes Realizados":
            self._cargar_historial_db()

    def _guardar_primer_pesada(self):
        patente = self.cb_chasis.get()
        chofer = self.ent_chofer.get().strip()
        bruto_str = self.ent_peso_entrada.get().strip()
        remito = self.ent_comprobante.get().strip()
        prod = self.ent_producto.get().strip()
        transp = self.ent_transporte.get().strip()

        prov_seleccionado = self.cb_proveedor.get()
        id_prov = None
        if prov_seleccionado and " - " in prov_seleccionado:
            id_prov = prov_seleccionado.split(" - ")[0]

        origen_seleccionado = self.cb_origen.get()
        id_origen = None
        texto_origen = ""
        if origen_seleccionado and " - " in origen_seleccionado:
            id_origen = origen_seleccionado.split(" - ")[0]
            resto_cadena = origen_seleccionado.split(" - ")[1]
            if " [" in resto_cadena:
                texto_origen = resto_cadena.split(" [")[0]
            else:
                texto_origen = resto_cadena

        if not patente or not bruto_str:
            messagebox.showwarning("Atención", "Los campos Patente y Peso Entrada son obligatorios.")
            return

        if not id_origen:
            messagebox.showwarning("Atención", "Debe seleccionar obligatoriamente un Lote Agrario de Origen.")
            return

        try:
            peso_ent = int(bruto_str)
        except ValueError:
            messagebox.showwarning("Error", "El peso de entrada debe ser un número entero válido.")
            return

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """INSERT INTO pesajes 
        (fecha, chasis, chofer, pesoentrada, pesosalida, pesofinal, comprobante, Producto, Transporte, origen, idorigen, idproveedor, usualta, falta, anulado) 
        VALUES (%s, %s, %s, %s, 0, 0, %s, %s, %s, %s, %s, %s, %s, %s, 0)"""
        
        params = (ahora, patente, chofer if chofer else None, peso_ent, remito if remito else None, prod if prod else None, transp if transp else None, texto_origen, id_origen, id_prov, self.current_user_id, ahora)
        
        try:
            self.db.execute_non_query(query, params)
            messagebox.showinfo("Éxito", f"Primer pesada registrada para el camión {patente} con Origen Lote #{id_origen}.")
            self._limpiar_pestaña_uno()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la primer pesada:\n{e}")

    def _guardar_segunda_pesada(self):
        seleccion = self.tree_pendientes.selection()
        if not seleccion:
            return
        
        id_registro = self.tree_pendientes.item(seleccion[0])["values"][0]
        peso_entrada_original = int(self.tree_pendientes.item(seleccion[0])["values"][4])
        
        salida_str = self.ent_peso_salida.get().strip()
        destino = self.ent_destino.get().strip()
        observacion = self.ent_obs.get().strip()

        if not salida_str:
            messagebox.showwarning("Atención", "Debe ingresar el peso de salida para cerrar el pesaje.")
            return

        try:
            peso_sal = int(salida_str)
        except ValueError:
            messagebox.showwarning("Error", "El peso de salida debe ser un entero.")
            return

        neto = abs(peso_entrada_original - peso_sal)
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """UPDATE pesajes SET 
        pesosalida = %s, pesofinal = %s, Destino = %s, Observaciones = %s, usumodi = %s, fmodi = %s 
        WHERE idregistro = %s"""
        
        try:
            self.db.execute_non_query(query, (peso_sal, neto, destino if destino else None, observacion if observacion else None, self.current_user_id, ahora, id_registro))
            messagebox.showinfo("Éxito", f"Ticket No. {id_registro} completado. Peso Neto: {neto} KG.")
            self._cargar_pendientes_db()
            self.ent_peso_salida.delete(0, "end")
            self.btn_registrar_salida.configure(state="disabled")
            self.lbl_info_camion.configure(text="Seleccione un camión de la grilla izquierda para operar.", text_color="gray")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al liquidar ticket:\n{e}")

    def _cargar_camion_para_salida(self, event):
        seleccion = self.tree_pendientes.selection()
        if not seleccion:
            return
        valores = self.tree_pendientes.item(seleccion[0])["values"]
        self.lbl_info_camion.configure(text=f"Operando Ticket #{valores[0]} | Camión: {valores[2]} (Entró con {valores[4]} KG)", text_color="#1d3557")
        self.btn_registrar_salida.configure(state="normal")

    def _cargar_pendientes_db(self):
        for item in self.tree_pendientes.get_children():
            self.tree_pendientes.delete(item)
        query = "SELECT idregistro, fecha, chasis, chofer, pesoentrada FROM pesajes WHERE pesosalida = 0 AND anulado = 0 ORDER BY idregistro DESC"
        resultados = self.db.execute_query(query)
        if resultados:
            for fila in resultados:
                self.tree_pendientes.insert("", "end", values=fila)

    def _cargar_historial_db(self):
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)
        query = "SELECT idregistro, fecha, chasis, comprobante, pesoentrada, pesosalida, pesofinal, Producto, IF(anulado=1, 'ANULADO', 'OK') FROM pesajes ORDER BY idregistro DESC LIMIT 100"
        resultados = self.db.execute_query(query)
        if resultados:
            for fila in resultados:
                self.tree_historial.insert("", "end", values=fila)

    def _anular_ticket(self):
        seleccion = self.tree_historial.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un ticket del historial para proceder a su anulación.")
            return
        id_reg = self.tree_historial.item(seleccion[0])["values"][0]
        confirmar = messagebox.askyesno("Confirmación", f"¿Está seguro de que desea ANULAR el ticket #{id_reg}?")
        if confirmar:
            self.db.execute_non_query("UPDATE pesajes SET anulado = 1 WHERE idregistro = %s", (id_reg,))
            self._cargar_historial_db()

    def _leer_puerto_balanza(self, nro_captura):
        """Lector dinámico del archivo INI antes de capturar el peso"""
        puerto, velocidad = self._obtener_parametros_balanza()
        print(f"Puerto configurado activo: {puerto} a {velocidad} bps")
        
        # Simulador temporal (cuando conectes la balanza real aquí usarás pyserial)
        import random
        peso_simulado = random.randint(24000, 44000) if nro_captura == 1 else random.randint(8500, 16000)
        if nro_captura == 1:
            self.ent_peso_entrada.delete(0, "end")
            self.ent_peso_entrada.insert(0, str(peso_simulado))
        else:
            self.ent_peso_salida.delete(0, "end")
            self.ent_peso_salida.insert(0, str(peso_simulado))

    # =================================================================
    # GESTIÓN Y CONFIGURACIÓN DE BALANZA (ARCHIVO INI)
    # =================================================================
    def _abrir_ventana_config_balanza(self):
        """Abre una ventana flotante tolerante a fallas para configurar los parámetros de la báscula"""
        if hasattr(self, "ventana_config") and self.ventana_config.winfo_exists():
            self.ventana_config.focus()
            return

        self.ventana_config = ctk.CTkToplevel(self)
        self.ventana_config.title("Configuración de Báscula")
        self.ventana_config.geometry("360x260")
        self.ventana_config.resizable(False, False)
        self.ventana_config.transient(self)  
        self.ventana_config.grab_set()       

        config = configparser.ConfigParser()
        puerto_actual = "COM1"
        baudios_actual = "9600"
        
        if os.path.exists("config.ini"):
            config.read("config.ini")
            if "BALANZA" in config:
                puerto_actual = config["BALANZA"].get("puerto", "COM1")
                baudios_actual = config["BALANZA"].get("baudios", "9600")

        ctk.CTkLabel(self.ventana_config, text="Configuración del Puerto Serie", font=("Arial", 14, "bold")).pack(pady=10)
        ctk.CTkLabel(self.ventana_config, text="Puerto COM Activo:").pack(anchor="w", padx=30)
        
        frame_puerto = ctk.CTkFrame(self.ventana_config, fg_color="transparent")
        frame_puerto.pack(padx=30, pady=(2, 10), fill="x")
        
        # ComboBox editable para el puerto COM
        self.cb_puerto = ctk.CTkComboBox(frame_puerto, values=[puerto_actual, "COM1", "COM2", "COM3", "COM4"], width=180)
        self.cb_puerto.pack(side="left", padx=(0, 10))
        self.cb_puerto.set(puerto_actual)
        
        def escanear_puertos():
            try:
                # Intento de importación dinámica defensiva
                import serial.tools.list_ports
                puertos_encontrados = serial.tools.list_ports.comports()
                lista_coms = [p.device for p in puertos_encontrados]
                
                if lista_coms:
                    self.cb_puerto.configure(values=lista_coms)
                    self.cb_puerto.set(lista_coms[0])
                    messagebox.showinfo("Escaneo", f"Se encontraron {len(lista_coms)} puerto(s) activo(s).", parent=self.ventana_config)
                else:
                    messagebox.showwarning("Escaneo", "No se detectó ningún dispositivo serial físico conectado. Podés escribirlo de forma manual.", parent=self.ventana_config)
            except ImportError:
                # Si pyserial no está en este entorno, guiamos al usuario sin romper nada
                messagebox.showinfo(
                    "Aviso de Entorno", 
                    "La detección automática requiere 'pyserial'.\n\nNo te preocupes: podés escribir el puerto directamente a mano (Ej: COM3) en el recuadro y guardará igual.", 
                    parent=self.ventana_config
                )
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al escanear: {e}", parent=self.ventana_config)

        btn_refrescar = ctk.CTkButton(frame_puerto, text="🔄 Detectar", fg_color="#3a7ebf", hover_color="#2b5e8f", width=90, font=("Arial", 11, "bold"), command=escanear_puertos)
        btn_refrescar.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(self.ventana_config, text="Velocidad (Baudios):").pack(anchor="w", padx=30)
        cb_baudios = ctk.CTkComboBox(self.ventana_config, values=["1200", "2400", "4800", "9600", "19200", "38400", "115200"], width=300)
        cb_baudios.pack(padx=30, pady=(2, 15))
        cb_baudios.set(baudios_actual)

        def guardar_ini():
            puerto_nuevo = self.cb_puerto.get().strip()
            baudios_nuevos = cb_baudios.get()

            if not puerto_nuevo:
                messagebox.showwarning("Atención", "Debe seleccionar o escribir un puerto.", parent=self.ventana_config)
                return

            config_guardar = configparser.ConfigParser()
            if os.path.exists("config.ini"):
                config_guardar.read("config.ini")

            if "BALANZA" not in config_guardar:
                config_guardar["BALANZA"] = {}
            
            config_guardar["BALANZA"]["puerto"] = puerto_nuevo
            config_guardar["BALANZA"]["baudios"] = baudios_nuevos

            try:
                with open("config.ini", "w") as configfile:
                    config_guardar.write(configfile)
                messagebox.showinfo("Éxito", "Configuración de balanza guardada correctamente.", parent=self.ventana_config)
                self.ventana_config.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo escribir el archivo config.ini:\n{e}", parent=self.ventana_config)

        btn_guardar = ctk.CTkButton(self.ventana_config, text="GUARDAR AJUSTES", fg_color="#8cb04e", hover_color="#73943c", text_color="black", font=("Arial", 12, "bold"), command=guardar_ini)
        btn_guardar.pack(pady=10, padx=30, fill="x")

    def _obtener_parametros_balanza(self):
        """Retorna los parámetros del archivo INI de forma segura"""
        config = configparser.ConfigParser()
        puerto = "COM1"
        baudios = 9600
        if os.path.exists("config.ini"):
            config.read("config.ini")
            if "BALANZA" in config:
                puerto = config["BALANZA"].get("puerto", "COM1")
                baudios = int(config["BALANZA"].get("baudios", "9600"))
        return puerto, baudios

    # =================================================================
    # POBLADORES DE COMBOBOX COLECTORES DE TUS ABM
    # =================================================================
    def _obtener_lista_vehiculos(self):
        try:
            res = self.db.execute_query("SELECT patente FROM vehiculos ORDER BY patente ASC")
            return [f[0] for f in res] if res else ["Sin Patentes"]
        except:
            return ["ABC-123", "XYZ-999"]

    def _obtener_lista_proveedores(self):
        try:
            res = self.db.execute_query("SELECT id, proveedor FROM proveedores ORDER BY proveedor ASC")
            return [f"{f[0]} - {f[1]}" for f in res] if res else ["Sin Proveedores"]
        except:
            return ["1 - Proveedor de Prueba"]

    def _obtener_lista_lotes_agrarios(self):
        try:
            query = """
                SELECT loteagrario.id, loteagrario.loteagrario, chacras.chacra
                FROM loteagrario
                INNER JOIN chacras ON loteagrario.idchacra = chacras.idchacra
                ORDER BY loteagrario.loteagrario ASC
            """
            res = self.db.execute_query(query)
            if res:
                return [f"{f[0]} - {f[1]} [{f[2]}]" for f in res]
            else:
                return ["Sin Lotes Registrados"]
        except Exception as e:
            print(f"Error al cargar lotes agrarios con JOIN: {e}")
            return ["1 - Parcela General"]

    def _limpiar_pestaña_uno(self):
        self.ent_chofer.delete(0, "end")
        self.ent_peso_entrada.delete(0, "end")
        self.ent_comprobante.delete(0, "end")
        self.ent_producto.delete(0, "end")
        self.ent_transporte.delete(0, "end")