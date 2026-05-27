#!/usr/bin/env python3
"""Sync board.svg with game_state.json. Usage: python sync_board.py"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from qwirkle_solver import Tile, load_game_state

ROOT = Path(__file__).parent
JSON = ROOT / "game_state.json"
SVG = ROOT / "board.svg"


def sync_svg(game_state: dict, hand_list: list):

    if not SVG.exists():
        pass # we can recreate it 

    # Backup SVG before overwriting
    if SVG.exists():
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = SVG.with_name(f"{SVG.name}.bak-{now}")
        shutil.copy2(SVG, backup_path)
        print(f"Backed up {SVG} to {backup_path}")

    # Calculate exact bounds
    if not game_state:
        min_x, max_x, min_y, max_y = 0, 0, 0, 0
    else:
        min_x = min(x for x, y in game_state.keys())
        max_x = max(x for x, y in game_state.keys())
        min_y = min(y for x, y in game_state.keys())
        max_y = max(y for x, y in game_state.keys())

    # 2 tiles margin on every side
    grid_min_x = min_x - 2
    grid_max_x = max_x + 2
    grid_min_y = min_y - 2
    grid_max_y = max_y + 2

    cols = grid_max_x - grid_min_x + 1
    rows = grid_max_y - grid_min_y + 1

    tile_size = 110
    board_offset_x = 50
    board_offset_y = 60

    # compute board bounding box size
    board_w = board_offset_x * 2 + cols * tile_size
    board_h = board_offset_y + rows * tile_size

    # The hand tiles list is 'hand_count' * 90 width
    hand_count = len(hand_list)
    hand_w = hand_count * 90
    
    # Let the svg width be max of board and hand
    svg_w = max(board_w, hand_w + 100)
    
    # Centre hand
    hand_start_x = (svg_w - hand_w) // 2

    # y-coordinates for hand rendering below board
    hand_label_y = board_h + 30
    hand_y = hand_label_y + 15
    hand_text_y = hand_y + 110
    
    svg_h = hand_text_y + 20

    def get_px_py(x: int, y: int):
        px = board_offset_x + (x - grid_min_x) * tile_size
        py = board_offset_y + (grid_max_y - y) * tile_size
        cx = px + tile_size // 2
        cy = py + tile_size // 2
        return px, py, cx, cy

    color_map = {
        "red": "#e02020",
        "blue": "#1a6edb",
        "green": "#22aa33",
        "orange": "#ff8800",
        "yellow": "#f5d000",
        "purple": "#8833cc",
    }

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}" style="background:#f5f0e8">')
    
    # Title
    svg_parts.append(f'  <text x="{svg_w//2}" y="30" text-anchor="middle" font-size="20" fill="#333" font-family="sans-serif" font-weight="bold">Qwirkle Board State</text>')

    svg_parts.append("  <!-- Coordinate labels: x (columns) -->")
    for x in range(grid_min_x, grid_max_x + 1):
        px, py, cx, cy = get_px_py(x, grid_max_y)
        svg_parts.append(f'  <text x="{cx}"  y="{board_offset_y - 12}" text-anchor="middle" font-size="36" fill="#777" font-family="monospace">{x}</text>')

    svg_parts.append("  <!-- Coordinate labels: y (rows) -->")
    for y in range(grid_min_y, grid_max_y + 1):
        px, py, cx, cy = get_px_py(grid_min_x, y)
        svg_parts.append(f'  <text x="{board_offset_x - 20}" y="{cy + 4}" text-anchor="middle" font-size="36" fill="#777" font-family="monospace">{y}</text>')

    svg_parts.append("\n  <!-- ============================================ -->")
    svg_parts.append("  <!-- TILES                                        -->")
    svg_parts.append("  <!-- ============================================ -->\n")

    for (gx, gy), tile in sorted(game_state.items(), key=lambda kv: (kv[0][0], -kv[0][1])):
        px, py, cx, cy = get_px_py(gx, gy)
        color = color_map.get(tile.color, tile.color)
        shape = tile.shape.lower()

        svg_parts.append(f"  <!-- ({gx},{gy}) {tile.color} {tile.shape}  |  px={px} py={py}  cx={cx} cy={cy} -->")
        svg_parts.append(f'  <rect x="{px}" y="{py}" width="110" height="110" rx="8" fill="#222"/>')
        
        if shape == "circle":
            svg_parts.append(f'  <circle cx="{cx}" cy="{cy}" r="36" fill="{color}"/>')
        elif shape == "square":
            svg_parts.append(f'  <rect x="{px+22}" y="{py+22}" width="66" height="66" rx="4" fill="{color}"/>')
        elif shape == "diamond":
            svg_parts.append(f'  <polygon points="{cx},{cy-41} {cx+41},{cy} {cx},{cy+41} {cx-41},{cy}" fill="{color}"/>')
        elif shape == "clover":
            svg_parts.append(f'  <g transform="translate({cx},{cy})">\n    <circle cx="0" cy="-26" r="18" fill="{color}"/>\n    <circle cx="26" cy="0" r="18" fill="{color}"/>\n    <circle cx="0" cy="26" r="18" fill="{color}"/>\n    <circle cx="-26" cy="0" r="18" fill="{color}"/>\n    <rect x="-9" y="-26" width="18" height="52" fill="{color}"/>\n    <rect x="-26" y="-9" width="52" height="18" fill="{color}"/>\n  </g>')
        elif shape == "crossx":
            svg_parts.append(f'  <g transform="translate({cx},{cy}) rotate(45)">\n    <polygon points="0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8" fill="{color}"/>\n  </g>')
        elif shape == "star":
            svg_parts.append(f'  <g transform="translate({cx},{cy})">\n    <polygon points="0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8" fill="{color}"/>\n    <polygon points="0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8" fill="{color}" transform="rotate(45)" />\n  </g>')
        else:
            svg_parts.append(f'  <text x="{cx}" y="{cy}" text-anchor="middle" font-size="12" fill="{color}" font-family="sans-serif">{tile.shape}</text>')
        svg_parts.append("")

    svg_parts.append("  <!-- ============================================ -->")
    svg_parts.append("  <!-- MY TILES (bottom center)                     -->")
    svg_parts.append("  <!-- ============================================ -->")
    svg_parts.append(f'  <text x="{svg_w//2}" y="{hand_label_y}" text-anchor="middle" font-size="18" fill="#333" font-family="sans-serif" font-weight="bold">My Tiles</text>\n')

    for idx, t in enumerate(hand_list):
        px = hand_start_x + idx * 90
        py = hand_y
        cx = px + 45
        cy = py + 45
        color = color_map.get(t.color, t.color)
        shape = t.shape.lower()

        svg_parts.append(f'  <!-- {idx+1}) {t.color} {t.shape} -->')
        svg_parts.append(f'  <rect x="{px}" y="{py}" width="90" height="90" rx="8" fill="#222"/>')

        if shape == "circle":
            svg_parts.append(f'  <circle cx="{cx}" cy="{cy}" r="30" fill="{color}"/>')
        elif shape == "square":
            svg_parts.append(f'  <rect x="{px+22}" y="{py+22}" width="44" height="44" rx="4" fill="{color}"/>')
        elif shape == "diamond":
            svg_parts.append(f'  <polygon points="{cx},{cy-30} {cx+30},{cy} {cx},{cy+30} {cx-30},{cy}" fill="{color}"/>')
        elif shape == "clover":
            svg_parts.append(f'  <g transform="translate({cx},{cy})">\n    <circle cx="0" cy="-18" r="12" fill="{color}"/>\n    <circle cx="18" cy="0" r="12" fill="{color}"/>\n    <circle cx="0" cy="18" r="12" fill="{color}"/>\n    <circle cx="-18" cy="0" r="12" fill="{color}"/>\n    <rect x="-6" y="-18" width="12" height="36" fill="{color}"/>\n  </g>')
        elif shape == "crossx":
            svg_parts.append(f'  <g transform="translate({cx},{cy}) rotate(45)">\n    <polygon points="0,-32 6,-6 32,0 6,6 0,32 -6,6 -32,0 -6,-6" fill="{color}"/>\n  </g>')
        elif shape == "star":
            svg_parts.append(f'  <g transform="translate({cx},{cy})">\n    <polygon points="0,-32 6,-6 32,0 6,6 0,32 -6,6 -32,0 -6,-6" fill="{color}"/>\n    <polygon points="0,-32 6,-6 32,0 6,6 0,32 -6,6 -32,0 -6,-6" fill="{color}" transform="rotate(45)" />\n  </g>')
        else:
            svg_parts.append(f'  <text x="{cx}" y="{cy}" text-anchor="middle" font-size="11" fill="{color}" font-family="sans-serif">{t.shape}</text>')

        # label under tile
        svg_parts.append(f'  <text x="{cx}" y="{hand_text_y}" text-anchor="middle" font-size="11" fill="#555" font-family="sans-serif">{t.color} {t.shape}</text>\n')

    svg_parts.append("</svg>")

    SVG.write_text("\n".join(svg_parts), encoding="utf-8")
    print(f"Regenerated {SVG} from {JSON} with total w={svg_w}, h={svg_h}")

if __name__ == "__main__":
    game_state, _ = load_game_state(JSON)
    with open(JSON, encoding="utf-8") as f:
        hand_list = [Tile(color=t["color"], shape=t["shape"]) for t in json.load(f)["hand"]]
    sync_svg(game_state, hand_list)
