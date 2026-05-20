from http import HTTPStatus
from typing import Any, Final

from flask import Flask, render_template, request

from app.db import DATABASE_PATH, RankingRepository
from app.game import GameSnapshot, GameState


JSON_ERROR_KEY: Final = "error"

type ErrorPayload = dict[str, str]
type JsonPayload = GameSnapshot | dict[str, Any] | ErrorPayload


class TicTacToeApplication:
    def __init__(self) -> None:
        self.repository = RankingRepository(DATABASE_PATH)
        self.repository.init_db()
        self.game = GameState(ranking_repository=self.repository)
        self.flask_app = Flask(__name__)
        self._register_routes()

    def _register_routes(self) -> None:
        self.flask_app.add_url_rule("/", view_func=self.index, methods=["GET"])
        self.flask_app.add_url_rule("/api/game", view_func=self.get_game, methods=["GET"])
        self.flask_app.add_url_rule("/api/game", view_func=self.create_game, methods=["POST"])
        self.flask_app.add_url_rule(
            "/api/game/reset",
            view_func=self.reset_game,
            methods=["POST"],
        )
        self.flask_app.add_url_rule("/api/move", view_func=self.make_move, methods=["POST"])
        self.flask_app.add_url_rule("/api/rankings", view_func=self.rankings, methods=["GET"])

    def _json_error(self, message: str, status: HTTPStatus) -> tuple[ErrorPayload, int]:
        return {JSON_ERROR_KEY: message}, int(status)

    def index(self) -> str:
        return render_template("index.html")

    def get_game(self) -> GameSnapshot:
        return self.game.to_dict()

    def create_game(self) -> tuple[JsonPayload, int]:
        payload = request.get_json(silent=True) or {}
        raw_players = payload.get("players")
        if not isinstance(raw_players, list):
            return self._json_error("Players must be sent as a list.", HTTPStatus.BAD_REQUEST)

        try:
            self.game.start(raw_players)
        except ValueError as error:
            return self._json_error(str(error), HTTPStatus.BAD_REQUEST)

        return self.game.to_dict(), int(HTTPStatus.CREATED)

    def reset_game(self) -> JsonPayload | tuple[ErrorPayload, int]:
        if not self.game.players:
            return self._json_error("No game has been started yet.", HTTPStatus.BAD_REQUEST)

        self.game.start(self.game.players)
        return self.game.to_dict()

    def make_move(self) -> JsonPayload | tuple[ErrorPayload, int]:
        payload = request.get_json(silent=True) or {}
        row = payload.get("row")
        col = payload.get("col")

        if not isinstance(row, int) or not isinstance(col, int):
            return self._json_error("Both row and col must be integers.", HTTPStatus.BAD_REQUEST)

        try:
            self.game.make_move(row, col)
        except ValueError as error:
            return self._json_error(str(error), HTTPStatus.BAD_REQUEST)

        self.game.record_result_if_needed()
        return self.game.to_dict()

    def rankings(self) -> dict[str, Any]:
        return {"rankings": self.repository.fetch_rankings()}


def create_app() -> Flask:
    return TicTacToeApplication().flask_app
