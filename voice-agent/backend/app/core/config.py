from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PERPLEXITY_API_KEY: str = ""
    ELEVENLABS_API_KEY: str
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str = ""
    NEO4J_URI: str = ""
    NEO4J_USERNAME: str = ""
    NEO4J_PASSWORD: str = ""
    # LiveKit (Path B pipeline)
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""
    ELEVENLABS_VOICE_ID: str = "ljX1ZrXuDIIRVcmiVSyR"
    # Deepgram STT (agent_worker)
    DEEPGRAM_API_KEY: str = ""
    # Optional TTS providers used by hybrid pipeline
    CARTESIA_API_KEY: str = ""
    INWORLD_API_KEY: str = ""
    # Internal service auth
    INTERNAL_SECRET: str = ""
    # CORS / redirect targets
    FRONTEND_URL: str = "http://localhost:3000"
    # Upstash Redis (rate limiter)
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
