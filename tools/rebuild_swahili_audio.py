#!/usr/bin/env python3
"""Rebuild page narration using a Tanzanian Swahili voice.

Display text remains unchanged. Speech text expands numbers, scales, units,
operators, Roman numerals, and list markers so they are read in Swahili.
"""

from pathlib import Path
import argparse
import asyncio
import json
import re
import shutil

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"

ONES = ["sifuri", "moja", "mbili", "tatu", "nne", "tano", "sita", "saba", "nane", "tisa"]
TENS = {10: "kumi", 20: "ishirini", 30: "thelathini", 40: "arobaini", 50: "hamsini",
        60: "sitini", 70: "sabini", 80: "themanini", 90: "tisini"}
LETTERS = {"a": "a", "b": "be", "c": "che", "d": "de", "e": "e", "f": "fe", "g": "ge",
           "h": "he", "i": "i", "j": "je", "k": "ke", "l": "le", "m": "me", "n": "ne"}
ROMAN = {"I": "moja", "II": "mbili", "III": "tatu", "IV": "nne", "V": "tano", "VI": "sita",
         "VII": "saba", "VIII": "nane", "IX": "tisa", "X": "kumi"}
CLASS_ORDINAL = {"I": "kwanza", "II": "pili", "III": "tatu", "IV": "nne", "V": "tano",
                 "VI": "sita", "VII": "saba", "VIII": "nane", "IX": "tisa", "X": "kumi"}

# Keep the visible text in Swahili, but guide the Tanzanian Swahili voice to
# pronounce embedded English product and interface terms naturally. Longer
# phrases must precede their component words.
ENGLISH_SPEECH = (
    (r"\bKas\s*[-–]\s*Mas\b", "Kaskazini Mashariki"),
    (r"\bKus\s*[-–]\s*Magh\b", "Kusini Magharibi"),
    (r"\bKus\s*[-–]\s*Mas\b", "Kusini Mashariki"),
    (r"\bKas\s*[-–]\s*Magh\b", "Kaskazini Magharibi"),
    (r"\bUDSM\b", "Yu Dee Es Em"),
    (r"\bUSGS\b", "Yu Es Jee Es"),
    (r"\bRCMRD\b", "Aa See Em Aa Dee"),
    (r"\bESRI\b", "Ee Es Aa Ai"),
    (r"\bGPS\b", "Jee Pee Es"),
    (r"\bDkt\.?", "Daktari"),
    (r"\bBw\.?", "Bwana"),
    (r"\bGoogle My Maps\b", "Guu gol Mai Maps"),
    (r"\bGoogle Maps\b", "Guu gol Maps"),
    (r"\bOpenStreetMap\b", "Oupen Street Map"),
    (r"\bOpenstreet Map\b", "Oupen Street Map"),
    (r"\bMy Maps\b", "Mai Maps"),
    (r"\bGoogle\b", "Guu gol"),
    (r"\bCreate a new map\b", "Kri eit a nyuu map"),
    (r"\bcreate new maps\b", "Kri eit nyuu maps"),
    (r"\bMeasure distances and areas\b", "Mezha distansiz and erias"),
    (r"\bAdd line or shapes\b", "Ad lain or sheips"),
    (r"\bNot owned\b", "Not ound"),
    (r"\bAdd line or shape\b", "Ad lain or sheip"),
    (r"\bAdd driving route\b", "Ad draiving ruut"),
    (r"\bAdd biking route\b", "Ad baiking ruut"),
    (r"\bAdd walking route\b", "Ad woking ruut"),
    (r"\bRename this layer\b", "Ri neim this leia"),
    (r"\bEdit layer name\b", "Edit leia neim"),
    (r"\bPolygon transparency\b", "Poligon transperensi"),
    (r"\bBorder width\b", "Boda width"),
    (r"\bUntitled map\b", "An taitold map"),
    (r"\bMap title\b", "Map taitol"),
    (r"\bPrint map\b", "Print map"),
    (r"\bAdd layer\b", "Ad leia"),
    (r"\bDraw line\b", "Dro lain"),
    (r"\bGame Reserve\b", "Geim Rizav"),
    (r"\bPolygon\s*1\b", "Poligon wan"),
    (r"\bOwned\b", "Ound"),
    (r"\bShared\b", "Shead"),
    (r"\bRecent\b", "Riisent"),
    (r"\bPreview\b", "Privyuu"),
    (r"\bShare\b", "Shea"),
    (r"\bLandscape\b", "Landskeip"),
    (r"\bPortrait\b", "Potret"),
    (r"\bImport\b", "Import"),
    (r"\bCancel\b", "Kansel"),
    (r"\bStyle\b", "Stail"),
    (r"\bSave\b", "Seiv"),
    (r"\bPrint\b", "Print"),
    (r"\bImage\b", "Imij"),
    (r"\bAll\b", "Ol"),
    (r"\bFDC\b", "Ef Dee See"),
    (r"\bPDF\b", "Pee Dee Ef"),
    (r"\bsearch\b", "Sach"),
    (r"\bAutoCAD\b", "Oto Kad"),
    (r"\bArcGIS\b", "Ark Jee Ai Es"),
    (r"\bQGIS\b", "Kyu Jee Ai Es"),
)

# Some layouts keep the question number in its own text node. These IDs must be
# announced as question labels instead of being read as bare cardinal numbers.
QUESTION_NUMBER_IDS = {
    "pg021_n0032": 1,
    "pg022_n0005": 2, "pg022_n0015": 3, "pg022_n0025": 4,
    "pg022_n0035": 5, "pg022_n0045": 6,
    "pg023_n0008": 7, "pg023_n0020": 8,
    "pg029_n0024": 1,
    "pg036_n0009": 1, "pg036_n0020": 2, "pg036_n0031": 3, "pg036_n0042": 4,
    "pg037_n0002": 5, "pg037_n0015": 6, "pg037_n0017": 7, "pg037_n0019": 8,
    "pg041_n0007": 1,
    "pg049_n0004": 1, "pg049_n0006": 2,
    "pg050_n0024": 1, "pg050_n0026": 2,
    "pg057_n0005": 1, "pg057_n0016": 2, "pg057_n0027": 3, "pg057_n0038": 4,
    "pg081_n0006": 1, "pg081_n0009": 2, "pg081_n0012": 3,
    "pg081_n0015": 4, "pg081_n0018": 5,
    "pg087_n0005": 1,
    "pg088_n0011": 3, "pg088_n0022": 4, "pg088_n0033": 5, "pg088_n0046": 6,
    "pg090_n0006": 1, "pg090_n0017": 2, "pg090_n0028": 3,
    "pg090_n0039": 4, "pg090_n0050": 5,
    "pg092_n0003": 10, "pg092_n0013": 11, "pg092_n0023": 12,
    "pg092_n0039": 13, "pg092_n0041": 14, "pg092_n0043": 15, "pg092_n0045": 16,
    "pg093_n0002": 17, "pg093_n0007": 18,
    "pg096_n0004": 19, "pg096_n0007": 20, "pg096_n0010": 21,
    "pg096_n0013": 22, "pg096_n0016": 23, "pg096_n0019": 24, "pg096_n0022": 25,
}

# Pages whose numbered text nodes are exercise questions/prompts. Numbered
# how-to instructions elsewhere in the book deliberately remain cardinal.
QUESTION_TEXT_PAGES = {
    8, 15, 16, 19, 21, 24, 27, 29, 30, 35, 42, 46, 48,
    56, 58, 60, 62, 63, 76, 82, 83, 86, 89, 91,
}
QUESTION_TEXT_EXCLUSIONS = {
    "pg056_n0002",  # final step of the preceding map-printing procedure
    "pg086_n0007", "pg086_n0008", "pg086_n0009", "pg086_n0010", "pg086_n0011",
}

TOC_SPEECH = {
    "pg003_im006": (
        "Shukurani, ukurasa wa namba ya Kirumi nne. "
        "Utangulizi, ukurasa wa namba ya Kirumi sita. "
        "Sura ya Kwanza, ukurasa wa kwanza. Dhana ya ramani, ukurasa wa kwanza. "
        "Sura ya Pili, ukurasa namba 19. Pande Kuu za Dunia, ukurasa namba 19. "
        "Sura ya Tatu, ukurasa namba 33. Uchoraji wa ramani sahili, ukurasa namba 33. "
        "Sura ya Nne, ukurasa namba 53. Matumizi ya ramani, ukurasa namba 53. "
        "Jaribio, ukurasa namba 84."
    ),
    "pg003_n0006": "Shukurani, ukurasa wa namba ya Kirumi nne.",
    "pg003_n0009": "Utangulizi, ukurasa wa namba ya Kirumi sita.",
    "pg003_n0012": "Sura ya Kwanza, ukurasa wa kwanza.",
    "pg003_n0015": "Dhana ya ramani, ukurasa wa kwanza.",
    "pg003_n0018": "Sura ya Pili, ukurasa namba 19.",
    "pg003_n0021": "Pande Kuu za Dunia, ukurasa namba 19.",
    "pg003_n0024": "Sura ya Tatu, ukurasa namba 33.",
    "pg003_n0027": "Uchoraji wa ramani sahili, ukurasa namba 33.",
    "pg003_n0030": "Sura ya Nne, ukurasa namba 53.",
    "pg003_n0033": "Matumizi ya ramani, ukurasa namba 53.",
    "pg003_n0036": "Jaribio, ukurasa namba 84.",
    "pg015_n0038": (
        "Swali la kwanza. Kwa nini ramani za thematiki zinaweza kutofautiana sana "
        "hata kama zinawasilisha eneo moja?"
    ),
    "pg015_n0040": (
        "Swali la pili. Iwapo kuna dharura ya moto katika mtaa wako, ni aina gani ya "
        "ramani ungetumia kuwaelekeza wataalamu wa kuzima moto kufika eneo hilo?"
    ),
    "pg015_n0042": (
        "Swali la tatu. Fuatilia maelezo yafuatayo, kisha pendekeza aina ya ramani "
        "inayoweza kutumiwa na watu wafuatao."
    ),
    "pg015_n0038_easy_read": (
        "Swali la kwanza. Kwa nini ramani za thematiki zinaweza kutofautiana sana, "
        "hata kama zinawasilisha eneo moja?"
    ),
    "pg015_n0040_easy_read": (
        "Swali la pili. Ikiwa kuna dharura ya moto katika mtaa wako, ni aina gani ya "
        "ramani ungetumia kuwaelekeza wataalamu wa kuzima moto wafike eneo hilo?"
    ),
    "pg015_n0042_easy_read": (
        "Swali la tatu. Chunguza jedwali lifuatalo. Kisha pendekeza aina ya ramani "
        "ambayo watu wafuatao wanaweza kutumia."
    ),
}

TABLE_23_SPEECH = {
    "pg023_n0032": "Namba moja ya Kirumi, Ramani za topografia.",
    "pg023_n0039": "Namba mbili ya Kirumi, Fremu.",
    "pg023_n0046": "Namba tatu ya Kirumi, Vipengele muhimu katika ramani.",
    "pg023_n0058": "Namba nne ya Kirumi, Skeli.",
    "pg023_n0068": "Namba tano ya Kirumi, Sehemu ambapo ramani inaweza kuchorwa.",
    "pg023_n0036": "Herufi a, juu ya karatasi, ardhi, kitambaa na kompyuta.",
    "pg023_n0043": "Herufi bee, huwakilisha maumbo ya uso wa dunia.",
    "pg023_n0053": "Herufi see, uhusiano wa umbali uliowasilishwa katika ramani na umbali halisi uliopo katika ardhi.",
    "pg023_n0063": "Herufi dee, skeli, fremu, uelekeo wa Kaskazini, kichwa cha ramani, ufunguo, chanzo na mistari ya gridi.",
    "pg023_n0075": "Herufi e, kuwasilisha mpaka wa ramani husika.",
    "pg023_n0080": "Herufi efu, isomeke kwa urahisi kwa watumiaji wa ramani husika.",
    "pg024_n0006": "Herufi gee, hufafanua alama na ishara zilizotumika katika ramani.",
}
TOC_SPEECH.update({
    "pg025_n0002": "Sura ya Pili. Pande Kuu za Dunia.",
    "pg025_n0002_easy_read": "Sura ya Pili. Pande Kuu za Dunia.",
    "pg029_n0016": "Swali la kwanza. Nenda nje ya darasa wakati wa asubuhi, na simama eneo la katikati ya shule yako.",
    "pg029_n0018": "Swali la pili. Baini upande wa jua linakochomoza, kisha bainisha Pande Kuu za Dunia na utaje vitu vinavyopatikana katika upande husika.",
    "pg029_n0020": "Swali la tatu. Tengeneza kifani cha Pande Kuu za Dunia kwa kutumia makunzi yanayopatikana katika mazingira uliopo.",
    "pg029_n0016_easy_read": "Swali la kwanza. Nenda nje ya darasa wakati wa asubuhi. Simama katikati ya shule yako.",
    "pg029_n0018_easy_read": "Swali la pili. Baini upande ambao jua linachomoza. Kisha bainisha Pande Kuu za Dunia. Halafu taja vitu vilivyopo upande huo.",
    "pg029_n0020_easy_read": "Swali la tatu. Tengeneza kifani cha Pande Kuu za Dunia. Tumia makunzi yanayopatikana katika mazingira yako.",
})
TOC_SPEECH.update(TABLE_23_SPEECH)
TOC_SPEECH.update({f"{key}_easy_read": value for key, value in TABLE_23_SPEECH.items()})

STEPS_32_SPEECH = {
    "pg032_n0004": "Hatua a. Chukua dira yako au pakua programu tumizi ya dira;",
    "pg032_n0005": "Hatua bee. Bofya programu tumizi ya dira na hakikisha mshale wa dira yako umeelekea upande wa Kaskazini, Kas;",
    "pg032_n0006": "Hatua see. Wakati mshale wa dira umeelekea upande wa Kaskazini, geuka kuelekea upande huo.",
    "pg032_n0008": "Hatua dee. Mara baada ya kutambua uelekeo wa Kaskazini, unaweza kubaini pande nyingine za dunia.",
}
TOC_SPEECH.update(STEPS_32_SPEECH)
TOC_SPEECH.update({f"{key}_easy_read": value for key, value in STEPS_32_SPEECH.items()})

# These five instructions form one Roman-numbered list across pages 68–69.
# Prefix the narration with an explicit ordinal so it sounds like a list too.
ROMAN_STEP_ORDINALS = {
    "pg068_n0022": "kwanza",
    "pg069_n0002": "pili",
    "pg069_n0003": "tatu",
    "pg069_n0005": "nne",
    "pg069_n0006": "tano",
}

# Easy-read mode uses the same table-of-contents page references.
TOC_SPEECH.update({f"{key}_easy_read": value for key, value in list(TOC_SPEECH.items())
                   if key.startswith("pg003_n")})


def number_sw(n: int) -> str:
    if n < 10:
        return ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        base = TENS[tens * 10]
        return base if not ones else f"{base} na {ONES[ones]}"
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        base = "mia moja" if hundreds == 1 else f"mia {ONES[hundreds]}"
        return base if not rest else f"{base} na {number_sw(rest)}"
    if n < 1_000_000:
        thousands, rest = divmod(n, 1000)
        base = f"elfu {number_sw(thousands)}"
        return base if not rest else f"{base} na {number_sw(rest)}"
    return " ".join(ONES[int(d)] for d in str(n))


def question_ordinal(n: int) -> str:
    if n == 1:
        return "kwanza"
    if n == 2:
        return "pili"
    return number_sw(n)


def question_number(key: str, text: str):
    base_key = key.removesuffix("_easy_read")
    if base_key in QUESTION_NUMBER_IDS:
        return QUESTION_NUMBER_IDS[base_key]
    page_match = re.match(r"pg(\d{3})_", base_key)
    number_match = re.match(r"^(\d{1,2})\.\s+", text)
    if (page_match and number_match and int(page_match.group(1)) in QUESTION_TEXT_PAGES
            and base_key not in QUESTION_TEXT_EXCLUSIONS):
        return int(number_match.group(1))
    return None


def speech_text(text: str, key: str = "") -> str:
    text = text.replace("FOR ONLINE READING ONLY", "")
    for pattern, pronunciation in ENGLISH_SPEECH:
        text = re.sub(pattern, pronunciation, text, flags=re.IGNORECASE)
    q_number = question_number(key, text) if key else None
    if q_number is not None:
        label = f"Swali la {question_ordinal(q_number)}."
        if re.fullmatch(r"\s*\d{1,2}\.?\s*", text):
            text = label
        else:
            text = re.sub(r"^\d{1,2}\.\s*", f"{label} ", text)
    step_ordinal = ROMAN_STEP_ORDINALS.get(key.removesuffix("_easy_read")) if key else None
    if step_ordinal:
        text = f"Hatua ya {step_ordinal}. {text}"
    # Class levels are ordinal in Swahili (Darasa la pili, not Darasa la mbili).
    text = re.sub(
        r"\bDarasa la (VIII|VII|VI|IV|IX|III|II|V|X|I)\s*[-–]\s*(VIII|VII|VI|IV|IX|III|II|V|X|I)\b",
        lambda m: f"Darasa la {CLASS_ORDINAL[m.group(1).upper()]} hadi la {CLASS_ORDINAL[m.group(2).upper()]}",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bDarasa la (VIII|VII|VI|IV|IX|III|II|V|X|I)\b",
        lambda m: f"Darasa la {CLASS_ORDINAL[m.group(1).upper()]}",
        text,
        flags=re.IGNORECASE,
    )
    # A parenthesized zero marks the scale origin visually and is intentionally silent.
    text = re.sub(r"\(\s*0\s*\)", "", text)
    # Speak the two common presentations of the 1-to-50,000 scale distinctly.
    text = re.sub(
        r"<math>\s*<mfrac>\s*<mn>\s*1\s*</mn>\s*<mn>\s*50\s*000\s*</mn>\s*</mfrac>\s*</math>",
        "moja juu ya hamsini elfu",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\b1\s*/\s*50\s*000\b", "moja juu ya hamsini elfu", text)
    text = re.sub(r"\b1\s*:\s*50\s*000\b", "moja kwa uwiano wa hamsini elfu", text)
    text = re.sub(r"\b1\s*:\s*100\s*000\b", "moja kwa laki moja", text)
    text = re.sub(r"\b(Sm|sm)\b", "sentimeta", text)
    text = re.sub(r"\b(Km|km)\b", "kilometa", text)
    # Keep the printed line label as “AB”, but pronounce its letters separately.
    text = re.sub(r"\bAB\b", "ah, bee", text)
    text = text.replace("=", " ni sawa sawa na ").replace("×", " zidisha na ")
    # Decimal numbers are spoken digit by digit after the decimal point.
    text = re.sub(r"\b(\d+)\.(\d+)\b", lambda m: number_sw(int(m.group(1))) + " nukta " +
                  ", ".join(ONES[int(d)] for d in m.group(2)), text)
    # Roman class/list numerals.
    text = re.sub(r"\b(?:VIII|VII|VI|IV|IX|III|II|V|X|I)\b", lambda m: ROMAN[m.group(0)], text)
    # Alternative markers are expanded to Swahili letter names.
    text = re.sub(r"\(([a-nA-N])\)", lambda m: f"kipengele {LETTERS[m.group(1).lower()]},", text)
    text = re.sub(r"\b\d+\b", lambda m: number_sw(int(m.group(0))), text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def synthesize(key: str, text: str, output: Path, semaphore: asyncio.Semaphore):
    spoken = speech_text(TOC_SPEECH.get(key, text), key)
    if not spoken:
        return "skip"
    async with semaphore:
        for attempt in range(4):
            try:
                temp = output.with_suffix(".tmp.mp3")
                await asyncio.wait_for(
                    edge_tts.Communicate(spoken, VOICE, rate="-4%", pitch="+0Hz").save(str(temp)),
                    timeout=45,
                )
                temp.replace(output)
                return "ok"
            except Exception:
                temp.unlink(missing_ok=True)
                if attempt == 3:
                    raise
                await asyncio.sleep(1.5 * (attempt + 1))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int, default=999)
    parser.add_argument("--concurrency", type=int, default=12)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--match", help="Only synthesize text matching this regular expression")
    parser.add_argument("--english-only", action="store_true",
                        help="Only rebuild text containing a configured English term")
    parser.add_argument("--questions-only", action="store_true",
                        help="Only rebuild numbered question labels/prompts")
    args = parser.parse_args()

    texts = json.loads((ROOT / "content/i18n/sw/texts.json").read_text(encoding="utf-8"))
    audios = json.loads((ROOT / "content/i18n/sw/audios.json").read_text(encoding="utf-8"))
    jobs = []
    for key, filename in audios.items():
        match = re.match(r"pg(\d{3})_", key)
        if not match or not (args.start_page <= int(match.group(1)) <= args.end_page):
            continue
        text = texts.get(key, "")
        if not text.strip():
            continue
        if args.questions_only and question_number(key, text) is None:
            continue
        if args.english_only and not any(
                re.search(pattern, text, flags=re.IGNORECASE)
                for pattern, _ in ENGLISH_SPEECH):
            continue
        if args.match and not re.search(args.match, text, flags=re.IGNORECASE):
            continue
        output = ROOT / "content/i18n/sw/audio" / filename
        if output.exists() and not args.force:
            continue
        jobs.append((key, text, output))
    if args.limit:
        jobs = jobs[:args.limit]
    semaphore = asyncio.Semaphore(args.concurrency)
    completed = 0
    for offset in range(0, len(jobs), 100):
        batch = jobs[offset:offset + 100]
        await asyncio.gather(*(synthesize(key, text, output, semaphore) for key, text, output in batch))
        completed += len(batch)
        print(f"generated {completed}/{len(jobs)}", flush=True)

    # Both bundle languages contain the same Swahili text; keep every mapped
    # page narration identical, including unchanged/empty-text legacy clips.
    for key, filename in audios.items():
        if not key.startswith("pg"):
            continue
        source = ROOT / "content/i18n/sw/audio" / filename
        target = ROOT / "content/i18n/sw-TZ/audio" / filename
        if source.exists():
            shutil.copy2(source, target)


if __name__ == "__main__":
    asyncio.run(main())
