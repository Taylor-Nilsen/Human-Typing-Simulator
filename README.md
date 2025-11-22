# Human-Like Keyboard Typing Simulator

A sophisticated Python script that simulates realistic human typing behavior by reading text from your clipboard and typing it with natural variations, mistakes, corrections, and pauses.

## Features

✨ **Natural Speed Variation** - Typing speed oscillates smoothly using a sine wave pattern  
🎯 **Realistic Typos** - Four types of mistakes: double-typing, character swaps, adjacent key errors, and skipped characters  
🔧 **Smart Corrections** - Weighted delayed corrections that catch mistakes after typing 0-5 more characters  
⏸️ **Thinking Pauses** - Natural pauses after spaces, punctuation, and newlines with configurable probabilities  
🎚️ **Highly Configurable** - All parameters organized at the top of the script for easy customization  
⌨️ **Toggle Control** - Press ` (backtick) to start/pause typing at any time

## Installation

```bash
pip install -r requirements.txt
```

**macOS Users:** Grant accessibility permissions to your Terminal app in:  
System Preferences > Security & Privacy > Privacy > Accessibility

## Usage

1. Copy text to clipboard
2. Run: `python keyboard_simulator.py`
3. Switch to your target application
4. Press `` ` `` (backtick) to start typing
5. Press `` ` `` again to pause/resume
6. Script completes automatically when done

## Configuration

All settings are at the top of `keyboard_simulator.py`:

### Typing Speed
- `WPM` - Base words per minute (default: 80)
- `MIN_SPEED` / `MAX_SPEED` - Speed variation range (0.80 to 1.20 = ±20%)
- `WAVE_FREQUENCY` - How fast speed oscillates (default: 0.3)

### Typo Settings
- `TYPO_PROBABILITY` - Chance of making a typo (0.05 = 5%)
- `TYPO_UNCORRECTED_PROBABILITY` - Chance typo stays uncorrected (0.1 = 10%)
- `TYPO_*_WEIGHT` - Relative probability of each typo type
- `CORRECTION_DELAY_WEIGHTS` - When mistakes are noticed (immediate vs delayed)

### Pause Settings
- `PAUSE_AFTER_SPACE_PROBABILITY` - Pause after space (0.05 = 5%)
- `PAUSE_AFTER_PERIOD_PROBABILITY` - Pause after punctuation (0.15 = 15%)
- `PAUSE_AFTER_NEWLINE_PROBABILITY` - Pause after newlines (0.3 = 30%)
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

When noticed, it backtracks, deletes the error, and retypes correctly.

### Thinking Pauses
Uses triangular distribution (y=x curve) where longer pauses are more likely than shorter ones:
- **Space pauses**: 0.3-2.5 seconds (between words)
- **Period pauses**: 0.5-3.5 seconds (end of sentence)
- **Newline pauses**: 1.0-5.0 seconds (end of paragraph)

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
PAUSE_AFTER_PERIOD_PROBABILITY = 0.4
```

## Requirements

- Python 3.7+
- pyperclip
- pynput

## License

MIT
