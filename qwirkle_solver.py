import json
from collections import Counter
from dataclasses import dataclass
from math import comb
from pathlib import Path
from typing import Iterable, Optional, TypedDict


TOTAL_QWIRKLE_TILES = 108
COPIES_PER_TILE = 3  # each (color, shape) appears 3 times in a standard set

# Strategy knobs (sweep these in future simulations -- see SIMULATION_NOTES.md):
QWIRKLE_GIFT_PENALTY = 12  # a Qwirkle = 6 (line) + 6 bonus; what an open 5-line hands away
QWIRKLE_BUILD_BAND = 3     # max points a hold-back move may give up vs the raw best (tunable)
MIN_BUILD_SET = 4          # smallest partial-Qwirkle set in hand that counts as "building"
OPPONENT_HAND_SIZE = 6     # assumed opponent hand size for gift-risk probability estimates

ALL_COLORS = {"red", "orange", "yellow", "green", "blue", "purple"}
ALL_SHAPES = {"circle", "square", "diamond", "clover", "crossx", "star"}


"""
Qwirkle is a tile-based game where players score points by creating lines of
tiles that share a common attribute (color or shape) but differ in the other.
Each tile has a color (e.g., red, orange, yellow, green, blue, purple)
and a shape (e.g., circle, square, diamond, star, clover, crossX).
"""

## History: 
# Day 0. (Fri. Jan.6, 2026) Originaly started w/Gemini - PROMPT: "Program something to help me find the best moves in qwirkle"
#   (Gemini 3 Flash, iPad, running in the Free tier)
#   See also Gmail.
# Day 1. Switched to vscode. Set Copilot Agent to 'Auto' - used mix that was mostly from both Claude Sonnet 4.5 - 0.9x and 
#  GPT-5.2-Codex 0.9x
#  See also: C:\git_multiple_repos\ai\general_notes\python-self-learn.txt
#  MILESTONE: It works! - Loads in-progress game state (from my manually entered game_state), 
#   check if a move is legal, and calculate the score for that move.
#  Fixed inability to commit & push by rm'ing subdirs (no subdirs allowed w/gists!)
# Day 2. (2026-02-09) Changed "(x,y)" param to "move tuple.  Hardcoded tiles for a real game with Expert (but no optimization implemented yet!). First .plan ideas added.
# Day 3. (2026-02-15) Fixed: Score was wrong: 3 instead of 6 given.
#   - DONE: Add ~loop to try all possible positions w/1 tile.
#   - DONE: Then outer loop to test all tiles in hand.
#   - DONE (in Day 4): Test out in an actual game (w/NO strategy besides Max score) 
#   - DONE: (Around this time or earlier & w/AI's help surprisingly easy to add) Support moves w/>1 tile at a time (to find best move from hand)
# Day 4. (2026-02-17) Did above; namely: Tested out in actual game vs. "Easy Robot" (got up to 76 pieces left in bag before called it a night).
# Day 5. (2026-02-18) git work: Combined gist w/a "full" repo w/only SVG so far and created git-history.md in ~ai/gen...nts repo.
# Day 6. (2026-02-19) In branch "new-game-w-Mom" it seems to prove it won't suggest 5-tile moves:
"""
    $ date; python ./qwirkle_solver.py; date
    Thu, Feb 19, 2026  9:31:37 PM
    Total legal multi-tile moves: 27
    Rank 1: 6 points -> (4, 1): Tile(color='green', shape='diamond'), (4, 2): Tile(color='red', shape='diamond'),
    Rank 2: 6 points -> (4, 0): Tile(color='red', shape='diamond'), (4, 1): Tile(color='green', shape='diamond'),
    Rank 3: 6 points -> (0, 0): Tile(color='red', shape='diamond'), (0, 1): Tile(color='green', shape='diamond'),
    Rank 4: 6 points -> (0, 1): Tile(color='green', shape='diamond'), (0, 2): Tile(color='red', shape='diamond'),
    Rank 5: 4 points -> (3, 2): Tile(color='green', shape='diamond'), (4, 2): Tile(color='red', shape='diamond'),
    Rank 6: 4 points -> (1, -3): Tile(color='red', shape='diamond'), (1, -2): Tile(color='green', shape='diamond'),
"""
# Day 7. (2026-02-21) Unplanned creation of board.svg and sync_board.py - which make it easier to keep up
# Day 8. (2026-02-22) Unplanned: Prompted "rename_files.py" to hide old board.svg backups. 
#   Made my move #~12.
#   (start ~11:10pm to 11:23pm; RESUME...)
#   ...total time-->   (12:25am-> ~fell asleep ~1:15am, woke: ~2:45am - END at 4:25am)
#   with a game on iPad.  Plus, I'm starting to see how I can build on this, with "heavy-lifting" 
#   from AI, to create a full GUI app that either easily follows games on the iPad or, like my boss (dmc)
#   suggested, reimplements the current Qwirkle app. (Simplest would be to have a GUI in SVG that 
#   I setup be read and updates the board and my_tiles in the solver.)
# Day 9. (2026-02-25): Start w/ bde64ab3a08accb666e4f3d8c66b85141e35a7eb
# Day 10. (2026-02-27): Played move #~13.  Score: me: 63; Mom: 31. 
# .. been working on this for ~21 calendar days (See subj:"Qwirkle solver by Gemini" emailed from self to "ycj" on 2/6/2026 )
# ... enough with the day-by-day history. Omitting going fwd for brevity. Of course can always see git-history for future details 
#     & even get AI in on that to see how well it interprets a git commit history ;-) / 😉.

# 'TODO || DONE? - on ~2/25: run rename >> chg. sync's out put to have .svg at end after .bak.svg. >> either plan then/or do a small...
#    ...step toward interactive GUI.  cr' "standing" check list w/security chk/prompt and other best practices (Think of boss's 
#    "standing" ~project instructions if hit enter - detect mid-thought).
# ==>> NEXT-IS-HERE::  FIXME?: Line ~494 not sync'ing to svg. It should "see": Tile(color="red", shape="diamond"),
# Day #TOMORROW#. (2026-02-22) Fixed above FIXME - (AI's prediction: "was a typo in game_state.")
# The Future ...is near.

# TODO's - See any FIXME or TODO above.
# - Use OpenCV to "see" the game board from a screenshot or iPhone's camera.
# - Add validation for game board. 
# - Break away for 1st learnings about OpenCV.
# - Validate game_state (To catch my typos and also useful when fully automated might catch a lot of OpenCV errors (acts as an assert when a tile not a legal placement).
## Strategy ##
#  - Come up w/more sophisticated strategy for suggesting moves: 
#  - Also, consider adding a "difficulty" setting that adjusts (ai:) how much it prioritizes blocking opponent's moves vs. maximizing own score.
#  - Rare but sometimes (~if >=3 tiles in hand) it might be worth (ai:) playing a lower-scoring move if it sets up a Qwirkle for the next turn.
#  - Rare but sometimes (~if true for >=3 tiles in hand and other tiles are low scoring), put trade X # of tiles in instead of laying down tiles on game board.
#  - (ai) Eventually, could even add a "learning" component where it tracks which moves lead to wins/losses and adjusts its strategy over time.
#>- Continue with OpenCV idea on Claude iPad app.
# - Is GPLv2 what you want to keep as license? (Check w/AI - esp. their TOS and do research on it).
# - Housekeeping: Either delete gist on GH (since private) or make 1 last commit to point to this repo - Either way, del my local gist.

# .plan: 
#   Baby step?: Test if move with a set of tiles works w/code (or adjust accordingly) and calculate score for it.
#   By end-of-weekend (Sun.2026-02-22): Go public w/CONTRIBUTING.md, IFF some form of GUI tile placement is working.
#   Start "simple" GUI (but 1st try "ambitious" 1st small jump to use screenshot) -> game_state 
#   How to suggest next move?
#   Understand current code's mv selection THEN implement simple "intelligence"[2] to improve it.
# 
    # [2] Integrating with a Hand Solver
    # To find the best move, you'll want to wrap this in a loop 
    # that simulates your hand:
    # best_score = 0
    # best_move = None
    # 
    # for tile in hand:
    #     for spot in available_spots:
    #         if engine.is_legal_move(spot.x, spot.y, tile):
    #             score = engine.calculate_score(spot.x, spot.y, tile)
    #             if score > best_score:
    #                 best_score = score
    #                 best_move = (spot, tile)


"""
## Rand. Notes
    - Pylance in use: Since vscode suggested I change its settings so some type checking happens
        and gave URL (not to Pylance*): https://microsoft.github.io/pyright/#/configuration?id=type-check-diagnostics-settings
        vs. AI here gave URL: https://code.visualstudio.com/docs/python/linting#_pylance-type-checking, I turned on "basic" type checking.
        *Pylance vs. Pyright: "Pylance incorporates the Pyright type checker but features additional capabilities" -- https://microsoft.github.io/pyright/#/installation?id=vs-code
      AI: "...built-in Python extension includes Pylance, you can leverage its features for better code analysis and suggestions."

## Ideas to make Qwirkle solver beat 'Expert' level:
1. Once program can run 2-player games 100% headless and output 
    appropriate stats/outcomes, then run simulations to see which of
    this is more successful:
    a) Always play the highest scoring move available.
    b) (human-gen'd) Hold on to single tile that would be the 5th in a line - for a later Q.
        And if two tiles in my hand are 5-pointers, pick the one that 
        has the highest probability to complete the Q.
        (AI: line score 1 point, and only play them when they open up a high-scoring move for the next turn.
    c) (ai-gen'd) Play the highest scoring move available, but if there are multiple
        with the same score, prefer the one that creates more future opportunities.
        (e.g., creates a line of 3 instead of 2, or opens up more empty spaces around it).
    d) Play the highest scoring move available, but if there are multiple with
      the same score, prefer the one that blocks the opponent's potential 
      high-scoring moves.  
    
"""

@dataclass(frozen=True)
class Tile:
    color: str
    shape: str

class QwirkleEngine:
    def __init__(self):
        # Board stores coordinates as (x, y): {'color': 'red', 'shape': 'star'}
        self.board: dict[tuple[int, int], Tile] = {}

    # gmr3 changed x,y param to move tuple. Good choice? -- 23c8e6f.
    def is_legal_move(self, move, tile):
        x, y = move
        """ FIXME: Where is check for 
            Checks if placing 'tile' at (x, y) follows Qwirkle rules."""
        if (x, y) in self.board:
            return False # Can't place on an occupied space.
            
        neighbors = self.get_neighbors(x, y)
        if not neighbors:
            return False # Must connect to at least one existing tile.
            
        for axis in ['horizontal', 'vertical']:
            line = self.get_line(x, y, axis)
            if not self.validate_line(line, tile):
                return False
        return True

    def validate_line(self, line, tile):
        """Ensures all tiles in a row/column share one trait and differ 
           in the other."""
        if not line:
            return True
        
        colors = {t.color for t in line} | {tile.color}
        shapes = {t.shape for t in line} | {tile.shape}
        
        # Rule: Either all colors same + shapes different, 
        # OR all shapes same + colors different
        valid_color_run = (len(colors) == 1 and len(shapes) == len(line) + 1)
        valid_shape_run = (len(shapes) == 1 and len(colors) == len(line) + 1)
        
        return (valid_color_run or valid_shape_run) and len(line) < 6

    def calculate_score(self, move, tile):
        """
        Calculates the total points for placing a tile at (x, y),
        including bonuses for Qwirkles (lines of 6).
        A tile can score in two directions: Horizontal and Vertical.
        """
        total_score = 0
        directions = [
            ('horizontal', [(1, 0), (-1, 0)]), # Change in x
            ('vertical', [(0, 1), (0, -1)])    # Change in y
        ]

        for axis, vecs in directions:
            line_length = 1  # The tile itself
            x, y = move
            for dx, dy in vecs:
                curr_x, curr_y = x + dx, y + dy
                while (curr_x, curr_y) in self.board:
                    line_length += 1
                    curr_x += dx
                    curr_y += dy
            
            # In Qwirkle, a line only scores if it's at least 2 tiles long
            # (unless it's the very first move of the game)
            if line_length > 1:
                total_score += line_length
                
                # Add Qwirkle Bonus
                if line_length == 6:
                    total_score += 6
                    
        # Edge case: If the tile doesn't form a line (lonely tile), it's worth 1
        return max(total_score, 1)

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        return self.board.get((x, y))

    def has_tile(self, x: int, y: int) -> bool:
        return (x, y) in self.board
    
    def load_board_state(self, tiles: dict[tuple[int, int], Tile]) -> None:
        """Load board state for an in-progress game."""
        self.board = tiles.copy()
    
    def get_neighbors(self, x: int, y: int) -> list[Tile]:
        """Get all adjacent tiles (up, down, left, right)."""
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            tile = self.get_tile(x + dx, y + dy)
            if tile:
                neighbors.append(tile)
        return neighbors
    
    def get_line(self, x: int, y: int, axis: str) -> list[Tile]:
        """Get all tiles in a line (horizontal or vertical) adjacent to (x, y)."""
        line = []
        if axis == 'horizontal':
            directions = [(1, 0), (-1, 0)]
        else:  # vertical
            directions = [(0, 1), (0, -1)]
        
        for dx, dy in directions:
            curr_x, curr_y = x + dx, y + dy
            while (curr_x, curr_y) in self.board:
                line.append(self.board[(curr_x, curr_y)])
                curr_x += dx
                curr_y += dy
        
        return line

def try_move(engine, move, tile) -> Optional[int]:
    if engine.is_legal_move(move, tile):
        return engine.calculate_score(move, tile)
    return None


def get_line_on_board(
    board: dict[tuple[int, int], Tile],
    x: int,
    y: int,
    axis: str,
) -> list[Tile]:
    line: list[Tile] = []
    if axis == "horizontal":
        directions = [(1, 0), (-1, 0)]
    else:  # vertical
        directions = [(0, 1), (0, -1)]

    for dx, dy in directions:
        curr_x, curr_y = x + dx, y + dy
        while (curr_x, curr_y) in board:
            line.append(board[(curr_x, curr_y)])
            curr_x += dx
            curr_y += dy

    return line


def get_adjacent_empty_cells(engine: QwirkleEngine) -> set[tuple[int, int]]:
    candidates: set[tuple[int, int]] = set()
    for x, y in engine.board:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            move = (x + dx, y + dy)
            if move not in engine.board:
                candidates.add(move)
    return candidates


def get_empty_line_through(
    engine: QwirkleEngine,
    start: tuple[int, int],
    axis: str,
) -> list[tuple[int, int]]:
    x, y = start
    if axis == "horizontal":
        directions = [(1, 0), (-1, 0)]
        key_index = 0
    else:
        directions = [(0, 1), (0, -1)]
        key_index = 1

    positions = {start}
    for dx, dy in directions:
        curr_x, curr_y = x + dx, y + dy
        # Scan up to 5 cells in each direction (max Qwirkle line length is 6,
        # so any cell more than 5 away from the anchor can't share a line with it).
        # Scan THROUGH existing tiles — placements may straddle them as long as
        # the final row/column is contiguous (e.g. place at y=-4 and y=-1 with
        # existing tiles at y=-3 and y=-2 bridging the gap).
        steps = 0
        while steps < 5:
            if (curr_x, curr_y) not in engine.board:
                positions.add((curr_x, curr_y))
            curr_x += dx
            curr_y += dy
            steps += 1

    return sorted(positions, key=lambda pos: pos[key_index])


def generate_connected_segments(
    engine: QwirkleEngine,
    min_len: int = 1,
    max_len: int = 6,
) -> list[tuple[tuple[int, int], ...]]:
    anchors = get_adjacent_empty_cells(engine)
    segments: set[tuple[tuple[int, int], ...]] = set()

    for anchor in anchors:
        for axis in ["horizontal", "vertical"]:
            line = get_empty_line_through(engine, anchor, axis)
            if len(line) < min_len:
                continue
            for i in range(len(line)):
                for j in range(i + min_len - 1, min(len(line), i + max_len)):
                    segment = line[i : j + 1]
                    if anchor in segment:
                        segments.add(tuple(segment))

    return list(segments)


def validate_full_line(tiles: list[Tile]) -> bool:
    if len(tiles) <= 1:
        return True

    colors = {t.color for t in tiles}
    shapes = {t.shape for t in tiles}
    valid_color_run = len(colors) == 1 and len(shapes) == len(tiles)
    valid_shape_run = len(shapes) == 1 and len(colors) == len(tiles)
    return (valid_color_run or valid_shape_run) and len(tiles) <= 6


def iter_tile_sequences(tiles: Counter[Tile], length: int) -> Iterable[tuple[Tile, ...]]:
    if length == 0:
        yield ()
        return

    for tile in list(tiles.keys()):
        if tiles[tile] == 0:
            continue
        tiles[tile] -= 1
        for suffix in iter_tile_sequences(tiles, length - 1):
            yield (tile,) + suffix
        tiles[tile] += 1


def is_legal_multi_move(
    engine: QwirkleEngine,
    placements: list[tuple[tuple[int, int], Tile]],
) -> bool:
    if not placements:
        return False

    moves = [move for move, _ in placements]
    if len(set(moves)) != len(moves):
        return False

    for move in moves:
        if move in engine.board:
            return False

    xs = {move[0] for move in moves}
    ys = {move[1] for move in moves}
    if len(xs) == 1:
        axis = "vertical"
    elif len(ys) == 1:
        axis = "horizontal"
    else:
        return False

    temp_board = engine.board.copy()
    for move, tile in placements:
        temp_board[move] = tile

    if engine.board:
        has_connection = False
        for x, y in moves:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (x + dx, y + dy) in engine.board:
                    has_connection = True
                    break
            if has_connection:
                break
        if not has_connection:
            return False

    if axis == "horizontal":
        fixed_y = moves[0][1]
        min_x = min(move[0] for move in moves)
        max_x = max(move[0] for move in moves)
        for x in range(min_x, max_x + 1):
            if (x, fixed_y) not in temp_board:
                return False
    else:
        fixed_x = moves[0][0]
        min_y = min(move[1] for move in moves)
        max_y = max(move[1] for move in moves)
        for y in range(min_y, max_y + 1):
            if (fixed_x, y) not in temp_board:
                return False

    sample_x, sample_y = moves[0]
    main_line = get_line_on_board(temp_board, sample_x, sample_y, axis)
    main_line_tiles = main_line + [temp_board[(sample_x, sample_y)]]
    if not validate_full_line(main_line_tiles):
        return False

    perpendicular = "vertical" if axis == "horizontal" else "horizontal"
    for x, y in moves:
        line = get_line_on_board(temp_board, x, y, perpendicular)
        line_tiles = line + [temp_board[(x, y)]]
        if not validate_full_line(line_tiles):
            return False

    return True


def calculate_score_multi(
    engine: QwirkleEngine,
    placements: list[tuple[tuple[int, int], Tile]],
) -> Optional[int]:
    if not is_legal_multi_move(engine, placements):
        return None

    temp_board = engine.board.copy()
    for move, tile in placements:
        temp_board[move] = tile

    moves = [move for move, _ in placements]
    xs = {move[0] for move in moves}
    axis = "vertical" if len(xs) == 1 else "horizontal"
    perpendicular = "vertical" if axis == "horizontal" else "horizontal"

    sample_x, sample_y = moves[0]
    main_length = 1 + len(get_line_on_board(temp_board, sample_x, sample_y, axis))
    total_score = 0
    if main_length > 1:
        total_score += main_length
        if main_length == 6:
            total_score += 6

    for x, y in moves:
        line_length = 1 + len(get_line_on_board(temp_board, x, y, perpendicular))
        if line_length > 1:
            total_score += line_length
            if line_length == 6:
                total_score += 6

    return max(total_score, 1)


def estimate_tiles_left_in_bag(
    board_tile_count: int,
    my_hand_count: int,
    players: int = 2,
    hand_size: int = 6,
    total_tiles: int = TOTAL_QWIRKLE_TILES,
) -> int:
    other_players = max(players - 1, 0)
    reserved_for_other_hands = other_players * hand_size
    return max(total_tiles - board_tile_count - my_hand_count - reserved_for_other_hands, 0)

def get_line_positions_on_board(
    board: dict[tuple[int, int], Tile],
    x: int,
    y: int,
    axis: str,
) -> list[tuple[int, int]]:
    if axis == "horizontal":
        directions = [(1, 0), (-1, 0)]
    else:
        directions = [(0, 1), (0, -1)]

    positions = [(x, y)]
    for dx, dy in directions:
        curr_x, curr_y = x + dx, y + dy
        while (curr_x, curr_y) in board:
            positions.append((curr_x, curr_y))
            curr_x += dx
            curr_y += dy
    return positions


def open_endpoints(
    board: dict[tuple[int, int], Tile],
    line_positions: list[tuple[int, int]],
    axis: str,
) -> list[tuple[int, int]]:
    """The empty cell(s) just past either end of a line."""
    if axis == "horizontal":
        y = line_positions[0][1]
        min_x = min(pos[0] for pos in line_positions)
        max_x = max(pos[0] for pos in line_positions)
        candidates = [(min_x - 1, y), (max_x + 1, y)]
    else:
        x = line_positions[0][0]
        min_y = min(pos[1] for pos in line_positions)
        max_y = max(pos[1] for pos in line_positions)
        candidates = [(x, min_y - 1), (x, max_y + 1)]
    return [cell for cell in candidates if cell not in board]


def completing_tile_for_line(line_tiles: list[Tile]) -> Optional[Tile]:
    """The single tile that would extend a valid line to a Qwirkle (length 6), or None.

    A valid line is a color-run (one color, distinct shapes) or a shape-run (one shape,
    distinct colors); the completer is the one missing attribute value.
    """
    colors = {t.color.lower() for t in line_tiles}
    shapes = {t.shape.lower() for t in line_tiles}
    if len(colors) == 1 and len(shapes) == len(line_tiles):
        missing = ALL_SHAPES - shapes
        if len(missing) == 1:
            return Tile(color=next(iter(colors)), shape=next(iter(missing)))
    elif len(shapes) == 1 and len(colors) == len(line_tiles):
        missing = ALL_COLORS - colors
        if len(missing) == 1:
            return Tile(color=next(iter(missing)), shape=next(iter(shapes)))
    return None


def completer_copies_available(
    board: dict[tuple[int, int], Tile],
    hand: Counter[Tile],
    completer: Tile,
) -> int:
    """Copies of `completer` NOT visible to me (i.e. board + my hand).

    A standard set has COPIES_PER_TILE of each tile; whatever isn't on the board or in
    my hand is in the bag or the opponent's hand -- so it could complete the Qwirkle.
    """
    seen = 0
    for tile in board.values():
        if tile.color.lower() == completer.color and tile.shape.lower() == completer.shape:
            seen += 1
    for tile, count in hand.items():
        if tile.color.lower() == completer.color and tile.shape.lower() == completer.shape:
            seen += count
    return COPIES_PER_TILE - seen


def probability_in_opponent_hand(
    copies_available: int,
    unseen_pool: int,
    opponent_hand_size: int = OPPONENT_HAND_SIZE,
) -> float:
    """P(at least one of `copies_available` unseen copies of a tile is in the opponent's
    hand), given `unseen_pool` total unseen tiles (bag + opponent hand combined).

    Exact hypergeometric: 1 - P(opponent's hand is drawn entirely from the *other*
    unseen tiles). A linear approximation (copies * hand / pool) over-estimates risk once
    the bag gets small relative to hand size -- exactly the late-game case this solver
    needs to get right (see SIMULATION_NOTES.md's Jeanne-03 loss).
    """
    if unseen_pool <= 0 or copies_available <= 0:
        return 0.0
    if copies_available >= unseen_pool:
        return 1.0
    hand = min(opponent_hand_size, unseen_pool)
    if hand <= 0:
        return 0.0
    return 1.0 - comb(unseen_pool - copies_available, hand) / comb(unseen_pool, hand)


def gift_risk(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
    placements: list[tuple[tuple[int, int], Tile]],
) -> Optional[tuple[Tile, int]]:
    """The (completer tile, unseen copies) an open 5-line this move leaves would let the
    opponent Qwirkle with, else None.

    A 5-line is only a real gift when BOTH (a) at least one copy of the completing tile
    is unaccounted-for (not on the board, not in my hand), AND (b) the open-end cell is a
    *legal* placement for it -- the perpendicular neighbours don't poison it. A single
    QwirkleEngine.is_legal_move call enforces (b) plus the extends-to-6 rule.
    """
    temp_board = engine.board.copy()
    for move, tile in placements:
        temp_board[move] = tile

    remaining_hand = tiles - Counter(tile for _, tile in placements)
    temp_engine = QwirkleEngine()
    temp_engine.load_board_state(temp_board)

    checked: set[frozenset[tuple[int, int]]] = set()
    for (x, y), _ in placements:
        for axis in ("horizontal", "vertical"):
            line_positions = get_line_positions_on_board(temp_board, x, y, axis)
            if len(line_positions) != 5:
                continue
            key = frozenset(line_positions)
            if key in checked:
                continue
            checked.add(key)

            line_tiles = [temp_board[pos] for pos in line_positions]
            if not validate_full_line(line_tiles):
                continue
            completer = completing_tile_for_line(line_tiles)
            if completer is None:
                continue
            copies_available = completer_copies_available(temp_board, remaining_hand, completer)
            if copies_available <= 0:
                continue
            for end in open_endpoints(temp_board, line_positions, axis):
                if temp_engine.is_legal_move(end, completer):
                    return completer, copies_available
    return None


def gifts_opponent_qwirkle(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
    placements: list[tuple[tuple[int, int], Tile]],
) -> Optional[Tile]:
    """The tile the opponent could drop to Qwirkle an open 5-line this move leaves, else
    None. Thin wrapper around `gift_risk` for callers that only need the tile."""
    risk = gift_risk(engine, tiles, placements)
    return risk[0] if risk is not None else None


def _best_partial_qwirkle_group(hand: Counter[Tile]) -> tuple[int, list[Tile]]:
    """The biggest in-hand set toward a Qwirkle -- distinct shapes of one color, or
    distinct colors of one shape -- as (size, missing tiles needed to reach 6)."""
    by_color: dict[str, set[str]] = {}
    by_shape: dict[str, set[str]] = {}
    for tile in hand:  # distinct tiles only; duplicates can't extend the same line
        by_color.setdefault(tile.color.lower(), set()).add(tile.shape.lower())
        by_shape.setdefault(tile.shape.lower(), set()).add(tile.color.lower())

    best_size = 0
    best_missing: list[Tile] = []
    for color, shapes in by_color.items():
        if len(shapes) > best_size:
            best_size = len(shapes)
            best_missing = [Tile(color=color, shape=s) for s in ALL_SHAPES - shapes]
    for shape, colors in by_shape.items():
        if len(colors) > best_size:
            best_size = len(colors)
            best_missing = [Tile(color=c, shape=shape) for c in ALL_COLORS - colors]
    return min(best_size, 6), best_missing


def largest_partial_qwirkle(hand: Counter[Tile]) -> int:
    """Size of the biggest in-hand set toward a Qwirkle (capped at 6). Drives the
    hold-back build bonus."""
    return _best_partial_qwirkle_group(hand)[0]


def partial_qwirkle_missing_tiles(hand: Counter[Tile]) -> Optional[tuple[int, list[Tile]]]:
    """(size, missing tiles) for the biggest in-hand partial-Qwirkle set, or None if
    nothing qualifies as "building" (below MIN_BUILD_SET). `missing` is empty when size
    == 6 -- a complete, unplayed Qwirkle sitting in hand -- which is a valid result, not
    a "nothing to build" case."""
    size, missing = _best_partial_qwirkle_group(hand)
    if size < MIN_BUILD_SET:
        return None
    return size, missing


def build_bonus(engine: QwirkleEngine, remaining_hand: Counter[Tile]) -> float:
    """Bounded reward for keeping a strong partial-Qwirkle set in hand after a move.

    set of 4 -> 1, 5 -> 2, 6 -> 3 (within QWIRKLE_BUILD_BAND so a hold-back move can
    outrank the raw best by at most a few points), scaled down by how many copies of the
    still-missing tiles are unaccounted-for -- a set that's realistically completable
    keeps close to the full band; a set whose missing tiles are already all visible
    elsewhere earns close to nothing.
    """
    detail = partial_qwirkle_missing_tiles(remaining_hand)
    if detail is None:
        return 0.0
    size, missing = detail
    band = min(max(0, size - (MIN_BUILD_SET - 1)), QWIRKLE_BUILD_BAND)
    if not missing:
        return band  # size == 6: a complete set is already in hand, full confidence
    availability = [
        completer_copies_available(engine.board, remaining_hand, tile) / COPIES_PER_TILE
        for tile in missing
    ]
    confidence = max(0.0, min(1.0, sum(availability) / len(availability)))
    return band * confidence


def apply_strategy_adjustments(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
    ranked_moves: list[tuple[int, list[tuple[tuple[int, int], Tile]]]],
) -> list[tuple[int, list[tuple[tuple[int, int], Tile]]]]:
    """Re-rank by strategy: subtract a Qwirkle-gift penalty scaled by the probability the
    opponent actually holds the completer, add a build bonus scaled by how completable the
    held set still is, then break ties among the top group by next-turn look-ahead. Moves
    keep their raw display score; only the ordering changes. Both adjustments are bounded
    at the flat QWIRKLE_GIFT_PENALTY (-12) / QWIRKLE_BUILD_BAND (<=3) knobs, so a real gift
    can never be rescued by build value.
    """
    if not ranked_moves:
        return ranked_moves

    scored: list[tuple[float, int, list[tuple[tuple[int, int], Tile]]]] = []
    for raw, placements in ranked_moves:
        rank_score: float = raw
        remaining_hand = tiles - Counter(tile for _, tile in placements)
        risk = gift_risk(engine, tiles, placements)
        if risk is not None:
            _completer, copies_available = risk
            board_count = len(engine.board) + len(placements)
            unseen_pool = TOTAL_QWIRKLE_TILES - board_count - sum(remaining_hand.values())
            probability = probability_in_opponent_hand(copies_available, unseen_pool)
            rank_score -= QWIRKLE_GIFT_PENALTY * probability
        rank_score += build_bonus(engine, remaining_hand)
        scored.append((rank_score, raw, placements))

    scored.sort(key=lambda item: item[0], reverse=True)

    # Tie-break only the moves tied at the best rank_score -- the one you'll actually
    # play. The multi-tile next-turn look-ahead (followup_score_profile) is expensive,
    # so run it on just this top group, not on every move. rank_score is now a float
    # (probability-weighted), so use a tolerance instead of exact equality -- otherwise
    # floating-point rounding could split genuinely-tied moves apart.
    best_rank = scored[0][0]
    RANK_TIE_EPSILON = 1e-9
    top = [item for item in scored if abs(item[0] - best_rank) < RANK_TIE_EPSILON]
    if len(top) > 1:
        top.sort(
            key=lambda item: followup_score_profile(engine, tiles, item[2]),
            reverse=True,
        )
        scored = top + scored[len(top):]

    return [(raw, placements) for _rank, raw, placements in scored]


def strategy_note(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
    placements: list[tuple[tuple[int, int], Tile]],
) -> str:
    """Human-readable reason a move was up- or down-ranked, for the printed output."""
    notes: list[str] = []
    remaining_hand = tiles - Counter(tile for _, tile in placements)
    risk = gift_risk(engine, tiles, placements)
    if risk is not None:
        completer, copies_available = risk
        board_count = len(engine.board) + len(placements)
        unseen_pool = TOTAL_QWIRKLE_TILES - board_count - sum(remaining_hand.values())
        probability = probability_in_opponent_hand(copies_available, unseen_pool)
        notes.append(
            f"⚠ opens a Qwirkle for opponent ({completer.color}-{completer.shape}, "
            f"~{probability:.0%} risk)"
        )
    partial = largest_partial_qwirkle(remaining_hand)
    if partial >= MIN_BUILD_SET:
        notes.append(f"holds {partial}/6 set")
    return " [" + "; ".join(notes) + "]" if notes else ""


def followup_score_profile(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
    placements: list[tuple[tuple[int, int], Tile]],
) -> tuple[int, ...]:
    """Descending score profile of legal multi-tile follow-up moves.

    Plays `placements` onto a copy of the board, removes those tiles from the
    hand, then enumerates every legal *next turn* -- which may lay down several
    of the leftover tiles at once, just like a real Qwirkle turn -- and returns
    their scores, highest-first. Bag draws are unknown, so only the leftover
    hand is considered.

    Used as a tie-breaker between equal-scoring moves: compared as a tuple it
    prefers a higher best next-turn score, then a richer menu of follow-ups.
    This re-generates a whole turn and is expensive, so callers apply it only
    to the small set of top tied moves -- see generate_all_multi_moves.
    """
    remaining = tiles - Counter(tile for _, tile in placements)
    if not remaining:
        return ()

    next_board = engine.board.copy()
    for move, tile in placements:
        next_board[move] = tile
    next_engine = QwirkleEngine()
    next_engine.load_board_state(next_board)

    scores: list[int] = []
    for segment in generate_connected_segments(next_engine):
        for sequence in iter_tile_sequences(remaining, len(segment)):
            score = calculate_score_multi(next_engine, list(zip(segment, sequence)))
            if score is not None:
                scores.append(score)
    scores.sort(reverse=True)
    return tuple(scores)


def generate_all_multi_moves(
    engine: QwirkleEngine,
    tiles: Counter[Tile],
) -> list[tuple[int, list[tuple[tuple[int, int], Tile]]]]:
    segments = generate_connected_segments(engine)
    results: list[tuple[int, list[tuple[tuple[int, int], Tile]]]] = []

    for segment in segments:
        for sequence in iter_tile_sequences(tiles, len(segment)):
            placements = list(zip(segment, sequence))
            score = calculate_score_multi(engine, placements)
            if score is not None:
                results.append((score, placements))

    # Strategy ranking (gift penalty + build bonus) and the top-group look-ahead
    # tie-break both live in apply_strategy_adjustments now.
    return apply_strategy_adjustments(engine, tiles, results)

def load_game_state(path: Path) -> tuple[dict[tuple[int, int], Tile], Counter[Tile]]:
    """Load board state and hand from a JSON file.

    JSON shape: {"moves": [{"n", "player", "tiles": [{"x","y","color","shape"}...]}, ...],
                 "hand":  [{"color","shape"}, ...]}

    `n` and `player` are per-move metadata (move number / who played) and are
    ignored here -- this loader only flattens every move's `tiles` into the board.
    The string "setup" is a sentinel: the interactive editor (app.py, SETUP_KEY)
    dumps all hand-placed tiles into the single move whose `n == "setup"`.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    board: dict[tuple[int, int], Tile] = {}
    for move in data["moves"]:
        for t in move["tiles"]:
            board[(t["x"], t["y"])] = Tile(color=t["color"], shape=t["shape"])

    hand = Counter(Tile(color=t["color"], shape=t["shape"]) for t in data["hand"])
    return board, hand


# Example usage
if __name__ == "__main__":
    engine = QwirkleEngine()

    game_state, my_tiles = load_game_state(Path(__file__).parent / "game_state.json")
    engine.load_board_state(game_state)

    all_moves = generate_all_multi_moves(engine, my_tiles)
    bag = estimate_tiles_left_in_bag(
        board_tile_count=len(engine.board),
        my_hand_count=sum(my_tiles.values()),
    )
    print(f"Tiles left in bag (est.): {bag}")
    print(f"Total legal multi-tile moves: {len(all_moves)}")

    top_n = 4
    for rank, (score, placements) in enumerate(all_moves[:top_n], start=1):
        placement_str = ", ".join(
            f"{move}: {tile}" for move, tile in placements
        )
        note = strategy_note(engine, my_tiles, placements)
        # Only the rank-1 move is the one you'll play; its next-turn look-ahead is
        # the expensive part, so annotate just that one.
        if rank == 1:
            profile = followup_score_profile(engine, my_tiles, placements)
            followup = profile[0] if profile else 0
            note = f" (best follow-up: {followup}, next moves: {len(profile)}){note}"
        print(f"Rank {rank}: {score} pts{note} -> {placement_str}")
