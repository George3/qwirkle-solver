"""FastAPI app for interactive Qwirkle board/hand editing.

Run:
    python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
"""
import copy
import json
import os
import random
import re
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from qwirkle_solver import load_game_state

ROOT = Path(__file__).parent
JSON_PATH = ROOT / "game_state.json"
GAMES_DIR = ROOT / "games"
INDEX_PATH = GAMES_DIR / "index.json"
STATIC_DIR = ROOT / "static"
SETUP_KEY = "setup"
DEFAULT_PLAYERS = ["Player 1", "Player 2"]

app = FastAPI(title="Qwirkle Interactive Editor")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class TilePayload(BaseModel):
    color: str
    shape: str


class PlacePayload(TilePayload):
    x: int
    y: int


class RemovePayload(BaseModel):
    x: int
    y: int


class HandPayload(BaseModel):
    tiles: list[TilePayload]


class PlayersPayload(BaseModel):
    players: list[str]


class NewGamePayload(BaseModel):
    name: str


class GameIdPayload(BaseModel):
    id: str


class RenamePayload(BaseModel):
    id: str
    name: str


class CommitMovePayload(BaseModel):
    player: str
    tiles: list[PlacePayload]


def _read_state() -> dict:
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def _clean_players(players: list[str] | None) -> list[str]:
    normalized = []
    for raw in players or []:
        player = str(raw).strip()
        if player and player not in normalized:
            normalized.append(player)
    return normalized


def _normalize_players(players: list[str] | None, *, fallback_moves: list[dict] | None = None) -> list[str]:
    normalized = _clean_players(players)
    if normalized:
        return normalized
    for move in fallback_moves or []:
        player = str(move.get("player", "")).strip()
        if player and player != SETUP_KEY and player not in normalized:
            normalized.append(player)
    return normalized or DEFAULT_PLAYERS.copy()


def _state_for_response(data: dict) -> dict:
    response = copy.deepcopy(data)
    response["players"] = _normalize_players(
        response.get("players"), fallback_moves=response.get("moves", [])
    )
    return response


def _find_tile_owner(data: dict, x: int, y: int) -> tuple[dict, dict] | tuple[None, None]:
    for move in data.get("moves", []):
        for tile in move.get("tiles", []):
            if tile["x"] == x and tile["y"] == y:
                return move, tile
    return None, None


def _next_move_number(data: dict) -> int:
    next_n = 1
    for move in data.get("moves", []):
        n = move.get("n")
        if n == SETUP_KEY:
            continue
        try:
            next_n = max(next_n, int(n) + 1)
        except (TypeError, ValueError):
            continue
    return next_n


def _atomic_write(data: dict) -> None:
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = JSON_PATH.with_name(f"{JSON_PATH.name}.bak-{now}")
    if JSON_PATH.exists():
        shutil.copy2(JSON_PATH, backup)
    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, JSON_PATH)
    load_game_state(JSON_PATH)
    _mirror_to_active(data)


# ─── Multi-game storage ────────────────────────────────────────────────
# Every game is its own file games/<id>_started-on-<yyyy-mm-dd>.json holding the
# usual {moves, hand} plus top-level "name"/"started"/optional "players".
# game_state.json is kept as a live mirror of the active game so the CLI tools
# (qwirkle_solver.py, sync_board.py) keep reading it unchanged.
# games/index.json = {"active": "<id>"}.


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "game"


def _unique_slug(name: str) -> str:
    base = _slugify(name)
    existing = {_id_of(p) for p in _game_files()}
    slug, i = base, 2
    while slug in existing:
        slug, i = f"{base}-{i}", i + 1
    return slug


def _game_files() -> list[Path]:
    return sorted(GAMES_DIR.glob("*_started-on-*.json"))


def _id_of(path: Path) -> str:
    return path.stem.split("_started-on-")[0]


def _game_path(game_id: str) -> Path:
    matches = list(GAMES_DIR.glob(f"{game_id}_started-on-*.json"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"No game '{game_id}'")
    return matches[0]


def _new_game_path(game_id: str, started: str) -> Path:
    return GAMES_DIR / f"{game_id}_started-on-{started}.json"


def _active_id() -> str:
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)["active"]


def _set_active(game_id: str) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump({"active": game_id}, f, indent=2)


def _write_game_file(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _mirror_to_active(data: dict) -> None:
    """Copy the just-written state into the active game's file (no .bak clutter)."""
    if INDEX_PATH.exists():
        _write_game_file(_game_path(_active_id()), data)


def _ensure_games_seeded() -> None:
    """First run: fold the existing single game_state.json into the games/ folder."""
    GAMES_DIR.mkdir(exist_ok=True)
    if _game_files():
        return
    data = _read_state()
    data.setdefault("name", "Game 1")
    data.setdefault("started", datetime.now().strftime("%Y-%m-%d"))
    game_id = _unique_slug(data["name"])
    _write_game_file(_new_game_path(game_id, data["started"]), data)
    _set_active(game_id)


def _find_or_create_setup_entry(data: dict) -> dict:
    for move in data.get("moves", []):
        if move.get("n") == SETUP_KEY:
            return move
    entry = {"n": SETUP_KEY, "player": SETUP_KEY, "tiles": []}
    data.setdefault("moves", []).append(entry)
    return entry


def _coord_exists(data: dict, x: int, y: int) -> bool:
    for move in data.get("moves", []):
        for t in move.get("tiles", []):
            if t["x"] == x and t["y"] == y:
                return True
    return False


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/state")
def get_state() -> dict:
    return _state_for_response(_read_state())


@app.post("/api/board/place")
def place_tile(payload: PlacePayload) -> dict:
    data = _read_state()
    if _coord_exists(data, payload.x, payload.y):
        raise HTTPException(status_code=409, detail=f"Tile already at ({payload.x},{payload.y})")
    entry = _find_or_create_setup_entry(data)
    entry["tiles"].append(
        {"x": payload.x, "y": payload.y, "color": payload.color, "shape": payload.shape}
    )
    _atomic_write(data)
    return _state_for_response(data)


@app.post("/api/board/replace")
def replace_tile(payload: PlacePayload) -> dict:
    data = _read_state()
    move, tile = _find_tile_owner(data, payload.x, payload.y)
    if tile is None:
        raise HTTPException(status_code=404, detail=f"No tile at ({payload.x},{payload.y})")
    if move.get("n") != SETUP_KEY:
        raise HTTPException(
            status_code=409,
            detail="Recorded move tiles are read-only. Edit only setup tiles or record a new move.",
        )
    tile["color"] = payload.color
    tile["shape"] = payload.shape
    _atomic_write(data)
    return _state_for_response(data)


@app.post("/api/board/remove")
def remove_tile(payload: RemovePayload) -> dict:
    data = _read_state()
    move, tile = _find_tile_owner(data, payload.x, payload.y)
    if tile is None:
        raise HTTPException(status_code=404, detail=f"No tile at ({payload.x},{payload.y})")
    if move.get("n") != SETUP_KEY:
        raise HTTPException(
            status_code=409,
            detail="Recorded move tiles are read-only. Remove only setup tiles or record a new move.",
        )
    move["tiles"] = [
        t for t in move.get("tiles", []) if not (t["x"] == payload.x and t["y"] == payload.y)
    ]
    data["moves"] = [m for m in data["moves"] if m.get("tiles") or m.get("n") != SETUP_KEY]
    _atomic_write(data)
    return _state_for_response(data)


@app.post("/api/hand")
def set_hand(payload: HandPayload) -> dict:
    data = _read_state()
    data["hand"] = [{"color": t.color, "shape": t.shape} for t in payload.tiles]
    _atomic_write(data)
    return _state_for_response(data)


@app.post("/api/players")
def set_players(payload: PlayersPayload) -> dict:
    players = _clean_players(payload.players)
    if not players:
        raise HTTPException(status_code=400, detail="Need at least one player name.")
    data = _read_state()
    data["players"] = players
    _atomic_write(data)
    return _state_for_response(data)


@app.post("/api/moves/commit")
def commit_move(payload: CommitMovePayload) -> dict:
    data = _read_state()
    player = payload.player.strip()
    if not player:
        raise HTTPException(status_code=400, detail="Move player cannot be blank.")
    players = _normalize_players(data.get("players"), fallback_moves=data.get("moves", []))
    if player not in players:
        raise HTTPException(
            status_code=409,
            detail=f"Unknown player '{player}'. Update this game's player list first.",
        )
    if not payload.tiles:
        raise HTTPException(status_code=400, detail="Need at least one tile to record a move.")

    seen_coords = set()
    tiles = []
    for tile in payload.tiles:
        coord = (tile.x, tile.y)
        if coord in seen_coords:
            raise HTTPException(status_code=409, detail=f"Duplicate tile coordinate {coord}.")
        if _coord_exists(data, tile.x, tile.y):
            raise HTTPException(
                status_code=409, detail=f"Tile already exists at ({tile.x},{tile.y})."
            )
        seen_coords.add(coord)
        tiles.append({"x": tile.x, "y": tile.y, "color": tile.color, "shape": tile.shape})

    data.setdefault("players", players)
    data.setdefault("moves", []).append(
        {"n": _next_move_number(data), "player": player, "tiles": tiles}
    )
    _atomic_write(data)
    return _state_for_response(data)


_ALL_COLORS = ["red", "orange", "yellow", "green", "blue", "purple"]
_ALL_SHAPES = ["circle", "square", "diamond", "clover", "crossx", "star"]


def _deal_new_game(name: str) -> dict:
    bag = [{"color": c, "shape": s} for c in _ALL_COLORS for s in _ALL_SHAPES] * 3
    random.shuffle(bag)
    center, *hand_tiles = bag[:7]
    return {
        "name": name,
        "started": datetime.now().strftime("%Y-%m-%d"),
        "players": DEFAULT_PLAYERS.copy(),
        "moves": [{"n": SETUP_KEY, "player": SETUP_KEY, "tiles": [{"x": 0, "y": 0, **center}]}],
        "hand": hand_tiles,
    }


def _activate(game_id: str) -> dict:
    """Make game_id active and mirror its file into game_state.json."""
    data = json.loads(_game_path(game_id).read_text(encoding="utf-8"))
    _set_active(game_id)
    _atomic_write(data)  # writes game_state.json + re-mirrors to the (now active) file
    return _state_for_response(data)


@app.get("/api/games")
def list_games() -> dict:
    _ensure_games_seeded()
    games = []
    for path in _game_files():
        info = json.loads(path.read_text(encoding="utf-8"))
        gid = _id_of(path)
        games.append({"id": gid, "name": info.get("name", gid), "started": info.get("started", "")})
    return {"games": games, "active": _active_id()}


@app.post("/api/games/new")
def games_new(payload: NewGamePayload) -> dict:
    _ensure_games_seeded()
    data = _deal_new_game(payload.name.strip() or "Untitled")
    game_id = _unique_slug(data["name"])
    _write_game_file(_new_game_path(game_id, data["started"]), data)
    return _activate(game_id)


@app.post("/api/games/switch")
def games_switch(payload: GameIdPayload) -> dict:
    _ensure_games_seeded()
    return _activate(payload.id)


@app.post("/api/games/rename")
def games_rename(payload: RenamePayload) -> dict:
    _ensure_games_seeded()
    path = _game_path(payload.id)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["name"] = payload.name.strip() or data.get("name", payload.id)
    _write_game_file(path, data)
    if payload.id == _active_id():
        _atomic_write(data)
    return {"id": payload.id, "name": data["name"]}


@app.post("/api/games/delete")
def games_delete(payload: GameIdPayload) -> dict:
    _ensure_games_seeded()
    path = _game_path(payload.id)
    was_active = payload.id == _active_id()
    path.unlink()
    if was_active:
        remaining = _game_files()
        if remaining:
            _activate(_id_of(remaining[0]))
        else:
            data = _deal_new_game("Game 1")
            new_id = _unique_slug(data["name"])
            _write_game_file(_new_game_path(new_id, data["started"]), data)
            _activate(new_id)
    return list_games()


_ensure_games_seeded()
