import json
import os
import re
import html
from models.event import Event
from extensions import db
from datetime import datetime


def clean_text(value):
    if not value:
        return ""

    text = html.unescape(str(value))
    text = text.replace("&nbsp;", " ")

  
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"[a-zA-Z0-9_\-\.\#,\s:\*\[\]\(\)]+?\{[^{}]*\}", "", text, flags=re.DOTALL)

    
    text = re.sub(r"<[^>]+>", "", text)

    
    match = re.search(r"[\u0600-\u06FF]", text)
    if match:
        text = text[match.start():]

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None

def load_events_to_database():
    file_path = os.path.join("data", "events.json")

    with open(file_path, "r", encoding="utf-8") as file:
        events = json.load(file)

    for item in events:
        existing_event = Event.query.filter_by(
            title=clean_text(item.get("title", "No Title"))
        ).first()

        if not existing_event:
            event = Event(
                title=clean_text(item.get("title", "No Title")),
                category=clean_text(item.get("category", "General")),
                city=clean_text(item.get("city", "Riyadh")),
                start_date=parse_date(item.get("date", "")),
                time=str(item.get("time", "")),
                description=clean_text(item.get("description", "")),
                image=item.get("image", ""),
                official_link=item.get("external_link") or item.get("official_link", ""),
                source=item.get("source", "Riyadh.sa"),
                price=clean_text(item.get("price", "")),
                location=clean_text(item.get("location", "")),
                end_date=parse_date(item.get("end_date", ""))
            )
            db.session.add(event)

    db.session.commit()
    print("Events inserted successfully")
