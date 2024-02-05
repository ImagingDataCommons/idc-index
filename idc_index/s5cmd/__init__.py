from __future__ import annotations

import os
import subprocess
import sys

S5CMD_BIN_DIR = os.path.join(os.path.dirname(__file__))


def _program(name, args):
    return subprocess.call([os.path.join(S5CMD_BIN_DIR, name), *args], close_fds=False)


def s5cmd():
    raise SystemExit(_program("s5cmd", sys.argv[1:]))
