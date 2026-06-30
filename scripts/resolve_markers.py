#!/usr/bin/env python3
"""
Strip git conflict markers from state/queue files, keeping a valid result.
For each file passed (or every tracked file with markers if none given), drop the
"theirs" + base sections and keep "ours"; for .json verify it parses. Used to
recover after a rebase leaves markers in the runtime JSON state files.

  python3 scripts/resolve_markers.py                 # auto-find + fix all
  python3 scripts/resolve_markers.py path1 path2 ...  # fix specific files
"""
import json, subprocess, sys, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def find():
    r = subprocess.run(["git", "grep", "-lE", r"^<<<<<<< |^>>>>>>> |^\|\|\|\|\|\|\| "],
                       cwd=ROOT, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def strip(path):
    out, state = [], 0   # 0 normal, 1 ours, 2 theirs, 3 base
    for ln in open(os.path.join(ROOT, path)):
        s = ln.rstrip("\n")
        if s.startswith("<<<<<<< "):
            state = 1; continue
        if s.startswith("|||||||"):
            state = 3; continue
        if s == "=======" and state in (1, 3):
            state = 2; continue
        if s.startswith(">>>>>>> "):
            state = 0; continue
        if state in (0, 1):
            out.append(ln)
    return "".join(out)


def main():
    files = sys.argv[1:] or find()
    if not files:
        print("no conflict markers found"); return
    for f in files:
        text = strip(f)
        if f.endswith(".json"):
            try:
                json.loads(text)
            except Exception as e:
                print(f"  {f}: STILL INVALID after strip -> {e}"); continue
        open(os.path.join(ROOT, f), "w").write(text)
        print(f"  {f}: resolved")


if __name__ == "__main__":
    main()
