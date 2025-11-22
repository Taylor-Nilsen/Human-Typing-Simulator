#!/usr/bin/env python3
import time
import math
import random
import pyperclip
from pynput.keyboard import Controller, Listener, Key

# ===== CONFIGURATION =====
WPM = 80                   # Base typing speed in words per minute
MIN_SPEED = 0.80            # Minimum speed multiplier (80% of base)
MAX_SPEED = 1.20            # Maximum speed multiplier (120% of base)
WAVE_FREQUENCY = 0.32        # How fast the speed oscillates (higher = faster changes)
TYPO_PROBABILITY = 0.025     # Chance of making a typo (0.01 = 1%)
CHARS_PER_WORD = 5          # Average characters per word

# Typo type weights (higher = more likely)
TYPO_DOUBLE_WEIGHT = 1.5      # Double-type character
TYPO_SKIP_WEIGHT = 1        # Skip character
TYPO_SWAP_WEIGHT = 1.5        # Swap two characters
TYPO_ADJACENT_WEIGHT = 2    # Type adjacent key

# Typo correction timing
TYPO_REALIZE_DELAY = 0.175    # Delay before starting to correct a typo (seconds)
TYPO_UNCORRECTED_PROBABILITY = 0.1  # Chance typo is not corrected (0.05 = 5%)

# Delayed correction weights (how many extra chars typed before noticing)
# 0 = immediate, 1 = after 1 char, 2 = after 2 chars, etc.
CORRECTION_DELAY_WEIGHTS = [75, 12.5, 6.25, 3.125, 1.5625, 1.5625]  # Up to 5 chars delay

# Pause settings for different characters
# Space pauses (between words)
PAUSE_AFTER_SPACE_PROBABILITY = 0.05  # Chance of pausing after typing a space
PAUSE_SPACE_MIN = 0.32                # Minimum pause duration for space
PAUSE_SPACE_MAX = 2.5                 # Maximum pause duration for space

# Period pauses (end of sentence)
PAUSE_AFTER_PUNCTUATION_PROBABILITY = 0.2 # Chance of pausing after typing a period
PAUSE_PUNCTUATION_MIN = .05                # Minimum pause duration for period
PAUSE_PUNCTUATION_MAX = 4                # Maximum pause duration for period

# Newline/Return pauses (end of paragraph)
PAUSE_AFTER_NEWLINE_PROBABILITY = 0.9 # Chance of pausing after typing a newline
PAUSE_NEWLINE_MIN = 2.0               # Minimum pause duration for newline
PAUSE_NEWLINE_MAX = 5.0               # Maximum pause duration for newline

# Keyboard proximity map for realistic typos
ADJACENT_KEYS = {
    "a": ["q", "w", "s", "z"],
    "b": ["v", "g", "h", "n"],
    "c": ["x", "d", "f", "v"],
    "d": ["s", "e", "r", "f", "c", "x"],
    "e": ["w", "s", "d", "r"],
    "f": ["d", "r", "t", "g", "v", "c"],
    "g": ["f", "t", "y", "h", "b", "v"],
    "h": ["g", "y", "u", "j", "n", "b"],
    "i": ["u", "j", "k", "o"],
    "j": ["h", "u", "i", "k", "n", "m"],
    "k": ["j", "i", "o", "l", "m"],
    "l": ["k", "o", "p"],
    "m": ["n", "j", "k"],
    "n": ["b", "h", "j", "m"],
    "o": ["i", "k", "l", "p"],
    "p": ["o", "l"],
    "q": ["w", "a"],
    "r": ["e", "d", "f", "t"],
    "s": ["a", "w", "e", "d", "x", "z"],
    "t": ["r", "f", "g", "y"],
    "u": ["y", "h", "j", "i"],
    "v": ["c", "f", "g", "b"],
    "w": ["q", "a", "s", "e"],
    "x": ["z", "s", "d", "c"],
    "y": ["t", "g", "h", "u"],
    "z": ["a", "s", "x"]
}

# ===== GLOBAL STATE =====
typing = False
keyboard = Controller()
text = ""
position = 0
typed_buffer = []  # Track recently typed characters for delayed corrections

def toggle_typing():
    """Toggle typing on/off and remove the backtick."""
    global typing
    typing = not typing
    time.sleep(0.01)
    keyboard.press(Key.backspace)
    keyboard.release(Key.backspace)
    print("▶ Started typing" if typing else "⏸ Paused typing")

def on_press(key):
    """Handle key press events."""
    try:
        if key.char == '`':
            toggle_typing()
    except AttributeError:
        pass

def calculate_char_delay(char_position, base_cpm):
    """Calculate delay for current character based on sine wave variation."""
    wave = math.sin(char_position * WAVE_FREQUENCY)
    speed_multiplier = (MIN_SPEED + MAX_SPEED) / 2 + wave * (MAX_SPEED - MIN_SPEED) / 2
    current_cpm = base_cpm * speed_multiplier
    return 60.0 / current_cpm

def get_correction_delay():
    """Randomly determine how many characters to type before noticing the error."""
    delays = list(range(len(CORRECTION_DELAY_WEIGHTS)))
    return random.choices(delays, weights=CORRECTION_DELAY_WEIGHTS)[0]

def backspace_and_retype(chars_to_backspace, char_delay):
    """Backspace N characters and retype them correctly."""
    global typed_buffer
    
    # Backspace
    for _ in range(chars_to_backspace):
        time.sleep(char_delay)
        keyboard.press(Key.backspace)
        keyboard.release(Key.backspace)
    
    # Get the characters that were backspaced
    chars_to_retype = typed_buffer[-chars_to_backspace:] if chars_to_backspace <= len(typed_buffer) else typed_buffer
    
    # Retype them correctly
    for char in chars_to_retype:
        time.sleep(char_delay)
        keyboard.type(char)

def simulate_typo(char, char_delay, fix=True, correction_delay=0):
    """Simulate a typing mistake: type character twice then backspace."""
    time.sleep(char_delay)
    keyboard.type(char)
    if fix:
        if correction_delay == 0:
            # Fix immediately
            time.sleep(char_delay + TYPO_REALIZE_DELAY)
            keyboard.press(Key.backspace)
            keyboard.release(Key.backspace)
            time.sleep(char_delay)
        else:
            # Will fix after typing more characters
            return correction_delay + 1  # +1 for the duplicate char
    else:
        time.sleep(char_delay)
    return 0

def simulate_skip_char(char, char_delay, fix=True, correction_delay=0):
    """Skip a character, then realize and go back to type it."""
    if fix:
        if correction_delay == 0:
            # Fix immediately
            time.sleep(char_delay + TYPO_REALIZE_DELAY)
            keyboard.type(char)
            time.sleep(char_delay)
        else:
            # Will fix after typing more characters
            return correction_delay + 1  # +1 for the missing char
    else:
        time.sleep(char_delay)
    return 0

def simulate_swap_chars(char1, char2, char_delay, fix=True, correction_delay=0):
    """Type two characters in wrong order, backspace, then type correctly."""
    time.sleep(char_delay)
    keyboard.type(char2)
    if fix:
        if correction_delay == 0:
            # Fix immediately
            time.sleep(char_delay + TYPO_REALIZE_DELAY)
            keyboard.press(Key.backspace)
            keyboard.release(Key.backspace)
            time.sleep(char_delay)
            keyboard.press(Key.backspace)
            keyboard.release(Key.backspace)
            time.sleep(char_delay)
            keyboard.type(char1)
            time.sleep(char_delay)
            keyboard.type(char2)
            time.sleep(char_delay)
        else:
            # Will fix after typing more characters
            return correction_delay + 2  # +2 for both swapped chars
    else:
        time.sleep(char_delay)
    return 0

def simulate_adjacent_typo(char, char_delay, fix=True, correction_delay=0):
    """Type an adjacent key by mistake, then backspace and correct."""
    char_lower = char.lower()
    if char_lower in ADJACENT_KEYS:
        wrong_char = random.choice(ADJACENT_KEYS[char_lower])
        # Preserve case
        if char.isupper():
            wrong_char = wrong_char.upper()
        
        time.sleep(char_delay)
        keyboard.type(wrong_char)
        if fix:
            if correction_delay == 0:
                # Fix immediately
                time.sleep(char_delay + TYPO_REALIZE_DELAY)
                keyboard.press(Key.backspace)
                keyboard.release(Key.backspace)
                time.sleep(char_delay)
                keyboard.type(char)
                time.sleep(char_delay)
            else:
                # Will fix after typing more characters
                return correction_delay + 1  # +1 for the wrong char
        else:
            time.sleep(char_delay)
    else:
        # Fallback to double-type if char not in map
        return simulate_typo(char, char_delay, fix, correction_delay)
    return 0

def pause_after_space():
    """Simulate a thinking pause after typing a space with linear probability weighting."""
    pause_duration = random.triangular(PAUSE_SPACE_MIN, PAUSE_SPACE_MAX, PAUSE_SPACE_MAX)
    time.sleep(pause_duration)

def pause_after_period():
    """Simulate a thinking pause after typing a period with linear probability weighting."""
    pause_duration = random.triangular(PAUSE_PUNCTUATION_MIN, PAUSE_PUNCTUATION_MAX, PAUSE_PUNCTUATION_MAX)
    time.sleep(pause_duration)

def pause_after_newline():
    """Simulate a thinking pause after typing a newline with linear probability weighting."""
    pause_duration = random.triangular(PAUSE_NEWLINE_MIN, PAUSE_NEWLINE_MAX, PAUSE_NEWLINE_MAX)
    time.sleep(pause_duration)

def main():
    global text, position, typed_buffer
    
    text = pyperclip.paste()
    if not text:
        print("No text in clipboard!")
        return
    
    print(f"Loaded {len(text)} characters from clipboard")
    print(f"Speed: {WPM} WPM")
    print("\nPress ` to start/stop typing")
    
    listener = Listener(on_press=on_press)
    listener.start()
    
    base_cpm = WPM * CHARS_PER_WORD
    pending_correction = 0  # Number of chars to backspace for delayed correction
    in_correction_mode = False  # Flag to prevent typos during corrections
    
    while position < len(text):
        if typing:
            char_delay = calculate_char_delay(position, base_cpm)
            
            # Check if we need to do a delayed correction
            if pending_correction > 0:
                in_correction_mode = True
                time.sleep(char_delay + TYPO_REALIZE_DELAY)
                backspace_and_retype(pending_correction, char_delay)
                pending_correction = 0
                in_correction_mode = False
                continue
            
            keyboard.type(text[position])
            current_char = text[position]
            typed_buffer.append(current_char)
            position += 1
            time.sleep(char_delay)
            
            # Check if we should pause based on character type
            if current_char == ' ' and random.random() < PAUSE_AFTER_SPACE_PROBABILITY:
                pause_after_space()
            elif current_char in './;:()?!' and random.random() < PAUSE_AFTER_PUNCTUATION_PROBABILITY:
                pause_after_period()
            elif current_char == '\n' and random.random() < PAUSE_AFTER_NEWLINE_PROBABILITY:
                pause_after_newline()
            
            # Randomly make a typo (but not when correcting another typo)
            if not in_correction_mode and random.random() < TYPO_PROBABILITY:
                # Decide if typo will be corrected
                fix_typo = random.random() >= TYPO_UNCORRECTED_PROBABILITY
                correction_delay = get_correction_delay() if fix_typo else 0
                
                # Weighted random choice of typo type
                typo_types = ['double', 'skip', 'swap', 'adjacent']
                typo_weights = [TYPO_DOUBLE_WEIGHT, TYPO_SKIP_WEIGHT, TYPO_SWAP_WEIGHT, TYPO_ADJACENT_WEIGHT]
                typo_type = random.choices(typo_types, weights=typo_weights)[0]
                
                if typo_type == 'double':
                    pending_correction = simulate_typo(current_char, char_delay, fix_typo, correction_delay)
                elif typo_type == 'skip':
                    # Skip next character, then fix it
                    if position < len(text):
                        next_char = text[position]
                        position += 1
                        time.sleep(char_delay)
                        typed_buffer.append(next_char)
                        pending_correction = simulate_skip_char(next_char, char_delay, fix_typo, correction_delay)
                elif typo_type == 'swap':
                    # Swap current and next character
                    if position < len(text):
                        next_char = text[position]
                        pending_correction = simulate_swap_chars(current_char, next_char, char_delay, fix_typo, correction_delay)
                        position += 1
                        typed_buffer.append(next_char)
                elif typo_type == 'adjacent':
                    # Type adjacent key instead
                    pending_correction = simulate_adjacent_typo(current_char, char_delay, fix_typo, correction_delay)
        else:
            time.sleep(0.1)
    
    print("\n✓ Complete!")
    listener.stop()

if __name__ == "__main__":
    main()

