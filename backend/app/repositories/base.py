# app/repositories/base.py
from sqlalchemy.orm import Session

class CRUDBase:

    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id):
        return db.query(self.model).get(id)

    def get_all(self, db: Session):
        return db.query(self.model).all()

    def create(self, db: Session, obj):
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, db_obj, data: dict):
        for key, value in data.items():
            setattr(db_obj, key, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id):
        obj = self.get(db, id)
        db.delete(obj)
        db.commit()