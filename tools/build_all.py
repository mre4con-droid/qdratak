# -*- coding: utf-8 -*-
"""بناء مسار التحصيلي كاملًا: الدورات، المحاكي، بنك الأسئلة، والصفحة الرئيسية،
ثم ربطه من الموقع الرئيسي.

  python3 tools/build_all.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tahsili      # noqa: E402
import build_simulator    # noqa: E402
import build_pages        # noqa: E402
import link_tahsili       # noqa: E402
import build_nav          # noqa: E402
import build_plans        # noqa: E402


def main():
    print("الدورات:")
    build_tahsili.main()
    print("\nالمحاكي:")
    build_simulator.main()
    print("\nالصفحات:")
    build_pages.main()
    print("\nالربط من الموقع الرئيسي:")
    link_tahsili.main()
    build_nav.main()
    build_plans.main()
    print("\nاكتمل البناء.")


if __name__ == "__main__":
    main()
