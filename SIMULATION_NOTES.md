# Simulation Notes — strategy tuning for `qwirkle_solver.py`

Durable record of strategy decisions that we **can't measure yet** because there's no
headless 2-player simulation loop. When that loop exists (the "run 1000s of games"
plan), use this as the to-do list of hypotheses to A/B and constants to sweep.

Cross-reference: the original a/b/c/d simulation ideas live in the narrative block at
[qwirkle_solver.py:117-133](qwirkle_solver.py#L117-L133). This file extends them.

## Background: the game that prompted this

Game "Jeanne 03" (commit `4b7a900`), Jeanne 77 – Me 55. She won by **building Qwirkles
in her hand** and completing them in one multi-tile drop, while the solver kept ending
lines at an open 5 — handing her one-tile Qwirkle completions (6 + 6 bonus = 12 pts).
The old defense (`apply_late_game_risk_filter`) only fired at bag ≤ 30; the game was at
**64** tiles, so it never fired.

## What we implemented (the safe/known-good half)

Both terms now run **every turn** in `apply_strategy_adjustments`, and both are now
**probability-weighted** rather than flat (see H3 below — implemented, not yet
simulation-validated):

- **Defense — `gift_risk`**: finds any open 5-line the opponent could *actually*
  complete (a completing-tile copy is unaccounted-for AND the open-end cell is a legal
  placement for it — perpendicular neighbors don't poison it), then scales
  `QWIRKLE_GIFT_PENALTY` by `probability_in_opponent_hand` — the exact hypergeometric
  odds that at least one unseen copy is in the opponent's hand rather than still in the
  bag, given the current unseen-tile pool. 1 unseen copy now costs less than 2; a big bag
  costs less than a nearly-empty one. `gifts_opponent_qwirkle` remains as a boolean
  wrapper for callers that only need the tile.
- **Offense — `build_bonus`**: reward for keeping a strong partial-Qwirkle set in hand,
  so the solver sometimes holds back the "5th tile" to build its own Qwirkle — completed
  later in a single multi-tile move the opponent can't intercept. The flat, capped band
  is now multiplied by a confidence factor (average `completer_copies_available /
  COPIES_PER_TILE` across the set's missing tiles), so a set that's realistically
  completable keeps close to the full band and one whose missing tiles are already gone
  earns close to nothing.

## The decision we deferred: Bounded vs Aggressive hold-back

We originally chose **Bounded** (capped, flat band) over **Aggressive** (band scales
with set closeness + weighted by unseen completer copies) only because we couldn't
measure it. **H3 (completer-availability weighting) is now implemented** — `build_bonus`
scales the flat band by availability, moving from pure-Bounded toward Aggressive without
uncapping `QWIRKLE_BUILD_BAND` itself. This is still **not simulation-validated** — the
harness below doesn't exist yet, so we can't confirm it beats the old flat-band version
by win rate. The risk flagged originally still applies: hoarding tiles and underplaying
if the board never offers a spot to cash the set (that's H4, still open).

## Tunable knobs (sweep these)

| Constant | Default | Meaning |
|---|---|---|
| `QWIRKLE_GIFT_PENALTY` | 12 | Max penalty (at 100% risk) for gifting an open 5-line. |
| `QWIRKLE_BUILD_BAND` | 3 | Max points (at 100% confidence) the solver will give up *now* to keep building a Qwirkle. **Raising this ≈ moving from Bounded toward Aggressive.** |
| `MIN_BUILD_SET` | 4 | Hand-set size that counts as "building." |
| `OPPONENT_HAND_SIZE` | 6 | Assumed opponent hand size used by `probability_in_opponent_hand`'s hypergeometric calculation. |

## Hypotheses to test

- **H1** — Always-on gift penalty beats the old late-game-only gate. (Expected: yes.)
- **H2** — Bounded build bonus beats no build bonus; find the `QWIRKLE_BUILD_BAND` value
  that peaks win-rate (sweep 0–6+).
- **H3** — Adding **completer-availability weighting** to `build_bonus` (note b's
  "highest probability to complete the Q": weight a held set by how many of its missing
  tiles are still unseen) beats the flat bonus. **Implemented** (see above); still needs
  simulation to confirm it actually beats the old flat-band version by win rate.
- **H4** — `build_bonus` should also require a plausible **board location** to play the
  set (it currently scores the hand only). Test whether adding board-feasibility helps
  or just adds cost. Still open — see README TODO.
- **H5** — Scaling `QWIRKLE_GIFT_PENALTY` by `probability_in_opponent_hand` (hypergeometric
  odds, not a flat any-unseen-copy trigger) beats the old flat penalty, especially in the
  late game where a small unseen pool makes a linear approximation over-confident.
  **Implemented**; not yet simulation-validated.

## Harness prerequisites (not built yet)

Per CLAUDE.md, tests/sim are still pending. To run these we need:

1. A headless 2-player driver: shuffle bag, deal hands, alternate turns calling
   `generate_all_multi_moves`, draw to refill, score, detect game end.
2. A configurable opponent (at least: greedy max-score, and a "hoarder" approximating
   Jeanne) to play the solver against.
3. Constants overridable per run (env or args) so a sweep can vary them without edits.
