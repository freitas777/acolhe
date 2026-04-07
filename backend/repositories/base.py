from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session, selectinload

from backend.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def create(self, data: dict[str, Any]) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self.db.get(self.model, id)

    def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        options: list | None = None,
    ) -> Sequence[ModelType]:
        stmt = select(self.model)
        if options:
            for opt in options:
                stmt = stmt.options(opt)
        stmt = stmt.offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return result.unique().scalars().all()

    def update(self, id: int, data: dict[str, Any]) -> Optional[ModelType]:
        instance = self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: int) -> bool:
        instance = self.get_by_id(id)
        if instance is None:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True
