#!/usr/bin/env python3
"""Run backend unit and API tests inside Docker."""

import subprocess
import sys

result = subprocess.run(
    ["docker", "compose", "run", "--rm", "--no-deps", "backend", "pytest", "tests/", "-v"],
    cwd=".",
)
sys.exit(result.returncode)
