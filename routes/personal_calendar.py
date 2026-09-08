import calendar as pycalendar
from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models.event import Event
from models.calendar_event import CalendarEvent


calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/calendar")
@login_required
def calendar_page():
    today = date.today()

    # Get the requested month/year from the URL.
    # If none are provided, show the current month.
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))

        if month < 1 or month > 12:
            raise ValueError

    except (TypeError, ValueError):
        year = today.year
        month = today.month

    # Previous month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    # Next month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    first_day = date(year, month, 1)
    next_month_first_day = date(next_year, next_month, 1)

    # Historical CalendarEvent rows remain in the database if an event
    # is soft-deleted. Inactive events are simply hidden from the
    # user-facing calendar.
    events = (
        Event.query
        .join(CalendarEvent, CalendarEvent.event_id == Event.id)
        .filter(
            CalendarEvent.user_id == current_user.user_id,
            Event.is_active == True,
            Event.start_date >= first_day,
            Event.start_date < next_month_first_day
        )
        .order_by(
            Event.start_date.asc(),
            Event.time.asc(),
            Event.title.asc()
        )
        .all()
    )

    # Group calendar events by their actual event start date.
    events_by_date = {}

    for event in events:
        events_by_date.setdefault(event.start_date, []).append(event)

    # Build a Sunday-to-Saturday monthly calendar grid.
    calendar_builder = pycalendar.Calendar(firstweekday=6)

    calendar_weeks = []

    for week in calendar_builder.monthdatescalendar(year, month):
        week_data = []

        for day in week:
            week_data.append({
                "date": day,
                "day_number": day.day,
                "in_current_month": day.month == month,
                "is_today": day == today,
                "events": events_by_date.get(day, [])
            })

        calendar_weeks.append(week_data)

    return render_template(
        "calendar.html",
        calendar_weeks=calendar_weeks,
        month=month,
        year=year,
        month_name=pycalendar.month_name[month],
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today=today
    )


@calendar_bp.route("/calendar/<int:event_id>/toggle", methods=["POST"])
@login_required
def toggle_calendar(event_id):
    event = Event.query.get_or_404(event_id)

    existing = CalendarEvent.query.filter_by(
        user_id=current_user.user_id,
        event_id=event_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()

        flash(
            "Removed from your personal calendar.",
            "success"
        )

        next_url = (
            request.form.get("next")
            or url_for(
                "events.event_details",
                event_id=event_id
            )
        )

    elif not event.is_active:
        flash(
            "This event is no longer available and can't be added to your calendar.",
            "warning"
        )

        next_url = (
            request.form.get("next")
            or url_for("events.events_page")
        )

    else:
        db.session.add(
            CalendarEvent(
                user_id=current_user.user_id,
                event_id=event_id
            )
        )

        db.session.commit()

        flash(
            "Added to your personal calendar.",
            "success"
        )

        next_url = (
            request.form.get("next")
            or url_for(
                "events.event_details",
                event_id=event_id
            )
        )

    return redirect(next_url)
