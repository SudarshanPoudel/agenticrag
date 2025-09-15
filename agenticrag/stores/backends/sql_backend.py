import os
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import DeclarativeMeta, declarative_base, sessionmaker, Session
from agenticrag.types.exceptions import StoreError
from agenticrag.stores.backends.base import BaseBackend
from agenticrag.types.core import BaseData
from agenticrag.utils.logging_config import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
SchemaType = TypeVar("SchemaType", bound=BaseData)


class SQLBackend(BaseBackend[SchemaType], Generic[ModelType, SchemaType]):
    def __init__(self, model: Type[ModelType], schema: Type[SchemaType], connection_url: str, async_url: Optional[str] = None):
        self.model = model
        self.schema = schema
        try:
            self.engine = create_engine(connection_url, future=True)
            self.SessionLocal = sessionmaker(self.engine, autocommit=False, autoflush=False)
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Sync DB initialized for {model.__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize sync DB engine: {e}")
            raise StoreError("DB engine initialization failed.") from e

        if async_url:
            try:
                self.async_engine: AsyncEngine = create_async_engine(async_url, future=True, echo=False)
                self.AsyncSessionLocal = async_sessionmaker(self.async_engine, expire_on_commit=False)
                import asyncio
                async def _init_async():
                    async with self.async_engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)
                asyncio.run(_init_async())
                logger.info(f"Async DB initialized for {model.__name__}")
            except Exception as e:
                logger.error(f"Failed to initialize async DB engine: {e}")
                raise StoreError("Async DB engine initialization failed.") from e
        else:
            self.async_engine = None
            self.AsyncSessionLocal = None

    def add(self, data: SchemaType) -> SchemaType:
        instance = self.model(**data.model_dump())
        with self.SessionLocal() as session:
            try:
                session.add(instance)
                session.commit()
                session.refresh(instance)
                return self.schema.model_validate(instance, from_attributes=True)
            except Exception as e:
                session.rollback()
                raise StoreError("Failed to add data.") from e

    def get(self, id) -> Optional[SchemaType]:
        with self.SessionLocal() as session:
            obj = session.get(self.model, id)
            return self.schema.model_validate(obj, from_attributes=True) if obj else None

    def get_all(self) -> List[SchemaType]:
        with self.SessionLocal() as session:
            objs = session.scalars(select(self.model)).all()
            return [self.schema.model_validate(o, from_attributes=True) for o in objs]

    def delete(self, id) -> None:
        with self.SessionLocal() as session:
            obj = session.get(self.model, id)
            if obj:
                session.delete(obj)
                session.commit()

    def update(self, id, **kwargs) -> None:
        with self.SessionLocal() as session:
            obj = session.get(self.model, id)
            if obj:
                for k, v in kwargs.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
                session.commit()

    def index(self, **filters) -> List[SchemaType]:
        valid_filters = {k: v for k, v in filters.items() if v is not None and k in self.model.__table__.columns}
        if not valid_filters:
            return self.get_all()
        with self.SessionLocal() as session:
            conditions = [getattr(self.model, k) == v for k, v in valid_filters.items()]
            objs = session.scalars(select(self.model).where(and_(*conditions))).all()
            return [self.schema.model_validate(o, from_attributes=True) for o in objs]

    async def aadd(self, data: SchemaType) -> SchemaType:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async DB not configured")
        instance = self.model(**data.model_dump())
        async with self.AsyncSessionLocal() as session:
            try:
                session.add(instance)
                await session.commit()
                await session.refresh(instance)
                return self.schema.model_validate(instance, from_attributes=True)
            except Exception as e:
                await session.rollback()
                raise StoreError("Failed to add data.") from e

    async def aget(self, id) -> Optional[SchemaType]:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async DB not configured")
        async with self.AsyncSessionLocal() as session:
            obj = await session.get(self.model, id)
            return self.schema.model_validate(obj, from_attributes=True) if obj else None

    async def aget_all(self) -> List[SchemaType]:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async DB not configured")
        async with self.AsyncSessionLocal() as session:
            result = await session.scalars(select(self.model))
            return [self.schema.model_validate(o, from_attributes=True) for o in result.all()]

    async def adelete(self, id) -> None:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async DB not configured")
        async with self.AsyncSessionLocal() as session:
            obj = await session.get(self.model, id)
            if obj:
                await session.delete(obj)
                await session.commit()

    async def aupdate(self, id, **kwargs) -> None:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async DB not configured")
        async with self.AsyncSessionLocal() as session:
            obj = await session.get(self.model, id)
            if obj:
                for k, v in kwargs.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
                await session.commit()

    async def aindex(self, **filters) -> List[SchemaType]:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async DB not configured")
        valid_filters = {k: v for k, v in filters.items() if v is not None and k in self.model.__table__.columns}
        if not valid_filters:
            return await self.aget_all()
        async with self.AsyncSessionLocal() as session:
            conditions = [getattr(self.model, k) == v for k, v in valid_filters.items()]
            result = await session.scalars(select(self.model).where(and_(*conditions)))
            return [self.schema.model_validate(o, from_attributes=True) for o in result.all()]
