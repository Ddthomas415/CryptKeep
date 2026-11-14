"""Offline Group B producer. No exchange calls, scheduling, or execution authority."""
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import tempfile

from services.market_data.group_b_selection import (
    FROZEN, MAX_BYTES, POLICY, assign_slots, digest, instant, producer_identity, validate_inputs,
    validate_selection, week_at, weekly_name,
)
from services.signals.market_ranker import rank_market


def build_selection(*, inputs, rank_at, generated_at, previous=None):
    if instant(rank_at) != week_at(rank_at) or instant(generated_at) < instant(rank_at):
        raise ValueError("monday_0005_required")
    root = Path(__file__).resolve().parents[2]
    for name, expected in FROZEN.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError("frozen_source_changed")
    previous_slots = [None, None, None]
    previous_hash = None
    if previous is not None:
        validate_selection(previous, now=previous["generated_at"])
        if instant(previous["rank_at"]) >= instant(rank_at):
            raise ValueError("previous_week_required")
        previous_slots = previous["slots"]
        previous_hash = previous["sha256"]
    ranked = rank_market(symbols_data=validate_inputs(inputs, rank_at))
    picks = [x["symbol"] for x in ranked if x["composite_score"] >= 38][:3]
    body = {"policy": POLICY, "venue": "coinbase", "rank_at": rank_at,
            "generated_at": generated_at,
            "valid_until": (instant(rank_at) + timedelta(days=7)).isoformat(),
            "code": dict(FROZEN), "producer_code": producer_identity(), "inputs": inputs, "ranked": ranked,
            "previous_slots": previous_slots, "previous_sha256": previous_hash,
            "slots": assign_slots(picks, previous_slots)}
    artifact = {**body, "sha256": digest(body)}
    return validate_selection(artifact, now=generated_at)


def publish_selection(artifact, directory):
    """One immutable dated file per week; readers never see a partial write."""
    validate_selection(artifact, now=artifact["generated_at"])
    directory = Path(directory)
    if not directory.is_absolute() or not directory.is_dir():
        raise ValueError("existing_absolute_directory_required")
    raw = json.dumps(artifact, sort_keys=True, allow_nan=False).encode()
    if len(raw) > MAX_BYTES:
        raise ValueError("selection_too_large")
    destination = directory / weekly_name(artifact["rank_at"])
    fd, temporary = tempfile.mkstemp(prefix=".group_b_", dir=directory)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)  # fails if a prior publication exists
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        os.unlink(temporary)
    return destination
