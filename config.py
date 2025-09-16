# config.py
# Configuración de la comunicación para la impresora fiscal.
# El puerto serial (SERIAL_PORT) se seleccionará desde la interfaz de usuario.

# [cite_start]Parámetros de comunicación según el manual (Página 15) [cite: 213]
BAUDRATE = 9600
PARITY = "E"  # Par (Even)
STOPBITS = 1
BYTESIZE = 8
