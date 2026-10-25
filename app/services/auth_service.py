"""
Authentication and User Account Service.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import UnauthorizedException, DuplicateEntityException, EntityNotFoundException


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        user = self.repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid username or password")
        if not user.is_active:
            raise UnauthorizedException("Account is disabled")

        token = create_access_token({
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
            "full_name": user.full_name
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }

    def register_user(self, user_in: UserCreate) -> User:
        if self.repo.get_by_username(user_in.username):
            raise DuplicateEntityException("User", "username", user_in.username)
        if self.repo.get_by_email(user_in.email):
            raise DuplicateEntityException("User", "email", user_in.email)

        user = User(
            username=user_in.username.strip(),
            email=user_in.email.strip().lower(),
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name.strip(),
            role=user_in.role.lower(),
            is_active=user_in.is_active
        )
        return self.repo.create(user)

    def get_user_by_id(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        return user
