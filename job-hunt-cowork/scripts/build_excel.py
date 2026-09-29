#!/usr/bin/env python3
"""
job-hunt-cowork :: build_excel.py  (runs locally in the Cowork sandbox)

Builds the job tracker workbook:
  Dashboard     KPIs (live formulas), source + verdict breakdown, top 10
  Top Matches   reviewed/high-fit roles, sorted, with why / gaps / next step
  All Jobs      every unique posting (filterable), Status dropdown, Notes
  Skipped       filtered-out roles and the reason (transparency)
  Search Log    every query per source: status, count, errors
  Profile       the search profile (also stored as JSON so the next run can
                restore memory from this file alone)

Usage:
  python build_excel.py --profile profile.json --scored scored.json \
      [--review review.json] --out /mnt/user-data/outputs/job_hunt_2026-09-29.xlsx
"""
import argparse, json, datetime as dt, os, subprocess, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

FONT = "Arial"
INK, MUTED, ACCENT, HEAD_BG, BAND = "1F2937", "6B7280", "2563EB", "1F3A5F", "F3F6FA"
H_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=10)
H_FILL = PatternFill("solid", fgColor=HEAD_BG)
B_FONT = Font(name=FONT, size=10, color=INK)
LINK = Font(name=FONT, size=10, color=ACCENT, underline="single")
THIN = Border(bottom=Side(style="thin", color="E5E7EB"))
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")
STATUSES = ["New", "Interested", "Applied", "Interview", "Offer", "Rejected", "Not interested", "Closed"]


def header(ws, cols, row=1):
    for i, (name, width) in enumerate(cols, 1):
        c = ws.cell(row=row, column=i, value=name)
        c.font, c.fill = H_FONT, H_FILL
        c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[row].height = 30
    ws.freeze_panes = ws.cell(row=row + 1, column=3)


def pay(r):
    if r.get("salary_text"):
        return str(r["salary_text"])[:60]
    if r.get("salary_min"):
        a, b = r["salary_min"], r.get("salary_max")
        cur = r.get("salary_currency") or ""
        f = lambda x: f"{float(x):,.0f}"
        return f"{cur} {f(a)}{' - ' + f(b) if b else ''} {r.get('salary_period') or ''}".strip()
    return ""


def put(ws, row, values, wrap_cols=(), link_col=None, url=None):
    for i, v in enumerate(values, 1):
        c = ws.cell(row=row, column=i, value=v)
        c.font, c.border = B_FONT, THIN
        c.alignment = WRAP if i in wrap_cols else TOP
    if link_col and url:
        c = ws.cell(row=row, column=link_col)
        c.hyperlink, c.font = url, LINK


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--scored", required=True)
    ap.add_argument("--review", help="Claude's review.json (list of {key, fit_score, verdict, why, gaps, legitimacy, archetype, next_step})")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-recalc", action="store_true")
    a = ap.parse_args()

    P = json.load(open(a.profile))
    S = json.load(open(a.scored))
    recs = S["records"]
    rev = {}
    if a.review and os.path.exists(a.review):
        for x in json.load(open(a.review)):
            rev[x["key"]] = x
    for r in recs:
        x = rev.get(r["key"])
        if x:
            for f in ("fit_score", "verdict", "why", "gaps", "legitimacy", "archetype", "next_step"):
                if x.get(f) not in (None, ""):
                    r[f] = x[f]
            r["reviewed"] = True
            if x.get("verdict", "").lower().startswith("skip"):
                r["skip_reason"] = r.get("skip_reason") or x.get("gaps") or "Claude review: skip"
    min_score = float(P.get("search", {}).get("min_score", 3.5))
    live = [r for r in recs if not str(r.get("verdict", "")).startswith("Skip")]
    skipped = [r for r in recs if str(r.get("verdict", "")).startswith("Skip")]
    live.sort(key=lambda r: (-(r.get("reviewed") is True), -float(r["fit_score"]), r.get("age_days") if r.get("age_days") is not None else 99))
    top = [r for r in live if float(r["fit_score"]) >= min_score or r.get("reviewed")]
    top.sort(key=lambda r: (-float(r["fit_score"]), r.get("age_days") if r.get("age_days") is not None else 99))

    wb = Workbook()
    dash = wb.active
    dash.title = "Dashboard"

    # ---------------- Top Matches
    ws = wb.create_sheet("Top Matches")
    cols = [("#", 5), ("Fit (1-5)", 9), ("Verdict", 22), ("Job title", 34), ("Company", 22), ("Location", 22),
            ("Mode", 10), ("Pay", 20), ("Posted", 11), ("Why it fits", 48), ("Gaps / red flags", 40),
            ("Posting check", 15), ("Next step", 30), ("Source(s)", 16), ("Link", 10), ("Status", 13), ("Notes", 28), ("Key", 6)]
    header(ws, cols)
    for i, r in enumerate(top, 1):
        why = r.get("why") or (f"Matched: {r['matched_skills']}" if r.get("matched_skills") else "") + \
            (f"  [{r['score_breakdown']}]" if not r.get("reviewed") else "")
        gaps = "; ".join(x for x in [r.get("gaps"), r.get("flags")] if x)
        put(ws, i + 1, [i, float(r["fit_score"]), r["verdict"], r["title"], r["company"], r["location"], r.get("work_mode"),
                        pay(r), r.get("posted_date") or "", why.strip(), gaps, r.get("legitimacy"), r.get("next_step", ""),
                        r.get("sources"), "Open" if r.get("url") else "", r.get("status", "New"), r.get("notes", ""), r["key"]],
            wrap_cols=(4, 10, 11, 13), link_col=15, url=r.get("url"))
    n_top = len(top)
    if n_top:
        ws.conditional_formatting.add(f"B2:B{n_top + 1}", ColorScaleRule(start_type="num", start_value=2.5, start_color="F8D7DA",
                                                                          mid_type="num", mid_value=3.8, mid_color="FFF3CD",
                                                                          end_type="num", end_value=5, end_color="C6EFCE"))
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{max(2, n_top + 1)}"
    ws.column_dimensions["R"].hidden = True
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"P2:P{max(2, n_top + 500)}")

    # ---------------- All Jobs
    wa = wb.create_sheet("All Jobs")
    cols_a = [("Fit (1-5)", 9), ("Verdict", 22), ("Job title", 34), ("Company", 22), ("Location", 22), ("Mode", 10),
              ("Type", 12), ("Seniority", 12), ("Pay", 20), ("Posted", 11), ("Age (days)", 8), ("Source(s)", 16),
              ("Matched skills", 30), ("Flags", 34), ("Score breakdown", 36), ("Posting check", 15), ("New?", 10),
              ("Link", 8), ("Apply link", 9), ("Applicants", 12), ("Status", 13), ("Notes", 24), ("First seen", 11),
              ("Description (excerpt)", 60), ("Key", 30)]
    header(wa, cols_a)
    for i, r in enumerate(live, 2):
        put(wa, i, [float(r["fit_score"]), r["verdict"], r["title"], r["company"], r["location"], r.get("work_mode"),
                    r.get("employment_type"), r.get("seniority"), pay(r), r.get("posted_date") or "", r.get("age_days"),
                    r.get("sources"), r.get("matched_skills"), r.get("flags"), r.get("score_breakdown"), r.get("legitimacy"),
                    r.get("is_new"), "Open" if r.get("url") else "", "Apply" if r.get("apply_url") else "",
                    r.get("applicants"), r.get("status", "New"), r.get("notes", ""), r.get("first_seen"),
                    (r.get("description") or "")[:600], r["key"]], wrap_cols=(3,), link_col=18, url=r.get("url"))
        if r.get("apply_url"):
            c = wa.cell(row=i, column=19)
            c.hyperlink, c.font = r["apply_url"], LINK
        wa.row_dimensions[i].height = 30
    n_all = len(live)
    if n_all:
        wa.conditional_formatting.add(f"A2:A{n_all + 1}", ColorScaleRule(start_type="num", start_value=2.5, start_color="F8D7DA",
                                                                          mid_type="num", mid_value=3.8, mid_color="FFF3CD",
                                                                          end_type="num", end_value=5, end_color="C6EFCE"))
        wa.conditional_formatting.add(f"Q2:Q{n_all + 1}", FormulaRule(formula=[f'$Q2="New"'], font=Font(name=FONT, bold=True, color="047857")))
    wa.auto_filter.ref = f"A1:{get_column_letter(len(cols_a))}{max(2, n_all + 1)}"
    dv2 = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
    wa.add_data_validation(dv2)
    dv2.add(f"U2:U{max(2, n_all + 500)}")

    # ---------------- Skipped
    wsk = wb.create_sheet("Skipped")
    header(wsk, [("Job title", 36), ("Company", 24), ("Location", 24), ("Why skipped", 50), ("Fit (1-5)", 9), ("Source", 16), ("Link", 8), ("Key", 6)])
    for i, r in enumerate(skipped, 2):
        put(wsk, i, [r["title"], r["company"], r["location"], r.get("skip_reason") or r.get("flags"), float(r["fit_score"]),
                     r.get("sources"), "Open" if r.get("url") else "", r["key"]], wrap_cols=(4,), link_col=7, url=r.get("url"))
    wsk.auto_filter.ref = f"A1:H{max(2, len(skipped) + 1)}"
    wsk.column_dimensions["H"].hidden = True

    # ---------------- Search Log
    wl = wb.create_sheet("Search Log")
    header(wl, [("Source", 26), ("Query / URL", 60), ("Status", 10), ("Results", 9), ("Seconds", 9), ("Error", 70)])
    for i, l in enumerate(S.get("log", []), 2):
        put(wl, i, [l.get("source"), l.get("query"), l.get("status"), l.get("count"), l.get("seconds"), l.get("error", "")], wrap_cols=(2, 6))

    # ---------------- Profile (doubles as portable memory)
    wp = wb.create_sheet("Profile")
    header(wp, [("Field", 28), ("Value", 90)])
    wp.freeze_panes = "A2"

    def flat(d, pre=""):
        for k, v in d.items():
            if isinstance(v, dict):
                yield from flat(v, f"{pre}{k}.")
            elif isinstance(v, list):
                yield f"{pre}{k}", "; ".join(json.dumps(x) if isinstance(x, dict) else str(x) for x in v)
            else:
                yield f"{pre}{k}", v
    row = 2
    for k, v in flat(P):
        put(wp, row, [k, str(v) if v is not None else ""], wrap_cols=(2,))
        row += 1
    row += 1
    put(wp, row, ["PROFILE_JSON (do not edit)", json.dumps(P, ensure_ascii=False)[:32000]], wrap_cols=())
    wp.cell(row=row, column=1).font = Font(name=FONT, size=9, color=MUTED, italic=True)
    wp.cell(row=row, column=2).font = Font(name=FONT, size=8, color=MUTED)
    wp.row_dimensions[row].height = 15

    # ---------------- Dashboard (formulas so it stays live as Status changes)
    d = dash
    d.sheet_view.showGridLines = False
    d.column_dimensions["A"].width = 2
    for col, w in zip("BCDEFGH", (30, 14, 4, 30, 14, 4, 30)):
        d.column_dimensions[col].width = w
    name = P.get("candidate", {}).get("name") or "Job search"
    d["B2"] = f"Job Hunt: {name}"
    d["B2"].font = Font(name=FONT, size=18, bold=True, color=INK)
    t = P.get("targets", {})
    L = P.get("location", {})
    d["B3"] = (f"{', '.join(t.get('roles', [])[:4])} · {', '.join(L.get('cities', []) or [L.get('country', '')])} · "
               f"{'/'.join(L.get('work_modes', []))} · run {dt.date.today().isoformat()}")
    d["B3"].font = Font(name=FONT, size=10, color=MUTED)

    kpis = [("Unique jobs found", f"=COUNTA('All Jobs'!C2:C{n_all + 1})"),
            ("New since last run", f"=COUNTIF('All Jobs'!Q2:Q{n_all + 1},\"New\")"),
            (f"Top matches (fit >= {min_score})", f"=COUNTA('Top Matches'!D2:D{max(2, n_top + 1)})"),
            ("Strong (4.5+)", f"=COUNTIF('All Jobs'!A2:A{n_all + 1},\">=4.5\")"),
            ("Applied", f"=COUNTIF('All Jobs'!U2:U{n_all + 1},\"Applied\")+COUNTIF('Top Matches'!P2:P{max(2, n_top + 1)},\"Applied\")"),
            ("Interviews", f"=COUNTIF('All Jobs'!U2:U{n_all + 1},\"Interview\")+COUNTIF('Top Matches'!P2:P{max(2, n_top + 1)},\"Interview\")"),
            ("Skipped (dealbreakers/filters)", f"=COUNTA(Skipped!A2:A{max(2, len(skipped) + 1)})")]
    r0 = 5
    for i, (lab, f) in enumerate(kpis):
        rr = r0 + i
        d.cell(row=rr, column=2, value=lab).font = Font(name=FONT, size=10, color=MUTED)
        c = d.cell(row=rr, column=3, value=f)
        c.font = Font(name=FONT, size=12, bold=True, color=INK)
        c.alignment = Alignment(horizontal="right")

    # by source (counts per primary source label; formulas count in Source(s) column)
    d.cell(row=4, column=5, value="Jobs by source").font = Font(name=FONT, bold=True, color=INK)
    srcs = sorted({s.strip() for r in live for s in str(r.get("sources", "")).split(",") if s.strip()})
    for i, s in enumerate(srcs):
        d.cell(row=r0 + i, column=5, value=s).font = B_FONT
        d.cell(row=r0 + i, column=6, value=f"=COUNTIF('All Jobs'!L2:L{n_all + 1},\"*{s}*\")").font = B_FONT

    d.cell(row=4, column=8, value="Verdicts").font = Font(name=FONT, bold=True, color=INK)
    verdicts = ["Strong match, apply", "Good match, worth applying", "Decent, apply if there's a reason", "Weak fit"]
    for i, v in enumerate(verdicts):
        d.cell(row=r0 + i, column=8, value=v).font = B_FONT
        c = d.cell(row=r0 + i, column=9, value=f"=COUNTIF('All Jobs'!B2:B{n_all + 1},\"{v}\")")
        c.font = B_FONT
    d.column_dimensions["I"].width = 8

    tr = r0 + max(len(kpis), len(srcs)) + 2
    d.cell(row=tr, column=2, value="Top 10 to look at first").font = Font(name=FONT, bold=True, size=12, color=INK)
    for j, h in enumerate(["Role", "Fit", "", "Company", "Pay", "", "Why"]):
        if h:
            c = d.cell(row=tr + 1, column=2 + j, value=h)
            c.font, c.fill = H_FONT, H_FILL
    for i, r in enumerate(top[:10]):
        rr = tr + 2 + i
        c = d.cell(row=rr, column=2, value=r["title"][:60])
        if r.get("url"):
            c.hyperlink, c.font = r["url"], LINK
        else:
            c.font = B_FONT
        d.cell(row=rr, column=3, value=float(r["fit_score"])).font = Font(name=FONT, bold=True, color=INK)
        d.cell(row=rr, column=5, value=r["company"][:40]).font = B_FONT
        d.cell(row=rr, column=6, value=pay(r)[:24]).font = B_FONT
        w = d.cell(row=rr, column=8, value=(r.get("why") or r.get("matched_skills") or "")[:160])
        w.font, w.alignment = Font(name=FONT, size=9, color=MUTED), Alignment(wrap_text=True, vertical="top")
        d.row_dimensions[rr].height = 30
    d.column_dimensions["H"].width = 70
    note_r = tr + 13
    d.cell(row=note_r, column=2, value="Status dropdowns live in Top Matches (col P) and All Jobs (col U). The counts above update as you change them. "
                                       "Next run: attach this file so new jobs are marked and your statuses carry over.").font = Font(name=FONT, size=9, italic=True, color=MUTED)

    for wsx in wb.worksheets:
        wsx.sheet_properties.tabColor = {"Dashboard": "2563EB", "Top Matches": "10B981"}.get(wsx.title, "9CA3AF")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print(f"Saved {a.out} | top={n_top} all={n_all} skipped={len(skipped)} log={len(S.get('log', []))}")

    if not a.no_recalc:  # cache formula values so previews/pandas show numbers
        for rc in ("/mnt/skills/public/xlsx/scripts/recalc.py",):
            if os.path.exists(rc):
                try:
                    out = subprocess.run([sys.executable, rc, a.out, "60"], capture_output=True, text=True, timeout=120)
                    print("recalc:", out.stdout.strip()[:300] or out.stderr.strip()[:300])
                except Exception as ex:
                    print("recalc skipped:", ex)
                break


if __name__ == "__main__":
    main()
