from datetime import date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from sqlalchemy import or_, func, desc
from flask_login import current_user
from models.search import Search

from extensions import db
from models.event import Event
from models.rating import Rating
from models.review import Review
from services.activity_service import (
    record_recently_viewed,
    get_user_favorite_ids,
    get_user_calendar_ids,
)


events_bp = Blueprint("events", __name__)


def build_event_ratings_map(event_ids):
    """
    Read-only helper for the UI: returns {event_id: {"avg": x.x, "count": n}}
    for the given event ids that have at least one rating. Does not change
    any existing query, filter, or ranking logic elsewhere in this file.
    """
    if not event_ids:
        return {}

    rows = (
        db.session.query(
            Rating.event_id,
            func.avg(Rating.value).label("avg_rating"),
            func.count(Rating.id).label("ratings_count")
        )
        .filter(Rating.event_id.in_(event_ids))
        .group_by(Rating.event_id)
        .all()
    )

    return {
        event_id: {"avg": round(float(avg_rating), 1), "count": ratings_count}
        for event_id, avg_rating, ratings_count in rows
    }


@events_bp.route("/")
def home():
    events = Event.query.filter(Event.is_active == True).limit(6).all()

    top_rated_query = (
        db.session.query(
            Event,
            func.avg(Rating.value).label("avg_rating"),
            func.count(Rating.id).label("ratings_count")
        )
        .join(Rating, Rating.event_id == Event.id)
        .filter(Event.is_active == True)
        .group_by(Event.id)
        .order_by(desc("avg_rating"), desc("ratings_count"))
        .limit(3)
        .all()
    )

    top_rated_events = [
        {
            "event": event,
            "avg_rating": round(float(avg_rating), 1),
            "ratings_count": ratings_count
        }
        for event, avg_rating, ratings_count in top_rated_query
    ]

    # Events whose end_date is today ("Ending Today" — Sprint 3).
    ending_today_events = Event.query.filter(
        Event.is_active == True, Event.end_date == date.today()
    ).all()

    # Read-only rating summary for the featured-events cards (UI display only;
    # does not change which events are returned or how they are ordered).
    all_shown_ids = (
        [e.id for e in events]
        + [item["event"].id for item in top_rated_events]
        + [e.id for e in ending_today_events]
    )
    event_ratings = build_event_ratings_map(all_shown_ids)

    favorited_event_ids = (
        get_user_favorite_ids(current_user.user_id, all_shown_ids)
        if current_user.is_authenticated else set()
    )

    return render_template(
        "index.html",
        events=events,
        top_rated_events=top_rated_events,
        ending_today_events=ending_today_events,
        event_ratings=event_ratings,
        favorited_event_ids=favorited_event_ids
    )


@events_bp.route("/events")
def events_page():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    date_filter = request.args.get("date_filter", "").strip()

    query = Event.query.filter(Event.is_active == True)

    if search:
        words = [w for w in search.lower().split() if len(w) > 2]

        conditions = []
        for w in words:
             conditions.append(Event.title.ilike(f"%{w}%"))
             conditions.append(Event.description.ilike(f"%{w}%"))
             conditions.append(Event.category.ilike(f"%{w}%"))

        query = query.filter(or_(*conditions))

        if current_user.is_authenticated:
            new_search = Search(
                user_id=current_user.user_id,
                keyword=search
            )
            db.session.add(new_search)
            db.session.commit()

    if category:
        query = query.filter(Event.category == category)

    today = date.today()

    if date_filter == "today":
        query = query.filter(
            Event.start_date <= today,
            or_(Event.end_date == None, Event.end_date >= today)
        )

    elif date_filter == "tomorrow":
        tomorrow = today + timedelta(days=1)
        query = query.filter(
            Event.start_date <= tomorrow,
            or_(Event.end_date == None, Event.end_date >= tomorrow)
        )

    elif date_filter == "this_week":
        week_end = today + timedelta(days=7)
        query = query.filter(
            Event.start_date <= week_end,
            or_(Event.end_date == None, Event.end_date >= today)
        )

    events = query.all()

    categories = (
        db.session.query(Event.category)
        .filter(Event.is_active == True)
        .distinct()
        .all()
    )
    categories = [c[0] for c in categories if c[0]]

    event_ratings = build_event_ratings_map([e.id for e in events])

    favorited_event_ids = (
        get_user_favorite_ids(current_user.user_id, [e.id for e in events])
        if current_user.is_authenticated else set()
    )

    return render_template(
        "events.html",
        events=events,
        categories=categories,
        selected_search=search,
        selected_category=category,
        selected_date_filter=date_filter,
        event_ratings=event_ratings,
        favorited_event_ids=favorited_event_ids
    )


@events_bp.route("/events/<int:event_id>")
def event_details(event_id):
    event = Event.query.get_or_404(event_id)

    # Soft-deleted events are no longer browsable as active events.
    # Historical interaction rows (Ratings, Reviews, Favorites,
    # CalendarEvent, RecentlyViewed) that reference this event are left
    # untouched in the database — only this page becomes inaccessible.
    if not event.is_active:
        abort(404)

    if current_user.is_authenticated:
        record_recently_viewed(current_user.user_id, event_id)

    ratings = Rating.query.filter_by(event_id=event_id).all()
    ratings_count = len(ratings)
    average_rating = round(sum(r.value for r in ratings) / ratings_count, 1) if ratings_count > 0 else None

    current_user_rating = None
    is_favorited = False
    is_in_calendar = False
    if current_user.is_authenticated:
        existing = Rating.query.filter_by(user_id=current_user.user_id, event_id=event_id).first()
        if existing:
            current_user_rating = existing.value

        favorite_ids = get_user_favorite_ids(current_user.user_id, [event_id])
        is_favorited = event_id in favorite_ids

        calendar_ids = get_user_calendar_ids(current_user.user_id, [event_id])
        is_in_calendar = event_id in calendar_ids

    reviews = Review.query.filter_by(event_id=event_id).order_by(Review.created_at.desc()).all()

    return render_template(
        "event_details.html",
        event=event,
        ratings=ratings,
        average_rating=average_rating,
        ratings_count=ratings_count,
        current_user_rating=current_user_rating,
        reviews=reviews,
        is_favorited=is_favorited,
        is_in_calendar=is_in_calendar,
    )


@events_bp.route("/events/<int:event_id>/rate", methods=["POST"])
def rate_event(event_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to rate an event.", "warning")
        return redirect(url_for("events.event_details", event_id=event_id))

    event = Event.query.get_or_404(event_id)

    if not event.is_active:
        flash("This event is no longer available and can't be rated.", "warning")
        return redirect(url_for("events.events_page"))

    try:
        value = int(request.form.get("rating", 0))
    except ValueError:
        value = 0

    if value < 1 or value > 5:
        flash("Rating must be between 1 and 5.", "danger")
        return redirect(url_for("events.event_details", event_id=event_id))

    existing = Rating.query.filter_by(user_id=current_user.user_id, event_id=event_id).first()
    if existing:
        existing.value = value
        flash("Your rating has been updated.", "success")
    else:
        db.session.add(Rating(user_id=current_user.user_id, event_id=event_id, value=value))
        flash("Thank you for rating this event!", "success")

    db.session.commit()
    return redirect(url_for("events.event_details", event_id=event_id))


@events_bp.route("/events/<int:event_id>/reviews", methods=["POST"])
def submit_review(event_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to write a review.", "warning")
        return redirect(url_for("events.event_details", event_id=event_id))

    event = Event.query.get_or_404(event_id)

    if not event.is_active:
        flash("This event is no longer available and can't be reviewed.", "warning")
        return redirect(url_for("events.events_page"))

    content = request.form.get("content", "").strip()

    if not content:
        flash("Review cannot be empty.", "danger")
        return redirect(url_for("events.event_details", event_id=event_id))

    existing = Review.query.filter_by(user_id=current_user.user_id, event_id=event_id).first()
    if existing:
        existing.content = content
        flash("Your review has been updated.", "success")
    else:
        db.session.add(Review(user_id=current_user.user_id, event_id=event_id, content=content))
        flash("Your review has been submitted!", "success")

    db.session.commit()
    return redirect(url_for("events.event_details", event_id=event_id))
