#!/usr/bin/env python3
"""Job-posting signal scanner.

Reads companies.csv (domain, company, optional ats, slug). For each company it
finds the public job board on Greenhouse, Lever or Ashby (trying the domain's
first label as the slug when none is given), pulls open roles, matches titles
against the signal rules, and writes signals.csv plus a short summary.

No API keys. All three boards are public JSON. Run weekly.
  python3 signals.py              # scan
  python3 signals.py --discover   # only find and cache board slugs
"""
import csv, json, os, re, sys, urllib.request, urllib.error
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
COMPANIES = os.path.join(HERE, "companies.csv")
OUT = os.path.join(HERE, "signals.csv")
SEEN = os.path.join(HERE, "seen.json")

# Title patterns -> (signal, lane). First match wins.
RULES = [
    (r"\b(cmo|chief marketing|vp,? ?marketing|vice president,? ?marketing|head of marketing|head of demand|director,? ?(of )?demand|head of growth|vp,? ?growth|director,? ?(of )?marketing)\b", "marketing_leader", "2 empty seat"),
    (r"\b(sdr|bdr|sales development|business development rep|outbound rep|new business rep)\b", "sdr", "1 gap"),
    (r"\b(marketing ops|marketing operations|revops|revenue operations|rev ops|gtm engineer|go.to.market engineer|growth engineer|sales ops|sales operations)\b", "ops", "1 gap"),
    (r"\b(vp,? ?sales|head of sales|chief revenue|cro\b|vp,? ?revenue)", "sales_leader", "1 gap"),
]

EXCLUDE = re.compile(r"(recruit|people business|talent|analyst|data science|enablement|intern|\bindia\b|\bemea\b|\bdach\b|\buk\b|europe)", re.I)
US_CA = re.compile(r"(london|india|bengaluru|europe|emea|dach|amsterdam|berlin|paris|dublin|são paulo|sao paulo|sydney|singapore)", re.I)
US_CA_OK = re.compile(r"\b(united states|usa|u\.s\.|remote|anywhere|canada|[A-Z]{2}\b|new york|san francisco|atlanta|denver|austin|chicago|seattle|boston|toronto|vancouver|los angeles|hybrid)\b", re.I)

UA = {"User-Agent": "Mozilla/5.0 (job-signals; danwestmoreland.com)"}

def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
            if r.status != 200: return None
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def fetch(ats, slug):
    """Return a list of {title, location, url, posted} or None if no board."""
    if ats == "greenhouse":
        d = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        if not d or "jobs" not in d: return None
        return [{"title": j["title"], "location": (j.get("location") or {}).get("name", ""), "url": j.get("absolute_url", ""), "posted": (j.get("updated_at") or "")[:10]} for j in d["jobs"]]
    if ats == "lever":
        d = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        if not isinstance(d, list): return None
        return [{"title": j["text"], "location": (j.get("categories") or {}).get("location", ""), "url": j.get("hostedUrl", ""), "posted": datetime.fromtimestamp(j["createdAt"]/1000, tz=timezone.utc).strftime("%Y-%m-%d") if j.get("createdAt") else ""} for j in d]
    if ats == "ashby":
        d = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        if not d or "jobs" not in d: return None
        return [{"title": j["title"], "location": j.get("location", ""), "url": j.get("jobUrl", ""), "posted": (j.get("publishedAt") or "")[:10]} for j in d["jobs"]]
    return None

def discover(domain, hint_ats="", hint_slug=""):
    label = domain.split(".")[0].lower()
    cands = []
    if hint_ats and hint_slug: cands.append((hint_ats, hint_slug))
    for s in dict.fromkeys([hint_slug, label, label.replace("-", ""), label + "hq", label + "inc"]):
        if not s: continue
        for a in ("greenhouse", "lever", "ashby"):
            if (a, s) not in cands: cands.append((a, s))
    for a, s in cands:
        jobs = fetch(a, s)
        if jobs is not None:
            return a, s, jobs
    return "", "", None

def classify(title):
    t = title.lower()
    for pat, sig, lane in RULES:
        if re.search(pat, t): return sig, lane
    return None, None

def main():
    discover_only = "--discover" in sys.argv
    rows = list(csv.DictReader(open(COMPANIES, encoding="utf-8")))
    seen = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out, found, missing, counts = [], 0, [], {}
    for r in rows:
        ats, slug, jobs = discover(r["domain"], r.get("ats", ""), r.get("slug", ""))
        if jobs is None:
            missing.append(r["domain"]); continue
        found += 1
        r["ats"], r["slug"] = ats, slug
        if discover_only: continue
        titles_done = set()
        for j in jobs:
            sig, lane = classify(j["title"])
            if not sig or EXCLUDE.search(j["title"]): continue
            if US_CA.search(j["location"] + " " + j["title"]): continue
            tkey = j["title"].strip().lower()
            if tkey in titles_done: continue       # same role, several cities
            titles_done.add(tkey)
            key = f"{r['domain']}|{j['title'].strip()}"
            new = key not in seen
            seen.setdefault(key, today)
            counts[sig] = counts.get(sig, 0) + 1
            out.append({"company": r["company"], "domain": r["domain"], "signal": sig, "lane": lane, "title": j["title"], "location": j["location"], "posted": j["posted"], "first_seen": seen[key], "new_this_run": "yes" if new else "", "url": j["url"]})
    # write back discovered slugs so next run is fast
    with open(COMPANIES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "company", "ats", "slug"]); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in w.fieldnames})
    if discover_only:
        print(f"boards found for {found}/{len(rows)} companies; none for: {', '.join(missing)}"); return
    out.sort(key=lambda x: (x["lane"], x["company"]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["company"]); w.writeheader(); w.writerows(out)
    json.dump(seen, open(SEEN, "w"), indent=0)
    new = [o for o in out if o["new_this_run"]]
    print(f"# {today}: {len(rows)} companies, boards found for {found}, {len(out)} signals ({len(new)} new)")
    print("# " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    for o in out:
        flag = "NEW " if o["new_this_run"] else "    "
        print(f"{flag}[{o['lane']}] {o['company']}: {o['title']} ({o['location']}, {o['posted']})")
    if missing: print(f"# no board found: {', '.join(missing)}")

if __name__ == "__main__":
    main()
