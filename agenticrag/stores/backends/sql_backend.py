from abc import ABC
import os
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, select, and_
from sqlalchemy.ext.declarative import DeclarativeMeta

from agenticrag.types.exceptions import StoreError
from agenticrag.stores.backends.base import BaseBackend
from agenticrag.types.core import BaseData
from agenticrag.utils.logging_config import setup_logger

logger = setup_logger(__name__)

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
SchemaType = TypeVar("SchemaType", bound=BaseData)
Base = declarative_base()


class SQLBackend(BaseBackend[SchemaType], ABC, Generic[ModelType, SchemaType]):
    def __init__(
        self,
        model: Type[ModelType],
        schema: Type[SchemaType],
        connection_url: str = "sqlite:///.agenticrag_data/agenticrag.db",
    ):
        self.model = model
        self.schema = schema
        try:
            if connection_url == "sqlite:///.agenticrag_data/agenticrag.db":
                os.mkdir(".agenticrag_data") if not os.path.exists(".agenticrag_data") else None
            self.engine = create_engine(connection_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.model.__table__.create(bind=self.engine, checkfirst=True)
            logger.info(f"Database initialized and table created for: {model.__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise StoreError("DB engine initialization failed.") from e

    def add(self, data: SchemaType) -> SchemaType:
        model_instance = self.model(**data.model_dump())
        try:
            with self.SessionLocal() as session:
                session.add(model_instance)
                session.commit()
                logger.info(f"Added data with id={getattr(model_instance, 'id', None)}")
                return self.schema.model_validate(model_instance, from_attributes=True)
        except Exception as e:
            logger.error(f"Failed to add data: {e}")
            raise StoreError("Failed to add data.") from e

    def get(self, id: str) -> Optional[SchemaType]:
        try:
            with self.SessionLocal() as session:
                obj = session.get(self.model, id)
                if obj:
                    logger.debug(f"Retrieved data with id={id}")
                    return self.schema.model_validate(obj, from_attributes=True)
                logger.info(f"No data found with id={id}")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve data with id={id}: {e}")
            raise StoreError("Failed to retrieve data.") from e

    def get_all(self) -> List[SchemaType]:
        try:
            with self.SessionLocal() as session:
                objs = session.scalars(select(self.model)).all()
                logger.info(f"Retrieved all data entries, count={len(objs)}")
                return [self.schema.model_validate(obj, from_attributes=True) for obj in objs]
        except Exception as e:
            logger.error(f"Failed to retrieve all data: {e}")
            raise StoreError("Failed to retrieve all data.") from e


    def delete(self, id: str) -> None:
        try:
            with self.SessionLocal() as session:
                obj = session.get(self.model, id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logger.info(f"Deleted data with id={id}")
                else:
                    logger.info(f"No data found to delete with id={id}")
        except Exception as e:
            logger.error(f"Failed to delete data with id={id}: {e}")
            raise StoreError("Failed to delete data.") from e
        

    def update(self, id: str, **kwargs) -> None:
        try:
            with self.SessionLocal() as session:
                obj = session.get(self.model, id)
                if obj:
                    for field, value in kwargs.items():
                        if hasattr(obj, field):
                            setattr(obj, field, value)
                    session.commit()
                    logger.info(f"Updated data with id={id}")
                else:
                    logger.info(f"No data found to update with id={id}")
        except Exception as e:
            logger.error(f"Failed to update data with id={id}: {e}")
            raise StoreError("Failed to update data.") from e


    def index(self, **filters) -> List[SchemaType]:
        valid_filters = {
            k: v for k, v in filters.items()
            if v is not None and hasattr(self.model, k)
        }

        if not valid_filters:
            logger.info("No filter criteria provided, returning all entries.")
            return self.get_all()

        try:
            with self.SessionLocal() as session:
                conditions = [getattr(self.model, k) == v for k, v in valid_filters.items()]
                stmt = select(self.model).where(and_(*conditions))
                objs = session.scalars(stmt).all()
                logger.info(f"Index query with filters {valid_filters}, found {len(objs)} entries")
                return [self.schema.model_validate(obj, from_attributes=True) for obj in objs]
        except Exception as e:
            logger.error(f"Failed to index data with filters {valid_filters}: {e}")
            raise StoreError("Indexing failed.") from e
