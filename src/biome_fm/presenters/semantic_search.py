from pathlib import Path

_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were",
    "in", "on", "at", "to", "for", "of", "with", "from", "by", "my", "your",
})


def extract_keywords(query: str) -> list[str]:
    return [w for w in query.lower().split() if w not in _STOPWORDS and len(w) > 1]


def score_path(path: Path, keywords: list[str]) -> int:
    name = path.name.lower()
    stem = path.stem.lower()
    return sum(1 for kw in keywords if kw in name or kw in stem)


def search_by_keywords(paths: list[Path], query: str) -> list[tuple[Path, int]]:
    kws = extract_keywords(query)
    if not kws:
        return []
    scored = [(p, score_path(p, kws)) for p in paths]
    return sorted([(p, s) for p, s in scored if s > 0], key=lambda x: -x[1])
