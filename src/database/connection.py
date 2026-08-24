from sqlalchemy import Engine, create_engine

from config.settings import settings


def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)
