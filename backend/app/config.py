import os

class Settings:
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")

    EMBEDDINGS_PROVIDER: str = os.getenv("EMBEDDINGS_PROVIDER", "openai")
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")

    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "docs")

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "aistarter")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "aistarter")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "aistarter")

    ENV: str = os.getenv("ENV", "dev")

settings = Settings()
