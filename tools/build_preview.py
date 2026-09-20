# -*- coding: utf-8 -*-
"""تجهيز نسخة معاينة قابلة للنشر خارج نطاق الموقع.

الصفحات تستعمل مسارات مطلقة (/tahsili/ و/favicon.png …) تصلح لجذر النطاق
وحده. هذا السكربت ينسخ الموقع إلى مجلد مؤقت ويحوّل كل مرجع مطلق إلى مرجع
نسبي حسب عمق الملف، ويستثني صفحة الدفع لأنها تحمّل نموذج دفع حقيقي لا محل
له في معاينة.

  python3 tools/build_preview.py <مجلد الخرج>
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tahsili as bt  # noqa: E402

ROOT = bt.ROOT
# مجلدات المشروع لا تُنشر: مصدر المحتوى والأدوات وسجل git
SKIP_DIRS = {".git", "tools", "content", "__pycache__"}
# صفحة الدفع تُستثنى عمدًا من المعاينة
SKIP_FILES = {os.path.join("checkout", "index.html")}

# الجذور المعروفة التي تُحوَّل؛ ما عداها يُترك كما هو
ROOTS = ("tahsili", "simulator", "courses", "question-bank", "info",
         "legal", "checkout", "media", "favicon.png", "404.html")


def rel_prefix(depth):
    return "./" if depth == 0 else "../" * depth


def to_relative(path_value, depth):
    """يحوّل مسارًا مطلقًا إلى نسبي، ويضيف index.html لمسارات المجلدات."""
    frag = ""
    if "#" in path_value:
        path_value, frag = path_value.split("#", 1)
        frag = "#" + frag
    body = path_value.lstrip("/")
    if body == "":                       # الصفحة الرئيسية
        target = "index.html"
    elif body.endswith("/"):             # مجلد ← صفحته
        target = body + "index.html"
    else:
        target = body
    return rel_prefix(depth) + target + frag


def rewrite(html, depth):
    known = "|".join(re.escape(r) for r in ROOTS)
    # المراجع في الوسوم وفي نصوص JS على حد سواء
    pattern = re.compile(r'(["\'])(/(?:%s)?[^"\']*)\1' % known)

    def sub(m):
        quote, value = m.group(1), m.group(2)
        if value == "/":
            return quote + to_relative("/", depth) + quote
        body = value.lstrip("/").split("#")[0].split("/")[0]
        if body not in ROOTS:
            return m.group(0)            # ليس مسار موقع — يُترك
        return quote + to_relative(value, depth) + quote

    return pattern.sub(sub, html)


def main(out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    pages, assets = 0, 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            src = os.path.join(base, name)
            rel = os.path.relpath(src, ROOT)
            if rel in SKIP_FILES or rel.startswith("."):
                continue
            dst = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if name.endswith(".html"):
                depth = len(os.path.dirname(rel).split(os.sep)) if os.path.dirname(rel) else 0
                bt.write_text(dst, rewrite(bt.read_text(src), depth))
                pages += 1
            else:
                shutil.copy2(src, dst)
                assets += 1
    print(f"المعاينة: {bt.ar(pages)} صفحة و{bt.ar(assets)} ملفًا → {out_dir}")
    return out_dir


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/preview")
