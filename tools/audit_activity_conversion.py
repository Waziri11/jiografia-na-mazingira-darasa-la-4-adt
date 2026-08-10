#!/usr/bin/env python3
"""Build the book-wide activity conversion tracker from the reading spine."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
texts = json.loads((ROOT / "content/i18n/sw/texts.json").read_text(encoding="utf-8"))

question_re = re.compile(r"\b(Maswali|Zoezi|Chagua|Oanisha|Jibu maswali|Eleza|Bainisha|Baini|Kokotoa)\b", re.I)
practical_re = re.compile(r"\b(Chora|Tengeneza|Nenda nje|Tembelea|Tumia atlasi|Google My Maps|simujanja|daftari|karatasi|rula|uzi|bikari)\b", re.I)
type_map = {
    "activity_open_ended_answer": "open_answer",
    "activity_fill_in_a_table": "open_answer",
    "activity_multiple_choice": "multiple_choice",
    "activity_matching": "matching",
}

# These sections introduce a figure, map, or external-tool procedure whose
# actual response questions are converted in the following section/page.
INTENTIONALLY_INSTRUCTIONAL = {
    "pg041_sec001",
    "pg047_sec001",
    "pg054_sec001",
    "pg080_sec001",
    "pg085_sec001",
    "pg095_sec001",
}

tracker = []
for position, page in enumerate(pages, 1):
    path = ROOT / page["href"]
    source = path.read_text(encoding="utf-8")
    ids = list(dict.fromkeys(re.findall(r'data-id="([^"]+)"', source)))
    visible = " ".join(texts.get(text_id, "") for text_id in ids)
    image_alts = " ".join(re.findall(r'alt="([^"]+)"', source))
    combined = f"{visible} {image_alts}"
    section_types = re.findall(r'data-section-type="([^"]+)"', source)
    supported = next((t for t in section_types if t in type_map), None)
    controls = {
        "textareas": len(re.findall(r"<textarea\b", source)),
        "text_inputs": len(re.findall(r'<input\b(?=[^>]*type="text")', source)),
        "radio_options": len(re.findall(r'type="radio"', source)),
        "matching_items": len(re.findall(r'data-activity-item="item-[^"]+"', source)) if supported == "activity_matching" else 0,
        "dropzones": len(re.findall(r'id="dropzone-[^"]+"', source)),
    }
    is_question = bool(question_re.search(combined))
    if not supported and not is_question:
        continue
    if supported:
        status = "converted"
        activity_type = type_map[supported]
        if activity_type == "open_answer":
            question_count = controls["textareas"] + controls["text_inputs"]
        elif activity_type == "multiple_choice":
            question_count = len(set(re.findall(r'name="(question-group-[^"]+)"', source)))
        else:
            question_count = controls["matching_items"]
        answer_key = "not_applicable" if activity_type == "open_answer" else ("verified" if "correctAnswers" in source else "review_required")
        notes = "Interactive controls present."
    else:
        intentional = page["section_id"] in INTENTIONALLY_INSTRUCTIONAL or practical_re.search(combined)
        activity_type = "instructional_practical" if intentional else "open_answer"
        status = "intentionally_instructional" if activity_type == "instructional_practical" else "awaiting_conversion_review"
        question_count = len(re.findall(r"(?:^|\s)\d+[.)]\s", combined)) or 1
        answer_key = "not_applicable"
        notes = "Practical/drawing/external-tool task retained as instructions." if status == "intentionally_instructional" else "Static question signal requires manual review."
    tracker.append({
        "reader_position": position,
        "pdf_page": page.get("page_number"),
        "section_id": page["section_id"],
        "href": page["href"],
        "source_text_ids": ids,
        "source_images": re.findall(r'src="images/([^"]+)"', source),
        "activity_type": activity_type,
        "question_count": question_count,
        "current_state": "interactive" if supported else "static_text_or_image",
        "answer_key_status": answer_key,
        "conversion_status": status,
        "controls": controls,
        "review_notes": notes,
    })

output = ROOT / "content/activity_conversion_tracker.json"
output.write_text(json.dumps(tracker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
summary = {}
for item in tracker:
    summary[item["conversion_status"]] = summary.get(item["conversion_status"], 0) + 1
print(json.dumps({"tracked_sections": len(tracker), "status": summary}, ensure_ascii=False))
