"""Run: python test_typing.py  (checks typos get fixed and the final text is right)"""
import random
import keyboard_simulator as ks

ks.time.sleep = lambda s: None
ks.running.set()
TEXT = "The quick brown fox jumps over the lazy dog.\nHello, World! It's 9:41 -- isn't it?\n" * 20

def run(uncorrected, proofread):
    """Type TEXT into a fake editor with a caret. Returns (editor text, arrow presses)."""
    ks.TYPO_PROBABILITY = 0.3
    ks.TYPO_UNCORRECTED_PROBABILITY = uncorrected
    ks.PROOFREAD = proofread
    doc, caret, arrows = [], 0, 0
    def press(ch, hold, repeats=1):
        nonlocal caret, arrows
        for _ in range(repeats):
            if ch == ks.LEFT:
                caret -= 1
                arrows += 1
            elif ch == '\b':
                caret -= 1
                del doc[caret]
            else:
                doc.insert(caret, ch)
                caret += 1
    out = ks.type_text(TEXT, press)
    assert ''.join(doc) == out
    return out, arrows

left_in = 0
for seed in range(200):
    random.seed(seed)
    assert run(0, False)[0] == TEXT, seed
    random.seed(seed)
    out, arrows = run(0.5, True)
    assert out == TEXT, seed           # proofread fixes every missed typo
    assert arrows > 0, seed            # and it actually had to go back for them
    random.seed(seed)
    left_in += run(0.5, False)[0] != TEXT
assert left_in > 190, left_in          # without proofreading, missed typos stay in

assert ks.key_event('A') == (dict(key='A', code='KeyA', windowsVirtualKeyCode=65, text='A'), True)
assert ks.key_event('?') == (dict(key='?', code='Slash', windowsVirtualKeyCode=191, text='?'), True)
assert ks.key_event('\n')[0]['text'] == '\r'
assert ks.key_event('é') == (dict(key='é', text='é'), False)
print("ok")
