# Clipboard to Keyboard Simulator

Reads text from clipboard and types it out at 300 characters per minute. Press ` (backtick) to start/stop.

## Installation

```bash
pip install -r requirements.txt
```

On macOS: Grant accessibility permissions to Terminal in System Preferences > Security & Privacy > Privacy > Accessibility.

## Usage

1. Copy text to clipboard
2. Run: `python keyboard_simulator.py`
3. Switch to target application
4. Press ` to start typing
5. Press ` again to pause
6. Repeats until complete

## Speed

Default: 300 CPM (~40 WPM). Edit `cpm = 300` in the script to change speed.
