"""
User repository.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(
            func.lower(User.username) == username.strip().lower()
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(
            func.lower(User.email) == email.strip().lower()
        ).first()
