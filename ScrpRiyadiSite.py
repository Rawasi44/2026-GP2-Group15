import json
import requests
import pandas as pd
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

HEADERS = {"Accept": "application/json", "Accept-Language": "ar"}
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_all_events():
    all_events = []
    page = 0
    while True:
        url = f"https://api.riyadh.sa/api/Events?_format=json&langcode=ar&page={page}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        items = r.json().get("result", {}).get("items", [])
        if not items:
            break
        print(f"page={page} → {len(items)} فعالية")
        all_events.extend(items)
        page += 1
    return all_events

def get_registration_links(events: list) -> dict:
    reg_links = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, ev in enumerate(events, 1):
            url = ev.get("link", "")
            if not url:
                continue
            print(f"[{i}/{len(events)}] سحب رابط التسجيل...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(4000)

                reg_link = ""
                for link in page.locator("a").all():
                    try:
                        text = link.inner_text().strip()
                        href = link.get_attribute("href") or ""
                        if ("سجل" in text or "register" in text.lower() or
                            "engage" in href or "reg_form" in href or
                            "ticket" in href or "book" in href):
                            if href.startswith("http"):
                                reg_link = href
                                break
                    except:
                        continue

                reg_links[url] = reg_link
                print(f"  {'✅ ' + reg_link if reg_link else '— لا يوجد'}")

            except Exception as e:
                print(f"  ❌ {e}")
                reg_links[url] = ""

        browser.close()
    return reg_links

def clean_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", str(text)).strip()

def format_date(timestamp):
    if not timestamp:
        return ""
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d")
    except:
        return str(timestamp)

def format_time(time_val):
    if not time_val or not isinstance(time_val, dict):
        return ""
    try:
        def secs(s):
            h, m = divmod(int(s) // 60, 60)
            return f"{h:02d}:{m:02d}"
        return f"{secs(time_val.get('start_time', 0))} - {secs(time_val.get('finish_time', 0))}"
    except:
        return ""

def parse_event(ev, reg_link=""):
    image = ev.get("image", "")
    if isinstance(image, list) and image:
        image = image[0].get("url", "")

    cat = ev.get("category", "")
    if isinstance(cat, list) and cat:
        cat = cat[0].get("taxonomy_term_name", "")
    elif isinstance(cat, dict):
        cat = cat.get("taxonomy_term_name", "")

    return {
        "title":         ev.get("title", ""),
        "category":      cat,
        "city":          "Riyadh",
        "date":          format_date(ev.get("start_date")),
        "time":          format_time(ev.get("time")),
        "description":   clean_html(ev.get("body", "")),
        "image":         image,
        "official_link": ev.get("link", ""),
        "source":        "Riyadh.sa",
        "price":         ev.get("cost") or "",
        "location":      ev.get("geofield", {}).get("lat", "") if isinstance(ev.get("geofield"), dict) else "",
        "end_date":      format_date(ev.get("finish_date")),
        "external_link": reg_link,
    }

if __name__ == "__main__":
    print("جاري سحب الفعاليات...")
    raw = fetch_all_events()
    print(f"إجمالي: {len(raw)} فعالية\n")

    print("جاري سحب روابط التسجيل...")
    reg_links = get_registration_links(raw)

    events = [parse_event(ev, reg_links.get(ev.get("link", ""), "")) for ev in raw]

    json_path = os.path.join(SAVE_DIR, "riyadh_events_final.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    xlsx_path = os.path.join(SAVE_DIR, "riyadh_events_final.xlsx")
    pd.DataFrame(events).to_excel(xlsx_path, index=False)

    print(f"\n✅ JSON:  {json_path}")
    print(f"✅ Excel: {xlsx_path}")
    print(f"✅ فعاليات بروابط تسجيل: {sum(1 for e in events if e['external_link'])}")