from abc import ABC, abstractmethod
from sqlmodel import SQLModel, Session, create_engine
from typing import List, Type
from ...utils.logging_config import setup_logger

logger = setup_logger(__name__)

class BaseSQLStore(ABC):
    def __init__(self, db_url="sqlite:///sqlite.db"):
        self.engine = create_engine(db_url)
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
            results = session.query(self.get_model()).all()
            return results

    def fetch(self, **kwargs) -> List[SQLModel]:
        with Session(self.engine) as session:
            results = session.query(self.get_model()).filter_by(**kwargs).all()
            return results
