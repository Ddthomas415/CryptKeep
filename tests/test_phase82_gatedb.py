from services.risk.live_risk_gates import LiveGateDB

def test_killswitch_roundtrip(tmp_path):
    db = str(tmp_path / "x.sqlite")
    g = LiveGateDB(exec_db=db)
    assert g.killswitch_on() is False
    g.set_killswitch(True)
    assert g.killswitch_on() is True
    g.set_killswitch(False)
    assert g.killswitch_on() is False
