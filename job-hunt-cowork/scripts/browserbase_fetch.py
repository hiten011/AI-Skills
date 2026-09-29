#!/usr/bin/env python3
"""
job-hunt-cowork :: browserbase_fetch.py  (runs locally in the Cowork sandbox)

Opens JS-heavy pages (Workday / iCIMS / custom careers sites, or a posting you
want to liveness-check) in a Browserbase cloud browser and saves the visible text.
Use it only when Firecrawl returns empty or blocked content.

1. Create a session through Composio:
     BROWSERBASE_TOOL_CREATE_SESSION  {"timeout": 300, "browserSettings": {"blockAds": true}}
   (Add "proxies": true if a site shows a Cloudflare/"Attention Required" page;
    that uses paid proxy bandwidth.)
2. Run immediately (sessions expire):
     python browserbase_fetch.py "<connectUrl>" out.json URL [URL ...]
3. Release the session: BROWSERBASE_TOOL_RELEASE_SESSION (or let it time out).

Output JSON: [{url, final_url, title, status: live|expired|blocked|error, text}]
"""
import asyncio, json, re, sys

EXPIRED = re.compile(r"(no longer (available|accepting|open)|position has been filled|job (has )?expired|"
                     r"this job is closed|page not found|404)", re.I)
BLOCKED = re.compile(r"(attention required|verify you are human|access denied|captcha)", re.I)


async def main(connect_url, out, urls):
    from playwright.async_api import async_playwright
    res = []
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(connect_url, timeout=30000)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        for u in urls:
            try:
                await page.goto(u, timeout=45000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)
                title = await page.title()
                text = await page.evaluate("document.body ? document.body.innerText : ''")
                text = re.sub(r"\n\s*\n+", "\n", text or "").strip()
                status = "blocked" if BLOCKED.search(title + text[:500]) else \
                    "expired" if (EXPIRED.search(text[:3000]) or "error=true" in page.url or len(text) < 300) else "live"
                res.append({"url": u, "final_url": page.url, "title": title, "status": status, "text": text[:15000]})
            except Exception as ex:
                res.append({"url": u, "status": "error", "error": str(ex)[:300]})
        await browser.close()
    json.dump(res, open(out, "w"), indent=1)
    for r in res:
        print(r["status"], "|", r.get("title", "")[:80], "|", r["url"])


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3:]))
