"""Derive readable message text and an explicit gap inventory from a saved UI capture."""

import hashlib
import json
import re
from pathlib import Path


def prepare(folder):
    source = folder / "conversation_capture.json"
    capture = json.loads(source.read_text())
    messages = capture["messages"]
    numbers = [message["number"] for message in messages]
    assert numbers == list(range(1, capture["boundary_messages"] + 1))
    blocks, gaps = [], []
    for message in messages:
        lines, flags = [], []
        for line in message["ax"].splitlines():
            text = re.match(r"\s*\d+ text (.*)", line)
            link = re.match(r"\s*\d+ link (.*)", line)
            button = re.match(r"\s*\d+ button (.*)", line)
            if text:
                lines.append(text[1])
            elif link:
                lines.append("[LINK] " + link[1])
            elif button and not button[1].startswith("Show message actions"):
                lines.append("[CONTROL] " + button[1])
            if any(term in line for term in (
                "Compacted conversation", "Message collapsed", "button Show more",
                "button Pasted text", "button View ", "button Download ",
                "container (showing ",
            )):
                flags.append(line.strip())
        blocks.append(f"## Message {message['number']} of {message['total']}\n\n" + "\n".join(lines))
        if flags:
            gaps.append({"message": message["number"], "flags": flags})
    text = "\n\n".join(blocks) + "\n"
    (folder / "conversation_readable.txt").write_text(text)
    inventory = {
        "capture_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "readable_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "messages": len(messages), "missing_message_numbers": [],
        "flagged_messages": gaps,
        "note": "Controls/compaction are coverage flags, not proof of absent content. Raw message blocks are preserved.",
    }
    (folder / "coverage_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    return {"messages": len(messages), "words": len(text.split()), "characters": len(text), "flags": gaps}


if __name__ == "__main__":
    print(json.dumps(prepare(Path(__file__).resolve().parent), indent=2))
