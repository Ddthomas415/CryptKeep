"""One synchronous summary POST in the supervisor-owned cycle child."""

import http.client
import math
import ssl
import time

from services.alerts.group_a_slack import _HOST, _webhook_path, accepted_response
from services.alerts.group_a_summary_protocol import summary_body


def send_summary(release, observed_ms, findings, health, health_mask, *, cfg, deadline,
                 clock=time.monotonic):
    connection = None
    try:
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            return False
        remaining = deadline - clock()
        if not 0 < remaining <= 40:
            return False
        alerts = cfg.get("alerts") if type(cfg) is dict else None
        if type(alerts) is not dict or alerts.get("enabled") is not True:
            return False
        path = _webhook_path(alerts.get("slack_webhook_url"))
        if path is None:
            return False
        body = summary_body(release, observed_ms, findings, health, health_mask)
        connection = http.client.HTTPSConnection(
            _HOST, timeout=min(5, remaining), context=ssl.create_default_context(),
        )
        connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        if deadline <= clock():
            return False
        with connection.getresponse() as response:
            accepted = accepted_response(response)
        return accepted and clock() <= deadline
    except Exception:
        # Raw transport failures may contain the webhook path.
        return False
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
