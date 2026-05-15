#!/usr/bin/env python3
"""Replay all moves in order and print running scores for both players.

This helps identify where the running total diverges from the actual 
scores shown in the iOS app.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Tile:
    color: str
    shape: str


def get_line_on_board(board, x, y, axis):
    line = []
    if axis == "horizontal":
        directions = [(1, 0), (-1, 0)]
    else:
        directions = [(0, 1), (0, -1)]
    for dx, dy in directions:
        cx, cy = x + dx, y + dy
        while (cx, cy) in board:
            line.append(board[(cx, cy)])
            cx += dx
            cy += dy
    return line


def score_placement(board, placements):
    """Score a multi-tile placement against the current board state."""
    temp_board = board.copy()
    for (x, y), tile in placements:
        temp_board[(x, y)] = tile

    moves = [pos for pos, _ in placements]
    xs = {m[0] for m in moves}
    ys = {m[1] for m in moves}

    if len(moves) == 1:
        # Single tile: score both axes
        x, y = moves[0]
        total = 0
        for axis in ["horizontal", "vertical"]:
            line_len = 1 + len(get_line_on_board(temp_board, x, y, axis))
            if line_len > 1:
                total += line_len
                if line_len == 6:
                    total += 6
        return max(total, 1)

    # Multi-tile
    if len(xs) == 1:
        axis = "vertical"
    elif len(ys) == 1:
        axis = "horizontal"
    else:
        return None  # invalid

    perpendicular = "vertical" if axis == "horizontal" else "horizontal"

    sample_x, sample_y = moves[0]
    main_length = 1 + len(get_line_on_board(temp_board, sample_x, sample_y, axis))
    total = 0
    if main_length > 1:
        total += main_length
        if main_length == 6:
            total += 6

    for x, y in moves:
        line_length = 1 + len(get_line_on_board(temp_board, x, y, perpendicular))
        if line_length > 1:
            total += line_length
            if line_length == 6:
                total += 6

    return max(total, 1)


# ── Move history in chronological order ──────────────────────────────
# Each entry: (player, description, [(pos, Tile), ...])
# "me" = you, "mom" = Mom
# Player attribution is based on comments in qwirkle_solver.py.
# Moves without explicit attribution are marked with "?" for review.

move_history = [
    # The very first tiles on the board — unclear who played what first.
    # Grouping the initial cluster as best we can from the comments.
    # The game_state doesn't have perfect move-by-move ordering for early moves,
    # so we'll group the "foundation" tiles and then track from where comments start.

    # My move #1
    ("me", "mv #1: green star/clover/square row at y=1",
     [((1, 1), Tile("green", "star")),
      ((2, 1), Tile("green", "clover")),
      ((3, 1), Tile("green", "square"))]),

    # Mom's move #1
    ("mom", "Mom mv #1: yellow/purple clover at x=2",
     [((2, 0), Tile("purple", "clover")),
      ((2, -1), Tile("yellow", "clover"))]),

    # My move #2
    ("me", "mv #2: red clover at (2,-2)",
     [((2, -2), Tile("red", "clover"))]),

    # Mom's move #2
    ("mom", "Mom mv #2: green/red diamond at x=4",
     [((4, 1), Tile("green", "diamond")),
      ((4, 2), Tile("red", "diamond"))]),

    # My move #3
    ("me", "mv #3: purple/yellow diamond at x=4",
     [((4, 0), Tile("purple", "diamond")),
      ((4, -1), Tile("yellow", "diamond"))]),

    # "bad 5-tile move" — yours
    ("me", "blue/green crossX at x=0",
     [((0, 0), Tile("blue", "crossX")),
      ((0, 1), Tile("green", "crossX"))]),

    ("?", "blue diamond (4,3) + orange diamond (4,-2)",
     [((4, 3), Tile("blue", "diamond")),
      ((4, -2), Tile("orange", "diamond"))]),

    # "bad move on my part"
    ("me", "purple/blue clover at x=1 (bad move)",
     [((1, -2), Tile("purple", "clover")),
      ((1, -1), Tile("blue", "clover"))]),

    # Mom
    ("mom", "blue star/circle at y=3",
     [((5, 3), Tile("blue", "star")),
      ((6, 3), Tile("blue", "circle"))]),

    # me (mv #~10)
    ("me", "mv #~10: yellow/purple circle at x=5",
     [((5, -1), Tile("yellow", "circle")),
      ((5, 0), Tile("purple", "circle"))]),

    ("me", "mv #~10 cont: orange crossX at (0,2)",
     [((0, 2), Tile("orange", "crossX"))]),

    # mv #~11 — 1st Qwirkle!
    ("me", "mv #~11: green circle (5,1) — 1st Qwirkle! (claimed 15 pts)",
     [((5, 1), Tile("green", "circle"))]),

    ("?", "orange diamond at (-1,2)",
     [((-1, 2), Tile("orange", "diamond"))]),

    # mv #~12
    ("me", "mv #~12: orange circle/square at y=-2",
     [((5, -2), Tile("orange", "circle")),
      ((6, -2), Tile("orange", "square"))]),

    # Score checkpoint: me 52, Mom 31

    ("?", "orange clover at (7,-2)",
     [((7, -2), Tile("orange", "clover"))]),

    # mv #~13
    ("me", "mv #~13: purple clover/star at y=-1",
     [((7, -1), Tile("purple", "clover")),
      ((8, -1), Tile("purple", "star"))]),

    # Mom's move (no label says it's mine)
    ("mom", "red square at (3,2)",
     [((3, 2), Tile("red", "square"))]),

    # mv #14
    ("me", "mv #14: yellow diamond/crossX at y=3 (claimed 8 pts)",
     [((-1, 3), Tile("yellow", "diamond")),
      ((0, 3), Tile("yellow", "crossX"))]),

    # Mom(?): yellow circle/clover at y=3
    ("?", "yellow circle/clover at (-3,3),(-2,3)",
     [((-3, 3), Tile("yellow", "circle")),
      ((-2, 3), Tile("yellow", "clover"))]),

    # mv #15
    ("me", "mv #15: blue clover/diamond at y=-3",
     [((2, -3), Tile("blue", "clover")),
      ((3, -3), Tile("blue", "diamond"))]),
]


if __name__ == "__main__":
    board: dict[tuple[int, int], Tile] = {}
    my_score = 0
    mom_score = 0
    unknown_score = 0

    print(f"{'#':>3}  {'Player':<6}  {'Pts':>4}  {'Me':>4}  {'Mom':>4}  {'?':>4}  Description")
    print("-" * 80)

    for i, (player, desc, placements) in enumerate(move_history, 1):
        pts = score_placement(board, placements)

        # Add tiles to board
        for pos, tile in placements:
            board[pos] = tile

        if player == "me":
            my_score += pts
        elif player == "mom":
            mom_score += pts
        else:
            unknown_score += pts

        print(f"{i:>3}  {player:<6}  {pts:>4}  {my_score:>4}  {mom_score:>4}  {unknown_score:>4}  {desc}")

    print("-" * 80)
    print(f"Final:  me={my_score}  mom={mom_score}  unattributed={unknown_score}")
    print(f"Combined total: {my_score + mom_score + unknown_score}")
    print(f"Expected (iOS app): me=64  mom=39  total=103")
    print(f"Difference:  me={my_score - 64:+d}  mom={mom_score - 39:+d}")
