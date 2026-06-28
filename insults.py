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
    "targets": [],
    "context": "",
    "hotkey": "F8",
    "overlay": False,
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


def required_quote_keys():
    keys = set()
    for template in templates:
        for word in template:
            if word != "user_name":
                keys.add(word)
    return sorted(keys)


def validate_quote_data(quote_data, active_templates=None):
    errors = []
    template_keys = set()
    for template in active_templates or templates:
        for word in template:
            if word != "user_name":
                template_keys.add(word)

    for key in sorted(template_keys):
        if key not in quote_data:
            errors.append(f"Missing quote category: {key}")
            continue
        if not isinstance(quote_data[key], list):
            errors.append(f"Quote category is not a list: {key}")
            continue
        if not quote_data[key]:
            errors.append(f"Empty quote category: {key}")
            continue
        for fragment in quote_data[key]:
            if not isinstance(fragment, str):
                errors.append(f"Non-string quote fragment in category: {key}")
                break
            if not fragment.strip():
                errors.append(f"Blank quote fragment in category: {key}")
                break

    return errors


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
    config["targets"] = []
    if not config_path.exists():
        return config

    with config_path.open("r", encoding="utf-8") as config_file:
        loaded = json.load(config_file)

    for key in DEFAULT_CONFIG:
        if key == "targets":
            continue
        if key == "overlay":
            value = loaded.get(key)
            if isinstance(value, bool):
                config[key] = value
            continue
        value = loaded.get(key)
        if isinstance(value, str):
            config[key] = value

    loaded_targets = loaded.get("targets", [])
    if isinstance(loaded_targets, list):
        config["targets"] = normalize_targets(loaded_targets)
    config["targets"] = add_target_to_list(config["targets"], config["target"])
    return config


def save_config(config, path=None):
    config_path = Path(path) if path else get_config_path()
    merged = dict(DEFAULT_CONFIG)
    for key in DEFAULT_CONFIG:
        if key == "targets":
            continue
        if key == "overlay":
            merged[key] = bool(config.get(key, DEFAULT_CONFIG[key]))
            continue
        value = config.get(key, DEFAULT_CONFIG[key])
        merged[key] = str(value)
    merged["targets"] = normalize_targets(config.get("targets", []))
    merged["targets"] = add_target_to_list(merged["targets"], merged["target"])

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as config_file:
        json.dump(merged, config_file, indent=2)
        config_file.write("\n")


def normalize_targets(targets):
    normalized = []
    for target in targets or []:
        cleaned = clean_target_name(target)
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def add_target_to_list(targets, target):
    normalized = [existing for existing in normalize_targets(targets) if existing != clean_target_name(target)]
    cleaned = clean_target_name(target)
    if cleaned:
        normalized.append(cleaned)
    return normalized


def add_saved_target(config, target):
    updated = dict(config)
    cleaned = clean_target_name(target)
    updated["target"] = cleaned
    updated["targets"] = add_target_to_list(config.get("targets", []), cleaned)
    return updated


def remove_saved_target(config, target):
    updated = dict(config)
    cleaned = clean_target_name(target)
    updated["targets"] = [existing for existing in normalize_targets(config.get("targets", [])) if existing != cleaned]
    if updated.get("target") == cleaned:
        updated["target"] = updated["targets"][-1] if updated["targets"] else ""
    return updated


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
        self.overlay_preview = None

        root.title("Trump Insult Generator")
        root.geometry("600x390")
        root.minsize(520, 340)

        self.target_var = tk.StringVar(value=self.config["target"])
        self.context_var = tk.StringVar(value=self.config["context"])
        self.hotkey_var = tk.StringVar(value=self.config["hotkey"])
        self.overlay_var = tk.BooleanVar(value=bool(self.config["overlay"]))
        self.status_var = tk.StringVar(value="Ready")
        self.latest_var = tk.StringVar(value="")
        self.target_combo = None
        self.overlay_preview = OverlayPreview(root)

        self._build()
        root.protocol("WM_DELETE_WINDOW", self.quit)

    def _build(self):
        root = self.root
        ttk = self.ttk

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)

        ttk.Label(frame, text="Target name").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.target_combo = ttk.Combobox(
            frame,
            textvariable=self.target_var,
            values=self.config["targets"],
        )
        self.target_combo.grid(row=0, column=1, sticky="ew", pady=(0, 8))

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

        ttk.Checkbutton(
            frame,
            text="Show overlay preview after copy",
            variable=self.overlay_var,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 12))

        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 12))
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
        latest.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(0, 8))

        ttk.Label(frame, textvariable=self.status_var).grid(row=6, column=0, columnspan=2, sticky="w")

    def save_current_config(self):
        target = clean_target_name(self.target_var.get())
        config = {
            "target": target,
            "targets": self.config.get("targets", []),
            "context": self.context_var.get().strip(),
            "hotkey": self.hotkey_var.get().strip() or DEFAULT_CONFIG["hotkey"],
            "overlay": bool(self.overlay_var.get()),
        }
        config = add_saved_target(config, target)
        save_config(config)
        self.config = config
        self.target_var.set(target)
        if self.target_combo:
            self.target_combo.configure(values=self.config["targets"])
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
        if self.overlay_var.get():
            self.overlay_preview.show(insult)
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


class OverlayPreview:
    def __init__(self, root, duration_ms=2500):
        import tkinter as tk

        self.root = root
        self.tk = tk
        self.duration_ms = duration_ms
        self.window = None
        self.after_id = None

    def show(self, text):
        if self.window:
            self.hide()

        window = self.tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.attributes("-alpha", 0.92)
        width = min(max(520, len(text) * 7), 1100)
        height = 90
        screen_width = window.winfo_screenwidth()
        x = max(0, int((screen_width - width) / 2))
        window.geometry(f"{width}x{height}+{x}+24")
        window.configure(bg="black")

        canvas = self.tk.Canvas(window, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        wrapped = self._wrap_text(text, width)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)]:
            canvas.create_text(
                width // 2 + dx,
                height // 2 + dy,
                text=wrapped,
                fill="black",
                font=("Segoe UI", 18, "bold"),
                width=width - 30,
                justify="center",
            )
        canvas.create_text(
            width // 2,
            height // 2,
            text=wrapped,
            fill="white",
            font=("Segoe UI", 18, "bold"),
            width=width - 30,
            justify="center",
        )

        self.window = window
        self.after_id = self.root.after(self.duration_ms, self.hide)

    def hide(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.window:
            self.window.destroy()
            self.window = None

    def _wrap_text(self, text, width):
        max_chars = max(40, width // 12)
        words = text.split()
        lines = []
        current = []
        current_len = 0
        for word in words:
            next_len = current_len + len(word) + (1 if current else 0)
            if current and next_len > max_chars:
                lines.append(" ".join(current))
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len = next_len
        if current:
            lines.append(" ".join(current))
        return "\n".join(lines[:2])


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
    parser.add_argument("--list-targets", action="store_true", help="Print saved targets and exit.")
    parser.add_argument("--remove-target", help="Remove a saved target name.")
    parser.add_argument("--context", help="Save optional context for future modes.")
    parser.add_argument("--hotkey", help="Function key for --loop or GUI hotkey mode, default F8.")
    parser.add_argument("--copy", action="store_true", help="Generate, copy, and print one insult.")
    parser.add_argument("--loop", action="store_true", help="Run a persistent global-hotkey copy loop.")
    parser.add_argument("--gui", action="store_true", help="Open the control window.")
    parser.add_argument("--validate", action="store_true", help="Validate trump.json and templates.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if argv is None and len(sys.argv) == 1:
        run_gui()
        return 0

    config = load_config()
    if args.set_target is not None:
        config = add_saved_target(config, args.set_target)
    if args.remove_target is not None:
        config = remove_saved_target(config, args.remove_target)
    if args.context is not None:
        config["context"] = args.context.strip()
    if args.hotkey is not None:
        hotkey_to_vk(args.hotkey)
        config["hotkey"] = args.hotkey.strip().upper()
    if args.set_target is not None or args.remove_target is not None or args.context is not None or args.hotkey is not None:
        save_config(config)

    if args.list_targets:
        for target in config.get("targets", []):
            print(target)
        return 0

    if args.gui:
        run_gui()
        return 0

    if args.validate:
        errors = validate_quote_data(load_quotes())
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("trump.json is valid.")
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

    if args.set_target is not None or args.remove_target is not None or args.context is not None or args.hotkey is not None:
        return 0

    run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
