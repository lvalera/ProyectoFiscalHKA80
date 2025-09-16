# communication.py
import serial
import time

# Ya no importamos SERIAL_PORT, pero sí el resto de la configuración
from config import BAUDRATE, PARITY, STOPBITS, BYTESIZE


class FiscalPrinter:
    """
    Clase para manejar la comunicación de bajo nivel con la impresora fiscal
    utilizando el protocolo directo.
    """

    _STX = b"\x02"
    _ETX = b"\x03"
    _ACK = b"\x06"
    _NAK = b"\x15"
    _ENQ = b"\x05"

    def __init__(
        self, port, baudrate=BAUDRATE, timeout=2
    ):  # 'port' ahora es un argumento obligatorio
        """
        Inicializa la conexión serial.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        # La lógica de conexión se mueve al método connect() para ser llamada por el usuario

    def connect(self):
        """Abre la conexión serial."""
        if self.serial_connection and self.serial_connection.is_open:
            print("La conexión ya está abierta.")
            return
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=PARITY,
                stopbits=STOPBITS,
                bytesize=BYTESIZE,
                timeout=self.timeout,
            )
            print(f"Conexión establecida en el puerto {self.port}.")
        except serial.SerialException as e:
            print(f"Error al abrir el puerto {self.port}: {e}")
            raise ConnectionError(f"No se pudo conectar a la impresora en {self.port}.")

    # ... el resto de la clase (calculate_lrc, send_command, etc.) no cambia ...

    def _calculate_lrc(self, data_bytes):
        lrc = 0
        for byte in data_bytes:
            lrc ^= byte
        lrc ^= self._ETX[0]
        return bytes([lrc])

    def send_command(self, command_data_str):
        if not self.serial_connection or not self.serial_connection.is_open:
            raise ConnectionError("La conexión serial no está abierta.")

        command_bytes = command_data_str.encode("ascii")
        lrc = self._calculate_lrc(command_bytes)
        frame = self._STX + command_bytes + self._ETX + lrc

        print(f"-> Enviando Trama: {frame}")
        self.serial_connection.write(frame)
        time.sleep(0.1)
        return self.read_response()

    def read_response(self):
        response = self.serial_connection.read_until(self._ETX)
        if self._ETX in response:
            lrc_byte = self.serial_connection.read(1)
            response += lrc_byte

        print(f"<- Recibido: {response}")
        return response

    def close(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Conexión serial cerrada.")

    # communication.py -> Añadir este método dentro de la clase FiscalPrinter

    def get_status(self):
        """
        Envía el comando ENQ para obtener el status STS1 y STS2 de la impresora.
        Este es un comando especial que no usa la trama STX/ETX.
        Referencia: Manual, Página 17 y 18.
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            raise ConnectionError("La conexión serial no está abierta.")

        enq_command = self._ENQ  # b'\x05'
        print(f"-> Enviando ENQ: {enq_command}")
        self.serial_connection.write(enq_command)
        time.sleep(0.1)

        # La respuesta esperada es: STX STS1 STS2 ETX LRC (5 bytes en total)
        response = self.serial_connection.read(5)
        print(f"<- Recibido de ENQ: {response}")

        # Verificamos que la respuesta tenga el formato correcto
        if (
            len(response) == 5
            and response.startswith(self._STX)
            and response[3:4] == self._ETX
        ):
            sts1_byte = response[1:2]  # El segundo byte (índice 1) es STS1
            sts2_byte = response[2:3]  # El tercer byte (índice 2) es STS2
            return sts1_byte, sts2_byte

        # Si la respuesta no es la esperada
        return None, None
