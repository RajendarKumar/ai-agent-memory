import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


class SessionMemory:
	"""Persist LangGraph checkpoints in SQLite, scoped by the graph thread ID."""

	def __init__(self, database_path: Path) -> None:
		database_path.parent.mkdir(parents=True, exist_ok=True)
		self.connection = sqlite3.connect(str(database_path), check_same_thread=False)
		self.checkpointer = SqliteSaver(self.connection)
		self.checkpointer.setup()

	def close(self) -> None:
		self.connection.close()

	def __enter__(self) -> "SessionMemory":
		return self

	def __exit__(self, *_: object) -> None:
		self.close()
