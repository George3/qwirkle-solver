# Qwirkle Solver repository instructions

## Commands

This repository does not define a formal build, lint, or automated test suite. The main executable entry points are:

```powershell
# Solver: rank legal moves from the current game_state.json
.venv\Scripts\python.exe qwirkle_solver.py

# Regenerate board.svg from game_state.json
.venv\Scripts\python.exe sync_board.py

# Replay the hardcoded move history and print running scores
.venv\Scripts\python.exe replay_score.py

# Interactive board/hand editor
.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Install the editor dependencies only if you need the FastAPI UI:

```powershell
.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]"
```

There is no single-test command because there is no test runner configured; validate changes by running the specific script or server you touched.

## MCP servers

- For interactive UI work and future browser tests, prefer a Playwright MCP server against the FastAPI editor.
- Start the app with `.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000` and target `http://127.0.0.1:8000/`.
- The key UI anchors are `#board` (board SVG), `#hand` (hand SVG), `#status`, `#picker-overlay`, `#picker-title`, `#picker-grid`, `#picker-remove`, and `#picker-cancel`.
- Board interaction is SVG-based rather than form-based: empty cells are clickable `<rect>` elements inside `#board`, placed tiles are rendered into the same SVG, and tile choice happens through the picker modal.
- Tests or MCP-driven flows that mutate the UI will mutate `game_state.json` on disk and create timestamped `.bak-*` backups. Reset or replace `game_state.json` between cases instead of assuming stateless requests.

## Architecture

- `game_state.json` is the single source of truth for the live game. `qwirkle_solver.py` reads it to rank moves, `sync_board.py` reads it to regenerate `board.svg`, and `app.py` plus `static/app.js` read and mutate it through the interactive editor.
- `load_game_state()` in `qwirkle_solver.py` flattens `moves[*].tiles` into `dict[(x, y), Tile]` and ignores move metadata like `n` and `player`. That is why the editor can safely store manual board edits in a synthetic `"setup"` move.
- Solver flow in `qwirkle_solver.py`: `QwirkleEngine` handles board state and single-tile legality, then `generate_connected_segments()` enumerates candidate placement spans, `iter_tile_sequences()` permutes tiles from hand, `calculate_score_multi()` scores legal multi-tile moves, and `apply_strategy_adjustments()` re-ranks them every turn — penalizing moves that gift the opponent an open-5 Qwirkle (`gifts_opponent_qwirkle`) and rewarding holding a partial-Qwirkle set in hand (`build_bonus`).
- The FastAPI editor is stateful only through `game_state.json`. `POST /api/board/place` appends to the `"setup"` move, `POST /api/board/remove` removes tiles from whichever move owns them, and `POST /api/hand` replaces the hand. Every write goes through `_atomic_write()` (backup, temp file, rename) and then calls `load_game_state()` as a sanity check.
- `sync_board.py` and `static/app.js` intentionally duplicate tile rendering rules, color mapping, and board coordinate projection. If you change tile geometry, colors, or screen-coordinate math in one renderer, mirror the change in the other.
- `replay_score.py` is a separate debugging script. It does not read `game_state.json`; it uses its own hardcoded `move_history`.

## Key conventions

- Preserve the long narrative comment block at the top of `qwirkle_solver.py`; it is intentional project history, not cleanup fodder.
- Coordinates use `(x, y)` tuples with `+x` to the right and `+y` upward. SVG/browser rendering flips Y for display using `grid_max_y - y`.
- Use lowercase shape names in code (`circle`, `square`, `diamond`, `clover`, `crossx`, `star`). Older JSON may contain `crossX`; existing Python and JS rendering paths normalize with `.lower()`.
- The color set is fixed to exactly six names: `red`, `orange`, `yellow`, `green`, `blue`, `purple`.
- The backup naming convention is `<name>.bak-YYYYMMDD-HHMMSS`. `app.py` uses it for `game_state.json` and `sync_board.py` uses it for `board.svg`.
- The frontend is plain static HTML/CSS/JS with no build step, bundler, or framework layer.
