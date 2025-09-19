from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from db.dao.base_dao import DatabaseDao, TModel
from db.model.config.config_model import ConfigModel


class ConfigDao(DatabaseDao[ConfigModel]):
    def __init__(self, app: Flask, db: SQLAlchemy):
        super().__init__(app, db)

    def get_by_id(self, obj_id: int) -> Optional[ConfigModel]:
        with self._app.app_context():
            return ConfigModel.query.get(obj_id)

    def get_all(self) -> list[ConfigModel]:
        with self._app.app_context():
            return ConfigModel.query.all()

    def save_or_update(self, model: TModel) -> TModel:
        with self._app.app_context():
            with self._db.session.begin_nested():
                if model.id is None or model.id == 0:
                    self._db.session.add(model)
                    return model
                merged = self._db.session.merge(model)
                return merged

    def delete(self, obj_id: int) -> ConfigModel:
        with self._app.app_context():
            with self._db.session.begin_nested():
                model = ConfigModel.query.get(obj_id)
                if model is None:
                    print(f"Unable to delete, config with id {obj_id} not found")
                    raise ValueError(f"Config not found")
                self._db.session.delete(model)
                return model