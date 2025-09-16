# models.py -> Añadir este nuevo código

from dataclasses import dataclass


def _parse_fiscal_amount(value_str: str) -> float:
    """Función de ayuda para convertir montos fiscales (ej: '000012345') a float (123.45)."""
    try:
        # Los montos vienen como enteros, los últimos 2 dígitos son los decimales.
        return float(value_str) / 100.0
    except (ValueError, TypeError):
        return 0.0


@dataclass
class ReportXData:
    """
    Representa los datos extraídos del Reporte X (comando U0X).
    La estructura se basa en las impresoras HKA80 y similares.
    Referencia: Manual, Páginas 70-71, Tabla 63.
    """

    numero_proximo_z: int
    fecha_ultimo_z: str
    hora_ultimo_z: str
    numero_ultima_factura: int
    fecha_ultima_factura: str
    hora_ultima_factura: str
    numero_ultima_nc: int
    numero_ultimo_nd: int
    numero_ultimo_doc_no_fiscal: int
    venta_exento: float
    venta_base_tasa1: float
    venta_iva_tasa1: float
    venta_base_tasa2: float
    venta_iva_tasa2: float
    venta_base_tasa3: float
    venta_iva_tasa3: float
    nc_exento: float
    nc_base_tasa1: float
    nc_iva_tasa1: float
    nc_base_tasa2: float
    nc_iva_tasa2: float
    nc_base_tasa3: float
    nc_iva_tasa3: float

    @classmethod
    def from_trama(cls, trama_str: str):
        """
        Crea una instancia de la clase a partir de la trama de respuesta 'U0X'.
        """
        # La trama viene como 'U0X\nCAMPO1\nCAMPO2\n...'
        # El separador es el carácter 0x0A (LF o '\n').
        parts = trama_str.strip().split("\n")

        if not parts[0].startswith("U0X") or len(parts) < 22:
            raise ValueError("Trama de Reporte X no válida o incompleta.")

        # El primer elemento es el comando 'U0X', los datos empiezan desde el índice 1
        data = parts[1:]

        # Para la HKA80 y similares, la estructura tiene notas de débito.
        # Nos basamos en la estructura del manual.
        # Por simplicidad, aquí mapeamos los campos más comunes.
        return cls(
            numero_proximo_z=int(data[0]),
            fecha_ultimo_z=data[1],
            hora_ultimo_z=data[2],
            numero_ultima_factura=int(data[3]),
            fecha_ultima_factura=data[4],
            hora_ultima_factura=data[5],
            numero_ultima_nc=int(data[6]),
            numero_ultimo_nd=int(data[7]),
            numero_ultimo_doc_no_fiscal=int(data[8]),
            venta_exento=_parse_fiscal_amount(data[9]),
            venta_base_tasa1=_parse_fiscal_amount(data[10]),
            venta_iva_tasa1=_parse_fiscal_amount(data[11]),
            venta_base_tasa2=_parse_fiscal_amount(data[12]),
            venta_iva_tasa2=_parse_fiscal_amount(data[13]),
            venta_base_tasa3=_parse_fiscal_amount(data[14]),
            venta_iva_tasa3=_parse_fiscal_amount(data[15]),
            # Omitimos los datos de ND por brevedad en el ejemplo
            # y saltamos a los de NC (Devoluciones)
            nc_exento=_parse_fiscal_amount(data[24]),
            nc_base_tasa1=_parse_fiscal_amount(data[25]),
            nc_iva_tasa1=_parse_fiscal_amount(data[26]),
            nc_base_tasa2=_parse_fiscal_amount(data[27]),
            nc_iva_tasa2=_parse_fiscal_amount(data[28]),
            nc_base_tasa3=_parse_fiscal_amount(data[29]),
            nc_iva_tasa3=_parse_fiscal_amount(data[30]),
        )


@dataclass
class S5PrinterData:
    """
    Representa los datos retornados por el comando de Status S5.
    Referencia: Manual, Página 64, Tabla 55.
    """

    rif: str
    serial_number: str
    audit_memory_number: int
    audit_memory_total_capacity_mb: int
    audit_memory_free_capacity_mb: int
    number_registered_documents: int

    @classmethod
    def from_trama(cls, trama_str: str):
        """
        Crea una instancia de la clase a partir de la trama de respuesta.
        """
        # La trama viene como 'S5\nJ-12345678\nSERIAL123\n0001\n2048\n1980\n123456'
        parts = trama_str.strip().split("\n")
        if len(parts) < 6 or not parts[0].startswith("S5"):
            raise ValueError("Trama de S5 no válida")

        return cls(
            rif=parts[1],
            serial_number=parts[2],
            audit_memory_number=int(parts[3]),
            audit_memory_total_capacity_mb=int(parts[4]),
            audit_memory_free_capacity_mb=int(parts[5]),
            number_registered_documents=int(parts[6]),
        )


# Puedes agregar más clases para otros status (S1, S2, S3, ReporteX, etc.)
# siguiendo la misma lógica y consultando las tablas del manual.
# Por ejemplo, para S1:
@dataclass
class S1PrinterData:
    """
    Representa los datos del comando S1 para HKA80.
    Referencia: Manual, Página 54, Tabla 45.
    """

    status_cajero: str
    subtotal_ventas: float
    numero_ultima_factura: int
    # ... y así sucesivamente con todos los campos.

    @classmethod
    def from_trama(cls, trama_str: str):
        # Implementar la lógica de parseo aquí...
        pass
