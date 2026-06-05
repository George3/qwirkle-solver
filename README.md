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
- Run: `.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000`
- Running `.venv\Scripts\python.exe qwirkle_solver.py` on a two-player empty-bag position now also infers the opponent's hidden hand and prints a reply-aware endgame report for the top candidate moves.

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

## TODO

- Plan->Use ~session sets/dabler ext.: Convert from same game_state.json file saved for different games via different branches to a single branch that can easily load differently named game_state.json files (This way new features we add to the solver engine are immediately avail. to every game)
- Move auto-backed up old game_state.json to a subdir.
- (minor) Clean up (remove) obsolete files like Screenshot*png.
- SOLVER IMPROVEMNETS: a) Revisit file "Toward a smarter...", b) TODOs in README.md, c) Try evolutionary approach as suggested in [video: The only AutoResearch tutorial...](https://youtu.be/uBWuKh1nZ2Y?si=Sg71v2EAUWEsRyzF)
- ADD TEST cases (Since saw in "big" ./scratch/~end_game.py analysis) ONLY rules Opus 4.8 would self-validate against seems to be: (copied from Claude's chat) "Verified — the engine is trustworthy: it scores the pre-block orange-crossx at (-1,1) as exactly 9 (matching what you blocked) and correctly rules it illegal now. Your block is airtight."
...from CLAUDE.md or ~/.claude/~~memory
- Add asserts (aka, validation) if a chosen tile breaks any rules of game.
- **(Claude Opus suggestion)** bag/remaining-tile tracker — derive what's left in the bag from `(108 total) − (tiles on board) − (tiles in hand)` and show a 6×6 grid of remaining counts. Naturally feeds `LATE_GAME_BAG_THRESHOLD` logic and helps real-game strategy (knowing if the last `purple star` is still out there)

## Lower priority TODOs

- Auto-resize board and "My Hand" to fit better on 1 screen
- Possibly mode features: **edit** vs. **play** modes — edit allows setting/removing any tiles including "my hand"; play mode would "use" tiles from "my hand" when they are added to the board
- Add "suggest moves" button (call `qwirkle_solver` in-process, render the top-N ranked placements as ghost overlays on the board)
- Add a score board area (not a button!?) - might only be available if every move is assigned to a specific player?
- **(Claude Opus suggestion)** undo/redo using the existing `game_state.json.bak-*` snapshots — they're already written on every mutation, so a `POST /api/undo` that restores the most-recent backup is nearly free and rescues the "oops, wrong click" case
