# -*- coding: utf-8 -*-
"""بناء القائمة العلوية وقسمَي المسارين وقسم التواصل في الصفحة الرئيسية.

القائمة وأقسامها تُولَّد من تعريف واحد هنا، فترتيب القائمة وترتيب الأقسام في
الصفحة يبقيان متطابقين بلا متابعة يدوية. العملية غير تراكمية.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tahsili as bt  # noqa: E402

ROOT = bt.ROOT
INDEX = os.path.join(ROOT, "index.html")

NAV_BEGIN, NAV_END = "<!-- NAV:BEGIN -->", "<!-- NAV:END -->"
QUD_BEGIN, QUD_END = "<!-- QUDURAT-SECTION:BEGIN -->", "<!-- QUDURAT-SECTION:END -->"
CON_BEGIN, CON_END = "<!-- CONTACT-SECTION:BEGIN -->", "<!-- CONTACT-SECTION:END -->"

NAV_ITEMS = [
    ("#qudurat", "قسم القدرات"),
    ("#tahsili", "قسم التحصيلي"),
    ("#courses", "الدورات المهارية"),
    ("/question-bank/", "بنك الأسئلة"),
    ("#pricing", "الأسعار"),
    ("#contact", "تواصل معنا"),
]

# بيانات التواصل — تُستبدل بالمعتمدة عند وصولها
CONTACT_EMAIL = "qdratak@gmail.com"
SOCIALS = [
    ("https://x.com/qdratak", "إكس"),
    ("https://instagram.com/qdratak", "إنستغرام"),
    ("https://snapchat.com/add/qdratak", "سناب شات"),
    ("https://tiktok.com/@qdratak", "تيك توك"),
    ("https://www.youtube.com/@%D9%85%D9%86%D8%B5%D8%A9%D9%82%D8%AF%D8%B1%D8%A7%D8%AA%D9%83", "يوتيوب"),
]

TILE = ('style="text-decoration:none; background:rgba(255,255,255,0.12); '
        'border:1px solid rgba(255,255,255,0.3); border-radius:8px; padding:12px; '
        'color:#fff; font-size:13.5px; font-weight:700; text-align:center;"')


def nav_block():
    links = "".join(f'      <a href="{href}">{label}</a>\n' for href, label in NAV_ITEMS)
    return "\n" + links + "    "


QUDURAT_SECTION = f"""
<!-- flex-wrap:nowrap لازم: .try-banner فيها flex-wrap:wrap، ومع flex-direction:column تلتفّ العناصر في أعمدة فتتمدد رأسيًا -->
<section id="qudurat">
  <div class="wrap">
    <div class="try-banner" style="background: var(--teal); flex-direction:column; align-items:stretch; flex-wrap:nowrap;">
      <div>
        <h2>قسم القدرات: محاكي وبنك أسئلة وثماني دورات</h2>
        <p>كل ما تحتاجه لاختبار القدرات العامة في مكان واحد — محاكي موقوت بـ١٢٠ سؤالًا
           يشخّص أضعف مهاراتك، وبنك أسئلة للتدريب الحر، ودورة كاملة لكل مهارة من
           المهارات الرسمية الثماني، ومعك المساعد الذكي تحت كل سؤال.</p>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:18px;">
        <a href="/simulator/" {TILE}>محاكي الاختبار<br><span style="font-weight:400; font-size:12px;">١٢٠ سؤالًا بتوقيت حقيقي</span></a>
        <a href="/question-bank/" {TILE}>بنك الأسئلة<br><span style="font-weight:400; font-size:12px;">تدريب حر بلا مؤقّت</span></a>
      </div>
      <a class="btn btn-gold" href="/simulator/" style="text-decoration:none; margin-top:18px; align-self:center;">ابدأ محاكي القدرات</a>
    </div>
  </div>
</section>
"""


def contact_section():
    socials = "".join(
        f'        <a href="{url}" target="_blank" rel="noopener" {TILE}>{name}</a>\n'
        for url, name in SOCIALS)
    return f"""
<section id="contact">
  <div class="wrap">
    <div class="try-banner" style="background: var(--ink); flex-direction:column; align-items:stretch; flex-wrap:nowrap;">
      <div>
        <h2>تواصل معنا</h2>
        <p>عندك سؤال عن الاشتراك أو ملاحظة على سؤال في المنصة؟ راسلنا على البريد،
           أو تابعنا على حساباتنا وأرسل لنا رسالة مباشرة.</p>
      </div>
      <a class="btn btn-gold" href="mailto:{CONTACT_EMAIL}" style="text-decoration:none; margin-top:14px; align-self:center; direction:ltr;">{CONTACT_EMAIL}</a>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(120px, 1fr)); gap:10px; margin-top:18px;">
{socials}      </div>
    </div>
  </div>
</section>
"""


def extract_section(html, sid):
    """يقتطع وسم <section id="sid"> كاملًا مع مراعاة التداخل، ويعيد (الباقي، الكتلة)."""
    start = html.find(f'<section id="{sid}"')
    if start < 0:
        raise RuntimeError(f"القسم {sid} غير موجود")
    depth, i = 0, start
    while i < len(html):
        nxt_open = html.find("<section", i)
        nxt_close = html.find("</section>", i)
        if nxt_close < 0:
            raise RuntimeError(f"القسم {sid} غير مغلق")
        if 0 <= nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 8
        else:
            depth -= 1
            i = nxt_close + 10
            if depth == 0:
                return html[:start] + html[i:], html[start:i]
    raise RuntimeError(f"تعذّر اقتطاع القسم {sid}")


def ensure_order(html, sid, before):
    """يضمن ورود القسم sid قبل القسم before؛ لا يفعل شيئًا إن كان كذلك أصلًا."""
    a, b = html.find(f'<section id="{sid}"'), html.find(f'<section id="{before}"')
    if a < 0 or b < 0 or a < b:
        return html
    rest, block = extract_section(html, sid)
    target = rest.find(f'<section id="{before}"')
    return rest[:target] + block.strip() + "\n\n" + rest[target:]


def replace_between(text, begin, end, body, what):
    i, j = text.find(begin), text.find(end)
    if i < 0 or j < 0:
        raise RuntimeError(f"علامات {what} غير موجودة")
    return text[:i + len(begin)] + body + text[j:]


def main():
    html = bt.read_text(INDEX)

    # ---- القائمة العلوية
    if NAV_BEGIN not in html:
        m = re.search(r'(<div class="nav-links">)(.*?)(\n    </div>)', html, re.S)
        if not m:
            raise RuntimeError("تعذّر العثور على القائمة العلوية")
        html = (html[:m.end(1)] + "\n" + NAV_BEGIN + m.group(2) + NAV_END + m.group(3)
                + html[m.end(3):])
    html = replace_between(html, NAV_BEGIN, NAV_END, nav_block(), "القائمة")

    # ---- ترتيب الأقسام يتبع ترتيب القائمة، وإلا قفز النزول في القائمة للخلف.
    # قسم القدرات يُنتزع أولًا ثم يُعاد إدراجه، وإلا بقيت علاماته مكانها عند نقل
    # قسم التحصيلي فانفصل القسمان.
    i, j = html.find(QUD_BEGIN), html.find(QUD_END)
    if i >= 0 and j >= 0:
        # تُطبَّع الأسطر الفارغة على الجانبين، وإلا تراكم سطر مع كل إعادة بناء
        html = html[:i].rstrip("\n") + "\n\n" + html[j + len(QUD_END):].lstrip("\n")
    html = ensure_order(html, "tahsili", "courses")

    # ---- قسم القدرات، قبل قسم التحصيلي مباشرة ليتجاور المساران
    anchor = '<section id="tahsili">'
    if anchor not in html:
        raise RuntimeError("قسم التحصيلي غير موجود")
    html = html.replace(anchor, QUD_BEGIN + QUD_END + "\n" + anchor, 1)
    html = replace_between(html, QUD_BEGIN, QUD_END, QUDURAT_SECTION, "قسم القدرات")

    # ---- قسم التواصل، بعد آخر قسم وقبل التذييل
    if CON_BEGIN not in html:
        anchor = "<footer>"
        if anchor not in html:
            raise RuntimeError("التذييل غير موجود")
        html = html.replace(anchor, CON_BEGIN + CON_END + "\n\n" + anchor, 1)
    html = replace_between(html, CON_BEGIN, CON_END, contact_section(), "قسم التواصل")

    bt.write_text(INDEX, html)
    print("  ✓ index.html: القائمة (%s بنود) وقسم القدرات وقسم التواصل"
          % bt.ar(len(NAV_ITEMS)))


if __name__ == "__main__":
    main()
