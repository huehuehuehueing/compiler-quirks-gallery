#!/usr/bin/env python3
# Copyright (c) 2026 Larry H <l.gr [at] dartmouth [dot] edu>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Compiler Optimization Gallery
# Developed for COSC-69.16: Basics of Reverse Engineering
# Dartmouth College, Winter 2026

"""
generate.py

Generates interactive HTML bingo cards with compiler-optimization challenges.

Usage:
    python bingo/generate.py [--output DIR] [--count N] [--seed INT]
                             [--difficulty easy|mixed|hard]

Each card is a self-contained HTML file with embedded CSS and JS.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError as e:
    raise SystemExit("Missing dependency: jinja2. Install with: pip install jinja2") from e

from challenges import CHALLENGE_POOL
from card import generate_card

_DIFFICULTY_PRESETS = {
    "easy":  {"easy_count": 12, "medium_count": 8, "hard_count": 4},
    "mixed": {"easy_count": 8, "medium_count": 10, "hard_count": 6},
    "hard":  {"easy_count": 4, "medium_count": 8, "hard_count": 12},
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Compiler Optimization Bingo cards as HTML files.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("bingo-cards"),
        help="Output directory for generated HTML cards (default: bingo-cards/)",
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        help="Number of cards to generate (default: 1)",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Base seed for reproducibility; subsequent cards use seed+1, seed+2, …",
    )
    parser.add_argument(
        "--difficulty", "-d",
        choices=list(_DIFFICULTY_PRESETS.keys()),
        default="mixed",
        help="Difficulty preset (default: mixed)",
    )
    args = parser.parse_args()

    # Resolve template directory relative to this script
    template_dir = Path(__file__).resolve().parent
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
    )
    template = env.get_template("template.html.j2")

    preset = _DIFFICULTY_PRESETS[args.difficulty]

    # Determine seeds
    if args.seed is not None:
        seeds = [args.seed + i for i in range(args.count)]
    else:
        rng = random.Random()
        seeds = [rng.randint(0, 2**32 - 1) for _ in range(args.count)]

    args.output.mkdir(parents=True, exist_ok=True)

    pool = list(CHALLENGE_POOL)
    generated = []

    for seed in seeds:
        card = generate_card(pool, seed=seed, **preset)
        html = template.render(card=card)
        out_path = args.output / f"bingo-{card.id}.html"
        out_path.write_text(html, encoding="utf-8")
        generated.append((card.id, out_path))
        print(f"  Card {card.id}  (seed {card.seed})  →  {out_path}")

    print(f"\nGenerated {len(generated)} card(s) in {args.output}/")


if __name__ == "__main__":
    main()
