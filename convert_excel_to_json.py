import pandas as pd
import json
import os

file_path = "data/events.xlsx"
df = pd.read_excel(file_path)

events = []

for _, row in df.iterrows():
    title = row.get("W-full Description")
    category = row.get("Font")
    price = row.get("Font.2")
    time = row.get("Font.3")
    location = row.get("Font.4")
    image = row.get("W-full Image")
    official_link = row.get("URL")
    start_date = row.get("Start Date")
    end_date = row.get("End Date")

    event = {
        "title": str(title).strip() if pd.notna(title) else "No Title",
        "category": str(category).strip() if pd.notna(category) else "General",
        "city": "Riyadh",
        "date": str(start_date).strip() if pd.notna(start_date) else "",
        "time": str(time).strip() if pd.notna(time) else "",
        "description": str(title).strip() if pd.notna(title) else "",
        "image": str(image).strip() if pd.notna(image) else "",
        "official_link": str(official_link).strip() if pd.notna(official_link) else "",
        "source": "GoSaudis",
        "price": str(price).strip() if pd.notna(price) else "",
        "location": str(location).strip() if pd.notna(location) else "",
        "end_date": str(end_date).strip() if pd.notna(end_date) else ""
    }

    events.append(event)

with open("data/events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=4)

print("events.json created successfully")
print(f"Total events: {len(events)}")