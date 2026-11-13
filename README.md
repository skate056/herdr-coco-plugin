# herdr-coco-plugin

Shows Cortex Code (Snowflake's `cortex` CLI) as an agent in [Herdr](https://github.com/herdrdev/herdr):
sidebar state, notifications, `herdr agent wait`, and session resume after a Herdr restart.
It uses Cortex's hooks and Herdr's public reporting CLI, so Herdr itself is unchanged.

## Install

Needs `python3`, Herdr 0.9.2+, and Cortex Code started at least once.

```sh
python3 scripts/install.py install                  # hooks only
python3 scripts/install.py install --guard-claude   # also edits ~/.claude/settings.json
python3 scripts/install.py doctor
python3 scripts/install.py uninstall
```

Changed files are backed up to `<file>.herdr-cortex-backup` first.

## Why `--guard-claude` exists

Cortex also runs hooks from `~/.claude/settings.json`, including Herdr's Claude integration. That
claims the pane as a Claude session, and Herdr then silently drops every Cortex report from it.
The flag makes that one hook skip itself under Cortex. Without the Claude integration you don't
need it. `herdr integration install claude` adds an unguarded entry back; `doctor` detects that,
and rerunning with `--guard-claude` fixes it.

## Events

| Cortex hook | Herdr state |
| --- | --- |
| `UserPromptSubmit`, `PostToolUse` | `working` |
| `PermissionRequest`, `Notification` | `blocked` |
| `Stop` | `idle` |
| `SessionEnd` | released |

## Limitations

- A pane appears after the first prompt, because `SessionStart` doesn't fire from `hooks.json`.
- A crashed session can show its last state until the pane returns to the shell prompt.
- `herdr agent explain` and plugins needing a *detected* agent won't see it; that needs Herdr core.

See [docs/verification.md](docs/verification.md) for what has and hasn't been tested. Set
`HERDR_CORTEX_DEBUG=1` to log hook event names and payload keys to `$TMPDIR/herdr-cortex-hook.log`.

## Test

```sh
python3 -I tests/test_hooks.py
```
