# Reviewing the shortlist (career-ops rubric, condensed)

`score_jobs.py` gives a mechanical pre-score. Your job is to read the shortlist and the full
posting where needed, then write the real verdict. Keep each role to about 30 seconds of
thought. This is career-ops' *triage* depth, not its full A–H report.

## Global fit score: 1.0–5.0, one holistic number

Judge these five dimensions together. It's not an average:

| Dimension | Ask |
|-----------|-----|
| CV match | Do the must-have requirements map to things the user has actually done? Cite them. |
| North Star | Is this the kind of role they want (title, archetype, level)? |
| Pay | Advertised pay vs their floor/target. Unknown pay counts as neutral. |
| Culture & location | Work mode and location fit, company stage/type, stability signals. |
| Red flags | Blockers: clearance, no sponsorship when they need it, seniority mismatch, commission-only, "rockstar 10 yrs for junior pay". |

| Score | Verdict text (use exactly) | Meaning |
|-------|----------------------------|---------|
| 4.5–5.0 | `Strong match, apply` | Apply this week |
| 4.0–4.4 | `Good match, worth applying` | Worth the effort |
| 3.5–3.9 | `Decent, apply if there's a reason` | Only with a specific angle (referral, dream company) |
| < 3.5 | `Weak fit` | Recommend against |
| any | `Skip` | Hard blocker; say which one in `gaps` |

Hard blockers mean `Skip`: an explicit no-sponsorship posting when the user needs it, a required clearance they lack, a location or on-site requirement they can't meet, a posting that is closed, or a listed dealbreaker.

## Fields to write per role (review.json)

```json
{"key": "<from shortlist>", "fit_score": 4.2, "verdict": "Good match, worth applying",
 "why": "Python + React match 4/5 must-haves; built RAG chatbot = their 'LLM apps' ask; hybrid Adelaide",
 "gaps": "No Go experience (nice-to-have); 2+ yrs asked vs 1",
 "legitimacy": "High confidence", "archetype": "Full-stack / AI apps",
 "next_step": "Apply; lead CV with the RAG project"}
```

- `why`: at most 25 words, concrete, referencing the user's real evidence. Never invent a skill.
- `gaps`: the honest missing must-haves or risks, at most 20 words.
- `next_step`: one action, such as "Apply", "Apply + reach out to hiring manager", "Ask recruiter for end client", "Skip", or "Check if still open".

## Posting legitimacy (career-ops Block G). Separate from the score.

- `High confidence`: fresh (under 30 days), specific tech/requirements, apply button live.
- `Proceed with caution`: 30–60 days old, vague description, agency posting with hidden client, reposted often, web-search-only find.
- `Suspicious`: over 60–90 days old, contradictory requirements, no real company, asks for payment or personal documents up front.

Present these as signals, never accusations, and mention innocent explanations when relevant (evergreen roles, slow hiring).

## Archetypes (use the closest, or invent a short label)

AI/ML Engineer · AI Platform/LLMOps · Agentic/Automation · Data Scientist/Analyst · Backend ·
Frontend · Full-stack · Mobile · DevOps/SRE/Cloud · Security · QA/Test · Product Manager ·
Solutions/Forward-deployed Engineer · Designer · non-tech (use the role family, e.g. "Marketing").

## Calibration

- A title match with no requirement evidence stays at 3.5 or below.
- Pay below the floor caps the score at 3.4, unless the user said pay is flexible.
- More than 200 applicants on LinkedIn doesn't lower the fit, but mention it in `gaps` so the user moves fast.
- Recruiter/agency listing: keep the score, set legitimacy to "Proceed with caution", and make the next step "Ask recruiter for end client" (career-ops agency rule: never double-apply through two channels).
