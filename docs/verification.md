# Verification status

## End to end with real Cortex Code (2026-11-13)

Cortex Code v1.2.41, herdr 0.9.5, Linux, no Claude integration installed.

- Cortex loads all six hooks from `~/.snowflake/cortex/hooks.json` (confirmed in `coco.log`).
- First prompt shows the pane as `working`.
- An approval prompt shows `blocked`; approving goes back to `working`, then `done`.
- An ask-user question shows `blocked`.
- Left idle for a few minutes it stayed `idle`: no false `blocked` from `Notification`.
- `/exit` removes the pane from `herdr agent list`.
- Resume: after `herdr session stop` and restart, the pane reopened the same Cortex conversation.
  This also shows that Cortex sends `session_id` on the events that carry the resume command.

## Against the real Herdr binary, on an isolated server (2026-11-05, macOS, herdr 0.9.5)

- Herdr's installed Claude hook (v11), given a simulated Cortex `SessionStart`, makes the pane
  ignore all later reports. Neither source's release clears it.
- With the guard, the same sequence works, and a non-Cortex run still claims normally.

## Not yet tested

- The `--guard-claude` path with real Cortex. It needs a machine with herdr's Claude integration
  installed. The guard relies on `CORTEX_PROJECT_DIR` or `CORTEX_CODE_CLIENT_SURFACE` being set
  while Cortex runs `SessionStart`; that was reported for 1.1.104 but not checked here.
- Real Cortex on macOS.
- Hook payload shapes. The `HERDR_CORTEX_DEBUG=1` log was not captured during the run above.
