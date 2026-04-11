# app/services/base_service.py
from app.repositories.base import CRUDBase

class BaseService:

    def __init__(self, model):
        self.repo = CRUDBase(model)
        self.model = model

    def create(self, db, data):
        obj = self.model(**data.dict())
        return self.repo.create(db, obj)

    def get_all(self, db):
        return self.repo.get_all(db)

    def get(self, db, id):
        return self.repo.get(db, id)

    def update(self, db, id, data):
        db_obj = self.repo.get(db, id)
        return self.repo.update(db, db_obj, data.dict())

    def delete(self, db, id):
        return self.repo.delete(db, id)