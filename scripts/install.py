#!/usr/bin/env python3
"""Install, remove, or check the Herdr hooks for Cortex Code.

  install.py install [--guard-claude]
  install.py uninstall
  install.py doctor

Honours SNOWFLAKE_HOME and CLAUDE_CONFIG_DIR. Existing files are backed up to
<file>.herdr-cortex-backup before the first change.
"""
import json
import os
import shlex
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "herdr_report.py"
# SessionStart is absent on purpose: Cortex runs it before loading hooks.json.
EVENTS = {
    "UserPromptSubmit": ("working", None),
    "PostToolUse": ("working", "*"),
    "PermissionRequest": ("blocked", "*"),
    "Notification": ("blocked", None),
    "Stop": ("idle", None),
    "SessionEnd": ("release", None),
}
# CORTEX_PROJECT_DIR is documented; CORTEX_CODE_CLIENT_SURFACE was observed during
# SessionStart. If both vanish the guard fails open, leaving Claude Code unharmed.
GUARD = '[ -n "${CORTEX_PROJECT_DIR:-}${CORTEX_CODE_CLIENT_SURFACE:-}" ] || '
CLAUDE_HOOK = "herdr-agent-state.sh"


def cortex_dir():
    return Path(os.environ.get("SNOWFLAKE_HOME", Path.home() / ".snowflake")) / "cortex"


def claude_settings():
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base) if base else Path.home() / ".claude") / "settings.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save(path, data):
    backup = path.with_name(path.name + ".herdr-cortex-backup")
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    if path.exists():
        shutil.copymode(path, tmp)
    os.replace(tmp, path)


def is_ours(group):
    return any(MARKER in str(h.get("command", "")) for h in group.get("hooks", []))


def strip_ours(config):
    hooks = config.get("hooks", {})
    for event in list(hooks):
        hooks[event] = [group for group in hooks[event] if not is_ours(group)]
        if not hooks[event]:
            del hooks[event]
    return config


def claude_commands(settings):
    """Yield every hook dict that runs Herdr's Claude integration."""
    for group in settings.get("hooks", {}).get("SessionStart", []):
        for hook in group.get("hooks", []):
            if CLAUDE_HOOK in str(hook.get("command", "")):
                yield hook


def guard_claude():
    path = claude_settings()
    settings = load(path)
    changed = False
    for hook in claude_commands(settings):
        if GUARD not in hook["command"]:
            hook["command"] = GUARD + hook["command"]
            changed = True
    if changed:
        save(path, settings)
    return changed


def install(argv):
    base = cortex_dir()
    if not base.is_dir():
        sys.exit(f"{base} does not exist: install and start Cortex Code first")
    target = base / "herdr-cortex" / MARKER
    target.parent.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "src" / MARKER, target)

    path = base / "hooks.json"
    config = strip_ours(load(path))
    hooks = config.setdefault("hooks", {})
    for event, (state, matcher) in EVENTS.items():
        command = f"python3 -I {shlex.quote(str(target))} {state}"
        group = {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
        if matcher:
            group["matcher"] = matcher
        hooks.setdefault(event, []).append(group)
    save(path, config)
    print(f"installed hooks in {path}")
    if "--guard-claude" in argv and guard_claude():
        print(f"guarded Herdr's Claude hook in {claude_settings()}")
    return doctor()


def uninstall():
    base = cortex_dir()
    path = base / "hooks.json"
    if path.exists():
        save(path, strip_ours(load(path)))
    shutil.rmtree(base / "herdr-cortex", ignore_errors=True)
    path = claude_settings()
    settings = load(path)
    changed = False
    for hook in claude_commands(settings):
        if GUARD in hook["command"]:
            hook["command"] = hook["command"].replace(GUARD, "")
            changed = True
    if changed:
        save(path, settings)
    print("uninstalled")
    return 0


def doctor():
    config = load(cortex_dir() / "hooks.json")
    missing = [e for e in EVENTS if not any(is_ours(g) for g in config.get("hooks", {}).get(e, []))]
    exposed = [h for h in claude_commands(load(claude_settings())) if GUARD not in h["command"]]
    print("hooks: " + (f"MISSING {', '.join(missing)}" if missing else "ok"))
    if exposed:
        print("claude hook: UNGUARDED. Cortex runs it too, so Herdr will ignore every")
        print("  report from that pane. Fix with: install.py install --guard-claude")
    else:
        print("claude hook: ok")
    return 1 if missing or exposed else 0


def main():
    argv = sys.argv[1:]
    action = argv[0] if argv else ""
    if action == "install":
        return install(argv)
    if action == "uninstall":
        return uninstall()
    if action == "doctor":
        return doctor()
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
