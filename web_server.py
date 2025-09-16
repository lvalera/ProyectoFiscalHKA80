# web_server.py
import threading
from flask import Flask, request, jsonify
import commands

# --- Variables Globales y Mecanismos de Sincronización ---

# Esta variable global contendrá la instancia de la impresora una vez que la GUI se conecte.
g_printer_instance = None

# Un Lock para asegurar que solo una petición a la vez acceda a la impresora.
printer_lock = threading.Lock()

# Creamos la aplicación Flask
api = Flask(__name__)

# --- Definición de los Endpoints de la API ---


@api.route("/status", methods=["GET"])
def get_status():
    """Endpoint para obtener el status STS1/STS2 de la impresora."""
    if g_printer_instance is None:
        return jsonify({"status": "error", "message": "Impresora no conectada."}), 503

    with printer_lock:
        status_message = commands.read_printer_status(g_printer_instance)

    return jsonify({"status": "success", "data": status_message})


@api.route("/invoice", methods=["POST"])
def create_invoice():
    """Endpoint para recibir datos de una factura en formato JSON y mandarla a imprimir."""
    if g_printer_instance is None:
        return jsonify({"status": "error", "message": "Impresora no conectada."}), 503

    data = request.get_json()
    if not data or "customer_data" not in data or "items" not in data:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "JSON inválido. Se requieren 'customer_data' y 'items'.",
                }
            ),
            400,
        )

    with printer_lock:
        result = commands.send_full_invoice(
            g_printer_instance, data["customer_data"], data["items"]
        )

    if "correctamente" in result:
        return jsonify({"status": "success", "message": result})
    else:
        return jsonify({"status": "error", "message": result}), 500


@api.route("/credit_note", methods=["POST"])
def create_credit_note():
    """Endpoint para recibir datos de una nota de crédito en JSON y mandarla a imprimir."""
    if g_printer_instance is None:
        return jsonify({"status": "error", "message": "Impresora no conectada."}), 503

    data = request.get_json()
    if (
        not data
        or "affected_doc" not in data
        or "customer_data" not in data
        or "items" not in data
    ):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "JSON inválido. Se requieren 'affected_doc', 'customer_data' y 'items'.",
                }
            ),
            400,
        )

    with printer_lock:
        result = commands.send_full_credit_note(
            g_printer_instance,
            data["affected_doc"],
            data["customer_data"],
            data["items"],
        )

    if "correctamente" in result:
        return jsonify({"status": "success", "message": result})
    else:
        return jsonify({"status": "error", "message": result}), 500


# --- Función para iniciar el servidor ---


def start_server(printer_object, host="0.0.0.0", port=5000):
    """
    Esta función establece la instancia de la impresora y arranca el servidor Flask.
    Se ejecuta en un hilo separado.
    """
    global g_printer_instance
    g_printer_instance = printer_object
    print(f"Servidor HTTP iniciado en http://{host}:{port}. Escuchando peticiones...")
    # '0.0.0.0' hace que el servidor sea accesible desde otras máquinas en la red.
    api.run(host=host, port=port)


def stop_server():
    """Actualiza la instancia de la impresora a None cuando se desconecta."""
    global g_printer_instance
    g_printer_instance = None
    print("Servidor HTTP detenido (ya no aceptará nuevas impresiones).")
