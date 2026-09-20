# -*- coding: utf-8 -*-
"""فحص صفحات التحصيلي في متصفح حقيقي: أخطاء الـJS، عرض الأسئلة، وصحة التحقق."""
import sys, glob, os
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME_BIN", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

# أخطاء بيئية لا علاقة لها بالصفحة: الخطوط عبر الوكيل، والأيقونة عبر file://
IGNORE = ("ERR_CERT_AUTHORITY_INVALID", "ERR_FILE_NOT_FOUND", "ERR_NAME_NOT_RESOLVED",
          "ERR_INTERNET_DISCONNECTED", "favicon")


def _real(text):
    return not any(tok in text for tok in IGNORE)


def check(page, path):
    errs = []
    page.on("console", lambda m: errs.append(m.text) if (m.type == "error" and _real(m.text)) else None)
    page.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
    page.goto("file://" + path, wait_until="load")
    banks = page.eval_on_selector_all('[id^="mc-list-"]', "els=>els.map(e=>e.id)")
    counts = {}
    for b in banks:
        counts[b] = page.eval_on_selector_all(f'#{b} .mc-question', "e=>e.length")
    # جرّب التحقق على أول بنك: اختر الإجابة الصحيحة لأول سؤال ثم تحقق
    ok = None
    if banks:
        bank = banks[0].replace("mc-list-", "")
        ok = page.evaluate("""(bank)=>{
            const q=document.querySelector('#mc-list-'+bank+' .mc-question');
            if(!q) return 'no-question';
            q.querySelectorAll('.mc-option')[0].click();
            window.checkBank(bank);
            const fb=document.getElementById('fb-'+bank+'-0');
            const sum=document.getElementById('score-summary-'+bank);
            return {feedback:(fb.textContent||'').slice(0,40), summary:sum.textContent};
        }""", bank)
    return errs, counts, ok

def main(paths):
    bad = 0
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for path in paths:
            page = br.new_page()
            errs, counts, ok = check(page, path)
            rel = os.path.relpath(path, ROOT)
            status = "✓" if not errs else "✗"
            if errs: bad += 1
            print(f"{status} {rel}")
            print(f"    بنوك: {counts}")
            print(f"    تحقق: {ok}")
            for e in errs[:5]:
                print(f"    خطأ: {e[:160]}")
            page.close()
        br.close()
    return bad

if __name__ == "__main__":
    args = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "tahsili", "**", "index.html"), recursive=True))
    sys.exit(1 if main([os.path.abspath(a) for a in args]) else 0)
