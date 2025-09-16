# gui.py (Corregido)
import tkinter as tk
from tkinter import ttk  # Importar ttk para el Treeview
from tkinter import messagebox, scrolledtext
from communication import FiscalPrinter
import commands
import serial.tools.list_ports
import threading
import web_server  # Importamos nuestro nuevo módulo de servidor


# gui.py -> Modificar la clase FiscalApp


class FiscalApp(tk.Tk):
    # ... (el método __init__ se mantiene igual) ...
    def __init__(self):
        super().__init__()
        self.title("Panel de Control Fiscal HKA80")
        self.geometry("700x500")

        self.printer = None
        self.port_variable = tk.StringVar(self)

        self.create_widgets()

    def create_widgets(self):
        # ... (el código del connection_frame y el área de texto se mantienen igual) ...
        connection_frame = tk.Frame(self, pady=5)
        connection_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(connection_frame, text="Puerto Serial:").pack(side="left", padx=(0, 5))
        self.ports_menu = tk.OptionMenu(
            connection_frame, self.port_variable, "No hay puertos disponibles"
        )
        self.ports_menu.pack(side="left", padx=5)
        self.refresh_button = tk.Button(
            connection_frame, text="Refrescar Puertos", command=self.update_ports_list
        )
        self.refresh_button.pack(side="left", padx=5)
        self.connect_button = tk.Button(
            connection_frame, text="Conectar", command=self.connect_printer
        )
        self.connect_button.pack(side="left", padx=5)
        self.disconnect_button = tk.Button(
            connection_frame,
            text="Desconectar",
            command=self.disconnect_printer,
            state="disabled",
        )
        self.disconnect_button.pack(side="left", padx=5)
        separator = tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill="x", padx=5, pady=5)
        self.output_area = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, state="disabled"
        )
        self.output_area.pack(expand=True, fill="both", padx=10, pady=10)

        # Barra de menú
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        # Menús existentes (Estado, Reportes, Documentos)
        self.status_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(
            label="Estado", menu=self.status_menu, state="disabled"
        )
        self.status_menu.add_command(
            label="Leer Status General (STS1/STS2)", command=self.read_status
        )
        self.status_menu.add_separator()
        self.status_menu.add_command(
            label="Obtener Status S5 (Memoria)", command=self.get_s5
        )

        self.reports_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(
            label="Reportes", menu=self.reports_menu, state="disabled"
        )
        self.reports_menu.add_command(
            label="Imprimir Reporte X", command=self.print_report_x
        )
        self.reports_menu.add_command(
            label="Obtener Datos Reporte X (Pantalla)", command=self.get_x_report_data
        )

        self.reports_menu.add_separator()  # Separador para agrupar comandos
        self.reports_menu.add_command(
            label="Imprimir Reporte Z (Cierre Diario)",
            command=self.print_z_report_confirmation,
        )

        self.reports_menu.add_command(
            label="Reimprimir Reporte Z por Número...",
            command=self.reprint_z_by_number_dialog,
        )
        # --- FIN DE CAMBIOS ---

        self.docs_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(
            label="Documentos Fiscales", menu=self.docs_menu, state="disabled"
        )
        self.docs_menu.add_command(
            label="Crear Nueva Factura...", command=self.create_invoice_dialog
        )
        self.docs_menu.add_command(
            label="Crear Nota de Crédito...", command=self.create_credit_note_dialog
        )

        self.docs_menu.add_separator()
        self.docs_menu.add_command(
            label="Enviar Factura de Ejemplo", command=self.send_example_invoice
        )

        # --- INICIO DE CAMBIOS ---
        # 1. Creamos un nuevo Menú de Mantenimiento
        self.maintenance_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(
            label="Mantenimiento", menu=self.maintenance_menu, state="disabled"
        )
        self.maintenance_menu.add_command(
            label="Imprimir Programación", command=self.print_printer_programming
        )
        # --- FIN DE CAMBIOS ---

        self.update_ports_list()

    # ... (update_ports_list y log_message se mantienen igual) ...
    def update_ports_list(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        menu = self.ports_menu["menu"]
        menu.delete(0, "end")

        if ports:
            for port in ports:
                menu.add_command(
                    label=port, command=lambda value=port: self.port_variable.set(value)
                )
            self.port_variable.set(ports[0])
        else:
            self.port_variable.set("No hay puertos")

    def log_message(self, message):
        self.output_area.config(state="normal")
        self.output_area.insert(tk.END, message + "\n\n")
        self.output_area.config(state="disabled")
        self.output_area.see(tk.END)

    def connect_printer(self):
        # ... (código existente para conectar) ...
        selected_port = self.port_variable.get()
        if not selected_port or selected_port == "No hay puertos":
            messagebox.showerror("Error", "No se ha seleccionado un puerto válido.")
            return

        try:
            self.printer = FiscalPrinter(port=selected_port)
            self.printer.connect()
            self.log_message(f"Conectado a la impresora en {selected_port}.")

            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.refresh_button.config(state="disabled")
            self.ports_menu.config(state="disabled")

            self.menubar.entryconfig("Estado", state="normal")
            self.menubar.entryconfig("Reportes", state="normal")
            self.menubar.entryconfig("Documentos Fiscales", state="normal")

            # 2. Habilitamos el nuevo menú al conectar
            self.menubar.entryconfig("Mantenimiento", state="normal")
            # Iniciar el servidor web en un hilo separado
            server_thread = threading.Thread(
                target=web_server.start_server,
                args=(
                    self.printer,
                ),  # Pasamos la instancia de la impresora al servidor
                daemon=True,  # El hilo del servidor se cerrará automáticamente cuando cerremos la GUI
            )
            server_thread.start()
            self.log_message("Servidor web activado. Escuchando en el puerto 5000.")

        except ConnectionError as e:
            self.log_message(str(e))
            messagebox.showerror("Error de Conexión", str(e))

    def disconnect_printer(self):
        # ... (código existente para desconectar) ...
        if self.printer:
            self.printer.close()
            self.printer = None
            self.log_message("Desconectado de la impresora.")

            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")
            self.refresh_button.config(state="normal")
            self.ports_menu.config(state="normal")

            self.menubar.entryconfig("Estado", state="disabled")
            self.menubar.entryconfig("Reportes", state="disabled")
            self.menubar.entryconfig("Documentos Fiscales", state="disabled")

            # 3. Deshabilitamos el nuevo menú al desconectar
            self.menubar.entryconfig("Mantenimiento", state="disabled")

            web_server.stop_server()
            self.log_message("Servidor web desactivado.")

    # ... (read_status, get_s5, etc., se mantienen igual) ...
    def read_status(self):
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        result = commands.read_printer_status(self.printer)
        self.log_message(result)

    def get_s5(self):
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        result = commands.get_s5_status(self.printer)
        self.log_message(f"Respuesta S5: {result}")

    def print_report_x(self):
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        result = commands.send_report_x(self.printer)
        self.log_message(f"Comando Reporte X: {result}")

    def send_example_invoice(self):
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        result = commands.send_invoice_example(self.printer)
        self.log_message(f"Comando Factura: {result}")

    def on_closing(self):
        self.disconnect_printer()
        self.destroy()

    # --- INICIO DE CAMBIOS ---
    # 4. Creamos la función que llama nuestro comando desde el menú
    def print_printer_programming(self):
        """
        Función para el botón de menú que envía el comando 'D'.
        """
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        result = commands.print_programming(self.printer)
        self.log_message(result)

    def get_x_report_data(self):
        """
        Función para el botón de menú que obtiene los datos del Reporte X.
        """
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        self.log_message("Obteniendo datos del Reporte X, por favor espera...")
        self.update_idletasks()  # Forzamos la actualización de la GUI para mostrar el mensaje

        result = commands.get_report_x_data(self.printer)
        self.log_message(result)

    def print_z_report_confirmation(self):
        """
        Muestra una advertencia y, si el usuario confirma, envía el comando para imprimir el Reporte Z.
        """
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        # --- INICIO DE CAMBIOS ---
        # Diálogo de confirmación para una operación crítica.
        is_confirmed = messagebox.askyesno(
            "Confirmación de Cierre Diario",
            "ADVERTENCIA: Imprimir un Reporte Z es una operación de cierre diario y NO se puede revertir.\n\n"
            "Esto reiniciará los totales de venta del día.\n\n"
            "¿Está seguro de que desea continuar?",
        )

        if is_confirmed:
            self.log_message("Enviando comando de Cierre Diario (Reporte Z)...")
            self.update_idletasks()  # Actualiza la GUI para mostrar el mensaje de espera
            result = commands.print_z_report(self.printer)
            self.log_message(result)
        else:
            self.log_message(
                "Operación de Cierre Diario (Reporte Z) cancelada por el usuario."
            )

    # Añade este nuevo método completo a la clase FiscalApp
    def reprint_z_by_number_dialog(self):
        """
        Abre una ventana de diálogo para que el usuario ingrese el rango
        de números de Reporte Z que desea reimprimir.
        """
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        # Creamos una nueva ventana Toplevel que funcionará como un diálogo.
        dialog = tk.Toplevel(self)
        dialog.title("Reimprimir Reporte Z")
        dialog.geometry("320x150")
        dialog.resizable(False, False)

        frame = tk.Frame(dialog, padx=15, pady=15)
        frame.pack(expand=True, fill="both")

        # Creamos los campos de texto y etiquetas para el rango
        tk.Label(frame, text="Número de Reporte Inicial:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        start_entry = tk.Entry(frame, width=15)
        start_entry.grid(row=0, column=1, padx=5)
        start_entry.focus_set()  # Pone el cursor en el primer campo

        tk.Label(frame, text="Número de Reporte Final:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        end_entry = tk.Entry(frame, width=15)
        end_entry.grid(row=1, column=1, padx=5)

        def on_submit():
            """Función que se ejecuta al presionar Aceptar."""
            try:
                start = int(start_entry.get())
                end = int(end_entry.get())

                if start <= 0 or end <= 0 or start > end:
                    messagebox.showerror(
                        "Entrada Inválida",
                        "Los números deben ser positivos y el número inicial no puede ser mayor que el final.",
                        parent=dialog,
                    )
                    return

                self.log_message(
                    f"Enviando comando para reimprimir Reportes Z del {start} al {end}..."
                )
                self.update_idletasks()

                result = commands.reprint_z_by_number(self.printer, start, end)
                self.log_message(result)
                dialog.destroy()  # Cierra el diálogo después de enviar

            except ValueError:
                messagebox.showerror(
                    "Entrada Inválida",
                    "Por favor, introduce solo números en ambos campos.",
                    parent=dialog,
                )

        # Botón para enviar los datos
        submit_button = tk.Button(frame, text="Reimprimir", command=on_submit)
        submit_button.grid(row=2, column=0, columnspan=2, pady=15)

        dialog.transient(self)  # Mantiene el diálogo sobre la ventana principal
        dialog.grab_set()  # Hace que el diálogo sea modal (bloquea la ventana principal)
        self.wait_window(dialog)  # Espera a que el diálogo se cierre para continuar

    # Añade este nuevo método completo a la clase FiscalApp. Es grande, pero maneja toda la ventana de facturación.
    def create_invoice_dialog(self):
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        invoice_window = tk.Toplevel(self)
        invoice_window.title("Crear Nueva Factura")
        invoice_window.geometry("800x600")
        invoice_window.grab_set()

        # --- Variables y Datos ---
        invoice_items = []
        tax_options = [
            "Exento (E)",
            "Tasa General (G)",
            "Tasa Reducida (R)",
            "Tasa Adicional (A)",
        ]

        # --- Frames Principales ---
        customer_frame = ttk.LabelFrame(
            invoice_window, text="Datos del Cliente", padding=(10, 5)
        )
        customer_frame.pack(fill="x", padx=10, pady=5)

        item_frame = ttk.LabelFrame(invoice_window, text="Añadir Ítem", padding=(10, 5))
        item_frame.pack(fill="x", padx=10, pady=5)

        items_display_frame = ttk.LabelFrame(
            invoice_window, text="Ítems de la Factura", padding=(10, 5)
        )
        items_display_frame.pack(expand=True, fill="both", padx=10, pady=5)

        actions_frame = ttk.Frame(invoice_window, padding=(10, 5))
        actions_frame.pack(fill="x", padx=10, pady=5)

        # --- Widgets de Datos del Cliente ---
        ttk.Label(customer_frame, text="RIF / C.I.:").grid(row=0, column=0, sticky="w")
        rif_entry = ttk.Entry(customer_frame, width=20)
        rif_entry.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(customer_frame, text="Nombre / Razón Social:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        name_entry = ttk.Entry(customer_frame, width=40)
        name_entry.grid(row=0, column=3, padx=5, sticky="ew")
        customer_frame.columnconfigure(3, weight=1)

        # --- Widgets para Añadir Ítem ---
        ttk.Label(item_frame, text="Descripción:").grid(row=0, column=0, sticky="w")
        desc_entry = ttk.Entry(item_frame, width=40)
        desc_entry.grid(row=0, column=1, padx=5, sticky="ew")
        item_frame.columnconfigure(1, weight=1)

        ttk.Label(item_frame, text="Precio:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        price_entry = ttk.Entry(item_frame, width=10)
        price_entry.grid(row=0, column=3, padx=5)

        ttk.Label(item_frame, text="Cantidad:").grid(
            row=0, column=4, sticky="w", padx=(10, 0)
        )
        qty_entry = ttk.Entry(item_frame, width=10)
        qty_entry.grid(row=0, column=5, padx=5)

        ttk.Label(item_frame, text="Tasa IVA:").grid(
            row=0, column=6, sticky="w", padx=(10, 0)
        )
        tax_var = tk.StringVar(value=tax_options[1])
        tax_menu = ttk.OptionMenu(item_frame, tax_var, tax_options[1], *tax_options)
        tax_menu.grid(row=0, column=7, padx=5)

        add_item_button = ttk.Button(
            item_frame, text="Añadir Ítem", command=lambda: add_item()
        )
        add_item_button.grid(row=0, column=8, padx=10)

        # --- Display de Ítems (Treeview) ---
        cols = ("qty", "desc", "price", "tax", "total")
        items_tree = ttk.Treeview(items_display_frame, columns=cols, show="headings")
        items_tree.pack(expand=True, fill="both")

        items_tree.heading("qty", text="Cantidad")
        items_tree.heading("desc", text="Descripción")
        items_tree.heading("price", text="Precio Unit.")
        items_tree.heading("tax", text="Tasa")
        items_tree.heading("total", text="Total Ítem")
        items_tree.column("qty", width=80, anchor="center")
        items_tree.column("price", width=100, anchor="e")
        items_tree.column("tax", width=120, anchor="center")
        items_tree.column("total", width=100, anchor="e")

        # --- Lógica de la Ventana ---
        def add_item():
            try:
                desc = desc_entry.get()
                price = float(price_entry.get())
                qty = float(qty_entry.get())
                tax = tax_var.get()

                if not desc or price <= 0 or qty <= 0:
                    messagebox.showerror(
                        "Error",
                        "Todos los campos del ítem son obligatorios y los montos deben ser positivos.",
                        parent=invoice_window,
                    )
                    return

                total = price * qty
                item_data = {"desc": desc, "price": price, "qty": qty, "tax_rate": tax}
                invoice_items.append(item_data)

                # Añadir al Treeview
                items_tree.insert(
                    "",
                    "end",
                    values=(f"{qty:,.3f}", desc, f"{price:,.2f}", tax, f"{total:,.2f}"),
                )

                # Limpiar campos
                desc_entry.delete(0, "end")
                price_entry.delete(0, "end")
                qty_entry.delete(0, "end")
                desc_entry.focus_set()

            except (ValueError, TypeError):
                messagebox.showerror(
                    "Error",
                    "El precio y la cantidad deben ser números válidos.",
                    parent=invoice_window,
                )

        def submit_invoice():
            if not invoice_items:
                messagebox.showerror(
                    "Error", "La factura no tiene ítems.", parent=invoice_window
                )
                return

            customer = {"rif": rif_entry.get(), "name": name_entry.get()}

            # Confirmación final
            if not messagebox.askyesno(
                "Confirmar Factura",
                "¿Está seguro de que desea enviar esta factura a la impresora?",
                parent=invoice_window,
            ):
                return

            self.log_message("Enviando factura a la impresora...")
            self.update_idletasks()

            result = commands.send_full_invoice(self.printer, customer, invoice_items)
            self.log_message(result)

            # Si tuvo éxito, cierra la ventana
            if "correctamente" in result:
                invoice_window.destroy()

        # --- Botón de Acción Final ---
        submit_button = ttk.Button(
            actions_frame, text="Totalizar e Imprimir Factura", command=submit_invoice
        )
        submit_button.pack(side="right")

    def create_credit_note_dialog(self):
        if not self.printer:
            messagebox.showwarning(
                "Sin Conexión", "Por favor, conecta la impresora primero."
            )
            return

        credit_note_window = tk.Toplevel(self)
        credit_note_window.title("Crear Nueva Nota de Crédito")
        credit_note_window.geometry(
            "800x700"
        )  # Un poco más alta para los nuevos campos
        credit_note_window.grab_set()

        # --- Variables y Datos ---
        credit_note_items = []
        tax_options = [
            "Exento (E)",
            "Tasa General (G)",
            "Tasa Reducida (R)",
            "Tasa Adicional (A)",
        ]

        # --- Frames Principales ---
        affected_doc_frame = ttk.LabelFrame(
            credit_note_window,
            text="Datos del Documento Afectado (Obligatorio)",
            padding=(10, 5),
        )
        affected_doc_frame.pack(fill="x", padx=10, pady=5)

        customer_frame = ttk.LabelFrame(
            credit_note_window, text="Datos del Cliente (Obligatorio)", padding=(10, 5)
        )
        customer_frame.pack(fill="x", padx=10, pady=5)

        item_frame = ttk.LabelFrame(
            credit_note_window, text="Añadir Ítem a Devolver", padding=(10, 5)
        )
        item_frame.pack(fill="x", padx=10, pady=5)

        items_display_frame = ttk.LabelFrame(
            credit_note_window, text="Ítems de la Nota de Crédito", padding=(10, 5)
        )
        items_display_frame.pack(expand=True, fill="both", padx=10, pady=5)

        actions_frame = ttk.Frame(credit_note_window, padding=(10, 5))
        actions_frame.pack(fill="x", padx=10, pady=5)

        # --- Widgets de Documento Afectado ---
        ttk.Label(affected_doc_frame, text="Nº Factura Afectada:").grid(
            row=0, column=0, sticky="w"
        )
        affected_num_entry = ttk.Entry(affected_doc_frame, width=20)
        affected_num_entry.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(affected_doc_frame, text="Fecha Factura (DD/MM/AAAA):").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        affected_date_entry = ttk.Entry(affected_doc_frame, width=20)
        affected_date_entry.grid(row=0, column=3, padx=5, sticky="ew")

        ttk.Label(affected_doc_frame, text="Serial Fiscal Impresora:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        affected_serial_entry = ttk.Entry(affected_doc_frame, width=20)
        affected_serial_entry.grid(row=1, column=1, padx=5, sticky="ew", pady=5)

        # --- Widgets de Datos del Cliente ---
        ttk.Label(customer_frame, text="RIF / C.I.:").grid(row=0, column=0, sticky="w")
        rif_entry = ttk.Entry(customer_frame, width=20)
        rif_entry.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(customer_frame, text="Nombre / Razón Social:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        name_entry = ttk.Entry(customer_frame, width=40)
        name_entry.grid(row=0, column=3, padx=5, sticky="ew")
        customer_frame.columnconfigure(3, weight=1)

        # --- Widgets para Añadir Ítem (igual que en la factura) ---
        ttk.Label(item_frame, text="Descripción:").grid(row=0, column=0, sticky="w")
        desc_entry = ttk.Entry(item_frame, width=40)
        # ... (el resto de este frame es idéntico al de la factura)
        desc_entry.grid(row=0, column=1, padx=5, sticky="ew")
        item_frame.columnconfigure(1, weight=1)
        ttk.Label(item_frame, text="Precio:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        price_entry = ttk.Entry(item_frame, width=10)
        price_entry.grid(row=0, column=3, padx=5)
        ttk.Label(item_frame, text="Cantidad:").grid(
            row=0, column=4, sticky="w", padx=(10, 0)
        )
        qty_entry = ttk.Entry(item_frame, width=10)
        qty_entry.grid(row=0, column=5, padx=5)
        ttk.Label(item_frame, text="Tasa IVA:").grid(
            row=0, column=6, sticky="w", padx=(10, 0)
        )
        tax_var = tk.StringVar(value=tax_options[1])
        tax_menu = ttk.OptionMenu(item_frame, tax_var, tax_options[1], *tax_options)
        tax_menu.grid(row=0, column=7, padx=5)
        add_item_button = ttk.Button(
            item_frame, text="Añadir Ítem", command=lambda: add_item()
        )
        add_item_button.grid(row=0, column=8, padx=10)

        # --- Display de Ítems (Treeview) ---
        cols = ("qty", "desc", "price", "tax", "total")
        items_tree = ttk.Treeview(items_display_frame, columns=cols, show="headings")
        items_tree.pack(expand=True, fill="both")
        # ... (el resto de la configuración del Treeview es idéntica a la factura)
        items_tree.heading("qty", text="Cantidad")
        items_tree.heading("desc", text="Descripción")
        items_tree.heading("price", text="Precio Unit.")
        items_tree.heading("tax", text="Tasa")
        items_tree.heading("total", text="Total Ítem")
        items_tree.column("qty", width=80, anchor="center")
        items_tree.column("price", width=100, anchor="e")
        items_tree.column("tax", width=120, anchor="center")
        items_tree.column("total", width=100, anchor="e")

        # --- Lógica de la Ventana ---
        def add_item():
            # ... (esta función es idéntica a la de la factura)
            try:
                desc = desc_entry.get()
                price = float(price_entry.get())
                qty = float(qty_entry.get())
                tax = tax_var.get()
                if not desc or price <= 0 or qty <= 0:
                    messagebox.showerror(
                        "Error",
                        "Todos los campos del ítem son obligatorios...",
                        parent=credit_note_window,
                    )
                    return
                item_data = {"desc": desc, "price": price, "qty": qty, "tax_rate": tax}
                credit_note_items.append(item_data)
                items_tree.insert(
                    "",
                    "end",
                    values=(
                        f"{qty:,.3f}",
                        desc,
                        f"{price:,.2f}",
                        tax,
                        f"{(price*qty):,.2f}",
                    ),
                )
                desc_entry.delete(0, "end")
                price_entry.delete(0, "end")
                qty_entry.delete(0, "end")
                desc_entry.focus_set()
            except (ValueError, TypeError):
                messagebox.showerror(
                    "Error",
                    "Precio y cantidad deben ser números.",
                    parent=credit_note_window,
                )

        def submit_credit_note():
            # Recolectar datos obligatorios
            affected_doc_data = {
                "number": affected_num_entry.get(),
                "date": affected_date_entry.get(),
                "serial": affected_serial_entry.get(),
            }
            customer = {"rif": rif_entry.get(), "name": name_entry.get()}

            # Validar que los campos obligatorios no estén vacíos
            if not all(affected_doc_data.values()) or not all(customer.values()):
                messagebox.showerror(
                    "Error",
                    "Todos los campos de 'Documento Afectado' y 'Datos del Cliente' son obligatorios.",
                    parent=credit_note_window,
                )
                return

            if not credit_note_items:
                messagebox.showerror(
                    "Error",
                    "La nota de crédito no tiene ítems.",
                    parent=credit_note_window,
                )
                return

            if not messagebox.askyesno(
                "Confirmar Nota de Crédito",
                "¿Está seguro de que desea enviar esta Nota de Crédito a la impresora?",
                parent=credit_note_window,
            ):
                return

            self.log_message("Enviando Nota de Crédito a la impresora...")
            self.update_idletasks()

            result = commands.send_full_credit_note(
                self.printer, affected_doc_data, customer, credit_note_items
            )
            self.log_message(result)

            if "correctamente" in result:
                credit_note_window.destroy()

        # --- Botón de Acción Final ---
        submit_button = ttk.Button(
            actions_frame,
            text="Totalizar e Imprimir Nota de Crédito",
            command=submit_credit_note,
        )
        submit_button.pack(side="right")
