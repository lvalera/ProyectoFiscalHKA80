import requests
import json

api_url = "http://192.168.68.108:5000/invoice"  # IP de la máquina con la impresora

invoice_data = {
    "customer_data": {"rif": "V-12345678", "name": "Prueba API Python"},
    "items": [
        {
            "desc": "Producto API",
            "price": 10.0,
            "qty": 2,
            "tax_rate": "Tasa General (G)",
        },
        {"desc": "Servicio Exento", "price": 50.0, "qty": 1, "tax_rate": "Exento (E)"},
    ],
}

response = requests.post(api_url, json=invoice_data)

print(f"Status Code: {response.status_code}")
print("Respuesta del servidor:")
print(response.json())
