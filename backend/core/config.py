from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str
    SUPER_ADMIN_ID: int
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_HTTPS_PORT: int = 8443
    API_SECRET_KEY: str
    DATABASE_PATH: str = "data/complaints.sqlite3"
    USERS_DB_PATH: str = "data/users.sqlite3"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # SSL для HTTPS
    SSL_CERT_PATH: str = ""
    SSL_KEY_PATH: str = ""
    DOMAIN: str = ""
    
    class Config:
        env_file = ".env"
    
    @property
    def admin_ids_list(self) -> List[int]:
        return [int(id.strip()) for id in self.ADMIN_IDS.split(',')]
    
    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.DATABASE_PATH}"

settings = Settings()
