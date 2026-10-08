#!/usr/bin/env python3
"""Extract a verified encrypted ZIP using a password from stdin, not argv.

The caller supplies the password over a pipe. unzip receives it only when its
interactive password prompt appears on a private pseudoterminal.
"""

import errno
import os
from pathlib import Path
import pty
import re
import select
import sys
import termios


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: unzip-ack.py ARCHIVE DESTINATION", file=sys.stderr)
        return 2
    password = sys.stdin.buffer.readline().rstrip(b"\r\n")
    if not password:
        print("Missing archive password on stdin", file=sys.stderr)
        return 2
    archive, destination = map(Path, sys.argv[1:])
    pid, master = pty.fork()
    if pid == 0:
        attrs = termios.tcgetattr(0)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(0, termios.TCSANOW, attrs)
        os.execvp("unzip", ["unzip", str(archive), "-d", str(destination)])
    tail = b""
    prompts = 0
    try:
        while True:
            select.select([master], [], [])
            try:
                chunk = os.read(master, 4096)
            except OSError as exc:
                if exc.errno == errno.EIO:  # PTY slave closed
                    break
                raise
            if not chunk:
                break
            os.write(sys.stdout.fileno(), chunk)
            prompt_text = tail + chunk
            # Info-ZIP prints a prompt without a newline. Only answer that
            # prompt; never feed the password to another unzip question.
            if re.search(rb"(?i)password[^\r\n]*:\s*$", prompt_text):
                prompts += 1
                if prompts > 1:
                    print("\nRepeated password prompt; stopping extraction", file=sys.stderr)
                    os.kill(pid, 15)
                    break
                os.write(master, password + b"\n")
                tail = b""
                continue
            tail = prompt_text[-256:]
    finally:
        os.close(master)
    _, status = os.waitpid(pid, 0)
    if prompts != 1:
        print(f"Expected one archive-password prompt; observed {prompts}", file=sys.stderr)
        return 1
    return os.waitstatus_to_exitcode(status)


if __name__ == "__main__":
    raise SystemExit(main())
