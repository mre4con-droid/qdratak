# -*- coding: utf-8 -*-
"""استخراج العناصر المشتركة (الهيكل، الأنماط، المساعد الذكي) من صفحات مسار القدرات.

مسار القدرات هو المصدر الوحيد للحقيقة في الشكل: صفحات التحصيلي تُولَّد من
نفس القطع، فأي تعديل على شكل القدرات ينعكس على التحصيلي بإعادة البناء.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# صفحة الدورة المرجعية التي تُستخرج منها القطع المشتركة
REF_COURSE = os.path.join(ROOT, "courses", "algebra", "index.html")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _blocks(html, tag):
    """كل محتويات وسم معيّن مع وسميه، بالترتيب."""
    out = []
    for m in re.finditer(r"<" + tag + r"\b[^>]*>", html):
        end = html.find("</" + tag + ">", m.end())
        out.append((m.start(), end + len(tag) + 3, html[m.end():end]))
    return out


def course_css():
    """ورقة أنماط الدورة المشتركة (كتلة <style> الأولى)."""
    return _blocks(read(REF_COURSE), "style")[0][2]


def assistant_module():
    """وحدة المساعد الذكي كاملة: التعليق الافتتاحي + الأنماط + الهيكل + السكربت."""
    html = read(REF_COURSE)
    start = html.find("<!-- AI-ASSISTANT-MODULE:START")
    end = html.find("<!-- AI-ASSISTANT-MODULE:END -->")
    if start < 0 or end < 0:
        raise RuntimeError("علامات وحدة المساعد الذكي غير موجودة في الصفحة المرجعية")
    return html[start:end + len("<!-- AI-ASSISTANT-MODULE:END -->")]


def report_script():
    """سكربت نافذة الإبلاغ عن خطأ (مشترك بين كل الصفحات)."""
    for _s, _e, body in _blocks(read(REF_COURSE), "script"):
        if "openReportModal" in body and "REPORT_EMAIL" in body:
            return body
    raise RuntimeError("سكربت الإبلاغ غير موجود في الصفحة المرجعية")


def logos():
    """شعارا الترويسة كما هما (data URI) من الصفحة المرجعية."""
    html = read(REF_COURSE)
    nav = html[html.find("<nav>"):html.find("</nav>")]
    srcs = re.findall(r'src="(data:image/png;base64,[A-Za-z0-9+/=]+)"', nav)
    if len(srcs) != 2:
        raise RuntimeError("لم يُعثر على شعاري الترويسة")
    return srcs


def background_svg():
    """خلفية الصفحة (data URI لملف SVG) من الصفحة المرجعية."""
    css = course_css()
    m = re.search(r'url\("(data:image/svg\+xml;base64,[A-Za-z0-9+/=]+)"\)', css)
    if not m:
        raise RuntimeError("خلفية الصفحة غير موجودة في الأنماط")
    return m.group(1)


REF_SIM = os.path.join(ROOT, "simulator", "index.html")


def simulator_css():
    """ورقة أنماط المحاكي المشتركة (كتلة <style> الأولى في صفحة المحاكي)."""
    return _blocks(read(REF_SIM), "style")[0][2]


def simulator_assistant():
    """وحدة المساعد الذكي بإعدادات المحاكي (بلا مسح البطاقات)."""
    html = read(REF_SIM)
    start = html.find("<!-- AI-ASSISTANT-MODULE:START")
    end = html.find("<!-- AI-ASSISTANT-MODULE:END -->")
    if start < 0 or end < 0:
        raise RuntimeError("علامات وحدة المساعد الذكي غير موجودة في صفحة المحاكي")
    return html[start:end + len("<!-- AI-ASSISTANT-MODULE:END -->")]


REF_BANK = os.path.join(ROOT, "question-bank", "index.html")


def bank_css():
    """ورقة أنماط بنك الأسئلة المشتركة."""
    return _blocks(read(REF_BANK), "style")[0][2]
