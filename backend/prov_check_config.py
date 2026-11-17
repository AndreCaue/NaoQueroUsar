from app.core.config import get_settings

settings = get_settings()

print("DATABASE_URL:", settings.DATABASE_URL.split("@")[-1])