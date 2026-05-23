"""FastAPI app for interactive Qwirkle board/hand editing.

Run:
    python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
"""
import json
import os
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
