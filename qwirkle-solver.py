from dataclasses import dataclass
from typing import Optional, TypedDict

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
# Day 2. (2026-02-09) Changed "(x,y)" param to "move tuple.  Hardcoded tiles for a real game with Expert (but no optimization implemented yet!)

# .plan: 
#   Baby step?: Test if move with a set of tiles works w/code (or adjust accordingly) and calculate score for it.
#   Add "hand" to the engine.
#   Start "simple" GUI (but 1st try "ambitious" 1st small jump to use screenshot) -> game_state 
#   How to suggest next move?
#   Understand current code's mv selection THEN implement simple "intelligence"[2] to improve it.
# Day 3. ... 
# Day 4
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
Qwirkle is a tile-based game where players score points by creating lines of
tiles that share a common attribute (color or shape) but differ in the other.
Each tile has a color (e.g., red, orange, yellow, green, blue, purple)
and a shape (e.g., circle, square, diamond, star, clover, cross-X).
"""

"""
## Rand. Notes
    - Pylance in use: Since vscode suggested I change its settings so some type checking happens
        and gave URL: https://microsoft.github.io/pyright/#/configuration?id=type-check-diagnostics-settings
        vs. AI here gave URL: https://code.visualstudio.com/docs/python/linting#_pylance-type-checking, I turned on "basic" type checking.
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

    def calculate_score(self, x, y, tile):
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
    

# Example usage
if __name__ == "__main__":
    engine = QwirkleEngine()

    # Define some tiles already on the board
    # board for vs. tinyb (not robot)
    game_state = {
        # Worked in 23c8e6f:  (-1, 0): Tile(color='red', shape='cross-X'),
        (0, 0): Tile(color='blue', shape='clover'),
        (1, 0): Tile(color='green', shape='clover'),
        (2, 0): Tile(color='yellow', shape='clover'),
        (2, 1): Tile(color='yellow', shape='star'),
        (3, 1): Tile(color='orange', shape='star'),
        (4, 1): Tile(color='red', shape='star'),
        (4, 2): Tile(color='red', shape='cross-X'),
        (5, 2): Tile(color='purple', shape='cross-X'),
        (4, 3): Tile(color='red', shape='circle'),
        (5, 3): Tile(color='purple', shape='circle')
    }

    # Load the in-progress game
    engine.load_board_state(game_state)

    # Now you can check moves against this board state
    test_tile = Tile(color='purple', shape='square')

    # test_move = (3, 0)
    test_move = (5, 4)
# TODO put in func. so can try mult. moves easily:
    if engine.is_legal_move(test_move, test_tile):
        score = engine.calculate_score(3, 0, test_tile)
        print(f"Valid move! Score: {score}")
    else:
        print("Not valid move: " + str(test_tile) + " at (3, 0)") # FIXME hardcoded move in print statement. 
