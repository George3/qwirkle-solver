# Another Qwirkle™ Solver

- ...but the first I've _written_[*]

> ⚠️ **Caution:** Pre-release quality. Mostly AI/LLM-generated. **Use at your own risk!**

## Intro

My first significant foray into vibe-coding(🙄)

- Fairly impressed with how well the AI agents/LLMs perform responding to my prompts to create this.

## Browser App

A local Flask app that runs in a browser and keeps the move validation and solver logic in Python.

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

## TODO ~ FIXME

- Began this mini-project ~[ 2026-02-06], by using ~CoPilot Pro (1 month Trial) $10/mo. in vscode.  Upgraded from CoPilot free because pro allows use of premium models like Claude Opus 4.6.

- In ~first month, most code gen'd w/Claude Haiku ~4.5/4.6, Claude Sonnet 4.5/4.6, GPT-5.3-Codex, and Gemini 3 Flash (Preview).
- Then around Ides of March 2026, starting using "Auto" more, especially for "big" GUI+Flask add where Auto tried Sonnet 4.6 first but, hit "length limit" (See Screenshot 2026-03-17 0042_HitPromptLen_on-1st-GUI-attempt.png), I clicked "Try again" and it switched to GPT-Codex 5.3 to do the job w/a nice TODO list - Screenshot 2026-03-17 0127_End_of_AI_Response_1stGenOfCode=Flask-GUI.png.
...Occasionally, used cutting edge Claude Opus 4.6 and Gemini 3 Pro(Preview). See some commit comments for example.

## Footnotes

[*] Heavily AI-assisted
