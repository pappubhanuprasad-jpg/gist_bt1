import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.APP_NAME: str = os.getenv("APP_NAME", "B.Tech Student Management System")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sms.db")
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")
        self.ACCESS_TOKEN_MINUTES: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
        self.ADMISSION_YEAR: int = int(os.getenv("ADMISSION_YEAR", "2026"))

        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "CONFIGURATION ERROR: SECRET_KEY in .env must be at least 32 characters long."
            )


settings = Settings()