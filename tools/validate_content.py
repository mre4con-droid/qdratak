# -*- coding: utf-8 -*-
"""فحص سلامة محتوى التحصيلي قبل النشر: بنية الأسئلة، تغطية الفروع،
كفاية بنك كل مادة لحصتها، وصحة الروابط الداخلية المولَّدة."""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tahsili as bt  # noqa: E402

problems = []


def err(msg):
    problems.append(msg)


def check_subject(track_id, meta, data):
    where = f'{track_id}/{meta["id"]}'
    branch_names = {b["name"] for b in data.get("branches", [])}
    if not branch_names:
        err(f"{where}: لا توجد فروع")

    for b in data.get("branches", []):
        for key in ("id", "name", "learn", "forms", "steps", "example"):
            if not b.get(key):
                err(f'{where}/{b.get("name", "?")}: الحقل «{key}» ناقص')
        ex = b.get("example") or {}
        oks = [o for o in ex.get("options", []) if o.get("ok")]
        if len(oks) != 1:
            err(f'{where}/{b.get("name")}: المثال المحلول فيه {len(oks)} إجابة صحيحة بدل واحدة')

    stems = Counter()
    for i, q in enumerate(data.get("questions", [])):
        tag = f"{where}[{i}]"
        if len(q.get("options", [])) != 4:
            err(f'{tag}: عدد الخيارات {len(q.get("options", []))} بدل ٤')
        if not isinstance(q.get("correct"), int) or not 0 <= q["correct"] < len(q.get("options", [])):
            err(f"{tag}: قيمة correct خارج النطاق")
        if not q.get("explanation"):
            err(f"{tag}: لا يوجد شرح")
        if not 1 <= q.get("difficulty", 0) <= 5:
            err(f'{tag}: صعوبة غير صالحة ({q.get("difficulty")})')
        if q.get("branch") not in branch_names:
            err(f'{tag}: الفرع «{q.get("branch")}» غير معرّف في فروع المادة')
        if len(set(q.get("options", []))) != len(q.get("options", [])):
            err(f"{tag}: خيارات مكررة")
        stems[q.get("stem", "")] += 1

    for stem, n in stems.items():
        if n > 1:
            err(f"{where}: السؤال مكرر {n} مرات — {stem[:50]}")

    # كل فرع يجب أن يحمل أسئلة، وإلا ظهر في الشرح وغاب عن التدريب
    used = {q.get("branch") for q in data.get("questions", [])}
    for name in branch_names - used:
        err(f"{where}: الفرع «{name}» بلا أسئلة")

    quota = meta.get("questions", 0)
    have = len(data.get("questions", []))
    if have < quota:
        err(f"{where}: البنك {have} سؤالًا وحصته في المخطط {quota} — "
            f"سيستكمل المحاكي من مواد أخرى وينحرف التوزيع")


def check_links():
    """كل رابط داخلي في صفحات التحصيلي يجب أن يشير إلى ملف موجود."""
    for root, _dirs, files in os.walk(bt.OUT):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(root, name)
            html = bt.read_text(path)
            rel = os.path.relpath(path, bt.ROOT)
            for href in set(re.findall(r'href="(/[^"#?]*)"', html)):
                target = os.path.join(bt.ROOT, href.lstrip("/"))
                if href.endswith("/"):
                    target = os.path.join(target, "index.html")
                if not os.path.exists(target):
                    err(f"{rel}: رابط مكسور → {href}")


def main():
    bp = bt.load_blueprint()
    total = 0
    for track_id, track in bp["tracks"].items():
        for meta in track["subjects"]:
            data = bt.load_subject(track_id, meta["id"])
            if data is None:
                err(f'{track_id}/{meta["id"]}: لا يوجد ملف محتوى')
                continue
            check_subject(track_id, meta, data)
            total += len(data.get("questions", []))
    check_links()

    if problems:
        print(f"وُجدت {bt.ar(len(problems))} مشكلة:\n")
        for p in problems:
            print("  ✗", p)
        return 1
    print(f"سليم: {bt.ar(total)} سؤالًا، ولا روابط مكسورة.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
