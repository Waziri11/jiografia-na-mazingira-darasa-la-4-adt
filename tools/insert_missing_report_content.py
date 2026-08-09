#!/usr/bin/env python3
"""Insert the report's specifically identified missing activities/content."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def insert_before(path: Path, marker: str, fragment: str, guard: str):
    text = path.read_text(encoding="utf-8")
    if guard in text:
        return False
    if marker not in text:
        raise RuntimeError(f"marker not found in {path.name}: {marker[:60]}")
    path.write_text(text.replace(marker, fragment + marker, 1), encoding="utf-8")
    return True


# Adapted activity 3 for learners with visual impairment.
for language in ("sw", "sw-TZ"):
    path = ROOT / f"content/i18n/{language}/texts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["pg015_n0042"] = (
        "3. Fuatilia maelezo yafuatayo, kisha pendekeza aina ya ramani inayoweza "
        "kutumiwa na watu wafuatao."
    )
    data["pg036_n0001"] = (
        "(d) Husaidia kuimarisha ulinzi na usalama; Pande Kuu za Dunia husaidia "
        "vyombo vya ulinzi na usalama katika kufanya mawasiliano na kutoa maelekezo "
        "wakati wa hatari na dharura."
    )
    data["pg036_n0047"] = "(b) Kusini"
    data["pg036_n0049"] = "(c) Mashariki"
    data["pg036_n0051"] = "(d) Magharibi"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audio_path = ROOT / f"content/i18n/{language}/audios.json"
    audio_data = json.loads(audio_path.read_text(encoding="utf-8"))
    for key in ("pg036_n0001", "pg036_n0047", "pg036_n0049", "pg036_n0051"):
        audio_data[key] = f"{key}.mp3"
    audio_path.write_text(json.dumps(audio_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pg015 = ROOT / "pg015_sec002.html"
text = pg015.read_text(encoding="utf-8")
text = text.replace(
    "3. Chunguza jedwali lifuatalo, kisha pendekeza aina ya ramani inayoweza kutumiwa na watu wafuatao.",
    "3. Fuatilia maelezo yafuatayo, kisha pendekeza aina ya ramani inayoweza kutumiwa na watu wafuatao.",
)
pg015.write_text(text, encoding="utf-8")

# Missing point (d) immediately before Activity 6.
insert_before(
    ROOT / "pg036_sec001.html",
    '<div class="relative mx-auto max-w-5xl rounded-[2rem] bg-[#f3e3d4]',
    '<p class="mx-auto mb-6 max-w-5xl rounded-2xl border-l-8 border-blue-700 bg-blue-50 p-6 '
    'text-left text-[1.05rem] leading-relaxed text-slate-900" data-id="pg036_n0001">'
    '(d) Husaidia kuimarisha ulinzi na usalama; Pande Kuu za Dunia husaidia vyombo vya '
    'ulinzi na usalama katika kufanya mawasiliano na kutoa maelekezo wakati wa hatari na dharura.'
    '</p>\n    ',
    'data-id="pg036_n0001"',
)

# Complete the missing alternatives for question 4.
question_4_options = '''
          <label class="activity-option flex items-start gap-4 py-1 cursor-pointer max-sm:gap-3">
            <div class="mt-1 h-8 w-8 flex-none rounded-full border border-gray-300 text-gray-500 flex items-center justify-center text-[18px] leading-none">b</div>
            <div class="flex-grow pt-0.5"><input type="radio" name="question-group-4" value="item-14" data-activity-item="item-14" class="sr-only" tabindex="0" aria-label="Swali la 4, chaguo b"><span class="text-[22px] leading-snug text-gray-900" data-id="pg036_n0047">(b) Kusini</span><div class="feedback-container mt-2 hidden"><div class="flex items-center gap-2"><span class="feedback-icon w-5 h-5 rounded-full flex items-center justify-center text-sm"></span><span class="feedback-text text-sm font-medium"></span></div></div></div>
          </label>
          <label class="activity-option flex items-start gap-4 py-1 cursor-pointer max-sm:gap-3">
            <div class="mt-1 h-8 w-8 flex-none rounded-full border border-gray-300 text-gray-500 flex items-center justify-center text-[18px] leading-none">c</div>
            <div class="flex-grow pt-0.5"><input type="radio" name="question-group-4" value="item-15" data-activity-item="item-15" class="sr-only" tabindex="0" aria-label="Swali la 4, chaguo c"><span class="text-[22px] leading-snug text-gray-900" data-id="pg036_n0049">(c) Mashariki</span><div class="feedback-container mt-2 hidden"><div class="flex items-center gap-2"><span class="feedback-icon w-5 h-5 rounded-full flex items-center justify-center text-sm"></span><span class="feedback-text text-sm font-medium"></span></div></div></div>
          </label>
          <label class="activity-option flex items-start gap-4 py-1 cursor-pointer max-sm:gap-3">
            <div class="mt-1 h-8 w-8 flex-none rounded-full border border-gray-300 text-gray-500 flex items-center justify-center text-[18px] leading-none">d</div>
            <div class="flex-grow pt-0.5"><input type="radio" name="question-group-4" value="item-16" data-activity-item="item-16" class="sr-only" tabindex="0" aria-label="Swali la 4, chaguo d"><span class="text-[22px] leading-snug text-gray-900" data-id="pg036_n0051">(d) Magharibi</span><div class="feedback-container mt-2 hidden"><div class="flex items-center gap-2"><span class="feedback-icon w-5 h-5 rounded-full flex items-center justify-center text-sm"></span><span class="feedback-text text-sm font-medium"></span></div></div></div>
          </label>
'''
pg036q = ROOT / "pg036_sec002.html"
qtext = pg036q.read_text(encoding="utf-8")
if 'data-id="pg036_n0047"' not in qtext:
    anchor = '''          </label>
        </div>
      </div>
    </div>
  </section>'''
    qtext = qtext.replace(anchor, '          </label>\n' + question_4_options + '        </div>\n      </div>\n    </div>\n  </section>', 1)
    qtext = qtext.replace('"item-13":false}', '"item-13":false,"item-14":false,"item-15":true,"item-16":false}')
    pg036q.write_text(qtext, encoding="utf-8")

# Chapter 1 revision exercise, Section B, which was present in the catalog but absent from HTML.
section_b_23 = '''
      <section class="mt-10 rounded-3xl border-2 border-sky-200 bg-white p-6 shadow-sm" aria-labelledby="section-b-23">
        <h2 id="section-b-23" data-id="pg023_n0018" class="text-2xl font-bold text-blue-900">Sehemu B:</h2>
        <p class="mt-3 text-lg"><span data-id="pg023_n0020">8.</span> <span data-id="pg023_n0021">Oanisha maneno yaliyoopo safu A na yale ya safu B kupata maana kamili.</span></p>
        <div class="mt-5 overflow-x-auto">
          <table class="w-full min-w-[680px] border-collapse text-left text-base" aria-label="Zoezi la kuoanisha maneno">
            <thead><tr class="bg-sky-100"><th class="border p-3" data-id="pg023_n0025">Na.</th><th class="border p-3" data-id="pg023_n0027">Safu A</th><th class="border p-3" data-id="pg023_n0029">Safu B</th></tr></thead>
            <tbody>
              <tr><td class="border p-3" data-id="pg023_n0032">i.</td><td class="border p-3" data-id="pg023_n0034">Ramani ya topografia</td><td class="border p-3" data-id="pg023_n0036">(a) juu ya karatasi, ardhi, kitambaa na kompyuta</td></tr>
              <tr><td class="border p-3" data-id="pg023_n0039">ii.</td><td class="border p-3" data-id="pg023_n0041">Fremu</td><td class="border p-3" data-id="pg023_n0043">(b) huwakilisha maumbo ya uso wa dunia</td></tr>
              <tr><td class="border p-3" data-id="pg023_n0046">iii.</td><td class="border p-3"><span data-id="pg023_n0049">Vipengele muhimu</span> <span data-id="pg023_n0050">katika ramani</span></td><td class="border p-3"><span data-id="pg023_n0053">(c) uhusiano wa umbali uliowasilishwa</span> <span data-id="pg023_n0054">katika ramani na umbali halisi uliopo</span> <span data-id="pg023_n0055">katika ardhi</span></td></tr>
              <tr><td class="border p-3" data-id="pg023_n0058">iv.</td><td class="border p-3" data-id="pg023_n0060">Skeli</td><td class="border p-3"><span data-id="pg023_n0063">(d) skeli, fremu, uelekeo wa Kaskazini,</span> <span data-id="pg023_n0064">kichwa cha ramani, ufunguo, chanzo</span> <span data-id="pg023_n0065">na mistari ya gridi</span></td></tr>
              <tr><td class="border p-3" data-id="pg023_n0068">v.</td><td class="border p-3"><span data-id="pg023_n0071">Sehemu ambapo</span> <span data-id="pg023_n0072">ramani inaweza</span> <span data-id="pg023_n0073">kuchorwa</span></td><td class="border p-3"><span data-id="pg023_n0075">(e) kuwasilisha mpaka wa ramani husika</span><br><span data-id="pg023_n0080">(f) isomeke kwa urahisi kwa watumiaji wa ramani husika</span></td></tr>
            </tbody>
          </table>
        </div>
      </section>
'''
insert_before(ROOT / "pg023_sec001.html", "  </section>\n</div>", section_b_23, 'id="section-b-23"')

# Chapter 4 revision exercise, missing question 6 / Section B.
section_b_88 = '''
      <section class="mt-10 rounded-3xl border-2 border-emerald-200 bg-white p-6 shadow-sm" aria-labelledby="section-b-88">
        <h2 id="section-b-88" data-id="pg088_n0044" class="text-2xl font-bold text-emerald-900">B. Maswali ya kuoanisha</h2>
        <p class="mt-3 text-lg"><span data-id="pg088_n0046">6.</span> <span data-id="pg088_n0047">Oanisha maneno yaliyopo katika safu A na yale ya safu B kupata maana kamili</span></p>
        <figure class="mt-5">
          <img src="images/pg088_im010.png" data-id="pg088_im010" class="mx-auto h-auto max-w-full" alt="Jedwali la kuoanisha maana kamili lenye safu Na., Safu A na Safu B.">
          <figcaption class="sr-only">Jedwali la kuoanisha maana kamili lenye safu Na., Safu A na Safu B.</figcaption>
        </figure>
      </section>
'''
insert_before(ROOT / "pg088_sec001.html", "  </section>\n</div>", section_b_88, 'id="section-b-88"')

# Replace the inaccessible image-only first question on page 87 with real text.
pg087 = ROOT / "pg087_sec001.html"
p87 = pg087.read_text(encoding="utf-8")
if 'data-id="pg087_n0006"' not in p87:
    start = p87.index('        <div class="flex justify-center">')
    end = p87.index('        <div class="space-y-3">', start)
    header = '''        <div class="mb-6 rounded-2xl bg-blue-50 p-5 text-left">
          <h1 data-id="pg087_n0002" class="text-3xl font-bold text-blue-900">Zoezi la marudio</h1>
          <h2 data-id="pg087_n0004" class="mt-2 text-xl font-semibold">A: Chagua herufi ya jibu sahihi</h2>
          <p class="mt-4 text-lg"><span data-id="pg087_n0005">1.</span> <span data-id="pg087_n0006">Mambo muhimu ya kuzingatia ili kubaini usahihi wa mipaka ya kiutawala ya eneo katika ramani ni pamoja na [[blank:item-1]].</span></p>
        </div>
'''
    p87 = p87[:start] + header + p87[end:]
    option_ids = [("pg087_n0008", "(a) kutumia ramani yenye taarifa nyingi"),
                  ("pg087_n0010", "(b) kutumia ramani yenye chanzo cha taarifa za kuaminika"),
                  ("pg087_n0012", "(c) kutumia ramani yenye rangi zinazokubalika"),
                  ("pg087_n0014", "(d) kutumia ramani yenye kuwasilisha mwinuko")]
    for item, (key, value) in enumerate(option_ids, start=1):
        needle = f'<input type="radio" name="question-group-1" value="item-{item}"'
        pos = p87.index(needle)
        close = p87.index('>', pos) + 1
        p87 = p87[:close] + f'\n              <span class="text-gray-700" data-id="{key}">{value}</span>' + p87[close:]
    pg087.write_text(p87, encoding="utf-8")

print("inserted adapted and missing report content")
