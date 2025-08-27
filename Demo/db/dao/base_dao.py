from abc import ABC
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

class BaseDao(ABC):
    def __init__(self, app: Flask, db: SQLAlchemy):
        self._app = app
        self._db = db