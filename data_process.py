"""通用文本读取、清洗和章节解析工具。

该模块只处理文本标准化，不承载具体统计业务。后续人物、词频、情绪、
章节字数等数据处理都应优先复用这里的工具函数，避免重复清洗逻辑。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from config import DEFAULT_ENCODING
from utils.text_utils import chinese_to_int


CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
SPACE_PATTERN = re.compile(r"\s+")
SPECIAL_SYMBOL_PATTERN = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9，。！？；：“”‘’、（）《》【】\[\]\n]")
INLINE_NOTE_PATTERN = re.compile(r"〔[^〕]*〕|\[[0-9一二三四五六七八九十百○〇]+\]")
PAREN_NOTE_PATTERN = re.compile(r"（[^）]{0,40}）")
MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")

CHAPTER_RE = re.compile(
    r"^第(?P<num>[一二三四五六七八九十百○〇]+)回(?:至(?P<num_to>[一二三四五六七八九十百○〇]+)回)?\s+(?P<title>.+)$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Chapter:
    """标准章节数据对象。"""

    index: int
    title: str
    raw_title: str
    content: str
    char_count: int


def read_source_text(path: Path) -> str:
    """按项目统一编码读取 txt 文本。"""
    return path.read_text(encoding=DEFAULT_ENCODING)


def normalize_newlines(text: str) -> str:
    """统一不同系统换行符，并去除 UTF-8 BOM。"""
    return text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")


def remove_inline_notes(text: str) -> str:
    """删除正文中的批注编号、校注标记等无关内容。"""
    return INLINE_NOTE_PATTERN.sub("", text)


def remove_short_parenthetical_notes(text: str) -> str:
    """删除较短括号注释，避免注音、说明干扰文本统计。"""
    return PAREN_NOTE_PATTERN.sub("", text)


def remove_special_symbols(text: str, keep_newline: bool = True) -> str:
    """去除特殊符号，保留中文、基础标点和可读字符。"""
    cleaned = SPECIAL_SYMBOL_PATTERN.sub("\n" if keep_newline else "", text)
    return cleaned


def compact_spaces(text: str) -> str:
    """压缩所有空白字符为无空格文本。"""
    return SPACE_PATTERN.sub("", text)


def compact_newlines(text: str) -> str:
    """压缩连续空行为最多一个空行。"""
    return MULTI_NEWLINE_PATTERN.sub("\n\n", text).strip()


def clean_text(text: str, keep_newline: bool = False) -> str:
    """执行通用文本清洗流程。

    参数：
        text: 原始文本。
        keep_newline: 是否保留换行结构。章节切分后通常保留，词频统计通常不保留。
    """
    cleaned = normalize_newlines(text)
    cleaned = remove_inline_notes(cleaned)
    cleaned = remove_short_parenthetical_notes(cleaned)
    cleaned = remove_special_symbols(cleaned, keep_newline=keep_newline)
    if keep_newline:
        return compact_newlines(cleaned)
    return compact_spaces(cleaned)


def count_chinese_chars(text: str) -> int:
    """统计中文字符数量。"""
    return len(CHINESE_CHAR_PATTERN.findall(text))


def get_line_number(text: str, position: int) -> int:
    """根据字符位置计算所在行号。"""
    return text.count("\n", 0, position) + 1


def is_catalog_heading(source_text: str, heading_start: int) -> bool:
    """过滤文本开头目录区中的回目。"""
    return get_line_number(source_text, heading_start) < 420


def looks_like_body_block(raw_content: str) -> bool:
    """判断回目后是否为正文段落，过滤连续目录行。"""
    sample = raw_content[:1000]
    chinese_count = count_chinese_chars(sample)
    sentence_count = len(re.findall(r"[，。！？；：“”]", sample))
    return chinese_count > 120 and sentence_count > 8


def clean_chapter_title(title: str) -> str:
    """清理回目标题中的注释标记。"""
    return remove_inline_notes(title).strip()


def parse_chapters(source_text: str) -> list[Chapter]:
    """从全文中解析正文章节列表。

    注意：当前 txt 中“第十七回至十八回”为合并正文块，因此解析结果为
    119 个正文块，但最大回目编号仍为 120。
    """
    normalized = normalize_newlines(source_text)
    matches = [
        match
        for match in CHAPTER_RE.finditer(normalized)
        if not is_catalog_heading(normalized, match.start())
    ]

    chapters: list[Chapter] = []
    for position, match in enumerate(matches):
        next_start = matches[position + 1].start() if position + 1 < len(matches) else len(normalized)
        raw_content = normalized[match.end():next_start]
        if not looks_like_body_block(raw_content):
            continue

        number = chinese_to_int(match.group("num"))
        number_to = chinese_to_int(match.group("num_to")) if match.group("num_to") else number
        content = clean_text(raw_content, keep_newline=False)
        chapters.append(
            Chapter(
                index=number_to if number_to != number else number,
                title=clean_chapter_title(match.group("title")),
                raw_title=match.group(0).strip(),
                content=content,
                char_count=count_chinese_chars(content),
            )
        )
    return chapters

