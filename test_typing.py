"""Run: python test_typing.py  (checks typos always get fixed and the final text is right)"""
import random
import keyboard_simulator as ks

ks.time.sleep = lambda s: None
ks.running.set()
TEXT = "The quick brown fox jumps over the lazy dog.\nHello, World! It's 9:41 -- isn't it?\n" * 20

def run(uncorrected):
    ks.TYPO_PROBABILITY = 0.3
    ks.TYPO_UNCORRECTED_PROBABILITY = uncorrected
    screen = []
    def press(ch, hold):
        screen.pop() if ch == '\b' else screen.append(ch)
    out = ks.type_text(TEXT, press)
    assert ''.join(screen) == out
    return out

for seed in range(200):
    random.seed(seed)
    assert run(0) == TEXT, seed
    run(0.5)  # must terminate and agree with the simulated screen

assert ks.key_event('A') == (dict(key='A', code='KeyA', windowsVirtualKeyCode=65, text='A'), True)
assert ks.key_event('?') == (dict(key='?', code='Slash', windowsVirtualKeyCode=191, text='?'), True)
assert ks.key_event('\n')[0]['text'] == '\r'
assert ks.key_event('é') == (dict(key='é', text='é'), False)
print("ok")
