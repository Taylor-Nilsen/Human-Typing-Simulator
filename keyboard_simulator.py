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
WAVE_FREQUENCY = 0.1        # How fast the speed oscillates (higher = faster changes)
TYPO_PROBABILITY = 0.01     # Chance of making a typo (0.01 = 1%)
CHARS_PER_WORD = 5          # Average characters per word

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
    time.sleep(char_delay * 0.3)
    keyboard.type(char)
    time.sleep(char_delay * 0.5)
    keyboard.press(Key.backspace)
    keyboard.release(Key.backspace)
    time.sleep(char_delay * 0.2)

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
            position += 1
            time.sleep(char_delay)
            
            # Randomly make a typo
            if random.random() < TYPO_PROBABILITY:
                simulate_typo(text[position - 1], char_delay)
        else:
            time.sleep(0.1)
    
    print("\n✓ Complete!")
    listener.stop()

if __name__ == "__main__":
    main()

