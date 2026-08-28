from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models.event import Event
from models.recently_viewed import RecentlyViewed
from services.activity_service import RECENTLY_VIEWED_LIMIT, get_user_favorite_ids

recently_viewed_bp = Blueprint("recently_viewed", __name__)


@recently_viewed_bp.route("/recently-viewed")
@login_required
def recently_viewed_page():
    # Historical RecentlyViewed rows are preserved even after their event
    # is soft-deleted, but inactive events are filtered out of this
    # user-facing list (their rows remain in the database untouched).
    entries = (
        RecentlyViewed.query
        .filter_by(user_id=current_user.user_id)
        .join(Event, RecentlyViewed.event_id == Event.id)
        .filter(Event.is_active == True)
        .order_by(RecentlyViewed.viewed_at.desc())
        .limit(RECENTLY_VIEWED_LIMIT)
        .all()
    )

    favorited_event_ids = get_user_favorite_ids(
        current_user.user_id, [entry.event_id for entry in entries]
    )

    return render_template(
        "recently_viewed.html",
        entries=entries,
        favorited_event_ids=favorited_event_ids
    )
