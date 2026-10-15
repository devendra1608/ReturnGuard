import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://returnguard:local_dev_password"
    "@localhost:5432/returnguard",
)

engine = create_async_engine(
  DATABASE_URL,
  pool_pre_ping=True,
)

SessionFactory = async_sessionmaker(
  bind=engine,
  class_=AsyncSession,
  expire_on_commit=False,
)

async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session