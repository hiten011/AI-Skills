#!/usr/bin/env python3
"""
job-hunt-cowork :: score_jobs.py  (runs locally in the Cowork sandbox)

Dedupe + heuristic pre-score of every fetched job against the profile, so Claude
only has to read a short shortlist.  The pre-score mirrors career-ops' five
dimensions (CV match, North-Star/title fit, comp, location/culture, red flags)
but is computed mechanically; Claude's review (review.json) overrides it for the
shortlisted roles.

Usage:
  python score_jobs.py --profile profile.json --jobs jobs.json --out scored.json \
      [--previous old_job_hunt.xlsx] [--shortlist 40]

Prints a compact shortlist (one line per job) for Claude to review.
"""
import argparse, json, re, datetime as dt, sys
from collections import Counter

SENIOR = re.compile(r"\b(senior|sr\.?|staff|principal|lead|head|director|vp|chief|architect|manager|intermediate|mid-level|ii|iii|iv|level [2-5])\b", re.I)
JUNIOR = re.compile(r"\b(junior|jr\.?|graduate|grad|entry|intern|internship|trainee|apprentice|associate)\b", re.I)
AGENCY = re.compile(r"\b(our client|on behalf of|recruitment agency|staffing|talent solutions)\b", re.I)
CLEARANCE = re.compile(r"\b(security clearance|baseline clearance|NV1|NV2|TS/SCI|secret clearance|clearance required)\b", re.I)
NO_SPONSOR = re.compile(r"(no (visa )?sponsorship|unable to sponsor|not able to sponsor|must have (full )?(working|work) rights|citizens? only|permanent residents? only)", re.I)

FX_TO_USD = {"USD": 1, "AUD": 0.66, "GBP": 1.27, "EUR": 1.08, "CAD": 0.73, "NZD": 0.6, "INR": 0.012, "SGD": 0.74}
PERIOD_MULT = {"hour": 2000, "day": 230, "week": 46, "month": 12, "year": 1, "": 1}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def canon_url(u):
    u = (u or "").split("#")[0]
    u = re.sub(r"[?&](utm_[^=&]+|ref|refId|trackingId|origin|type|sol|from)=[^&]*", "", u)
    return u.rstrip("?&/").lower()


def key(r):
    loc = norm(r.get("location")).split(" ")[0] if r.get("location") else ""
    comp = re.sub(r"\b(the|pty|ltd|inc|llc|limited|gmbh|co|corp|corporation|group|australia|airways|technologies|technology|labs)\b", "",
                  norm(r.get("company"))).split()
    return f"{comp[0] if comp else ''}|{norm(r.get('title'))}|{loc}"


def days_old(d):
    try:
        return (dt.date.today() - dt.date.fromisoformat(d[:10])).days
    except Exception:
        return None


def annual_usd(v, cur, period):
    if not v:
        return None
    try:
        v = float(v)
    except Exception:
        return None
    p = (period or "year").lower()
    p = "hour" if "hour" in p else "day" if ("day" in p or "daily" in p) else "week" if "week" in p else \
        "month" if "month" in p else "year"
    return v * PERIOD_MULT[p] * FX_TO_USD.get((cur or "").upper(), 1)


def load_previous(path):
    """Read a previous job_hunt_*.xlsx: statuses/notes carry over, repeats get marked, and rows the
    user is acting on (Applied, Interview, ...) are kept even if this search doesn't find them again."""
    prev = {}
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        for sheet in ("All Jobs", "Top Matches", "Skipped"):
            if sheet not in wb.sheetnames:
                continue
            ws = wb[sheet]
            hdr = [str(c.value or "") for c in ws[1]]
            ix = {h: i for i, h in enumerate(hdr)}
            if "Key" not in ix:
                continue
            for row in ws.iter_rows(min_row=2):
                val = lambda h: row[ix[h]].value if h in ix else None
                k = val("Key")
                if not k:
                    continue
                cur = prev.setdefault(k, {"status": "New", "notes": "", "first_seen": "", "row": {}})
                st = val("Status")
                if st and st != "New":
                    cur["status"] = st
                if val("Notes"):
                    cur["notes"] = val("Notes")
                if val("First seen"):
                    cur["first_seen"] = val("First seen")
                link = row[ix["Link"]].hyperlink.target if "Link" in ix and row[ix["Link"]].hyperlink else ""
                data = {"title": val("Job title"), "company": val("Company"), "location": val("Location"),
                        "work_mode": val("Mode"), "salary_text": val("Pay"), "posted_date": val("Posted"),
                        "fit_score": val("Fit (1-5)"), "url": link}
                for f, v in data.items():
                    if v not in (None, "") and not cur["row"].get(f):
                        cur["row"][f] = v
    except Exception as ex:
        print(f"[warn] could not read previous workbook: {ex}", file=sys.stderr)
    return prev


KEEP_STATUSES = {"interested", "applied", "interview", "offer"}


def score(r, P):
    t = P.get("targets", {})
    loc = P.get("location", {})
    comp = P.get("compensation", {})
    skills_core = [s.lower() for s in P.get("skills", {}).get("core", [])]
    skills_sec = [s.lower() for s in P.get("skills", {}).get("secondary", [])]
    pos = [k.lower() for k in t.get("title_keywords_positive", [])] or \
        [w for role in t.get("roles", []) for w in norm(role).split() if len(w) > 2]
    neg = [k.lower() for k in t.get("title_keywords_negative", [])]
    title = (r.get("title") or "").lower()
    text = f"{title} {r.get('description', '')} {r.get('skills_tags', '')}".lower()
    flags, skip = [], []

    # 1) Title / North-Star fit (0-35)
    role_hit = max((sum(w in title for w in norm(role).split()) / max(1, len(norm(role).split())))
                   for role in (t.get("roles") or [""]))
    kw_hit = sum(1 for k in pos if k in title)
    s_title = min(35, 25 * role_hit + 5 * min(kw_hit, 2))
    if any(n in title for n in neg):
        skip.append("title matches an excluded keyword")
    want = {s.lower() for s in t.get("seniority", [])}
    if want and want <= {"internship", "entry", "junior", "graduate", "associate"} and SENIOR.search(title):
        s_title -= 15
        flags.append("seniority above target")
    if want and not (want & {"internship", "entry", "junior", "graduate"}) and JUNIOR.search(title):
        s_title -= 10
        flags.append("seniority below target")

    # 2) Skills / CV match (0-30)
    hits_core = [s for s in skills_core if re.search(r"(?<![a-z])" + re.escape(s) + r"(?![a-z])", text)]
    hits_sec = [s for s in skills_sec if re.search(r"(?<![a-z])" + re.escape(s) + r"(?![a-z])", text)]
    denom = max(1, min(len(skills_core), 8))
    s_skill = min(30, 30 * (len(hits_core) + 0.5 * len(hits_sec)) / denom) if (skills_core or skills_sec) else 15
    if len(r.get("description") or "") < 80:
        s_skill = max(s_skill, 12)  # no JD text: don't punish, judge later

    # 3) Location / work-mode fit (0-15)
    modes = [m.lower() for m in loc.get("work_modes", ["remote", "hybrid", "onsite"])]
    L = f"{r.get('location', '')} {r.get('work_mode', '')}".lower()
    cities = [c.lower() for c in loc.get("cities", [])]
    country = (loc.get("country") or "").lower()
    wm = (r.get("work_mode") or "").lower()
    if "remote" in wm and "remote" in modes:
        generic_remote = not re.sub(r"\b(remote|remoto|anywhere|worldwide|global|work from home|wfh)\b|[^a-z]", "",
                                    str(r.get("location") or "").lower())
        if not country or country in L or any(c in L for c in cities) or generic_remote \
                or re.search(r"\b(anywhere|worldwide|global)\b", L):
            s_loc = 15
        else:  # remote, but the posting names other countries/regions (e.g. "United States", "North America")
            s_loc = 3
            flags.append("remote, but listed for another country/region")
    elif any(c in L for c in cities):
        s_loc = 15 if (not wm or wm.replace("-", "") in [m.replace("-", "") for m in modes] or "onsite" in modes) else 8
    elif country and country in L:
        s_loc = 10 if loc.get("open_to_relocation") or not cities else 6
    elif not r.get("location"):
        s_loc = 7
    else:
        s_loc = 3 if loc.get("open_to_relocation") else 0
        flags.append("location outside preferences")
    if "remote" not in modes and "remote" in wm and not any(c in L for c in cities):
        s_loc = min(s_loc, 8)

    # 4) Comp (0-10)
    cur = r.get("salary_currency") or comp.get("currency") or ""
    smax = annual_usd(r.get("salary_max") or r.get("salary_min"), cur, r.get("salary_period"))
    floor = annual_usd(comp.get("minimum"), comp.get("currency"), comp.get("period", "year"))
    target = annual_usd(comp.get("target"), comp.get("currency"), comp.get("period", "year"))
    if smax is None or not floor:
        s_comp = 5
    elif target and smax >= target:
        s_comp = 10
    elif smax >= floor:
        s_comp = 7
    else:
        s_comp = 1
        flags.append("advertised pay below your minimum")

    # 5) Recency (0-10)
    age = days_old(r.get("posted_date") or "")
    s_rec = 5 if age is None else 10 if age <= 3 else 8 if age <= 7 else 6 if age <= 14 else 4 if age <= 30 else 1
    if age is not None and age > 60:
        flags.append(f"posted {age} days ago (possible ghost job)")

    # Red flags / dealbreakers (career-ops Block G + work-auth checks)
    desc = r.get("description") or ""
    if AGENCY.search(desc):
        flags.append("recruiter/agency listing (end employer may be hidden)")
    if CLEARANCE.search(desc) and not P.get("candidate", {}).get("has_clearance"):
        if any("clearance" in d.lower() for d in P.get("dealbreakers", [])):
            skip.append("dealbreaker: security clearance required")
        else:
            flags.append("security clearance required")
    if NO_SPONSOR.search(desc) and P.get("candidate", {}).get("needs_sponsorship"):
        skip.append("no visa sponsorship and you need sponsorship")
    for db in P.get("dealbreakers", []):
        d = db.lower().strip()
        if d and len(d) > 3 and d in text:
            skip.append(f"dealbreaker: {db}")
    if not r.get("verified", True):
        flags.append("found via web search, confirm it's still open")
    m = re.search(r"(\d+)\+?\s*applicants|over (\d+) applicants", str(r.get("applicants") or ""), re.I)
    if m and int(m.group(1) or m.group(2)) >= 200:
        flags.append("200+ applicants")

    total = max(0, s_title) + s_skill + s_loc + s_comp + s_rec
    fit = round(min(5.0, 1 + total / 25), 1)
    # career-ops geo-mismatch rule: a role you can't take is never a good match, whatever the skills
    if "location outside preferences" in flags and not loc.get("open_to_relocation"):
        fit = min(fit, 2.9)
    elif "remote, but listed for another country/region" in flags:
        fit = min(fit, 3.4)
    if any(f.startswith("seniority") for f in flags):
        fit = min(fit, 3.6)
    legit = "Suspicious" if (age and age > 90) else "Proceed with caution" if any(
        x in " ".join(flags) for x in ("ghost", "agency", "web search")) else "High confidence"
    if skip:
        verdict = "Skip"
    elif fit >= 4.5:
        verdict = "Strong match, apply"
    elif fit >= 4.0:
        verdict = "Good match, worth applying"
    elif fit >= 3.5:
        verdict = "Decent, apply if there's a reason"
    else:
        verdict = "Weak fit"
    r.update({
        "prescore": round(total, 1), "fit_score": fit, "verdict": verdict, "legitimacy": legit,
        "matched_skills": ", ".join(hits_core + hits_sec), "flags": "; ".join(dict.fromkeys(flags)),
        "skip_reason": "; ".join(skip), "age_days": age,
        "score_breakdown": f"title {max(0, s_title):.0f}/35 · skills {s_skill:.0f}/30 · location {s_loc:.0f}/15 · pay {s_comp}/10 · recency {s_rec}/10",
        "reviewed": False,
    })
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--jobs", required=True, nargs="+", help="one or more jobs_*.json from fetch_jobs.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--previous", help="previous job_hunt_*.xlsx to carry statuses and mark repeats")
    ap.add_argument("--shortlist", type=int, default=40)
    a = ap.parse_args()

    P = json.load(open(a.profile))
    recs, logs, runs = [], [], []
    for p in a.jobs:
        d = json.load(open(p))
        recs += d.get("records", [])
        logs += d.get("log", [])
        runs.append(d.get("run_id"))

    # Dedupe: canonical URL first, then company+title+city; keep the richest record, merge sources.
    by_key, url_to_key = {}, {}
    for r in recs:
        if not r.get("title"):
            continue
        k, cu = key(r), canon_url(r.get("url"))
        k = url_to_key.get(cu, k) if cu else k
        if k in by_key:
            cur = by_key[k]
            srcs = set(cur["sources"].split(", ")) | {r["source"]}
            richer = len(r.get("description") or "") > len(cur.get("description") or "")
            for f, v in r.items():
                if v and (not cur.get(f) or (f == "description" and richer)):
                    cur[f] = v
            cur["sources"] = ", ".join(sorted(srcs))
            cur["verified"] = cur.get("verified", True) or r.get("verified", True)
        else:
            r["sources"] = r["source"]
            by_key[k] = r
        if cu:
            url_to_key[cu] = k

    # Postings with a blank company (some boards hide it) merge into a same-title, same-city posting that has one
    named = {}
    for k in by_key:
        c, t, l = k.split("|", 2)
        if c:
            named.setdefault(f"{t}|{l}", []).append(k)
    for k in [k for k in list(by_key) if k.startswith("|")]:
        cands = named.get(k[1:], [])
        if len(cands) == 1:
            tgt, r = by_key[cands[0]], by_key.pop(k)
            tgt["sources"] = ", ".join(sorted(set(tgt["sources"].split(", ")) | set(r["sources"].split(", "))))
            for f, v in r.items():
                if v and not tgt.get(f):
                    tgt[f] = v

    prev = load_previous(a.previous) if a.previous else {}
    today = dt.date.today().isoformat()
    out = []
    for k, r in by_key.items():
        r["key"] = k
        score(r, P)
        if k in prev:
            r["is_new"] = "Seen before"
            r["status"] = prev[k].get("status") or "New"
            r["notes"] = prev[k].get("notes") or ""
            r["first_seen"] = str(prev[k].get("first_seen") or today)[:10]
        else:
            r["is_new"], r["status"], r["notes"], r["first_seen"] = "New", "New", "", today
        out.append(r)

    # Keep jobs the user is acting on, even if this search didn't surface them again
    for k, p in prev.items():
        if k in by_key or str(p.get("status", "")).lower() not in KEEP_STATUSES:
            continue
        d = p.get("row", {})
        out.append({"key": k, "title": d.get("title") or k.split("|")[1], "company": d.get("company") or "",
                    "location": d.get("location") or "", "work_mode": d.get("work_mode") or "",
                    "salary_text": d.get("salary_text") or "", "posted_date": str(d.get("posted_date") or "")[:10],
                    "url": d.get("url") or "", "sources": "Previous tracker", "source": "Previous tracker",
                    "fit_score": float(d.get("fit_score") or 3.0), "prescore": 0,
                    "verdict": "Tracking (not in this search)", "legitimacy": "", "matched_skills": "",
                    "flags": "not found in this search; may be closed", "skip_reason": "", "age_days": None,
                    "score_breakdown": "", "reviewed": False, "is_new": "Carried over", "status": p["status"],
                    "notes": p.get("notes") or "", "first_seen": str(p.get("first_seen") or "")[:10], "description": ""})

    # Posting-age filter from the profile (undated postings pass: career-ops rule)
    max_age = P.get("search", {}).get("posted_within_days")
    for r in out:
        if max_age and r["age_days"] is not None and r["age_days"] > max(max_age * 2, 30) and r["verdict"] != "Skip":
            r["verdict"], r["skip_reason"] = "Skip", f"older than {max(max_age * 2, 30)} days"

    out.sort(key=lambda r: (r["verdict"] == "Skip", -r["fit_score"], r["age_days"] if r["age_days"] is not None else 99))
    json.dump({"runs": runs, "generated": today, "records": out, "log": logs}, open(a.out, "w"), indent=1, default=str)

    live = [r for r in out if r["verdict"] != "Skip"]
    print(f"Total unique: {len(out)} | candidates: {len(live)} | skipped: {len(out) - len(live)} | "
          f"sources: {dict(Counter(s.strip() for r in out for s in r['sources'].split(',')))}")
    print(f"--- SHORTLIST (top {a.shortlist}) : key || fit || title || company || location || mode || pay || age || matched || flags")
    for r in live[: a.shortlist]:
        pay = r.get("salary_text") or (f"{r.get('salary_min')}-{r.get('salary_max')}" if r.get("salary_min") else "")
        print(f"{r['key']} || {r['fit_score']} || {r['title'][:70]} || {r['company'][:40]} || {r['location'][:40]} || "
              f"{r['work_mode']} || {pay[:30]} || {r['age_days']} || {r['matched_skills'][:60]} || {r['flags'][:90]}")


if __name__ == "__main__":
    main()
