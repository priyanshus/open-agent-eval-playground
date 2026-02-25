from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool


class CheckpointerManager:
    def __init__(self, conn_info: str | None, max_size: int = 10):
        if not conn_info:
            raise ValueError("POSTGRES_URI (conninfo) is required for Postgres checkpointer")
        self.conn_info = conn_info
        self.max_size = max_size
        self._pool: ConnectionPool | None = None
        self._checkpointer: PostgresSaver | None = None

    def setup(self) -> PostgresSaver:
        self._pool = ConnectionPool(
            conninfo=self.conn_info,
            max_size=self.max_size,
            open=True,
            timeout=5,
            kwargs={"autocommit": True},
        )
        self._checkpointer = PostgresSaver(conn=self._pool)
        self._checkpointer.setup()
        return self._checkpointer

    def get_checkpointer(self) -> PostgresSaver:
        if self._checkpointer is None:
            raise RuntimeError("Checkpointer not initialized. Call setup() first.")
        return self._checkpointer

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None
        self._checkpointer = None
