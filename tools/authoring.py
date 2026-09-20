# -*- coding: utf-8 -*-
"""مساعدات تأليف محتوى مواد التحصيلي (تُستخدم من سكربتات التأليف)."""
import json
import os

CONTENT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "content", "tahsili")


def branch(bid, name, learn, forms, steps, example, summary, note):
    return {"id": bid, "name": name, "learn": learn, "forms": forms, "steps": steps,
            "example": example, "summary": summary, "note": note}


def example(question, think, options, passage=None):
    """options: قائمة (نص، صحيحة؟، تعليل)."""
    out = {"question": question, "think": think,
           "options": [{"text": t, "ok": ok, "why": why} for t, ok, why in options]}
    if passage:
        out["passage"] = passage
    return out


def save(track, subject):
    path = os.path.join(CONTENT, track, subject["id"] + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(subject, fh, ensure_ascii=False, indent=1)
    from collections import Counter
    counts = Counter(q["branch"] for q in subject["questions"])
    print(f"{subject['name']}: {len(subject['branches'])} فروع، "
          f"{len(subject['questions'])} سؤالًا {dict(counts)}")
