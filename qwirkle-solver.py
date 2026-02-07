# From Gemini

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

    def calculate_score(self, x, y, tile):
        """Calculates points, including bonuses for Qwirkles (lines of 6)."""
        # Logic to sum points for both intersecting lines
        pass
