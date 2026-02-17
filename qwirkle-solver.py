from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from itertools import product
from typing import Iterable, Optional

## History: 
# ...existing code... (keep all comments)

"""
Qwirkle is a tile-based game where players score points by creating lines of
tiles that share a common attribute (color or shape) but differ in the other.
Each tile has a color (e.g., red, orange, yellow, green, blue, purple)
and a shape (e.g., circle, square, diamond, star, clover, crossX).
"""

# ...existing code... (keep Rand. Notes and Ideas comments)

# Type aliases for readability
Coord = tuple[int, int]
Placement = tuple[Coord, Tile]
ScoredMove = tuple[int, list[Placement]]

DIRECTIONS = ((0, 1), (0, -1), (1, 0), (-1, 0))
AXIS_VECTORS: dict[str, list[Coord]] = {
    "horizontal": [(1, 0), (-1, 0)],
    "vertical": [(0, 1), (0, -1)],
}
PERPENDICULAR = {"horizontal": "vertical", "vertical": "horizontal"}
MAX_LINE_LENGTH = 6
QWIRKLE_BONUS = 6


@dataclass(frozen=True)
class Tile:
    color: str
    shape: str


class QwirkleEngine:
    def __init__(self) -> None:
        self.board: dict[Coord, Tile] = {}

    def is_legal_move(self, move: Coord, tile: Tile) -> bool:
        """Check if placing 'tile' at move follows Qwirkle rules."""
        if move in self.board:
            return False  # Can't place on an occupied space.

        if not self.get_neighbors(*move):
            return False  # Must connect to at least one existing tile.

        return all(
            self.validate_line(self.get_line(*move, axis), tile)
            for axis in AXIS_VECTORS
        )

    def validate_line(self, line: list[Tile], tile: Tile) -> bool:
        """Ensures all tiles in a row/column share one trait and differ in the other."""
        if not line:
            return True

        colors = {t.color for t in line} | {tile.color}
        shapes = {t.shape for t in line} | {tile.shape}
        n = len(line) + 1

        valid_color_run = len(colors) == 1 and len(shapes) == n
        valid_shape_run = len(shapes) == 1 and len(colors) == n

        return (valid_color_run or valid_shape_run) and len(line) < MAX_LINE_LENGTH

    def calculate_score(self, move: Coord, tile: Tile) -> int:
        """
        Calculates the total points for placing a tile at move,
        including bonuses for Qwirkles (lines of 6).
        """
        x, y = move
        total_score = sum(
            self._score_axis(x, y, vectors)
            for vectors in AXIS_VECTORS.values()
        )
        return max(total_score, 1)

    def _score_axis(self, x: int, y: int, vectors: list[Coord]) -> int:
        """Score a single axis (horizontal or vertical) for a tile placement."""
        line_length = 1  # The tile itself
        for dx, dy in vectors:
            cx, cy = x + dx, y + dy
            while (cx, cy) in self.board:
                line_length += 1
                cx += dx
                cy += dy

        if line_length <= 1:
            return 0

        bonus = QWIRKLE_BONUS if line_length == MAX_LINE_LENGTH else 0
        return line_length + bonus

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        return self.board.get((x, y))

    def has_tile(self, x: int, y: int) -> bool:
        return (x, y) in self.board

    def load_board_state(self, tiles: dict[Coord, Tile]) -> None:
        """Load board state for an in-progress game."""
        self.board = tiles.copy()

    def get_neighbors(self, x: int, y: int) -> list[Tile]:
        """Get all adjacent tiles (up, down, left, right)."""
        return [
            tile
            for dx, dy in DIRECTIONS
            if (tile := self.get_tile(x + dx, y + dy)) is not None
        ]

    def get_line(self, x: int, y: int, axis: str) -> list[Tile]:
        """Get all tiles in a line (horizontal or vertical) adjacent to (x, y)."""
        line: list[Tile] = []
        for dx, dy in AXIS_VECTORS[axis]:
            cx, cy = x + dx, y + dy
            while (cx, cy) in self.board:
                line.append(self.board[(cx, cy)])
                cx += dx
                cy += dy
        return line


def try_move(engine: QwirkleEngine, move: Coord, tile: Tile) -> Optional[int]:
    if engine.is_legal_move(move, tile):
        return engine.calculate_score(move, tile)
    return None


def get_line_on_board(
    board: dict[Coord, Tile],
    x: int,
    y: int,
    axis: str,
) -> list[Tile]:
    line: list[Tile] = []
    for dx, dy in AXIS_VECTORS[axis]:
        cx, cy = x + dx, y + dy
        while (cx, cy) in board:
            line.append(board[(cx, cy)])
            cx += dx
            cy += dy
    return line


def get_adjacent_empty_cells(engine: QwirkleEngine) -> set[Coord]:
    return {
        (x + dx, y + dy)
        for x, y in engine.board
        for dx, dy in DIRECTIONS
        if (x + dx, y + dy) not in engine.board
    }


def get_empty_line_through(
    engine: QwirkleEngine,
    start: Coord,
    axis: str,
) -> list[Coord]:
    x, y = start
    key_index = 0 if axis == "horizontal" else 1

    positions = {start}
    for dx, dy in AXIS_VECTORS[axis]:
        cx, cy = x + dx, y + dy
        for _ in range(MAX_LINE_LENGTH):
            if (cx, cy) in engine.board:
                break
            positions.add((cx, cy))
            cx += dx
            cy += dy

    return sorted(positions, key=lambda pos: pos[key_index])


def generate_connected_segments(
    engine: QwirkleEngine,
    min_len: int = 1,
    max_len: int = MAX_LINE_LENGTH,
) -> list[tuple[Coord, ...]]:
    anchors = get_adjacent_empty_cells(engine)
    segments: set[tuple[Coord, ...]] = set()

    for anchor in anchors:
        for axis in AXIS_VECTORS:
            line = get_empty_line_through(engine, anchor, axis)
            if len(line) < min_len:
                continue
            for i in range(len(line)):
                for j in range(i + min_len - 1, min(len(line), i + max_len)):
                    segment = tuple(line[i : j + 1])
                    if anchor in segment:
                        segments.add(segment)

    return list(segments)


def validate_full_line(tiles: list[Tile]) -> bool:
    if len(tiles) <= 1:
        return True

    colors = {t.color for t in tiles}
    shapes = {t.shape for t in tiles}
    n = len(tiles)

    valid_color_run = len(colors) == 1 and len(shapes) == n
    valid_shape_run = len(shapes) == 1 and len(colors) == n

    return (valid_color_run or valid_shape_run) and n <= MAX_LINE_LENGTH


def iter_tile_sequences(tiles: Counter[Tile], length: int) -> Iterable[tuple[Tile, ...]]:
    if length == 0:
        yield ()
        return

    for tile in list(tiles):
        if tiles[tile] <= 0:
            continue
        tiles[tile] -= 1
        for suffix in iter_tile_sequences(tiles, length - 1):
            yield (tile, *suffix)
        tiles[tile] += 1


def _has_board_connection(engine: QwirkleEngine, moves: list[Coord]) -> bool:
    """Check if any placement is adjacent to an existing board tile."""
    return any(
        (x + dx, y + dy) in engine.board
        for x, y in moves
        for dx, dy in DIRECTIONS
    )


def _is_contiguous(temp_board: dict[Coord, Tile], moves: list[Coord], axis: str) -> bool:
    """Check that the placed tiles form a contiguous line with no gaps."""
    if axis == "horizontal":
        fixed = moves[0][1]
        min_v, max_v = min(m[0] for m in moves), max(m[0] for m in moves)
        return all((v, fixed) in temp_board for v in range(min_v, max_v + 1))
    else:
        fixed = moves[0][0]
        min_v, max_v = min(m[1] for m in moves), max(m[1] for m in moves)
        return all((fixed, v) in temp_board for v in range(min_v, max_v + 1))


def is_legal_multi_move(
    engine: QwirkleEngine,
    placements: list[Placement],
) -> bool:
    if not placements:
        return False

    moves = [move for move, _ in placements]

    # Check for duplicate or occupied positions
    if len(set(moves)) != len(moves) or any(m in engine.board for m in moves):
        return False

    # Determine axis — all tiles must share a row or column
    xs = {m[0] for m in moves}
    ys = {m[1] for m in moves}
    match len(xs) == 1, len(ys) == 1:
        case True, _:
            axis = "vertical"
        case _, True:
            axis = "horizontal"
        case _:
            return False

    temp_board = engine.board | dict(placements)

    # Must connect to existing board (unless first move)
    if engine.board and not _has_board_connection(engine, moves):
        return False

    # Check contiguity
    if not _is_contiguous(temp_board, moves, axis):
        return False

    # Validate main line
    sx, sy = moves[0]
    main_line = [*get_line_on_board(temp_board, sx, sy, axis), temp_board[(sx, sy)]]
    if not validate_full_line(main_line):
        return False

    # Validate all perpendicular lines
    perp = PERPENDICULAR[axis]
    return all(
        validate_full_line([*get_line_on_board(temp_board, x, y, perp), temp_board[(x, y)]])
        for x, y in moves
    )


def calculate_score_multi(
    engine: QwirkleEngine,
    placements: list[Placement],
) -> Optional[int]:
    if not is_legal_multi_move(engine, placements):
        return None

    temp_board = engine.board | dict(placements)
    moves = [move for move, _ in placements]

    xs = {m[0] for m in moves}
    axis = "vertical" if len(xs) == 1 else "horizontal"
    perp = PERPENDICULAR[axis]

    def _line_score(x: int, y: int, ax: str) -> int:
        length = 1 + len(get_line_on_board(temp_board, x, y, ax))
        if length <= 1:
            return 0
        bonus = QWIRKLE_BONUS if length == MAX_LINE_LENGTH else 0
        return length + bonus

    sx, sy = moves[0]
    total_score = _line_score(sx, sy, axis) + sum(
        _line_score(x, y, perp) for x, y in moves
    )

    return max(total_score, 1)


def generate_all_multi_moves(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
) -> list[ScoredMove]:
    segments = generate_connected_segments(engine)
    results: list[ScoredMove] = []

    for segment in segments:
        for sequence in iter_tile_sequences(tiles, len(segment)):
            placements = list(zip(segment, sequence))
            if (score := calculate_score_multi(engine, placements)) is not None:
                results.append((score, placements))

    results.sort(key=lambda item: item[0], reverse=True)
    return results


# Example usage
if __name__ == "__main__":
    engine = QwirkleEngine()

    # Define some tiles already on the board
    # board for vs. tinyb (not robot)
    game_state: dict[Coord, Tile] = {
        # Possible colors: red, orange, yellow, green, blue, purple.
        # Possible shapes: circle, square, diamond, star, clover, crossX.
        (0, 0): Tile(color='red', shape='clover'),
        (0, 1): Tile(color='red', shape='crossX'),
        (1, 1): Tile(color='red', shape='circle'),
        (-1, 1): Tile(color='red', shape='diamond'),
        (-1, 2): Tile(color='blue', shape='diamond'),
        (-1, 3): Tile(color='green', shape='diamond'),
        (-1, 4): Tile(color='yellow', shape='diamond'),
        (-2, 3): Tile(color='green', shape='square'),
        (-2, 4): Tile(color='yellow', shape='square'),
        (0, 4): Tile(color='yellow', shape='circle'),
        (0, 3): Tile(color='green', shape='circle'),
        (-3, 3): Tile(color='green', shape='star'),
        (-4, 3): Tile(color='green', shape='crossX'),
        (-4, 4): Tile(color='orange', shape='crossX'),
        (-4, 2): Tile(color='red', shape='crossX'),
        (0, 5): Tile(color='blue', shape='circle'),
        (1, 5): Tile(color='green', shape='circle'),
        (1, 6): Tile(color='green', shape='square'),
        (1, 7): Tile(color='green', shape='star'),
        (2, 1): Tile(color='red', shape='clover'),
    }

    engine.load_board_state(game_state)
    my_tiles = Counter([
        # Possible colors: red, orange, yellow, green, blue, purple.
        # Possible shapes: circle, square, diamond, star, crossX, clover.
        Tile(color="purple", shape="diamond"),
        Tile(color="red", shape="square"),
        Tile(color="yellow", shape="clover"),
        Tile(color="green", shape="star"),
        Tile(color="yellow", shape="star"),
        Tile(color="blue", shape="circle"),
    ])

    all_moves = generate_all_multi_moves(engine, my_tiles)
    print(f"Total legal multi-tile moves: {len(all_moves)}")

    MULTI_TILE_THRESHOLD = 50
    top_n = 5
    for rank, (score, placements) in enumerate(all_moves[:top_n], start=1):
        placement_str = ", ".join(f"{move}: {tile}" for move, tile in placements)
        # Add trailing comma for multi-tile moves for easier copy-paste
        if len(placement_str) > MULTI_TILE_THRESHOLD:
            placement_str += ","
        print(f"Rank {rank}: {score} points -> {placement_str}")