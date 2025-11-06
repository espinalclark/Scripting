# login.py
import tkinter as tk
from tkinter import messagebox
from database import validar_login, registrar_usuario
from dashboard import abrir_dashboard

def iniciar_login():
    ventana = tk.Tk()
    ventana.title("Inicio de sesión")
    ventana.geometry("350x250")

    tk.Label(ventana, text="Usuario:").pack()
    usuario_entry = tk.Entry(ventana)
    usuario_entry.pack()

    tk.Label(ventana, text="Contraseña:").pack()
    password_entry = tk.Entry(ventana, show="*")
    password_entry.pack()

    def login():
        usuario = usuario_entry.get().strip()
        password = password_entry.get().strip()
        if validar_login(usuario, password):
            ventana.destroy()
            abrir_dashboard(usuario)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def registrar():
        usuario = usuario_entry.get().strip()
        password = password_entry.get().strip()
        if registrar_usuario(usuario, password):
            messagebox.showinfo("Éxito", "Usuario registrado correctamente")
        else:
            messagebox.showerror("Error", "El usuario ya existe o no se pudo registrar")

    tk.Button(ventana, text="Iniciar sesión", command=login).pack(pady=10)
    tk.Button(ventana, text="Registrar", command=registrar).pack()

    ventana.mainloop()

