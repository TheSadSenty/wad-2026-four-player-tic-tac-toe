from dataclasses import dataclass, field
from typing import Final, Literal, Sequence, TypedDict

from app.db import RankingRepository

type PlayerSymbol = Literal["X", "O", "▽", "●"]
type Cell = PlayerSymbol | None
type Board = list[list[Cell]]
type Direction = tuple[int, int]
type GameStatus = Literal["waiting", "in_progress", "finished"]


class PlayerSnapshot(TypedDict):
    name: str
    symbol: PlayerSymbol


class GameSnapshot(TypedDict):
    players: list[PlayerSnapshot]
    board: Board
    boardSize: int
    winLength: int
    currentTurn: int
    status: GameStatus
    message: str
    winnerIndex: int | None
    hasGame: bool


PLAYER_SYMBOLS: Final[tuple[PlayerSymbol, ...]] = ("X", "O", "▽", "●")
DIRECTIONS: Final[tuple[Direction, ...]] = ((1, 0), (0, 1), (1, 1), (1, -1))
BOARD_SIZE: Final = 6
WIN_LENGTH: Final = 4


@dataclass(slots=True)
class GameState:
    ranking_repository: RankingRepository | None = None
    players: list[str] = field(default_factory=list)
    board_size: int = BOARD_SIZE
    win_length: int = WIN_LENGTH
    board: Board = field(default_factory=list)
    current_turn: int = 0
    status: GameStatus = "waiting"
    message: str = "Start a new game to begin."
    winner_index: int | None = None
    move_count: int = 0
    result_recorded: bool = False

    def start(self, players: Sequence[str]) -> None:
        cleaned_players = [name.strip() for name in players]
        if len(cleaned_players) != 4 or any(not name for name in cleaned_players):
            raise ValueError("Exactly four player names are required.")

        self.players = cleaned_players
        self.board = self._empty_board()
        self.current_turn = 0
        self.status = "in_progress"
        self.message = f"{self.players[0]} ({PLAYER_SYMBOLS[0]}) starts."
        self.winner_index = None
        self.move_count = 0
        self.result_recorded = False

    def make_move(self, row: int, col: int) -> None:
        if self.status != "in_progress":
            raise ValueError("The game is not active.")
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            raise ValueError("Move is out of bounds.")
        if self.board[row][col] is not None:
            raise ValueError("That cell is already taken.")

        symbol = PLAYER_SYMBOLS[self.current_turn]
        self.board[row][col] = symbol
        self.move_count += 1

        if self._is_winning_move(row, col, symbol):
            self.status = "finished"
            self.winner_index = self.current_turn
            self.message = f"{self.players[self.current_turn]} ({symbol}) wins."
            return

        if self.move_count == self.board_size * self.board_size:
            self.status = "finished"
            self.message = "Draw game."
            return

        self.current_turn = (self.current_turn + 1) % len(self.players)
        next_symbol = PLAYER_SYMBOLS[self.current_turn]
        self.message = f"{self.players[self.current_turn]} ({next_symbol}) to move."

    def record_result_if_needed(self) -> None:
        if not self.players or self.status != "finished" or self.result_recorded:
            return

        if self.ranking_repository is not None:
            self.ranking_repository.record_game(self.players, self.winner_name)
        self.result_recorded = True

    @property
    def winner_name(self) -> str | None:
        if self.winner_index is None:
            return None
        return self.players[self.winner_index]

    def to_dict(self) -> GameSnapshot:
        return {
            "players": [
                {"name": name, "symbol": PLAYER_SYMBOLS[index]}
                for index, name in enumerate(self.players)
            ],
            "board": self.board,
            "boardSize": self.board_size,
            "winLength": self.win_length,
            "currentTurn": self.current_turn,
            "status": self.status,
            "message": self.message,
            "winnerIndex": self.winner_index,
            "hasGame": bool(self.players),
        }

    def _empty_board(self) -> Board:
        return [[None for _ in range(self.board_size)] for _ in range(self.board_size)]

    def _is_winning_move(self, row: int, col: int, symbol: PlayerSymbol) -> bool:
        for delta_row, delta_col in DIRECTIONS:
            streak = 1
            streak += self._count_direction(row, col, delta_row, delta_col, symbol)
            streak += self._count_direction(row, col, -delta_row, -delta_col, symbol)
            if streak >= self.win_length:
                return True
        return False

    def _count_direction(
        self,
        row: int,
        col: int,
        delta_row: int,
        delta_col: int,
        symbol: PlayerSymbol,
    ) -> int:
        count = 0
        next_row = row + delta_row
        next_col = col + delta_col

        while 0 <= next_row < self.board_size and 0 <= next_col < self.board_size:
            if self.board[next_row][next_col] != symbol:
                break
            count += 1
            next_row += delta_row
            next_col += delta_col

        return count
