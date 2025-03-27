import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Conexión a la base de datos
conexion = pymysql.connect(
    host=os.getenv("host"),
    user=os.getenv("user"),
    password=os.getenv("password"),
    db=os.getenv("db"),
    cursorclass=pymysql.cursors.DictCursor
)

# Estilo visual
def aplicar_estilo():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
    style.configure("Treeview", font=('Segoe UI', 10), rowheight=25)
    style.configure("TButton", font=('Segoe UI', 10), padding=5)
    style.configure("TCombobox", font=('Segoe UI', 10))
    style.configure("TLabel", font=('Segoe UI', 11))

# Obtener citas de hoy
def obtener_citas_hoy():
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT crm.id_cliente, crm.fecha_cita, crm.hora_cita, cl.nombre_completo
            FROM citas_crm crm
            LEFT JOIN clientes cl ON crm.id_cliente = cl.id_cliente
            WHERE DATE(crm.fecha_cita) = CURDATE()
        """)
        return cursor.fetchall()

# App principal
class AppCitas:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de asistencia - Citas de hoy")
        self.root.geometry("700x400")
        aplicar_estilo()

        ttk.Label(root, text="Citas para hoy", font=('Segoe UI', 14, 'bold')).pack(pady=10)

        self.frame = ttk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.tree = ttk.Treeview(self.frame, columns=("hora", "nombre", "asistencia"), show='headings')
        self.tree.heading("hora", text="Hora")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("asistencia", text="Asistió")

        self.tree.column("hora", width=100, anchor=tk.CENTER)
        self.tree.column("nombre", width=250)
        self.tree.column("asistencia", width=100, anchor=tk.CENTER)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.scroll.set)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.combos = {}
        self.cargar_citas()

        self.tree.bind("<ButtonRelease-1>", self.colocar_combobox)

        self.btn_enviar = ttk.Button(root, text="Enviar asistencia", command=self.enviar_asistencias)
        self.btn_enviar.pack(pady=10)

    def cargar_citas(self):
        self.datos_citas = obtener_citas_hoy()
        for cita in self.datos_citas:
            key = f"{cita['id_cliente']}|{cita['hora_cita']}"
            self.tree.insert("", tk.END, iid=key, values=(cita['hora_cita'], cita['nombre_completo'], ""))
            combo = ttk.Combobox(self.frame, values=["S", "N"], width=3, state="readonly")
            combo.current(0)
            self.combos[key] = combo

    def colocar_combobox(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if col == '#3' and item:
            x, y, width, height = self.tree.bbox(item, column="#3")
            combo = self.combos[item]
            combo.place(in_=self.tree, x=x, y=y)

    def enviar_asistencias(self):
        citas_insertadas = 0
        for key, combo in self.combos.items():
            id_cliente, hora = key.split("|")
            asistencia = combo.get()

            with conexion.cursor() as cursor:
                # Verificar si ya existe
                cursor.execute("""
                    SELECT 1 FROM citas_servicios 
                    WHERE id_cliente = %s AND fecha_cita = CURDATE() AND hora_cita = %s
                """, (id_cliente, hora))
                ya_existe = cursor.fetchone()

                if not ya_existe:
                    cursor.execute("""
                        INSERT INTO citas_servicios (
                            id_cliente, cita_asistida, fecha_cita, id_peluquero, hora_cita
                        ) VALUES (
                            %s, %s, CURDATE(),
                            (SELECT id_peluquero FROM citas_crm 
                             WHERE id_cliente = %s AND hora_cita = %s LIMIT 1),
                            %s
                        )
                    """, (id_cliente, asistencia, id_cliente, hora, hora))
                    citas_insertadas += 1

        conexion.commit()
        messagebox.showinfo("Registro completado", f"Asistencias registradas: {citas_insertadas}")

# Ejecutar app
if __name__ == "__main__":
    root = tk.Tk()
    app = AppCitas(root)
    root.mainloop()
