# -*- coding: utf-8 -*-
"""نشر كتالوج الباقات من content/plans.json إلى المواضع التي تستهلكه.

الكتالوج كان مكررًا في خمسة مواضع (قسم الأسعار، قائمة صفحة الدفع، أسماء
الباقات فيها، قائمة الباقات المسموحة، ومدد الاشتراك في المحاكي)، فإضافة باقة
كانت تعني خمسة تعديلات متفرقة يسهل أن يتخلّف أحدها. هذا السكربت يولّدها كلها
من ملف واحد، ويُعاد تشغيله بلا أثر تراكمي.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tahsili as bt  # noqa: E402

ROOT = bt.ROOT
BEGIN = "<!-- PLANS:BEGIN -->"
END = "<!-- PLANS:END -->"
JS_BEGIN = "/* PLANS:BEGIN */"
JS_END = "/* PLANS:END */"


def load_plans():
    with open(os.path.join(ROOT, "content", "plans.json"), encoding="utf-8") as fh:
        return json.load(fh)["plans"]


def replace_between(text, begin, end, body, where):
    i, j = text.find(begin), text.find(end)
    if i < 0 or j < 0:
        raise RuntimeError(f"علامات الكتالوج غير موجودة في {where}")
    return text[:i + len(begin)] + body + text[j:]


# ------------------------------------------------------- قسم الأسعار

def pricing_cards(plans):
    out = "\n"
    for p in plans:
        featured = " featured" if p.get("featured") else ""
        badge = f'\n        <span class="tag">{p["badge"]}</span>' if p.get("badge") else ""
        items = "".join(f"\n          <li>{f}</li>" for f in p["features"])
        btn = "btn-gold" if p.get("featured") else "btn-ghost"
        out += f"""      <div class="price-card{featured}">{badge}
        <h3>{p["label"]}</h3>
        <div class="price">{bt.ar(p["price"])} <span>ريال</span></div>
        <div class="price-note">{p["note"]}</div>
        <ul>{items}
        </ul>
        <button class="btn {btn} btn-block" onclick="goSubscribe('{p["id"]}')">{p["cta"]}</button>
      </div>
"""
    return out


def patch_index(plans):
    path = os.path.join(ROOT, "index.html")
    html = bt.read_text(path)
    if BEGIN not in html:
        # أول تشغيل: نحصر شبكة البطاقات القائمة بين العلامتين
        m = re.search(r'(<div class="price-grid">)(.*?)(\n    </div>)', html, re.S)
        if not m:
            raise RuntimeError("تعذّر العثور على شبكة الأسعار في index.html")
        html = (html[:m.end(1)] + "\n" + BEGIN + m.group(2) + END + m.group(3)
                + html[m.end(3):])
    html = replace_between(html, BEGIN, END, pricing_cards(plans), "index.html")
    bt.write_text(path, html)
    print("  ✓ index.html: قسم الأسعار")


# --------------------------------------------------------- صفحة الدفع

def patch_checkout(plans):
    path = os.path.join(ROOT, "checkout", "index.html")
    html = bt.read_text(path)

    # تمييز العدد منصوب فيما فوق الصفر، كما في الصياغة الأصلية للصفحة
    def riyal(price):
        return "ريال" if price == 0 else "ريالًا"

    options = "\n" + "".join(
        f'        <option value="{p["id"]}"{" selected" if p["id"] == "69" else ""}>'
        f'{p["label"]} — {bt.ar(p["price"])} {riyal(p["price"])}</option>\n'
        for p in plans) + "      "
    if BEGIN not in html:
        m = re.search(r'(<select id="plan-select">)(.*?)(</select>)', html, re.S)
        if not m:
            raise RuntimeError("تعذّر العثور على قائمة الباقات في صفحة الدفع")
        html = (html[:m.end(1)] + "\n" + BEGIN + m.group(2) + END + m.group(3)
                + html[m.end(3):])
    html = replace_between(html, BEGIN, END, options, "checkout")

    names = ", ".join(f'"{p["id"]}": "{p["short"]}"' for p in plans)
    allowed = ", ".join(f'"{p["id"]}"' for p in plans)
    if JS_BEGIN not in html:
        m = re.search(r"(  var planNames = \{)(.*?)(\};\n)", html, re.S)
        if not m:
            raise RuntimeError("تعذّر العثور على planNames في صفحة الدفع")
        html = html[:m.start()] + JS_BEGIN + "\n" + m.group(0) + JS_END + "\n" + html[m.end():]
    html = replace_between(
        html, JS_BEGIN, JS_END,
        "\n  var planNames = { %s };\n  var PLAN_IDS = [%s];\n" % (names, allowed),
        "checkout")
    # قائمة السماح تقرأ من PLAN_IDS بدل مصفوفة مكتوبة يدويًا
    html = re.sub(r'\["0", "69", "99", "120"\]\.indexOf\(plan\)', "PLAN_IDS.indexOf(plan)", html)

    bt.write_text(path, html)
    print("  ✓ checkout/: القائمة وأسماء الباقات وقائمة السماح")


# ------------------------------------------------------------ المحاكي

def patch_simulator(plans):
    path = os.path.join(ROOT, "simulator", "index.html")
    html = bt.read_text(path)
    durations = ", ".join(f'"{p["id"]}": {p["days"]}' for p in plans)
    labels = ", ".join(f'"{p["id"]}": "{p["label"]}"' for p in plans)
    tracks = ", ".join(f'"{p["id"]}": {json.dumps(p["tracks"])}' for p in plans)
    body = ("\n  var PLAN_DURATIONS = { %s };\n"
            "  var PLAN_LABELS = { %s };\n"
            "  // المسارات التي تفتحها كل باقة — تُقرأ من content/plans.json\n"
            "  var PLAN_TRACKS = { %s };\n" % (durations, labels, tracks))
    if JS_BEGIN not in html:
        m = re.search(r"(  var PLAN_DURATIONS = .*?\n)(  var PLAN_LABELS = .*?\n)", html, re.S)
        if not m:
            raise RuntimeError("تعذّر العثور على PLAN_DURATIONS في المحاكي")
        html = html[:m.start()] + JS_BEGIN + "\n" + m.group(0) + JS_END + "\n" + html[m.end():]
    html = replace_between(html, JS_BEGIN, JS_END, body, "simulator")
    bt.write_text(path, html)
    print("  ✓ simulator/: مدد الباقات ومسمياتها ومساراتها")


def main():
    plans = load_plans()
    patch_index(plans)
    patch_checkout(plans)
    patch_simulator(plans)
    print(f"\nنُشر {bt.ar(len(plans))} باقات من content/plans.json")


if __name__ == "__main__":
    main()
