from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from flask import Flask, jsonify, render_template, request

from qwirkle_core import (
    COLORS,
    SHAPES,
    Tile,
    board_to_payload,
    calculate_score_multi,
    generate_all_multi_moves,
    get_board_bounds,
    get_legal_drop_positions,
    hand_counter_to_payload,
    is_legal_multi_move,
    tile_from_payload,
    tile_to_payload,
)


@dataclass
class GameState:
    board: dict[tuple[int, int], Tile] = field(default_factory=dict)
    hand: Counter[Tile] = field(default_factory=Counter)


app = Flask(__name__)
STATE = GameState()


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _parse_turn_payload() -> list[tuple[tuple[int, int], Tile]]:
    payload = request.get_json(force=True, silent=False)
    raw_placements = payload.get("placements", [])
    placements: list[tuple[tuple[int, int], Tile]] = []
    for entry in raw_placements:
        move = (int(entry["x"]), int(entry["y"]))
        tile = tile_from_payload(entry["tile"])
        placements.append((move, tile))
    return placements


def _state_payload() -> dict[str, object]:
    return {
        "ok": True,
        "board": board_to_payload(STATE.board),
        "hand": hand_counter_to_payload(STATE.hand),
        "bounds": get_board_bounds(STATE.board),
        "palette": [
            {"color": color, "shape": shape}
            for color in COLORS
            for shape in SHAPES
        ],
    }


def _hand_has_tiles(placements: list[tuple[tuple[int, int], Tile]]) -> bool:
    required = Counter(tile for _, tile in placements)
    for tile, count in required.items():
        if STATE.hand[tile] < count:
            return False
    return True


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def api_state():
    return jsonify(_state_payload())


@app.post("/api/reset")
def api_reset():
    STATE.board.clear()
    STATE.hand.clear()
    return jsonify(_state_payload())


@app.post("/api/hand/add")
def api_hand_add():
    payload = request.get_json(force=True, silent=False)
    tile = tile_from_payload(payload["tile"])
    STATE.hand[tile] += 1
    return jsonify(_state_payload())


@app.post("/api/hand/remove")
def api_hand_remove():
    payload = request.get_json(force=True, silent=False)
    tile = tile_from_payload(payload["tile"])
    if STATE.hand[tile] <= 0:
        return _json_error("Tile is not in hand.")
    STATE.hand[tile] -= 1
    if STATE.hand[tile] == 0:
        del STATE.hand[tile]
    return jsonify(_state_payload())


@app.post("/api/board/place")
def api_board_place():
    payload = request.get_json(force=True, silent=False)
    move = (int(payload["x"]), int(payload["y"]))
    tile = tile_from_payload(payload["tile"])
    if move in STATE.board:
        return _json_error("That board cell is already occupied.")

    from qwirkle_core import QwirkleEngine

    engine = QwirkleEngine()
    engine.load_board_state(STATE.board)
    if not engine.is_legal_move(move, tile):
        return _json_error("That tile is not legal at this board position.")

    STATE.board[move] = tile
    return jsonify(_state_payload())


@app.post("/api/board/remove")
def api_board_remove():
    payload = request.get_json(force=True, silent=False)
    move = (int(payload["x"]), int(payload["y"]))
    if move not in STATE.board:
        return _json_error("No tile exists at that board position.")
    del STATE.board[move]
    return jsonify(_state_payload())


@app.post("/api/legal-drops")
def api_legal_drops():
    payload = request.get_json(force=True, silent=False)
    tile = tile_from_payload(payload["tile"])
    pending = []
    for entry in payload.get("placements", []):
        pending.append(((int(entry["x"]), int(entry["y"])), tile_from_payload(entry["tile"])))

    legal_positions = get_legal_drop_positions(STATE.board, pending, tile)
    return jsonify(
        {
            "ok": True,
            "positions": [{"x": x, "y": y} for x, y in legal_positions],
            "bounds": get_board_bounds(STATE.board, pending),
        }
    )


@app.post("/api/turn/preview")
def api_turn_preview():
    placements = _parse_turn_payload()
    from qwirkle_core import QwirkleEngine

    engine = QwirkleEngine()
    engine.load_board_state(STATE.board)

    is_legal = is_legal_multi_move(engine, placements)
    score = calculate_score_multi(engine, placements) if is_legal else None
    return jsonify({"ok": True, "legal": is_legal, "score": score})


@app.post("/api/turn/commit")
def api_turn_commit():
    placements = _parse_turn_payload()
    if not placements:
        return _json_error("No pending placements to commit.")
    if not _hand_has_tiles(placements):
        return _json_error("Hand does not contain all pending tiles.")

    from qwirkle_core import QwirkleEngine

    engine = QwirkleEngine()
    engine.load_board_state(STATE.board)
    if not is_legal_multi_move(engine, placements):
        return _json_error("Pending placements are not a legal move.")

    score = calculate_score_multi(engine, placements)
    used_tiles = Counter(tile for _, tile in placements)
    for tile, count in used_tiles.items():
        STATE.hand[tile] -= count
        if STATE.hand[tile] == 0:
            del STATE.hand[tile]

    for move, tile in placements:
        STATE.board[move] = tile

    payload = _state_payload()
    payload["last_score"] = score
    return jsonify(payload)


@app.get("/api/suggestions")
def api_suggestions():
    from qwirkle_core import QwirkleEngine

    engine = QwirkleEngine()
    engine.load_board_state(STATE.board)
    suggestions = []
    for score, placements in generate_all_multi_moves(engine, STATE.hand)[:8]:
        suggestions.append(
            {
                "score": score,
                "placements": [
                    {"x": move[0], "y": move[1], "tile": tile_to_payload(tile)}
                    for move, tile in placements
                ],
            }
        )
    return jsonify({"ok": True, "suggestions": suggestions})


if __name__ == "__main__":
    app.run(debug=True)