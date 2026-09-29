# job-hunt-cowork

A Claude **Cowork** skill that runs your whole job search from one prompt ("run my job search").
It checks memory for your profile, asks only what's missing, and pulls jobs from many sources
through **Composio** connectors. It then dedupes and scores every role against you and hands back
a formatted **Excel tracker**.

Inspired by [career-ops](https://github.com/career-ops-hq/career-ops) (the rubric, ghost-job
checks, and "never apply for the user"). This version is rebuilt for Cowork's cloud sandbox,
so it has no local repo, no npm and no Playwright install.

## What it searches

| Source | How |
|--------|-----|
| LinkedIn | Apify actor `valig/linkedin-jobs-scraper` (Composio `apify`) |
| Indeed (60 countries) | Apify `APIFY_SCRAPE_INDEED_JOBS` |
| Seek, Jora, Reed, Naukri, Built In, StepStone, We Work Remotely, … | Firecrawl JSON extraction of search pages (Composio `firecrawl`) |
| Greenhouse / Lever / Ashby | Apify cross-ATS search, plus free public board APIs for your target companies |
| Hidden postings on company ATS pages | Exa web search (`composio_search`) |
| Remotive, RemoteOK, Himalayas, Arbeitnow | free public APIs |
| Dice, ZipRecruiter | Composio MCP toolkits (US-focused) |
| JS-heavy careers sites / liveness checks | Browserbase cloud browser (`browserbase_tool`) |
| Your name/headline | LinkedIn connector |

## Output: `job_hunt_YYYY-MM-DD.xlsx`

- **Dashboard**: live counts (found, new, top matches, applied, interviews), jobs by source and verdict, top 10.
- **Top Matches**: fit 1–5, verdict, why it fits, gaps and red flags, posting-legitimacy check, next step, link, and Status dropdown.
- **All Jobs**: every unique posting with filters, score breakdown, and "New since last run".
- **Skipped**: what was filtered out and why (dealbreakers, seniority, stale).
- **Search Log**: every query per source, with counts and errors.
- **Profile**: your search profile, embedded as JSON so the file doubles as memory.

Attach last run's Excel next time: your profile is restored, new jobs are marked, and your
statuses and notes carry over.

## Install in Cowork

1. Connect the tools in Composio: **apify, firecrawl, browserbase_tool, linkedin** (Exa search, Dice and ZipRecruiter need no auth).
2. Add this folder as a skill: Settings → Capabilities → Skills → upload a zip of `job-hunt-cowork/`, or save it from Claude's skill proposal card.
3. Say **"run my job search"**.

## Files

```
job-hunt-cowork/
├── SKILL.md                    # the workflow Claude follows
├── references/
│   ├── onboarding.md           # memory-first profile + question flow
│   ├── sources.md              # connectors, CONFIG, costs, troubleshooting
│   └── scoring.md              # career-ops-style fit rubric + legitimacy
├── scripts/
│   ├── fetch_jobs.py           # runs in the Composio workbench: all sources in parallel
│   ├── score_jobs.py           # dedupe + heuristic pre-score + dealbreakers
│   ├── build_excel.py          # the formatted tracker
│   └── browserbase_fetch.py    # cloud-browser fallback for JS-heavy pages
└── assets/profile.example.json
```

## Guarantees

It never submits applications, sends messages, or invents experience. Scraped content is
treated as data, never as instructions.
