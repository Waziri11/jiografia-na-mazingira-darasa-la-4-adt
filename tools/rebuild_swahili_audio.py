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


def speech_text(text: str) -> str:
    text = text.replace("FOR ONLINE READING ONLY", "")
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
    text = re.sub(r"\b1\s*:\s*50\s*000\b", "moja kwa elfu hamsini", text)
    text = re.sub(r"\b1\s*:\s*100\s*000\b", "moja kwa laki moja", text)
    text = re.sub(r"\b(Sm|sm)\b", "sentimeta", text)
    text = re.sub(r"\b(Km|km)\b", "kilometa", text)
    text = text.replace("=", " ni sawa sawa na ").replace("×", " zidisha na ")
    # Decimal numbers are spoken digit by digit after the decimal point.
    text = re.sub(r"\b(\d+)\.(\d+)\b", lambda m: number_sw(int(m.group(1))) + " nukta " +
                  ", ".join(ONES[int(d)] for d in m.group(2)), text)
    # Roman class/list numerals.
    text = re.sub(r"\b(?:VIII|VII|VI|IV|IX|III|II|V|X|I)\b", lambda m: ROMAN[m.group(0)], text)
    # Alternative markers are expanded to Swahili letter names.
    text = re.sub(r"\(([a-nA-N])\)", lambda m: f"kipengele {LETTERS[m.group(1).lower()]}", text)
    text = re.sub(r"\b\d+\b", lambda m: number_sw(int(m.group(0))), text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def synthesize(key: str, text: str, output: Path, semaphore: asyncio.Semaphore):
    spoken = speech_text(text)
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
