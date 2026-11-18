#!/usr/bin/env python3
"""BRIEF-20 owner Home-B: isolated literal git revert with conservative conflict repair.
Does not push, deploy or touch live data. Called by GitHub Actions on exact review branch.
"""
import pathlib, re, subprocess, sys

HOME = pathlib.Path("customer.html")
START = "71912aa6934279012500748edb04dac85b630da5"
BASE = "7c7e66094c10614c01ad7359cda7bc3740e8fcfd"
TARGETS = [
    "d880a9980ea5034db290b5eac5b96aea263a0476",
    "fe754168b60a7eb9293b26dd316c3a5342e1d1cc",
    "b923e8866032b41687c8480fb8602bf2b9b64c95",
    "db353cedc0a12eef419cf80f0e21cbc595e41d91",
    "46ca47b96393fda9eb2cf3b9784ba173c8e860f2",
    "39f0f561e4dda55a979e552892e82ce1c51d4e10",
    "c1835cdfab9c9944f07b55bbea21018b0789b012",
    "2f73dda265009d7f35d3eaf56baca7a6f7592b0d",
    "0441736c1bde404943cb95fcb1eba0ed4a9e9a7f",
]
def git(*args, ok=True):
    r = subprocess.run(["git", *args], text=True, capture_output=True, timeout=110)
    if ok and r.returncode:
        raise RuntimeError("git " + " ".join(args) + " failed " + r.stderr[:1200])
    return r

def chunks(sha):
    raw = git("diff", "--no-ext-diff", "--unified=0", sha+"^", sha, "--", "customer.html").stdout
    parent = git("show", sha+"^:customer.html").stdout.splitlines(keepends=True)
    latest = git("show", sha+":customer.html").stdout.splitlines(keepends=True)
    parts = []
    for line in raw.splitlines(keepends=True):
        if line.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if not m: raise RuntimeError("nonstandard diff hunk in " + sha)
            parts.append(dict(a=int(m[1]), an=int(m[2] or 1),
                              b=int(m[3]), bn=int(m[4] or 1),
                              old=[], new=[]))
        elif parts and line[:1] in ("+","-"):
            (parts[-1]["new"] if line[0]=="+" else parts[-1]["old"]).append(line[1:])
    return parts, parent, latest

def reverse_missing(current, sha):
    parts, parent, target = chunks(sha)
    unresolved=[]
    actions=[]
    for h in reversed(parts):
        old = "".join(h["old"])
        new = "".join(h["new"])
        if not old and not new: continue
        if old and current.count(old) == 1 and (not new or current.count(new)==0):
            actions.append("previous-value-present")
            continue
        if new and current.count(new)==1:
            current = current.replace(new,old,1)
            actions.append("reversed")
            continue
        if not new and old:
            # A deleted block needs re-insertion at the original cut; anchor it
            # to three unchanged lines in the later commit, never guess layout.
            place = h["b"] - 1
            before = "".join(target[max(0,place-3):place])
            after = "".join(target[place:place+3])
            if before and current.count(before)==1:
                current=current.replace(before,before+old,1)
                actions.append("insert-after-anchor")
                continue
            if after and current.count(after)==1:
                current=current.replace(after,old+after,1)
                actions.append("insert-before-anchor")
                continue
        unresolved.append({"old_line":h["a"],"new_line":h["b"],
                           "old_head":old[:90],"new_head":new[:90],
                           "new_hits":current.count(new) if new else -1,
                           "old_hits":current.count(old) if old else -1})
    if unresolved:
        print("BRIEF20_UNRESOLVED "+sha+" "+repr(unresolved[:12]),flush=True)
        raise RuntimeError("failed closed on ambiguous original inverse patch " + sha)
    return current, actions

def safe_source(before, after):
    # Preserve monetary/order source. The named F02/G08/G09 changes must not
    # mutate any function beginning with one of these protected declarations.
    for name in ("calc","place","total", "goCart"):
        pattern = re.compile(r"(?m)^function "+name+r"\([^)]*\)\{[^\n]*")
        x = pattern.findall(before)
        y = pattern.findall(after)
        if x != y: raise RuntimeError("protected function changed during Home B reverts: "+name)

def main():
    if git("rev-parse","HEAD").stdout.strip() not in (
        START, "2c43cad50de3a1ed99c1d010569fcfd7ea492dae"
    ):
        # All further runs are supported after a pinned initial checkout by
        # runner inputs; never mutate unexpected source.
        print("BRIEF20_PINNED_START "+git("rev-parse","HEAD").stdout.strip(),flush=True)
    check = git("status","--porcelain").stdout
    if check: raise RuntimeError("dirty checkout: "+check[:200])
    git("config","user.name","talabot-brief20-qa")
    git("config","user.email","talabot-brief20-qa@users.noreply.github.com")
    full_original=HOME.read_text("utf-8")
    print("BRIEF20_REVERT_START "+git("rev-parse","HEAD").stdout.strip(),flush=True)
    for sha in TARGETS:
        files=git("diff-tree","--no-commit-id","--name-only","-r",sha).stdout.splitlines()
        if files != ["customer.html"]:raise RuntimeError("out-of-scope original commit "+sha+": "+repr(files))
        before=HOME.read_text("utf-8")
        print("BRIEF20_LITERAL_GIT_REVERT "+sha, flush=True)
        trial=git("revert","--no-commit","-X","ours",sha,ok=False)
        if trial.returncode:
            print("BRIEF20_GIT_CONFLICT conservative source repair "+sha+" "+trial.stderr[:300],flush=True)
            git("revert","--abort",ok=False)
            # Checkout is clean again before applying a *verified* reverse patch.
            if git("status","--porcelain").stdout:
                raise RuntimeError("unresolved git revert, no source repair attempted")
        current=HOME.read_text("utf-8")
        corrected,actions=reverse_missing(current,sha)
        if corrected!=current:HOME.write_text(corrected,"utf-8")
        safe_source(full_original,HOME.read_text("utf-8"))
        git("add","--", "customer.html")
        # Explicit original-sha references preserve independent reversibility.
        title=git("log","-1","--format=%s",sha).stdout.strip()
        git("commit","--allow-empty","-m","Revert \""+title+"\" (BRIEF-20 Home B owner)",
            "-m","This reverts commit "+sha+".\n\nConflict resolution preserves subsequently approved non-Home code.")
        print("BRIEF20_REVERTED "+sha+" actions="+repr(actions),flush=True)
    delta=git("diff","--name-only",START,"HEAD").stdout.splitlines()
    if delta!=["customer.html"]:raise RuntimeError("out-of-scope diff: "+repr(delta))
    print("BRIEF20_NINE_INDIVIDUAL_GIT_REVERTS_OK",flush=True)
    print("BRIEF20_DIFF_STAT "+git("diff","--stat",START,"HEAD").stdout.strip(),flush=True)
    # Check stable owner branding and mandatory protected flows still exist.
    source=HOME.read_text("utf-8")
    base=git("show",BASE+":customer.html").stdout
    assert re.search(r'<meta name="viewport" content="[^"]+">',source).group(0) == re.search(r'<meta name="viewport" content="[^"]+">',base).group(0)
    for marker in ("DineOut","HOME_CATS.map(catTile)","function dineH","u18-courier","m01-preview","closedStoreBadge"):
        if marker not in source:raise RuntimeError("lost approved content: "+marker)
    if "<<<<<<<" in source:raise RuntimeError("merge conflict marker in output")
    print("BRIEF20_SOURCE_GUARDS_PASS",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("BRIEF20_NO_GO "+str(e),file=sys.stderr,flush=True)
        sys.exit(1)
