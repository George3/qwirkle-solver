# Another Qwirkle™ Solver

- but the first I've "written"*

## Intro

My first significant forey(sp?) into vibe-coding(🙄)

- Fairly impressed with how well the AI agent perform responding to my prompts to create this.

## Browser App

There is now a local Flask app that runs in a browser and keeps the move validation and solver logic in Python.

### Run It

1. Install dependencies: `pip install -r requirements.txt`
2. Start the app: `python app.py`
3. Open the local URL shown in the terminal, usually `http://127.0.0.1:5000`

### What It Does

- Starts with an empty board.
- Lets you add any tile from the full palette into your hand.
- Lets you drag a tile from your hand onto highlighted legal board cells.
- Validates pending moves in Python before commit.
- Lets you use a board setup mode to place or remove tiles directly on the board.
- Shows solver suggestions for the current board and hand.

## DRFT ~ FIXME = FINISH-ME

- Using ~CoPilot Pro (1 month Trial) $10/mo.  Upgraded from CoPilot free because pro allows use of premium models like Claude Opus 4.6.

- Most code gen'd w/Claude Haiku #.#?, Sonnet #.#?, GPT-5.3-Codex. 
...Occasionally, used cutting edge Claude Opus 4.6 and Gemini -see branches for example.

(*Heavily AI-assisted)