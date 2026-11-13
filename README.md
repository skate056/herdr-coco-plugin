# herdr-coco-plugin

Cortex Code support for [Herdr](https://github.com/herdrdev/herdr).

Herdr doesn't recognise Snowflake's `cortex` CLI, so a Cortex pane normally looks like a plain
terminal. With this installed, Cortex shows up as an agent:

- its state (`working`, `blocked`, `done`) appears in the sidebar and in `herdr agent list`
- Herdr notifies you when it finishes or is waiting for an approval
- `herdr agent wait` works on it
- after a Herdr restart, the pane reopens the same Cortex conversation

It works through Cortex's own hooks and Herdr's public CLI. Herdr itself is not modified.

This is a community project. It is not affiliated with or endorsed by Snowflake or Herdr.

## Requirements

- Herdr 0.9.2 or later (session resume needs 0.9.2; tested on 0.9.5)
- Cortex Code, installed and started at least once (tested on v1.2.41)
- `python3`
- macOS or Linux

## Install

```sh
git clone https://github.com/skate056/herdr-coco-plugin.git
cd herdr-coco-plugin
```

First check whether Herdr's Claude Code integration is installed:

```sh
herdr integration status | grep claude
```

If it says `not installed`:

```sh
python3 scripts/install.py install
```

If it shows a version (for example `current (v11)`):

```sh
python3 scripts/install.py install --guard-claude
```

The installer finishes by running `doctor`, which should print:

```text
hooks: ok
claude hook: ok
```

Restart any Cortex sessions that were already running so they pick up the hooks.

### Why `--guard-claude`

Cortex also runs the hooks in `~/.claude/settings.json`, including Herdr's Claude integration.
That hook claims the pane as a Claude session, and from then on Herdr silently ignores every
Cortex report from that pane. `--guard-claude` adds a check to that one hook so it does nothing
when Cortex runs it. Claude Code itself is unaffected.

## Use

Run `cortex` in a Herdr pane as usual. There is nothing else to do.

| What Cortex is doing | What Herdr shows |
| --- | --- |
| Just started, no prompt sent yet | Not listed as an agent yet |
| Working on your prompt or running a tool | `working` |
| Waiting for you to approve something or answer a question | `blocked` |
| Finished its turn | `done` until you look at the pane, then `idle` |
| You quit with `/exit` | Removed from the agent list |

Check from another pane with:

```sh
herdr agent list
```

### Resume after a Herdr restart

After the first prompt, Herdr remembers the conversation. If the Herdr server restarts, the pane
reopens in the same folder and runs `cortex --resume <session-id>`. To turn this off for every
agent, set `[session] resume_agents_on_restore = false` in Herdr's config.

## Check, update, uninstall

```sh
python3 scripts/install.py doctor      # check the install; exits 1 if something is wrong
git pull && python3 scripts/install.py install [--guard-claude]   # update
python3 scripts/install.py uninstall   # remove hooks and the Claude guard
```

The installer copies the hook to `~/.snowflake/cortex/herdr-cortex/`, so after `git pull` run
`install` again to pick up changes. Running it twice is safe: it replaces its own entries and
leaves any other hooks in place.

Before changing a file for the first time, the installer saves a copy next to it as
`<file>.herdr-cortex-backup`. It honours `SNOWFLAKE_HOME` and `CLAUDE_CONFIG_DIR`.

## Troubleshooting

**Cortex never appears in `herdr agent list`.**
Send a prompt first, since the pane only appears after one. Then run `doctor`.
If it says `claude hook: UNGUARDED`, run `install --guard-claude`, then close that pane and
open a new one: a pane that was already claimed as a Claude session stays ignored until it is
closed.

**`doctor` says `UNGUARDED` again after a while.**
Reinstalling Herdr's Claude integration (`herdr integration install claude`) adds the
unguarded hook back. Run `install --guard-claude` again.

**A pane is stuck in an old state after Cortex crashed.**
Cortex couldn't report its exit. Herdr clears it once the pane is back at the shell prompt; if
it doesn't, close the pane.

**Seeing what Cortex sends.**
Start Cortex with `HERDR_CORTEX_DEBUG=1 cortex`. Each hook appends its event name and the names
of the payload fields to `$TMPDIR/herdr-cortex-hook.log` (`/tmp` when `TMPDIR` is unset).
It never records prompts, SQL, or any other values.

## Limitations

- `herdr agent explain` and Herdr plugins that need a *detected* agent, such as herdr-annotate,
  don't see Cortex. That needs native support in Herdr.
- Herdr can't read the Cortex screen, so if Cortex crashes the last state stays until the pane
  returns to the shell prompt.

## How it works

| Cortex hook | Reported to Herdr |
| --- | --- |
| `UserPromptSubmit`, `PostToolUse` | `working` |
| `PermissionRequest`, `Notification` | `blocked` |
| `Stop` | `idle` |
| `SessionEnd` | release |

Each hook runs `src/herdr_report.py`, which calls `herdr pane report-agent` with the session's
resume command. It does nothing outside a Herdr pane, always exits 0, and prints nothing, so it
can't interrupt Cortex. `SessionStart` isn't used, because Cortex runs it before it reads
`hooks.json`.

See [docs/verification.md](docs/verification.md) for what has been tested and on what.

## Contributing

Issues and pull requests are welcome, especially results from Cortex or Herdr versions not
listed in [docs/verification.md](docs/verification.md). The code uses only the Python standard
library. Run the tests with:

```sh
python3 -I tests/test_hooks.py
```

For native Cortex support inside Herdr itself, add your voice to Herdr discussions
[#783](https://github.com/herdrdev/herdr/discussions/783) and
[#5636](https://github.com/herdrdev/herdr/discussions/5636).

## License

[MIT](LICENSE)
