import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import random
import re
import sys
import threading
import time

try:
    import pyperclip
except ImportError:  # pragma: no cover - exercised by users without setup
    pyperclip = None


DATA_PATH = Path(__file__).with_name("trump.json")
DEFAULT_CONFIG = {
    "target": "",
    "context": "",
    "hotkey": "F8",
}


templates = [
    ["subjectnametwice1", "user_name", "subjectnametwice2", "user_name", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
]


niceQuotes = [
    "What a beautiful person!",
    "That one should be our president!",
    "I know the best people. And that's one of them.",
    "Fantastic, yuge potential!",
]


def clean_target_name(name):
    return str(name or "").strip()


def format_insult_parts(parts):
    stripped_parts = [str(part).strip() for part in parts if str(part).strip()]
    text = " ".join(stripped_parts)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def load_quotes(path=DATA_PATH):
    with Path(path).open("r", encoding="utf-8") as quotes_file:
        return json.load(quotes_file)


def generate_insult(name, quotes_data=None, rng=None):
    cleaned_name = clean_target_name(name)
    if not cleaned_name:
        raise ValueError("Target name is required.")

    selector = rng or random
    lower_name = cleaned_name.lower()
    if "donald" in lower_name or "trump" in lower_name or "ivanka" in lower_name:
        return selector.choice(niceQuotes)

    active_quotes = quotes_data or load_quotes()
    template = selector.choice(templates)
    parts = []
    for word in template:
        if word == "user_name":
            parts.append(cleaned_name)
        else:
            parts.append(selector.choice(active_quotes[word]))

    return format_insult_parts(parts)


def copy_to_clipboard(text):
    if pyperclip is None:
        raise RuntimeError("pyperclip is not installed. Run: pip install pyperclip")
    pyperclip.copy(text)


def generate_and_copy(target, clipboard_copy=copy_to_clipboard, rng=None):
    insult = generate_insult(target, rng=rng)
    clipboard_copy(insult)
    return insult


def get_config_path():
    override = os.environ.get("TRUMP_INSULT_GENERATOR_CONFIG")
    if override:
        return Path(override)

    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "TrumpInsultGenerator" / "config.json"

    return Path.home() / ".trump_insult_generator" / "config.json"


def load_config(path=None):
    config_path = Path(path) if path else get_config_path()
    config = dict(DEFAULT_CONFIG)
    if not config_path.exists():
        return config

    with config_path.open("r", encoding="utf-8") as config_file:
        loaded = json.load(config_file)

    for key in DEFAULT_CONFIG:
        value = loaded.get(key)
        if isinstance(value, str):
            config[key] = value
    return config


def save_config(config, path=None):
    config_path = Path(path) if path else get_config_path()
    merged = dict(DEFAULT_CONFIG)
    for key in DEFAULT_CONFIG:
        value = config.get(key, DEFAULT_CONFIG[key])
        merged[key] = str(value)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as config_file:
        json.dump(merged, config_file, indent=2)
        config_file.write("\n")


def hotkey_to_vk(hotkey):
    key = str(hotkey or "").strip().upper()
    if not re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])", key):
        raise ValueError("Only F1 through F24 are supported for now.")
    return 0x6F + int(key[1:])


class GlobalHotkey:
    def __init__(self, hotkey, callback):
        self.hotkey = hotkey
        self.callback = callback
        self.hotkey_id = 1
        self.thread = None
        self.thread_id = None
        self.ready = threading.Event()
        self.error = None

    def start(self):
        if sys.platform != "win32":
            raise RuntimeError("Global hotkeys are currently supported on Windows only.")
        if self.thread and self.thread.is_alive():
            return

        self.ready.clear()
        self.error = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(timeout=2):
            raise RuntimeError("Timed out while registering the hotkey.")
        if self.error:
            raise self.error

    def stop(self):
        if not self.thread or not self.thread.is_alive() or not self.thread_id:
            return
        user32 = ctypes.windll.user32
        user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
        self.thread.join(timeout=2)

    def _run(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self.thread_id = kernel32.GetCurrentThreadId()
        vk = hotkey_to_vk(self.hotkey)
        mod_norepeat = 0x4000

        if not user32.RegisterHotKey(None, self.hotkey_id, mod_norepeat, vk):
            self.error = ctypes.WinError()
            self.ready.set()
            return

        self.ready.set()
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312 and msg.wParam == self.hotkey_id:
                    self.callback()
        finally:
            user32.UnregisterHotKey(None, self.hotkey_id)


class InsultGeneratorApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.config = load_config()
        self.hotkey = None

        root.title("Trump Insult Generator")
        root.geometry("560x340")
        root.minsize(480, 300)

        self.target_var = tk.StringVar(value=self.config["target"])
        self.context_var = tk.StringVar(value=self.config["context"])
        self.hotkey_var = tk.StringVar(value=self.config["hotkey"])
        self.status_var = tk.StringVar(value="Ready")
        self.latest_var = tk.StringVar(value="")

        self._build()
        root.protocol("WM_DELETE_WINDOW", self.quit)

    def _build(self):
        root = self.root
        ttk = self.ttk

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(4, weight=1)

        ttk.Label(frame, text="Target name").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=self.target_var).grid(row=0, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="Context").grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=self.context_var).grid(row=1, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="Hotkey").grid(row=2, column=0, sticky="w", pady=(0, 12))
        ttk.Combobox(
            frame,
            textvariable=self.hotkey_var,
            values=[f"F{i}" for i in range(1, 13)],
            width=8,
            state="readonly",
        ).grid(row=2, column=1, sticky="w", pady=(0, 12))

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Button(buttons, text="Generate + Copy", command=self.generate_copy).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Save Target", command=self.save_current_config).pack(side="left", padx=(0, 8))
        self.hotkey_button = ttk.Button(buttons, text="Start Hotkeys", command=self.toggle_hotkeys)
        self.hotkey_button.pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Quit", command=self.quit).pack(side="right")

        latest = ttk.Label(
            frame,
            textvariable=self.latest_var,
            wraplength=500,
            justify="left",
            anchor="nw",
            relief="solid",
            padding=10,
        )
        latest.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, 8))

        ttk.Label(frame, textvariable=self.status_var).grid(row=5, column=0, columnspan=2, sticky="w")

    def save_current_config(self):
        target = clean_target_name(self.target_var.get())
        config = {
            "target": target,
            "context": self.context_var.get().strip(),
            "hotkey": self.hotkey_var.get().strip() or DEFAULT_CONFIG["hotkey"],
        }
        save_config(config)
        self.config = config
        self.target_var.set(target)
        self.status_var.set("Saved")

    def generate_copy(self):
        from tkinter import messagebox

        try:
            target = clean_target_name(self.target_var.get())
            if not target:
                raise ValueError("Enter a target name first.")
            self.save_current_config()
            insult = generate_and_copy(target)
        except Exception as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("Copy failed", str(exc))
            return

        self.latest_var.set(insult)
        self.status_var.set("Copied")

    def toggle_hotkeys(self):
        if self.hotkey and self.hotkey.thread and self.hotkey.thread.is_alive():
            self.hotkey.stop()
            self.hotkey = None
            self.hotkey_button.configure(text="Start Hotkeys")
            self.status_var.set("Hotkeys stopped")
            return

        try:
            self.save_current_config()
            self.hotkey = GlobalHotkey(
                self.hotkey_var.get(),
                lambda: self.root.after(0, self.generate_copy),
            )
            self.hotkey.start()
        except Exception as exc:
            self.hotkey = None
            self.status_var.set(str(exc))
            return

        self.hotkey_button.configure(text="Stop Hotkeys")
        self.status_var.set(f"{self.hotkey_var.get()} copies a fresh insult")

    def quit(self):
        if self.hotkey:
            self.hotkey.stop()
        self.root.destroy()


def run_gui():
    import tkinter as tk

    root = tk.Tk()
    InsultGeneratorApp(root)
    root.mainloop()


def run_hotkey_loop(config):
    target = clean_target_name(config["target"])
    if not target:
        raise ValueError("No target configured. Run the GUI or use --set-target NAME first.")

    lock = threading.Lock()

    def generate_print_copy():
        with lock:
            insult = generate_and_copy(target)
            print(insult, flush=True)

    hotkey = GlobalHotkey(config["hotkey"], generate_print_copy)
    hotkey.start()
    try:
        while True:
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        hotkey.stop()


def build_parser():
    parser = argparse.ArgumentParser(description="Generate and copy Trump-style insults.")
    parser.add_argument("name", nargs="*", help="Target name for one generated insult.")
    parser.add_argument("--target", help="Target name for one generated insult.")
    parser.add_argument("--set-target", help="Save the default target name.")
    parser.add_argument("--context", help="Save optional context for future modes.")
    parser.add_argument("--hotkey", help="Function key for --loop or GUI hotkey mode, default F8.")
    parser.add_argument("--copy", action="store_true", help="Generate, copy, and print one insult.")
    parser.add_argument("--loop", action="store_true", help="Run a persistent global-hotkey copy loop.")
    parser.add_argument("--gui", action="store_true", help="Open the control window.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if argv is None and len(sys.argv) == 1:
        run_gui()
        return 0

    config = load_config()
    if args.set_target is not None:
        config["target"] = clean_target_name(args.set_target)
    if args.context is not None:
        config["context"] = args.context.strip()
    if args.hotkey is not None:
        hotkey_to_vk(args.hotkey)
        config["hotkey"] = args.hotkey.strip().upper()
    if args.set_target is not None or args.context is not None or args.hotkey is not None:
        save_config(config)

    if args.gui:
        run_gui()
        return 0

    if args.loop:
        run_hotkey_loop(config)
        return 0

    positional_target = " ".join(args.name).strip()
    target = clean_target_name(args.target or positional_target or config["target"])
    if args.copy or args.target or positional_target:
        insult = generate_and_copy(target)
        print(insult)
        return 0

    if args.set_target is not None or args.context is not None or args.hotkey is not None:
        return 0

    run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
