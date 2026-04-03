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


def test_reconcile_ambiguous_submission_closes_built_client_after_boundary_fetch():
    client = Mock()
    built = Mock()
    client.build.return_value = built

    with patch(
        "services.execution.order_reconciliation.fetch_order_via_boundary",
        return_value={"id": "abc", "status": "open"},
    ):
        out = reconcile_ambiguous_submission(
            venue="coinbase",
            client=client,
            symbol="BTC/USD",
            client_oid=None,
            remote_order_id="abc",
            age_sec=5,
        )

    built.close.assert_called_once_with()
    assert out.outcome == "confirmed_placed"


def test_reconcile_ambiguous_submission_does_not_close_raw_client_without_build():
    client = Mock()

    with patch(
        "services.execution.order_reconciliation.fetch_order_via_boundary",
        return_value={"id": "abc", "status": "open"},
    ):
        out = reconcile_ambiguous_submission(
            venue="coinbase",
            client=client,
            symbol="BTC/USD",
            client_oid=None,
            remote_order_id="abc",
            age_sec=5,
        )

    client.close.assert_not_called()
    assert out.outcome == "confirmed_placed"
