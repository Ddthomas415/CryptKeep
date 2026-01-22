# Paste your original webhook_server.py code here

def run():
    cfg = _cfg()
    try:
        _bind_guard(cfg)
    except RuntimeError as e:
        print(f"Bind error: {e}")
        return
    host = cfg["host"]
    port = int(cfg["port"])
    httpd = HTTPServer((host, port), Handler)
    print(f"[evidence_webhook] listening on http://{host}:{port}/evidence (hmac_required={cfg['require_hmac']})")
    httpd.serve_forever()