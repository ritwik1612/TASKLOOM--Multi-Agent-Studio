"""Entry point used by the Windows Taskloom desktop application."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from paths import resource_path


SERVER_FLAG = "--taskloom-server"


def find_available_port() -> int:
    """Reserve a temporary local port number for this Taskloom session."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def run_streamlit_server(port: int) -> int:
    """Run the internal, browserless Streamlit server for the native window."""
    from streamlit.web import cli as streamlit_cli

    sys.argv = [
        "streamlit",
        "run",
        str(resource_path("app.py")),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
        f"--server.port={port}",
    ]
    return streamlit_cli.main()


def wait_for_server(url: str, timeout_seconds: float = 20) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.75) as response:
                if response.status == 200:
                    return True
        except OSError:
            time.sleep(0.2)
    return False


def launch_desktop_window() -> int:
    """Start a local server in the background and display it in a native window."""
    import webview

    webview.settings["ALLOW_DOWNLOADS"] = True
    port = find_available_port()
    url = f"http://127.0.0.1:{port}"
    command = [sys.executable]
    if getattr(sys, "frozen", False):
        command.append(SERVER_FLAG)
    else:
        command.extend([str(Path(__file__).resolve()), SERVER_FLAG])
    command.extend(["--port", str(port)])

    child_env = os.environ.copy()
    child_env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    server = subprocess.Popen(command, env=child_env, creationflags=creation_flags)
    try:
        if not wait_for_server(url):
            raise RuntimeError("Taskloom could not start its local application service.")
        webview.create_window(
            "Taskloom · Multi-Agent Studio",
            url,
            width=1440,
            height=920,
            min_size=(390, 640),
            resizable=True,
            text_select=True,
        )
        webview.start(gui="edgechromium", private_mode=True)
        return 0
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


def main() -> int:
    if SERVER_FLAG in sys.argv:
        port_index = sys.argv.index("--port") + 1
        return run_streamlit_server(int(sys.argv[port_index]))
    return launch_desktop_window()


if __name__ == "__main__":
    raise SystemExit(main())
