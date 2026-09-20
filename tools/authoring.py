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


def add(track, subject_id, questions):
    """إلحاق أسئلة بمادة قائمة، مع رفض المكرر بنص السؤال."""
    path = os.path.join(CONTENT, track, subject_id + ".json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    known = {q["stem"] for q in data["questions"]}
    branches = {b["name"] for b in data["branches"]}
    added, dupes, unknown = 0, [], []
    for q in questions:
        if q["stem"] in known:
            dupes.append(q["stem"][:45])
            continue
        if q["branch"] not in branches:
            unknown.append(q["branch"])
            continue
        data["questions"].append(q)
        known.add(q["stem"])
        added += 1
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    from collections import Counter
    counts = Counter(q["branch"] for q in data["questions"])
    print(f'{data["name"]}: +{added} → {len(data["questions"])} سؤالًا')
    for name, n in counts.items():
        print(f"    {name}: {n}")
    if dupes:
        print("    مكرر مرفوض:", dupes)
    if unknown:
        print("    فرع غير معروف:", set(unknown))


def q(stem, options, correct, explanation, difficulty, branch):
    return {"stem": stem, "options": options, "correct": correct,
            "explanation": explanation, "difficulty": difficulty, "branch": branch}
