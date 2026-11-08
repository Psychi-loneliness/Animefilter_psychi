"""Parse the filter-bot card syntax used in anime groups.

Admins write things like::

    /filter "The Case Study of Vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+l16u8)
    [🗞️Update](buttonurl:https://t.me/redlineanime)

and the bot turns that into a library entry:

    title    = The Case Study of Vanitas
    language = hindi          (from the "Hindi dub" label)
    link     = https://t.me/+l16u8      (first/primary button)
    extras   = [(🗞️Update, https://t.me/redlineanime), …]

Anything the human bot understands is also accepted, in any mix:
    | hin | 🍀Hindi dub🍀        → language
    | action,shonen               → tags
    | https://t.me/+abc           → link
    | 95                          → popularity
    | lang=hindi / pop=95 / tags=…→ explicit keys
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# ---------------------------------------------------------------- primitives
# [label](buttonurl:https://t.me/+abc)   /  [label](https://t.me/+abc)
BUTTON_RE = re.compile(
    r"\[(?P<label>[^\[\]]+)\]\s*\(\s*(?:(?i:buttonurl)\s*:\s*)?(?P<url>https?://[^\s)]+)\s*\)"
)
# bare [https://t.me/+abc]
URL_BUTTON_RE = re.compile(r"\[\s*(?P<url>https?://[^\s\]]+)\s*\]")
# "quoted title" or “quoted title” or «quoted»
QUOTED_TITLE_RE = re.compile(r"""^\s*["“”'«](?P<title>.+?)["“”'»]\s*""")

LANG_WORDS = {
    "hindi": "hindi", "hin": "hindi", "hi": "hindi",
    "english": "english", "eng": "english", "en": "english",
    "multi": "any", "dual": "any", "sub": "any", "both": "any", "any": "any",
}
POPULARITY_KEYS = {"pop", "popularity", "rating", "stars", "star"}
TAG_KEYS = {"tag", "tags", "genre", "genres", "category", "categories"}
LINK_KEYS = {"link", "url", "group", "invite"}
LANG_KEYS = {"lang", "language", "audio", "dub"}
TITLE_KEYS = {"title", "name", "anime"}

# words we never expose as genre tags
STOPWORDS = {
    "update", "updates", "channel", "join", "request", "requests", "how", "to",
    "watch", "download", "telegram", "group", "gc", "link", "links", "season",
    "episodes", "episode", "available", "new", "latest", "batch", "quality",
}
FLAG_WORDS = {"hindi", "english", "hin", "eng", "dub", "sub", "multi", "dual", "hi", "en"}


@dataclass(slots=True)
class Extras:
    label: str
    url: str


@dataclass(slots=True)
class Entry:
    title: str
    language: str = "any"
    link: str = ""
    tags: list[str] = field(default_factory=list)
    popularity: int = 0
    extras: list[Extras] = field(default_factory=list)
    smart: bool = False  # came from the filter-bot card syntax

    @property
    def primary_link(self) -> str:
        return self.link or next((e.url for e in self.extras if e.url), "")

    def other_buttons(self) -> list[Extras]:
        return [e for e in self.extras if e.url != self.primary_link]


# ------------------------------------------------------------------ helpers
def lang_from(text: str) -> str | None:
    """Read a language from a label / segment, tolerating emoji and 'dub'."""
    cleaned = re.sub(r"[^\w\s]", " ", text).lower()
    words = cleaned.split()
    for word in words:
        if word in LANG_WORDS:
            return LANG_WORDS[word]
    if "dub" in words or "dubbed" in words:
        return "any"  # a dub exists but the language is not stated
    return None


def clean_tag(text: str) -> str:
    cleaned = re.sub(r"[^\w\s&+-]", " ", text).strip().lower()
    cleaned = re.sub(r"\s+", "-", cleaned).strip("-")
    return cleaned


def tags_from(label_or_segment: str) -> list[str]:
    """Extract real genre-ish tags, skipping words like 'update' or 'hindi'."""
    cleaned = re.sub(r"[^\w\s&+-]", " ", label_or_segment)
    out: list[str] = []
    for chunk in re.split(r"[,/&+]|\band\b", cleaned):
        for word in chunk.split():
            slug = clean_tag(word)
            if not slug or slug in {"dub", "dubbed", "sub", "subbed"}:
                continue
            if slug in STOPWORDS or slug in FLAG_WORDS:
                continue
            if len(slug) < 3:
                continue
            if slug not in out:
                out.append(slug)
    return out


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(i for i in items if i))


# ------------------------------------------------------------------- parser
def _language_from_many(sources: Iterable[str]) -> str:
    """hindi + hindi → hindi, hindi + english → any, nothing → any."""
    strong: list[str] = []
    weak = False
    for source in sources:
        language = lang_from(source)
        if language is None:
            continue
        if language == "any":
            weak = True
        else:
            strong.append(language)
    if strong:
        return strong[0] if len(set(strong)) == 1 else "any"
    return "any" if weak else "any"


def parse_entry(raw: str) -> Entry:
    """Parse a filter-bot card (or the human syntax) into an :class:`Entry`."""
    text = (raw or "").strip()
    # tolerate the command prefix being included ("/filter …")
    text = re.sub(r"^/\w+(@\w+)?\s*", "", text)
    entry = Entry(title="")

    # 1. buttons: [label](buttonurl:https://…)  and  [https://…]
    for m in BUTTON_RE.finditer(text):
        entry.extras.append(Extras((m.group("label") or "").strip(), m.group("url")))
    text = BUTTON_RE.sub(" ", text)
    for m in URL_BUTTON_RE.finditer(text):
        entry.extras.append(Extras("", m.group("url")))
    text = URL_BUTTON_RE.sub(" ", text)

    # 2. title: "quoted" … else everything before the first [ | newline
    match = QUOTED_TITLE_RE.match(text)
    if match:
        entry.title = match.group("title").strip()
        entry.smart = True
        text = text[match.end():]
    else:
        match = re.match(r"^\s*(.+?)\s*(?=[\[|\n]|$)", text)
        if match and match.group(1):
            entry.title = match.group(1).strip()
            text = text[match.end():]

    # 3. leftovers split on | and newlines
    segments = [seg.strip(" \t-•*") for seg in re.split(r"[|\n]", text) if seg.strip(" \t-•*")]
    tag_segments: list[str] = []
    language_sources: list[str] = [e.label for e in entry.extras if e.label]
    for seg in segments:
        keyed = re.match(r"^\s*(\w+)\s*=\s*(.+)$", seg)
        if keyed:
            key, value = keyed.group(1).lower(), keyed.group(2).strip()
            if key in LINK_KEYS:
                entry.link = entry.link or value
            elif key in LANG_KEYS:
                entry.language = lang_from(value) or entry.language
            elif key in TAG_KEYS:
                entry.tags += tags_from(value)
            elif key in POPULARITY_KEYS and value.isdigit():
                entry.popularity = int(value)
            elif key in TITLE_KEYS and value:
                entry.title = value
            continue
        low = seg.lower()
        if low.startswith(("http://", "https://", "t.me/", "@")):
            entry.link = entry.link or seg
            continue
        if entry.title and low == entry.title.lower():
            continue
        if seg.isdigit():
            entry.popularity = int(seg)
            continue
        language_sources.append(seg)
        tag_segments.append(seg)

    # 4. language: button labels carry it in the filter-bot style
    if entry.language == "any":
        entry.language = _language_from_many(language_sources)

    # 5. tags come from labels ("Action & Adventure") and leftover segments
    for label in (e.label for e in entry.extras):
        if label and lang_from(label) is None or label:
            entry.tags += tags_from(label)
    for seg in tag_segments:
        entry.tags += tags_from(seg)
    entry.tags = _dedupe(entry.tags)

    # 6. primary link = first button (that is how cards are written)
    if entry.extras and not entry.link:
        entry.link = entry.extras[0].url

    entry.title = _tidy(entry.title)
    entry.smart = entry.smart or bool(entry.extras)
    return entry


def _tidy(title: str) -> str:
    title = re.sub(r"[\[\]{}]", " ", title or "")
    title = re.sub(r"\s+", " ", title).strip(" -|:")
    # "the Case study of vanitas" -> "The Case study of vanitas"
    if title[:1].islower():
        title = title[0].upper() + title[1:]
    return title


def looks_like_card(raw: str) -> bool:
    """True when the text carries filter-bot style markup."""
    return bool(BUTTON_RE.search(raw or "") or QUOTED_TITLE_RE.match(raw or ""))


def render_preview(entry: Entry, escape=lambda s: s) -> str:
    """Human readable summary of what will be saved."""
    lines = [
        f"🎬 <b>{escape(entry.title)}</b>",
        f"🗣 language: <b>{entry.language}</b>",
    ]
    if entry.primary_link:
        lines.append(f"🔗 join link: <code>{escape(entry.primary_link)}</code>")
    if entry.tags:
        lines.append("🏷 tags: " + ", ".join(f"#{escape(t)}" for t in entry.tags))
    if entry.popularity:
        lines.append(f"⭐ popularity: {entry.popularity}")
    other = entry.other_buttons()
    if other:
        lines.append("")
        lines.append("<i>extra buttons on the card:</i>")
        for extra in other:
            lines.append(f"• {escape(extra.label or 'link')} → {escape(extra.url)}")
    return "\n".join(lines)
