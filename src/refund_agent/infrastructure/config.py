from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    orders_file: Path
    session_db: Path
    long_term_memory_enabled: bool
    milvus_uri: str
    milvus_token: str | None
    milvus_collection: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is required. Set it in .env or the environment.")

        return cls(
            groq_api_key=api_key,
            groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            orders_file=_project_path(os.getenv("ORDERS_FILE", "data/orders.csv")),
            session_db=_project_path(os.getenv("SESSION_DB", "data/refund_sessions.sqlite3")),
            long_term_memory_enabled=_as_bool(os.getenv("LONG_TERM_MEMORY_ENABLED", "false")),
            milvus_uri=os.getenv("MILVUS_URI", "http://localhost:19530"),
            milvus_token=os.getenv("MILVUS_TOKEN") or None,
            milvus_collection=os.getenv("MILVUS_COLLECTION", "refund_memories"),
        )


def _project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}