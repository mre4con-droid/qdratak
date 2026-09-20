# -*- coding: utf-8 -*-
"""مولّد صفحات مسار التحصيلي.

يقرأ المحتوى من content/tahsili/ ويولّد صفحات ثابتة تحت /tahsili/ بنفس
قوالب مسار القدرات (tools/chrome.py)، فيبقى المساران متطابقين في الشكل.

  python3 tools/build_tahsili.py
"""
import hashlib
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chrome  # noqa: E402
import entitlement  # noqa: E402

ROOT = chrome.ROOT
CONTENT = os.path.join(ROOT, "content", "tahsili")
OUT = os.path.join(ROOT, "tahsili")
SITE = "https://qdratak.com"

AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"


def ar(n):
    """تحويل الأرقام اللاتينية إلى عربية."""
    return str(n).translate(str.maketrans("0123456789", AR_DIGITS))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def shuffle_options(questions):
    """خلط خيارات كل سؤال خلطًا حتميًا (مشتقًا من نص السؤال).

    الأسئلة تُكتب عادة والإجابة الصحيحة أولًا، وهذا نمط يكشف الإجابة.
    الخلط مشتق من بصمة النص فيبقى ثابتًا بين عمليات البناء.
    """
    out = []
    for q in questions:
        seed = int(hashlib.sha1(q["stem"].encode("utf-8")).hexdigest()[:8], 16)
        order = list(range(len(q["options"])))
        random.Random(seed).shuffle(order)
        item = dict(q)
        item["options"] = [q["options"][i] for i in order]
        item["correct"] = order.index(q["correct"])
        out.append(item)
    return out


def load_blueprint():
    with open(os.path.join(CONTENT, "blueprint.json"), encoding="utf-8") as fh:
        return json.load(fh)


def load_subject(track, subject_id):
    path = os.path.join(CONTENT, track, subject_id + ".json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- قطع مشتركة

def head(title, desc, canonical, extra_css=""):
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="canonical" href="{canonical}">
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_SA">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>{chrome.course_css()}{extra_css}</style>
</head>
<body>
"""


def nav(home="/tahsili/", label="التحصيلي"):
    """ترويسة مكتفية بذاتها.

    أبعاد الشعار مكتوبة في السطر لا في ورقة الأنماط: قاعدة `.brand-mark img`
    موجودة في أنماط الدورات وبنك الأسئلة وغائبة عن أنماط المحاكي، فالاعتماد
    عليها يجعل الشعار يظهر بحجمه الطبيعي في بعض الصفحات دون بعض.
    """
    a, b = chrome.logos()
    return f"""
<nav>
  <div class="wrap nav-row">
    <a class="brand-mark" href="/" style="text-decoration:none; margin-bottom:0;" aria-label="قدراتك — الصفحة الرئيسية">
      <img src="{a}" alt="قدراتك" style="height:24px; width:auto; display:block;">
      <img src="{b}" alt="قدراتك" style="height:30px; width:auto; display:block; margin-inline-start:4px;">
    </a>
    <a class="home-link" href="{home}">🏠 {label}</a>
  </div>
</nav>
"""


# ------------------------------------------------------------- صفحة الدورة

def lesson_html(branch, idx):
    """درس فرع واحد: ماذا ستتعلم، شكل السؤال، خطوات الحل، مثال محلول."""
    n = ar(idx)
    forms = "".join(f"<li>{f}</li>" for f in branch.get("forms", []))
    steps = "".join(f"<li>{s}</li>" for s in branch.get("steps", []))
    ex = branch.get("example") or {}
    opts = ""
    for o in ex.get("options", []):
        cls = "ok" if o.get("ok") else "bad"
        tag = '<span class="ls-tag">الإجابة</span>' if o.get("ok") else ""
        opts += (f'<div class="ls-opt {cls}">{o["text"]} {tag}'
                 f'<span class="ls-why">{o.get("why", "")}</span></div>')
    passage = f'<div class="ls-passage">{ex["passage"]}</div>' if ex.get("passage") else ""
    think = f'<div class="ls-think">{ex["think"]}</div>' if ex.get("think") else ""
    summary = (f'<div class="ls-part"><div class="ls-sum">الخلاصة: {branch["summary"]}</div></div>'
               if branch.get("summary") else "")
    target = "mc-list-" + branch["id"]
    return f"""
    <div class="branch-card">
      <h3 style="margin:0 0 6px; font-size:17px;"><span class="branch-num">{n}</span>{branch["name"]}</h3>
      <div class="ls">
        <div class="ls-part"><div class="ls-h"><i>🎯</i>ماذا ستتعلم في هذا الدرس؟</div>
          <p class="ls-intro">{branch["learn"]}</p></div>
        <div class="ls-part"><div class="ls-h"><i>📝</i>كيف يأتي السؤال في الاختبار؟</div>
          <ul class="ls-forms">{forms}</ul></div>
        <div class="ls-part"><div class="ls-h"><i>🧭</i>طريقة الحل خطوة بخطوة</div>
          <ol class="ls-steps">{steps}</ol></div>
        <div class="ls-part"><div class="ls-h"><i>✍️</i>مثال محلول بالتفكير بصوت عالٍ</div>
          {passage}<div class="ls-q">{ex.get("question", "")}</div>{think}{opts}</div>
        {summary}
        <button type="button" class="ls-go" onclick="var t=document.getElementById('{target}'); if(t){{t.scrollIntoView({{behavior:'smooth',block:'start'}});}}">جرّب الآن على التمارين ←</button>
      </div>
    </div>"""


def practice_block(bank_id, title, tag, note, count, intro):
    """قسم تدريب: عنوان، بطاقة قاعدة، حاوية أسئلة، أزرار تحقق."""
    rule = (f'<div class="rule-card"><p style="font-size:13.5px; color:var(--ink-soft); margin:0;">'
            f'{note}</p></div>') if note else ""
    return f"""
  <section class="block">
    <h2 id="{bank_id}-section" class="block-title"><span class="tag">{tag}</span> {title} ({ar(count)} سؤالًا)</h2>
    {rule}
    <div class="practice-card" style="margin-top:12px;">
      <p class="practice-intro">{intro}</p>
      <div id="mc-list-{bank_id}"></div>
      <div class="practice-actions">
        <button class="btn" onclick="checkBank('{bank_id}')">تحقق من الإجابات</button>
        <button class="btn btn-ghost" onclick="resetBank('{bank_id}')">إعادة المحاولة</button>
      </div>
      <p id="score-summary-{bank_id}" style="font-size:14px; font-weight:700; margin-top:12px;"></p>
    </div>
  </section>"""


COURSE_ENGINE = """
(function () {
  "use strict";
  var SKILL_ID = %(skill)s;
  var TRACK_ID = %(track)s;
  var BANKS = %(banks)s;

  /* AI-BRIDGE:START */
  // جسر للمساعد الذكي: يجد بيانات السؤال من نصه (ليعطي تلميحًا دقيقًا دون كشف الإجابة)
  window.aiCourseLookup = function (stemText) {
    var norm = function (h) {
      var d = document.createElement("div"); d.innerHTML = h || "";
      return (d.textContent || "").replace(/\\s+/g, " ").trim();
    };
    if (!window.__aiStemMap) {
      var map = {};
      Object.keys(BANKS).forEach(function (b) {
        BANKS[b].forEach(function (q) { map[norm(q.stem)] = q; });
      });
      window.__aiStemMap = map;
    }
    return window.__aiStemMap[norm(stemText)] || null;
  };
  /* AI-BRIDGE:END */

  function diagKey() {
    try {
      var pid = localStorage.getItem("qudurat_current_profile_id");
      return pid ? "tahsili_diagnostics__" + pid : "tahsili_diagnostics";
    } catch (e) { return "tahsili_diagnostics"; }
  }
  function loadDiag() {
    try { return JSON.parse(localStorage.getItem(diagKey()) || "{}"); }
    catch (e) { return {}; }
  }
  function saveDiag(d) {
    try { localStorage.setItem(diagKey(), JSON.stringify(d)); } catch (e) {}
  }
  function logAttempt(skillId, difficulty, correct) {
    var d = loadDiag();
    if (!d[skillId]) d[skillId] = { track: TRACK_ID, totalAttempts: 0, totalCorrect: 0, byDifficulty: {}, byBranch: {} };
    var s = d[skillId];
    s.track = TRACK_ID;
    s.totalAttempts++;
    if (correct) s.totalCorrect++;
    var dk = String(difficulty);
    if (!s.byDifficulty[dk]) s.byDifficulty[dk] = { correct: 0, total: 0 };
    s.byDifficulty[dk].total++;
    if (correct) s.byDifficulty[dk].correct++;
    saveDiag(d);
  }
  function logBranch(branch, correct) {
    var d = loadDiag();
    if (!d[SKILL_ID]) return;
    var bb = d[SKILL_ID].byBranch || (d[SKILL_ID].byBranch = {});
    if (!bb[branch]) bb[branch] = { correct: 0, total: 0 };
    bb[branch].total++;
    if (correct) bb[branch].correct++;
    saveDiag(d);
  }

  function toArabicDigits(n) {
    var map = ["٠","١","٢","٣","٤","٥","٦","٧","٨","٩"];
    return String(n).replace(/[0-9]/g, function (d) { return map[d]; });
  }

  var state = {};
  Object.keys(BANKS).forEach(function (b) {
    state[b] = { checked: false, sel: new Array(BANKS[b].length).fill(null) };
  });

  function render(bank) {
    var html = "";
    BANKS[bank].forEach(function (q, qi) {
      html += '<div class="mc-question" data-qi="' + qi + '">';
      html += '<div class="mc-stem">' + q.stem +
              '<span class="mc-diff-badge">' + q.branch + ' — صعوبة ' + toArabicDigits(q.difficulty) + '</span></div>';
      html += '<div class="mc-options">';
      q.options.forEach(function (opt, oi) {
        html += '<div class="mc-option" data-qi="' + qi + '" data-oi="' + oi +
                '" onclick="pickOption(\\'' + bank + '\\',' + qi + ',' + oi + ')">' + opt + '</div>';
      });
      html += '</div><div class="mc-feedback" id="fb-' + bank + '-' + qi + '"></div>';
      html += '<button type="button" class="report-btn" onclick="openReportModal(this)">🚩 أبلغ عن خطأ</button>';
      html += '</div>';
    });
    document.getElementById("mc-list-" + bank).innerHTML = html;
  }

  window.pickOption = function (bank, qi, oi) {
    if (state[bank].checked) return;
    state[bank].sel[qi] = oi;
    var opts = document.querySelectorAll('#mc-list-' + bank + ' .mc-option[data-qi="' + qi + '"]');
    Array.prototype.forEach.call(opts, function (el) {
      el.classList.toggle("selected", parseInt(el.getAttribute("data-oi"), 10) === oi);
    });
  };

  window.checkBank = function (bank) {
    if (window.tahsiliRequire && !window.tahsiliRequire()) return;
    var st = state[bank];
    st.checked = true;
    var correctCount = 0;
    BANKS[bank].forEach(function (q, qi) {
      var sel = st.sel[qi];
      var fb = document.getElementById("fb-" + bank + "-" + qi);
      var opts = document.querySelectorAll('#mc-list-' + bank + ' .mc-option[data-qi="' + qi + '"]');
      Array.prototype.forEach.call(opts, function (el) {
        var oi = parseInt(el.getAttribute("data-oi"), 10);
        if (oi === q.correct) el.classList.add("correct");
        else if (oi === sel) el.classList.add("wrong");
      });
      if (sel === null || sel === undefined) {
        fb.textContent = "لم تجب على هذا السؤال.";
        fb.style.color = "var(--ink-soft)";
        return;
      }
      var ok = sel === q.correct;
      if (ok) correctCount++;
      fb.innerHTML = ok
        ? "✓ إجابة صحيحة." + (q.explanation ? '<div class="course-explain">' + q.explanation + "</div>" : "")
        : "✗ الإجابة الصحيحة: " + q.options[q.correct] +
          (q.explanation ? '<div class="course-explain">' + q.explanation + "</div>" : "");
      fb.style.color = ok ? "var(--green)" : "var(--red)";
      logAttempt(SKILL_ID, q.difficulty, ok);
      logBranch(q.branch, ok);
    });
    document.getElementById("score-summary-" + bank).textContent =
      "نتيجتك: " + toArabicDigits(correctCount) + " من " + toArabicDigits(BANKS[bank].length);
  };

  window.resetBank = function (bank) {
    state[bank] = { checked: false, sel: new Array(BANKS[bank].length).fill(null) };
    document.getElementById("score-summary-" + bank).textContent = "";
    render(bank);
  };

  Object.keys(BANKS).forEach(render);
})();
"""


def assistant_for(subject_name):
    """وحدة المساعد الذكي معايَرة على اسم المادة."""
    mod = chrome.assistant_module()
    return re.sub(r'AI_SKILL_NAME = "[^"]*"',
                  'AI_SKILL_NAME = ' + json.dumps(subject_name, ensure_ascii=False),
                  mod, count=1)


def build_course(track_id, track, subject_meta, data):
    """صفحة دورة مادة واحدة."""
    sid, name = subject_meta["id"], subject_meta["name"]
    url = f"{SITE}/tahsili/courses/{sid}/"
    title = f'{data.get("title", "دورة " + name)} | قدراتك'
    desc = data.get("description", f"دورة {name} لاختبار التحصيلي: شرح، أمثلة محلولة، وتدريب.")

    branches = data.get("branches", [])
    overview = "".join(
        f'<div class="branch-overview-item"><span class="branch-num">{ar(i)}</span>'
        f'<span><b>{b["name"]}</b></span></div>'
        for i, b in enumerate(branches, 1))
    lessons = "".join(lesson_html(b, i) for i, b in enumerate(branches, 1))

    # بنوك التدريب: بنك شامل + بنك لكل فرع
    questions = shuffle_options(data.get("questions", []))
    banks = {"all": questions}
    sections = [practice_block(
        "all", "بنك الأسئلة الشامل", "تطبيق", "",
        len(questions), 'اكتب الحل على ورقة قبل الاختيار، ثم اضغط "تحقق من الإجابات".')]
    for b in branches:
        bq = [q for q in questions if q.get("branch") == b["name"]]
        if not bq:
            continue
        banks[b["id"]] = bq
        sections.append(practice_block(
            b["id"], f'وحدة مكثّفة: {b["name"]}', "تعمّق", b.get("note", ""),
            len(bq), "حل كل الأسئلة، وراقب أي نمط فرعي تتكرر فيه أخطاؤك."))

    engine = COURSE_ENGINE % {
        "skill": json.dumps(name, ensure_ascii=False),
        "track": json.dumps(track_id, ensure_ascii=False),
        "banks": json.dumps(banks, ensure_ascii=False),
    }

    n_of = f'({ar(subject_meta["index"])} من {ar(subject_meta["count"])} — {track["name"]})'
    html = head(title, desc, url) + nav() + f"""
<div class="wrap">

  <header class="path-header">
    <div class="eyebrow">
      <span>دورات التحصيلي {n_of}</span>
      <span class="sep">/</span>
      <span>{track["short"]}</span>
    </div>
    <h1>{data.get("title", "دورة " + name)}</h1>
    <p>{data.get("intro", desc)}</p>
  </header>

  <section class="block">
    <h2 class="block-title"><span class="tag">تعريف</span> ماذا تشمل مادة {name}؟</h2>
    <div class="rule-card">
      <p style="font-size:14px; color:var(--ink-soft); margin:0 0 10px;">{data.get("about", "")}</p>
      {'<div class="note-strip">💡 ' + data["tip"] + "</div>" if data.get("tip") else ""}
    </div>
    <div class="rule-card" style="margin-top:12px;">
      <h3 style="margin:0 0 8px; font-size:14px;">الفروع ({ar(len(branches))})</h3>
      {overview}
    </div>
  </section>

  <section class="block">
    <h2 class="block-title"><span class="tag">شرح تفصيلي</span> كل فرع بأمثلة محلولة</h2>
    {lessons}
  </section>
{"".join(sections)}
</div>

<script>{engine}</script>
<script>{chrome.report_script()}</script>
{entitlement.script()}
{assistant_for(name)}
</body>
</html>
"""
    write(os.path.join(OUT, "courses", sid, "index.html"), html)
    return len(questions)


def write(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)


# ------------------------------------------------------------------- البناء

def main():
    bp = load_blueprint()
    built, total_q = [], 0
    for track_id, track in bp["tracks"].items():
        subjects = track["subjects"]
        for i, meta in enumerate(subjects, 1):
            data = load_subject(track_id, meta["id"])
            if data is None:
                print(f"  — تخطٍّ: {track_id}/{meta['id']} (لا يوجد ملف محتوى بعد)")
                continue
            meta = dict(meta, index=i, count=len(subjects))
            n = build_course(track_id, track, meta, data)
            total_q += n
            built.append(f"{track_id}/{meta['id']}")
            print(f"  ✓ tahsili/courses/{meta['id']}/ — {ar(n)} سؤالًا")
    print(f"\nتم بناء {ar(len(built))} دورة، بإجمالي {ar(total_q)} سؤالًا.")


if __name__ == "__main__":
    main()


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
