"""FastAPI app for interactive Qwirkle board/hand editing.

Run:
    python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
"""
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


class NewGamePayload(BaseModel):
    name: str


class GameIdPayload(BaseModel):
    id: str


class RenamePayload(BaseModel):
    id: str
    name: str


def _read_state() -> dict:
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


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
# usual {moves, hand} plus top-level "name"/"started". game_state.json is kept as a
# live mirror of the active game so the CLI tools (qwirkle_solver.py, sync_board.py)
# keep reading it unchanged. games/index.json = {"active": "<id>"}.


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
    return _read_state()


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
    return data


@app.post("/api/board/replace")
def replace_tile(payload: PlacePayload) -> dict:
    data = _read_state()
    found = False
    for move in data.get("moves", []):
        for t in move.get("tiles", []):
            if t["x"] == payload.x and t["y"] == payload.y:
                t["color"] = payload.color
                t["shape"] = payload.shape
                found = True
    if not found:
        raise HTTPException(status_code=404, detail=f"No tile at ({payload.x},{payload.y})")
    _atomic_write(data)
    return data


@app.post("/api/board/remove")
def remove_tile(payload: RemovePayload) -> dict:
    data = _read_state()
    removed = False
    for move in data.get("moves", []):
        before = len(move.get("tiles", []))
        move["tiles"] = [
            t for t in move.get("tiles", []) if not (t["x"] == payload.x and t["y"] == payload.y)
        ]
        if len(move["tiles"]) != before:
            removed = True
    if not removed:
        raise HTTPException(status_code=404, detail=f"No tile at ({payload.x},{payload.y})")
    data["moves"] = [m for m in data["moves"] if m.get("tiles") or m.get("n") != SETUP_KEY]
    _atomic_write(data)
    return data


@app.post("/api/hand")
def set_hand(payload: HandPayload) -> dict:
    data = _read_state()
    data["hand"] = [{"color": t.color, "shape": t.shape} for t in payload.tiles]
    _atomic_write(data)
    return data


_ALL_COLORS = ["red", "orange", "yellow", "green", "blue", "purple"]
_ALL_SHAPES = ["circle", "square", "diamond", "clover", "crossx", "star"]


def _deal_new_game(name: str) -> dict:
    bag = [{"color": c, "shape": s} for c in _ALL_COLORS for s in _ALL_SHAPES] * 3
    random.shuffle(bag)
    center, *hand_tiles = bag[:7]
    return {
        "name": name,
        "started": datetime.now().strftime("%Y-%m-%d"),
        "moves": [{"n": SETUP_KEY, "player": SETUP_KEY, "tiles": [{"x": 0, "y": 0, **center}]}],
        "hand": hand_tiles,
    }


def _activate(game_id: str) -> dict:
    """Make game_id active and mirror its file into game_state.json."""
    data = json.loads(_game_path(game_id).read_text(encoding="utf-8"))
    _set_active(game_id)
    _atomic_write(data)  # writes game_state.json + re-mirrors to the (now active) file
    return data


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
