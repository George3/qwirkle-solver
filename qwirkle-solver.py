# From Gemini - PROMPT: "Program something to help me find the best moves in qwirkle"
# (Gemini 3 Flash, iPad, running in the Free tier)
# See also Gmail.

class QwirkleEngine:
    def __init__(self):
        # Board stores coordinates as (x, y): {'color': 'red', 'shape': 'star'}
        self.board = {}

    def is_legal_move(self, x, y, tile):
        """Checks if placing 'tile' at (x, y) follows Qwirkle rules."""
        if (x, y) in self.board:
            return False
            
        neighbors = self.get_neighbors(x, y)
        if not neighbors:
            return False # Must connect to existing tiles
            
        for axis in ['horizontal', 'vertical']:
            line = self.get_line(x, y, axis)
            if not self.validate_line(line, tile):
                return False
        return True

    def validate_line(self, line, tile):
        """Ensures all tiles in a row/column share one trait and differ in the other."""
        if not line:
            return True
        
        colors = {t['color'] for t in line} | {tile['color']}
        shapes = {t['shape'] for t in line} | {tile['shape']}
        
        # Rule: Either all colors same + shapes different, OR all shapes same + colors different
        valid_color_run = (len(colors) == 1 and len(shapes) == len(line) + 1)
        valid_shape_run = (len(shapes) == 1 and len(colors) == len(line) + 1)
        
        return (valid_color_run or valid_shape_run) and len(line) < 6

    
# Expanded  calculate_score
# [1] - 
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


# [2] Integrating with a Hand Solver
# To find the best move, you'll want to wrap this in a loop 
# that simulates your hand:
best_score = 0
best_move = None

for tile in hand:
    for spot in available_spots:
        if self.is_legal_move(spot.x, spot.y, tile):
            score = self.calculate_score(spot.x, spot.y, tile)
            if score > best_score:
                best_score = score
                best_move = (spot, tile)

