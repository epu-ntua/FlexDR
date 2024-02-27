from typing import List

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field(..., env='APP_NAME')
    keycloak_url: str = Field(..., env='KEYCLOAK_URL')
    client_id: str = Field(..., env='CLIENT_ID')
    client_secret: str = Field(..., env='CLIENT_SECRET')
    admin_roles: List[str] = Field(..., env='ADMIN_ROLES')
    user_roles: List[str] = Field(..., env='USER_ROLES')

    # class Config:
    #     env_file = "../.env"


settings = Settings()
