#!/usr/bin/env python3
"""Dedicated script for running the bitaxe-mcp test suite via pytest."""

import argparse
import subprocess
import sys


def main() -> int:
    """Run the test suite, passing through any extra flags to pytest."""
    _ = argparse.ArgumentParser().parse_known_args()
    result = subprocess.run(["uv", "run", "python", "-m", "pytest"] + sys.argv[1:])
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
