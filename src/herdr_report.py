#!/usr/bin/env python3
"""Cortex Code hook: report agent state to Herdr.

Usage: herdr_report.py <working|idle|blocked|release>

A hook must never disturb Cortex, so this always exits 0, prints nothing, and
does nothing outside a Herdr pane.
"""
import json
import os
import re
import subprocess
import sys
import time

SOURCE = "cortex-herdr"  # the herdr: prefix is reserved for Herdr's own integrations
AGENT = "cortex"
STATES = ("working", "idle", "blocked", "release")
TIMEOUT_SECONDS = 2
# Herdr rejects resume commands with apostrophes or control characters, and the
# id is passed as a CLI value, so accept only an unremarkable token.
SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def read_payload():
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def debug_log(state, payload):
    """Record event names and keys only: payload values can hold prompts and SQL."""
    if os.environ.get("HERDR_CORTEX_DEBUG") != "1":
        return
    path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "herdr-cortex-hook.log")
    with open(path, "a", encoding="utf-8") as log:
        event = payload.get("hook_event_name")
        log.write(f"{state} event={event} keys={sorted(payload)}\n")


def build_command(state, payload, seq):
    herdr = os.environ["HERDR_BIN_PATH"]
    pane = os.environ["HERDR_PANE_ID"]
    identity = ["--source", SOURCE, "--agent", AGENT, "--seq", str(seq)]
    if state == "release":
        return [herdr, "pane", "release-agent", pane, *identity]

    command = [herdr, "pane", "report-agent", pane, *identity, "--state", state]
    if state == "blocked":
        command += ["--message", "Permission required"]
    session_id = payload.get("session_id")
    if isinstance(session_id, str) and SESSION_ID.match(session_id):
        command += ["--agent-session-id", session_id, "--", "cortex", "--resume", session_id]
    return command


def main():
    # Taken first, so a slow start cannot reorder this against a later event.
    seq = time.time_ns()
    state = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = read_payload()
    debug_log(state, payload)
    if state not in STATES or os.environ.get("HERDR_ENV") != "1":
        return
    if not os.environ.get("HERDR_PANE_ID") or not os.environ.get("HERDR_BIN_PATH"):
        return
    if payload.get("agent_id"):  # subagents must not drive the pane's state
        return
    subprocess.run(
        build_command(state, payload, seq),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - reporting is best effort by design
        pass
    sys.exit(0)
