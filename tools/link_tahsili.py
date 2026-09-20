# -*- coding: utf-8 -*-
"""ربط مسار التحصيلي من الموقع الرئيسي: قسم في الصفحة الرئيسية ومدخلات في
خريطة الموقع. القائمة العلوية يملكها tools/build_nav.py. العملية غير تراكمية."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tahsili as bt  # noqa: E402

ROOT = bt.ROOT
MARK = "<!-- TAHSILI-LINK -->"

BANNER = """
<section id="tahsili">%s
  <div class="wrap">
    <div class="try-banner" style="background: var(--ink); flex-direction:column; align-items:stretch; flex-wrap:nowrap;">
      <div>
        <h2>وتستعد للتحصيلي كمان؟ المسار جاهز</h2>
        <p>مسار كامل لاختبار التحصيل الدراسي بنفس أدوات القدرات: دورة لكل مادة فيها شرح
           وأمثلة محلولة وتدريب، ومحاكي اختبار موقوت يطابق التوزيع الرسمي، وبنك أسئلة للمراجعة الحرة.</p>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:18px;">
        <a href="/tahsili/#scientific" style="text-decoration:none; background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.3); border-radius:8px; padding:12px; color:#fff; font-size:13.5px; font-weight:700; text-align:center;">القسم العلمي<br><span style="font-weight:400; font-size:12px;">أحياء · كيمياء · فيزياء · رياضيات</span></a>
        <a href="/tahsili/#literary" style="text-decoration:none; background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.3); border-radius:8px; padding:12px; color:#fff; font-size:13.5px; font-weight:700; text-align:center;">القسم الأدبي<br><span style="font-weight:400; font-size:12px;">نحو · بلاغة · أدب · شرعية · اجتماعيات</span></a>
      </div>
      <a class="btn btn-gold" href="/tahsili/" style="text-decoration:none; margin-top:18px; align-self:center;">ادخل مسار التحصيلي</a>
    </div>
  </div>
</section>
""" % MARK


def patch_index():
    path = os.path.join(ROOT, "index.html")
    html = bt.read_text(path)
    if MARK in html:
        print("  — index.html: الربط موجود مسبقًا")
        return
    # قسم التحصيلي (القائمة يملكها tools/build_nav.py)
    close = '<!-- قسم آراء الطلاب'
    if close not in html:
        raise RuntimeError("تعذّر العثور على نهاية قسم الدورات في index.html")
    html = html.replace(close, BANNER + "\n" + close, 1)
    bt.write_text(path, html)
    print("  ✓ index.html: قسم التحصيلي")


def patch_sitemap(bp):
    path = os.path.join(ROOT, "sitemap.xml")
    xml = bt.read_text(path)
    urls = ["/tahsili/", "/tahsili/simulator/", "/tahsili/question-bank/"]
    for track in bp["tracks"].values():
        for meta in track["subjects"]:
            if os.path.exists(os.path.join(bt.OUT, "courses", meta["id"], "index.html")):
                urls.append(f'/tahsili/courses/{meta["id"]}/')
    lastmod = re.search(r"<lastmod>([\d-]+)</lastmod>", xml).group(1)
    added = [u for u in urls if f"<loc>{bt.SITE}{u}</loc>" not in xml]
    if not added:
        print("  — sitemap.xml: المدخلات موجودة مسبقًا")
        return
    rows = "".join(f"  <url><loc>{bt.SITE}{u}</loc><lastmod>{lastmod}</lastmod></url>\n"
                   for u in added)
    xml = xml.replace("</urlset>", rows + "</urlset>")
    bt.write_text(path, xml)
    print(f"  ✓ sitemap.xml: أُضيف {bt.ar(len(added))} رابطًا")


def main():
    patch_index()
    patch_sitemap(bt.load_blueprint())


if __name__ == "__main__":
    main()
