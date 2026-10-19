"""Explicit configuration projection, never evidence of runtime attachment."""
import hashlib
import json
import re

from scripts.research import companion_runtime_adapter as adapter

ID = re.compile(r"[0-9a-f]{64}\Z")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
CONTRACT = "configured-network-v1"


def validate_bindings(bindings):
    if type(bindings) is not dict or not 1 <= len(bindings) <= 7:
        raise ValueError("network_configuration_refused")
    if any(type(k) is not str or not NAME.fullmatch(k) or type(v) is not str
           or not ID.fullmatch(v) for k, v in bindings.items()):
        raise ValueError("network_configuration_refused")
    if len(set(bindings.values())) != len(bindings):
        raise ValueError("network_configuration_refused")


def project(row, bindings):
    """Keep raw fields intact; caller verifies daemon bindings and ownership."""
    validate_bindings(bindings)
    networks = row.get("networks")
    if type(networks) is not dict:
        raise ValueError("network_configuration_refused")
    projected, evidence = {}, []
    for name, network in sorted(networks.items()):
        if name not in bindings or type(network) is not dict:
            raise ValueError("network_configuration_refused")
        observed = network.get("NetworkID")
        if type(observed) is not str or observed not in ("", bindings[name]):
            raise ValueError("network_configuration_refused")
        if observed == "" and any(network.get(k) not in (None, "", 0) for k in
                ("EndpointID", "IPAddress", "IPv6Address", "GlobalIPv6Address", "Gateway", "IPv6Gateway")):
            raise ValueError("network_configuration_refused")
        copy = dict(network)
        copy["NetworkID"] = bindings[name]
        if copy.get("IPAMConfig") == {}:
            copy["IPAMConfig"] = None
        projected[name] = copy
        evidence.append((name, bindings[name], "reported_id" if observed else "configured_only"))
    value = {"schema": CONTRACT,
             "preservation": adapter.preservation_digest({**row, "networks": projected})}
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest(), tuple(sorted(bindings[n] for n in networks)), tuple(evidence)
