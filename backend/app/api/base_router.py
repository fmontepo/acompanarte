from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db


def create_router(model, schema_create, schema_read, service, prefix):
    router = APIRouter(prefix=prefix, tags=[prefix])

    @router.post("/", response_model=schema_read)
    def create(data: schema_create, db: Session = Depends(get_db)):
        return service.create(db, data)

    @router.get("/", response_model=list[schema_read])
    def get_all(db: Session = Depends(get_db)):
        return service.get_all(db)

    @router.get("/{id}", response_model=schema_read)
    def get_one(id: str, db: Session = Depends(get_db)):
        obj = service.get(db, id)
        if not obj:
            raise HTTPException(404)
        return obj

    return router