from services.logging.app_logger import _redact_text

def test_redact_text_masks_sensitive_pairs() -> None:
    text = "Authorization: Bearer abc123 token=xyz password=hunter2 secret=s3 api_key=k1 cookie=c1 session=s1 jwt=j1"
    out = _redact_text(text)
    assert "abc123" not in out
    assert "xyz" not in out
    assert "hunter2" not in out
    assert "s3" not in out
    assert "k1" not in out
    assert "c1" not in out
    assert "s1" not in out
    assert "j1" not in out
    assert "***REDACTED***" in out
