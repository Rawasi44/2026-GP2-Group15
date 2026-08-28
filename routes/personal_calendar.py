from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models.event import Event
from models.calendar_event import CalendarEvent

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/calendar")
@login_required
def calendar_page():
    # Historical CalendarEvent rows are preserved even after their event
    # is soft-deleted, but inactive events are filtered out of this
    # user-facing list (their rows remain in the database untouched).
    entries = (
        CalendarEvent.query
        .filter_by(user_id=current_user.user_id)
        .join(Event, CalendarEvent.event_id == Event.id)
        .filter(Event.is_active == True)
        .order_by(Event.start_date.asc())
        .all()
    )
    return render_template("calendar.html", entries=entries)


@calendar_bp.route("/calendar/<int:event_id>/toggle", methods=["POST"])
@login_required
def toggle_calendar(event_id):
    event = Event.query.get_or_404(event_id)

    existing = CalendarEvent.query.filter_by(user_id=current_user.user_id, event_id=event_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from your personal calendar.", "success")
        next_url = request.form.get("next") or url_for("events.event_details", event_id=event_id)
    elif not event.is_active:
        flash("This event is no longer available and can't be added to your calendar.", "warning")
        next_url = request.form.get("next") or url_for("events.events_page")
    else:
        db.session.add(CalendarEvent(user_id=current_user.user_id, event_id=event_id))
        db.session.commit()
        flash("Added to your personal calendar.", "success")
        next_url = request.form.get("next") or url_for("events.event_details", event_id=event_id)

    return redirect(next_url)
