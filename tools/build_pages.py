# -*- coding: utf-8 -*-
"""مولّد صفحة التحصيلي الرئيسية وبنك أسئلته."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chrome  # noqa: E402
import build_tahsili as bt  # noqa: E402
import entitlement  # noqa: E402

SITE = bt.SITE


def footer(label):
    return (f'\n  <footer style="padding:30px 0 40px; text-align:center; font-size:12.5px; '
            f'color:var(--ink-soft);">\n'
            f'    <a href="/" style="color:var(--teal); font-weight:600;">قدراتك</a> — {label}\n'
            f'  </footer>\n')


# ------------------------------------------------------- صفحة التحصيلي الرئيسية

LANDING_CSS = """
  .track-block { scroll-margin-top: 20px; background: var(--paper); border: 1px solid var(--border); border-radius: 16px;
    padding: 20px; box-shadow: var(--shadow); margin-bottom: 16px; }
  .track-block h2 { margin: 0 0 4px; font-size: 21px; }
  .track-block .track-sub { font-size: 13.5px; color: var(--ink-soft); margin: 0 0 14px; }
  .subject-grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
  .subject-card { display: block; background: var(--bg); border: 1px solid var(--border);
    border-radius: 12px; padding: 14px; color: inherit; transition: border-color .15s, transform .15s; }
  .subject-card:hover { border-color: var(--teal); transform: translateY(-2px); }
  .subject-card b { display: block; font-size: 15.5px; margin-bottom: 4px; }
  .subject-card span { font-size: 12.5px; color: var(--ink-soft); }
  .cta-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
"""


def build_landing(bp, stats):
    blocks = ""
    for tid, track in bp["tracks"].items():
        cards = ""
        for meta in track["subjects"]:
            n = stats.get((tid, meta["id"]), 0)
            if not n:
                continue
            cards += (f'<a class="subject-card" href="/tahsili/courses/{meta["id"]}/">'
                      f'<b>{meta["name"]}</b>'
                      f'<span>{bt.ar(n)} سؤالًا مع الشرح والأمثلة</span></a>')
        blocks += f"""
    <div class="track-block" id="{tid}">
      <h2>{track["name"]}</h2>
      <p class="track-sub">{track["description"]}
         — {bt.ar(track["total_questions"])} سؤالًا في {bt.ar(track["duration_minutes"])} دقيقة.</p>
      <div class="subject-grid">{cards}</div>
    </div>"""

    total = sum(stats.values())
    html = bt.head(
        "التحصيلي — دورات ومحاكي اختبار التحصيل الدراسي | قدراتك",
        "مسار التحصيلي في منصة قدراتك: دورات مهارية لكل مادة في القسمين العلمي والأدبي، "
        "محاكي اختبار موقوت بالتوزيع الرسمي، وبنك أسئلة مع شرح لكل سؤال.",
        SITE + "/tahsili/",
        LANDING_CSS,
    ) + bt.nav("/", "الصفحة الرئيسية") + f"""
<div class="wrap">
  <header class="path-header">
    <div class="eyebrow"><span>مسار التحصيلي</span></div>
    <h1>استعد لاختبار التحصيل الدراسي</h1>
    <p>مسار كامل موازٍ لمسار القدرات: دورة لكل مادة فيها شرح مفصّل وأمثلة محلولة وتدريب،
       ومحاكي اختبار موقوت يطابق التوزيع الرسمي، وبنك أسئلة للمراجعة الحرة.
       {bt.ar(total)} سؤالًا حتى الآن في القسمين العلمي والأدبي.</p>
    <div class="cta-row">
      <a class="btn" href="/tahsili/simulator/">ابدأ محاكي الاختبار</a>
      <a class="btn btn-ghost" href="/tahsili/question-bank/">تصفّح بنك الأسئلة</a>
      <a class="btn btn-ghost" href="/">مسار القدرات</a>
    </div>
  </header>
{blocks}
</div>
{footer("التحصيلي")}
{entitlement.script()}
</body>
</html>
"""
    bt.write(os.path.join(bt.OUT, "index.html"), html)
    print("  ✓ tahsili/ — الصفحة الرئيسية")


# ----------------------------------------------------------- بنك أسئلة التحصيلي

BANK_ENGINE = r"""
(function () {
  "use strict";
  var DATA = %(data)s;
  var TRACKS = %(tracks)s;
  var current = { track: Object.keys(TRACKS)[0], subject: null, branch: null };

  function ar(n) { return String(n).replace(/[0-9]/g, function (d) { return "٠١٢٣٤٥٦٧٨٩"[d]; }); }
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
  function el(id) { return document.getElementById(id); }

  window.selectTrack = function (tid) {
    current = { track: tid, subject: null, branch: null };
    Object.keys(TRACKS).forEach(function (t) {
      el("tab-" + t).classList.toggle("active", t === tid);
    });
    renderSubjects();
    el("branch-area").style.display = "none";
    renderEmpty();
  };

  function renderSubjects() {
    el("skill-grid").innerHTML = TRACKS[current.track].subjects.map(function (s) {
      var d = DATA[current.track][s.id];
      if (!d) return "";
      var active = current.subject === s.id ? " active" : "";
      return '<button type="button" class="skill-card' + active + '" onclick="selectSubject(\'' + s.id + '\')">' +
        '<b>' + esc(s.name) + '</b>' +
        '<span>' + ar(d.branches.length) + ' فروع · ' + ar(d.count) + ' سؤالًا</span>' +
        '</button>';
    }).join("");
  }

  window.selectSubject = function (sid) {
    current.subject = sid;
    current.branch = null;
    renderSubjects();
    var d = DATA[current.track][sid];
    el("branch-area").style.display = "";
    el("branch-area-title").textContent = "اختر فرعًا من " + d.name;
    el("branch-pills").innerHTML = d.branches.map(function (b) {
      return '<button type="button" class="branch-pill" onclick="selectBranch(\'' + b.id + '\')">' +
        esc(b.name) + ' (' + ar(b.questions.length) + ')</button>';
    }).join("");
    renderEmpty("اختر فرعًا لعرض أسئلته.");
  };

  window.selectBranch = function (bid) {
    if (window.tahsiliRequire && !window.tahsiliRequire()) return;
    current.branch = bid;
    var d = DATA[current.track][current.subject];
    var branch = d.branches.filter(function (b) { return b.id === bid; })[0];
    Array.prototype.forEach.call(el("branch-pills").querySelectorAll(".branch-pill"), function (p) {
      p.classList.toggle("active", p.textContent.indexOf(branch.name) === 0);
    });
    el("content-area").innerHTML =
      '<div class="practice-card">' +
      '<p class="practice-intro">' + esc(d.name) + ' — ' + esc(branch.name) +
      '. جرّب الإجابة أولًا ثم اكشف الحل.</p>' +
      branch.questions.map(function (q, i) {
        return '<div class="mc-question">' +
          '<div class="mc-stem">' + ar(i + 1) + ') ' + esc(q.stem) +
          '<span class="mc-diff-badge">صعوبة ' + ar(q.difficulty) + '</span></div>' +
          '<div class="mc-options">' +
          q.options.map(function (o, oi) {
            return '<div class="mc-option" data-oi="' + oi + '" onclick="reveal(this,' + q.correct + ')">' +
              esc(o) + '</div>';
          }).join("") +
          '</div>' +
          '<div class="mc-feedback" hidden>' +
          '<div class="course-explain">' + esc(q.explanation) + '</div></div>' +
          '<button type="button" class="report-btn" onclick="openReportModal(this)">🚩 أبلغ عن خطأ</button>' +
          '</div>';
      }).join("") + '</div>';
  };

  window.reveal = function (node, correct) {
    var wrap = node.parentNode;
    if (wrap.getAttribute("data-done")) return;
    wrap.setAttribute("data-done", "1");
    var chosen = parseInt(node.getAttribute("data-oi"), 10);
    Array.prototype.forEach.call(wrap.querySelectorAll(".mc-option"), function (o) {
      var oi = parseInt(o.getAttribute("data-oi"), 10);
      if (oi === correct) o.classList.add("correct");
      else if (oi === chosen) o.classList.add("wrong");
    });
    wrap.parentNode.querySelector(".mc-feedback").hidden = false;
  };

  function renderEmpty(msg) {
    el("content-area").innerHTML =
      '<div class="empty-state"><div class="icon">👆</div>' +
      '<h3>' + (msg ? "اختر فرعًا" : "اختر مادة ثم فرعًا") + '</h3>' +
      '<p>' + esc(msg || "حدد مادة من الأعلى، ثم فرعًا محددًا، لتبدأ المراجعة الحرة عليه.") + '</p></div>';
  }

  selectTrack(current.track);
})();
"""


def build_bank(bp, subjects):
    data, tracks = {}, {}
    for tid, track in bp["tracks"].items():
        tracks[tid] = {"name": track["name"], "short": track["short"],
                       "subjects": [{"id": m["id"], "name": m["name"]} for m in track["subjects"]
                                    if (tid, m["id"]) in subjects]}
        data[tid] = {}
        for meta in track["subjects"]:
            d = subjects.get((tid, meta["id"]))
            if not d:
                continue
            qs = bt.shuffle_options(d.get("questions", []))
            branches = []
            for b in d.get("branches", []):
                bq = [q for q in qs if q["branch"] == b["name"]]
                if bq:
                    branches.append({"id": b["id"], "name": b["name"], "questions": bq})
            data[tid][meta["id"]] = {"name": meta["name"], "count": len(qs), "branches": branches}

    tabs = "".join(
        f'<button class="section-tab" id="tab-{tid}" onclick="selectTrack(\'{tid}\')">{t["name"]}</button>'
        for tid, t in tracks.items())

    engine = BANK_ENGINE % {"data": json.dumps(data, ensure_ascii=False),
                            "tracks": json.dumps(tracks, ensure_ascii=False)}

    html = bt.head(
        "بنك أسئلة التحصيلي | قدراتك",
        "بنك أسئلة التحصيلي: تصفّح أسئلة كل مادة وفرع في القسمين العلمي والأدبي، "
        "بلا مؤقّت ومع شرح لكل سؤال.",
        SITE + "/tahsili/question-bank/",
    ).replace("<style>" + chrome.course_css(), "<style>" + chrome.bank_css()) + bt.nav("/tahsili/", "التحصيلي") + f"""
<div class="wrap">
  <header class="path-header">
    <div class="eyebrow">
      <span>تدريب حر بدون وقت</span>
      <span class="sep">/</span>
      <span>بنك أسئلة التحصيلي</span>
    </div>
    <h1>بنك أسئلة التحصيلي</h1>
    <p>مكان واحد لتصفّح أسئلة أي فرع من فروع مواد التحصيلي، بلا مؤقّت وبلا ضغط اختبار —
       للفهم والمراجعة لا للقياس. اختر مسارًا ثم مادة ثم فرعًا لتبدأ.</p>
  </header>

  <section class="block">
    <div class="section-tabs">{tabs}</div>
    <div class="skill-grid" id="skill-grid"></div>
    <div id="branch-area" style="display:none; margin-top:4px;">
      <h3 style="font-size:14px; margin:0 0 10px;" id="branch-area-title"></h3>
      <div class="branch-pills" id="branch-pills"></div>
    </div>
    <div id="content-area" style="margin-top:10px;"></div>
  </section>
{footer("بنك أسئلة التحصيلي")}
</div>

<script>{engine}</script>
<script>{chrome.report_script()}</script>
{entitlement.script()}
{bt.assistant_for("التحصيلي")}
</body>
</html>
"""
    bt.write(os.path.join(bt.OUT, "question-bank", "index.html"), html)
    print("  ✓ tahsili/question-bank/")


def main():
    bp = bt.load_blueprint()
    subjects, stats = {}, {}
    for tid, track in bp["tracks"].items():
        for meta in track["subjects"]:
            d = bt.load_subject(tid, meta["id"])
            if d:
                subjects[(tid, meta["id"])] = d
                stats[(tid, meta["id"])] = len(d.get("questions", []))
    build_landing(bp, stats)
    build_bank(bp, subjects)


if __name__ == "__main__":
    main()
