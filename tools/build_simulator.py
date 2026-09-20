# -*- coding: utf-8 -*-
"""مولّد محاكي اختبار التحصيلي.

يبني محاكيًا موقوتًا لكل مسار (علمي/أدبي) من بنوك أسئلة الدورات، بالتوزيع
المحدد في content/tahsili/blueprint.json، وبنفس أنماط محاكي القدرات.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chrome  # noqa: E402
import build_tahsili as bt  # noqa: E402
import entitlement  # noqa: E402

SITE = bt.SITE


def collect_pool(bp):
    """يجمع أسئلة كل مسار من ملفات المواد، موسومة بمادتها وفرعها."""
    pools = {}
    for track_id, track in bp["tracks"].items():
        items = []
        for meta in track["subjects"]:
            data = bt.load_subject(track_id, meta["id"])
            if not data:
                continue
            for q in bt.shuffle_options(data.get("questions", [])):
                items.append({
                    "subject": meta["name"], "subjectId": meta["id"],
                    "branch": q["branch"], "difficulty": q["difficulty"],
                    "stem": q["stem"], "options": q["options"],
                    "correct": q["correct"], "explanation": q.get("explanation", ""),
                })
        pools[track_id] = items
    return pools


SCREENS = """
%(nav)s

<section id="screen-start">
  <div class="wrap">
    <header class="path-header">
      <div class="eyebrow"><span>محاكي التحصيلي</span></div>
      <h1>محاكي اختبار التحصيل الدراسي</h1>
      <p>اختبار موقوت يحاكي الاختبار الحقيقي: عدد الأسئلة نفسه، والتوزيع نفسه على المواد، ونتيجة فورية مع تشخيص لكل مادة.</p>
    </header>
    <div class="track-grid" id="track-grid"></div>
    <div class="dash-entry"><a href="#" onclick="showScreen('screen-dashboard'); return false;">📊 لوحتي: تشخيصي وسجلي وخطتي وبنك أخطائي ←</a></div>
    <div class="rule-card" style="margin-top:16px;">
      <h3 style="margin:0 0 8px; font-size:15px;">📋 قبل ما تبدأ</h3>
      <ul class="intro-list">
        <li>العدّاد يبدأ فور دخولك ولا يتوقف، فاحجز وقتًا كاملًا بلا مقاطعة.</li>
        <li>تنقّل بين الأسئلة من الزرّين أو من شريط الأرقام، وتقدر ترجع وتغيّر إجابتك قبل التسليم.</li>
        <li>ما فيه خصم على الإجابة الخاطئة — لا تترك سؤالًا فارغًا.</li>
        <li>النتيجة تظهر فورًا مع تشخيص لكل مادة ومراجعة كاملة للإجابات.</li>
      </ul>
    </div>
  </div>
</section>


<section id="screen-dashboard" class="hidden">
  <div class="wrap">
    <div class="qcard">
      <div class="qcard-top" style="align-items:center;">
        <span class="qnum" id="dash-welcome">لوحة التحصيلي</span>
        <a class="dash-home-btn" href="/tahsili/" style="text-decoration:none;">🏠 التحصيلي</a>
      </div>
      <div class="dash-follow">
        <a href="#" onclick="showScreen('screen-report'); return false;"><span>📊</span>تقرير التشخيص</a>
        <a href="#" onclick="showScreen('screen-history'); return false;"><span>📅</span>سجل محاولاتي</a>
        <a href="#" onclick="showScreen('screen-plan'); return false;"><span>🎯</span>خطة اليوم</a>
        <a href="#" onclick="showScreen('screen-wrong'); return false;"><span>🚩</span>بنك أخطائي</a>
      </div>
      <div id="dash-summary" style="margin-top:16px;"></div>
      <button class="btn" onclick="showScreen('screen-start')" style="margin-top:16px;">ابدأ اختبارًا جديدًا</button>
    </div>
  </div>
</section>

<section id="screen-report" class="hidden">
  <div class="wrap">
    <div class="qcard">
      <div class="qcard-top"><span class="qnum">📊 تقرير التشخيص</span></div>
      <p class="screen-intro">التشخيص مبني على أدائك في محاكيات التحصيلي الكاملة وتدريبات الدورات — كل سؤال موسوم بمادته وفرعه.</p>
      <div id="report-body"></div>
      <button class="btn btn-ghost" onclick="showScreen('screen-dashboard')" style="margin-top:16px;">رجوع</button>
    </div>
  </div>
</section>

<section id="screen-history" class="hidden">
  <div class="wrap">
    <div class="qcard">
      <div class="qcard-top"><span class="qnum">📅 سجل محاولاتي</span></div>
      <p class="screen-intro">كل محاولة اختبار كاملة تُسجَّل هنا بتاريخها ونتيجتها وأضعف موادها، لتتابع تطورك بمرور الوقت.</p>
      <div id="history-body"></div>
      <button class="btn btn-ghost" onclick="showScreen('screen-dashboard')" style="margin-top:16px;">رجوع</button>
    </div>
  </div>
</section>

<section id="screen-plan" class="hidden">
  <div class="wrap">
    <div class="qcard">
      <div class="qcard-top"><span class="qnum">🎯 خطة اليوم</span></div>
      <p class="screen-intro">توصيات مبنية على أدائك الفعلي — لا ذكاء اصطناعي هنا، بل ترتيب بسيط: الأضعف أداءً أولًا، ثم ما لم تجرّبه بعد.</p>
      <div id="plan-body"></div>
      <button class="btn btn-ghost" onclick="showScreen('screen-dashboard')" style="margin-top:16px;">رجوع</button>
    </div>
  </div>
</section>

<section id="screen-wrong" class="hidden">
  <div class="wrap">
    <div class="qcard">
      <div class="qcard-top"><span class="qnum">🚩 بنك أخطائي</span></div>
      <p class="screen-intro">الأسئلة التي أخطأت فيها في المحاكي تُحفظ هنا بشرحها، لتراجعها قبل الاختبار الحقيقي.</p>
      <div id="wrong-body"></div>
      <div class="practice-actions" style="margin-top:14px;">
        <button class="btn btn-ghost" onclick="clearWrongBank()">تفريغ البنك</button>
        <button class="btn btn-ghost" onclick="showScreen('screen-dashboard')">رجوع</button>
      </div>
    </div>
  </div>
</section>

<section id="screen-exam" class="hidden">
  <div class="examhead">
    <div class="examhead-row">
      <a class="btn-exit" href="/tahsili/">🏠 خروج</a>
      <div class="section-tag">المادة: <span id="section-name"></span></div>
      <div class="timer" id="timer">٠٠:٠٠</div>
    </div>
    <div class="progress-track"><div class="progress-fill" id="progress-fill" style="width:0%%"></div></div>
  </div>
  <div class="wrap">
    <div class="qnav" id="qnav"></div>
    <div class="qcard">
      <div class="qcard-top">
        <span class="qnum" id="qnum"></span>
        <span class="difficulty" id="qdiff"></span>
      </div>
      <p class="qtext" id="qtext"></p>
      <div class="options" id="options"></div>
      <div class="hint-row">
        <button type="button" class="report-btn" onclick="openReportModal(this)">🚩 أبلغ عن خطأ</button>
      </div>
    </div>
    <div class="nav-row">
      <button class="btn btn-ghost" id="btn-prev" onclick="goPrev()">السابق</button>
      <button class="btn" id="btn-next" onclick="goNext()">التالي</button>
    </div>
  </div>
</section>

<section id="screen-results" class="hidden">
  <div class="wrap">
    <header class="path-header">
      <h1>نتيجتك</h1>
      <p id="results-sub"></p>
    </header>
    <div id="results-body"></div>
    <div class="practice-actions" style="margin-top:16px;">
      <button class="btn" onclick="location.reload()">اختبار جديد</button>
      <button class="btn btn-ghost" onclick="showScreen('screen-dashboard')">لوحتي</button>
      <a class="btn btn-ghost" href="/tahsili/">العودة للتحصيلي</a>
    </div>
    <h2 class="block-title" style="margin-top:24px;"><span class="tag">مراجعة</span> كل الأسئلة بإجاباتها</h2>
    <div id="review-body"></div>
  </div>
</section>
"""

ENGINE = r"""
(function () {
  "use strict";
  var POOLS = %(pools)s;
  var BLUEPRINT = %(blueprint)s;

  var state = null;
  var timerId = null;

  function ar(n) {
    return String(n).replace(/[0-9]/g, function (d) { return "٠١٢٣٤٥٦٧٨٩"[d]; });
  }
  function two(n) { return (n < 10 ? "0" : "") + n; }
  function esc(s) {
    var d = document.createElement("div"); d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function el(id) { return document.getElementById(id); }
  var SCREENS = ["screen-start", "screen-dashboard", "screen-report", "screen-history",
                 "screen-plan", "screen-wrong", "screen-exam", "screen-results"];
  function show(id) {
    SCREENS.forEach(function (s) { el(s).classList.toggle("hidden", s !== id); });
    window.scrollTo(0, 0);
  }

  // شاشة واحدة تُبنى عند فتحها، فالبيانات تُقرأ لحظة العرض لا عند تحميل الصفحة
  var BUILDERS = {
    "screen-dashboard": renderDashboard,
    "screen-report": renderReport,
    "screen-history": renderHistory,
    "screen-plan": renderPlan,
    "screen-wrong": renderWrong
  };
  window.showScreen = function (id) {
    if (BUILDERS[id]) BUILDERS[id]();
    show(id);
  };

  // ---------------- شاشة البداية: بطاقة لكل مسار

  function renderTracks() {
    var html = "";
    Object.keys(BLUEPRINT).forEach(function (tid) {
      var t = BLUEPRINT[tid];
      var have = (POOLS[tid] || []).length;
      var rows = t.subjects.map(function (s) {
        return '<li>' + esc(s.name) + ' — ' + ar(s.questions) + ' سؤالًا</li>';
      }).join("");
      html += '<div class="track-card">' +
        '<h3>' + esc(t.name) + '</h3>' +
        '<p class="track-desc">' + esc(t.description) + '</p>' +
        '<ul class="track-subjects">' + rows + '</ul>' +
        // الفاصل النقطي بين رقمين عربيين يلتصق بأولهما بصريًا فيُقرأ ١٦٠٠ بدل ١٦٠
        '<div class="track-meta">' + ar(t.total_questions) + ' سؤالًا في ' +
          ar(t.duration_minutes) + ' دقيقة</div>' +
        '<div class="track-note">المتاح حاليًا في بنك الأسئلة: ' + ar(have) + ' سؤالًا</div>' +
        '<button class="btn" onclick="startExam(\'' + tid + '\')">ابدأ الاختبار</button>' +
        '</div>';
    });
    el("track-grid").innerHTML = html;
  }

  // ---------------- بناء الاختبار بالتوزيع المحدد

  function pickQuestions(trackId) {
    var t = BLUEPRINT[trackId];
    var pool = POOLS[trackId] || [];
    var chosen = [];
    t.subjects.forEach(function (s) {
      var bySubject = shuffle(pool.filter(function (q) { return q.subjectId === s.id; }));
      chosen = chosen.concat(bySubject.slice(0, s.questions));
    });
    // إن نقص بنك مادة عن حصتها يُستكمل العدد من بقية المواد حتى لا يقصر الاختبار
    if (chosen.length < t.total_questions) {
      var used = {};
      chosen.forEach(function (q) { used[q.stem] = true; });
      var rest = shuffle(pool.filter(function (q) { return !used[q.stem]; }));
      chosen = chosen.concat(rest.slice(0, t.total_questions - chosen.length));
    }
    return chosen;
  }

  window.startExam = function (trackId) {
    if (window.tahsiliRequire && !window.tahsiliRequire()) return;
    var t = BLUEPRINT[trackId];
    var questions = pickQuestions(trackId);
    if (!questions.length) {
      alert("بنك أسئلة هذا المسار فارغ حاليًا.");
      return;
    }
    // المدة تتناسب مع عدد الأسئلة المتاح فعلًا، فلا يبقى الطالب أمام عدّاد فارغ
    var seconds = Math.round(t.duration_minutes * 60 * questions.length / t.total_questions);
    state = {
      trackId: trackId, track: t, questions: questions,
      answers: new Array(questions.length).fill(null),
      index: 0, remaining: seconds, finished: false
    };
    show("screen-exam");
    buildNav();
    renderQuestion();
    startTimer();
  };

  function startTimer() {
    tick();
    timerId = setInterval(tick, 1000);
  }
  function tick() {
    if (state.remaining <= 0) { finish(true); return; }
    state.remaining--;
    var h = Math.floor(state.remaining / 3600);
    var m = Math.floor((state.remaining %% 3600) / 60), s = state.remaining %% 60;
    // اختبار التحصيلي يتجاوز الساعة، فصيغة دقائق:ثوانٍ وحدها تُربك القارئ
    el("timer").textContent = ar(h > 0 ? h + ":" + two(m) + ":" + two(s) : two(m) + ":" + two(s));
  }

  function buildNav() {
    el("qnav").innerHTML = state.questions.map(function (_q, i) {
      return '<button type="button" class="qnav-btn" data-i="' + i +
             '" onclick="goTo(' + i + ')">' + ar(i + 1) + '</button>';
    }).join("");
    refreshNav();
  }
  function refreshNav() {
    var btns = el("qnav").querySelectorAll(".qnav-btn");
    Array.prototype.forEach.call(btns, function (b) {
      var i = parseInt(b.getAttribute("data-i"), 10);
      b.classList.toggle("answered", state.answers[i] !== null);
      b.classList.toggle("current", i === state.index);
    });
    var done = state.answers.filter(function (a) { return a !== null; }).length;
    el("progress-fill").style.width = (done / state.questions.length * 100) + "%%";
  }

  var DIFF = { 1: "سهل", 2: "سهل", 3: "متوسط", 4: "صعب", 5: "صعب" };

  function renderQuestion() {
    var q = state.questions[state.index];
    el("section-name").textContent = q.subject;
    el("qnum").textContent = "السؤال " + ar(state.index + 1) + " من " + ar(state.questions.length);
    el("qdiff").textContent = DIFF[q.difficulty] || "متوسط";
    el("qtext").textContent = q.stem;
    el("options").innerHTML = q.options.map(function (opt, oi) {
      var sel = state.answers[state.index] === oi ? " selected" : "";
      return '<div class="option' + sel + '" onclick="pick(' + oi + ')">' + esc(opt) + '</div>';
    }).join("");
    el("btn-prev").disabled = state.index === 0;
    el("btn-next").textContent = state.index === state.questions.length - 1 ? "إنهاء وتسليم" : "التالي";
    refreshNav();
  }

  window.pick = function (oi) {
    state.answers[state.index] = oi;
    renderQuestion();
  };
  window.goTo = function (i) { state.index = i; renderQuestion(); };
  window.goPrev = function () { if (state.index > 0) { state.index--; renderQuestion(); } };
  window.goNext = function () {
    if (state.index < state.questions.length - 1) { state.index++; renderQuestion(); return; }
    var blank = state.answers.filter(function (a) { return a === null; }).length;
    var msg = blank
      ? "باقي " + ar(blank) + " سؤالًا بلا إجابة. تسلّم الآن؟"
      : "تسليم الاختبار وعرض النتيجة؟";
    if (confirm(msg)) finish(false);
  };

  // ---------------- النتيجة والتشخيص

  function finish(timeUp) {
    if (state.finished) return;
    state.finished = true;
    clearInterval(timerId);

    var bySubject = {}, correct = 0;
    state.questions.forEach(function (q, i) {
      var s = bySubject[q.subject] || (bySubject[q.subject] = { total: 0, correct: 0 });
      s.total++;
      if (state.answers[i] === q.correct) { s.correct++; correct++; }
    });

    var pct = Math.round(correct / state.questions.length * 100);
    el("results-sub").textContent = (timeUp ? "انتهى الوقت. " : "") +
      "أجبت عن " + ar(correct) + " من " + ar(state.questions.length) +
      " إجابة صحيحة في " + state.track.name + ".";

    var rows = Object.keys(bySubject).map(function (name) {
      var s = bySubject[name];
      var p = Math.round(s.correct / s.total * 100);
      return '<div class="subject-row">' +
        '<div class="subject-row-head"><b>' + esc(name) + '</b>' +
        '<span>' + ar(s.correct) + ' / ' + ar(s.total) + ' — ' + ar(p) + '٪</span></div>' +
        '<div class="subject-bar"><div class="subject-bar-fill" style="width:' + p + '%%"></div></div>' +
        '</div>';
    }).join("");

    el("results-body").innerHTML =
      '<div class="score-card"><div class="score-big">' + ar(pct) + '٪</div>' +
      '<div class="score-label">نسبتك في هذا الاختبار</div></div>' +
      '<div class="rule-card" style="margin-top:12px;">' +
      '<h3 style="margin:0 0 10px; font-size:15px;">أداؤك حسب المادة</h3>' + rows + '</div>';

    saveDiagnostics(bySubject);
    addToWrongBank(state.questions.filter(function (q, i) {
      return state.answers[i] !== q.correct;
    }).map(function (q) {
      return { stem: q.stem, options: q.options, correct: q.correct,
               explanation: q.explanation, subject: q.subject, branch: q.branch };
    }));
    renderReview();
    show("screen-results");
  }

  var HISTORY_MAX = 30;
  function saveDiagnostics(bySubject) {
    var hist = examHistory();
    hist.unshift({
      at: Date.now(), track: state.trackId,
      total: state.questions.length,
      correct: state.questions.filter(function (q, i) { return state.answers[i] === q.correct; }).length,
      bySubject: bySubject
    });
    writeJSON(keyFor("tahsili_exam_history"), hist.slice(0, HISTORY_MAX));
  }

  function renderReview() {
    el("review-body").innerHTML = state.questions.map(function (q, i) {
      var sel = state.answers[i];
      var opts = q.options.map(function (opt, oi) {
        var cls = oi === q.correct ? "correct" : (oi === sel ? "wrong" : "");
        return '<div class="mc-option ' + cls + '">' + esc(opt) + '</div>';
      }).join("");
      var verdict = sel === null ? "لم تجب"
        : (sel === q.correct ? "✓ إجابة صحيحة" : "✗ إجابة خاطئة");
      return '<div class="mc-question">' +
        '<div class="mc-stem">' + ar(i + 1) + ') ' + esc(q.stem) +
        '<span class="mc-diff-badge">' + esc(q.subject) + ' — ' + esc(q.branch) + '</span></div>' +
        '<div class="mc-options">' + opts + '</div>' +
        '<div class="mc-feedback">' + verdict +
        (q.explanation ? '<div class="course-explain">' + esc(q.explanation) + '</div>' : '') +
        '</div></div>';
    }).join("");
  }


  // ---------------- التخزين: مفاتيح مرتبطة بالحساب كما في مسار القدرات

  function pid() {
    try { return localStorage.getItem("qudurat_current_profile_id"); } catch (e) { return null; }
  }
  function keyFor(base) { var p = pid(); return p ? base + "__" + p : base; }
  function readJSON(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key) || "null") || fallback; }
    catch (e) { return fallback; }
  }
  function writeJSON(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {}
  }

  function examHistory() { return readJSON(keyFor("tahsili_exam_history"), []); }
  function courseDiag() { return readJSON(keyFor("tahsili_diagnostics"), {}); }
  function wrongBank() { return readJSON(keyFor("tahsili_wrong_bank"), []); }

  var WRONG_MAX = 80;
  function addToWrongBank(items) {
    var bank = wrongBank();
    var seen = {};
    bank.forEach(function (q) { seen[q.stem] = true; });
    items.forEach(function (q) { if (!seen[q.stem]) { bank.unshift(q); seen[q.stem] = true; } });
    writeJSON(keyFor("tahsili_wrong_bank"), bank.slice(0, WRONG_MAX));
  }
  window.clearWrongBank = function () {
    if (!confirm("تفريغ بنك الأخطاء نهائيًا؟")) return;
    writeJSON(keyFor("tahsili_wrong_bank"), []);
    renderWrong();
  };

  // ---------------- تجميع الأداء من مصدرين: المحاكي وتدريبات الدورات

  function aggregate() {
    var bySubject = {}, byBranch = {};
    examHistory().forEach(function (h) {
      Object.keys(h.bySubject || {}).forEach(function (name) {
        var s = bySubject[name] || (bySubject[name] = { total: 0, correct: 0 });
        s.total += h.bySubject[name].total;
        s.correct += h.bySubject[name].correct;
      });
    });
    var diag = courseDiag();
    Object.keys(diag).forEach(function (subject) {
      var d = diag[subject];
      var s = bySubject[subject] || (bySubject[subject] = { total: 0, correct: 0 });
      s.total += d.totalAttempts || 0;
      s.correct += d.totalCorrect || 0;
      Object.keys(d.byBranch || {}).forEach(function (b) {
        var t = byBranch[b] || (byBranch[b] = { total: 0, correct: 0, subject: subject });
        t.total += d.byBranch[b].total;
        t.correct += d.byBranch[b].correct;
      });
    });
    return { bySubject: bySubject, byBranch: byBranch };
  }

  function pct(s) { return s.total ? Math.round(s.correct / s.total * 100) : 0; }

  function bar(label, s) {
    var p = pct(s);
    var tone = p >= 70 ? "var(--teal)" : (p >= 50 ? "var(--gold)" : "var(--red)");
    return '<div class="subject-row">' +
      '<div class="subject-row-head"><b>' + esc(label) + '</b><span>' +
      ar(s.correct) + ' / ' + ar(s.total) + ' — ' + ar(p) + '٪</span></div>' +
      '<div class="subject-bar"><div class="subject-bar-fill" style="width:' + p +
      '%%; background:' + tone + '"></div></div></div>';
  }

  function emptyState(msg) {
    return '<div class="empty-state"><div class="icon">📭</div><h3>لا توجد بيانات بعد</h3>' +
           '<p>' + esc(msg) + '</p></div>';
  }

  // ---------------- الشاشات

  function renderDashboard() {
    var name = "";
    try {
      var p = pid();
      var prof = p && JSON.parse(localStorage.getItem("qudurat_profiles") || "{}")[p];
      if (prof && prof.name) name = prof.name;
    } catch (e) {}
    el("dash-welcome").textContent = name ? "لوحة التحصيلي — أهلًا " + name : "لوحة التحصيلي";

    var hist = examHistory();
    var agg = aggregate();
    var subjects = Object.keys(agg.bySubject);
    if (!hist.length && !subjects.length) {
      el("dash-summary").innerHTML = emptyState("خُض محاكي اختبار كامل أو تدرّب في الدورات، وستظهر لوحتك هنا.");
      return;
    }
    var last = hist[0];
    var lastLine = last
      ? '<div class="rule-card" style="margin-bottom:12px;"><b>آخر محاولة:</b> ' +
        ar(last.correct) + ' من ' + ar(last.total) + ' — ' +
        ar(Math.round(last.correct / last.total * 100)) + '٪ في ' +
        esc(BLUEPRINT[last.track] ? BLUEPRINT[last.track].name : last.track) + '</div>'
      : "";
    el("dash-summary").innerHTML = lastLine +
      '<div class="rule-card"><h3 style="margin:0 0 10px; font-size:15px;">أداؤك حسب المادة</h3>' +
      (subjects.length ? subjects.map(function (n) { return bar(n, agg.bySubject[n]); }).join("")
                       : '<p class="screen-intro" style="margin:0;">لا توجد بيانات مواد بعد.</p>') +
      '</div>';
  }

  function renderReport() {
    var agg = aggregate();
    var subjects = Object.keys(agg.bySubject);
    if (!subjects.length) {
      el("report-body").innerHTML = emptyState("خُض محاكي اختبار كامل ليظهر تشخيص حقيقي حسب المادة والفرع.");
      return;
    }
    var branches = Object.keys(agg.byBranch).sort(function (a, b) {
      return pct(agg.byBranch[a]) - pct(agg.byBranch[b]);
    });
    el("report-body").innerHTML =
      '<div class="rule-card"><h3 style="margin:0 0 10px; font-size:15px;">حسب المادة</h3>' +
      subjects.map(function (n) { return bar(n, agg.bySubject[n]); }).join("") + '</div>' +
      (branches.length
        ? '<div class="rule-card" style="margin-top:12px;">' +
          '<h3 style="margin:0 0 10px; font-size:15px;">حسب الفرع — من الأضعف</h3>' +
          branches.map(function (b) {
            return bar(b + " (" + agg.byBranch[b].subject + ")", agg.byBranch[b]);
          }).join("") + '</div>'
        : '<div class="rule-card" style="margin-top:12px;"><p class="screen-intro" style="margin:0;">' +
          'تفصيل الفروع يظهر بعد التدرّب في صفحات الدورات.</p></div>');
  }

  var ARABIC_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                       "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"];
  function fmtDate(ts) {
    var d = new Date(ts);
    return ar(d.getDate()) + " " + ARABIC_MONTHS[d.getMonth()] + " " + ar(d.getFullYear());
  }

  function renderHistory() {
    var hist = examHistory();
    if (!hist.length) {
      el("history-body").innerHTML = emptyState("ما خضت محاكيًا كاملًا بعد.");
      return;
    }
    el("history-body").innerHTML = hist.map(function (h) {
      var p = Math.round(h.correct / h.total * 100);
      var names = Object.keys(h.bySubject || {});
      var weakest = names.sort(function (a, b) {
        return pct(h.bySubject[a]) - pct(h.bySubject[b]);
      })[0];
      return '<div class="rule-card" style="margin-bottom:10px;">' +
        '<div class="subject-row-head"><b>' +
        esc(BLUEPRINT[h.track] ? BLUEPRINT[h.track].name : h.track) + '</b>' +
        '<span>' + fmtDate(h.at) + '</span></div>' +
        '<div style="font-size:14px; margin:6px 0;">' + ar(h.correct) + ' من ' + ar(h.total) +
        ' — <b>' + ar(p) + '٪</b></div>' +
        (weakest ? '<div class="screen-intro" style="margin:0;">أضعف مادة: ' +
                   esc(weakest) + ' (' + ar(pct(h.bySubject[weakest])) + '٪)</div>' : "") +
        '</div>';
    }).join("");
  }

  function renderPlan() {
    var agg = aggregate();
    var units = Object.keys(agg.byBranch).map(function (b) {
      return { name: b, subject: agg.byBranch[b].subject, stat: agg.byBranch[b] };
    });
    if (!units.length) {
      units = Object.keys(agg.bySubject).map(function (n) {
        return { name: n, subject: n, stat: agg.bySubject[n] };
      });
    }
    if (!units.length) {
      el("plan-body").innerHTML = emptyState("خُض محاكيًا أو تدرّب في دورة، ثم ارجع لتحصل على خطة مبنية على أدائك.");
      return;
    }
    units.sort(function (a, b) { return pct(a.stat) - pct(b.stat); });
    var top = units.slice(0, 5);
    el("plan-body").innerHTML =
      '<div class="rule-card"><h3 style="margin:0 0 10px; font-size:15px;">ابدأ بهذه اليوم</h3>' +
      top.map(function (u, i) {
        var p = pct(u.stat);
        // عند غياب بيانات الفروع يكون اسم الوحدة هو المادة نفسها، فلا يُكرَّر
        var where = u.subject === u.name ? "" : esc(u.subject) + " — ";
        return '<div class="plan-step"><span class="branch-num">' + ar(i + 1) + '</span>' +
          '<div><b>' + esc(u.name) + '</b>' +
          '<div class="screen-intro" style="margin:2px 0 0;">' + where +
          'إتقانك الحالي ' + ar(p) + '٪' +
          (p < 50 ? ' · يحتاج مراجعة الشرح قبل التدريب' : ' · تدرّب على أسئلة إضافية') +
          '</div></div></div>';
      }).join("") + '</div>' +
      '<div class="rule-card" style="margin-top:12px;"><p class="screen-intro" style="margin:0;">' +
      'الترتيب من الأضعف إلى الأقوى. راجع شرح الفرع في صفحة دورته ثم عُد لبنك أسئلته.</p></div>';
  }

  function renderWrong() {
    var bank = wrongBank();
    if (!bank.length) {
      el("wrong-body").innerHTML = emptyState("ما فيه أخطاء محفوظة — أخطاؤك في المحاكي تُحفظ هنا تلقائيًا.");
      return;
    }
    el("wrong-body").innerHTML = bank.map(function (q, i) {
      return '<div class="mc-question">' +
        '<div class="mc-stem">' + ar(i + 1) + ') ' + esc(q.stem) +
        '<span class="mc-diff-badge">' + esc(q.subject) + ' — ' + esc(q.branch) + '</span></div>' +
        '<div class="mc-options">' +
        q.options.map(function (o, oi) {
          return '<div class="mc-option ' + (oi === q.correct ? "correct" : "") + '">' + esc(o) + '</div>';
        }).join("") + '</div>' +
        (q.explanation ? '<div class="mc-feedback"><div class="course-explain">' +
                          esc(q.explanation) + '</div></div>' : "") +
        '</div>';
    }).join("");
  }

  renderTracks();
})();
"""

EXTRA_CSS = """
  /* أنماط المحاكي لا تعرّف شريط ترويسة (nav) ولا محاذاته، فتُضاف هنا
     ليطابق شكل بقية صفحات الموقع بدل أن يظهر بلا شريط ولا حدّ. */
  nav { position: sticky; top: 0; z-index: 40;
    background: color-mix(in srgb, var(--paper) 92%, transparent);
    backdrop-filter: blur(8px); border-bottom: 1px solid var(--border); margin-bottom: 18px; }
  nav .nav-row { display: flex; align-items: center; justify-content: space-between;
    padding: 12px 0; margin-top: 0; }
  nav .home-link { font-size: 14px; font-weight: 700; color: var(--teal); text-decoration: none; }
  .track-grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
  .track-card { background: var(--paper); border: 1px solid var(--border); border-radius: 14px;
    padding: 18px; box-shadow: var(--shadow); }
  .track-card h3 { margin: 0 0 6px; font-size: 19px; }
  .track-desc { font-size: 13.5px; color: var(--ink-soft); margin: 0 0 10px; }
  .track-subjects { margin: 0 0 10px; padding-inline-start: 18px; font-size: 13.5px; color: var(--ink-soft); }
  .track-subjects li { margin-bottom: 3px; }
  .track-meta { font-size: 13px; font-weight: 700; color: var(--teal); margin-bottom: 4px; }
  .track-note { font-size: 12.5px; color: var(--ink-soft); margin-bottom: 12px; }
  .score-card { background: var(--paper); border: 1px solid var(--border); border-radius: 14px;
    padding: 22px; text-align: center; box-shadow: var(--shadow); }
  .score-big { font-size: 46px; font-weight: 800; color: var(--teal); line-height: 1.1; }
  .score-label { font-size: 13.5px; color: var(--ink-soft); margin-top: 4px; }
  .subject-row { margin-bottom: 12px; }
  .subject-row-head { display: flex; justify-content: space-between; font-size: 13.5px; margin-bottom: 5px; }
  .subject-bar { height: 8px; background: var(--bg); border-radius: 6px; overflow: hidden; }
  .subject-bar-fill { height: 100%; background: var(--teal); border-radius: 6px; }
  .hidden { display: none !important; }
  .screen-intro { font-size: 13.5px; color: var(--ink-soft); margin: 0 0 18px; }
  .dash-entry { margin-top: 16px; text-align: center; }
  .dash-entry a { font-size: 14px; font-weight: 700; color: var(--teal); text-decoration: none; }
  .dash-follow { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }
  .dash-follow a { display: flex; align-items: center; gap: 8px; padding: 12px 14px;
    background: var(--bg); border: 1px solid var(--border); border-radius: 12px;
    font-size: 14px; font-weight: 700; color: inherit; text-decoration: none; }
  .dash-follow a:hover { border-color: var(--teal); }
  .dash-home-btn { font-size: 13px; font-weight: 700; color: var(--teal); }
  .plan-step { display: flex; gap: 10px; align-items: flex-start; padding: 10px 0;
    border-bottom: 1px solid var(--border); }
  .plan-step:last-child { border-bottom: 0; }
"""


def build(bp, pools):
    blueprint = {tid: {k: t[k] for k in
                       ("name", "short", "description", "total_questions",
                        "duration_minutes", "subjects")}
                 for tid, t in bp["tracks"].items()}
    body = SCREENS % {"nav": bt.nav("/tahsili/", "التحصيلي")}
    engine = ENGINE % {
        "pools": json.dumps(pools, ensure_ascii=False),
        "blueprint": json.dumps(blueprint, ensure_ascii=False),
    }
    html = (bt.head("محاكي اختبار التحصيلي | قدراتك",
                    "محاكي اختبار التحصيل الدراسي: اختبار موقوت بعدد الأسئلة الرسمي وتوزيعه على المواد، "
                    "مع نتيجة فورية وتشخيص لكل مادة ومراجعة كاملة.",
                    SITE + "/tahsili/simulator/").replace(
                "<style>" + chrome.course_css(),
                "<style>" + chrome.simulator_css() + EXTRA_CSS)
            + body
            + "\n<script>" + engine + "</script>\n"
            + "<script>" + chrome.report_script() + "</script>\n"
            + entitlement.script()
            + chrome.simulator_assistant()
            + "\n</body>\n</html>\n")
    bt.write(os.path.join(bt.OUT, "simulator", "index.html"), html)
    total = sum(len(v) for v in pools.values())
    print("  ✓ tahsili/simulator/ — مخزون %s سؤالًا" % bt.ar(total))


def main():
    bp = bt.load_blueprint()
    pools = collect_pool(bp)
    for tid, items in pools.items():
        print("    %s: %s سؤالًا" % (bp["tracks"][tid]["name"], bt.ar(len(items))))
    build(bp, pools)


if __name__ == "__main__":
    main()
