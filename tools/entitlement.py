# -*- coding: utf-8 -*-
"""طبقة صلاحيات مسار التحصيلي.

تقرأ حساب الطالب نفسه المستخدم في مسار القدرات (qudurat_profiles)، وتتحقق أن
باقته تفتح مسار التحصيلي حسب content/plans.json. تُحقن في صفحات التحصيلي
المولَّدة، ويتحكم فيها علم واحد يوافق وضع المنصة الحالي.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tahsili as bt  # noqa: E402

# المنصة كلها في وضع تجربة مجانية (COURSES_CATALOG_REQUIRES_SUBSCRIPTION = false
# و AI_TRIAL_MODE = true في مسار القدرات). هذا العلم يوافقه، ويُرفع يوم الإطلاق
# مع نظيريه فيُحمى المساران معًا.
REQUIRES_SUBSCRIPTION = False

TEMPLATE = r"""
<script>
/* TAHSILI-ENTITLEMENT — مولَّد من tools/entitlement.py، لا يُعدَّل يدويًا */
(function () {
  "use strict";
  var REQUIRES_SUBSCRIPTION = %(requires)s;
  var PLAN_DURATIONS = %(durations)s;
  var PLAN_TRACKS = %(tracks)s;
  var PRICING_URL = "/#pricing";

  function profile() {
    try {
      var pid = localStorage.getItem("qudurat_current_profile_id");
      if (!pid) return null;
      return JSON.parse(localStorage.getItem("qudurat_profiles") || "{}")[pid] || null;
    } catch (e) { return null; }
  }

  function daysRemaining(p) {
    if (!p || !p.subscription || !p.subscription.plan) return null;
    var dur = PLAN_DURATIONS[p.subscription.plan];
    if (!dur) return null;
    var elapsed = Math.floor((Date.now() - p.subscription.startTs) / 86400000);
    return Math.max(dur - elapsed, 0);
  }

  // الصلاحية تتطلب اشتراكًا ساريًا وباقةً تفتح مسار التحصيلي تحديدًا
  function entitled() {
    var p = profile();
    var remaining = daysRemaining(p);
    if (remaining === null || remaining <= 0) return false;
    var tracks = PLAN_TRACKS[p.subscription.plan] || [];
    return tracks.indexOf("tahsili") !== -1;
  }

  window.tahsiliEntitled = function () { return !REQUIRES_SUBSCRIPTION || entitled(); };
  window.tahsiliDaysRemaining = function () { return daysRemaining(profile()); };

  // يُستدعى عند أي إجراء محمي: يعيد true إن كان مسموحًا، وإلا عرض سبب المنع
  window.tahsiliRequire = function () {
    if (window.tahsiliEntitled()) return true;
    var p = profile();
    var msg = !p
      ? "مسار التحصيلي يحتاج حسابًا واشتراكًا في الباقة الشاملة."
      : "باقتك الحالية تغطي مسار القدرات فقط. الباقة الشاملة تفتح المسارين معًا.";
    showGate(msg);
    return false;
  };

  function showGate(msg) {
    var old = document.getElementById("tahsili-gate");
    if (old) old.parentNode.removeChild(old);
    var wrap = document.createElement("div");
    wrap.id = "tahsili-gate";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-modal", "true");
    wrap.style.cssText = "position:fixed; inset:0; z-index:9999; display:flex;" +
      "align-items:center; justify-content:center; padding:20px;" +
      "background:rgba(22,35,63,.55);";
    var box = document.createElement("div");
    box.style.cssText = "background:var(--paper); color:var(--ink); border:1px solid var(--border);" +
      "border-radius:16px; padding:24px; max-width:420px; box-shadow:var(--shadow); text-align:center;";
    var h = document.createElement("h3");
    h.textContent = "🔒 مسار التحصيلي";
    h.style.cssText = "margin:0 0 8px; font-size:19px;";
    var pEl = document.createElement("p");
    pEl.textContent = msg;
    pEl.style.cssText = "margin:0 0 16px; font-size:14px; line-height:1.9; color:var(--ink-soft);";
    var go = document.createElement("a");
    go.href = PRICING_URL;
    go.className = "btn";
    go.textContent = "شوف الباقة الشاملة";
    go.style.textDecoration = "none";
    var close = document.createElement("button");
    close.type = "button";
    close.className = "btn btn-ghost";
    close.textContent = "إغلاق";
    close.style.marginInlineStart = "8px";
    close.onclick = function () { wrap.parentNode.removeChild(wrap); };
    box.appendChild(h); box.appendChild(pEl); box.appendChild(go); box.appendChild(close);
    wrap.appendChild(box);
    wrap.addEventListener("click", function (e) { if (e.target === wrap) wrap.removeChild(box); });
    document.body.appendChild(wrap);
  }

  // شريط يوضح حالة الوصول أعلى الصفحة، ليعرف الطالب موقفه قبل أن يصطدم بالقفل
  document.addEventListener("DOMContentLoaded", function () {
    var host = document.querySelector(".path-header");
    if (!host) return;
    var remaining = daysRemaining(profile());
    var bar = document.createElement("div");
    bar.style.cssText = "margin-top:12px; padding:9px 13px; border-radius:10px;" +
      "font-size:13px; border:1px solid var(--border); background:var(--paper);";
    if (!REQUIRES_SUBSCRIPTION) {
      bar.innerHTML = "🎁 مسار التحصيلي متاح مجانًا خلال فترة التجربة.";
    } else if (window.tahsiliEntitled()) {
      bar.innerHTML = "✅ اشتراكك يشمل مسار التحصيلي — باقٍ " +
        String(remaining).replace(/[0-9]/g, function (d) { return "٠١٢٣٤٥٦٧٨٩"[d]; }) + " يومًا.";
    } else {
      bar.innerHTML = '🔒 مسار التحصيلي ضمن <b>الباقة الشاملة</b>. ' +
        '<a href="' + PRICING_URL + '" style="color:var(--teal); font-weight:700;">شوف الباقات ←</a>';
    }
    host.appendChild(bar);
  });
})();
</script>
"""


def script():
    with open(os.path.join(bt.CONTENT.replace("tahsili", ""), "plans.json"), encoding="utf-8") as fh:
        plans = json.load(fh)["plans"]
    return TEMPLATE % {
        "requires": "true" if REQUIRES_SUBSCRIPTION else "false",
        "durations": json.dumps({p["id"]: p["days"] for p in plans}, ensure_ascii=False),
        "tracks": json.dumps({p["id"]: p["tracks"] for p in plans}, ensure_ascii=False),
    }
