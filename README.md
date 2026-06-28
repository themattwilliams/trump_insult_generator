# The BEST Trump Insult Generator

Generate a Trump-style insult for a target name, copy it to the clipboard, and paste it into a game chat window in one fast action.

## What it is

This is a small Windows-first Python utility for game-chat use. The default mode opens a simple control window where you set the target name, optional context, and hotkey. The generated insult is copied to your clipboard so you can paste it into chat as a single chunk of text.

The insult fragments come from `trump.json`. Some misspellings are intentional quote fragments and should not be corrected unless the source text is wrong. Spacing around generated output is normalized so player names do not pick up stray spaces.

## Requirements

- Python 3.10+
- `pyperclip`
- Windows for global hotkey mode

Install dependencies:

```powershell
pip install -r requirements.txt
```

Recommended Windows launch:

```powershell
.\run_insult_generator.bat
```

The batch launcher creates `.venv` if needed, installs dependencies from `requirements.txt` into that virtual environment, and starts the app with `.venv\Scripts\python.exe`. On later launches it reuses `.venv` and skips dependency install unless `requirements.txt` changes.

## Default GUI Usage

Run:

```powershell
.\run_insult_generator.bat
```

Then:

1. Enter the target player or character name exactly as you want it to appear.
2. Add optional context if useful for later modes.
3. Choose a function-key hotkey. Default is `F8`.
4. Click `Generate + Copy` to create one insult and copy it.
5. Click `Start Hotkeys` to let the hotkey generate and copy a fresh insult while the app is running.

The app does not send chat messages or interact with the game process. It only writes text to the clipboard.

## CLI Usage

Generate once, copy to clipboard, and print only the insult:

```powershell
.\run_insult_generator.bat "xX_Player_Xx"
```

Save a default target:

```powershell
.\run_insult_generator.bat --set-target "xX_Player_Xx"
```

Generate for the saved target:

```powershell
.\run_insult_generator.bat --copy
```

Run persistent hotkey mode using the saved target:

```powershell
.\run_insult_generator.bat --loop
```

Change the hotkey:

```powershell
.\run_insult_generator.bat --hotkey F9 --set-target "xX_Player_Xx"
```

## Config

The app stores config at:

```text
%APPDATA%\TrumpInsultGenerator\config.json
```

Stored fields:

- `target`
- `context`
- `hotkey`

## Development

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Run a syntax check:

```powershell
python -m py_compile insults.py
```

## Modifying Insults

Edit `trump.json` to change quote fragments. Edit the `templates` list in `insults.py` to change how fragments are assembled.

Keep intentional quote misspellings intact. Fix spacing and punctuation assembly in code/tests instead of manually rewriting quote fragments.

## License

This program is released under the GNU General Public License v3.0. See `LICENSE`.
