from abc import ABC, abstractmethod
from sqlmodel import SQLModel, Session, create_engine
from typing import List, Type
from sqlmodel import select

from ...utils.logging_config import setup_logger

logger = setup_logger(__name__)

class BaseSQLStore():
    def __init__(self, connection_url="sqlite:///sqlite.db"):
        self.engine = create_engine(connection_url)
        SQLModel.metadata.create_all(self.engine)

    @abstractmethod
    def get_model(self) -> Type[SQLModel]:
        ...

    def add(self, data: SQLModel) -> None:
        with Session(self.engine) as session:
            session.add(data)
            session.commit()
            logger.info(f"Added entry to {self.get_model().__name__}")

    def fetch_all(self) -> List[SQLModel]:
        with Session(self.engine) as session:
            statement = select(self.get_model())
            results = session.exec(statement).all()
            return results


    def fetch(self, **kwargs) -> List[SQLModel]:
        model = self.get_model()
        with Session(self.engine) as session:
            statement = select(model).filter_by(**kwargs)
            results = session.exec(statement).all()
            return results

