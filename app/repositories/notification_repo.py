"""
Notification repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.notification import Notification
from .base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: Session):
        super().__init__(Notification, db)

    def get_for_user(self, user_id: Optional[int] = None) -> List[Notification]:
        if user_id is None:
            return self.db.query(Notification).filter(Notification.user_id.is_(None)).order_by(Notification.created_at.desc()).all()
        return self.db.query(Notification).filter(
            or_(Notification.user_id == user_id, Notification.user_id.is_(None))
        ).order_by(Notification.created_at.desc()).all()
