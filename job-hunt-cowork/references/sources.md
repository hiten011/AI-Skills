# Sources, connectors and CONFIG

Tested end-to-end in Cowork on 2026-09-29 through Composio. Slugs can drift. If one 404s,
rediscover it with `COMPOSIO_SEARCH_TOOLS` (use `search_strategy: "tool_search"`) and fix the call.

## Source map (what `fetch_jobs.py` runs)

| key | Where jobs come from | Composio toolkit / tool | Cost | Auto-enabled when |
|-----|----------------------|-------------------------|------|-------------------|
| `linkedin` | LinkedIn public job search | apify → `APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS` with actor `valig/linkedin-jobs-scraper` (input: `keywords`, `location`, `datePosted` r86400/r604800/r2592000, `limit`, `titleExclude`) | ~$0.40 per 1k jobs | always |
| ↳ fallback 1 | LinkedIn public (logged-out) job pages | `requests` to `linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search` (25 cards/page, 1 s between pages) | free | only if valig fails |
| ↳ fallback 2 | LinkedIn (richer filters) | `APIFY_SEARCH_LINKEDIN_JOBS` | $0.001/job | only if valig fails. **Needs a one-time approval** in the Apify console (the error message contains the approval URL; show it to the user) |
| `indeed` | Indeed (60 countries) | `APIFY_SCRAPE_INDEED_JOBS` (`title`, `country`, `location`, `datePosted` 1/3/7/14, `limit` ≤1000). If the typed tool fails validating its own output, the script reruns actor `valig/indeed-jobs-scraper` through `APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS` | ~$0.10 per 1k | always (skipped if the country is unsupported) |
| `boards` | Local boards, via Firecrawl JSON extraction of search pages: **Seek** + **Jora** (AU/NZ), **Reed** + Jora (UK), **Naukri** + Foundit (IN), **Built In** (US), **Job Bank** (CA), **MyCareersFuture** (SG), **StepStone** (DE/AT/CH), **We Work Remotely** (remote) + `extra_board_urls` | firecrawl → `FIRECRAWL_SCRAPE` with `formats:["json"]` | ~5 credits/page (free plan: 1,000/mo) | always |
| `web` | Postings on Lever/Greenhouse/Ashby found by web search (discovers companies not on boards). Marked **unverified** | composio_search → `COMPOSIO_SEARCH_WEB` (Exa) | free | always |
| `ats_search` | Greenhouse + Lever + Ashby cross-search | `APIFY_SEARCH_JOBS_ACROSS_SITES` (agentx/all-jobs-scraper) | ~$0.35 per 100 | always (often 0 results outside the US/UK) |
| `company_boards` | The user's target companies' own boards | free public ATS APIs (Greenhouse/Lever/Ashby JSON) via `requests` in the workbench | free | `target_companies` has slugs |
| `remote_boards` | Remotive, RemoteOK, Himalayas (+ Arbeitnow in EU) | free public JSON APIs | free | `remote` in work_modes |
| `dice` | Dice (US tech) | dice_mcp → `DICE_MCP_SEARCH_JOBS` | free | tech role and (US or remote) |
| `ziprecruiter` | ZipRecruiter (US/CA only) | ziprecruiter_mcp → `ZIPRECRUITER_MCP_SEARCH_JOBS` | free | country US/CA (flaky, errors are normal) |

**Browserbase** (`browserbase_tool`) is not a bulk source. `BROWSERBASE_TOOL_CREATE_SESSION` returns a
CDP `connectUrl`. `scripts/browserbase_fetch.py` drives it with local Playwright to read
JS-heavy careers pages (Workday, iCIMS, custom SPAs) or to liveness-check postings when
Firecrawl fails. Seek, Glassdoor and similar sites show Cloudflare to a plain session, so pass
`"proxies": true` for those (paid bandwidth) or stick with Firecrawl.

**LinkedIn connector** (`linkedin` toolkit): `LINKEDIN_GET_MY_INFO` gives name and headline for onboarding. The official API does **not** search jobs, which is why LinkedIn jobs come through Apify.

**Other useful Composio sources if the user connects them** (add a runner or call them inline): `APIFY_SEARCH_LINKEDIN_PROFILES` (hiring-manager lookup for outreach), Google Drive/Sheets (if they later want the tracker in the cloud), Gmail (spot recruiter replies; read-only unless asked).

## CONFIG (built from profile.json)

```python
CONFIG = {
  "run_id": "20260929-0930",                 # new per run; reuse for collect_only
  "roles": profile["targets"]["roles"],      # first 3-4 drive searches
  "title_keywords_positive": profile["targets"]["title_keywords_positive"],
  "title_keywords_negative": profile["targets"]["title_keywords_negative"],
  "country": profile["location"]["country"],            # full name, e.g. "Australia"
  "country_code": profile["location"]["country_code"],  # "au", "us", "gb", "in", ...
  "region_code": profile["location"].get("region_code", ""),   # AU state for Seek URLs
  "cities": profile["location"]["cities"],
  "work_modes": profile["location"]["work_modes"],
  "posted_within_days": profile["search"]["posted_within_days"],
  "max_per_source": profile["search"]["max_per_source"],   # per query; 50 default, 100 wide
  "target_companies": [c for c in profile["targets"]["target_companies"] if c.get("slug")],
  "extra_board_urls": profile["search"].get("extra_board_urls", []),  # "{q}"/"{role}" placeholders
  "is_tech_role": True,          # False for non-tech searches (disables Dice)
  "sources": "auto",             # or an explicit list of keys from the table above
  "time_budget_s": 120,          # the workbench kills cells at 180 s; leave room for upload
  # "only": ["linkedin"],        # rerun just some sources
  # "collect_only": True,        # just merge what finished, then upload
}
```

Budget: the user's Apify plan is the free $5/month tier, and the user chose full usage.
A default run (4 roles × up to 3 locations × 50) costs roughly $0.10–0.40 of Apify credit and
10–40 Firecrawl credits. For a very wide search, raise `max_per_source` to 100–200, then mention
the credit use in the report.

## Getting the file back

The last stdout line is `RESULT_JSON {"download_url": ...}`. Download it with
`curl -sSL -o jobs_<run_id>.json "<download_url>"` (it redirects to R2, so `-L` is required).
If the upload failed, rerun with `collect_only`. As a last resort, print the records in chunks.

## Troubleshooting (try one fix, then move on)

| Symptom | Fix |
|---------|-----|
| `full-permission-actor-not-approved` | Show the user the approval URL from the error. Carry on with the other sources. |
| Apify `402`/usage limit | The free credit is spent. Drop `linkedin`/`indeed`/`ats_search` and tell the user. The free sources still run. |
| valig returns 0 for a city | Retry with `location` = country name, or `"<city>, <state>, <country>"`. |
| Seek returns 0 / wrong page | Check `region_code`. Seek URLs look like `/software-engineer-jobs/in-All-Adelaide-SA?daterange=14`. |
| Firecrawl `429`/timeout | The script runs 2 scrapes at a time. If several searches share the account, rerun `only:["boards"]` once. Otherwise skip. |
| LinkedIn rows about the wrong role/city | Another run shared the workbench kernel. Rerun with a fresh globals dict for `exec` (see SKILL.md step 3). |
| Firecrawl JSON empty on a JS site | Use `browserbase_fetch.py` on that URL, then parse the text yourself. |
| Exa `429` | The script already sleeps 0.6 s between queries. Rerun `only:["web"]` later. |
| ZipRecruiter "Connection closed" | Known flakiness. Ignore. |
| Pending sources after collect_only | Report them as timed out in the Search Log, and don't block the run. |
