#!/usr/bin/env python3
import os
import pty
import select
import subprocess
import sys
import termios
import tty


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
    stdin_fd = sys.stdin.fileno()
    stdout_fd = sys.stdout.fileno()
    stdin_is_tty = os.isatty(stdin_fd)
    original_stdin_attrs = None
    if stdin_is_tty:
        original_stdin_attrs = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)
    try:
        while True:
            read_fds = [master_fd]
            if stdin_is_tty:
                read_fds.append(stdin_fd)
            ready, _, _ = select.select(read_fds, [], [], 0.1)
            if master_fd in ready:
                try:
                    data_bytes = os.read(master_fd, 1024)
                except OSError:
                    break
                if not data_bytes:
                    break
                data = data_bytes.decode("utf-8", errors="ignore")
                safe_data = data.replace(password, "[REDACTED:MASTER_PASSWORD]")
                os.write(stdout_fd, safe_data.encode("utf-8", errors="ignore"))
                if any(token in data.lower() for token in prompt_tokens):
                    os.write(master_fd, (password + "\n").encode())
            if stdin_is_tty and stdin_fd in ready:
                try:
                    user_data = os.read(stdin_fd, 1024)
                except OSError:
                    user_data = b""
                if user_data:
                    os.write(master_fd, user_data)
            if proc.poll() is not None:
                break
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait(timeout=2)
    finally:
        if stdin_is_tty and original_stdin_attrs is not None:
            termios.tcsetattr(stdin_fd, termios.TCSANOW, original_stdin_attrs)
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
