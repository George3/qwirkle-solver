// Qwirkle interactive editor — vanilla JS frontend
// Mirrors rendering geometry/colors from sync_board.py.

const SVG_NS = "http://www.w3.org/2000/svg";
const COLORS = ["red", "orange", "yellow", "green", "blue", "purple"];
const SHAPES = ["circle", "square", "diamond", "clover", "crossx", "star"];
const COLOR_MAP = {
  red:    "#e02020",
  orange: "#ff8800",
  yellow: "#f5d000",
  green:  "#22aa33",
  blue:   "#1a6edb",
  purple: "#8833cc",
};

const TILE_SIZE = 110;
const BOARD_OFFSET_X = 50;
const BOARD_OFFSET_Y = 60;
const HAND_TILE_SIZE = 90;

let state = null;
let bounds = null; // {minX, maxX, minY, maxY, gridMinX, gridMaxX, gridMinY, gridMaxY}
let placedCoords = new Set(); // "x,y"

// ─── Rendering helpers (port of sync_board.py) ─────────────────────────

function el(tag, attrs = {}, children = []) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  for (const c of children) node.appendChild(c);
  return node;
}

function drawShape(parent, shape, color, cx, cy, px, py, scale = 1) {
  const c = COLOR_MAP[color] || color;
  shape = shape.toLowerCase();
  if (shape === "circle") {
    parent.appendChild(el("circle", { cx, cy, r: 36 * scale, fill: c }));
  } else if (shape === "square") {
    const s = 66 * scale;
    parent.appendChild(el("rect", {
      x: cx - s / 2, y: cy - s / 2, width: s, height: s, rx: 4, fill: c,
    }));
  } else if (shape === "diamond") {
    const r = 41 * scale;
    parent.appendChild(el("polygon", {
      points: `${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`,
      fill: c,
    }));
  } else if (shape === "clover") {
    const g = el("g", { transform: `translate(${cx},${cy}) scale(${scale})` });
    g.appendChild(el("circle", { cx: 0, cy: -26, r: 18, fill: c }));
    g.appendChild(el("circle", { cx: 26, cy: 0, r: 18, fill: c }));
    g.appendChild(el("circle", { cx: 0, cy: 26, r: 18, fill: c }));
    g.appendChild(el("circle", { cx: -26, cy: 0, r: 18, fill: c }));
    g.appendChild(el("rect", { x: -9, y: -26, width: 18, height: 52, fill: c }));
    g.appendChild(el("rect", { x: -26, y: -9, width: 52, height: 18, fill: c }));
    parent.appendChild(g);
  } else if (shape === "crossx") {
    const g = el("g", { transform: `translate(${cx},${cy}) rotate(45) scale(${scale})` });
    g.appendChild(el("polygon", {
      points: "0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8",
      fill: c,
    }));
    parent.appendChild(g);
  } else if (shape === "star") {
    const g = el("g", { transform: `translate(${cx},${cy}) scale(${scale})` });
    g.appendChild(el("polygon", {
      points: "0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8",
      fill: c,
    }));
    g.appendChild(el("polygon", {
      points: "0,-42 8,-8 42,0 8,8 0,42 -8,8 -42,0 -8,-8",
      fill: c, transform: "rotate(45)",
    }));
    parent.appendChild(g);
  } else {
    parent.appendChild(el("text", {
      x: cx, y: cy + 4, "text-anchor": "middle", "font-size": 12, fill: c,
    }, [document.createTextNode(shape)]));
  }
}

function computeBounds(boardTiles) {
  if (boardTiles.length === 0) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0, gridMinX: -2, gridMaxX: 2, gridMinY: -2, gridMaxY: 2 };
  }
  const xs = boardTiles.map(t => t.x);
  const ys = boardTiles.map(t => t.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  return {
    minX, maxX, minY, maxY,
    gridMinX: minX - 2, gridMaxX: maxX + 2,
    gridMinY: minY - 2, gridMaxY: maxY + 2,
  };
}

function getPx(x, y) {
  const px = BOARD_OFFSET_X + (x - bounds.gridMinX) * TILE_SIZE;
  const py = BOARD_OFFSET_Y + (bounds.gridMaxY - y) * TILE_SIZE;
  return { px, py, cx: px + TILE_SIZE / 2, cy: py + TILE_SIZE / 2 };
}

// ─── Board render ──────────────────────────────────────────────────────

function flattenBoardTiles() {
  const out = [];
  for (const move of state.moves || []) {
    for (const t of move.tiles || []) out.push(t);
  }
  return out;
}

function renderBoard() {
  const svg = document.getElementById("board");
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const boardTiles = flattenBoardTiles();
  bounds = computeBounds(boardTiles);
  placedCoords = new Set(boardTiles.map(t => `${t.x},${t.y}`));

  const cols = bounds.gridMaxX - bounds.gridMinX + 1;
  const rows = bounds.gridMaxY - bounds.gridMinY + 1;
  const w = BOARD_OFFSET_X * 2 + cols * TILE_SIZE;
  const h = BOARD_OFFSET_Y + rows * TILE_SIZE;
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);

  // axis labels
  for (let x = bounds.gridMinX; x <= bounds.gridMaxX; x++) {
    const { cx } = getPx(x, bounds.gridMaxY);
    const t = el("text", {
      x: cx, y: BOARD_OFFSET_Y - 12, "text-anchor": "middle",
      "font-size": 36, fill: "#777", "font-family": "monospace",
    });
    t.textContent = x;
    svg.appendChild(t);
  }
  for (let y = bounds.gridMinY; y <= bounds.gridMaxY; y++) {
    const { cy } = getPx(bounds.gridMinX, y);
    const t = el("text", {
      x: BOARD_OFFSET_X - 20, y: cy + 4, "text-anchor": "middle",
      "font-size": 36, fill: "#777", "font-family": "monospace",
    });
    t.textContent = y;
    svg.appendChild(t);
  }

  // empty cells (clickable)
  for (let x = bounds.gridMinX; x <= bounds.gridMaxX; x++) {
    for (let y = bounds.gridMinY; y <= bounds.gridMaxY; y++) {
      if (placedCoords.has(`${x},${y}`)) continue;
      const { px, py } = getPx(x, y);
      const adjacent = isAdjacent(x, y);
      const rect = el("rect", {
        x: px + 2, y: py + 2,
        width: TILE_SIZE - 4, height: TILE_SIZE - 4,
        rx: 8,
      });
      rect.setAttribute("class", "cell-empty" + (adjacent || placedCoords.size === 0 ? " adjacent" : ""));
      rect.addEventListener("click", () => {
        if (adjacent || placedCoords.size === 0) openBoardPicker(x, y);
      });
      svg.appendChild(rect);
    }
  }

  // placed tiles
  for (const t of boardTiles) {
    const { px, py, cx, cy } = getPx(t.x, t.y);
    const g = el("g", { class: "tile-group" });
    g.addEventListener("click", () => openTilePopover(t));
    g.appendChild(el("rect", { x: px, y: py, width: 110, height: 110, rx: 8, fill: "#222" }));
    drawShape(g, t.shape, t.color, cx, cy, px, py, 1);
    svg.appendChild(g);
  }
}

function isAdjacent(x, y) {
  for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
    if (placedCoords.has(`${x + dx},${y + dy}`)) return true;
  }
  return false;
}

// ─── Hand render ───────────────────────────────────────────────────────

const HAND_SLOTS = 6;

function renderHand() {
  const svg = document.getElementById("hand");
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const hand = state.hand || [];
  const w = HAND_SLOTS * (HAND_TILE_SIZE + 10);
  const h = HAND_TILE_SIZE + 20;
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);

  for (let i = 0; i < HAND_SLOTS; i++) {
    const px = i * (HAND_TILE_SIZE + 10) + 5;
    const py = 5;
    const cx = px + HAND_TILE_SIZE / 2;
    const cy = py + HAND_TILE_SIZE / 2;
    const tile = hand[i];

    if (tile) {
      const g = el("g", { class: "tile-group" });
      g.addEventListener("click", () => openHandPicker(i, tile));
      g.appendChild(el("rect", { x: px, y: py, width: HAND_TILE_SIZE, height: HAND_TILE_SIZE, rx: 8, fill: "#222" }));
      drawShape(g, tile.shape, tile.color, cx, cy, px, py, 0.82);
      svg.appendChild(g);
    } else {
      const slot = el("rect", { x: px, y: py, width: HAND_TILE_SIZE, height: HAND_TILE_SIZE, rx: 8 });
      slot.setAttribute("class", "hand-slot-empty");
      slot.addEventListener("click", () => openHandPicker(i, null));
      svg.appendChild(slot);
      const plus = el("text", {
        x: cx, y: cy + 8, "text-anchor": "middle", "font-size": 28, fill: "#888",
      });
      plus.textContent = "+";
      svg.appendChild(plus);
    }
  }
}

// ─── Picker modal ──────────────────────────────────────────────────────

let pickerContext = null; // {kind: 'board'|'hand', ...args}

function openBoardPicker(x, y) {
  pickerContext = { kind: "board", x, y };
  showPicker(`Place tile at (${x}, ${y})`, false);
}

function openTilePopover(tile) {
  pickerContext = { kind: "board-edit", x: tile.x, y: tile.y };
  showPicker(`Edit tile at (${tile.x}, ${tile.y})`, true);
}

function openHandPicker(slotIndex, existingTile) {
  pickerContext = { kind: "hand", slotIndex };
  const title = existingTile
    ? `Replace hand slot ${slotIndex + 1} (${existingTile.color} ${existingTile.shape})`
    : `Add tile to hand slot ${slotIndex + 1}`;
  showPicker(title, !!existingTile);
}

function showPicker(title, showRemove) {
  document.getElementById("picker-title").textContent = title;
  const grid = document.getElementById("picker-grid");
  grid.innerHTML = "";

  for (const color of COLORS) {
    for (const shape of SHAPES) {
      const btn = document.createElement("button");
      btn.className = "swatch";
      btn.title = `${color} ${shape}`;

      const svg = document.createElementNS(SVG_NS, "svg");
      svg.setAttribute("viewBox", "0 0 56 56");
      svg.setAttribute("width", 52);
      svg.setAttribute("height", 52);
      drawShape(svg, shape, color, 28, 28, 0, 0, 0.5);
      btn.appendChild(svg);

      btn.addEventListener("click", () => onPickerChoice(color, shape));
      grid.appendChild(btn);
    }
  }

  const removeBtn = document.getElementById("picker-remove");
  if (showRemove) removeBtn.classList.remove("hidden");
  else removeBtn.classList.add("hidden");

  document.getElementById("picker-overlay").classList.remove("hidden");
}

function hidePicker() {
  document.getElementById("picker-overlay").classList.add("hidden");
  pickerContext = null;
}

async function onPickerChoice(color, shape) {
  if (!pickerContext) return;
  if (pickerContext.kind === "board") {
    const { x, y } = pickerContext;
    hidePicker();
    await api("/api/board/place", { x, y, color, shape });
    await refresh();
  } else if (pickerContext.kind === "board-edit") {
    const { x, y } = pickerContext;
    hidePicker();
    await api("/api/board/replace", { x, y, color, shape });
    await refresh();
  } else if (pickerContext.kind === "hand") {
    const { slotIndex } = pickerContext;
    const hand = (state.hand || []).slice();
    hand[slotIndex] = { color, shape };
    const tiles = hand.filter(Boolean).slice(0, HAND_SLOTS);
    hidePicker();
    await api("/api/hand", { tiles });
    await refresh();
  }
}

async function onPickerRemove() {
  if (!pickerContext) return;
  if (pickerContext.kind === "board-edit") {
    const { x, y } = pickerContext;
    hidePicker();
    await api("/api/board/remove", { x, y });
    await refresh();
  } else if (pickerContext.kind === "hand") {
    const { slotIndex } = pickerContext;
    const hand = (state.hand || []).slice();
    hand.splice(slotIndex, 1);
    hidePicker();
    await api("/api/hand", { tiles: hand });
    await refresh();
  }
}

// ─── API ──────────────────────────────────────────────────────────────

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    setStatus(`Error: ${err.detail || res.statusText}`);
    throw new Error(err.detail || res.statusText);
  }
  return await res.json();
}

function setStatus(msg) {
  document.getElementById("status").textContent = msg;
  setTimeout(() => { document.getElementById("status").textContent = ""; }, 4000);
}

async function refresh() {
  const res = await fetch("/api/state");
  state = await res.json();
  renderBoard();
  renderHand();
  const total = flattenBoardTiles().length;
  setStatus(`${total} tiles on board · ${(state.hand || []).length}/6 in hand`);
}

// ─── Init ─────────────────────────────────────────────────────────────

document.getElementById("new-game-btn").addEventListener("click", async () => {
  if (!confirm("Start a new game? This will clear the board and deal 6 random tiles.")) return;
  await api("/api/new_game", {});
  await refresh();
});

document.getElementById("picker-cancel").addEventListener("click", hidePicker);
document.getElementById("picker-remove").addEventListener("click", onPickerRemove);
document.getElementById("picker-overlay").addEventListener("click", (e) => {
  if (e.target.id === "picker-overlay") hidePicker();
});

refresh().catch(err => setStatus(`Failed to load: ${err.message}`));
