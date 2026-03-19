from __future__ import annotations

import os
import time
import subprocess
import tkinter as tk
from tkinter import messagebox

from services.app.dashboard_launch import (
    dashboard_default_port,
    dashboard_port_search_limit,
    dashboard_streamlit_cmd,
    open_dashboard_browser,
    port_open,
    resolve_dashboard_launch,
)

LOG_PATH = os.path.join("data", "desktop_launcher.log")

def _log(msg: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{int(time.time())} {msg}\n")

class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Crypto Bot Pro — Desktop")
        self.proc: subprocess.Popen | None = None

        self.port = dashboard_default_port(fallback=8501)
        self.host = "127.0.0.1"
        self.ctx = resolve_dashboard_launch(
            host=self.host,
            preferred_port=self.port,
            search_limit=dashboard_port_search_limit(),
        )
        self.url = self.ctx.url

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

    def _refresh_context(self) -> None:
        self.ctx = resolve_dashboard_launch(
            host=self.host,
            preferred_port=self.port,
            search_limit=dashboard_port_search_limit(),
        )
        self.url = self.ctx.url
        status_port = self.ctx.resolved_port
        if self.ctx.auto_switched:
            self.status.set(f"Status: requested {self.ctx.requested_port} busy, using {status_port}")

    def start(self):
        if self.proc and self.proc.poll() is None:
            self.status.set("Status: already running")
            return

        self._refresh_context()

        if not self.ctx.auto_switched and port_open(self.ctx.host, self.ctx.resolved_port):
            self.status.set("Status: port already in use — opening UI")
            self.open_ui()
            return

        cmd = dashboard_streamlit_cmd(self.ctx, headless=True)
        _log("Starting Streamlit: " + " ".join(cmd))

        creationflags = 0
        if os.name == "nt":
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
            if port_open(self.ctx.host, self.ctx.resolved_port):
                self.status.set("Status: running")
                self.open_ui()
                return
            time.sleep(0.2)

        self.status.set("Status: started (UI not reachable yet)")
        self.open_ui()

    def open_ui(self):
        open_dashboard_browser(self.ctx)

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
