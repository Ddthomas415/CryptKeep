from __future__ import annotations

import os
import sys
import time
import socket
import subprocess
import webbrowser
import tkinter as tk
from tkinter import messagebox

LOG_PATH = os.path.join("data", "desktop_launcher.log")

def _log(msg: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{int(time.time())} {msg}\n")

def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False

class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Crypto Bot Pro — Desktop")
        self.proc: subprocess.Popen | None = None

        self.port = int(os.environ.get("APP_PORT", "8501"))
        self.host = "127.0.0.1"
        self.url = f"http://{self.host}:{self.port}"

        frm = tk.Frame(self.root, padx=14, pady=14)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="Crypto Bot Pro — Desktop Launcher", font=("Arial", 14, "bold")).pack(anchor="w")
        tk.Label(frm, text=f"UI URL: {self.url}").pack(anchor="w", pady=(6, 10))

        btns = tk.Frame(frm)
        btns.pack(fill="x")

        self.start_btn = tk.Button(btns, text="Start", command=self.start)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.open_btn = tk.Button(btns, text="Open UI", command=self.open_ui)
        self.open_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(btns, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.status = tk.StringVar(value="Status: stopped")
        tk.Label(frm, textvariable=self.status).pack(anchor="w", pady=(10, 0))

        tk.Label(frm, text=f"Log: {LOG_PATH}", fg="#444").pack(anchor="w", pady=(6, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _streamlit_cmd(self) -> list[str]:
        # Important: use module invocation so PyInstaller + venv behave consistently.
        # Streamlit app path:
        app_path = os.path.join("dashboard", "app.py")
        # Make Streamlit quieter and deterministic.
        return [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.address", self.host,
            "--server.port", str(self.port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ]

    def start(self):
        if self.proc and self.proc.poll() is None:
            self.status.set("Status: already running")
            return

        if _port_open(self.host, self.port):
            self.status.set("Status: port already in use — opening UI")
            self.open_ui()
            return

        cmd = self._streamlit_cmd()
        _log("Starting Streamlit: " + " ".join(cmd))

        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.getcwd(),
                creationflags=creationflags,
            )
        except Exception as e:
            messagebox.showerror("Start failed", str(e))
            _log(f"Start failed: {e}")
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.set("Status: starting...")

        # Wait briefly for server
        for _ in range(50):  # ~10s
            if _port_open(self.host, self.port):
                self.status.set("Status: running")
                self.open_ui()
                return
            time.sleep(0.2)

        self.status.set("Status: started (UI not reachable yet)")
        self.open_ui()

    def open_ui(self):
        webbrowser.open(self.url)

    def stop(self):
        if not self.proc or self.proc.poll() is not None:
            self.status.set("Status: not running")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            return

        _log("Stopping Streamlit")
        try:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
        except Exception as e:
            _log(f"Stop error: {e}")

        self.proc = None
        self.status.set("Status: stopped")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def on_close(self):
        try:
            self.stop()
        finally:
            self.root.destroy()

def main():
    Launcher().root.mainloop()

if __name__ == "__main__":
    main()
