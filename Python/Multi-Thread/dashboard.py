# dashboard.py
import tkinter as tk
from tkinter import ttk, messagebox
from downloader import MultiThreadDownloader
from database import registrar_descarga, obtener_historial
import datetime

def abrir_dashboard(usuario):
    ventana = tk.Tk()
    ventana.title(f"Gestor de Descargas - {usuario}")
    ventana.geometry("600x450")

    tk.Label(ventana, text=f"Bienvenido, {usuario}", font=("Arial", 14)).pack(pady=10)

    url_entry = tk.Entry(ventana, width=50)
    url_entry.pack(pady=5)

    progreso = tk.DoubleVar()
    progress_bar = ttk.Progressbar(ventana, variable=progreso, maximum=100, length=400)
    progress_bar.pack(pady=10)

    historial_box = tk.Listbox(ventana, width=80, height=10)
    historial_box.pack(pady=10)

    def cargar_historial():
        historial_box.delete(0, tk.END)
        historial = obtener_historial(usuario)
        if not historial:
            historial_box.insert(tk.END, "No hay descargas registradas.")
        else:
            for file_name, file_url, fecha in historial:
                historial_box.insert(tk.END, f"{fecha} - {file_name} ({file_url})")

    def descargar():
        url = url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Debe ingresar una URL válida.")
            return

        downloader = MultiThreadDownloader(url, progreso)
        try:
            archivo = downloader.start()
            registrar_descarga(usuario, os.path.basename(archivo), url)
            messagebox.showinfo("Éxito", f"Archivo descargado: {archivo}")
            cargar_historial()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo descargar el archivo.\n{e}")

    tk.Button(ventana, text="Descargar", command=descargar).pack(pady=10)
    tk.Button(ventana, text="Actualizar historial", command=cargar_historial).pack(pady=5)

    cargar_historial()
    ventana.mainloop()

