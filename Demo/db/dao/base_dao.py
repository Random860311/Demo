from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional

from flask_sqlalchemy import SQLAlchemy
from flask import Flask

TModel = TypeVar("TModel")

class BaseDao(Generic[TModel], ABC):
    @abstractmethod
    def get_by_id(self, obj_id: int) -> Optional[TModel]:
        pass

    @abstractmethod
    def get_all(self) -> list[TModel]:
        pass


class DatabaseDao(BaseDao[TModel], ABC):
    def __init__(self, app: Flask, db: SQLAlchemy):
        self._app = app
        self._db = db