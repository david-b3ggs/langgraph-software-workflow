from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-6"

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "AI-WORKFLOW"

    # CodeRabbit (optional — LLM fallback used if absent)
    coderabbit_api_key: str = ""

    # Paths
    checkpoints_db: str = "checkpoints.db"
    repo_path: str = "."


settings = Settings()
