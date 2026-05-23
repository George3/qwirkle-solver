# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A personal Qwirkle solver/companion the author uses while playing real games (often against family on an iPad). It is heavily AI-assisted "vibe-coded" Python with a long, narrative comment history at the top of [qwirkle_solver.py](qwirkle_solver.py) that is worth skimming before non-trivial changes — it documents past decisions and dead ends.

Single-user, local-only tool. No tests, no CI, no packaging.

## Commands

All commands assume the project venv at `.venv/`:

```powershell
# Solver: prints top-ranked legal moves for the current game_state.json
.venv\Scripts\python.exe qwirkle_solver.py

# Regenerate the static board.svg from game_state.json
.venv\Scripts\python.exe sync_board.py

# Replay hardcoded move history and print running scores (debugging tool —
# its move list is INDEPENDENT of game_state.json, hardcoded inside the file)
.venv\Scripts\python.exe replay_score.py

# Interactive editor (FastAPI + browser UI) for placing tiles and editing hand
.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
# Then open http://127.0.0.1:8000/
```

Install runtime deps (only needed for the interactive editor):

```powershell
.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]"
```

## Architecture

### Data flow

`game_state.json` is the single source of truth for the in-progress game. Everything else reads or writes it:

```
                  ┌──── qwirkle_solver.py (reads → ranks legal moves)
game_state.json ──┼──── sync_board.py     (reads → writes board.svg snapshot)
                  └──── app.py / static/  (reads + mutates via FastAPI + JS UI)

replay_score.py — standalone, uses its own hardcoded move_history list,
                  does NOT touch game_state.json
```

`game_state.json` schema: `{"moves": [{"n", "player", "tiles": [{"x","y","color","shape"}, ...]}, ...], "hand": [{"color","shape"}, ...]}`.

`load_game_state` at [qwirkle_solver.py:595](qwirkle_solver.py#L595) flattens all moves into a `dict[(x,y), Tile]` and ignores `n` / `player`. This is why the interactive editor can append a synthetic `{"n": "setup", "player": "setup", "tiles": [...]}` entry without breaking the solver.

### Solver internals (qwirkle_solver.py)

- `QwirkleEngine` holds the board as `dict[(x,y), Tile]` with single-tile placement validation.
- Top-level functions `generate_connected_segments` → `iter_tile_sequences` → `calculate_score_multi` build and score every legal multi-tile placement.
- `apply_late_game_risk_filter` ([qwirkle_solver.py:536](qwirkle_solver.py#L536)) suppresses moves that leave an open 5-line for the opponent, but only when the bag is low (`LATE_GAME_BAG_THRESHOLD = 30`) and a comparable safer alternative exists (within `SAFE_ALTERNATIVE_SCORE_GAP = 2`).

### Interactive editor (app.py + static/)

FastAPI backend serves:
- `GET /api/state` — returns raw `game_state.json`
- `POST /api/board/place` `{x, y, color, shape}` — appends to the single `n=="setup"` move entry (creates if missing)
- `POST /api/board/remove` `{x, y}` — removes the tile from whichever move contains it; prunes empty `setup` entry
- `POST /api/hand` `{tiles: [...]}` — replaces hand wholesale

Every mutation writes via `_atomic_write` (tmp → rename) and snapshots a timestamped `game_state.json.bak-YYYYMMDD-HHMMSS` first. Post-write, `load_game_state` is called as a sanity check.

Frontend is vanilla JS — no build step. [static/app.js](static/app.js) re-implements the SVG rendering from `sync_board.py` (`COLOR_MAP`, `drawShape`, axis layout) in the browser so click handlers can be wired without DOM-ifying the static SVG. The two renderers must stay visually consistent; if you change colors or shape geometry in one, mirror it in the other.

Backups accumulate: every mutation produces a `game_state.json.bak-*`. These are not gitignored — periodically clean them up or extend `.gitignore`.

### Backups & file naming

The `.bak` file convention (`<name>.bak-YYYYMMDD-HHMMSS`) is shared by `sync_board.py` (for `board.svg`) and `app.py` (for `game_state.json`). [rename_files.py](rename_files.py) is a one-shot historical tool that migrated old `*.bak-TIMESTAMP` names to `*-TIMESTAMP.bak` — note the *current* convention is `.bak-TIMESTAMP` (no trailing `.bak`), and the rename script reflects an earlier scheme.

## Conventions worth knowing

- Coordinates: `(x, y)` tuples, `+y` is up (north), `+x` is right (east). The SVG renderers flip y for screen coords (`grid_max_y - y`).
- Shape names lowercase in code (`circle`, `square`, `diamond`, `clover`, `crossx`, `star`). JSON occasionally has `crossX` (capital X) in older move entries — both the Python and JS shape dispatchers `.lower()` before matching.
- Colors: `red, orange, yellow, green, blue, purple` — exactly 6.
- The narrative comment block at the top of [qwirkle_solver.py](qwirkle_solver.py) (lines 13-133) is intentionally preserved as a journal. Don't refactor it away.
