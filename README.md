# Four-Player Tic-Tac-Toe

Web game with a Python backend, four-player turn rotation, automatic winner detection, and a persistent ranking table.

## Stack

- Python 3.13
- Flask
- SQLite
- Vanilla HTML, CSS, and JavaScript

## Rules

- 4 players join each match: `X`, `O`, `▽`, and `●`
- The board is `6 x 6`
- A player wins by connecting `4` of their own symbols horizontally, vertically, or diagonally
- Ranking points:
  - Win: `3`
  - Draw: `1`
  - Loss: `0`

## Run

```bash
uv sync
uv run python -m app
```

Then open `http://127.0.0.1:5000`.

## Docker

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8000`.

The image installs dependencies with `uv sync --frozen --no-dev` from `uv.lock`, then runs Gunicorn against the existing `app` module via `app:create_app()`.

## Tests

```bash
uv run python -m unittest discover -s tests
```
