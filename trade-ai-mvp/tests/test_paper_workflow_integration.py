from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi import HTTPException

from services.gateway.routes import paper as paper_routes
from services.gateway.routes import query as query_routes
from shared.schemas.paper import PaperOrderCreateRequest
from shared.schemas.trade import TradeProposalRequest


async def _noop_audit(*args, **kwargs):
    _ = (args, kwargs)
    return None


@dataclass
class _FakeExecutionSim:
    price: float = 145.0
    fill_fee: float = 0.12
    fail_fills_once: bool = False
    order_by_client_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    order_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    fills_store: list[dict[str, Any]] = field(default_factory=list)
    cash: float = 100000.0
    qty: float = 0.0

    async def call(
        self,
        *,
        method: str,
        path: str,
        json_payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retries: int = 2,
    ) -> dict[str, Any]:
        _ = (params, retries)
        if method == "POST" and path == "/paper/orders":
            payload = json_payload or {}
            client_id = str(payload.get("client_order_id") or "paper-default")
            existing = self.order_by_client_id.get(client_id)
            if existing:
                return existing

            side = str(payload.get("side") or "buy")
            qty = float(payload.get("quantity") or 0.0)
            order_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, client_id))
            metadata = dict(payload.get("metadata") or {})
            order = {
                "id": order_id,
                "client_order_id": client_id,
                "symbol": str(payload.get("symbol") or "SOL-USD"),
                "side": side,
                "order_type": str(payload.get("order_type") or "market"),
                "status": "filled",
                "quantity": qty,
                "limit_price": None,
                "filled_quantity": qty,
                "average_fill_price": self.price,
                "risk_gate": "ALLOW",
                "signal_source": payload.get("signal_source"),
                "rationale": payload.get("rationale"),
                "catalyst_tags": list(payload.get("catalyst_tags") or []),
                "execution_disabled": True,
                "paper_mode": True,
                "created_at": "2026-03-11T02:00:00Z",
                "updated_at": "2026-03-11T02:00:00Z",
                "canceled_at": None,
                "metadata": metadata,
            }
            self.order_by_client_id[client_id] = order
            self.order_by_id[order_id] = order

            fill = {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{client_id}-fill")),
                "order_id": order_id,
                "symbol": order["symbol"],
                "side": side,
                "price": self.price,
                "quantity": qty,
                "fee": self.fill_fee,
                "liquidity": "taker",
                "created_at": "2026-03-11T02:00:01Z",
            }
            self.fills_store.append(fill)
            notional = qty * self.price
            if side == "buy":
                self.cash -= notional + self.fill_fee
                self.qty += qty
            else:
                self.cash += notional - self.fill_fee
                self.qty -= qty
            return order

        if method == "GET" and path.startswith("/paper/orders/"):
            order_id = path.split("/paper/orders/", 1)[1]
            if order_id not in self.order_by_id:
                raise RuntimeError("order_not_found")
            return self.order_by_id[order_id]

        if method == "GET" and path == "/paper/fills":
            if self.fail_fills_once:
                self.fail_fills_once = False
                raise RuntimeError("fills_temporarily_unavailable")
            return {"fills": list(self.fills_store), "next_cursor": None, "has_more": False}

        if method == "GET" and path == "/paper/summary":
            gross = abs(self.qty * self.price)
            equity = self.cash + gross
            return {
                "as_of": "2026-03-11T02:01:00Z",
                "cash": self.cash,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "equity": equity,
                "gross_exposure_usd": gross,
                "positions": (
                    [
                        {
                            "symbol": "SOL-USD",
                            "quantity": self.qty,
                            "avg_entry_price": self.price,
                            "mark_price": self.price,
                            "notional_usd": self.qty * self.price,
                            "unrealized_pnl": 0.0,
                        }
                    ]
                    if self.qty > 0
                    else []
                ),
            }

        raise AssertionError(f"unexpected execution_sim call: {method} {path}")


def _build_trade_proposal() -> dict[str, Any]:
    return {
        "asset": "SOL",
        "question": "Should we open a SOL paper position now?",
        "side": "buy",
        "order_type": "market",
        "suggested_quantity": 1.0,
        "estimated_price": 145.0,
        "estimated_notional_usd": 145.0,
        "rationale": "Momentum setup with risk gate green.",
        "confidence": 0.81,
        "risk": {"gate": "ALLOW", "paper_approved": True},
        "execution_disabled": True,
        "requires_user_approval": True,
        "paper_submit_path": "/paper/orders",
    }


def test_integration_proposal_to_fill_to_pnl(monkeypatch):
    fake_exec = _FakeExecutionSim()

    async def _fake_propose(payload):
        _ = payload
        return _build_trade_proposal()

    monkeypatch.setattr(query_routes, "_call_orchestrator_propose", _fake_propose)
    monkeypatch.setattr(query_routes, "emit_audit_event", _noop_audit)
    monkeypatch.setattr(paper_routes, "_call_execution_sim", fake_exec.call)
    monkeypatch.setattr(paper_routes, "emit_audit_event", _noop_audit)
    monkeypatch.setattr(paper_routes.settings, "paper_order_require_approval", True)

    proposal = asyncio.run(
        query_routes.propose_trade(
            TradeProposalRequest(asset="SOL", question="Should we open a SOL paper position now?")
        )
    )
    assert proposal.side == "buy"
    assert proposal.requires_user_approval is True

    order = asyncio.run(
        paper_routes.submit_order(
            PaperOrderCreateRequest(
                symbol="SOL-USD",
                side="buy",
                order_type="market",
                quantity=proposal.suggested_quantity,
                client_order_id="integration-001",
                signal_source="proposal_flow",
                rationale=proposal.rationale,
                catalyst_tags=["governance"],
                metadata={"user_approved": True},
            )
        )
    )
    assert order.status == "filled"
    assert order.signal_source == "proposal_flow"

    fills = asyncio.run(
        paper_routes.fills(symbol="SOL-USD", order_id=None, since=None, cursor=None, limit=10, sort="desc")
    )
    assert len(fills.fills) == 1
    assert fills.fills[0].order_id == order.id

    summary = asyncio.run(paper_routes.summary())
    assert summary.gross_exposure_usd > 0
    assert summary.cash < 100000.0
    assert summary.equity > 0


def test_integration_degraded_dependency_preserves_paper_state(monkeypatch):
    fake_exec = _FakeExecutionSim(fail_fills_once=True)
    monkeypatch.setattr(paper_routes, "_call_execution_sim", fake_exec.call)
    monkeypatch.setattr(paper_routes, "emit_audit_event", _noop_audit)
    monkeypatch.setattr(paper_routes.settings, "paper_order_require_approval", False)

    order = asyncio.run(
        paper_routes.submit_order(
            PaperOrderCreateRequest(
                symbol="SOL-USD",
                side="buy",
                order_type="market",
                quantity=1.0,
                client_order_id="degraded-001",
            )
        )
    )
    assert order.status == "filled"

    with pytest.raises(HTTPException) as err:
        asyncio.run(
            paper_routes.fills(symbol="SOL-USD", order_id=None, since=None, cursor=None, limit=10, sort="desc")
        )
    assert err.value.status_code == 503

    fetched = asyncio.run(paper_routes.get_order(order.id))
    assert fetched.status == "filled"
    assert fetched.client_order_id == "degraded-001"


def test_determinism_replay_same_inputs_same_fills(monkeypatch):
    async def _run_replay() -> tuple[float, float, str]:
        fake_exec = _FakeExecutionSim()
        monkeypatch.setattr(paper_routes, "_call_execution_sim", fake_exec.call)
        monkeypatch.setattr(paper_routes, "emit_audit_event", _noop_audit)
        monkeypatch.setattr(paper_routes.settings, "paper_order_require_approval", False)

        _ = await paper_routes.submit_order(
            PaperOrderCreateRequest(
                symbol="SOL-USD",
                side="buy",
                order_type="market",
                quantity=1.0,
                client_order_id="determinism-001",
            )
        )
        fills = await paper_routes.fills(
            symbol="SOL-USD",
            order_id=None,
            since=None,
            cursor=None,
            limit=10,
            sort="desc",
        )
        first = fills.fills[0]
        return first.price, first.fee, first.order_id

    p1, fee1, oid1 = asyncio.run(_run_replay())
    p2, fee2, oid2 = asyncio.run(_run_replay())
    assert p1 == p2
    assert fee1 == fee2
    assert oid1 == oid2
