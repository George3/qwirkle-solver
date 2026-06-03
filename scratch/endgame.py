"""Read-only endgame analyzer for Game-002-vs-Jeanne.

Imports the pure engine from qwirkle_core; NEVER writes game_state.json.
Models: current board (post-block), my real hand, and Jeanne's unseen-tile
superset, to answer "can I still win or am I checkmated?".
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qwirkle_core import Tile, QwirkleEngine, generate_all_multi_moves  # noqa: E402


def load_board() -> dict[tuple[int, int], Tile]:
    data = json.loads((ROOT / "game_state.json").read_text(encoding="utf-8"))
    board: dict[tuple[int, int], Tile] = {}
    for mv in data["moves"]:
        for t in mv["tiles"]:
            board[(t["x"], t["y"])] = Tile(color=t["color"], shape=t["shape"])
    return board


def my_hand() -> Counter:
    data = json.loads((ROOT / "game_state.json").read_text(encoding="utf-8"))
    return Counter(Tile(color=t["color"], shape=t["shape"]) for t in data["hand"])


# The 8 tiles unseen by me = Jeanne's 6 + 2 in bag. Using all 8 finds her CEILING.
JEANNE_UNSEEN = Counter()
for color, shape, n in [
    ("red", "star", 1),
    ("orange", "diamond", 1),
    ("orange", "square", 1),
    ("orange", "crossx", 2),
    ("blue", "circle", 1),
    ("blue", "diamond", 1),
    ("blue", "crossx", 1),
]:
    JEANNE_UNSEEN[Tile(color, shape)] += n


def fmt(placements) -> str:
    parts = []
    for (x, y), t in placements:
        parts.append(f"({x:>2},{y:>2}) {t.color} {t.shape}")
    return "  |  ".join(parts)


def distinct_top(moves, n):
    """Dedup equivalent placements (same cells+tiles), keep highest score order."""
    seen = set()
    out = []
    for score, placements in moves:
        key = frozenset(((x, y), t.color, t.shape) for (x, y), t in placements)
        if key in seen:
            continue
        seen.add(key)
        out.append((score, placements))
        if len(out) >= n:
            break
    return out


def apply(board, placements):
    nb = dict(board)
    for m, t in placements:
        nb[m] = t
    return nb


def best_moves(board, hand):
    eng = QwirkleEngine()
    eng.load_board_state(board)
    return generate_all_multi_moves(eng, hand)


def main():
    board = load_board()
    hand = my_hand()

    print("=" * 78)
    print("MY HAND:", ", ".join(f"{t.color} {t.shape}" for t in sorted(hand, key=lambda z: (z.color, z.shape)) for _ in range(hand[t])))
    print("JEANNE UNSEEN SUPERSET (she has 6 of these 8):")
    print("   ", ", ".join(f"{t.color} {t.shape}" for t in JEANNE_UNSEEN for _ in range(JEANNE_UNSEEN[t])))
    print("=" * 78)

    # 1) My best moves on the CURRENT board (if it were my turn now)
    mine_now = distinct_top(best_moves(board, hand), 8)
    print("\n[1] MY best moves on the CURRENT board (top 8):")
    for i, (s, p) in enumerate(mine_now, 1):
        print(f"  {i:>2}. {s:>3} pts   {fmt(p)}")

    # 2) Jeanne's best moves, worst case (all 8 unseen as her hand)
    jeanne = distinct_top(best_moves(board, JEANNE_UNSEEN), 10)
    print("\n[2] JEANNE's best moves, WORST CASE (top 10):")
    for i, (s, p) in enumerate(jeanne, 1):
        print(f"  {i:>2}. {s:>3} pts   {fmt(p)}")

    # 3) For Jeanne's top distinct moves, my best reply
    print("\n[3] MY best reply after each of Jeanne's top 4 moves:")
    for i, (js, jp) in enumerate(jeanne[:4], 1):
        nb = apply(board, jp)
        reply = distinct_top(best_moves(nb, hand), 4)
        print(f"\n  Jeanne plays #{i} ({js} pts): {fmt(jp)}")
        for r, (s, p) in enumerate(reply, 1):
            print(f"      reply {r}: {s:>3} pts   {fmt(p)}")
        if reply:
            swing = reply[0][0] - js
            print(f"      -> best single-round swing (my reply - Jeanne): {swing:+d}")


if __name__ == "__main__":
    main()
