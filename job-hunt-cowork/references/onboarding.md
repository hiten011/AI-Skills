# Onboarding: ask only what's missing

Goal: a complete `profile.json` (schema: `assets/profile.example.json`) in **at most two
AskUserQuestion rounds**. Derive options from what you already know, such as the CV or memory,
so the user mostly clicks. Everything has an "Other" free-text option automatically.

## Round 1 (always, unless already known): up to 4 questions

| # | Header | Question | Options (derive from the CV where possible) | multiSelect |
|---|--------|----------|-----------------------------------------------|-------------|
| 1 | Roles | Which roles should I search for? | 3–4 titles inferred from the CV's recent titles and skills, e.g. "Software Engineer", "AI/ML Engineer", "Data Analyst" | yes |
| 2 | Location | Where can you work? | "<CV city> (on-site/hybrid)", "Remote within <country>", "Remote worldwide", "Open to relocating" | yes |
| 3 | Level | What level are you targeting? | "Internship / graduate", "Junior (0–2 yrs)", "Mid (2–5 yrs)", "Senior (5+)" (recommend the one matching CV years) | yes |
| 4 | CV | Can you share your CV so I can score fit properly? | "I'll attach it now (Recommended)", "Use my LinkedIn headline + what I tell you", "Skip, just match on titles" | no |

If a CV is already attached, replace Q4 with **Pay**: "What's your minimum annual pay?", with
3 bands in local currency around the market for the role and level, plus "Skip pay filtering".

## Round 2 (only if still missing): up to 4 questions

| Header | Question | Options |
|--------|----------|---------|
| Pay | Minimum / target pay? | 3 local-currency bands + "Skip" |
| Freshness | How recent should postings be? | "Last 7 days", "Last 14 days (Recommended)", "Last 30 days" |
| Avoid | Anything to exclude? (multiSelect) | "Security clearance roles", "Recruiter/agency posts", "Contract/temp", "Unpaid/commission-only" |
| Companies | Any dream companies to track directly? | "No, just search broadly", "Yes, I'll list them" (then ask for names; resolve ATS slugs, see below) |

Work rights and sponsorship: ask only when the target country differs from the CV country or
the user mentions visas. That sets `candidate.work_rights` and `candidate.needs_sponsorship`.

## Mapping answers → profile.json

- `targets.roles`: the chosen titles (max 6; the first 3–4 drive searches).
- `targets.title_keywords_positive`: distinctive lowercase words from the roles plus close synonyms ("developer" for "engineer", "ml" for "machine learning").
- `targets.title_keywords_negative`: seniority words above or below the target level ("senior", "staff", "principal", "lead", "manager", "director" for junior searches; "intern", "graduate" for senior searches), plus obvious wrong-domain words (e.g. "mechanical", "civil", "sales" for software roles).
- `targets.seniority`: from Q3, using linkedin-style buckets (`internship`, `entry`, `junior`, `graduate`, `associate`, `mid-senior`, `director`).
- `location.country` and `country_code` use ISO-2 lowercase. `gb` is fine; the scripts map it to `uk` where boards need that. For Australia also set `region_code` (SA, NSW, VIC, QLD, WA, TAS, ACT, NT), which Seek URLs need.
- `location.work_modes`: any of `remote`, `hybrid`, `onsite`.
- `skills.core`: the 5–10 strongest hard skills from the CV (lowercase, as written in job ads: "python", "react", "sql", "aws"). `skills.secondary` holds the rest.
- `compensation`: numbers only, annual unless the user says hourly.
- `search.posted_within_days` defaults to 14, `max_per_source` to 50 (use 100 for wide searches), and `min_score` to 3.5.
- `targets.target_companies`: for each company, find its ATS once. Try `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs`, `https://api.lever.co/v0/postings/<slug>`, then `https://api.ashbyhq.com/posting-api/job-board/<slug>` (a quick requests call in the workbench), or search `"<company> careers greenhouse OR lever OR ashby"`. Store `{name, ats, slug}`. Leave `ats` empty if it's none of those; the web and board sources will still catch them.

## Confirm before searching

Show the search brief in 4–6 lines (roles · location/modes · level · pay floor · freshness ·
sources) and ask "Search now?" with "Search now (Recommended)" and "Adjust". Skip this if the user
already said "just run it".

## Updating an existing profile

On "Tweak something", ask one multiSelect question: "What changed?" with the options "Roles",
"Location", "Pay", "Level" and "Exclusions". Re-ask only those fields. Bump `updated`.
