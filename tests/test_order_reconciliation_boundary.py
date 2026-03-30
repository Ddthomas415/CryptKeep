from unittest.mock import Mock, patch

from services.execution.order_reconciliation import reconcile_ambiguous_submission


def test_reconcile_ambiguous_submission_uses_boundary_for_remote_order_id():
    client = Mock()
    client.build.return_value = Mock()

    with patch(
        "services.execution.order_reconciliation.fetch_order_via_boundary",
        return_value={"id": "abc", "status": "open"},
    ) as fetch_mock:
        out = reconcile_ambiguous_submission(
            venue="coinbase",
            client=client,
            symbol="BTC/USD",
            client_oid=None,
            remote_order_id="abc",
            age_sec=5,
        )

    client.build.assert_called_once()
    fetch_mock.assert_called_once_with(
        client.build.return_value,
        venue="coinbase",
        symbol="BTC/USD",
        order_id="abc",
        source="order_reconciliation.remote_order_id",
    )
    assert out.outcome == "confirmed_placed"
    assert out.details == {"source": "remote_order_id"}
