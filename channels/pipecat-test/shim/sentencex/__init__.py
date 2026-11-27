"""Test-only stand-in: Windows Smart App Control blocks sentencex's compiled DLL on this laptop.
Splits on sentence-ending punctuation, which is all a text-only test needs."""
import re
def segment(language, text):
    for s in re.split(r"(?<=[.!?])\s+", text):
        if s:
            yield s
