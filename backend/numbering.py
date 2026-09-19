"""Tooth numbering. Stored ids are FDI two-digit text ('36'). The dentist
speaks Universal numbers on camera ('nineteen' = #19 = FDI 36).

    universal_to_fdi('19') -> '36'      fdi_to_universal('36') -> '19'
    parse_tooth('nineteen') -> '36'     parse_tooth('36') -> '36'
    spoken('36') -> 'nineteen'
"""
from __future__ import annotations

import re

# Universal 1..16 runs upper right to upper left; FDI upper right is 18..11,
# upper left is 21..28. Universal 17..32 runs lower left to lower right;
# FDI lower left is 38..31, lower right is 41..48.
_UNI_TO_FDI: dict[str, str] = {}
for u in range(1, 9):
    _UNI_TO_FDI[str(u)] = str(19 - u)            # 1->18 ... 8->11
for u in range(9, 17):
    _UNI_TO_FDI[str(u)] = str(12 + u)            # 9->21 ... 16->28
for u in range(17, 25):
    _UNI_TO_FDI[str(u)] = str(55 - u)            # 17->38 ... 24->31
for u in range(25, 33):
    _UNI_TO_FDI[str(u)] = str(16 + u)            # 25->41 ... 32->48
_FDI_TO_UNI = {v: k for k, v in _UNI_TO_FDI.items()}

_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30,
}
_SPOKEN = {v: k for k, v in _WORDS.items()}


def universal_to_fdi(n: str | int) -> str:
    return _UNI_TO_FDI[str(int(n))]


def fdi_to_universal(fdi: str | int) -> str:
    return _FDI_TO_UNI[str(int(fdi))]


def is_fdi(n: str | int) -> bool:
    return str(n) in _FDI_TO_UNI


def words_to_int(text: str) -> int | None:
    """'nineteen' -> 19, 'twenty two' -> 22, 'thirty' -> 30, '19' -> 19."""
    t = text.lower().strip().replace("-", " ")
    if t.isdigit():
        return int(t)
    parts = t.split()
    if not parts or any(p not in _WORDS for p in parts):
        return None
    if len(parts) == 1:
        return _WORDS[parts[0]]
    if len(parts) == 2 and _WORDS[parts[0]] in (20, 30) and _WORDS[parts[1]] < 10:
        return _WORDS[parts[0]] + _WORDS[parts[1]]
    return None


def parse_tooth(text: str) -> str | None:
    """Best-effort tooth id from speech or a bare number. Universal 1-32 wins
    because that is what the dentist says; a two-digit FDI code (11-48 with
    valid quadrant) is accepted when it is not a valid universal number."""
    n = words_to_int(text)
    if n is None:
        m = re.search(r"\b(\d{1,2})\b", text)
        if not m:
            return None
        n = int(m.group(1))
    if 1 <= n <= 32:
        return universal_to_fdi(n)
    if is_fdi(n):
        return str(n)
    return None


def spoken(fdi: str | int) -> str:
    """FDI '36' -> 'nineteen', for text that will be read aloud."""
    u = int(fdi_to_universal(fdi))
    if u in _SPOKEN:
        return _SPOKEN[u]
    tens, ones = (u // 10) * 10, u % 10
    return f"{_SPOKEN[tens]} {_SPOKEN[ones]}"
