from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Optional, TypedDict


COLORS = ("red", "orange", "yellow", "green", "blue", "purple")
SHAPES = ("circle", "square", "diamond", "clover", "crossX", "star")


class TilePayload(TypedDict):
    color: str
    shape: str


@dataclass(frozen=True)
class Tile:
    color: str
    shape: str


def normalize_tile(tile: Tile) -> Tile:
    return Tile(color=tile.color.lower(), shape=tile.shape)


def tile_from_payload(payload: TilePayload) -> Tile:
    return normalize_tile(Tile(color=payload["color"], shape=payload["shape"]))


def tile_to_payload(tile: Tile) -> TilePayload:
    return {"color": tile.color, "shape": tile.shape}


def hand_counter_to_payload(hand: Counter[Tile]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for tile in sorted(hand.keys(), key=lambda entry: (entry.color, entry.shape)):
        count = hand[tile]
        if count > 0:
            items.append({"tile": tile_to_payload(tile), "count": count})
    return items


def board_to_payload(board: dict[tuple[int, int], Tile]) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for (x, y), tile in sorted(board.items(), key=lambda entry: (entry[0][1], entry[0][0])):
        payload.append({"x": x, "y": y, "tile": tile_to_payload(tile)})
    return payload


class QwirkleEngine:
    def __init__(self):
        self.board: dict[tuple[int, int], Tile] = {}

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        return self.board.get((x, y))

    def has_tile(self, x: int, y: int) -> bool:
        return (x, y) in self.board

    def load_board_state(self, tiles: dict[tuple[int, int], Tile]) -> None:
        self.board = tiles.copy()

    def get_neighbors(self, x: int, y: int) -> list[Tile]:
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            tile = self.get_tile(x + dx, y + dy)
            if tile:
                neighbors.append(tile)
        return neighbors

    def get_line(self, x: int, y: int, axis: str) -> list[Tile]:
        line = []
        if axis == "horizontal":
            directions = [(1, 0), (-1, 0)]
        else:
            directions = [(0, 1), (0, -1)]

        for dx, dy in directions:
            curr_x, curr_y = x + dx, y + dy
            while (curr_x, curr_y) in self.board:
                line.append(self.board[(curr_x, curr_y)])
                curr_x += dx
                curr_y += dy

        return line

    def validate_line(self, line: list[Tile], tile: Tile) -> bool:
        if not line:
            return True

        colors = {entry.color for entry in line} | {tile.color}
        shapes = {entry.shape for entry in line} | {tile.shape}
        valid_color_run = len(colors) == 1 and len(shapes) == len(line) + 1
        valid_shape_run = len(shapes) == 1 and len(colors) == len(line) + 1
        return (valid_color_run or valid_shape_run) and len(line) < 6

    def is_legal_move(self, move: tuple[int, int], tile: Tile) -> bool:
        x, y = move
        if (x, y) in self.board:
            return False

        neighbors = self.get_neighbors(x, y)
        if self.board and not neighbors:
            return False

        for axis in ["horizontal", "vertical"]:
            line = self.get_line(x, y, axis)
            if not self.validate_line(line, tile):
                return False
        return True

    def calculate_score(self, move: tuple[int, int], tile: Tile) -> int:
        total_score = 0
        directions = [
            ("horizontal", [(1, 0), (-1, 0)]),
            ("vertical", [(0, 1), (0, -1)]),
        ]

        for axis, vectors in directions:
            del axis
            line_length = 1
            x, y = move
            for dx, dy in vectors:
                curr_x, curr_y = x + dx, y + dy
                while (curr_x, curr_y) in self.board:
                    line_length += 1
                    curr_x += dx
                    curr_y += dy

            if line_length > 1:
                total_score += line_length
                if line_length == 6:
                    total_score += 6

        return max(total_score, 1)


def try_move(engine: QwirkleEngine, move: tuple[int, int], tile: Tile) -> Optional[int]:
    if engine.is_legal_move(move, tile):
        return engine.calculate_score(move, tile)
    return None


def get_line_on_board(
    board: dict[tuple[int, int], Tile],
    x: int,
    y: int,
    axis: str,
) -> list[Tile]:
    line: list[Tile] = []
    if axis == "horizontal":
        directions = [(1, 0), (-1, 0)]
    else:
        directions = [(0, 1), (0, -1)]

    for dx, dy in directions:
        curr_x, curr_y = x + dx, y + dy
        while (curr_x, curr_y) in board:
            line.append(board[(curr_x, curr_y)])
            curr_x += dx
            curr_y += dy

    return line


def get_adjacent_empty_cells(engine: QwirkleEngine) -> set[tuple[int, int]]:
    candidates: set[tuple[int, int]] = set()
    for x, y in engine.board:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            move = (x + dx, y + dy)
            if move not in engine.board:
                candidates.add(move)
    return candidates


def get_empty_line_through(
    engine: QwirkleEngine,
    start: tuple[int, int],
    axis: str,
) -> list[tuple[int, int]]:
    x, y = start
    if axis == "horizontal":
        directions = [(1, 0), (-1, 0)]
        key_index = 0
    else:
        directions = [(0, 1), (0, -1)]
        key_index = 1

    positions = {start}
    for dx, dy in directions:
        curr_x, curr_y = x + dx, y + dy
        steps = 0
        while steps < 6 and (curr_x, curr_y) not in engine.board:
            positions.add((curr_x, curr_y))
            curr_x += dx
            curr_y += dy
            steps += 1

    return sorted(positions, key=lambda pos: pos[key_index])


def generate_connected_segments(
    engine: QwirkleEngine,
    min_len: int = 1,
    max_len: int = 6,
) -> list[tuple[tuple[int, int], ...]]:
    anchors = get_adjacent_empty_cells(engine)
    if not engine.board:
        anchors = {(0, 0)}

    segments: set[tuple[tuple[int, int], ...]] = set()
    for anchor in anchors:
        for axis in ["horizontal", "vertical"]:
            line = get_empty_line_through(engine, anchor, axis)
            if len(line) < min_len:
                continue
            for start_index in range(len(line)):
                max_end = min(len(line), start_index + max_len)
                for end_index in range(start_index + min_len - 1, max_end):
                    segment = line[start_index : end_index + 1]
                    if anchor in segment:
                        segments.add(tuple(segment))

    return list(segments)


def validate_full_line(tiles: list[Tile]) -> bool:
    if len(tiles) <= 1:
        return True

    colors = {tile.color for tile in tiles}
    shapes = {tile.shape for tile in tiles}
    valid_color_run = len(colors) == 1 and len(shapes) == len(tiles)
    valid_shape_run = len(shapes) == 1 and len(colors) == len(tiles)
    return (valid_color_run or valid_shape_run) and len(tiles) <= 6


def iter_tile_sequences(tiles: Counter[Tile], length: int) -> Iterable[tuple[Tile, ...]]:
    if length == 0:
        yield ()
        return

    for tile in list(tiles.keys()):
        if tiles[tile] == 0:
            continue
        tiles[tile] -= 1
        for suffix in iter_tile_sequences(tiles, length - 1):
            yield (tile,) + suffix
        tiles[tile] += 1


def is_legal_multi_move(
    engine: QwirkleEngine,
    placements: list[tuple[tuple[int, int], Tile]],
) -> bool:
    if not placements:
        return False

    moves = [move for move, _ in placements]
    if len(set(moves)) != len(moves):
        return False

    for move in moves:
        if move in engine.board:
            return False

    xs = {move[0] for move in moves}
    ys = {move[1] for move in moves}
    if len(xs) == 1:
        axis = "vertical"
    elif len(ys) == 1:
        axis = "horizontal"
    elif len(moves) == 1:
        axis = "horizontal"
    else:
        return False

    temp_board = engine.board.copy()
    for move, tile in placements:
        temp_board[move] = tile

    if engine.board:
        has_connection = False
        for x, y in moves:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (x + dx, y + dy) in engine.board:
                    has_connection = True
                    break
            if has_connection:
                break
        if not has_connection:
            return False

    if axis == "horizontal":
        fixed_y = moves[0][1]
        min_x = min(move[0] for move in moves)
        max_x = max(move[0] for move in moves)
        for x in range(min_x, max_x + 1):
            if (x, fixed_y) not in temp_board:
                return False
    else:
        fixed_x = moves[0][0]
        min_y = min(move[1] for move in moves)
        max_y = max(move[1] for move in moves)
        for y in range(min_y, max_y + 1):
            if (fixed_x, y) not in temp_board:
                return False

    sample_x, sample_y = moves[0]
    main_line = get_line_on_board(temp_board, sample_x, sample_y, axis)
    main_line_tiles = main_line + [temp_board[(sample_x, sample_y)]]
    if not validate_full_line(main_line_tiles):
        return False

    perpendicular = "vertical" if axis == "horizontal" else "horizontal"
    for x, y in moves:
        line = get_line_on_board(temp_board, x, y, perpendicular)
        line_tiles = line + [temp_board[(x, y)]]
        if not validate_full_line(line_tiles):
            return False

    return True


def calculate_score_multi(
    engine: QwirkleEngine,
    placements: list[tuple[tuple[int, int], Tile]],
) -> Optional[int]:
    if not is_legal_multi_move(engine, placements):
        return None

    temp_board = engine.board.copy()
    for move, tile in placements:
        temp_board[move] = tile

    moves = [move for move, _ in placements]
    xs = {move[0] for move in moves}
    axis = "vertical" if len(xs) == 1 else "horizontal"
    perpendicular = "vertical" if axis == "horizontal" else "horizontal"

    sample_x, sample_y = moves[0]
    main_length = 1 + len(get_line_on_board(temp_board, sample_x, sample_y, axis))
    total_score = 0
    if main_length > 1:
        total_score += main_length
        if main_length == 6:
            total_score += 6

    for x, y in moves:
        line_length = 1 + len(get_line_on_board(temp_board, x, y, perpendicular))
        if line_length > 1:
            total_score += line_length
            if line_length == 6:
                total_score += 6

    return max(total_score, 1)


def generate_all_multi_moves(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
) -> list[tuple[int, list[tuple[tuple[int, int], Tile]]]]:
    segments = generate_connected_segments(engine)
    results: list[tuple[int, list[tuple[tuple[int, int], Tile]]]] = []

    for segment in segments:
        for sequence in iter_tile_sequences(tiles, len(segment)):
            placements = list(zip(segment, sequence))
            score = calculate_score_multi(engine, placements)
            if score is not None:
                results.append((score, placements))

    results.sort(key=lambda item: item[0], reverse=True)
    return results


def _candidate_cells_for_pending(
    board: dict[tuple[int, int], Tile],
    pending_moves: list[tuple[int, int]],
) -> set[tuple[int, int]]:
    occupied = set(board) | set(pending_moves)
    if not board and not pending_moves:
        return {(0, 0)}

    if not pending_moves:
        candidates: set[tuple[int, int]] = set()
        for x, y in board:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                move = (x + dx, y + dy)
                if move not in occupied:
                    candidates.add(move)
        return candidates

    if len(pending_moves) == 1:
        x, y = pending_moves[0]
        return {
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        } - occupied

    xs = {x for x, _ in pending_moves}
    ys = {y for _, y in pending_moves}
    candidates = set()
    if len(xs) == 1:
        x = pending_moves[0][0]
        min_y = min(y for _, y in pending_moves)
        max_y = max(y for _, y in pending_moves)
        for y in range(min_y - 1, max_y + 2):
            move = (x, y)
            if move not in occupied:
                candidates.add(move)
    elif len(ys) == 1:
        y = pending_moves[0][1]
        min_x = min(x for x, _ in pending_moves)
        max_x = max(x for x, _ in pending_moves)
        for x in range(min_x - 1, max_x + 2):
            move = (x, y)
            if move not in occupied:
                candidates.add(move)
    return candidates


def get_legal_drop_positions(
    board: dict[tuple[int, int], Tile],
    pending: list[tuple[tuple[int, int], Tile]],
    tile: Tile,
) -> list[tuple[int, int]]:
    engine = QwirkleEngine()
    engine.load_board_state(board)
    pending_moves = [move for move, _ in pending]
    candidate_cells = _candidate_cells_for_pending(board, pending_moves)
    legal: list[tuple[int, int]] = []
    for move in sorted(candidate_cells):
        placements = pending + [(move, tile)]
        if is_legal_multi_move(engine, placements):
            legal.append(move)
    return legal


def get_board_bounds(
    board: dict[tuple[int, int], Tile],
    pending: Optional[list[tuple[tuple[int, int], Tile]]] = None,
    margin: int = 2,
) -> dict[str, int]:
    pending = pending or []
    coords = list(board.keys()) + [move for move, _ in pending]
    if not coords:
        min_x = max_x = min_y = max_y = 0
    else:
        min_x = min(x for x, _ in coords)
        max_x = max(x for x, _ in coords)
        min_y = min(y for _, y in coords)
        max_y = max(y for _, y in coords)

    return {
        "min_x": min_x - margin,
        "max_x": max_x + margin,
        "min_y": min_y - margin,
        "max_y": max_y + margin,
    }