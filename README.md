# Human-Like Keyboard Typing Simulator

A sophisticated Python script that simulates realistic human typing behavior by reading text from your clipboard and typing it with natural variations, mistakes, corrections, and pauses.

## Features

✨ **Natural Speed Variation** - Typing speed oscillates smoothly using a sine wave pattern  
🎯 **Realistic Typos** - Four types of mistakes: double-typing, character swaps, adjacent key errors, and skipped characters  
🔧 **Smart Corrections** - Weighted delayed corrections that catch mistakes after typing 0-5 more characters  
⏸️ **Thinking Pauses** - Natural pauses after spaces, punctuation, and newlines with configurable probabilities  
🎚️ **Highly Configurable** - All parameters organized at the top of the script for easy customization  
⌨️ **Toggle Control** - Press F9 to start/pause typing from any app
🪟 **Background Mode** - Types into a Chrome tab while you keep using your keyboard and mouse in other apps and tabs

## Installation

```bash
pip install -r requirements.txt
```

**macOS Users:** Grant accessibility permissions to your Terminal app in:  
System Preferences > Security & Privacy > Privacy > Accessibility

## Usage

### Background mode (default)

1. Copy text to clipboard
2. Run: `python keyboard_simulator.py`
3. A separate Chrome window opens (its own profile, so sign in to Google there the first time; it remembers you after that)
4. Open your doc in that window and click where the text should go
5. Press `F9`. From here on you can use any other app, window, or tab, including your normal Chrome
6. Press `F9` again (from anywhere) to pause/resume
7. Script exits when done

The page gets normal trusted `keydown`/`keypress`/`input`/`keyup` events with real key codes, Shift for capitals, and realistic key hold times. It also keeps thinking it's the focused, visible tab while you're somewhere else.

Notes:
- Only works for pages in that Chrome window, not desktop apps. Use foreground mode for those.
- Don't close that Chrome window or the target tab while it's typing.
- While that Chrome window is open, any program on your machine can control it through port 9222. Close it when you're done.

### Foreground mode

Types real OS keystrokes into whatever window has focus (any app, but you can't use your keyboard while it runs).

1. Copy text to clipboard
2. Run: `python keyboard_simulator.py --foreground` (or set `BACKGROUND = False`)
3. Click into the target app and press `F9`

## Configuration

All settings are at the top of `keyboard_simulator.py`:

### Mode
- `BACKGROUND` - `True` types into a Chrome tab in the background, `False` types into the focused window
- `HOTKEY` - Start/pause key (default: F9)
- `CHROME_PATH` - Set this if Chrome isn't found automatically

### Typing Speed
- `WPM` - Base words per minute (default: 80)
- `JITTER` - Random variation on every keystroke delay (0.25 = ±25%)
- `KEY_HOLD_MIN` / `KEY_HOLD_MAX` - How long each key is held down
- `MIN_SPEED` / `MAX_SPEED` - Speed variation range (0.80 to 1.20 = ±20%)
- `WAVE_FREQUENCY` - How fast speed oscillates (default: 0.3)

### Typo Settings
- `TYPO_PROBABILITY` - Chance of making a typo on a letter (0.025 = 2.5%)
- `TYPO_UNCORRECTED_PROBABILITY` - Chance typo stays uncorrected (0.1 = 10%)
- `TYPO_*_WEIGHT` - Relative probability of each typo type
- `CORRECTION_DELAY_WEIGHTS` - When mistakes are noticed (immediate vs delayed)

### Pause Settings
- `PAUSE_AFTER_SPACE_PROBABILITY` - Pause after space (0.05 = 5%)
- `PAUSE_AFTER_PUNCTUATION_PROBABILITY` - Pause after punctuation (0.2 = 20%)
- `PAUSE_AFTER_NEWLINE_PROBABILITY` - Pause after newlines (0.9 = 90%)
- Duration ranges for each pause type (min/max in seconds)

## How It Works

### Speed Variation
Typing speed varies smoothly along a sine wave between MIN_SPEED and MAX_SPEED multipliers, creating natural rhythm changes.

### Typo Types
1. **Double-type** - Character typed twice by accident
2. **Skip** - Character accidentally skipped
3. **Swap** - Two adjacent characters typed in wrong order  
4. **Adjacent Key** - Wrong key pressed (based on QWERTY keyboard proximity)

### Delayed Corrections
When a typo occurs, the script probabilistically decides when to notice it:
- 75% chance: noticed immediately
- 12.5% chance: after 1 more character
- Decreasing probabilities up to 5 characters later

When noticed, it backspaces to the last correct character and keeps typing from there.

### Thinking Pauses
Uses triangular distribution (y=x curve) where longer pauses are more likely than shorter ones:
- **Space pauses**: 0.32-2.5 seconds (between words)
- **Punctuation pauses**: 0.05-4.0 seconds (end of sentence)
- **Newline pauses**: 2.0-5.0 seconds (end of paragraph)

## Example Settings

**Fast, accurate typing:**
```python
WPM = 120
TYPO_PROBABILITY = 0.02
PAUSE_AFTER_SPACE_PROBABILITY = 0.02
```

**Slow, error-prone typing:**
```python
WPM = 40
TYPO_PROBABILITY = 0.15
TYPO_UNCORRECTED_PROBABILITY = 0.3
```

**Thoughtful writing style:**
```python
PAUSE_AFTER_SPACE_PROBABILITY = 0.15
PAUSE_SPACE_MAX = 4.0
PAUSE_AFTER_PUNCTUATION_PROBABILITY = 0.4
```

## Requirements

- Python 3.8+
- pyperclip
- pynput
- websocket-client
- Google Chrome (background mode)

Logic self-check: `python test_typing.py`

## License

MIT
