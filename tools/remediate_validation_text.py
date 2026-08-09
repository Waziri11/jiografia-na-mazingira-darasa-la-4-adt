#!/usr/bin/env python3
"""Apply the validation report's deterministic text/accessibility corrections."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

# Report-wide accessibility terminology corrections. Longer forms come first.
GLOBAL = [
    ("Kuonyesha", "Kuwasilisha"),
    ("Onyesha", "Wasilisha"),
    ("Onesha", "Wasilisha"),
    ("inavyoonyeshwa", "inavyowasilishwa"),
    ("zinazoonyeshwa", "zinazowasilishwa"),
    ("kinachoonyeshwa", "kinachowasilishwa"),
    ("iliyoonyeshwa", "iliyowasilishwa"),
    ("inaonyesha", "inawasilisha"),
    ("zinaonyesha", "zinawasilisha"),
    ("kinaonyesha", "kinawasilisha"),
    ("huonyeshwa", "huwasilishwa"),
    ("huonyesha", "huwasilisha"),
    ("kuonyeshwa", "kuwasilishwa"),
    ("kuonyesha", "kuwasilisha"),
    ("onyesha", "wasilisha"),
    ("inavvoonekana", "inavyowasilishwa"),
    ("inavyooneshwa", "inavyowasilishwa"),
    ("zinazooneshwa", "zinazowasilishwa"),
    ("kinachooneshwa", "kinachowasilishwa"),
    ("ilivyoonekana", "ilivyowasilishwa"),
    ("iliyooneshwa", "iliyowasilishwa"),
    ("huoneshwaje", "huwasilishwaje"),
    ("yanavyoonekana", "yalivyowasilishwa"),
    ("vinavyoonekana", "vinavyowakilishwa"),
    ("zinavyoonekana", "zinavyowakilishwa"),
    ("inavyoonekana", "inavyowasilishwa"),
    ("inavyooneka", "inavyowasilishwa"),
    ("inayoonesha", "inayowasilisha"),
    ("unaoonesha", "unawasilisha"),
    ("unapoonesha", "unapowasilisha"),
    ("kinaonesha", "kinawasilisha"),
    ("zinaonesha", "zinawasilisha"),
    ("inaonesha", "inawasilisha"),
    ("huoneshwa", "huwasilishwa"),
    ("huonesha", "huwasilisha"),
    ("kulionesha", "kuliwasilisha"),
    ("ukionesha", "ukiwasilisha"),
    ("itaonesha", "itatuongoza"),
    ("itakuonesha", "itakuongoza"),
    ("kuoneshwa", "kuwasilishwa"),
    ("kuonesha", "kuwasilisha"),
    ("ioneshe", "iwasilishe"),
    ("onesha", "wasilisha"),
]

PAGE = {
    "pg007": [("kutafanua", "kufafanua"), ("zinazowezesha kuwasilishwa", "zinazoweza kuwasilishwa")],
    "pg008": [("yanavyoonekana katika uso wa dunia", "yalivyowasilishwa katika uso wa dunia"),
               ("kama inavyowasilishwa katika Kielelezo namba 1", "kama kilivyowasilishwa katika Kielelezo namba 1")],
    "pg009": [("kama inavyowasilishwa katika Kielelezo namba 2", "kama ilivyowasilishwa katika Kielelezo namba 2")],
    "pg012": [("kuona maeneo", "kutambua maeneo")],
    "pg013": [("Mtwanyiko", "Mtawanyiko")],
    "pg014": [("Mtwanyiko", "Mtawanyiko"),
               ("kama inavyowasilishwa katika Kielelezo namba 6", "kama kilivyowasilishwa katika Kielelezo namba 6")],
    "pg018": [("Kielelezo namba 8 kinawasilisha", "Kielelezo namba 8 kinawakilisha")],
    "pg019": [("ulichoabaini", "ulichobaini"), ("uliyoabaini", "uliyobaini")],
    "pg025": [("Mashhariki", "Mashariki"), ("(Mas)", "(Mash)")],
    "pg027": [("Ukitazama", "Ukizingatia"), ("ukitazama", "ukizingatia")],
    "pg028": [("Kuangalia", "Kutambua"), ("kuangalia", "kutambua"), ("kwa kulitazama", "kuelekea jua linapochomoza"),
               ("ukilitazama", "ukielekea"), ("kulitaza", "kulielekea")],
    "pg029": [("unapotazama", "unapoelekea")],
    "pg030": [("Ametazama", "Amesimama uelekeo"), ("ametazama", "amesimama uelekeo"),
               ("umetazama upande gani", "umesimama uelekeo gani")],
    "pg031": [("kusoma na kuwasilisha uelekeo", "kubaini uelekeo")],
    "pg032": [("Chora", "Unda"), ("chora", "unda"), ("Andika", "Weka alama ya"), ("andika", "weka alama ya")],
    "pg033": [("Chora", "Unda"), ("chora", "unda"), ("Andika", "Weka alama ya"), ("andika", "weka alama ya")],
    "pg036": [("unapotazama", "unapokabili")],
    "pg040": [("iliilokusudiwa", "lililokusudiwa"), ("Iliilokusudiwa", "Lililokusudiwa"),
               ("tunaweza kuona", "tunaweza kutambua")],
    "pg045": [("uelekeo ya Kaskazini", "uelekeo wa Kaskazini"), ("ulichora", "ulilochora"),
               ("andika jina", "bainisha jina")],
    "pg051": [("simuanja", "simujanja"), ("Simuanja", "Simujanja")],
    "pg060": [("Dasara", "Darasa")],
    "pg061": [("kuwasilisha uelekeo", "kutambua uelekeo")],
    "pg063": [("vilivyonooka", "vilivyonyooka")],
    "pg077": [("ikionekana", "ikipatikana")],
    "pg082": [("inawasilisha", "inawakilisha")],
    "pg084": [("kuwasilisha", "kuwakilisha"), ("unaona", "unatambua"),
               ("karibuana", "karibiana"), ("kuona", "kutambua")],
    "pg085": [("Kielezo namba 29", "Kielelezo namba 29")],
    "pg087": [("[[blank:item-1]]", "jibu sahihi"), ("(a)kutumia", "(a) kutumia"),
               ("(b)kutumia", "(b) kutumia"), ("(c)kutumia", "(c) kutumia"),
               ("(d)kutumia", "(d) kutumia")],
    "pg093": [("inawasilisha", "inawakilisha")],
    "pg095": [("Ramani ya Tanzania kuwasilisha mipaka ya kiutawala",
                "Ramani ya Tanzania inayowasilisha mipaka ya kiutawala")],
}


def replace_case_sensitive(text: str, pairs):
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def clean_value(value: str, page: str) -> str:
    if value.strip().upper() in {"FOR ONLINE READING ONLY", "FOR ONLINE USE ONLY"}:
        return ""
    if re.fullmatch(r"JIOGRAFIA NA MAZINGIRA DARASA LA 4\.indd(?:\s+\d+)?", value.strip(), re.IGNORECASE):
        return ""
    if re.fullmatch(r"12/09/2025\s+\d{2}:\d{2}", value.strip()):
        return ""
    value = replace_case_sensitive(value, GLOBAL)
    value = replace_case_sensitive(value, PAGE.get(page, []))
    return value


def clean_html(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    page = path.stem[:5]
    updated = source
    # Remove printer-only elements completely so neither screen readers nor TTS encounter them.
    updated = re.sub(
        r'\s*<(?P<tag>[a-z0-9]+)\b[^>]*>\s*FOR ONLINE (?:READING|USE) ONLY\s*</(?P=tag)>',
        "", updated, flags=re.IGNORECASE,
    )
    updated = replace_case_sensitive(updated, GLOBAL)
    updated = replace_case_sensitive(updated, PAGE.get(page, []))
    if updated != source:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


changed_html = sum(clean_html(p) for p in sorted(ROOT.glob("pg*.html")))

changed_json = 0
for language in ("sw", "sw-TZ"):
    path = ROOT / "content" / "i18n" / language / "texts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for key, value in list(data.items()):
        page = key[:5] if key.startswith("pg") else ""
        new_value = clean_value(value, page)
        if new_value != value:
            data[key] = new_value
            changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed_json += 1

print(f"updated {changed_html} HTML files and {changed_json} text catalogs")
