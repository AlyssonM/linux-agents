#!/usr/bin/env python3
import os
import pty
import select
import subprocess
import sys
import termios


def run_with_pty(args, password):
    cmd = ["secretctl", *args]
    env = os.environ.copy()
    master_fd, slave_fd = pty.openpty()
    attrs = termios.tcgetattr(slave_fd)
    attrs[3] = attrs[3] & ~termios.ECHO
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)
    proc = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        close_fds=True,
        text=True,
    )
    os.close(slave_fd)
    prompt_tokens = ("master password", "password:")
    while True:
        ready, _, _ = select.select([master_fd], [], [], 0.1)
        if master_fd in ready:
            try:
                data = os.read(master_fd, 1024).decode("utf-8", errors="ignore")
            except OSError:
                break
            if not data:
                break
            safe_data = data.replace(password, "[REDACTED:MASTER_PASSWORD]")
            sys.stdout.write(safe_data)
            sys.stdout.flush()
            if any(token in data.lower() for token in prompt_tokens):
                os.write(master_fd, (password + "\n").encode())
        if proc.poll() is not None:
            break
    os.close(master_fd)
    return proc.returncode


def main():
    if len(sys.argv) < 2:
        print("Uso: wrapper_secretctl.py <comando> [args...]")
        return 1
    password = os.getenv("SECRETCTL_PASSWORD")
    if not password:
        print("ERRO: Defina SECRETCTL_PASSWORD")
        return 1
    return run_with_pty(sys.argv[1:], password)


if __name__ == "__main__":
    raise SystemExit(main())
