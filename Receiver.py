# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import scrolledtext, messagebox
import pika, json, threading, datetime

class Receiver:
    def __init__(self, root):
        self.root = root
        self.root.title("Receiver | SO UMG")
        self.root.geometry("680x420")

        self.host = tk.StringVar(value="127.0.0.1")
        self.user = tk.StringVar(value="admin")
        self.password = tk.StringVar(value="admin123")

        frame = tk.Frame(root)
        frame.pack(pady=10, padx=10, fill="x")

        tk.Label(frame, text="Host:").grid(row=0, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.host, width=20).grid(row=0, column=1)
        tk.Label(frame, text="Usuario:").grid(row=1, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.user, width=20).grid(row=1, column=1)
        tk.Label(frame, text="Contraseña:").grid(row=2, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.password, show="*", width=20).grid(row=2, column=1)

        self.btn_start = tk.Button(frame, text="Iniciar Receiver", command=self.start_receiver)
        self.btn_start.grid(row=3, column=0, pady=10)

        self.log = scrolledtext.ScrolledText(root, state="disabled", height=16)
        self.log.pack(padx=10, pady=10, fill="both", expand=True)

    # ---------- UI helpers ----------
    def log_message(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", f"{msg}\n")
        self.log.yview("end")
        self.log.config(state="disabled")

    def start_receiver(self):
        self.btn_start.config(state="disabled")
        # Un hilo por cola (requisito de la tarea)
        threading.Thread(target=self.worker_queue1, daemon=True).start()
        threading.Thread(target=self.worker_queue2, daemon=True).start()

    # ---------- Hilo 1: lee cola 1 y genera 8 en cola 2 ----------
    def worker_queue1(self):
        try:
            creds = pika.PlainCredentials(self.user.get(), self.password.get())
            params = pika.ConnectionParameters(host=self.host.get(), port=5672, credentials=creds)
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.queue_declare(queue='cola 1')
            ch.queue_declare(queue='cola 2')
            ch.basic_qos(prefetch_count=1)

            self.log_message("✅ Hilo 1 escuchando: cola 1")

            def on_msg(ch_, method, properties, body):
                try:
                    msg = json.loads(body)
                except Exception:
                    msg = {"raw": body.decode("utf-8", errors="ignore")}
                self.log_message(f"[Cola 1] RX: {msg}")

                # Generar 8 mensajes nuevos en cola 2 (requisito)
                for i in range(8):
                    nuevo = {
                        "origen": msg,
                        "nuevo_id": i + 1,
                        "distintivo": "Generado por hilo1 a partir de cola 1",
                        "auto_generated": True,
                        "ts": datetime.datetime.now().isoformat(timespec="seconds")
                    }
                    ch_.basic_publish(exchange='', routing_key='cola 2', body=json.dumps(nuevo))
                    self.log_message(f"[Cola 1→Cola 2] Generado {i+1}/8")

                ch_.basic_ack(delivery_tag=method.delivery_tag)

            ch.basic_consume(queue='cola 1', on_message_callback=on_msg, auto_ack=False)
            ch.start_consuming()
        except Exception as e:
            self.log_message(f"❌ Hilo 1 error: {e}")
            self.btn_start.config(state="normal")

    # ---------- Hilo 2: solo lee cola 2 (no publica) ----------
    def worker_queue2(self):
        try:
            creds = pika.PlainCredentials(self.user.get(), self.password.get())
            params = pika.ConnectionParameters(host=self.host.get(), port=5672, credentials=creds)
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.queue_declare(queue='cola 2')
            ch.basic_qos(prefetch_count=1)

            self.log_message("✅ Hilo 2 escuchando: cola 2")

            def on_msg(ch_, method, properties, body):
                try:
                    msg = json.loads(body)
                except Exception:
                    msg = {"raw": body.decode("utf-8", errors="ignore")}
                self.log_message(f"[Cola 2] RX: {msg}")
                # NO publicar nada aquí (requisito)
                ch_.basic_ack(delivery_tag=method.delivery_tag)

            ch.basic_consume(queue='cola 2', on_message_callback=on_msg, auto_ack=False)
            ch.start_consuming()
        except Exception as e:
            self.log_message(f"❌ Hilo 2 error: {e}")
            self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = Receiver(root)
    root.mainloop()
