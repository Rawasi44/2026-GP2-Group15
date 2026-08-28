from datetime import datetime

from extensions import db
from models.favorite import Favorite
from models.calendar_event import CalendarEvent
from models.recently_viewed import RecentlyViewed

RECENTLY_VIEWED_LIMIT = 10


def record_recently_viewed(user_id, event_id):
    """
    Upserts a RecentlyViewed row for (user_id, event_id): refreshes
    viewed_at if a row already exists, otherwise inserts a new one.

    Does NOT trim or delete older history — every view is preserved in
    the database so Sprint 4's recommendation system can later use the
    full interaction history. The user-facing page limits its display to
    the most recent RECENTLY_VIEWED_LIMIT events via its own query
    (see routes/recently_viewed.py); that display limit is not a
    database retention limit.
    """
    existing = RecentlyViewed.query.filter_by(user_id=user_id, event_id=event_id).first()

    if existing:
        existing.viewed_at = datetime.utcnow()
    else:
        db.session.add(RecentlyViewed(user_id=user_id, event_id=event_id))

    db.session.commit()


def get_user_favorite_ids(user_id, event_ids):
    """Read-only helper: returns the subset of event_ids the user has favorited."""
    if not user_id or not event_ids:
        return set()

    rows = (
        Favorite.query
        .filter(Favorite.user_id == user_id, Favorite.event_id.in_(event_ids))
        .all()
    )
    return {row.event_id for row in rows}


def get_user_calendar_ids(user_id, event_ids):
    """Read-only helper: returns the subset of event_ids the user has added to their calendar."""
    if not user_id or not event_ids:
        return set()

    rows = (
        CalendarEvent.query
        .filter(CalendarEvent.user_id == user_id, CalendarEvent.event_id.in_(event_ids))
        .all()
    )
    return {row.event_id for row in rows}
