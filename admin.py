import tkinter as tk
from tkinter import messagebox, ttk
import cv2
from PIL import Image, ImageTk
from datetime import datetime


class AdminWindow:
    def __init__(self, parent, logic, camera):
        """
        Inicializa la ventana de administración

        Args:
            parent: Ventana principal de la aplicación
            logic: Instancia de FaceAppLogic
            camera: Instancia de la cámara (cv2.VideoCapture)
        """
        self.parent = parent
        self.logic = logic
        self.cap = camera
        self.window = None

    def show(self):
        """Muestra la ventana de administración"""
        if self.window:
            self.window.deiconify()
            self.refrescar_tabla()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Administrador de Rostros")
        self.window.geometry("900x500")

        # Frame superior con la tabla
        frame_tabla = tk.Frame(self.window)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Crear tabla con scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tabla mejorada
        self.tree = ttk.Treeview(frame_tabla,
                                 columns=("ID", "Nombre", "Estado", "Días Restantes", "Carnet ID"),
                                 show="headings",
                                 yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Estado", text="Estado")
        self.tree.heading("Días Restantes", text="Días Restantes")
        self.tree.heading("Carnet ID", text="Carnet ID")

        # Ajustar ancho de columnas
        self.tree.column("ID", width=50)
        self.tree.column("Nombre", width=150)
        self.tree.column("Estado", width=100)
        self.tree.column("Días Restantes", width=120)
        self.tree.column("Carnet ID", width=120)

        # Frame inferior con formulario CRUD
        frame_crud = tk.Frame(self.window)
        frame_crud.pack(fill=tk.X, padx=10, pady=10)

        # Campos de formulario
        tk.Label(frame_crud, text="ID:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_id = tk.Entry(frame_crud, width=10)
        self.entry_id.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_crud, text="Nombre:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_nombre = tk.Entry(frame_crud, width=20)
        self.entry_nombre.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(frame_crud, text="Carnet:").grid(row=0, column=4, padx=5, pady=5)
        self.entry_carnet = tk.Entry(frame_crud, width=20)
        self.entry_carnet.grid(row=0, column=5, padx=5, pady=5)

        # Frame para botones
        frame_botones = tk.Frame(self.window)
        frame_botones.pack(fill=tk.X, padx=10, pady=10)

        # Botones CRUD
        self.btn_nuevo = tk.Button(frame_botones, text="Nuevo", command=self.nuevo_registro,
                                   bg="#4CAF50", fg="white", width=15)
        self.btn_nuevo.pack(side=tk.LEFT, padx=5)

        self.btn_actualizar = tk.Button(frame_botones, text="Actualizar", command=self.actualizar_registro,
                                        bg="#2196F3", fg="white", width=15)
        self.btn_actualizar.pack(side=tk.LEFT, padx=5)

        self.btn_eliminar = tk.Button(frame_botones, text="Eliminar", command=self.eliminar_registro,
                                      bg="#F44336", fg="white", width=15)
        self.btn_eliminar.pack(side=tk.LEFT, padx=5)

        self.btn_refrescar = tk.Button(frame_botones, text="Refrescar", command=self.refrescar_tabla,
                                       bg="#9E9E9E", fg="white", width=15)
        self.btn_refrescar.pack(side=tk.RIGHT, padx=5)

        # Vincular evento de selección de fila
        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_fila)

        # Cargar datos
        self.refrescar_tabla()

    def seleccionar_fila(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        valores = item['values']

        # Limpia y llena los campos
        self.entry_id.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.entry_carnet.delete(0, tk.END)

        self.entry_id.insert(0, valores[0])
        self.entry_nombre.insert(0, valores[1])
        self.entry_carnet.insert(0, valores[4] if valores[4] else "")

    def refrescar_tabla(self):
        # Limpia la tabla
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Obtiene datos actualizados incluyendo ID
        filas = self.logic.obtener_todas_personas_con_id()
        for fila in filas:
            id_persona, nombre, habilitado, fecha_registro, carnet_id = fila
            dias_restantes = "?"
            if fecha_registro:
                fecha = datetime.strptime(fecha_registro, "%Y-%m-%d")
                dias_restantes = 30 - (datetime.now() - fecha).days
                if dias_restantes <= 0:
                    dias_restantes = "Expirado"
            estado = "Activo" if habilitado else "Deshabilitado"
            self.tree.insert("", "end", values=(id_persona, nombre, estado, dias_restantes, carnet_id))

    def nuevo_registro(self):
        # Abre ventana para capturar nuevo rostro
        nombre = self.entry_nombre.get().strip()
        carnet_id = self.entry_carnet.get().strip()

        if not nombre:
            messagebox.showwarning("Advertencia", "Ingrese un nombre válido.")
            return

        # Capturar rostro
        top = tk.Toplevel(self.window)
        top.title("Capturar Rostro")
        top.geometry("500x400")

        label_video_capture = tk.Label(top)
        label_video_capture.pack(pady=10)

        def actualizar_captura():
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.logic.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )

                frame_copia = frame.copy()
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame_copia, (x, y), (x + w, y + h), (0, 255, 0), 2)

                img = cv2.cvtColor(frame_copia, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                imgtk = ImageTk.PhotoImage(image=img)
                label_video_capture.imgtk = imgtk
                label_video_capture.configure(image=imgtk)
                label_video_capture.img = imgtk
                top.after(30, actualizar_captura)

        def capturar():
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
            face_roi = gray[y:y + h, x:x + w]

            try:
                self.logic.registrar_rostro_con_carnet(nombre, face_roi, carnet_id)
                messagebox.showinfo("Éxito", f"Rostro de {nombre} registrado correctamente.")
                top.destroy()
                self.refrescar_tabla()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el rostro: {e}")

        actualizar_captura()

        btn_capturar = tk.Button(top, text="Capturar", command=capturar,
                                 bg="#4CAF50", fg="white", width=15)
        btn_capturar.pack(pady=10)

    def actualizar_registro(self):
        id_persona = self.entry_id.get().strip()
        nombre = self.entry_nombre.get().strip()
        carnet_id = self.entry_carnet.get().strip()

        if not id_persona or not nombre:
            messagebox.showwarning("Advertencia", "Seleccione un registro válido.")
            return

        try:
            self.logic.actualizar_persona(id_persona, nombre, carnet_id)
            messagebox.showinfo("Éxito", "Registro actualizado correctamente.")
            self.refrescar_tabla()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el registro: {e}")

    def eliminar_registro(self):
        id_persona = self.entry_id.get().strip()

        if not id_persona:
            messagebox.showwarning("Advertencia", "Seleccione un registro válido.")
            return

        confirmacion = messagebox.askyesno("Confirmar",
                                           "¿Está seguro que desea eliminar este registro? Esta acción no se puede deshacer.")

        if confirmacion:
            try:
                self.logic.eliminar_persona(id_persona)
                messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
                self.refrescar_tabla()

                # Limpia los campos
                self.entry_id.delete(0, tk.END)
                self.entry_nombre.delete(0, tk.END)
                self.entry_carnet.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")