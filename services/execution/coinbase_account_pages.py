"""Unwired Coinbase page reader; uses a caller-owned client, creates no authority."""

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import json
import math
import inspect


class Incomplete(ValueError):
    pass


def amount(value):
    if type(value) not in (str, int):
        raise Incomplete("invalid_amount")
    try:
        d = Decimal(value)
        if not d.is_finite() or d < 0:
            raise Incomplete("invalid_amount")
        return Fraction(d)
    except (InvalidOperation, ValueError, OverflowError):
        raise Incomplete("invalid_amount") from None


def text(value):
    if type(value) is not str or not value.strip():
        raise Incomplete("identity_required")
    return value


class Pager:
    def __init__(self, *, version, scope, page_size, max_pages, max_rows,
                 max_json_bytes, deadline, clock):
        if version not in ("v2", "v3"):
            raise ValueError("explicit_version_required")
        if (type(scope) not in (tuple, list) or len(scope) != 2
                or any(type(x) is not str or not x.strip() for x in scope)):
            raise ValueError("explicit_venue_account_scope_required")
        for bound in (page_size, max_pages, max_rows, max_json_bytes):
            if type(bound) is not int or bound <= 0:
                raise ValueError("positive_integer_bounds_required")
        if page_size > 250 or type(deadline) not in (int, float) or not math.isfinite(deadline):
            raise ValueError("invalid_page_or_deadline_bound")
        self.version, self.scope = version, list(scope)
        self.page_size, self.max_pages, self.max_rows = page_size, max_pages, max_rows
        self.max_json_bytes, self.deadline, self.clock = max_json_bytes, deadline, clock
        self.cursor, self.seen_cursors = None, set()
        self.raw_pages, self.rows, self.calls, self.json_bytes = [], {}, 0, 0
        self.finished, self.last_body = False, None
        self.last_clock = None

    def timely(self):
        try:
            now = self.clock()
        except Exception:
            raise Incomplete("clock_failure") from None
        if (type(now) not in (int, float) or not math.isfinite(now) or now >= self.deadline
                or (self.last_clock is not None and now < self.last_clock)):
            raise Incomplete("deadline_or_clock")
        self.last_clock = now

    def request(self):
        self.timely()
        if self.calls >= self.max_pages:
            raise Incomplete("page_budget")
        params = {"limit": self.page_size}
        if self.cursor is not None:
            params["starting_after" if self.version == "v2" else "cursor"] = self.cursor
        self.calls += 1
        return params

    def accept(self, page):
        encoded = json.dumps(page, sort_keys=True, allow_nan=False).encode()
        if self.json_bytes + len(encoded) > self.max_json_bytes:
            raise Incomplete("json_byte_budget")
        self.raw_pages.append(deepcopy(page))
        self.json_bytes += len(encoded)
        self.timely()
        if not isinstance(page, dict) or page.get("scope") != self.scope:
            raise Incomplete("scope_mismatch")
        body = page["body"]
        if not isinstance(body, dict):
            raise Incomplete("invalid_page")
        if body.get("errors") or body.get("error"):
            raise Incomplete("provider_error")
        if self.version == "v2":
            rows, pagination = body["data"], body["pagination"]
            if not isinstance(pagination, dict) or "next_starting_after" not in pagination:
                raise Incomplete("continuation_unknown")
            cursor = pagination["next_starting_after"]
            more = cursor not in (None, "")
            if not more and pagination.get("next_uri"):
                raise Incomplete("continuation_inconsistent")
            if "starting_after" in pagination and pagination["starting_after"] != self.cursor:
                raise Incomplete("cursor_response_mismatch")
        else:
            rows, more, cursor = body["accounts"], body["has_next"], body["cursor"]
            if type(more) is not bool:
                raise Incomplete("continuation_unknown")
        if cursor is not None and type(cursor) is not str:
            raise Incomplete("invalid_cursor")
        if more and (not cursor or cursor in self.seen_cursors):
            raise Incomplete("repeated_or_missing_cursor")
        if not isinstance(rows, list) or (more and not rows):
            raise Incomplete("invalid_page_rows")
        for row in rows:
            identity, *_ = self.account(row)
            if identity in self.rows and self.rows[identity] != row:
                raise Incomplete("conflicting_account")
            self.rows[identity] = deepcopy(row)
            if len(self.rows) > self.max_rows:
                raise Incomplete("row_budget")
        if more:
            self.seen_cursors.add(cursor)
        self.cursor, self.finished, self.last_body = cursor, not more, deepcopy(body)

    def account(self, row):
        if not isinstance(row, dict):
            raise Incomplete("invalid_account")
        if self.version == "v2":
            identity, currency = text(row["id"]), text(row["currency"]["code"])
            if row["balance"]["currency"] != currency:
                raise Incomplete("currency_mismatch")
            return identity, currency, amount(row["balance"]["amount"]), None, None
        identity, currency = text(row["uuid"]), text(row["currency"])
        available, hold = row["available_balance"], row["hold"]
        if available["currency"] != currency or hold["currency"] != currency:
            raise Incomplete("currency_mismatch")
        free, used = amount(available["value"]), amount(hold["value"])
        return identity, currency, free + used, free, used

    def result(self, reason=None):
        view = None
        if reason is None and self.finished:
            totals, available, used = {}, {}, {}
            for row in self.rows.values():
                _, currency, total, free, locked = self.account(row)
                totals[currency] = totals.get(currency, Fraction(0)) + total
                if free is not None:
                    available[currency] = available.get(currency, Fraction(0)) + free
                    used[currency] = used.get(currency, Fraction(0)) + locked
            pack = lambda rows: {k: [v.numerator, v.denominator] for k, v in rows.items()}
            info = deepcopy(self.last_body)
            info["data" if self.version == "v2" else "accounts"] = list(self.rows.values())
            view = {"info": info, "total": pack(totals),
                    "available": pack(available) if self.version == "v3" else None,
                    "used": pack(used) if self.version == "v3" else None}
        return {"status": "COMPLETE" if view is not None else "INCOMPLETE",
                "reason": reason, "version": self.version, "scope": self.scope,
                "view": view, "raw_pages": deepcopy(self.raw_pages),
                "page_callbacks_attempted": self.calls, "retained_json_bytes": self.json_bytes,
                "qualification": "SYNTHETIC_PAGES_NOT_CCXT_BALANCE_OR_ACCOUNT_PROOF",
                "scope_authenticated": False, "spendable_verified": False,
                "legacy_info_data_shape": self.version == "v2",
                "execution_authority": False}


def collect_sync(fetch_page, **options):
    pager = Pager(**options)
    try:
        while not pager.finished:
            params = pager.request()
            try:
                page = fetch_page(params)
            except Exception:
                return pager.result("page_callback_failure")
            pager.accept(page)
        return pager.result()
    except Exception as error:
        return pager.result(str(error) if isinstance(error, Incomplete) else "page_or_schema_failure")


async def collect_async(fetch_page, **options):
    pager = Pager(**options)
    try:
        while not pager.finished:
            params = pager.request()
            try:
                page = await fetch_page(params)
            except Exception:
                return pager.result("page_callback_failure")
            pager.accept(page)
        return pager.result()
    except Exception as error:
        return pager.result(str(error) if isinstance(error, Incomplete) else "page_or_schema_failure")


def _client_method(client, options):
    # Validate all bounds before obtaining any method from the supplied client.
    validated = Pager(**options)
    if (getattr(client, "id", None) != "coinbase"
            or validated.scope[0] != "coinbase"):
        raise ValueError("explicit_coinbase_client_and_scope_required")
    name = "v2PrivateGetAccounts" if validated.version == "v2" else "v3PrivateGetBrokerageAccounts"
    method = getattr(client, name, None)
    if not callable(method):
        raise ValueError("configured_account_method_unavailable")
    return name, method


def _sdk_result(result, name):
    result["qualification"] = "SUPPLIED_SDK_PAGES_NOT_AUTHENTICATED_SCOPE_OR_CCXT_BALANCE"
    result["endpoint_method"] = name
    return result


def read_account_pages_sync(client, **options):
    name, method = _client_method(client, options)
    if inspect.iscoroutinefunction(method):
        raise ValueError("async_client_requires_async_reader")
    def fetch(params):
        body = method(dict(params))
        if inspect.isawaitable(body):
            if inspect.iscoroutine(body):
                body.close()
            raise Incomplete("async_result_in_sync_reader")
        return {"scope": list(options["scope"]), "body": body}
    return _sdk_result(collect_sync(fetch, **options), name)


async def read_account_pages_async(client, **options):
    name, method = _client_method(client, options)
    async def fetch(params):
        body = method(dict(params))
        if inspect.isawaitable(body):
            body = await body
        return {"scope": list(options["scope"]), "body": body}
    return _sdk_result(await collect_async(fetch, **options), name)
