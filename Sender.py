# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pika, json, threading, datetime # pyright: ignore[reportMissingModuleSource]

class Sender:
    def __init__(self, root):
        self.root = root
        self.root.title("Sender | SO UMG")
        self.root.geometry("600x400")

        self.host = tk.StringVar(value="127.0.0.1")
        self.user = tk.StringVar(value="admin")
        self.password = tk.StringVar(value="admin123")
        self.queue = tk.StringVar(value="cola 1")
        self.count = tk.IntVar(value=5)
        self.prefix = tk.StringVar(value="Mensaje")

        frame = tk.Frame(root)
        frame.pack(pady=10, padx=10, fill="x")

        tk.Label(frame, text="Host:").grid(row=0, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.host, width=20).grid(row=0, column=1)
        tk.Label(frame, text="Usuario:").grid(row=1, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.user, width=20).grid(row=1, column=1)
        tk.Label(frame, text="Contraseña:").grid(row=2, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.password, show="*", width=20).grid(row=2, column=1)

        tk.Label(frame, text="Cola:").grid(row=0, column=2, sticky="e")
        ttk.Combobox(frame, textvariable=self.queue, values=["cola 1", "cola 2"], width=10).grid(row=0, column=3)
        tk.Label(frame, text="Cantidad:").grid(row=1, column=2, sticky="e")
        tk.Spinbox(frame, from_=1, to=10000, textvariable=self.count, width=10).grid(row=1, column=3)
        tk.Label(frame, text="Prefijo:").grid(row=2, column=2, sticky="e")
        tk.Entry(frame, textvariable=self.prefix, width=10).grid(row=2, column=3)

        self.btn_connect = tk.Button(frame, text="Conectar", command=self.connect)
        self.btn_connect.grid(row=3, column=0, pady=10)
        self.btn_send = tk.Button(frame, text="Enviar", command=self.send_messages, state="disabled")
        self.btn_send.grid(row=3, column=1, pady=10)

        self.log = scrolledtext.ScrolledText(root, state="disabled", height=15)
        self.log.pack(padx=10, pady=10, fill="both", expand=True)

        self.connection = None
        self.channel = None

    def connect(self):
        try:
            credentials = pika.PlainCredentials(self.user.get(), self.password.get())
            parameters = pika.ConnectionParameters(host=self.host.get(), port=5672, credentials=credentials)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='cola 1')
            self.channel.queue_declare(queue='cola 2')
            self.log_message("✅ Conectado correctamente a RabbitMQ")
            self.btn_send.config(state="normal")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_messages(self):
        if not self.channel:
            messagebox.showwarning("Error", "No hay conexión activa.")
            return

        queue = self.queue.get()
        count = self.count.get()
        prefix = self.prefix.get()

        def worker():
            for i in range(count):
                msg = {"id": i+1, "mensaje": f"{prefix} {i+1} en {queue}", "tiempo": str(datetime.datetime.now())}
                self.channel.basic_publish(exchange='', routing_key=queue, body=json.dumps(msg))
                self.log_message(f"[Enviado] {msg}")
            self.log_message("✅ Envío completado.")

        threading.Thread(target=worker, daemon=True).start()

    def log_message(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", f"{msg}\n")
        self.log.yview("end")
        self.log.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = Sender(root)
    root.mainloop()
