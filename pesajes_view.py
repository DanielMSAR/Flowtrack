# pesajes_view.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from ticket_generator import generar_ticket_pdf, abrir_e_imprimir_pdf
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

        # --- ORIGEN COMBOBOX CON FORMATO LOTE Y CHACRA ---
        ctk.CTkLabel(frame_izq, text="Origen (Lote / Chacra) *", text_color="black", font=("Arial", 12, "bold")).pack(padx=15, anchor="w")
        self.cb_origen = ctk.CTkComboBox(frame_izq, values=self._obtener_lista_lotes_agrarios(), width=280)
        self.cb_origen.pack(padx=15, pady=(2, 10))

        # Panel Derecho: Datos de Carga y Kilos Iniciales
        frame_der = ctk.CTkFrame(self.tab_primera, fg_color="#f8f9fa", corner_radius=8)
        frame_der.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_der, text="Datos de Carga y Pesaje", font=("Arial", 14, "bold"), text_color="black").pack(pady=10, padx=15, anchor="w")

        # 1. Agrupación limpia de los campos de texto con el NUEVO COMBOBOX
        ctk.CTkLabel(frame_der, text="Producto *", text_color="black", font=("Arial", 12, "bold")).pack(padx=15, anchor="w")
        self.cb_producto = ctk.CTkComboBox(frame_der, values=self._obtener_lista_productos_activos(), width=280)
        self.cb_producto.pack(padx=15, pady=(2, 10))

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
        
        self.ent_peso_entrada = ctk.CTkEntry(frame_balanza_1, width=160, font=("Arial", 16, "bold"), text_color="#ceffea")
        self.ent_peso_entrada.pack(side="left", padx=(0, 10))
        
        self.btn_leer_balanza_1 = ctk.CTkButton(frame_balanza_1, text="Capturar Balanza", fg_color="#3a7ebf", hover_color="#2b5e8f", font=("Arial", 11, "bold"), command=lambda: self._leer_puerto_balanza(1))
        self.btn_leer_balanza_1.pack(side="left", fill="x", expand=True)

        # 3. El acceso de configuración queda abajo, integrado con el flujo técnico
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
        
        self.ent_peso_salida = ctk.CTkEntry(frame_balanza_2, width=160, font=("Arial", 16, "bold"), text_color="#f88284")
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
        # --- NUEVO BOTÓN DE REIMPRIMIR (AGREGAR ESTA LÍNEA AQUÍ) ---
        self.btn_reimprimir = ctk.CTkButton(
            frame_top, 
            text="Reimprimir Ticket", 
            fg_color="#2b6cb0", 
            hover_color="#1a365d", 
            command=self._reimprimir_ticket_cerrado
        )
        self.btn_reimprimir.pack(side="right", padx=5)

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
        if pestaña_activa == "Primer Pesada":
            # Recarga el combobox de productos por si se agregaron nuevos en el ABM
            self.cb_producto.configure(values=self._obtener_lista_productos_activos())
        elif pestaña_activa == "Segunda Pesada":
            self._cargar_pendientes_db()
        elif pestaña_activa == "Pesajes Realizados":
            self._cargar_historial_db()

    def _guardar_primer_pesada(self):
        patente = self.cb_chasis.get()
        chofer = self.ent_chofer.get().strip()
        bruto_str = self.ent_peso_entrada.get().strip()
        remito = self.ent_comprobante.get().strip()
        transp = self.ent_transporte.get().strip()

        # --- EXTRACCIÓN DEL PRODUCTO SELECCIONADO DESDE EL COMBO ---
        prod_seleccionado = self.cb_producto.get()
        texto_producto = ""
        if prod_seleccionado and " - " in prod_seleccionado:
            texto_producto = prod_seleccionado.split(" - ")[1]
        else:
            texto_producto = prod_seleccionado

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
            
        if not texto_producto or texto_producto == "Sin Productos Activos":
            messagebox.showwarning("Atención", "Debe seleccionar un producto válido.")
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
        
        params = (ahora, patente, chofer if chofer else None, peso_ent, remito if remito else None, texto_producto, transp if transp else None, texto_origen, id_origen, id_prov, self.current_user_id, ahora)
        
        try:
            self.db.execute_non_query(query, params)
            messagebox.showinfo("Éxito", f"Primer pesada registrada para el camión {patente} con el producto {texto_producto}.")
            self._limpiar_pestaña_uno()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la primer pesada:\n{e}")

    def _guardar_segunda_pesada(self):
        seleccion = self.tree_pendientes.selection()
        if not seleccion:
            return
        
        # Obtenemos los valores de la grilla de pendientes
        valores_grilla = self.tree_pendientes.item(seleccion[0])["values"]
        id_registro = valores_grilla[0]
        fecha_entrada = valores_grilla[1]
        patente = valores_grilla[2]
        chofer = valores_grilla[3]
        peso_entrada_original = int(valores_grilla[4])
        
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
            
            # --- OBTENER INFORMACIÓN DE REMITO Y PRODUCTO DE ESTE TICKET ---
            # Hacemos un SELECT rápido para traer los datos faltantes (Producto, Remito/Comprobante, Transporte, Origen)
            # que guardamos en la primera pesada para que salgan completos en el PDF impreso.
            datos_db = self.db.execute_query(
                "SELECT comprobante, Producto, Transporte, origen FROM pesajes WHERE idregistro = %s", 
                (id_registro,)
            )
            
            remito, producto, transporte, origen = "S/N", "General", "Propio", "General"
            if datos_db:
                remito = datos_db[0][0] if datos_db[0][0] else "S/N"
                producto = datos_db[0][1] if datos_db[0][1] else "General"
                transporte = datos_db[0][2] if datos_db[0][2] else "Propio"
                origen = datos_db[0][3] if datos_db[0][3] else "General"

            # --- PREPARAR MAPEO DE DATOS PARA EL PDF ---
            datos_impresion = {
                "id": id_registro,
                "fecha": ahora,
                "patente": patente,
                "chofer": chofer if chofer else "Asociado",
                "transporte": transporte,
                "producto": producto,
                "origen": origen,
                "destino": destino if destino else "Establecimiento",
                "remito": remito,
                "entrada": peso_entrada_original,
                "salida": peso_sal,
                "neto": neto
            }

            # Generar el PDF con formato A4 con dos copias exactas y abrirlo para imprimir
            nombre_archivo = f"ticket_balanza_{id_registro}.pdf"
            generar_ticket_pdf(datos_impresion, nombre_archivo)
            abrir_e_imprimir_pdf(nombre_archivo)

            # --- LIMPIEZA DE LA INTERFAZ ORIGINAL ---
            messagebox.showinfo("Éxito", f"Ticket No. {id_registro} completado. Guardado e impreso. Peso Neto: {neto} KG.")
            self._cargar_pendientes_db()
            self.ent_peso_salida.delete(0, "end")
            self.btn_registrar_salida.configure(state="disabled")
            self.lbl_info_camion.configure(text="Seleccione un camión de la grilla izquierda para operar.", text_color="gray")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al liquidar ticket o generar PDF:\n{e}")

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
        """Intenta conectarse a la balanza física por puerto serie y capturar el peso real.
        Si falla o no puede establecer conexión, muestra una alerta y no altera los campos."""
        puerto, velocidad = self._obtener_parametros_balanza()
        print(f"Intentando conectar al puerto: {puerto} a {velocidad} bps...")
        
        # 1. Comprobación defensiva de la librería pyserial
        try:
            import serial
        except ImportError:
            messagebox.showerror(
                "Librería Faltante", 
                "No se encontró el paquete 'pyserial' en este entorno.\n\n"
                "Para solucionarlo, ejecutá en tu consola:\n"
                "pip install pyserial",
                parent=self
            )
            return

        ser = None
        try:
            # 2. Intentamos abrir el puerto serie con un timeout de 2 segundos
            # para evitar que la interfaz gráfica (Tkinter) se congele si la balanza no responde.
            ser = serial.Serial(port=puerto, baudrate=velocidad, timeout=2)
            
            # Limpiamos los buffers de entrada viejos para asegurar una lectura instantánea y real
            ser.reset_input_buffer()
            
            # 3. Leemos una línea completa enviada por la balanza (espera hasta el salto de línea \n)
            datos_bytes = ser.readline()
            
            if not datos_bytes:
                raise Exception(
                    "Timeout de lectura.\nNo se recibieron datos en el tiempo esperado. "
                    "Verifique que la balanza esté encendida, transmitiendo datos y que el cable esté bien conectado."
                )
            
            # Decodificamos los bytes recibidos evitando caracteres corruptos
            lectura = datos_bytes.decode('utf-8', errors='ignore').strip()
            print(f"Datos crudos de balanza: '{lectura}'")
            
            # 4. Filtramos la lectura con una expresión regular para extraer solo la parte numérica.
            # Esto es vital porque las balanzas suelen enviar tramas tipo '+ 12450 kg' o 'ST,GS,  12450'
            import re
            numeros = re.findall(r'\d+', lectura)
            
            if not numeros:
                raise Exception(
                    f"Se abrió el puerto pero no se pudo interpretar un valor numérico válido en la trama.\n"
                    f"Recibido crudo: '{lectura}'"
                )
            
            # Tomamos la cadena numérica más larga encontrada (que corresponderá al peso)
            peso_detectado = int(max(numeros, key=len))
            
            # 5. Insertamos el peso real en el cuadro de texto correspondiente
            if nro_captura == 1:
                self.ent_peso_entrada.delete(0, "end")
                self.ent_peso_entrada.insert(0, str(peso_detectado))
            else:
                self.ent_peso_salida.delete(0, "end")
                self.ent_peso_salida.insert(0, str(peso_detectado))
                
        except serial.SerialException as se:
            # Error específico del puerto serie (puerto inexistente, ocupado por otro programa como putty, etc.)
            messagebox.showerror(
                "Error de Conexión", 
                f"No se pudo acceder al puerto {puerto}.\n\n"
                f"Posibles causas:\n"
                f"1. El puerto está siendo usado por otra aplicación.\n"
                f"2. El adaptador USB-Serie se desconectó.\n"
                f"3. El puerto '{puerto}' configurado no existe en este equipo.\n\n"
                f"Detalle técnico: {se}",
                parent=self
            )
        except Exception as e:
            # Cualquier otro tipo de error (timeout, decodificación, etc.)
            messagebox.showerror(
                "Error de Lectura", 
                f"Ocurrió un problema al intentar pesar:\n\n{str(e)}",
                parent=self
            )
        finally:
            # 6. Nos aseguramos de cerrar SIEMPRE el puerto serie si quedó abierto,
            # previniendo que el puerto quede bloqueado para futuras capturas.
            if ser and ser.is_open:
                ser.close()
                print("Puerto serie cerrado correctamente.")

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
    def _obtener_lista_productos_activos(self):
        """Trae de manera dinámica la lista de productos con estado activo desde MariaDB"""
        try:
            res = self.db.execute_query("SELECT id, Producto FROM productos WHERE activo = 1 ORDER BY Producto ASC")
            return [f"{f[0]} - {f[1]}" for f in res] if res else ["Sin Productos Activos"]
        except Exception as e:
            print(f"Error al cargar productos activos: {e}")
            return ["1 - Producto General"]

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
        self.ent_transporte.delete(0, "end")
        # Restablecemos el combobox de producto a la primera opción
        opciones = self._obtener_lista_productos_activos()
        self.cb_producto.configure(values=opciones)
        if opciones:
            self.cb_producto.set(opciones[0])
            
            
    def _reimprimir_ticket_cerrado(self):
        # 1. Obtener la fila seleccionada de la grilla de historial
        seleccion = self.tree_historial.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, seleccione un pesaje del historial para reimprimir.")
            return

        # Obtenemos los valores de la fila
        valores = self.tree_historial.item(seleccion[0], "values")
        
        try:
            id_registro = valores[0]
            estado = valores[8]
        except IndexError:
            messagebox.showerror("Error", "No se pudieron recuperar los datos del ticket seleccionado.")
            return

        if estado == "ANULADO":
            messagebox.showwarning("Atención", "No se puede reimprimir un ticket que ha sido anulado.")
            return

        # 2. Consultar TODOS los datos necesarios de la base de datos usando 'idregistro'
        try:
            query = """
                SELECT fecha, chasis, chofer, pesoentrada, pesosalida, pesofinal, comprobante, Producto, Transporte, origen, Destino 
                FROM pesajes 
                WHERE idregistro = %s
            """
            datos_db = self.db.execute_query(query, (id_registro,))
            
            if not datos_db:
                messagebox.showerror("Error", f"No se encontraron registros en la base de datos para el Ticket #{id_registro}.")
                return
            
            # Desempaquetamos de forma segura el registro obtenido
            registro = datos_db[0]
            fecha_mov = registro[0]
            patente = registro[1]
            chofer = registro[2] if registro[2] else "Asociado"
            entrada = registro[3]
            salida = registro[4]
            neto = registro[5]
            remito = registro[6] if registro[6] else "S/N"
            producto = registro[7] if registro[7] else "General"
            transporte = registro[8] if registro[8] else "Propio"
            origen = registro[9] if registro[9] else "General"
            destino = registro[10] if registro[10] else "Establecimiento"

        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar la base de datos para reimpresión:\n{e}")
            return

        # 3. Mapear datos al diccionario de impresión
        datos_impresion = {
            "id": id_registro,
            "fecha": fecha_mov,
            "patente": patente,
            "chofer": chofer,
            "transporte": transporte,
            "producto": producto,
            "origen": origen,
            "destino": destino,
            "remito": remito,
            "entrada": entrada,
            "salida": salida,
            "neto": neto
        }

        # 4. Generar el PDF y mandarlo a abrir para impresión
        try:
            nombre_archivo = f"ticket_balanza_reimpresion_{id_registro}.pdf"
            generar_ticket_pdf(datos_impresion, nombre_archivo)
            abrir_e_imprimir_pdf(nombre_archivo)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar o abrir el PDF para reimpresión:\n{str(e)}")