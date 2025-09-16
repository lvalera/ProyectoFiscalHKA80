# commands.py
from communication import FiscalPrinter
from models import S5PrinterData
import time


# commands.py -> Añadir al inicio 'from models import ReportXData'
# y luego añadir esta función


def get_report_x_data(printer: FiscalPrinter):
    """
    Envía el comando 'U0X' para obtener los datos del reporte X y los devuelve
    en un formato legible.
    Referencia: Manual, Página 69.
    """
    try:
        raw_response = printer.send_command("U0X")

        # Una respuesta con datos viene en una trama STX...ETX
        if raw_response and raw_response.startswith(FiscalPrinter._STX):
            # Extraemos la data, que está entre STX y ETX
            data_str = raw_response[1:-2].decode("ascii", errors="ignore")

            # Usamos nuestro modelo para parsear los datos
            report_data = ReportXData.from_trama(data_str)

            # Formateamos el resultado para mostrarlo al usuario
            formatted_string = (
                f"--- Datos del Reporte X ---\n"
                f"  Número del Próximo Reporte Z: {report_data.numero_proximo_z}\n"
                f"  Última Factura: {report_data.numero_ultima_factura} ({report_data.fecha_ultima_factura} {report_data.hora_ultima_factura})\n"
                f"  Última Nota de Crédito: {report_data.numero_ultima_nc}\n"
                f"--- ACUMULADOS DE VENTAS ---\n"
                f"  Venta Exenta: {report_data.venta_exento:,.2f}\n"
                f"  Base Imponible General: {report_data.venta_base_tasa1:,.2f}\n"
                f"  IVA General: {report_data.venta_iva_tasa1:,.2f}\n"
                f"--- ACUMULADOS DE NOTAS DE CRÉDITO (DEVOLUCIONES) ---\n"
                f"  Devolución Exenta: {report_data.nc_exento:,.2f}\n"
                f"  Base Devolución General: {report_data.nc_base_tasa1:,.2f}\n"
                f"  IVA Devolución General: {report_data.nc_iva_tasa1:,.2f}\n"
                f"-----------------------------"
            )
            return formatted_string
        else:
            return (
                f"Respuesta no reconocida o error al obtener Reporte X: {raw_response}"
            )
    except (ConnectionError, ValueError, IndexError) as e:
        # Capturamos posibles errores de comunicación o de parseo de datos
        return f"Error al procesar Reporte X: {e}"


# commands.py -> Añadir este código nuevo

# Diccionarios para traducir los códigos de estado y error a texto.
# Referencia: Manual, Página 18, Tabla 7.
STS1_MAP = {
    b"\x40": "Modo Entrenamiento y en Espera",
    b"\x41": "Modo Entrenamiento y en medio de una Transacción Fiscal",
    b"\x42": "Modo Entrenamiento y en medio de una Transacción No fiscal",
    b"\x60": "Modo Fiscal y en Espera",
    b"\x61": "Modo Fiscal y en medio de una Transacción Fiscal",
    b"\x62": "Modo Fiscal y en medio de una Transacción No fiscal",
    b"\x68": "Modo Fiscal con la Memoria Fiscal llena y en Espera",
    b"\x69": "Modo Fiscal con la MF llena y en medio de una Transacción Fiscal",
    b"\x6a": "Modo Fiscal con la MF llena y en Transacción No fiscal",
}

# Referencia: Manual, Página 19, Tabla 8.
STS2_MAP = {
    b"\x40": "Ningún error",
    b"\x41": "Error: Sin papel",
    b"\x42": "Error mecánico de la impresora / Papel atascado",
    b"\x43": "Error mecánico de la impresora y fin de papel",
    b"\x48": "Error: Gaveta de dinero abierta",
    b"\x60": "Error fiscal",
    b"\x64": "Error en la memoria fiscal",
    b"\x6c": "Error: Memoria fiscal llena",
}


def read_printer_status(printer: FiscalPrinter):
    """
    Llama al método get_status de la impresora y devuelve una descripción
    legible del estado (STS1) y el error (STS2).
    """
    try:
        sts1_byte, sts2_byte = printer.get_status()

        if sts1_byte is None:
            return "Error: No se recibió una respuesta válida de la impresora al solicitar status."

        # .get() permite obtener un valor por defecto si la clave no se encuentra
        status_desc = STS1_MAP.get(sts1_byte, f"Status Desconocido ({sts1_byte.hex()})")
        error_desc = STS2_MAP.get(sts2_byte, f"Error Desconocido ({sts2_byte.hex()})")

        return (
            f"--- Status de la Impresora ---\n"
            f"STATUS (STS1): {status_desc}\n"
            f"ERROR (STS2):  {error_desc}"
        )

    except (ConnectionError, ValueError) as e:
        return f"Error de comunicación al leer status: {e}"


def get_s5_status(printer: FiscalPrinter):
    """
    Obtiene el status S5 y devuelve un objeto S5PrinterData.
    """
    try:
        raw_response = printer.send_command("S5")

        # Decodificar y limpiar la respuesta
        # La impresora devuelve STX + DATA + ETX + LRC. Solo necesitamos DATA.
        if raw_response.startswith(b"\x02") and raw_response.endswith(
            b"\x03" + b"LRC_BYTE_AQUI"[-1:]
        ):  # Placeholder
            # Extraer la data, que está entre STX y ETX
            data_str = raw_response[1:-2].decode("ascii", errors="ignore")
            return S5PrinterData.from_trama(data_str)
        else:
            return f"Respuesta no reconocida: {raw_response}"

    except (ConnectionError, ValueError) as e:
        return f"Error: {e}"


def send_report_x(printer: FiscalPrinter):
    """
    Envía el comando para imprimir un Reporte X.
    """
    try:
        # Comando para Reporte X es 'I0X' (Página 67, Tabla 59)
        raw_response = printer.send_command("I0X")
        if raw_response == FiscalPrinter._ACK:
            return (
                "Comando de Reporte X aceptado. La impresora debería estar imprimiendo."
            )
        else:
            return f"La impresora respondió con error: {raw_response}"
    except ConnectionError as e:
        return f"Error de comunicación: {e}"


def send_invoice_example(printer: FiscalPrinter):
    """
    Envía una secuencia de comandos para generar una factura de ejemplo.
    Referencia: Manual, Páginas 33 y 34.
    """
    try:
        # Secuencia de una factura simple
        # 1. Establecer datos del cliente (Opcional, pero buena práctica)
        printer.send_command("iR*J-123456789")  # RIF
        printer.send_command("iS*Cliente de Ejemplo C.A.")  # Razón Social

        # 2. Agregar un ítem (Tasa General '!')
        # Formato: !{precio}{cantidad}{descripción}
        # Precio: 10.00 (formato 0000001000)
        # Cantidad: 1.000 (formato 00010000)
        # Ver manual pág 32 para formatos de precio/cantidad
        printer.send_command("!000000100000010000Producto de Prueba 1")

        # 3. Agregar otro ítem (Exento ' ')
        printer.send_command(" 0000000500000020000Producto Exento")

        # 4. Totalizar y pagar (Pago directo con medio de pago 01)
        # El comando '101' es para pago directo.
        response = printer.send_command("101")

        if response == FiscalPrinter._ACK:
            return "Factura enviada y cerrada correctamente."
        else:
            return "Hubo un problema al cerrar la factura."

    except ConnectionError as e:
        return f"Error durante el envío de la factura: {e}"

    # commands.py -> Añadir esta nueva función


def print_programming(printer: FiscalPrinter):
    """
    Envía el comando 'D' para que la impresora imprima su configuración actual.
    Este comando no devuelve datos, solo una confirmación (ACK).
    Referencia: Manual, Página 28, Tabla 25.
    """
    try:
        # El comando para Imprimir Programación es 'D' [cite: 550]
        raw_response = printer.send_command("D")

        # La respuesta esperada para un comando simple es ACK (0x06) [cite: 247]
        if raw_response == FiscalPrinter._ACK:
            return "Comando 'Imprimir Programación' aceptado. La impresora debería estar imprimiendo el reporte de configuración."
        # Si la impresora devuelve NAK (Comando No Aceptado) [cite: 252]
        elif raw_response == FiscalPrinter._NAK:
            return "Error: La impresora no aceptó el comando 'Imprimir Programación' (NAK)."
        else:
            return f"Respuesta no reconocida de la impresora: {raw_response}"
    except ConnectionError as e:
        return f"Error de comunicación: {e}"


# commands.py -> Añadir esta nueva función


def print_z_report(printer: FiscalPrinter):
    """
    Envía el comando 'I0Z' para imprimir el Reporte Z (cierre diario).
    Esta es una operación crítica que reinicia los acumuladores diarios.
    Referencia: Manual, Página 67, Tabla 59.
    """
    try:
        # Comando para Reporte Z es 'I0Z'
        raw_response = printer.send_command("I0Z")

        if raw_response == FiscalPrinter._ACK:
            # Es crucial advertir al usuario sobre el tiempo que puede tomar la operación.
            return (
                "Comando 'Reporte Z' aceptado. La impresora iniciará el proceso de Cierre Diario. "
                "Este proceso puede tardar varios segundos. Por favor, espere a que la impresora "
                "termine completamente antes de enviar nuevos comandos."
            )[cite:1729]
        elif raw_response == FiscalPrinter._NAK:
            return "Error: La impresora no aceptó el comando 'Reporte Z' (NAK). Verifique el estado de la impresora."
        else:
            return f"Respuesta no reconocida de la impresora: {raw_response}"
    except ConnectionError as e:
        return f"Error de comunicación: {e}"


def reprint_z_by_number(printer: FiscalPrinter, start_num: int, end_num: int):
    """
    Envía el comando 'RZ' para reimprimir un rango de reportes Z por su número.
    Referencia: Manual, Página 49, Tabla 39.
    """
    try:
        # El manual especifica que los números deben tener 7 dígitos.
        # Usamos zfill() para rellenar con ceros a la izquierda si es necesario.
        start_str = str(start_num).zfill(7)
        end_str = str(end_num).zfill(7)

        command = f"RZ{start_str}{end_str}"

        raw_response = printer.send_command(command)

        if raw_response == FiscalPrinter._ACK:
            return f"Comando 'Reimprimir Reporte Z' (rango: {start_num}-{end_num}) aceptado. La impresora iniciará la reimpresión."
        elif raw_response == FiscalPrinter._NAK:
            return f"Error: La impresora no aceptó el comando 'Reimprimir Reporte Z' (NAK)."
        else:
            return f"Respuesta no reconocida de la impresora: {raw_response}"
    except (ConnectionError, ValueError) as e:
        return f"Error de comunicación o datos inválidos: {e}"


# --- Funciones de ayuda para formatear los datos ---
def _format_price(price: float) -> str:
    """Convierte un float a un string de 10 dígitos para el precio (8 enteros, 2 decimales)."""
    return str(int(price * 100)).zfill(10)


def _format_quantity(qty: float) -> str:
    """Convierte un float a un string de 8 dígitos para la cantidad (5 enteros, 3 decimales)."""
    return str(int(qty * 1000)).zfill(8)


# --- Diccionario para mapear tasas a comandos ---
TAX_RATE_COMMANDS = {
    "Exento (E)": " ",
    "Tasa General (G)": "!",
    "Tasa Reducida (R)": '"',  # El comando es el carácter de comillas dobles
    "Tasa Adicional (A)": "#",
}


def send_full_invoice(printer: FiscalPrinter, customer_data: dict, items: list):
    """
    Envía una secuencia de comandos completa para crear y cerrar una factura.
    Referencia: Manual, Páginas 32-34.
    """
    try:
        # --- 1. Enviar datos del cliente ---
        if customer_data.get("rif"):
            printer.send_command(f"iR*{customer_data['rif']}")
            time.sleep(0.1)  # Pequeña pausa entre comandos
        if customer_data.get("name"):
            printer.send_command(f"iS*{customer_data['name']}")
            time.sleep(0.1)

        # --- 2. Enviar los ítems de la factura ---
        for item in items:
            tax_command = TAX_RATE_COMMANDS.get(item["tax_rate"])
            if tax_command is None:
                return f"Error: Tasa de impuesto desconocida '{item['tax_rate']}'."

            price_str = _format_price(item["price"])
            qty_str = _format_quantity(item["qty"])

            # Construir comando del ítem: CMD + Precio + Cantidad + Descripción
            item_command = f"{tax_command}{price_str}{qty_str}{item['desc']}"

            response = printer.send_command(item_command)
            if response != FiscalPrinter._ACK:
                return f"Error al agregar el ítem '{item['desc']}'. La impresora no aceptó el comando."
            time.sleep(0.2)  # Pausa mayor para procesar el ítem

        # --- 3. Cerrar la factura (Pago directo con medio de pago 01) ---
        # El comando '101' es para pago directo total con el medio de pago 01.
        close_response = printer.send_command("101")
        if close_response == FiscalPrinter._ACK:
            return "Factura enviada y cerrada correctamente. La impresora debería estar imprimiendo."
        else:
            # Si el cierre falla, es importante intentar anular el documento
            printer.send_command("7")  # Comando para anular documento fiscal en curso
            return "Error al cerrar la factura. Se ha intentado anular el documento en la impresora."

    except (ConnectionError, ValueError) as e:
        return f"Error durante el envío de la factura: {e}"


# commands.py -> Añadir este nuevo código

# --- Diccionario para mapear tasas a comandos de Nota de Crédito ---
CREDIT_NOTE_TAX_COMMANDS = {
    "Exento (E)": "d0",
    "Tasa General (G)": "d1",
    "Tasa Reducida (R)": "d2",
    "Tasa Adicional (A)": "d3",
}


def send_full_credit_note(
    printer: FiscalPrinter, affected_doc: dict, customer_data: dict, items: list
):
    """
    Envía una secuencia de comandos completa para crear y cerrar una Nota de Crédito.
    Referencia: Manual, Páginas 35-37.
    """
    try:
        # --- 1. Enviar datos OBLIGATORIOS del documento afectado y del cliente ---
        # El manual indica que estos campos son obligatorios.
        printer.send_command(
            f"iF*{affected_doc['number']}"
        )  # Número de Factura Afectada
        time.sleep(0.1)
        printer.send_command(f"iD*{affected_doc['date']}")  # Fecha de Factura Afectada
        time.sleep(0.1)
        printer.send_command(
            f"il*{affected_doc['serial']}"
        )  # Serial de la Máquina Fiscal que emitió la factura
        time.sleep(0.1)
        printer.send_command(f"iR*{customer_data['rif']}")  # RIF del Cliente
        time.sleep(0.1)
        printer.send_command(f"iS*{customer_data['name']}")  # Nombre del Cliente
        time.sleep(0.1)

        # --- 2. Enviar los ítems de la Nota de Crédito ---
        for item in items:
            tax_command = CREDIT_NOTE_TAX_COMMANDS.get(item["tax_rate"])
            if tax_command is None:
                return f"Error: Tasa de impuesto desconocida '{item['tax_rate']}'."

            price_str = _format_price(item["price"])
            qty_str = _format_quantity(item["qty"])

            item_command = f"{tax_command}{price_str}{qty_str}{item['desc']}"

            response = printer.send_command(item_command)
            if response != FiscalPrinter._ACK:
                return f"Error al agregar el ítem '{item['desc']}'. La impresora no aceptó el comando."
            time.sleep(0.2)

        # --- 3. Cerrar la Nota de Crédito (Pago directo con medio de pago 01) ---
        close_response = printer.send_command("101")
        if close_response == FiscalPrinter._ACK:
            return "Nota de Crédito enviada y cerrada correctamente. La impresora debería estar imprimiendo."
        else:
            printer.send_command(
                "7"
            )  # Intentar anular el documento en curso si falla el cierre
            return "Error al cerrar la Nota de Crédito. Se ha intentado anular el documento en la impresora."

    except (ConnectionError, ValueError) as e:
        return f"Error durante el envío de la Nota de Crédito: {e}"
