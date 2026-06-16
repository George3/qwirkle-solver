# Another Qwirkle™ Solver

- ...but the first I've _written_[*]

> ⚠️ **Caution:** Pre-release quality. Mostly AI/LLM-generated. **Use at your own risk!**

## Intro

My first significant foray into vibe-coding(🙄)

- Fairly impressed with how well the AI agents/LLMs perform responding to my prompts to create this.

DRFT ~ FIXME = FINISH-ME:

- Using ~CoPilot Pro (Trial) $10/mo. (Upgraded from CoPilot free becase allows to use premium models like laude Opus 4.6 -- TODO check usage if "Free" would still cover it?! 💸💳)
- Most code gen'd w/Claude Haiku #.#?, Sonnet #.#?, GPT-5.3-Codex. ...Occasionally, cutting edge Claude Opus 4.6, ...Gemini -see branch on refactor.

## AI History / How-To

- To start server from: C:\src\fun\qwirkle-solver>
- One-time setup for repo hooks: `git config core.hooksPath .githooks`
- Run: `.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000`

- After prompted for 1st phase of creating an interactive GUI,
Then ran "/init" to have CLAUDE.md created.
It noted:
Globpattern: "{CLAUDE.md,.cursorrules,.cursor/rules/**,.github/copilot-instructions.md}"
No files found
Read c:\src\fun\qwirkle-solver\rename_files.py
Read c:\src\fun\qwirkle-solver\.gitignore
Write c:\src\fun\qwirkle-solver\CLAUDE.md
86 lines
Created CLAUDE.md. Key things it captures that future Claudes would otherwise have to rediscover:

game_state.json is the hub — solver, sync_board, and the new FastAPI editor all revolve around it, but replay_score.py is an exception (uses its own hardcoded history).
The "setup" move trick — why the interactive editor can append a synthetic move entry without breaking the solver.
The two SVG renderers must stay in sync — sync_board.py (Python) and static/app.js (JS) duplicate geometry/colors.
crossX capitalization quirk in older JSON entries.
The narrative comment block at the top of qwirkle_solver.py is intentional history, not cruft.
.bak-* files accumulate on every editor mutation — flagged for cleanup/gitignore.

## Game JSON notes

- Legacy board snapshots still use the synthetic move `{"n": "setup", "player": "setup", "tiles": [...]}` for freeform editor changes.
- Newly recorded turns can now be stored as real move entries with a numbered `n`, a real `player`, and that move's `tiles`.
- Top-level `players` is optional on older files and is added when you start using player-attributed move recording for a game.

## TODO

- resize board and "My Hand" to fit better on 1 screen
- asserts (aka, validation) if a chosen tile breaks any rules of game
- possibly mode features: **edit** vs. **play** modes — edit allows setting/removing any tiles including "my hand"; play mode would "use" tiles from "my hand" when they are added to the board
- a "Suggest moves" button (call `qwirkle_solver` in-process, render the top-N ranked placements as ghost overlays on the board)
- a score button (might only be available if every move is assigned to a specific player)
- **(Claude Opus suggestion)** bag/remaining-tile tracker — derive what's left in the bag from `(108 total) − (tiles on board) − (tiles in hand)` and show a 6×6 grid of remaining counts. Naturally feeds `LATE_GAME_BAG_THRESHOLD` logic and helps real-game strategy (knowing if the last `purple star` is still out there)
- **(Claude Opus suggestion)** undo/redo using the existing `game_state.json.bak-*` snapshots — they're already written on every mutation, so a `POST /api/undo` that restores the most-recent backup is nearly free and rescues the "oops, wrong click" case
- run many fully automated game simulations (solver vs. solver) to empirically find the optimal value for `LATE_GAME_BAG_THRESHOLD` in `qwirkle_solver.py` — currently hardcoded to 30, but the right number should be determined by win-rate data across many games
- **strategy:** should any weight be assigned to a move that leaves more similar tiles in My Hand? (e.g., prefer moves that preserve hand tiles sharing a color or shape, since they enable bigger future plays / Qwirkles)
