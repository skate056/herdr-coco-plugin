# herdr-coco-plugin

Cortex Code hooks that report state to Herdr through its public CLI.

- `src/herdr_report.py`: the hook. Must always exit 0 and print nothing.
- `scripts/install.py`: install, uninstall, doctor.
- `docs/verification.md`: keep this honest when testing against real Cortex.
- `herdr/` is a gitignored reference clone of upstream.

Rules:
- Upstream closes PRs from unapproved accounts. Don't open one; use Discussions #783 / #5636.
- Inside a Herdr pane the `HERDR_*` env points at the user's live server. Test on an isolated
  server, and stop it by a PID confirmed from its environment, never `herdr server stop`.
- Don't use the `herdr:` source prefix; it is reserved.
- Test with `python3 -I tests/test_hooks.py`.
