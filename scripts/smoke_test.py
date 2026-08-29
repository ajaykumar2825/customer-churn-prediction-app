"""Headless smoke test: executes each app page through Streamlit's test harness.

Usage (from repo root):  python scripts/smoke_test.py [page_name ...]
Prints PASS/FAIL per page and exits non-zero if any page raises.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

DEFAULT_PAGES = ["main.py"] + sorted(str(p.relative_to(ROOT)) for p in (ROOT / "pages").glob("*.py"))


def main() -> int:
    targets = sys.argv[1:] or DEFAULT_PAGES
    failed = 0
    for rel in targets:
        path = ROOT / rel
        print(f">> {rel} ...", flush=True)
        at = AppTest.from_file(str(path), default_timeout=300)
        at.run()
        if at.exception:
            failed += 1
            for exc in at.exception:
                print(f"    FAIL {rel}: {exc.value} {exc.stack_trace}")
        else:
            print(f"    OK {rel}: {len(at.main)} elements rendered")
    if failed:
        print(f"\n{failed} page(s) failed")
        return 1
    print("\nAll pages rendered cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())