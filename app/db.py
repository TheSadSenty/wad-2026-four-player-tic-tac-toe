import sqlite3
from pathlib import Path
from typing import TypedDict


class RankingRow(TypedDict):
    player_name: str
    games_played: int
    wins: int
    draws: int
    losses: int
    points: int


class RankingRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.instance_dir = database_path.parent

    def connect(self) -> sqlite3.Connection:
        self.instance_dir.mkdir(exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_db(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rankings (
                    player_name TEXT PRIMARY KEY,
                    games_played INTEGER NOT NULL DEFAULT 0,
                    wins INTEGER NOT NULL DEFAULT 0,
                    draws INTEGER NOT NULL DEFAULT 0,
                    losses INTEGER NOT NULL DEFAULT 0,
                    points INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def record_game(self, players: list[str], winner_name: str | None) -> None:
        with self.connect() as connection:
            for player in players:
                connection.execute(
                    """
                    INSERT INTO rankings (player_name, games_played, wins, draws, losses, points)
                    VALUES (?, 0, 0, 0, 0, 0)
                    ON CONFLICT(player_name) DO NOTHING
                    """,
                    (player,),
                )

            if winner_name is None:
                self._record_draw(connection, players)
                return

            self._record_win(connection, players, winner_name)

    def fetch_rankings(self) -> list[RankingRow]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT player_name, games_played, wins, draws, losses, points
                FROM rankings
                ORDER BY points DESC, wins DESC, draws DESC, player_name ASC
                """
            ).fetchall()
        return [RankingRow(**dict(row)) for row in rows]

    def _record_draw(self, connection: sqlite3.Connection, players: list[str]) -> None:
        for player in players:
            connection.execute(
                """
                UPDATE rankings
                SET games_played = games_played + 1,
                    draws = draws + 1,
                    points = points + 1
                WHERE player_name = ?
                """,
                (player,),
            )

    def _record_win(
        self,
        connection: sqlite3.Connection,
        players: list[str],
        winner_name: str,
    ) -> None:
        for player in players:
            is_winner = player == winner_name
            connection.execute(
                """
                UPDATE rankings
                SET games_played = games_played + 1,
                    wins = wins + ?,
                    losses = losses + ?,
                    points = points + ?
                WHERE player_name = ?
                """,
                (1 if is_winner else 0, 0 if is_winner else 1, 3 if is_winner else 0, player),
            )


PROJECT_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = PROJECT_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "rankings.db"
