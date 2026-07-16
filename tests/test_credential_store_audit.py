from __future__ import annotations

import importlib
import json


class FakeKeyring:
    def __init__(self) -> None:
        self.store: dict[tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        self.store[(service, username)] = password

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def delete_password(self, service: str, username: str) -> None:
        key = (service, username)
        if key not in self.store:
            raise RuntimeError("not_found")
        del self.store[key]


def _fresh_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.audit.operator_event_journal as journal
    import services.audit.operator_event_secret_scan as secret_scan
    import services.security.credential_store as store

    importlib.reload(store)
    return store, journal, secret_scan


def test_set_exchange_credentials_appends_metadata_only_operator_event(monkeypatch, tmp_path):
    store, journal, secret_scan = _fresh_modules(monkeypatch, tmp_path)
    fake = FakeKeyring()
    monkeypatch.setattr(store, "_require_keyring", lambda: fake)

    result = store.set_exchange_credentials(
        " Coinbase ",
        api_key="APIKEY-DO-NOT-LOG",
        api_secret="SECRET-DO-NOT-LOG",
        passphrase="PASSPHRASE-DO-NOT-LOG",
    )

    assert result["ok"] is True
    assert result["exchange"] == "coinbase"
    assert result["fields"] == ["apiKey", "passphrase", "secret"]
    assert result["operator_event"]["ok"] is True

    events = journal.load_operator_events()
    assert len(events) == 1
    event = events[0]
    assert event["action"] == "api_credential_rotation"
    assert event["target"] == "exchange:coinbase"
    assert event["reason"] == "set_exchange_credentials"
    assert event["pre_state"] == {"stored": {"present": False, "field_names": [], "parse_ok": True}}
    assert event["post_state"]["stored"]["field_names"] == ["apiKey", "passphrase", "secret"]

    raw_event_text = journal.operator_event_journal_path().read_text(encoding="utf-8")
    assert "APIKEY-DO-NOT-LOG" not in raw_event_text
    assert "SECRET-DO-NOT-LOG" not in raw_event_text
    assert "PASSPHRASE-DO-NOT-LOG" not in raw_event_text
    assert secret_scan.scan_operator_event_journal(require_events=True)["ok"] is True


def test_delete_exchange_credentials_appends_rotation_event_with_pre_state(monkeypatch, tmp_path):
    store, journal, _secret_scan = _fresh_modules(monkeypatch, tmp_path)
    fake = FakeKeyring()
    monkeypatch.setattr(store, "_require_keyring", lambda: fake)

    store.set_exchange_credentials("coinbase", "old-api-key", "old-secret")
    result = store.delete_exchange_credentials("COINBASE")

    assert result["ok"] is True
    assert result["deleted"] is True
    assert result["operator_event"]["ok"] is True

    events = journal.load_operator_events()
    assert [event["reason"] for event in events] == [
        "set_exchange_credentials",
        "delete_exchange_credentials:deleted",
    ]
    delete_event = events[-1]
    assert delete_event["pre_state"]["stored"]["present"] is True
    assert delete_event["pre_state"]["stored"]["field_names"] == ["apiKey", "secret"]
    assert delete_event["post_state"] == {"stored": {"present": False, "field_names": [], "parse_ok": True}}
    assert "old-api-key" not in json.dumps(delete_event)
    assert "old-secret" not in json.dumps(delete_event)


def test_credential_rotation_journal_failure_is_best_effort(monkeypatch, tmp_path):
    store, _journal, _secret_scan = _fresh_modules(monkeypatch, tmp_path)
    fake = FakeKeyring()
    monkeypatch.setattr(store, "_require_keyring", lambda: fake)

    def _raise_operator_event(**_kwargs):
        raise PermissionError("audit path read-only")

    monkeypatch.setattr(store, "append_operator_event", _raise_operator_event)

    result = store.set_exchange_credentials("coinbase", "api-key", "api-secret")

    assert result["ok"] is True
    assert result["operator_event"] == {"ok": False, "reason": "operator_event_write_failed:PermissionError"}
    stored = json.loads(fake.store[(store.SERVICE_NAME, "coinbase")])
    assert stored == {"apiKey": "api-key", "secret": "api-secret"}
