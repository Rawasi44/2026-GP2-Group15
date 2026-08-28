import json
import re
import os

def get_event_id(link):
    match = re.search(r"/event/(\d+)", link or "")
    return match.group(1) if match else None

with open("riyadh_events_final.json", "r", encoding="utf-8") as f:
    english_events = json.load(f)

with open("data/events.json", "r", encoding="utf-8") as f:
    arabic_events = json.load(f)

arabic_links = {}
for ev in arabic_events:
    event_id = get_event_id(ev.get("official_link"))
    if event_id:
        arabic_links[event_id] = ev.get("external_link", "")

for ev in english_events:
    event_id = get_event_id(ev.get("official_link"))
    if event_id:
        ev["external_link"] = arabic_links.get(event_id, "")

os.makedirs("data", exist_ok=True)

with open("data/events.json", "w", encoding="utf-8") as f:
    json.dump(english_events, f, ensure_ascii=False, indent=2)

print("Done: data/events.json created with English text + external links")