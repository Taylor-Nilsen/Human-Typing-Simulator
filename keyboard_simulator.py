#!/usr/bin/env python3
import time
import math
import random
import pyperclip
from pynput.keyboard import Controller, Listener, Key

# ===== CONFIGURATION =====
WPM = 120                   # Base typing speed in words per minute
MIN_SPEED = 0.80            # Minimum speed multiplier (80% of base)
MAX_SPEED = 1.20            # Maximum speed multiplier (120% of base)
WAVE_FREQUENCY = 0.3        # How fast the speed oscillates (higher = faster changes)
TYPO_PROBABILITY = 0.2     # Chance of making a typo (0.01 = 1%)
CHARS_PER_WORD = 5          # Average characters per word

# Typo type weights (higher = more likely)
TYPO_DOUBLE_WEIGHT = 1      # Double-type character
TYPO_SKIP_WEIGHT = 1        # Skip character then fix
TYPO_SWAP_WEIGHT = 1        # Swap two characters
TYPO_ADJACENT_WEIGHT = 2    # Type adjacent key

# Typo correction timing
TYPO_REALIZE_DELAY = 0.1    # Delay before starting to correct a typo (seconds)

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

def simulate_typo(char, char_delay):
    """Simulate a typing mistake: type character twice then backspace."""
    keyboard.type(char)
    time.sleep(TYPO_REALIZE_DELAY)
    keyboard.press(Key.backspace)
    keyboard.release(Key.backspace)
    time.sleep(char_delay)

def simulate_skip_char(char, char_delay):
    """Skip a character, then realize and go back to type it."""
    time.sleep(TYPO_REALIZE_DELAY)
    keyboard.type(char)
    time.sleep(char_delay)

def simulate_swap_chars(char1, char2, char_delay):
    """Type two characters in wrong order, backspace, then type correctly."""
    keyboard.type(char2)
    time.sleep(TYPO_REALIZE_DELAY)
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

def simulate_adjacent_typo(char, char_delay):
    """Type an adjacent key by mistake, then backspace and correct."""
    char_lower = char.lower()
    if char_lower in ADJACENT_KEYS:
        wrong_char = random.choice(ADJACENT_KEYS[char_lower])
        # Preserve case
        if char.isupper():
            wrong_char = wrong_char.upper()
        
        keyboard.type(wrong_char)
        time.sleep(char_delay * 0.5)
        keyboard.press(Key.backspace)
        keyboard.release(Key.backspace)
        time.sleep(char_delay * 0.3)
        keyboard.type(char)
    else:
        # Fallback to double-type if char not in map
        simulate_typo(char, char_delay)

def main():
    global text, position
    
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
    
    while position < len(text):
        if typing:
            char_delay = calculate_char_delay(position, base_cpm)
            
            keyboard.type(text[position])
            current_char = text[position]
            position += 1
            time.sleep(char_delay)
            
            # Randomly make a typo
            if random.random() < TYPO_PROBABILITY:
                # Weighted random choice of typo type
                typo_types = ['double', 'skip', 'swap', 'adjacent']
                typo_weights = [TYPO_DOUBLE_WEIGHT, TYPO_SKIP_WEIGHT, TYPO_SWAP_WEIGHT, TYPO_ADJACENT_WEIGHT]
                typo_type = random.choices(typo_types, weights=typo_weights)[0]
                
                if typo_type == 'double':
                    simulate_typo(current_char, char_delay)
                elif typo_type == 'skip':
                    # Skip next character, then fix it
                    if position < len(text):
                        next_char = text[position]
                        position += 1
                        time.sleep(char_delay)
                        simulate_skip_char(next_char, char_delay)
                elif typo_type == 'swap':
                    # Swap current and next character
                    if position < len(text):
                        next_char = text[position]
                        simulate_swap_chars(current_char, next_char, char_delay)
                        position += 1
                elif typo_type == 'adjacent':
                    # Type adjacent key instead
                    simulate_adjacent_typo(current_char, char_delay)
        else:
            time.sleep(0.1)
    
    print("\n✓ Complete!")
    listener.stop()

if __name__ == "__main__":
    main()

