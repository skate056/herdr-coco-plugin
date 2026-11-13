"""Unit tests. A fake herdr records argv, so no server is needed."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "src" / "herdr_report.py"
INSTALL = ROOT / "scripts" / "install.py"
CLAUDE_CMD = "bash '/h/.claude/hooks/herdr-agent-state.sh' session"


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.log = self.tmp / "argv.log"
        self.fake = self.tmp / "herdr"
        self.fake.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> {self.log}\n')
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IEXEC)

    def report(self, state, payload="{}", **env):
        base = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_")}
        base.update(HERDR_ENV="1", HERDR_PANE_ID="w1:p1", HERDR_BIN_PATH=str(self.fake))
        base.update(env)
        return subprocess.run(
            [sys.executable, "-I", str(REPORT), state],
            input=payload.encode(), capture_output=True, env=base, check=False,
        )

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []


class Report(Base):
    def test_state_includes_session_and_resume(self):
        r = self.report("working", '{"session_id":"abc-1"}')
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, b"", b""))
        call = self.calls()[0]
        self.assertIn("pane report-agent w1:p1 --source cortex-herdr --agent cortex", call)
        self.assertTrue(call.endswith("--agent-session-id abc-1 -- cortex --resume abc-1"))

    def test_release(self):
        self.report("release")
        self.assertIn("pane release-agent w1:p1", self.calls()[0])

    def test_unsafe_session_id_is_not_resumable(self):
        self.report("working", json.dumps({"session_id": "a'b"}))
        self.assertNotIn("--resume", self.calls()[0])

    def test_seq_increases(self):
        self.report("working")
        self.report("idle")
        seqs = [int(c.split("--seq ")[1].split()[0]) for c in self.calls()]
        self.assertLess(seqs[0], seqs[1])

    def test_silent_outside_herdr_and_for_subagents(self):
        self.report("working", HERDR_ENV="0")
        self.report("working", '{"agent_id":"sub"}')
        self.report("bogus")
        self.assertEqual(self.calls(), [])

    def test_bad_input_or_broken_herdr_still_exits_zero(self):
        self.assertEqual(self.report("working", "not json").returncode, 0)
        self.assertEqual(self.report("idle", HERDR_BIN_PATH="/no/such").returncode, 0)


class Install(Base):
    def run_install(self, *args):
        env = dict(os.environ, SNOWFLAKE_HOME=str(self.tmp / "sf"),
                   CLAUDE_CONFIG_DIR=str(self.tmp / "claude"))
        return subprocess.run([sys.executable, "-I", str(INSTALL), *args],
                              capture_output=True, text=True, env=env, check=False)

    def setUp(self):
        super().setUp()
        (self.tmp / "sf" / "cortex").mkdir(parents=True)
        (self.tmp / "claude").mkdir()
        self.hooks = self.tmp / "sf" / "cortex" / "hooks.json"
        self.claude = self.tmp / "claude" / "settings.json"
        self.claude.write_text(json.dumps({"model": "x", "hooks": {"SessionStart": [
            {"matcher": "^startup$", "hooks": [{"type": "command", "command": CLAUDE_CMD}]}]}}))

    def claude_cmd(self):
        return json.loads(self.claude.read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"]

    def test_refuses_without_cortex(self):
        (self.tmp / "sf" / "cortex").rmdir()
        self.assertNotEqual(self.run_install("install").returncode, 0)

    def test_install_is_idempotent_and_keeps_user_hooks(self):
        mine = {"hooks": [{"type": "command", "command": "mine.sh"}]}
        self.hooks.write_text(json.dumps({"hooks": {"Stop": [mine]}}))
        self.run_install("install")
        self.run_install("install")
        hooks = json.loads(self.hooks.read_text())["hooks"]
        self.assertEqual(len(hooks["Stop"]), 2)
        self.assertEqual(hooks["Stop"][0], mine)
        self.assertNotIn("SessionStart", hooks)
        self.run_install("uninstall")
        self.assertEqual(json.loads(self.hooks.read_text())["hooks"], {"Stop": [mine]})

    def test_claude_untouched_unless_opted_in(self):
        r = self.run_install("install")
        self.assertEqual(self.claude_cmd(), CLAUDE_CMD)
        self.assertIn("UNGUARDED", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_guard_round_trip(self):
        r = self.run_install("install", "--guard-claude")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(self.claude_cmd().endswith(CLAUDE_CMD))
        self.assertNotEqual(self.claude_cmd(), CLAUDE_CMD)
        self.assertEqual(json.loads(self.claude.read_text())["model"], "x")
        self.run_install("uninstall")
        self.assertEqual(self.claude_cmd(), CLAUDE_CMD)

    def test_guard_blocks_only_under_cortex(self):
        self.run_install("install", "--guard-claude")
        cmd = self.claude_cmd().replace(CLAUDE_CMD, "echo ran")
        clean = {k: v for k, v in os.environ.items() if not k.startswith("CORTEX_")}
        run = lambda e: subprocess.run(["sh", "-c", cmd], env=e, capture_output=True, text=True).stdout
        self.assertEqual(run(clean), "ran\n")
        self.assertEqual(run(dict(clean, CORTEX_PROJECT_DIR="/p")), "")
        self.assertEqual(run(dict(clean, CORTEX_CODE_CLIENT_SURFACE="coco_cli")), "")


if __name__ == "__main__":
    unittest.main()
