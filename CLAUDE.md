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

Check requirements drift (imports vs. requirements.txt):

```powershell
.venv\Scripts\python.exe scripts\check_requirements.py
```

Enable the repo pre-commit hook (runs the same check before commits):

```powershell
git config core.hooksPath .githooks
```

If the script reports drift, update `requirements.txt` in the same change so
it stays aligned with direct runtime imports and startup dependencies.

## Architecture

### Data flow

`game_state.json` is the single source of truth for the in-progress game. Everything else reads or writes it:

```ascii
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

## Git conventions

- Always use **merge** (never rebase) when integrating branches. Full history is valued; linear history is not a goal here.
- When resolving conflicts where one branch should simply win, use `git checkout --ours` / `--theirs` per file, then `git add` and commit to complete the merge.

## Tile counting

Total tiles in a standard Qwirkle set: **108** (6 colors × 6 shapes × 3 copies each).

Tiles left in bag = `108 − board_tiles − my_hand − opponent_hands`

In a 2-player game: `108 − board_tiles − 6 (my hand) − 6 (opponent's hand)`. Never forget the opponent's hand — it is not visible but must be subtracted. The solver's `estimate_tiles_left_in_bag` ([qwirkle_solver.py:471](qwirkle_solver.py#L471)) does this correctly; always use it or replicate its logic rather than computing ad-hoc.

The late-game risk filter activates when the bag estimate drops to ≤ `LATE_GAME_BAG_THRESHOLD` (default 30).

## Move legality (two-axis rule)

A tile placed at `(x, y)` joins a line on **both** axes simultaneously if it has neighbors on both. **Every** such line — horizontal AND vertical — must independently be valid (all tiles share exactly one attribute: same color with distinct shapes, OR same shape with distinct colors, never both, never a repeat, max length 6).

When reasoning about a placement in prose, you MUST check **every adjacent occupied cell on both axes**, not just the line you are trying to extend. The common failure mode (which has happened): aiming to extend a vertical color-line, picking a tile that matches that line, but ignoring an occupied horizontal neighbor the new tile shares neither color nor shape with → **illegal**.

Concrete example of the trap: cell `(-1, 1)` sits above a vertical run of **orange** tiles `(-1,0)`…`(-1,-3)`, so an orange tile "fits" that column. But `(0,1)` holds a **blue-crossx**. Any tile placed at `(-1,1)` also forms a horizontal pair with that blue-crossx, so it must match blue-crossx on color or shape. `orange-star` matches neither → **ILLEGAL**, even though it extends the orange column perfectly. `orange-crossx` would be legal there (shares `crossx` with the blue-crossx, shares `orange` with the column).

The solver's `QwirkleEngine` placement validation and the `valid_tile_at`-style checks in analysis scripts already enforce this on both axes — trust their output over hand-eyeballed prose. Before recommending a move in prose, mentally place it and verify both axes, or just confirm against the engine.

## Blocking analysis (search depth — "poison the cell")

When asked how to deny the opponent a specific high-value cell, do NOT only consider (a) occupying that exact cell, or (b) single-tile plays next to it. A legal placement at a cell C depends on **C's neighbors on both axes**. You can make C illegal for the opponent's intended tile by **changing C's neighborhood** — most often a **multi-tile move on this turn** that drops a tile into a cell *adjacent* to C, breaking the line C relied on.

Worked example from this game: Jeanne's 9-pt `orange-crossx` at `(-1,1)` was legal because `(-1,1)` sat atop a pure-orange vertical column `(-1,0)…(-1,-3)` and beside a pure-crossx horizontal run. We **couldn't** fill `(-1,1)` ourselves (no hand tile satisfied both axes), and capping the column from above seemed impossible with one tile. The actual block was a **two-tile play**: `blue-square at (-1,2)` + `blue-circle at (0,2)`. Placing a *non-orange* tile at `(-1,2)` — directly **above** the chokepoint — means any tile later played at `(-1,1)` joins a vertical line mixing orange + blue → illegal on that axis. The chokepoint is poisoned from an adjacent cell, not occupied. (The second tile `(0,2)` makes the pair a legal blue line and adds points.)

Checklist when hunting blocks: for the target cell C and each of C's four neighbor cells N, ask "can I legally place a tile at N **this turn** (possibly as part of a multi-tile move) such that the line through C on that axis no longer admits the opponent's tile?" Enumerate **multi-tile** combinations, not just singles — the enabling move and the poisoning move may need to be placed together. Single-tile, occupy-the-cell-only reasoning under-searches and will miss real blocks.

## Conventions worth knowing

- Coordinates: `(x, y)` tuples, `+y` is up (north), `+x` is right (east). The SVG renderers flip y for screen coords (`grid_max_y - y`).
- Shape names lowercase in code (`circle`, `square`, `diamond`, `clover`, `crossx`, `star`). JSON occasionally has `crossX` (capital X) in older move entries — both the Python and JS shape dispatchers `.lower()` before matching.
- Colors: `red, orange, yellow, green, blue, purple` — exactly 6.
- The narrative comment block at the top of [qwirkle_solver.py](qwirkle_solver.py) (lines 13-133) is intentionally preserved as a journal. Don't refactor it away.
