from __future__ import annotations
import argparse
import os
import threading
import time
import webbrowser
from services.os.app_paths import code_root, ensure_dirs, runtime_dir, state_root

def _read_env(name: str, default: str) -> str:
    v = os.getenv(name, "").strip()
    return v or default

def _open(url: str):
    try:
        webbrowser.open(url, new=1)
    except Exception:
        pass

def _write_stop_files(stop_tick: bool, stop_webhook: bool) -> None:
    try:
        (runtime_dir() / "flags").mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    if stop_tick:
        try:
            (runtime_dir() / "flags" / "tick_publisher.stop").write_text("stop\n", encoding="utf-8")
        except Exception:
            pass
    if stop_webhook:
        try:
            (runtime_dir() / "flags" / "evidence_webhook.stop").write_text("stop\n", encoding="utf-8")
        except Exception:
            pass

def _start_streamlit(host: str, port: str):
    import streamlit.web.bootstrap as bootstrap
    app_path = str((code_root() / "dashboard" / "app.py").resolve())
    flag_options = {
        "server.address": host,
        "server.port": int(port),
        "browser.serverAddress": host,
        "browser.gatherUsageStats": False,
    }
    bootstrap.run(app_path, "streamlit run", [], flag_options)

def _start_tick_publisher():
    try:
        from services.market_data.system_status_publisher import run_forever
        t = threading.Thread(target=run_forever, daemon=True)
        t.start()
    except Exception:
        pass

def _start_evidence_webhook():
    try:
        from services.evidence.webhook_server import run
        t = threading.Thread(target=run, daemon=True)
        t.start()
    except Exception:
        pass

def main():
    ensure_dirs()
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--safe", action="store_true", help="Safe Mode: dashboard only (no tick publisher, no webhook).")
    args, _ = ap.parse_known_args()
    host = _read_env("CBP_HOST", "127.0.0.1")
    port = _read_env("CBP_PORT", "8501")
    url = f"http://{host}:{port}"
    default_mode = "safe" if args.safe or (_read_env("CBP_MODE", "").lower() == "safe") else "full"
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        if default_mode == "full":
            _start_tick_publisher()
            _start_evidence_webhook()
        _open(url)
        _start_streamlit(host, port)
        return
    root = tk.Tk()
    root.title("CryptoBotPro")
    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    ttk.Label(frm, text="CryptoBotPro (local)", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
    ttk.Label(frm, text=f"URL: {url}").grid(row=1, column=0, columnspan=3, sticky="w")
    ttk.Label(frm, text=f"State dir: {state_root()}").grid(row=2, column=0, columnspan=3, sticky="w")
    mode = tk.StringVar(value=default_mode)
    ttk.Label(frm, text="Mode:").grid(row=3, column=0, sticky="w", pady=(10,0))
    ttk.Radiobutton(frm, text="Full (Dashboard + Tick + Webhook)", variable=mode, value="full").grid(row=3, column=1, sticky="w", pady=(10,0))
    ttk.Radiobutton(frm, text="Safe (Dashboard only)", variable=mode, value="safe").grid(row=3, column=2, sticky="w", pady=(10,0))
    status = tk.StringVar(value="Ready.")
    ttk.Label(frm, textvariable=status).grid(row=4, column=0, columnspan=3, sticky="w", pady=(10,0))
    started = {"ok": False}
    def do_start():
        if started["ok"]:
            status.set("Already running.")
            return
        started["ok"] = True
        status.set("Starting…")
        if mode.get() == "full":
            _start_tick_publisher()
            _start_evidence_webhook()
        th = threading.Thread(target=_start_streamlit, args=(host, port), daemon=True)
        th.start()
        def later():
            time.sleep(0.8)
            _open(url)
            status.set("Running. Quit stops the whole app. Stop Services requests graceful stop for tick/webhook.")
        threading.Thread(target=later, daemon=True).start()
    def do_open():
        _open(url)
        status.set("Browser opened.")
    def do_stop_services():
        _write_stop_files(stop_tick=True, stop_webhook=True)
        status.set("Stop requested for Tick/Webhook (stop-files written).")
    def do_quit():
        status.set("Stopping…")
        _write_stop_files(stop_tick=True, stop_webhook=True)
        root.after(150, root.destroy)
    btns = ttk.Frame(frm)
    btns.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10,0))
    ttk.Button(btns, text="Start", command=do_start).grid(row=0, column=0, padx=(0,8))
    ttk.Button(btns, text="Open Browser", command=do_open).grid(row=0, column=1, padx=(0,8))
    ttk.Button(btns, text="Stop Services", command=do_stop_services).grid(row=0, column=2, padx=(0,8))
    ttk.Button(btns, text="Quit", command=do_quit).grid(row=0, column=3)
    do_start()
    root.mainloop()

if __name__ == "__main__":
    main()
