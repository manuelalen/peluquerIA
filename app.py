from flask import Flask, request, render_template, jsonify, url_for
import pymysql
import random
from twilio.rest import Client
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Conexión MySQL
conexion = pymysql.connect(
    host=os.getenv('host'),
    user=os.getenv('user'),
    password=os.getenv('password'),
    db=os.getenv('db'),
    cursorclass=pymysql.cursors.DictCursor
)

# Twilio
account_sid = os.getenv("account_sid")
auth_token = os.getenv("auth_token")
twilio_client = Client(account_sid, auth_token)
twilio_number = 'whatsapp:+14155238886'  # Número sandbox Twilio

@app.route("/", methods=["GET", "POST"])
def cita():
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id_peluquero, nombre_completo FROM trabajadores_peluqueria")
        peluqueros = cursor.fetchall()

    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        servicio = request.form["servicio"]
        id_peluquero = request.form["peluquero"]

        with conexion.cursor() as cursor:
            # Verificar si el cliente ya existe
            cursor.execute("SELECT id_cliente FROM clientes WHERE telefono = %s", (telefono,))
            resultado = cursor.fetchone()

            if resultado:
                id_cliente = resultado['id_cliente']
            else:
                id_cliente = random.randint(10**7, 10**8 - 1)
                cursor.execute("""
                    INSERT INTO clientes (id_cliente, nombre_completo, telefono, email)
                    VALUES (%s, %s, %s, 'null@nullez.com')
                """, (id_cliente, nombre, telefono))
                conexion.commit()

            # Insertar la cita
            cursor.execute("""
                INSERT INTO citas_crm (id_cliente, fecha_cita, Servicio, hora_cita, id_peluquero) 
                VALUES (%s, %s, %s, %s, %s)
            """, (id_cliente, fecha, servicio, hora, id_peluquero))
            conexion.commit()

        # Enviar WhatsApp
        try:
            twilio_client.messages.create(
                from_=twilio_number,
                to=f'whatsapp:+34{telefono}',
                body=f"Confirmamos tu cita el {fecha} a las {hora}. ¡Te esperamos!"
            )
        except Exception as e:
            print("Error al enviar WhatsApp:", e)

        return "¡Cita registrada y confirmación enviada por WhatsApp!"

    return render_template("formulario.html", peluqueros=peluqueros)

@app.route("/horas_disponibles", methods=["POST"])
def horas_disponibles():
    data = request.get_json()
    fecha = data['fecha']
    peluquero = data['peluquero']

    # Horas posibles entre 13:00 y 21:00
    todas_horas = [f"{h:02d}:00" for h in range(13, 22)]

    with conexion.cursor() as cursor:
        # Filtrar citas ya ocupadas
        cursor.execute("""
            SELECT hora_cita FROM citas_crm 
            WHERE DATE(fecha_cita) = %s AND id_peluquero = %s
        """, (fecha, peluquero))
        horas_ocupadas = [row['hora_cita'] for row in cursor.fetchall()]

        # Verificar vacaciones del peluquero
        cursor.execute("""
            SELECT 1 FROM vacaciones 
            WHERE id_peluquero = %s AND %s BETWEEN DATE(fecha_inicio) AND DATE(fecha_final)
        """, (peluquero, fecha))
        en_vacaciones = cursor.fetchone()

    if en_vacaciones:
        return jsonify([])

    horas_libres = [h for h in todas_horas if h not in horas_ocupadas]
    return jsonify(horas_libres)

if __name__ == "__main__":
    app.run(debug=True)
