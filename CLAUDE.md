# herdr-coco-plugin

Cortex Code hooks that report state to Herdr through its public CLI.

- `src/herdr_report.py`: the hook. Must always exit 0 and print nothing, or it can disturb Cortex.
- `scripts/install.py`: install, uninstall, doctor.
- `docs/verification.md`: what has been tested, on what. Keep it accurate.

Rules:
- Standard library only; no third-party Python packages.
- Don't use the `herdr:` source prefix; Herdr reserves it for its own integrations.
- Inside a Herdr pane the `HERDR_*` variables point at the live server. Test against an isolated
  server (`herdr server` with its own `XDG_CONFIG_HOME` and `HERDR_SOCKET_PATH`), and stop it by
  a PID confirmed from its environment, never with `herdr server stop`.
- Upstream Herdr closes PRs from unapproved accounts. Native support requests belong in its
  Discussions (#783, #5636), not PRs.
- Test with `python3 -I tests/test_hooks.py`.
