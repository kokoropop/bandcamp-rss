import os
import time
from curl_cffi import requests

# ⬇⬇⬇ ВАШИ ТЕГИ (без grunge) ⬇⬇⬇
TAGS = [
    "postpunk", "post-punk",
    "shoe-gaze", "shoegaze",
    "synth-pop",
    "postrock", "post-rock",
    "emo",
    "darkwave",
    "hardcore-punk",
    "dream-pop", "dreampop",
    "posthardcore", "post-hardcore",
    "goth",
    "atmospheric-black-metal",
    "gothic",
    "slowcore", "slow-core",
    "coldwave",
    "screamo",
    "sludge",
    "mathrock", "math-rock",
    "midwestemo",
    "sludge-metal",
    "midwest emo",
    "post-metal",
    "gothicrock",
    "ethereal",
    "dark-synth",
    "darkpop", "dark-pop",
    "blackgaze", "black-gaze",
    "punk-hardcore",
    "post-blackmetal", "post-black-metal", "postblackmetal",
    "skramz",
    "emoviolence",
    "metallic-hardcore",
    "minimalsynth", "minimal-synth",
    "melodichardcore", "melodic-hardcore",
    "grungegaze",
    "nintendocore",
    "future-pop",
    "sadcore",
    "doomgaze",
    "minimal-wave", "minimalwave",
    "emocore",
    "shoegazer", "shoegazing",
    "midwest",
    "emotional-hardcore",
    "etherealwave",
    "dark-synthpop",
    "chaotic hardcore",
    "dreamo",
    "sludgecore",
    "emo-punk",
    "blackened-hardcore",
    "post-black",
    "neocrust",
    "emotive-hardcore",
    "twinkly", "twinkle",
]

# На GitHub Actions нет Рабочего стола — сохраняем в папку репозитория
OUT_DIR = "rss_feeds"
os.makedirs(OUT_DIR, exist_ok=True)

PAUSE_SEC = 3  # пауза между запросами, чтобы не словить блокировку


def esc(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_date(s):
    if not s:
        return ""
    try:
        from email.utils import format_datetime
        from datetime import datetime, timezone
        dt = datetime.strptime(s.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        return format_datetime(dt)
    except Exception:
        return ""


def make_feed(tag):
    payload = {
        "category_id": 0, "cursor": "*", "geoname_id": 0,
        "include_result_types": ["a", "s"], "size": 100,
        "slice": "new", "tag_norm_names": [tag], "time_facet_id": None,
    }
    try:
        r = requests.post(
            "https://bandcamp.com/api/discover/1/discover_web",
            json=payload, impersonate="chrome",
            headers={
                "Referer": f"https://bandcamp.com/discover/{tag}",
                "Origin": "https://bandcamp.com",
                "Accept": "application/json",
            },
            timeout=30,
        )
    except Exception as e:
        print(f"[{tag}] сетевая ошибка: {e}")
        return

    if r.status_code != 200:
        print(f"[{tag}] ошибка HTTP: {r.status_code}")
        return

    try:
        data = r.json()
    except Exception:
        print(f"[{tag}] ответ не JSON")
        return

    results = data.get("results") or data.get("items") or []
    results = [i for i in results if "/merch/" not in (i.get("itemUrl") or "")]

    rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
    rss += f'<title>Bandcamp: {tag}</title>\n'
    rss += f'<link>https://bandcamp.com/discover/{tag}/digital?s=new</link>\n'
    rss += f'<description>New {tag} releases</description>\n'

    count = 0
    for item in results:
        link = (item.get("itemUrl") or "").split("?")[0]
        if not link:
            continue
        title = item.get("title") or ""
        artist = item.get("albumArtist") or item.get("bandName") or ""
        date = item.get("releaseDate") or ""
        primary = item.get("primaryImage") or {}
        art_id = primary.get("imageId") if isinstance(primary, dict) else None
        img = f"https://f4.bcbits.com/img/a{art_id}_10.jpg" if art_id else ""
        full_title = title if not artist or artist in title else f"{artist} – {title}"

        rss += "<item>\n"
        rss += f"<title>{esc(full_title)}</title>\n"
        rss += f"<link>{esc(link)}</link>\n"
        rss += f'<guid isPermaLink="true">{esc(link)}</guid>\n'
        pub = fmt_date(date)
        if pub:
            rss += f"<pubDate>{pub}</pubDate>\n"
        if img:
            rss += f'<enclosure url="{img}" length="0" type="image/jpeg" />\n'
            rss += f'<description><![CDATA[<img src="{img}" /><br/>{esc(full_title)}]]></description>\n'
        else:
            rss += f"<description>{esc(full_title)}</description>\n"
        rss += "</item>\n"
        count += 1

    rss += "</channel>\n</rss>\n"

    safe = tag.replace("/", "_").replace(" ", "_")
    out = os.path.join(OUT_DIR, f"feed_{safe}.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"[{tag}] {count} элементов → {out}")


total = len(TAGS)
print(f"Всего тегов: {total}. Примерное время: ~{total * PAUSE_SEC // 60} мин.\n")

for i, t in enumerate(TAGS, 1):
    print(f"({i}/{total}) ", end="")
    make_feed(t)
    if i < total:
        time.sleep(PAUSE_SEC)

print(f"\nГотово. Все файлы в папке: {OUT_DIR}")