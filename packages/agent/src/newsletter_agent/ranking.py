from __future__ import annotations
from typing import List, Dict
from .types import Candidate

def dedupe_candidates(candidates: List[Candidate]) -> List[Candidate]:
    seen = set()
    out: List[Candidate] = []
    for c in candidates:
        key = str(c.url).lower().strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out

def simple_rank(candidates: List[Candidate], topic_weights: Dict[str, float] | None = None) -> List[Candidate]:
    # MVP heuristic:
    # - prefer items that have snippets
    # - prefer items with topic tags
    # - preserve input order otherwise
    topic_weights = topic_weights or {}
    def score(c: Candidate) -> float:
        s = 0.0
        if c.snippet:
            s += 1.0
        if c.topic_tags:
            s += 0.5
            for t in c.topic_tags:
                s += 0.2 * float(topic_weights.get(t, 0.0))
        return s
    return sorted(candidates, key=score, reverse=True)
