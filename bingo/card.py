"""
Bingo card generation logic.

Selects challenges from the pool, balances difficulty across the 5x5 grid,
and ensures category diversity.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from challenges import Challenge

# Grid positions grouped by distance from the FREE center (index 12).
_RING_CORNERS = [0, 4, 20, 24]                                      # 4  positions
_RING_EDGES = [1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23]          # 12 positions
_RING_CENTER = [6, 7, 8, 11, 13, 16, 17, 18]                        # 8  positions

_MAX_PER_CATEGORY = 6


@dataclass
class BingoCard:
    id: str
    seed: int
    squares: List[Optional[Challenge]]   # 25 items; index 12 is None (FREE)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def max_points(self) -> int:
        return sum(sq.difficulty for sq in self.squares if sq is not None)


def generate_card(
    pool: List[Challenge],
    seed: Optional[int] = None,
    easy_count: int = 8,
    medium_count: int = 10,
    hard_count: int = 6,
) -> BingoCard:
    """Generate a single 5x5 bingo card from *pool*.

    The 24 playable squares (centre is FREE) are filled with a balanced
    mix of easy / medium / hard challenges.  Harder squares are placed
    toward the corners, easier ones near the centre.
    """
    assert easy_count + medium_count + hard_count == 24

    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    rng = random.Random(seed)

    # -- partition pool by difficulty --
    easy = [c for c in pool if c.difficulty == 1]
    medium = [c for c in pool if c.difficulty == 2]
    hard = [c for c in pool if c.difficulty == 3]

    if len(easy) < easy_count:
        raise ValueError(f"Need {easy_count} easy challenges, pool has {len(easy)}")
    if len(medium) < medium_count:
        raise ValueError(f"Need {medium_count} medium challenges, pool has {len(medium)}")
    if len(hard) < hard_count:
        raise ValueError(f"Need {hard_count} hard challenges, pool has {len(hard)}")

    # -- sample with category cap --
    selected = _sample_with_category_cap(
        rng, easy, medium, hard, easy_count, medium_count, hard_count
    )

    # -- place on grid --
    squares: List[Optional[Challenge]] = [None] * 25

    by_diff = {1: [], 2: [], 3: []}
    for ch in selected:
        by_diff[ch.difficulty].append(ch)
    for v in by_diff.values():
        rng.shuffle(v)

    # Corners (4 slots) — prefer hard, then medium
    _fill_positions(squares, _RING_CORNERS, by_diff, prefer=[3, 2, 1], rng=rng)
    # Center-adjacent (8 slots) — prefer easy, then medium
    _fill_positions(squares, _RING_CENTER, by_diff, prefer=[1, 2, 3], rng=rng)
    # Edges (12 slots) — whatever remains
    _fill_positions(squares, _RING_EDGES, by_diff, prefer=[2, 1, 3], rng=rng)

    card_id = hashlib.sha256(str(seed).encode()).hexdigest()[:8]
    return BingoCard(id=card_id, seed=seed, squares=squares)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _sample_with_category_cap(
    rng: random.Random,
    easy: List[Challenge],
    medium: List[Challenge],
    hard: List[Challenge],
    easy_n: int,
    medium_n: int,
    hard_n: int,
) -> List[Challenge]:
    """Sample challenges while enforcing the per-category cap."""
    category_counts: dict[str, int] = {}
    selected: List[Challenge] = []

    for bucket, need in [(hard, hard_n), (medium, medium_n), (easy, easy_n)]:
        shuffled = bucket[:]
        rng.shuffle(shuffled)
        picked = 0
        for ch in shuffled:
            if picked >= need:
                break
            cat = ch.category
            if category_counts.get(cat, 0) >= _MAX_PER_CATEGORY:
                continue
            selected.append(ch)
            category_counts[cat] = category_counts.get(cat, 0) + 1
            picked += 1
        if picked < need:
            raise ValueError(
                f"Cannot fill {need} challenges at difficulty "
                f"{bucket[0].difficulty if bucket else '?'} "
                f"with category cap {_MAX_PER_CATEGORY}"
            )

    return selected


def _fill_positions(
    squares: List[Optional[Challenge]],
    positions: List[int],
    by_diff: dict[int, List[Challenge]],
    prefer: List[int],
    rng: random.Random,
) -> None:
    """Fill *positions* on the grid from *by_diff* buckets in preference order."""
    slots = positions[:]
    rng.shuffle(slots)
    for pos in slots:
        if squares[pos] is not None:
            continue
        for diff in prefer:
            if by_diff[diff]:
                squares[pos] = by_diff[diff].pop()
                break
