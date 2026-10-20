#!/usr/bin/env python3
import os
import sys
import json
import time
import math
import random
import shutil
import threading
import subprocess
from urllib.request import urlopen
import pyperclip
from pynput.keyboard import Controller, Listener, Key

# ===== CONFIGURATION =====
WPM = 80                   # Base typing speed in words per minute
MIN_SPEED = 0.80            # Minimum speed multiplier (80% of base)
MAX_SPEED = 1.20            # Maximum speed multiplier (120% of base)
WAVE_FREQUENCY = 0.32        # How fast the speed oscillates (higher = faster changes)
JITTER = 0.25               # Random +/- variation on every keystroke delay (0.25 = 25%)
TYPO_PROBABILITY = 0.025     # Chance of making a typo (0.01 = 1%)
CHARS_PER_WORD = 5          # Average characters per word

# How long each key is held down (seconds). Real keys are never 0.
KEY_HOLD_MIN = 0.04
KEY_HOLD_MAX = 0.11

# Typo type weights (higher = more likely)
TYPO_DOUBLE_WEIGHT = 1.5      # Double-type character
TYPO_SKIP_WEIGHT = 1        # Skip character
TYPO_SWAP_WEIGHT = 1.5        # Swap two characters
TYPO_ADJACENT_WEIGHT = 2    # Type adjacent key

# Typo correction timing
TYPO_REALIZE_DELAY = 0.175    # Delay before starting to correct a typo (seconds)
TYPO_UNCORRECTED_PROBABILITY = 0.1  # Chance typo is missed while typing (0.05 = 5%)

# Proofreading: once the text is done, go back with the arrow keys and fix missed typos.
# False = missed typos stay in for good.
PROOFREAD = True
PROOFREAD_PAUSE_MIN = 0.8     # "Reading" pause before each fix (seconds)
PROOFREAD_PAUSE_MAX = 3.0
KEY_REPEAT_DELAY = 0.5        # Holding an arrow key: delay before it starts repeating
KEY_REPEAT_INTERVAL = 0.033   # then one move per this many seconds (~30/s, OS default)

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

# Start/pause hotkey. Works from any app.
HOTKEY = Key.f9

# Background mode types into a Chrome tab through Chrome's DevTools port, so you
# can keep using your keyboard and mouse elsewhere. False = old behaviour (types
# into whatever window is focused). Override per run with --background / --foreground.
BACKGROUND = True
CHROME_PATH = ""            # Leave empty to auto-detect Chrome
DEBUG_PORT = 9222
CHROME_PROFILE = os.path.join(os.path.expanduser("~"), ".human-typing-chrome")

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

running = threading.Event()  # set = typing, clear = paused

# ===== KEY SENDERS =====
# press(ch, hold, repeats) sends one full keystroke. '\b' means backspace, LEFT the left
# arrow. repeats > 1 holds the key down long enough to auto-repeat that many times.

LEFT = 'ArrowLeft'
OS_SPECIAL = {'\b': Key.backspace, '\n': Key.enter, '\t': Key.tab, LEFT: Key.left}

def repeat_wait(r):
    time.sleep(KEY_REPEAT_DELAY if r == 0 else KEY_REPEAT_INTERVAL)

def make_os_press():
    """Real OS keystrokes into the focused window."""
    keyboard = Controller()
    def press(ch, hold, repeats=1):
        k = OS_SPECIAL.get(ch, ch)
        keyboard.press(k)
        for r in range(repeats - 1):
            repeat_wait(r)
            keyboard.press(k)
        time.sleep(hold)
        keyboard.release(k)
    return press

# US layout, so the page sees the same key/code/keyCode a real keyboard sends.
SHIFTED = dict(zip('~!@#$%^&*()_+{}|:"<>?', '`1234567890-=[]\\;\',./'))
PUNCT_CODES = {'`': ('Backquote', 192), '-': ('Minus', 189), '=': ('Equal', 187),
               '[': ('BracketLeft', 219), ']': ('BracketRight', 221), '\\': ('Backslash', 220),
               ';': ('Semicolon', 186), "'": ('Quote', 222), ',': ('Comma', 188),
               '.': ('Period', 190), '/': ('Slash', 191), ' ': ('Space', 32)}
NAMED_KEYS = {'\b': ('Backspace', 8, None), '\n': ('Enter', 13, '\r'), '\t': ('Tab', 9, '\t'),
              LEFT: ('ArrowLeft', 37, None)}

def key_event(ch):
    """Return (DevTools key event fields, needs_shift) for one character."""
    if ch in NAMED_KEYS:
        name, vk, text = NAMED_KEYS[ch]
        ev = dict(key=name, code=name, windowsVirtualKeyCode=vk)
        if text:
            ev['text'] = text
        return ev, False
    base = SHIFTED.get(ch, ch.lower())
    shift = ch in SHIFTED or ch != base
    if base.isascii() and base.isalpha():
        code, vk = 'Key' + base.upper(), ord(base.upper())
    elif base.isascii() and base.isdigit():
        code, vk = 'Digit' + base, ord(base)
    elif base in PUNCT_CODES:
        code, vk = PUNCT_CODES[base]
    else:
        return dict(key=ch, text=ch), False  # no key for it on a US keyboard (é, “, —)
    return dict(key=ch, code=code, windowsVirtualKeyCode=vk, text=ch), shift

class Tab:
    """Minimal Chrome DevTools connection to one tab."""
    def __init__(self, ws_url):
        import websocket
        self.ws = websocket.create_connection(ws_url, suppress_origin=True)
        self.n = 0

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                return msg.get("result", {})

def make_tab_press(tab):
    """Trusted key events straight into one Chrome tab, focused or not."""
    shift_key = dict(key='Shift', code='ShiftLeft', windowsVirtualKeyCode=16)
    def press(ch, hold, repeats=1):
        ev, shift = key_event(ch)
        mods = 8 if shift else 0
        if shift:
            tab.call('Input.dispatchKeyEvent', type='rawKeyDown', modifiers=8, **shift_key)
        down = 'keyDown' if 'text' in ev else 'rawKeyDown'
        tab.call('Input.dispatchKeyEvent', type=down, modifiers=mods, **ev)
        for r in range(repeats - 1):
            repeat_wait(r)
            tab.call('Input.dispatchKeyEvent', type=down, modifiers=mods, autoRepeat=True, **ev)
        time.sleep(hold)
        ev.pop('text', None)
        tab.call('Input.dispatchKeyEvent', type='keyUp', modifiers=mods, **ev)
        if shift:
            tab.call('Input.dispatchKeyEvent', type='keyUp', **shift_key)
    return press

def find_chrome():
    candidates = [
        CHROME_PATH,
        os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('chromium-browser'),
    ]
    return next((p for p in candidates if p and os.path.isfile(p)), None)

def devtools(path):
    return json.load(urlopen(f"http://127.0.0.1:{DEBUG_PORT}{path}", timeout=2))

def ensure_chrome():
    """Reuse a Chrome already on the debug port, otherwise launch one."""
    try:
        devtools("/json/version")
        return
    except OSError:
        pass
    exe = find_chrome()
    if not exe:
        sys.exit("Couldn't find Chrome. Set CHROME_PATH at the top of the script.")
    # Chrome refuses the debug port on your normal profile, so this uses its own.
    # Sign in to Google there once and it stays signed in.
    subprocess.Popen([exe, f"--remote-debugging-port={DEBUG_PORT}",
                      f"--user-data-dir={CHROME_PROFILE}"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(150):
        try:
            devtools("/json/version")
            return
        except OSError:
            time.sleep(0.1)
    sys.exit("Chrome started but its debug port never came up.")

def focused_tab():
    """The tab you were in when you hit the hotkey, or None."""
    for t in devtools("/json/list"):
        if t.get("type") != "page" or "webSocketDebuggerUrl" not in t:
            continue
        tab = Tab(t["webSocketDebuggerUrl"])
        r = tab.call("Runtime.evaluate", expression="document.hasFocus()")
        if r.get("result", {}).get("value"):
            # Keep the page thinking it has focus after you click away.
            tab.call("Emulation.setFocusEmulationEnabled", enabled=True)
            return tab
        tab.ws.close()
    return None

# ===== TYPING =====

def calculate_char_delay(char_position, base_cpm):
    """Delay for the current character: sine wave speed plus random jitter."""
    wave = math.sin(char_position * WAVE_FREQUENCY)
    speed_multiplier = (MIN_SPEED + MAX_SPEED) / 2 + wave * (MAX_SPEED - MIN_SPEED) / 2
    current_cpm = base_cpm * speed_multiplier
    return 60.0 / current_cpm * random.uniform(1 - JITTER, 1 + JITTER)

def get_correction_delay():
    """Randomly determine how many characters to type before noticing the error."""
    delays = list(range(len(CORRECTION_DELAY_WEIGHTS)))
    return random.choices(delays, weights=CORRECTION_DELAY_WEIGHTS)[0]

def make_typo(text, i):
    """Return (wrong keys to type, next index into text) for a typo at text[i]."""
    c = text[i]
    kind = random.choices(['double', 'skip', 'swap', 'adjacent'],
                          weights=[TYPO_DOUBLE_WEIGHT, TYPO_SKIP_WEIGHT,
                                   TYPO_SWAP_WEIGHT, TYPO_ADJACENT_WEIGHT])[0]
    if kind == 'skip':
        return [], i + 1
    if kind == 'swap' and i + 1 < len(text) and text[i + 1].isalpha():
        return [text[i + 1], c], i + 2
    if kind == 'adjacent' and c.lower() in ADJACENT_KEYS:
        wrong = random.choice(ADJACENT_KEYS[c.lower()])
        return [wrong.upper() if c.isupper() else wrong], i + 1
    return [c, c], i + 1

def pause_after(c):
    """Thinking pauses. Triangular with mode at max, so longer pauses are more likely."""
    if c == ' ' and random.random() < PAUSE_AFTER_SPACE_PROBABILITY:
        time.sleep(random.triangular(PAUSE_SPACE_MIN, PAUSE_SPACE_MAX, PAUSE_SPACE_MAX))
    elif c in './;:()?!' and random.random() < PAUSE_AFTER_PUNCTUATION_PROBABILITY:
        time.sleep(random.triangular(PAUSE_PUNCTUATION_MIN, PAUSE_PUNCTUATION_MAX, PAUSE_PUNCTUATION_MAX))
    elif c == '\n' and random.random() < PAUSE_AFTER_NEWLINE_PROBABILITY:
        time.sleep(random.triangular(PAUSE_NEWLINE_MIN, PAUSE_NEWLINE_MAX, PAUSE_NEWLINE_MAX))

def type_text(text, press):
    """Type text with human timing and typos. Returns what actually ended up typed."""
    text = list(text)
    screen = []      # what has actually been typed so far
    i = 0            # next index of text to type
    notice = None    # keystrokes left before the pending typo gets noticed
    missed = []      # (start, wrong, right) typos left in for the proofread
    base_cpm = WPM * CHARS_PER_WORD

    def key(ch):
        delay = calculate_char_delay(len(screen), base_cpm)
        hold = random.uniform(KEY_HOLD_MIN, KEY_HOLD_MAX)
        press(ch, hold)
        time.sleep(max(0, delay - hold))

    while i < len(text) or screen != text:
        running.wait()

        if notice == 0 or (notice is not None and i >= len(text)):
            # Noticed the mistake: backspace to the last correct character, carry on from there.
            time.sleep(TYPO_REALIZE_DELAY)
            while screen != text[:len(screen)]:
                key('\b')
                screen.pop()
            i = len(screen)
            notice = None
            continue

        c = text[i]
        if notice is None and c.isalpha() and random.random() < TYPO_PROBABILITY:
            start = i
            wrong, i = make_typo(text, i)
            for ch in wrong:
                key(ch)
                screen.append(ch)
            if random.random() < TYPO_UNCORRECTED_PROBABILITY:
                if wrong != text[start:i]:
                    missed.append((start, wrong, text[start:i]))
                text = screen + text[i:]   # leave it; the typo is now part of the text
                i = len(screen)
            else:
                notice = get_correction_delay()
            continue

        key(c)
        screen.append(c)
        i += 1
        if notice is not None:
            notice -= 1
        pause_after(c)

    if PROOFREAD:
        # Walk back from the end with the left arrow, fixing missed typos last to first,
        # so fixing one never shifts the position of the ones still ahead.
        # ponytail: counts one arrow press per character. Apps that rewrite text as you
        # type (Docs turning "1. " into a list) shift positions and throw this off.
        caret = len(screen)
        for start, wrong, right in reversed(missed):
            running.wait()
            time.sleep(random.uniform(PROOFREAD_PAUSE_MIN, PROOFREAD_PAUSE_MAX))
            n = caret - (start + len(wrong))
            if n > 4:
                press(LEFT, random.uniform(KEY_HOLD_MIN, KEY_HOLD_MAX), n)  # hold it down
            else:
                for _ in range(n):
                    key(LEFT)
            time.sleep(TYPO_REALIZE_DELAY)
            for _ in wrong:
                key('\b')
            for ch in right:
                key(ch)
            screen[start:start + len(wrong)] = right
            caret = start + len(right)

    return ''.join(screen)

def main():
    background = BACKGROUND
    if '--foreground' in sys.argv:
        background = False
    if '--background' in sys.argv:
        background = True

    text = pyperclip.paste().replace('\r\n', '\n')
    if not text:
        print("No text in clipboard!")
        return

    print(f"Loaded {len(text)} characters from clipboard")
    print(f"Speed: {WPM} WPM")

    def on_press(k):
        if k == HOTKEY:
            if running.is_set():
                running.clear()
                print("⏸ Paused typing")
            else:
                running.set()
                print("▶ Started typing")

    listener = Listener(on_press=on_press)
    listener.start()

    if background:
        ensure_chrome()
        print("\nIn the Chrome window this opened: open your doc, click where the text should go,")
        print("then press F9. After that you can use anything else. F9 again pauses/resumes.")
        while True:
            running.wait()
            tab = focused_tab()
            if tab:
                break
            running.clear()
            print("No focused Chrome tab found. Click into the doc in that Chrome window, then press F9.")
        press = make_tab_press(tab)
    else:
        print("\nClick into the target app and press F9 to start/stop typing")
        press = make_os_press()

    type_text(text, press)
    print("\n✓ Complete!")
    listener.stop()

if __name__ == "__main__":
    main()
