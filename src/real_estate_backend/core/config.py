from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    app_name:str="Real Estate Backend"
    debug_mode:bool=False
    database_url:str
    secret_key:str
    access_token_expire_hours: int = 24
    webhook_secret: str
    
    model_config=SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"   
    )
    
settings=Settings()
def get_settings()->Settings:
    return settings