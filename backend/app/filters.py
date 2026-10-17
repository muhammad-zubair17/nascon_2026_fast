import re

JUNK_PATTERNS = [
    r"\bquiz(zes)?\b",
    r"\bthe download\b",
    r"\broundtable\b",
    r"\bnewsletter\b",
    r"\bwho am i\b",
    r"\bcrossword\b",
    r"\bpuzzle\b",
    r"\bhoroscope\b",
    r"\bpodcast\b",
    r"\bsponsored\b",
    r"\bplus today'?s other\b",
]
_JUNK_RE = re.compile("|".join(JUNK_PATTERNS), re.IGNORECASE)


def is_junk(title: str, summary: str = "") -> bool:
    """True for quizzes, newsletters, puzzles and other non-news items."""
    return bool(_JUNK_RE.search(title or ""))