#!/usr/bin/env python3
"""Register the restored official front matter in manifests and catalogs."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

FRONT = [
    {"section_id": "pg001_sec001", "href": "index.html", "page_number": 1},
    {"section_id": "pg002_sec001", "href": "pg002_sec001.html", "page_number": 2},
    {"section_id": "pg003_sec001", "href": "pg003_sec001.html", "page_number": 3},
    {"section_id": "pg004_sec001", "href": "pg004_sec001.html", "page_number": 4},
    {"section_id": "pg005_sec001", "href": "pg005_sec001.html", "page_number": 5},
]

TEXTS = {
    "pg002_n0001": "Hakimiliki",
    "pg002_n0002": "© Taasisi ya Elimu Tanzania 2024",
    "pg002_n0003": "Toleo la kwanza 2024",
    "pg002_n0004": "ISBN: 978-9912-753-83-9",
    "pg002_n0005": "Taasisi ya Elimu Tanzania, Eneo la Mikocheni, 132 Barabara ya Ali Hassan Mwinyi, S.L.P. 35094, 14112 Dar es Salaam.",
    "pg002_n0006": "Simu: +255 735 041 170 / +255 735 041 168. Baruapepe: director.general@tie.go.tz. Tovuti: www.tie.go.tz.",
    "pg002_n0007": "Haki zote zimehifadhiwa. Hairuhusiwi kunakili, kurudufu, kuchapisha, kutafsiri, wala kukitoa kitabu hiki kwa namna yoyote ile bila idhini ya maandishi kutoka Taasisi ya Elimu Tanzania.",
    "pg004_n0001": "Shukurani",
    "pg004_n0002": "Taasisi ya Elimu Tanzania (TET) inatambua na kuthamini mchango muhimu wa washiriki kutoka taasisi mbalimbali za serikali na zisizo za serikali zilizoshiriki kufanikisha uandishi wa kitabu hiki cha mwanafunzi.",
    "pg004_n0003": "Kipekee, TET inatoa shukurani kwa Chuo Kikuu cha Dar es Salaam, Chuo Kikuu cha Dodoma, Idara ya Uthibiti Ubora wa Shule, vyuo vya ualimu, pamoja na shule za msingi na sekondari.",
    "pg004_n0004": "Dkt. Zahor K. Zahor (UDSM), Dkt. Verdiana T. Tilumanywa (UDSM), Bw. Dickson A. Kavishe (UDSM), Bi. Blandina F. Ajali (TET), Bw. Karani H. Mdee (TET), Bi. Neema A. Kashindye (TET), Bw. Musa T. Mwalutanile (TET), Bi. Mariam Japhet (TET), na Bi. Beatrice S. Rulenguka (TET).",
    "pg004_n0005": "Dkt. Festo J. Ntensya (UDSM), Dkt. Mromba Clement (UDSM), Dkt. Fredy Mswima (UDOM), Bw. Frank Mahuve (UDOM), na Mwl. Michael Sichundwe (Tusiime Sekondari).",
    "pg004_n0006": "Bw. Maulid M. Majaliwa.",
    "pg004_n0007": "Bw. Fikiri Msimbe na Bw. Hance E. Wawar (TET).",
    "pg004_n0008": "Bw. Dickson A. Kavishe (UDSM) na Bw. Frank Mahuve (UDOM).",
    "pg004_n0009": "Bi. Blandina F. Ajali (TET).",
    "pg005_n0001": "Shukurani",
    "pg005_n0002": "Vilevile, TET inatoa shukurani kwa walimu wote wa shule za msingi na wanafunzi walioshiriki katika ujaribishaji wa maudhui ya kitabu hiki.",
    "pg005_n0003": "Mwisho, TET inatoa shukurani za kipekee kwa Serikali ya Jamhuri ya Muungano wa Tanzania kwa kutoa fedha zilizofanikisha kazi ya uandishi na uchapaji wa kitabu hiki.",
    "pg005_n0004": "Dkt. Aneth A. Komba",
    "pg005_n0005": "Mkurugenzi Mkuu, Taasisi ya Elimu Tanzania",
}

pages_path = ROOT / "content/pages.json"
pages = json.loads(pages_path.read_text(encoding="utf-8"))
pages = FRONT + [p for p in pages if p["href"] not in {x["href"] for x in FRONT}]
pages_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

toc_path = ROOT / "content/toc.json"
toc = json.loads(toc_path.read_text(encoding="utf-8"))
front_toc = [
    {"section_id": "pg001_sec001", "href": "index.html", "title": "Jiografia na Mazingira", "chapter_id": "pg001_n0003", "level": 1},
    {"section_id": "pg002_sec001", "href": "pg002_sec001.html", "title": "Hakimiliki", "chapter_id": "pg002_n0001", "level": 1},
    {"section_id": "pg003_sec001", "href": "pg003_sec001.html", "title": "Yaliyomo", "chapter_id": "pg003_n0002", "level": 1},
    {"section_id": "pg004_sec001", "href": "pg004_sec001.html", "title": "Shukurani", "chapter_id": "pg004_n0001", "level": 1},
    {"section_id": "pg005_sec001", "href": "pg005_sec001.html", "title": "Shukurani na uthibitisho", "chapter_id": "pg005_n0001", "level": 1},
]
toc = front_toc + [entry for entry in toc if entry.get("href") not in {x["href"] for x in front_toc}]
toc_path.write_text(json.dumps(toc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for language in ("sw", "sw-TZ"):
    text_path = ROOT / f"content/i18n/{language}/texts.json"
    data = json.loads(text_path.read_text(encoding="utf-8"))
    data.update(TEXTS)
    text_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audio_path = ROOT / f"content/i18n/{language}/audios.json"
    audio = json.loads(audio_path.read_text(encoding="utf-8"))
    audio.update({key: f"{key}.mp3" for key in TEXTS})
    audio_path.write_text(json.dumps(audio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for index, page in enumerate(pages, start=1):
    path = ROOT / page["href"]
    html = path.read_text(encoding="utf-8")
    html = re.sub(r'(<meta\s+name="page-section-id"\s+content=")[^"]+("\s*/?>)', rf"\g<1>{index}\2", html, count=1)
    path.write_text(html, encoding="utf-8")

print(f"registered {len(FRONT) - 2} restored front-matter pages")
