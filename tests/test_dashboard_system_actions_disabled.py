from dashboard.components import actions

def test_system_actions_expose_explicit_runtime_halt() -> None:
    assert actions.PRIMARY_ACTIONS == ()
    assert actions.SECONDARY_ACTIONS == (("Halt Runtime", ["stop-everything"]),)
