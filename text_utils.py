"""Shared text normalization helpers."""

import re


CHINESE_NUMERAL_MAP = {
    "零": 0,
    "○": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def strip_annotations(text: str) -> str:
    """Remove editorial notes and inline annotation markers from source text."""
    text = re.sub(r"〔[^〕]*〕", "", text)
    text = re.sub(r"\[[0-9一二三四五六七八九十百]+\]", "", text)
    text = re.sub(r"（[^）]{0,30}）", "", text)
    return text


def compact_text(text: str) -> str:
    """Normalize whitespace while preserving Chinese punctuation."""
    return re.sub(r"\s+", "", text)


def chinese_to_int(value: str) -> int:
    """Convert simple Chinese chapter numerals used by the novel to integers."""
    if "○" in value or "〇" in value:
        digits = [str(CHINESE_NUMERAL_MAP.get(char, 0)) for char in value]
        return int("".join(digits))
    if len(value) > 2 and "十" not in value and "百" not in value:
        digits = [str(CHINESE_NUMERAL_MAP.get(char, 0)) for char in value]
        return int("".join(digits))
    if value == "十":
        return 10
    if "百" in value:
        left, _, right = value.partition("百")
        total = CHINESE_NUMERAL_MAP.get(left, 1) * 100
        if right:
            total += chinese_to_int(right)
        return total
    if "十" in value:
        left, _, right = value.partition("十")
        tens = CHINESE_NUMERAL_MAP.get(left, 1) * 10 if left else 10
        ones = CHINESE_NUMERAL_MAP.get(right, 0) if right else 0
        return tens + ones
    return CHINESE_NUMERAL_MAP.get(value, 0)
