"""Windows installer for the self-contained Taskloom desktop app.

The installer is packaged as one executable. It prompts for an install
location (Program Files/Taskloom by default), then places Taskloom.exe and
its runtime beside each other in that chosen location.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


PRODUCT_NAME = "Taskloom"
DEFAULT_INSTALL_DIR = Path(os.environ.get("ProgramFiles", r"C:\\Program Files")) / PRODUCT_NAME


def bundled_path(*parts: str) -> Path:
    """Resolve payload files in a PyInstaller one-file executable."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root.joinpath(*parts)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_elevated() -> None:
    args = " ".join(f'"{item}"' for item in sys.argv[1:] if item != "--elevated")
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args, None, 1)
    if result <= 32:
        raise OSError("Windows could not approve the installer.")


class Installer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Install Taskloom")
        # A generous, resizable window prevents controls being clipped at
        # common Windows display-scaling settings.
        self.geometry("820x610")
        self.minsize(720, 540)
        self.configure(bg="#f5f1e8")
        self.resizable(True, True)

        self.destination = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
        self.launch_after = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Choose where Taskloom should be installed.")
        self._build()

    def _build(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f1e8")
        style.configure("Title.TLabel", background="#f5f1e8", foreground="#151526", font=("Georgia", 27))
        style.configure("Kicker.TLabel", background="#f5f1e8", foreground="#1838df", font=("Courier New", 10, "bold"))
        style.configure("Body.TLabel", background="#f5f1e8", foreground="#56556a", font=("Segoe UI", 10))
        style.configure("Path.TEntry", fieldbackground="#ffffff", foreground="#151526", padding=10)
        style.configure("Secondary.TButton", background="#ffffff", foreground="#1838df", padding=(15, 11))

        main = ttk.Frame(self, padding=(48, 32))
        main.pack(fill="both", expand=True)
        # Reserve the footer before laying out content. This is important on
        # high-DPI screens: the install action stays in view instead of being
        # pushed below the window edge.
        actions = tk.Frame(main, bg="#f5f1e8", height=60)
        actions.pack(fill="x", side="bottom", pady=(24, 0))
        actions.pack_propagate(False)
        tk.Button(
            actions,
            text="Cancel",
            command=self.destroy,
            bg="#ffffff",
            fg="#1838df",
            activebackground="#e9edff",
            activeforeground="#1838df",
            relief="solid",
            bd=1,
            padx=22,
            pady=10,
            cursor="hand2",
        ).pack(side="right", fill="y")
        tk.Button(
            actions,
            text="Install Taskloom  →",
            command=self.install,
            bg="#1838df",
            fg="#ffffff",
            activebackground="#294be1",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=26,
            pady=10,
            font=("Courier New", 10, "bold"),
            cursor="hand2",
        ).pack(side="right", fill="y", padx=(0, 12))

        content = ttk.Frame(main)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text="TASKLOOM DESKTOP", style="Kicker.TLabel").pack(anchor="w")
        ttk.Label(content, text="Install your studio.", style="Title.TLabel").pack(anchor="w", pady=(9, 5))
        ttk.Label(
            content,
            text="Taskloom runs as a native Windows app. Your Gemini keys are set up later and saved only in Windows Credential Manager.",
            style="Body.TLabel",
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(0, 24))

        ttk.Label(content, text="INSTALL LOCATION", style="Kicker.TLabel").pack(anchor="w", pady=(0, 7))
        row = ttk.Frame(content)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.destination, style="Path.TEntry").pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse…", command=self.choose_folder, style="Secondary.TButton").pack(side="left", padx=(10, 0))
        ttk.Label(content, text="Default: Program Files. You can select a different folder if you prefer.", style="Body.TLabel").pack(anchor="w", pady=(7, 18))

        ttk.Checkbutton(content, text="Open Taskloom when installation finishes", variable=self.launch_after).pack(anchor="w", pady=(0, 16))
        ttk.Label(content, textvariable=self.status, style="Body.TLabel").pack(anchor="w")

    def choose_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Choose a Taskloom installation folder", initialdir=self.destination.get())
        if chosen:
            self.destination.set(str(Path(chosen) / PRODUCT_NAME) if Path(chosen).name.lower() != PRODUCT_NAME.lower() else chosen)

    def install(self) -> None:
        destination = Path(self.destination.get()).expanduser()
        payload = bundled_path("TaskloomPayload")
        executable = payload / "Taskloom.exe"
        if not executable.exists():
            messagebox.showerror("Installer files missing", "Taskloom's installation files could not be found. Please download the installer again.")
            return
        if not destination.name or destination == destination.anchor:
            messagebox.showerror("Choose a folder", "Please choose a folder for Taskloom.")
            return

        try:
            self.status.set("Installing Taskloom…")
            self.update_idletasks()
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copy2(executable, destination / "Taskloom.exe")
            shutil.copytree(payload / "Taskloom Runtime", destination / "Taskloom Runtime", dirs_exist_ok=True)
            readme = destination / "READ ME.txt"
            readme.write_text(
                "TASKLOOM DESKTOP\n\nOpen Taskloom.exe to start the app.\n\n"
                "On first use, select Connect Gemini. Create a Google AI Studio API key, then paste a primary key and (optionally) a spare backup key. "
                "Your keys are saved in Windows Credential Manager, not in this folder.\n",
                encoding="utf-8",
            )
        except OSError as exc:
            messagebox.showerror("Installation could not finish", f"Taskloom could not be installed here.\n\n{exc}")
            self.status.set("Installation needs a different folder or administrator permission.")
            return

        self.status.set("Installed successfully.")
        messagebox.showinfo("Taskloom installed", f"Taskloom is ready in:\n{destination}\n\nOpen Taskloom.exe whenever you want to work.")
        if self.launch_after:
            os.startfile(destination / "Taskloom.exe")
        self.destroy()


def main() -> None:
    # Program Files is protected. Elevate once so the default path works while
    # still letting the user select a different location in the installer UI.
    if not is_admin():
        try:
            relaunch_elevated()
        except OSError as exc:
            messagebox.showerror("Administrator approval required", str(exc))
        return
    Installer().mainloop()


if __name__ == "__main__":
    main()
