# Verification status (2026-11-05, Herdr 0.9.5)

## Tested against the real Herdr binary, on an isolated server

- working → blocked → working → done → released, under an unknown agent label.
- Herdr's installed Claude hook (v11), given a simulated Cortex `SessionStart`, makes the pane
  ignore all later reports. Neither source's release clears it.
- With the guard, the same sequence works, and a non-Cortex run still claims normally.
- After a server restart Herdr ran `cortex --resume sess-42` (fake `cortex` on `PATH`).

## Not tested: no real Cortex Code has run these hooks

Cortex was not installed. Taken from Snowflake's docs and reports in herdr discussion #783:

- `hooks.json` shape and these events firing on current Cortex.
- `session_id` present on every event; documented only for `PreToolUse` on the CLI.
- `CORTEX_PROJECT_DIR` / `CORTEX_CODE_CLIENT_SURFACE` being set during `SessionStart`, which the
  guard depends on. Reported for 1.1.104.
- Payload shapes for `Notification` and `SessionEnd`, which are undocumented.

## Known risk

`Notification` maps to `blocked` because ask-user dialogs fire only that (reported on 1.1.27). If
Cortex sends other notifications, an idle pane will wrongly show blocked. Check with
`HERDR_CORTEX_DEBUG=1`.
