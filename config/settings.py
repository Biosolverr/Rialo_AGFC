import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    PORT: int = int(os.getenv("PORT", 8080))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    RIALO_RPC_URL: str = os.getenv("RIALO_RPC_URL", "")
    AGENT_API_URL: str = os.getenv("AGENT_API_URL", "https://autonomous-financial-governance-system-agfs-production.up.railway.app")

settings = Settings()
