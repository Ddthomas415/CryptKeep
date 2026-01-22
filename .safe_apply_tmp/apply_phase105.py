# apply_phase105.py - Phase 105 launcher (windowed desktop supervisor + frozen config paths)
from pathlib import Path
import re

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Patch config_editor to use frozen-safe writable config directory
def patch_config_editor(t: str) -> str:
    if "from services.os.app_paths import config_dir, ensure_dirs" not in t:
        if "from pathlib import Path" in t:
            t = t.replace("from pathlib import Path\n", "from pathlib import Path\nfrom services.os.app_paths import config_dir, ensure_dirs\n", 1)
        else:
            t = "from services.os.app_paths import config_dir, ensure_dirs\n" + t
    t = t.replace('Path("runtime") / "config" / "user.yaml"', 'config_dir() / "user.yaml"')
    t = t.replace("Path('runtime') / 'config' / 'user.yaml'", "config_dir() / 'user.yaml'")
    t = t.replace('Path("runtime") / "config"', "config_dir()")
    t = t.replace("Path('runtime') / 'config'", "config_dir()")
    t = t.replace('"runtime/config/user.yaml"', 'str(config_dir() / "user.yaml")')
    t = t.replace("'runtime/config/user.yaml'", 'str(config_dir() / "user.yaml")')
    def inject_ensure(func_name: str, txt: str) -> str:
        m = re.search(rf"def {func_name}\s*\(.*?\):\n", txt)
        if not m:
            return txt
        start = m.end()
        snippet = txt[start:start+200]
        if "ensure_dirs()" in snippet:
            return txt
        return txt[:start] + "    ensure_dirs()\n" + txt[start:]
    t = inject_ensure("load_user_yaml", t)
    t = inject_ensure("save_user_yaml", t)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 2) Desktop GUI supervisor (Tkinter main thread, Streamlit + helpers in background threads)
write("desktop_launcher_gui.py", r'''from __future__ import annotations
import os
import threading
import time
import webbrowser
from services.os.app_paths import code_root, ensure_dirs, state_root

def _read_env(name: str, default: str) -> str:
    v = os.getenv(name, "").strip()
    return v or default

def _open(url: str):
    try:
        webbrowser.open(url, new=1)
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

def _start_tick_publisher_if_enabled(enabled: bool):
    if not enabled:
        return
    try:
        from services.market_data.system_status_publisher import run_forever
        t = threading.Thread(target=run_forever, daemon=True)
        t.start()
    except Exception:
        pass

def _start_evidence_webhook_if_enabled(enabled: bool):
    if not enabled:
        return
    try:
        from services.evidence.webhook_server import run
        t = threading.Thread(target=run, daemon=True)
        t.start()
    except Exception:
        pass

def main():
    ensure_dirs()
    host = _read_env("CBP_HOST", "127.0.0.1")
    port = _read_env("CBP_PORT", "8501")
    url = f"http://{host}:{port}"
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        _open(url)
        _start_tick_publisher_if_enabled(True)
        _start_evidence_webhook_if_enabled(False)
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
    var_tick = tk.BooleanVar(value=True)
    var_webhook = tk.BooleanVar(value=False)
    ttk.Checkbutton(frm, text="Auto-start Tick Publisher", variable=var_tick).grid(row=3, column=0, sticky="w", pady=(8,0))
    ttk.Checkbutton(frm, text="Auto-start Evidence Webhook (local)", variable=var_webhook).grid(row=4, column=0, sticky="w")
    status = tk.StringVar(value="Ready.")
    ttk.Label(frm, textvariable=status).grid(row=5, column=0, columnspan=3, sticky="w", pady=(8,0))
    started = {"ok": False}
    def do_start():
        if started["ok"]:
            status.set("Already running.")
            return
        started["ok"] = True
        status.set("Starting…")
        _start_tick_publisher_if_enabled(bool(var_tick.get()))
        _start_evidence_webhook_if_enabled(bool(var_webhook.get()))
        th = threading.Thread(target=_start_streamlit, args=(host, port), daemon=True)
        th.start()
        def later():
            time.sleep(0.8)
            _open(url)
            status.set("Running. Use Quit to stop the app.")
        threading.Thread(target=later, daemon=True).start()
    def do_open():
        _open(url)
        status.set("Browser opened.")
    def do_quit():
        status.set("Stopping…")
        root.after(150, root.destroy)
    btns = ttk.Frame(frm)
    btns.grid(row=6, column=0, columnspan=3, sticky="w", pady=(10,0))
    ttk.Button(btns, text="Start", command=do_start).grid(row=0, column=0, padx=(0,8))
    ttk.Button(btns, text="Open Browser", command=do_open).grid(row=0, column=1, padx=(0,8))
    ttk.Button(btns, text="Quit", command=do_quit).grid(row=0, column=2)
    do_start()
    root.mainloop()

if __name__ == "__main__":
    main()
''')

# 3) Update PyInstaller spec: windowed build + optional icons
def patch_spec(t: str) -> str:
    if "desktop_launcher_gui.py" in t and "console=False" in t and "disable_windowed_traceback" in t:
        return t
    t = t.replace('Analysis(\n ["desktop_launcher.py"],', 'Analysis(\n ["desktop_launcher_gui.py"],')
    if "icon_path =" not in t:
        icon_block = r"""
import sys
from pathlib import Path
icon_path = None
assets_dir = Path("assets") / "icons"
if sys.platform.startswith("win"):
    p = assets_dir / "app.ico"
    if p.exists():
        icon_path = str(p)
elif sys.platform == "darwin":
    p = assets_dir / "app.icns"
    if p.exists():
        icon_path = str(p)
"""
        t = t.replace("from PyInstaller.utils.hooks import collect_all, copy_metadata\n", "from PyInstaller.utils.hooks import collect_all, copy_metadata\n" + icon_block + "\n", 1)
    t = t.replace(" console=True, # keep console for crash visibility; can change to False later\n", " console=False,\n")
    if "disable_windowed_traceback" not in t:
        t = t.replace(" console=False,\n", " console=False,\n disable_windowed_traceback=True,\n", 1)
    if "icon=icon_path" not in t:
        t = t.replace(" disable_windowed_traceback=True,\n", " disable_windowed_traceback=True,\n icon=icon_path,\n", 1)
    if '("assets", "assets")' not in t:
        t = t.replace('("docs", "docs"),\n ],\n', '("docs", "docs"),\n ("assets", "assets"),\n ],\n')
    return t

patch("packaging/crypto_bot_pro.spec", patch_spec)

# 4) Add assets folder (empty; user can drop icons in assets/icons/)
write("assets/.keep", "# place optional assets under assets/\n")
write("assets/icons/README.txt", r"""Optional icons for PyInstaller builds:
- Windows: assets/icons/app.ico
- macOS: assets/icons/app.icns
If these files do not exist, PyInstaller will use the default icon.
""")

# 5) Update build script help text
def patch_build_script(t: str) -> str:
    if "windowed/no-console build is controlled by the spec" in t:
        return t
    return t + "\n# Note: windowed/no-console build is controlled by packaging/crypto_bot_pro.spec\n"

patch("scripts/build_desktop.py", patch_build_script)

# 6) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DA) Double-Click Desktop Supervisor" in t:
        return t
    return t + (
        "\n## DA) Double-Click Desktop Supervisor\n"
        "- ✅ DA1: desktop_launcher_gui.py provides a small Tk supervisor (Start/Open/Quit)\n"
        "- ✅ DA2: Streamlit runs via bootstrap in a background thread; quitting stops the whole process\n"
        "- ✅ DA3: Frozen app uses user-writable state/config paths via services/os/app_paths.py + config_editor patch\n"
        "- ✅ DA4: PyInstaller spec now builds windowed (no console) and disables windowed traceback\n"
        "- ✅ DA5: Optional icons supported if assets/icons/app.ico (Win) or app.icns (macOS) are provided\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 105 applied (windowed desktop supervisor + frozen-safe config path + optional icons + checkpoints).")
print("Next steps:")
print("  1. Build the app: python3 scripts/build_desktop.py")
print("  2. Run the bundled app: dist/CryptoBotPro/CryptoBotPro")
print("  3. Optional: add icons to assets/icons/app.ico (Windows) or app.icns (macOS)")