from dashboard.components import actions

def test_system_actions_are_disabled() -> None:
    assert actions.PRIMARY_ACTIONS == ()
    assert actions.SECONDARY_ACTIONS == ()
