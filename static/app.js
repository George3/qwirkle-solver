const colorMap = {
  red: "#e02020",
  orange: "#ff8800",
  yellow: "#f5d000",
  green: "#22aa33",
  blue: "#1a6edb",
  purple: "#8833cc",
};

const state = {
  board: [],
  hand: [],
  bounds: { min_x: -2, max_x: 2, min_y: -2, max_y: 2 },
  palette: [],
  selectedPaletteTile: null,
  pendingPlacements: [],
  legalDrops: new Set(),
  mode: "play",
  draggedHandTile: null,
};

const elements = {
  boardGrid: document.getElementById("board-grid"),
  boardStatus: document.getElementById("board-status"),
  handList: document.getElementById("hand-list"),
  paletteGrid: document.getElementById("palette-grid"),
  suggestionsList: document.getElementById("suggestions-list"),
  selectedTileLabel: document.getElementById("selected-tile-label"),
  commitButton: document.getElementById("commit-button"),
  clearPendingButton: document.getElementById("clear-pending-button"),
  resetButton: document.getElementById("reset-button"),
  addToHandButton: document.getElementById("add-to-hand-button"),
  removeSelectedFromHandButton: document.getElementById("remove-selected-from-hand-button"),
  suggestionsButton: document.getElementById("suggestions-button"),
  modePlay: document.getElementById("mode-play"),
  modeSetup: document.getElementById("mode-setup"),
};

function tileKey(tile) {
  return `${tile.color}:${tile.shape}`;
}

function cellKey(x, y) {
  return `${x},${y}`;
}

function getBoardTile(x, y) {
  return state.board.find((entry) => entry.x === x && entry.y === y)?.tile ?? null;
}

function getPendingTile(x, y) {
  return state.pendingPlacements.find((entry) => entry.x === x && entry.y === y)?.tile ?? null;
}

function svgForTile(tile) {
  const fill = colorMap[tile.color];
  if (tile.shape === "circle") {
    return `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="30" fill="${fill}"></circle></svg>`;
  }
  if (tile.shape === "square") {
    return `<svg viewBox="0 0 100 100"><rect x="20" y="20" width="60" height="60" rx="4" fill="${fill}"></rect></svg>`;
  }
  if (tile.shape === "diamond") {
    return `<svg viewBox="0 0 100 100"><polygon points="50,13 87,50 50,87 13,50" fill="${fill}"></polygon></svg>`;
  }
  if (tile.shape === "clover") {
    return `
      <svg viewBox="0 0 100 100">
        <circle cx="50" cy="27" r="15" fill="${fill}"></circle>
        <circle cx="73" cy="50" r="15" fill="${fill}"></circle>
        <circle cx="50" cy="73" r="15" fill="${fill}"></circle>
        <circle cx="27" cy="50" r="15" fill="${fill}"></circle>
        <rect x="42" y="27" width="16" height="46" fill="${fill}"></rect>
        <rect x="27" y="42" width="46" height="16" fill="${fill}"></rect>
      </svg>
    `;
  }
  if (tile.shape === "crossX") {
    return `
      <svg viewBox="0 0 100 100">
        <g transform="translate(50 50) rotate(45)">
          <polygon points="0,-36 7,-7 36,0 7,7 0,36 -7,7 -36,0 -7,-7" fill="${fill}"></polygon>
        </g>
      </svg>
    `;
  }
  return `
    <svg viewBox="0 0 100 100">
      <g transform="translate(50 50)">
        <polygon points="0,-36 7,-7 36,0 7,7 0,36 -7,7 -36,0 -7,-7" fill="${fill}"></polygon>
        <polygon points="0,-36 7,-7 36,0 7,7 0,36 -7,7 -36,0 -7,-7" fill="${fill}" transform="rotate(45)"></polygon>
      </g>
    </svg>
  `;
}

function makeTileNode(tile) {
  const template = document.getElementById("tile-template");
  const node = template.content.firstElementChild.cloneNode(true);
  node.querySelector(".tile-art").innerHTML = svgForTile(tile);
  return node;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}

function renderPalette() {
  elements.paletteGrid.innerHTML = "";
  for (const tile of state.palette) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "palette-item";
    if (state.selectedPaletteTile && tileKey(state.selectedPaletteTile) === tileKey(tile)) {
      item.classList.add("selected");
    }
    item.appendChild(makeTileNode(tile));

    const meta = document.createElement("div");
    meta.className = "tile-meta";
    meta.textContent = `${tile.color} ${tile.shape}`;
    item.appendChild(meta);

    item.addEventListener("click", () => {
      state.selectedPaletteTile = tile;
      updateModeButtons();
      renderPalette();
    });

    elements.paletteGrid.appendChild(item);
  }
  elements.selectedTileLabel.textContent = state.selectedPaletteTile
    ? `Selected: ${state.selectedPaletteTile.color} ${state.selectedPaletteTile.shape}`
    : "Selected: none";
}

function renderHand() {
  elements.handList.innerHTML = "";
  if (state.hand.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-note";
    empty.textContent = "Your hand is empty.";
    elements.handList.appendChild(empty);
    return;
  }

  for (const entry of state.hand) {
    const item = document.createElement("div");
    item.className = "hand-item";
    item.draggable = true;
    item.appendChild(makeTileNode(entry.tile));

    const meta = document.createElement("div");
    meta.className = "tile-meta";
    meta.innerHTML = `${entry.tile.color} ${entry.tile.shape}<span class="count-pill">x${entry.count}</span>`;
    item.appendChild(meta);

    item.addEventListener("dragstart", async (event) => {
      state.draggedHandTile = entry.tile;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", tileKey(entry.tile));
      await refreshLegalDrops(entry.tile);
    });

    item.addEventListener("dragend", () => {
      state.draggedHandTile = null;
      state.legalDrops.clear();
      renderBoard();
    });

    elements.handList.appendChild(item);
  }
}

function updateModeButtons() {
  elements.modePlay.classList.toggle("active", state.mode === "play");
  elements.modeSetup.classList.toggle("active", state.mode === "setup");
}

function renderBoardStatus() {
  if (state.pendingPlacements.length === 0) {
    elements.boardStatus.textContent = state.mode === "setup"
      ? "Setup mode: click a selected palette tile onto the board."
      : "No pending move.";
    return;
  }

  const placementsText = state.pendingPlacements
    .map((entry) => `(${entry.x}, ${entry.y}) ${entry.tile.color} ${entry.tile.shape}`)
    .join(" | ");
  elements.boardStatus.textContent = `Pending: ${placementsText}`;
}

function renderBoard() {
  const { min_x, max_x, min_y, max_y } = state.bounds;
  const cols = max_x - min_x + 1;

  elements.boardGrid.style.gridTemplateColumns = `repeat(${cols}, 58px)`;
  elements.boardGrid.innerHTML = "";
  renderBoardStatus();

  for (let y = max_y; y >= min_y; y -= 1) {
    for (let x = min_x; x <= max_x; x += 1) {
      const cell = document.createElement("div");
      cell.className = "board-cell";
      cell.dataset.coord = `${x},${y}`;

      const boardTile = getBoardTile(x, y);
      const pendingTile = getPendingTile(x, y);
      if (boardTile || pendingTile) {
        cell.appendChild(makeTileNode(pendingTile || boardTile));
      }
      if (pendingTile) {
        cell.classList.add("pending");
      }
      if (state.legalDrops.has(cellKey(x, y))) {
        cell.classList.add("legal");
      }
      if (state.mode === "setup" && state.selectedPaletteTile && !boardTile) {
        cell.classList.add("setup-selected");
      }

      cell.addEventListener("dragover", (event) => {
        if (state.legalDrops.has(cellKey(x, y))) {
          event.preventDefault();
          event.dataTransfer.dropEffect = "move";
        }
      });

      cell.addEventListener("drop", async (event) => {
        event.preventDefault();
        if (!state.draggedHandTile || !state.legalDrops.has(cellKey(x, y))) {
          return;
        }
        state.pendingPlacements.push({ x, y, tile: state.draggedHandTile });
        state.draggedHandTile = null;
        state.legalDrops.clear();
        await updatePreview();
        renderBoard();
      });

      cell.addEventListener("click", async () => {
        if (pendingTile) {
          state.pendingPlacements = state.pendingPlacements.filter((entry) => !(entry.x === x && entry.y === y));
          renderBoard();
          return;
        }

        if (boardTile && state.mode === "setup") {
          await fetchJson("/api/board/remove", {
            method: "POST",
            body: JSON.stringify({ x, y }),
          });
          await loadState();
          return;
        }

        if (state.mode === "setup" && state.selectedPaletteTile && !boardTile) {
          try {
            await fetchJson("/api/board/place", {
              method: "POST",
              body: JSON.stringify({ x, y, tile: state.selectedPaletteTile }),
            });
            await loadState();
          } catch (error) {
            alert(error.message);
          }
        }
      });

      elements.boardGrid.appendChild(cell);
    }
  }
}

function renderSuggestions(suggestions = []) {
  elements.suggestionsList.innerHTML = "";
  if (suggestions.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-note";
    empty.textContent = "No suggestions yet.";
    elements.suggestionsList.appendChild(empty);
    return;
  }

  for (const suggestion of suggestions) {
    const item = document.createElement("div");
    item.className = "suggestion-item";

    const score = document.createElement("div");
    score.className = "suggestion-score";
    score.textContent = `${suggestion.score} points`;
    item.appendChild(score);

    const placements = document.createElement("div");
    placements.className = "suggestion-placements";
    placements.textContent = suggestion.placements
      .map((entry) => `(${entry.x}, ${entry.y}) ${entry.tile.color} ${entry.tile.shape}`)
      .join(" | ");
    item.appendChild(placements);

    elements.suggestionsList.appendChild(item);
  }
}

async function refreshLegalDrops(tile) {
  const data = await fetchJson("/api/legal-drops", {
    method: "POST",
    body: JSON.stringify({ tile, placements: state.pendingPlacements }),
  });
  state.legalDrops = new Set(data.positions.map((entry) => cellKey(entry.x, entry.y)));
  state.bounds = data.bounds;
  renderBoard();
}

async function updatePreview() {
  if (state.pendingPlacements.length === 0) {
    return;
  }
  const preview = await fetchJson("/api/turn/preview", {
    method: "POST",
    body: JSON.stringify({ placements: state.pendingPlacements }),
  });
  const scoreText = preview.score === null ? "invalid" : `${preview.score} points`;
  elements.boardStatus.textContent = preview.legal
    ? `Pending move is legal: ${scoreText}`
    : "Pending move is not legal.";
}

async function loadState() {
  const data = await fetchJson("/api/state");
  state.board = data.board;
  state.hand = data.hand;
  state.bounds = data.bounds;
  state.palette = data.palette;
  state.legalDrops.clear();
  renderPalette();
  renderHand();
  renderBoard();
}

elements.modePlay.addEventListener("click", () => {
  state.mode = "play";
  updateModeButtons();
  renderBoard();
});

elements.modeSetup.addEventListener("click", () => {
  state.mode = "setup";
  updateModeButtons();
  renderBoard();
});

elements.addToHandButton.addEventListener("click", async () => {
  if (!state.selectedPaletteTile) {
    alert("Select a palette tile first.");
    return;
  }
  await fetchJson("/api/hand/add", {
    method: "POST",
    body: JSON.stringify({ tile: state.selectedPaletteTile }),
  });
  await loadState();
});

elements.removeSelectedFromHandButton.addEventListener("click", async () => {
  if (!state.selectedPaletteTile) {
    alert("Select a palette tile first.");
    return;
  }
  try {
    await fetchJson("/api/hand/remove", {
      method: "POST",
      body: JSON.stringify({ tile: state.selectedPaletteTile }),
    });
    await loadState();
  } catch (error) {
    alert(error.message);
  }
});

elements.clearPendingButton.addEventListener("click", () => {
  state.pendingPlacements = [];
  state.legalDrops.clear();
  renderBoard();
});

elements.commitButton.addEventListener("click", async () => {
  if (state.pendingPlacements.length === 0) {
    alert("No pending move to commit.");
    return;
  }
  try {
    const data = await fetchJson("/api/turn/commit", {
      method: "POST",
      body: JSON.stringify({ placements: state.pendingPlacements }),
    });
    state.pendingPlacements = [];
    state.board = data.board;
    state.hand = data.hand;
    state.bounds = data.bounds;
    state.legalDrops.clear();
    renderHand();
    renderBoard();
    if (typeof data.last_score === "number") {
      elements.boardStatus.textContent = `Committed move for ${data.last_score} points.`;
    }
  } catch (error) {
    alert(error.message);
  }
});

elements.resetButton.addEventListener("click", async () => {
  if (!window.confirm("Reset the board and hand?")) {
    return;
  }
  await fetchJson("/api/reset", { method: "POST", body: JSON.stringify({}) });
  state.pendingPlacements = [];
  renderSuggestions([]);
  await loadState();
});

elements.suggestionsButton.addEventListener("click", async () => {
  const data = await fetchJson("/api/suggestions");
  renderSuggestions(data.suggestions);
});

loadState().catch((error) => {
  alert(error.message);
});