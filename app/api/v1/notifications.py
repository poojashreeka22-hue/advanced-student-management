"""
Notification API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.notification_repo import NotificationRepository
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.api.dependencies import get_current_user_optional
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(data: NotificationCreate, db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    notif = Notification(
        user_id=data.user_id,
        title=data.title.strip(),
        message=data.message.strip(),
        category=data.category
    )
    return repo.create(notif)


@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    repo = NotificationRepository(db)
    uid = current_user.id if current_user else None
    return repo.get_for_user(uid)
