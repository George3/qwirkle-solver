#!/usr/bin/env python3
"""Sync board.svg with `game_state` and `my_tiles` in `qwirkle-solver.py`.

Usage: python sync_board.py
"""
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path(__file__).parent
PY = ROOT / "qwirkle-solver.py"
SVG = ROOT / "board.svg"


@dataclass(frozen=True)
class Tile:
    color: str
    shape: str


def _find_matching(text: str, start: int, open_char: str, close_char: str) -> int:
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == open_char:
            depth += 1
        elif c == close_char:
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("No matching closing char found")


def extract_game_state_and_hand(py_text: str):
    # Extract game_state dict literal
    m = re.search(r"game_state\s*=\s*\{", py_text)
    game_state = {}
    if m:
        open_idx = py_text.find("{", m.start())
        close_idx = _find_matching(py_text, open_idx, "{", "}")
        dict_src = py_text[open_idx: close_idx + 1]
        ns = {"Tile": Tile}
        game_state = eval(dict_src, ns)

    # Extract list literal inside Counter([...]) for my_tiles to preserve order
    m2 = re.search(r"my_tiles\s*=\s*Counter\s*\(\s*\[", py_text)
    hand_list = []
    if m2:
        open_idx = py_text.find("[", m2.start())
        close_idx = _find_matching(py_text, open_idx, "[", "]")
        list_src = py_text[open_idx: close_idx + 1]
        ns = {"Tile": Tile}
        hand_list = eval(list_src, ns)

    return game_state, hand_list


def svg_px_py(x: int, y: int):
    px = 45 + x * 110
    py = 605 - (y + 2) * 110
    cx = px + 55
    cy = py + 55
    return px, py, cx, cy


def sync_svg(game_state: dict, hand_list: list):

    if not SVG.exists():
        raise SystemExit(f"{SVG} not found")

    # Backup SVG before overwriting
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = SVG.with_name(f"{SVG.name}.bak-{now}")
    shutil.copy2(SVG, backup_path)
    print(f"Backed up {SVG} to {backup_path}")

    s = SVG.read_text(encoding="utf-8")

    # Replace coordinate comments like <!-- (x,y) ... -->
    def board_comment_repl(m):
        gx = int(m.group(1))
        gy = int(m.group(2))
        tile = game_state.get((gx, gy))
        if tile is None:
            return m.group(0)
        px, py, cx, cy = svg_px_py(gx, gy)
        return f"<!-- ({gx},{gy}) {tile.color} {tile.shape}  |  px={px} py={py}  cx={cx} cy={cy} -->"

    s = re.sub(r"<!--\s*\((-?\d+),\s*(-?\d+)\)\s*[^>]*-->", board_comment_repl, s)

    # Always regenerate the big TILES and MY TILES sections from source
    color_map = {
        "red": "#e02020",
        "blue": "#1a6edb",
        "green": "#22aa33",
        "orange": "#ff8800",
        "yellow": "#f5d000",
        "purple": "#8833cc",
    }

    def render_tile_svg(gx: int, gy: int, tile: Tile) -> str:
        px, py, cx, cy = svg_px_py(gx, gy)
        color = color_map.get(tile.color, tile.color)
        parts = []
        parts.append(f"  <!-- ({gx},{gy}) {tile.color} {tile.shape}  |  px={px} py={py}  cx={cx} cy={cy} -->")
        parts.append(f"  <rect x=\"{px}\" y=\"{py}\" width=\"110\" height=\"110\" rx=\"8\" fill=\"#222\"/>")
        shape = tile.shape.lower()
        if shape == "circle":
            parts.append(f"  <circle cx=\"{cx}\" cy=\"{cy}\" r=\"36\" fill=\"{color}\"/>")
        elif shape == "square":
            parts.append(f"  <rect x=\"{px+22}\" y=\"{py+22}\" width=\"66\" height=\"66\" rx=\"4\" fill=\"{color}\"/>")
        elif shape == "diamond":
            parts.append(f"  <polygon points=\"{cx},{cy-41} {cx+41},{cy} {cx},{cy+41} {cx-41},{cy}\" fill=\"{color}\"/>")
        elif shape == "clover":
            parts.append(
                f"  <g transform=\"translate({cx},{cy})\">\n    <circle cx=\"0\" cy=\"-26\" r=\"18\" fill=\"{color}\"/>\n    <circle cx=\"26\" cy=\"0\" r=\"18\" fill=\"{color}\"/>\n    <circle cx=\"0\" cy=\"26\" r=\"18\" fill=\"{color}\"/>\n    <circle cx=\"-26\" cy=\"0\" r=\"18\" fill=\"{color}\"/>\n    <rect x=\"-9\" y=\"-26\" width=\"18\" height=\"52\" fill=\"{color}\"/>\n    <rect x=\"-26\" y=\"-9\" width=\"52\" height=\"18\" fill=\"{color}\"/>\n  </g>")
        elif shape == "crossx":
            parts.append(
                f"  <g transform=\"translate({cx},{cy}) rotate(45)\">\n    <polygon points=\"0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8\" fill=\"{color}\"/>\n  </g>")
        elif shape == "star":
            parts.append(
                f"  <g transform=\"translate({cx},{cy})\">\n    <polygon points=\"0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8\" fill=\"{color}\"/>\n    <polygon points=\"0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8\" fill=\"{color}\" transform=\"rotate(45)\" />\n  </g>")
        else:
            parts.append(f"  <text x=\"{cx}\" y=\"{cy}\" text-anchor=\"middle\" font-size=\"12\" fill=\"{color}\" font-family=\"sans-serif\">{tile.shape}</text>")
        return "\n".join(parts)

    board_tiles = []
    for (gx, gy), tile in sorted(game_state.items(), key=lambda kv: (kv[0][0], -kv[0][1])):
        board_tiles.append(render_tile_svg(gx, gy, tile))

    board_section = (
        "  <!-- ============================================ -->\n"
        "  <!-- TILES                                        -->\n"
        "  <!-- ============================================ -->\n\n"
        + "\n\n".join(board_tiles)
        + "\n\n  <!-- ============================================ -->\n  <!-- Legend                                       -->\n  <!-- ============================================ -->\n"
    )

    # Build My Tiles section
    # Remove spaces between tiles: each tile is 90px wide, so x = 90 + idx*90
    hand_parts = [
        "  <!-- ============================================ -->",
        "  <!-- MY TILES (bottom center)                     -->",
        "  <!-- ============================================ -->",
        "  <text x=\"410\" y=\"765\" text-anchor=\"middle\" font-size=\"18\" fill=\"#333\" font-family=\"sans-serif\" font-weight=\"bold\">My Tiles</text>\n",
    ]

    for idx, t in enumerate(hand_list):
        px = 90 + idx * 90  # No gap between tiles
        py = 790
        cx = px + 45
        cy = py + 45
        color = color_map.get(t.color, t.color)
        hand_parts.append(f"  <!-- {idx+1}) {t.color} {t.shape} -->")
        hand_parts.append(f"  <rect x=\"{px}\" y=\"{py}\" width=\"90\" height=\"90\" rx=\"8\" fill=\"#222\"/>")
        shape = t.shape.lower()
        if shape == "circle":
            hand_parts.append(f"  <circle cx=\"{cx}\" cy=\"{cy}\" r=\"30\" fill=\"{color}\"/>")
        elif shape == "square":
            hand_parts.append(f"  <rect x=\"{px+22}\" y=\"{py+22}\" width=\"44\" height=\"44\" rx=\"4\" fill=\"{color}\"/>")
        elif shape == "diamond":
            hand_parts.append(f"  <polygon points=\"{cx},{cy-30} {cx+30},{cy} {cx},{cy+30} {cx-30},{cy}\" fill=\"{color}\"/>")
        elif shape == "clover":
            hand_parts.append(f"""  <g transform="translate({cx},{cy})">
    <circle cx="0" cy="-18" r="12" fill="{color}"/>
    <circle cx="18" cy="0" r="12" fill="{color}"/>
    <circle cx="0" cy="18" r="12" fill="{color}"/>
    <circle cx="-18" cy="0" r="12" fill="{color}"/>
    <rect x="-6" y="-18" width="12" height="36" fill="{color}"/>
  </g>""")
        elif shape == "crossx":
            hand_parts.append(f"""  <g transform="translate({cx},{cy}) rotate(45)">
    <polygon points="0,-32 6,-6 32,0 6,6 0,32 -6,6 -32,0 -6,-6" fill="{color}"/>
  </g>""")
        elif shape == "star":
            hand_parts.append(f"""  <g transform="translate({cx},{cy})">
    <polygon points="0,-32 6,-6 32,0 6,6 0,32 -6,6 -32,0 -6,-6" fill="{color}"/>
    <polygon points="0,-32 6,-6 32,0 6,6 0,32 -6,6 -32,0 -6,-6" fill="{color}" transform="rotate(45)" />
  </g>""")
        else:
            hand_parts.append(f"  <text x=\"{cx}\" y=\"{cy}\" text-anchor=\"middle\" font-size=\"11\" fill=\"{color}\" font-family=\"sans-serif\">{t.shape}</text>")

        # label under tile
        hand_parts.append(f"  <text x=\"{cx}\" y=\"900\" text-anchor=\"middle\" font-size=\"11\" fill=\"#555\" font-family=\"sans-serif\">{t.color} {t.shape}</text>\n")

    hand_section = "\n".join(hand_parts)

    # Replace existing TILES ... Legend block
    s_new = re.sub(r"<!-- =+ -->\n\s*<!-- TILES[\s\S]*?<!-- =+ -->\n\s*<!-- Legend[\s\S]*?<!-- =+ -->\n",
                   board_section, s, count=1)

    # Replace existing MY TILES block (after Legend) and insert our hand_section before </svg>
    if "<!-- MY TILES" in s_new:
        s_new = re.sub(r"<!-- =+ -->\n\s*<!-- MY TILES[\s\S]*?</svg>", hand_section + "\n</svg>", s_new, count=1)
    else:
        # append before </svg>
        s_new = s_new.replace("</svg>", hand_section + "\n</svg>")

    SVG.write_text(s_new, encoding="utf-8")
    print(f"Regenerated {SVG} from {PY}")


if __name__ == "__main__":
    py_text = PY.read_text(encoding="utf-8")
    game_state, hand_list = extract_game_state_and_hand(py_text)
    sync_svg(game_state, hand_list)
