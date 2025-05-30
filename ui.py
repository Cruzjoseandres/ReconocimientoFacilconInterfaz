import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from datetime import datetime, timedelta
from logic import FaceAppLogic
from admin import AdminWindow

class FaceAppUI:
    def __init__(self, root, logic: FaceAppLogic):
        self.root = root
        self.logic = logic
        self.root.title("Registro facial")
        self.root.geometry("1000x600")

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.video_frame = tk.Frame(self.main_frame)
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.label_video = tk.Label(self.video_frame)
        self.label_video.pack(padx=10, pady=10, expand=True)

        self.control_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        self.entry_name = tk.Entry(self.control_frame, font=("Arial", 12))
        self.entry_name.pack(pady=10)
        self.entry_name.insert(0, "Nombre de la persona")

        self.button_register = tk.Button(
            self.control_frame, text="Registrar Rostro", command=self.registrar_rostro,
            bg="blue", fg="white", font=("Arial", 12), width=20)
        self.button_register.pack(pady=5)

        self.entry_update = tk.Entry(self.control_frame, font=("Arial", 12))
        self.entry_update.pack(pady=20)
        self.entry_update.insert(0, "Nombre para actualizar")

        self.button_habilitar = tk.Button(
            self.control_frame, text="Habilitar acceso", command=self.habilitar_acceso,
            bg="green", fg="white", font=("Arial", 12), width=20)
        self.button_habilitar.pack(pady=5)

        self.button_deshabilitar = tk.Button(
            self.control_frame, text="Deshabilitar acceso", command=self.deshabilitar_acceso,
            bg="red", fg="white", font=("Arial", 12), width=20)
        self.button_deshabilitar.pack(pady=5)

        self.entry_dias = tk.Entry(self.control_frame, font=("Arial", 12))
        self.entry_dias.pack(pady=10)
        self.entry_dias.insert(0, "Días disponibles")

        self.button_actualizar_dias = tk.Button(
            self.control_frame, text="Actualizar días disponibles", command=self.actualizar_dias_disponibles,
            bg="#FFA500", fg="white", font=("Arial", 12), width=25)
        self.button_actualizar_dias.pack(pady=5)

        self.button_admin = tk.Button(
            self.control_frame, text="Administrador", command=self.mostrar_admin,
            bg="#6A5ACD", fg="white", font=("Arial", 12), width=20)
        self.button_admin.pack(pady=15)

        self.cap = cv2.VideoCapture(0)
        self.current_frame = None
        self.face_locations_actual = None

        self.admin_window = AdminWindow(self.root, self.logic, self.cap)

        self.ventana_admin = None
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.bind('<Control-a>', self.mostrar_admin)

        self.actualizar_video()

    def actualizar_video(self):
        self.logic.verificar_fechas_expiracion()
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(30, self.actualizar_video)
            return

        display_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.logic.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        self.face_locations_actual = faces

        for (x, y, w, h) in faces:
            nombre = "Desconocido"
            color = (0, 255, 0)
            face_roi = frame[y:y + h, x:x + w]

            if face_roi.size > 0:
                # Usar el nuevo método de reconocimiento
                nombre_bd, confidence = self.logic.reconocer_rostro(face_roi)

                if nombre_bd != "Desconocido":
                    result = self.logic.obtener_info_persona(nombre_bd)
                    if result:
                        habilitado, fecha_registro, carnet_id = result
                        dias_restantes = "?"
                        if fecha_registro:
                            fecha = datetime.strptime(fecha_registro, "%Y-%m-%d")
                            dias_restantes = 30 - (datetime.now() - fecha).days
                            if dias_restantes <= 0:
                                dias_restantes = 0
                        if habilitado == 0:
                            nombre = f"{nombre_bd} (Acceso denegado)"
                            color = (0, 0, 255)
                        elif dias_restantes <= 5:
                            nombre = f"{nombre_bd} ({dias_restantes} dias)"
                            color = (0, 255, 255)
                        else:
                            nombre = f"{nombre_bd} ({dias_restantes} dias)"
                            color = (0, 255, 0)

            cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(display_frame, nombre, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

        self.current_frame = display_frame
        img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        self.label_video.imgtk = imgtk
        self.label_video.configure(image=imgtk)
        self.root.after(30, self.actualizar_video)

    def mostrar_admin(self):
        if not hasattr(self, 'admin_window'):
            self.admin_window = AdminWindow(self.root, self.logic, self.cap)
        self.admin_window.show()

    def registrar_rostro(self):
        nombre = self.entry_name.get().strip()
        if not nombre or nombre == "Nombre de la persona":
            messagebox.showwarning("Advertencia", "Ingrese un nombre válido.")
            return

        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "No se pudo capturar imagen de la cámara.")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.logic.face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) == 0:
            messagebox.showinfo("Info", "No se detectó ningún rostro.")
            return

        x, y, w, h = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        # Usar el nuevo método de registrar rostro
        try:
            self.logic.registrar_rostro(nombre, face_roi)
            messagebox.showinfo("Éxito", f"Rostro de {nombre} registrado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el rostro: {e}")

    def habilitar_acceso(self):
        nombre = self.entry_update.get().strip()
        if not nombre or nombre == "Nombre para actualizar":
            messagebox.showwarning("Advertencia", "Ingrese un nombre válido.")
            return
        self.logic.cursor.execute(
            "UPDATE personas SET habilitado = 1, expirado = 0 WHERE nombre = ?", (nombre,))
        self.logic.com.commit()
        messagebox.showinfo("Éxito", f"Acceso habilitado para {nombre}.")

    def deshabilitar_acceso(self):
        nombre = self.entry_update.get().strip()
        if not nombre or nombre == "Nombre para actualizar":
            messagebox.showwarning("Advertencia", "Ingrese un nombre válido.")
            return
        self.logic.cursor.execute(
            "UPDATE personas SET habilitado = 0 WHERE nombre = ?", (nombre,))
        self.logic.com.commit()
        messagebox.showinfo("Éxito", f"Acceso deshabilitado para {nombre}.")

    def actualizar_dias_disponibles(self):
        nombre = self.entry_update.get().strip()
        dias = self.entry_dias.get().strip()
        if not nombre or nombre == "Nombre para actualizar":
            messagebox.showwarning("Advertencia", "Ingrese un nombre válido.")
            return
        try:
            dias = int(dias)
            if dias < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Advertencia", "Ingrese un número de días válido.")
            return
        fecha_nueva = (datetime.now() - timedelta(days=30 - dias)).strftime("%Y-%m-%d")
        self.logic.cursor.execute(
            "UPDATE personas SET fecha_registro = ?, habilitado = 1, expirado = 0 WHERE nombre = ?",
            (fecha_nueva, nombre)
        )
        self.logic.com.commit()
        messagebox.showinfo("Éxito", f"Días disponibles actualizados para {nombre}.")




    def cerrar_aplicacion(self):
        self.cap.release()
        self.logic.cerrar()
        self.root.quit()



