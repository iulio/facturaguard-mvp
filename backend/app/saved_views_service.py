from datetime import datetime
import json
from sqlalchemy.orm import Session

from .models import SavedView, User

def list_saved_views(db: Session, user: User, view_type: str = "portfolio") -> list[SavedView]:
    return (
        db.query(SavedView)
        .filter(SavedView.user_id == user.id, SavedView.view_type == view_type)
        .order_by(SavedView.is_default.desc(), SavedView.created_at.asc())
        .all()
    )

def create_saved_view(
    db: Session,
    user: User,
    name: str,
    view_type: str,
    filters: dict,
    is_default: bool = False,
) -> SavedView:
    if is_default:
        clear_default_views(db, user, view_type)

    saved_view = SavedView(
        user_id=user.id,
        name=name,
        view_type=view_type,
        filters_json=json.dumps(filters or {}),
        is_default=is_default,
    )
    db.add(saved_view)
    db.flush()
    return saved_view

def update_saved_view(
    db: Session,
    user: User,
    saved_view_id: int,
    name: str | None = None,
    filters: dict | None = None,
    is_default: bool | None = None,
) -> SavedView:
    saved_view = (
        db.query(SavedView)
        .filter(SavedView.id == saved_view_id, SavedView.user_id == user.id)
        .first()
    )
    if not saved_view:
        raise ValueError("Saved view nu există.")

    if name is not None:
        saved_view.name = name

    if filters is not None:
        saved_view.filters_json = json.dumps(filters)

    if is_default is not None:
        if is_default:
            clear_default_views(db, user, saved_view.view_type)
        saved_view.is_default = is_default

    saved_view.updated_at = datetime.utcnow()
    db.flush()
    return saved_view

def delete_saved_view(db: Session, user: User, saved_view_id: int) -> None:
    saved_view = (
        db.query(SavedView)
        .filter(SavedView.id == saved_view_id, SavedView.user_id == user.id)
        .first()
    )
    if not saved_view:
        raise ValueError("Saved view nu există.")

    db.delete(saved_view)
    db.flush()

def clear_default_views(db: Session, user: User, view_type: str) -> None:
    views = (
        db.query(SavedView)
        .filter(SavedView.user_id == user.id, SavedView.view_type == view_type)
        .all()
    )
    for view in views:
        view.is_default = False
