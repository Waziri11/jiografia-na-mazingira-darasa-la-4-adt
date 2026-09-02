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
    data["pg087_n0006"] = "Mambo muhimu ya kuzingatia ili kubaini usahihi wa mipaka ya kiutawala ya eneo katika ramani ni pamoja na ______."
    data["pg061_n0005"] = "Vilevile, tunaweza kubaini uelekeo na mahali kwa kutumia ramani za kidijitali na GPS (Ji-Pi-Es)."
    data["pg061_n0006"] = "GPS (Ji-Pi-Es) hutumika kubaini mahali ulipo, wakati ramani ya kidijitali huwasilisha sehemu mbalimbali pamoja na pale unapotaka kwenda."
    data["pg061_n0007"] = "Baada ya kubaini mahali ulipo na unakokwenda, GPS (Ji-Pi-Es) hukokotoa na kuwasilisha umbali na uelekeo wa kufuata."
    data["pg061_n0008"] = "Ramani za kidijitali na GPS (Ji-Pi-Es) zinapatikana katika vifaa vya kielektroniki kama vile, simujanja, tableti na kompyuta."
    data["pg066_n0007"] = "= Sentimeta laki mbili na elfu hamsini (250 000)"
    data["pg066_n0009"] = "Ikiwa kilometa 1 = sentimeta laki moja (100 000), umbali halisi kwenye ardhi unaweza kubadilishwa kutoka sentimeta kwenda kilometa kama ifuatavyo:"
    data["pg066_n0011"] = "(Umbali kwenye ardhi katika Sentimeta / Sentimeta laki moja) × Kilometa 1"
    data["pg066_n0012"] = "= Sentimeta laki mbili na elfu hamsini × Kilometa 1 / Sentimeta laki moja"
    data["pg085_n0076"] = "Mwandishi: Taasisi ya Elimu Tanzania (TET)"
    data["pg095_n0068"] = "Chanzo: Ofisi ya Takwimu Tanzania (2019)"
    data["pg095_n0069"] = "Mwandishi: Taasisi ya Elimu Tanzania (TET)"
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
          <span class="sr-only" data-id="pg088_im010"></span>
          <img src="images/pg088_im010.png" data-id="pg088_im010" class="mx-auto h-auto max-w-full" alt="Jedwali la kuoanisha maana kamili lenye safu Na., Safu A na Safu B.">
          <figcaption class="sr-only">Jedwali la kuoanisha maana kamili lenye safu Na., Safu A na Safu B.</figcaption>
        </figure>
      </section>
'''
insert_before(ROOT / "pg088_sec001.html", "  </section>\n</div>", section_b_88, 'id="section-b-88"')

# Chapter 3 vocabulary block, present in the catalogs but omitted from HTML.
glossary_58 = '''<section class="mt-10 rounded-2xl border border-blue-200 bg-blue-50 p-6" aria-labelledby="pg058-glossary">
  <h2 id="pg058-glossary" data-id="pg058_n0034" class="mb-5 text-3xl font-bold text-blue-900">Msamiati</h2>
  <dl class="grid gap-4">
    <div><dt data-id="pg058_n0036" class="font-bold">Kiolesura</dt><dd data-id="pg058_n0037">Sura ya programu fulani katika kompyuta</dd></div>
    <div><dt data-id="pg058_n0039" class="font-bold">Kipanya</dt><dd data-id="pg058_n0040">Kifaa cha kompyuta chenye vitufe viwili vya kubofya kulia na kushoto, kinachofanya kazi kwa kutumia alama ya mshale au kiganja, kung’amua na kufungua taarifa mbalimbali ndani ya kompyuta.</dd></div>
    <div><dt data-id="pg058_n0042" class="font-bold">Kivinjari</dt><dd data-id="pg058_n0043">Programu tumizi inayomuwezesha mtumiaji kusoma na kuunganishwa na taarifa zingine zilizomo ndani ya wavuti kuu.</dd></div>
    <div><dt data-id="pg058_n0045" class="font-bold">Wavuti</dt><dd data-id="pg058_n0046">Mtandao wa mawasiliano ya kompyuta wenye taarifa mbalimbali za kimataifa.</dd></div>
  </dl>
</section>'''
insert_before(ROOT / "pg058_sec002.html", "</div></main>", glossary_58, 'id="pg058-glossary"')

# Complete questions 3–5 of Chapter 4, Exercise 1 (continued from question 2).
questions_3_5 = '''<div class="mt-8 space-y-7" aria-label="Maswali ya 3 hadi 5">
  <div><p class="text-xl">3. Iwapo unaona doti nyingi zilizokaribiana kwenye ramani, inamaanisha nini?</p><div class="ml-8 mt-2 space-y-1"><p>(a) Kuna watu wachache</p><p>(b) Kuna watu wengi</p><p>(c) Kuna miti mingi</p><p>(d) Kuna maji mengi</p></div></div>
  <div><p class="text-xl">4. Doti zilizotawanyika kwenye ramani zinaashiria nini?</p><div class="ml-8 mt-2 space-y-1"><p>(a) Kuna watu wengi</p><p>(b) Kuna watu wachache</p><p>(c) Kuna magari mengi</p><p>(d) Kuna shule nyingi</p></div></div>
  <div><p class="text-xl">5. Ni njia ipi kati ya zifuatazo inaweza kukusaidia kubaini mtawanyiko wa watu na vitu?</p><div class="ml-8 mt-2 space-y-1"><p>(a) Kitabu cha hadithi</p><p>(b) Redio</p><p>(c) Mifumo ya Taarifa za Kijiografia (GIS)</p><p>(d) Saa ya mkononi</p></div></div>
</div>'''
insert_before(ROOT / "pg086_sec002.html", "</section>", questions_3_5, 'aria-label="Maswali ya 3 hadi 5"')

# Place Activity 7's response field after its subparts, not before them.
pg089 = ROOT / "pg089_sec001.html"
p89 = pg089.read_text(encoding="utf-8")
q7_field = '<textarea class="mt-3 mb-5 min-h-24 w-full resize-y rounded-lg border border-gray-400 bg-white p-3 text-base" data-aria-id="aria-pg089_sec001-1" aria-label="Jibu la swali la 1" tabindex="0"></textarea>'
if q7_field in p89:
    p89 = p89.replace(q7_field, "", 1)
    q7_end = '<div class="mb-4 pl-12 text-[1.05rem] leading-relaxed max-lg:pl-8 max-lg:text-base max-sm:pl-5 max-sm:text-sm"><span data-id="pg089_n0012">(c)Bonde.</span></div>'
    p89 = p89.replace(q7_end, q7_end + q7_field.replace('Jibu la swali la 1', 'Jibu la swali la 7 na vipengele vyake'), 1)
    pg089.write_text(p89, encoding="utf-8")

# Add the standard activity character where the report identified omissions.
for filename, heading_id in (("pg060_sec001.html", "pg060_n0005"), ("pg070_sec001.html", "pg070_n0006")):
    path = ROOT / filename
    html = path.read_text(encoding="utf-8")
    guard = f'data-report-icon-for="{heading_id}"'
    if guard not in html:
        needle = f'<div class="inline-block' if filename.startswith("pg060") else '<div class="bg-gradient-to-r'
        icon = f'<img src="images/pg045_activity_icon.png" alt="" aria-hidden="true" data-report-icon-for="{heading_id}" class="mb-3 h-20 w-20 rounded-full bg-white object-contain shadow-md">'
        html = html.replace(needle, icon + needle, 1)
        path.write_text(html, encoding="utf-8")

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
