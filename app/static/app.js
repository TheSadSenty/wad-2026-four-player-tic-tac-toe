const symbols = ["X", "O", "▽", "●"];
const playerColors = ["#ef476f", "#ffd166", "#06d6a0", "#118ab2"];

const boardElement = document.querySelector("#board");
const statusText = document.querySelector("#status-text");
const playerForm = document.querySelector("#player-form");
const resetButton = document.querySelector("#reset-button");
const rankingsBody = document.querySelector("#rankings-body");
const legend = document.querySelector("#legend");

let state = null;

function renderLegend(players = []) {
    legend.innerHTML = "";
    symbols.forEach((symbol, index) => {
        const item = document.createElement("div");
        item.className = "legend-item";
        item.style.setProperty("--accent", playerColors[index]);
        const name = players[index]?.name || `Player ${symbol}`;
        item.innerHTML = `<strong>${symbol}</strong><span>${name}</span>`;
        legend.appendChild(item);
    });
}

function renderBoard() {
    boardElement.innerHTML = "";

    if (!state?.hasGame) {
        boardElement.classList.add("board-idle");
        for (let i = 0; i < 36; i += 1) {
            const idleCell = document.createElement("div");
            idleCell.className = "cell idle";
            idleCell.textContent = "·";
            boardElement.appendChild(idleCell);
        }
        return;
    }

    boardElement.classList.remove("board-idle");
    boardElement.style.setProperty("--size", state.boardSize);

    state.board.forEach((row, rowIndex) => {
        row.forEach((cell, colIndex) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "cell";
            button.dataset.row = rowIndex;
            button.dataset.col = colIndex;
            button.disabled = state.status !== "in_progress" || Boolean(cell);

            if (cell) {
                button.textContent = cell;
                const colorIndex = symbols.indexOf(cell);
                button.style.setProperty("--accent", playerColors[colorIndex]);
                button.classList.add("occupied");
            } else {
                button.textContent = "";
            }

            boardElement.appendChild(button);
        });
    });
}

function renderStatus() {
    statusText.textContent = state?.message || "Start a new game to begin.";
    renderLegend(state?.players || []);
}

function renderRankings(rankings) {
    rankingsBody.innerHTML = "";

    if (!rankings.length) {
        rankingsBody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">No ranked games yet.</td>
            </tr>
        `;
        return;
    }

    rankings.forEach((player) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${player.player_name}</td>
            <td>${player.points}</td>
            <td>${player.wins}</td>
            <td>${player.draws}</td>
            <td>${player.losses}</td>
            <td>${player.games_played}</td>
        `;
        rankingsBody.appendChild(row);
    });
}

async function refreshRankings() {
    const response = await fetch("/api/rankings");
    const payload = await response.json();
    renderRankings(payload.rankings);
}

async function refreshGame() {
    const response = await fetch("/api/game");
    state = await response.json();
    renderStatus();
    renderBoard();
}

async function postJson(url, payload = {}) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }
    return data;
}

playerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const players = [...new FormData(playerForm).getAll("player")];

    try {
        state = await postJson("/api/game", { players });
        renderStatus();
        renderBoard();
    } catch (error) {
        statusText.textContent = error.message;
    }
});

resetButton.addEventListener("click", async () => {
    try {
        state = await postJson("/api/game/reset");
        renderStatus();
        renderBoard();
    } catch (error) {
        statusText.textContent = error.message;
    }
});

boardElement.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-row]");
    if (!button) {
        return;
    }

    try {
        state = await postJson("/api/move", {
            row: Number(button.dataset.row),
            col: Number(button.dataset.col),
        });
        renderStatus();
        renderBoard();
        if (state.status === "finished") {
            await refreshRankings();
        }
    } catch (error) {
        statusText.textContent = error.message;
    }
});

refreshGame();
refreshRankings();
