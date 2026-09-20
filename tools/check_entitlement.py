# -*- coding: utf-8 -*-
"""فحص طبقة الصلاحيات في المتصفح: وضع التجربة، وبعد رفع العلم بباقات مختلفة."""
import os, sys, subprocess
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME_BIN", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
SIM = "file://" + os.path.join(ROOT, "tahsili", "simulator", "index.html")

DAY = 86400000
CASES = [
    ("بلا حساب",            None),
    ("باقة القدرات (١٢٠)",  {"plan": "120", "startTs": "NOW"}),
    ("الباقة الشاملة (١٤٩)", {"plan": "149", "startTs": "NOW"}),
    ("الشاملة منتهية",       {"plan": "149", "startTs": "OLD"}),
]


def set_profile(page, sub):
    if sub is None:
        page.evaluate("()=>{localStorage.clear()}")
        return
    ts = "Date.now()" if sub["startTs"] == "NOW" else f"Date.now()-{200*DAY}"
    page.evaluate("""(p)=>{
        localStorage.setItem('qudurat_current_profile_id','t1');
        localStorage.setItem('qudurat_profiles', JSON.stringify({t1:{name:'اختبار',subscription:{plan:p.plan,startTs:p.ts}}}));
    }""", {"plan": sub["plan"], "ts": None})
    page.evaluate(f"""(plan)=>{{
        localStorage.setItem('qudurat_current_profile_id','t1');
        localStorage.setItem('qudurat_profiles', JSON.stringify({{t1:{{name:'اختبار',subscription:{{plan:plan,startTs:{ts}}}}}}}));
    }}""", sub["plan"])


def run(page):
    rows = []
    for name, sub in CASES:
        page.goto(SIM, wait_until="load")
        set_profile(page, sub)
        page.reload(wait_until="load")
        page.wait_for_timeout(150)
        entitled = page.evaluate("window.tahsiliEntitled()")
        page.evaluate("startExam('scientific')")
        page.wait_for_timeout(200)
        started = page.is_visible("#screen-exam")
        gated = page.evaluate("!!document.getElementById('tahsili-gate')")
        bar = page.evaluate(
            "()=>{const h=document.querySelector('.path-header');"
            "const d=h&&h.lastElementChild;"
            "return d&&d.tagName==='DIV'?d.textContent.trim().slice(0,44):'(لا شريط)';}")
        rows.append((name, entitled, started, gated, bar))
    return rows


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        page = br.new_page()
        for mode in (False, True):
            subprocess.run([sys.executable, "-c",
                f"import re,io;p='{ROOT}/tools/entitlement.py';"
                f"s=open(p,encoding='utf-8').read();"
                f"s=re.sub(r'REQUIRES_SUBSCRIPTION = (True|False)','REQUIRES_SUBSCRIPTION = {mode}',s,count=1);"
                f"open(p,'w',encoding='utf-8').write(s)"], check=True)
            subprocess.run([sys.executable, f"{ROOT}/tools/build_all.py"],
                           check=True, capture_output=True)
            print(f"\n=== REQUIRES_SUBSCRIPTION = {mode} ===")
            print(f"{'الحالة':22s} {'مصرّح':7s} {'بدأ':6s} {'قفل':6s} الشريط")
            for name, ent, started, gated, bar in run(page):
                print(f"{name:22s} {str(ent):7s} {str(started):6s} {str(gated):6s} {bar}")
        br.close()
    # إعادة العلم إلى وضع المنصة الفعلي (تجربة مجانية) وإعادة البناء عليه
    subprocess.run([sys.executable, "-c",
        f"import re;p='{ROOT}/tools/entitlement.py';"
        f"s=open(p,encoding='utf-8').read();"
        f"s=re.sub(r'REQUIRES_SUBSCRIPTION = (True|False)','REQUIRES_SUBSCRIPTION = False',s,count=1);"
        f"open(p,'w',encoding='utf-8').write(s)"], check=True)
    subprocess.run([sys.executable, f"{ROOT}/tools/build_all.py"], check=True, capture_output=True)
    print("\nأُعيد العلم إلى وضع التجربة المجانية.")


if __name__ == "__main__":
    main()
