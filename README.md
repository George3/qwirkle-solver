# Qwirkle™ Solver

## Intro

My first significant fore(sp?) into vibe-coding(🙄)

- Fairly impressed with how well the AI agent perform responding to my prompts to create this.

DRFT ~ FIXME = FINISH-ME:
- Using ~CoPilot Pro (Trial) $10/mo. (Upgraded from CoPilot free becase allows to use premium models like laude Opus 4.6 -- TODO check usage if "Free" would still cover it?! 💸💳)
- Most code gen'd w/Claude Haiku #.#?, Sonnet #.#?, GPT-5.3-Codex. ...Occasionally, cutting edge Claude Opus 4.6, ...Gemini -see branch on refactor.


## AI History / How-To

- To start server from: C:\src\fun\qwirkle-solver>
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
