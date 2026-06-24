"""Small Chinese numeral parser for common shopping amounts."""

from __future__ import annotations

CHINESE_DIGITS = {
    "\u96f6": 0,
    "\u3007": 0,
    "\u4e00": 1,
    "\u4e8c": 2,
    "\u4e24": 2,
    "\u4e09": 3,
    "\u56db": 4,
    "\u4e94": 5,
    "\u516d": 6,
    "\u4e03": 7,
    "\u516b": 8,
    "\u4e5d": 9,
}
CHINESE_UNITS = {"\u5341": 10, "\u767e": 100, "\u5343": 1000, "\u4e07": 10000}


def parse_chinese_number(text: str) -> int | None:
    value_text = text.strip()
    if not value_text:
        return None
    total = 0
    section = 0
    number = 0
    last_unit = 1
    seen = False
    for char in value_text:
        if char in CHINESE_DIGITS:
            number = CHINESE_DIGITS[char]
            seen = True
            continue
        unit = CHINESE_UNITS.get(char)
        if unit is None:
            return None
        seen = True
        if unit == 10000:
            section = (section + number) or 1
            total += section * unit
            section = 0
        else:
            section += (number or 1) * unit
            last_unit = unit
        number = 0
    if number and last_unit >= 100:
        number *= last_unit // 10
    return total + section + number if seen else None
